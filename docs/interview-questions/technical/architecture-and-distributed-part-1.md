# Architecture and Distributed Systems Questions (Part 1)

Questions on monolith versus microservices, service boundaries, synchronous and asynchronous communication, Kafka and RabbitMQ, and distributed transactions. Part 2 covers resilience, data, and system design. For system design rounds, state your assumptions first, then sketch the components, then discuss the trade-offs.

---

## 1. When is a monolith the better choice than microservices?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A monolith is the better choice when the team is small, the domain is not yet well understood, deployment and operations capacity is limited, or the parts of the system change together. Microservices pay off when independent teams need to deploy separately, parts of the system need different scaling, or failure isolation matters enough to justify the operational cost.

### Explanation
Microservices add network calls, distributed failures, versioned contracts, separate deployments, distributed tracing, and data consistency problems. A well-structured modular monolith keeps package boundaries clear and can be split later, when a module has a real reason to become a service.

### When to use / pitfalls
- Splitting too early creates a distributed monolith: services that must be deployed together and share a database.
- Use the team's organisation as a hint. Services usually map to teams that can own them end to end.

**See also:** [Microservices fundamentals](../../learning/14-microservices/microservices-fundamentals.md)

</details>

---

## 2. How do you decide service boundaries, and why does each service own its data?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Find bounded contexts from Domain-Driven Design: areas of the business with their own language and rules, such as "ordering" and "billing". Each service owns its data, so other services reach that data through its API or its events, not through its tables. Shared databases couple services at the storage level, and a schema change in one breaks the others.

### Explanation
Signs of a bad boundary: two services that must change together for every feature, or one service that calls another for almost every request. Signs of a good one: a team can change most of its work without touching other services.

Database-per-service also has costs. Joins across services become API calls or read models, and transactions cannot span services as easily. Those costs are worth paying only when the boundaries are right.

### When to use / pitfalls
- A shared "customer" table across services is a common source of hidden coupling. Let each service keep the fields it needs, copied through events.
- Reporting across services needs a separate read model or a data platform, not direct joins into other services' tables.
- Starting with a shared database is acceptable for a young system. Move to database-per-service when the boundaries are clear.

**See also:** [Microservices fundamentals](../../learning/14-microservices/microservices-fundamentals.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 3. When do you use synchronous calls and when do you use asynchronous messaging?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use synchronous calls (REST, gRPC, GraphQL) when the caller needs the answer to continue, such as a price lookup during checkout. Use asynchronous messaging (Kafka, RabbitMQ, SQS) when the caller only needs to hand off work or announce something happened, such as "order placed". Asynchronous messaging decouples availability and load, at the cost of eventual consistency and harder debugging.

### Explanation
A chain of synchronous calls is only as available as its weakest link: if five services each have 99.9% availability in series, the chain is roughly 99.5% available. Async handoffs keep the caller working when a downstream service is slow or down, as long as messages are stored durably.

Synchronous requests are simple to implement and give immediate errors. Their weakness is coupling in time: a slow callee holds the caller's threads, and that pressure spreads upstream.

### When to use / pitfalls
- Set timeouts on every synchronous call, or one slow dependency will hold threads across the whole system.
- gRPC suits internal, low-latency calls with strong contracts; REST suits public APIs that many clients consume.
- Do not turn every call into a message. Asynchronous flows are harder to trace and to reason about.

**See also:** [Inter-service communication](../../learning/14-microservices/inter-service-communication.md), [Messaging and event-driven architecture](../../learning/13-messaging/event-driven-architecture.md)

</details>

---

## 4. How does Kafka organise data, and where is ordering guaranteed?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Kafka stores records in topics, and each topic is split into partitions. Each partition is an ordered, append-only log replicated across brokers. Ordering is guaranteed only within one partition. Producers choose the partition from the record key (keys with the same hash go to the same partition), and consumers in one consumer group share the partitions, with each partition read by one consumer at a time.

### Explanation
```java
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
class OrderEvents {
    private final KafkaTemplate<String, String> kafka;

    OrderEvents(KafkaTemplate<String, String> kafka) {
        this.kafka = kafka;
    }

    void orderPlaced(String orderId, String json) {
        kafka.send("orders", orderId, json);   // same key -> same partition -> ordered per order
    }
}
```

Kafka retains records for a configured time or size, independent of whether consumers read them, so consumers can replay. Ordering across different keys is not guaranteed, and adding partitions later changes the key-to-partition mapping for new records.

### When to use / pitfalls
- Plan partition counts up front. Adding partitions later changes where new records with a given key land.
- Do not design logic that needs global order across all keys.
- A single hot key sends all its traffic to one partition, which limits throughput for that key.

**See also:** [Apache Kafka](../../learning/13-messaging/kafka.md)

</details>

---

## 5. How do consumer groups share partitions, and what do offsets track?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A consumer group is a named set of consumers that split a topic's partitions between them, so each partition has one reader in the group at a time. An offset is the position of a group in a partition, and the group's committed offsets are stored by Kafka, in the internal `__consumer_offsets` topic. Different groups keep separate offsets, so each group sees the full stream. When a consumer joins, leaves, or crashes, the group rebalances and moves partitions to the remaining members.

### Explanation
Partitions are the unit of parallelism. A topic with four partitions can be read by up to four consumers in one group. A fifth consumer sits idle until one of the others leaves.

```java
import java.time.Duration;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;

class OrderPoller {

    void run(KafkaConsumer<String, String> consumer) {
        while (true) {
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(500));
            for (ConsumerRecord<String, String> record : records) {
                process(record.value());
            }
            consumer.commitSync();   // commit only after the whole batch succeeded
        }
    }

    private void process(String value) {
        // business logic goes here
    }
}
```

Committing after processing gives at-least-once behaviour: a crash between processing and committing replays the batch. Committing before processing gives at-most-once: a crash loses the batch. If a batch takes longer than the configured poll interval, the consumer is considered failed and the group rebalances, so keep batch handling bounded.

### When to use / pitfalls
- Two groups reading the same topic do not share offsets. Use one group per independent service.
- Changing a group's name starts it from its configured reset position, which may skip or repeat records.
- Rebalances pause consumption briefly. Frequent rebalances usually mean consumers are crashing or running too slowly.

**See also:** [Apache Kafka](../../learning/13-messaging/kafka.md)

</details>

---

## 6. What are Kafka delivery semantics, and how do you consume messages safely?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
At-most-once means a message can be lost but is never processed twice. At-least-once means it is never lost but may be processed more than once. Exactly-once, within Kafka itself, uses idempotent producers and transactions; end-to-end exactly-once with an external database still needs idempotent processing. Most systems use at-least-once and make consumers idempotent.

### Explanation
```java
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

class IdempotentHandler {
    private final Set<String> processed = ConcurrentHashMap.newKeySet();

    void handle(String messageId, Runnable work) {
        if (processed.add(messageId)) {   // add() returns false if the ID was already seen
            work.run();
        }
    }
}
```

The in-memory set is a demonstration only. In production, store the processed IDs in the same database transaction as the business change, so a crash cannot separate them. Kafka's exactly-once support covers reads and writes that stay inside Kafka; a database write or an email is outside it.

### When to use / pitfalls
- With auto-commit offsets, a crash after commit but before processing loses the message. Commit offsets after processing when loss is unacceptable.
- Failed messages that retry forever block a partition. Send them to a dead-letter topic after a bounded number of attempts.
- Schema changes need compatibility rules (Avro, Protobuf, or JSON Schema with a registry).

**See also:** [Apache Kafka](../../learning/13-messaging/kafka.md), [Event-driven architecture](../../learning/13-messaging/event-driven-architecture.md)

</details>

---

## 7. What is the saga pattern, and what is the difference between choreography and orchestration?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A saga breaks a business transaction across services into local transactions, each followed by a compensating action if a later step fails. In choreography, services react to each other's events with no central controller. In orchestration, one coordinator service calls each step and decides what to compensate. Sagas give eventual consistency, not the isolation of a single ACID transaction.

### Explanation
Consider a money transfer. The debit happens in one service and the credit in another. If the credit fails, the saga must reverse the debit, which is a compensating action, not a rollback.

```java
import java.math.BigDecimal;

interface AccountClient {
    void debit(String accountId, BigDecimal amount);
    void credit(String accountId, BigDecimal amount);
}

class TransferOrchestrator {

    private final AccountClient accounts;

    TransferOrchestrator(AccountClient accounts) {
        this.accounts = accounts;
    }

    void moveMoney(String payer, String payee, BigDecimal value) {
        accounts.debit(payer, value);                // step 1: local transaction in the payer's account
        try {
            accounts.credit(payee, value);           // step 2: local transaction in the payee's account
        } catch (RuntimeException e) {
            accounts.credit(payer, value);           // compensation: a new credit, not a database rollback
            throw e;
        }
    }
}
```

Choreography suits a few steps with clear events. Orchestration suits longer flows where you need one place to see the state and handle timeouts, retries, and manual intervention. Workflow engines such as Temporal implement orchestration. The orchestrator in the example would itself need durable state in a real system, because a crash between steps would otherwise lose track of the saga.

### When to use / pitfalls
- Compensations are not always exact undos: a refund is a new transaction, not a reversal. Design compensations as business actions.
- Make each step idempotent, because the saga engine will retry it.
- Other readers can see intermediate states. Show them as "pending" in the user interface.

**See also:** [Distributed transactions](../../learning/14-microservices/distributed-transactions.md)

</details>

---

## 8. What is the transactional outbox pattern, and why is it needed?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The outbox pattern solves the dual-write problem: a service must update its database and publish an event, but no single transaction covers both a database and a broker. The service writes the event into an `outbox` table in the same database transaction as the business change. A separate relay reads the outbox and publishes the events, then marks them sent. This gives at-least-once delivery without losing events.

### Explanation
```sql
CREATE TABLE outbox (
    id          BIGINT PRIMARY KEY,
    aggregate   VARCHAR(100) NOT NULL,
    payload     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL,
    sent_at     TIMESTAMP
);
```

The relay can poll the table or read the database's change log with change data capture. Consumers must still be idempotent, because the relay can publish a message twice after a crash.

### When to use / pitfalls
- Saving to the database and then publishing, in either order, can lose or duplicate events on failure.
- Clean up sent rows on a schedule, or the outbox table grows without limit.

**See also:** [Event-driven architecture](../../learning/13-messaging/event-driven-architecture.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 9. What are your options when one business operation spans several services?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
ACID transactions do not span several services and their databases, so the usual answer is not one big transaction. Use a saga for multi-step business work with compensations, the outbox pattern for reliable event publishing, and idempotent consumers for retries. Event sourcing and CQRS fit when you need an audit trail or read models shaped very differently from writes. Two-phase commit exists, but it is rarely the right choice between microservices.

### Explanation
Two-phase commit works in two rounds. A coordinator asks every participant to prepare, then tells all of them to commit. Participants hold locks while they wait, a slow participant slows everyone, and if the coordinator fails after the prepare round, participants can be stuck waiting for a decision. Those costs are why most microservice designs avoid it.

| Scenario | Usual approach |
|---|---|
| Money transfer between accounts | Saga with a compensating credit or debit |
| Order and inventory | Events with eventual consistency, plus a conditional stock reservation |
| Audit trail is required | Event sourcing |
| Reads need a different shape from writes | CQRS with read models built from events |

Delivery guarantees frame each step. At-most-once can lose messages, at-least-once can duplicate them, and exactly-once is achieved end to end only by combining idempotent processing with transactional writes.

### When to use / pitfalls
- Do not add two-phase commit to a microservice design by default. Consider it only when every participant supports it and the cost is acceptable.
- A saga without a compensation for each step leaves partial work behind.
- Compensations must tolerate retries, so make them idempotent.

**See also:** [Distributed transactions](../../learning/14-microservices/distributed-transactions.md), [Event-driven architecture](../../learning/13-messaging/event-driven-architecture.md)

</details>

---

## 10. Where is eventual consistency good enough, and where is it not?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Eventual consistency means that after an update, different copies of the data may disagree for a while, and then converge once the updates have been delivered. It is acceptable when a short period of stale data causes little harm, such as a like count, an analytics dashboard, a search index, a cached profile, or a notification. It is not acceptable when stale data leads to a wrong decision that costs money or breaks a rule, such as an account balance, an overselling inventory count, or a payment that is charged twice.

### Explanation
Consider a payment that a service records and a ledger that applies. For a short time the order service can show "payment pending" while the ledger has not yet applied it. Once the event is consumed, both agree. The user interface and the API must be designed for that window: show the pending state and avoid assuming the other service has already reacted.

Strong consistency inside one service's transaction is still available and often used. A common design is strong consistency for the rule that must never break (a conditional update that reserves the last unit of stock) and eventual consistency for everything around it (the search index, the recommendation feed, the confirmation email).

Strategies that make eventual consistency workable include events with idempotent consumers, read models updated asynchronously, version numbers that let consumers ignore stale updates, and compensating actions when a later step fails.

### When to use / pitfalls
- "Eventually" needs a bound in practice. Monitor consumer lag so that a stuck consumer is noticed in minutes, not days.
- Do not use eventual consistency for a rule that must hold at every moment. Keep that rule inside one transaction.
- A read right after a write may not show the write. Route those reads to the source of truth, or return the new value in the write response.

**See also:** [System design fundamentals](../../learning/19-system-design-fundamentals/core-concepts.md), [Distributed transactions](../../learning/14-microservices/distributed-transactions.md)

</details>

---

## 11. How do you choose between RabbitMQ and Kafka for a given workload?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use RabbitMQ when you need flexible routing, per-message acknowledgement and retries, and work queues where each message is processed by one consumer and then removed. Use Kafka when you need a high-throughput, ordered log that several consumer groups read independently, and you want replay within a retention window. Both work in a microservice system, and the choice depends on the traffic shape and the replay requirement, not on which one is more popular.

### Explanation
RabbitMQ routes through exchanges and bindings, so a message can reach different queues by topic, header, or fanout rules. Acknowledged messages are removed. Kafka keeps records for the retention period, and each consumer group keeps its own offset, so a new analytics job can start from last week's data.

Examples that fit each:

- A pool of workers sends welcome emails, each email is processed once, failures go to a dead-letter queue. This is a RabbitMQ shape.
- Every service needs every order event, a fraud model replays the last seven days after a fix, and the stream reaches tens of thousands of messages per second. This is a Kafka shape.

### When to use / pitfalls
- Choosing Kafka for a simple job queue adds operational overhead for little benefit.
- Choosing RabbitMQ when you need replay means keeping your own archive, because acknowledged messages are gone.
- Kafka orders records within a partition only. RabbitMQ orders within a queue, but competing consumers process messages concurrently.

**See also:** [RabbitMQ](../../learning/13-messaging/rabbitmq.md), [Apache Kafka](../../learning/13-messaging/kafka.md)

</details>

---

**See also:** [Architecture and distributed systems, part 2](architecture-and-distributed-part-2.md), [Interview preparation](../interview-process.md), [Technical questions index](index.md)
