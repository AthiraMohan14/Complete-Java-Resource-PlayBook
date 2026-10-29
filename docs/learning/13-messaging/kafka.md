# Apache Kafka

Kafka is a distributed log: producers append records to topics, the records are kept for a configured retention period, and consumers read them at their own pace, tracking their position with offsets. That design differs from a traditional queue, where a consumed message is removed. Interviewers ask about Kafka to test whether you understand partitions, ordering, consumer groups, and what "exactly once" really means.

## Core concepts

### Architecture

- **Broker**: a Kafka server that stores partitions and serves clients.
- **Topic**: a named stream of records, such as `orders`.
- **Partition**: an ordered, append-only log that is a unit of storage and parallelism. A topic has one or more partitions spread across brokers.
- **Replica**: a copy of a partition on another broker. One replica is the **leader** that serves reads and writes; the others follow it.
- **Record**: a key, a value, headers, and a timestamp. The key decides the partition (usually by hashing).

Ordering is guaranteed only within a single partition. Records with the same key go to the same partition, so they stay in order relative to each other. Across partitions, there is no global order.

### Producers

Producers choose a partition from the key (or round-robin when the key is null), so records with the same key, such as an order ID, stay ordered. Serialisation converts objects to bytes; use a schema-aware serialiser for shared contracts (see schema management below).

The `acks` setting controls durability:

| `acks` | Meaning | Trade-off |
|---|---|---|
| `0` | Do not wait for the broker | Fastest, can lose data silently |
| `1` | Wait for the leader to write | Loses data if the leader fails before replication |
| `all` | Wait for all in-sync replicas | Strongest durability, higher latency |

Enable the idempotent producer (`enable.idempotence=true`) so retries do not write duplicates into a partition. Transactions extend this across several writes (see delivery semantics).

### Consumers and consumer groups

A consumer group is a set of consumers that share the partitions of a topic. Each partition is read by one consumer in the group at a time, so adding consumers increases parallelism up to the number of partitions. Consumers beyond that count sit idle. Different groups each receive every record, which is how one topic feeds several independent services.

Offsets record each group's position in each partition. Committing offsets tells Kafka where to resume after a restart or rebalance.

- **Auto-commit**: offsets are committed periodically, regardless of whether processing succeeded. A crash can lose or repeat work.
- **Manual commit**: you commit after processing. This gives at-least-once behaviour when processing is idempotent.

Rebalancing happens when consumers join or leave a group. Partitions are reassigned, and in-flight work for revoked partitions must be finished or abandoned safely.

### Delivery semantics

| Semantic | How | Risk |
|---|---|---|
| At-most-once | Commit the offset before processing | Messages are lost if processing fails |
| At-least-once | Process, then commit | Duplicates after a crash; consumers must be idempotent |
| Exactly-once | Idempotent producer, transactions, and read-process-write within Kafka | Scope is Kafka-to-Kafka; external side effects (a database write, an email) are not covered |

The honest answer for interviews is that most systems use at-least-once delivery with idempotent consumers. Kafka's exactly-once support is real, but it covers Kafka's own reads and writes, not an arbitrary side effect in your code.

### Tombstones and compaction

A topic with `cleanup.policy=compact` keeps the latest record per key and discards older ones. A record with a key and a null value is a tombstone: it tells compaction to remove that key. Compacted topics suit "current state" streams, such as the latest address per customer.

### Spring for Apache Kafka

`KafkaTemplate` sends records, and `@KafkaListener` consumes them.

```java
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
class OrderEventPublisher {

    private final KafkaTemplate<String, String> kafka;

    OrderEventPublisher(KafkaTemplate<String, String> kafka) {
        this.kafka = kafka;
    }

    void orderPlaced(String orderId, String payloadJson) {
        // The key keeps all events for one order in the same partition, in order.
        kafka.send("orders", orderId, payloadJson);
    }
}
```

```java
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

@Component
class BillingOrderListener {

    // Requires spring.kafka.listener.ack-mode=manual
    @KafkaListener(topics = "orders", groupId = "billing")
    void onOrder(String payloadJson, Acknowledgment ack) {
        process(payloadJson);   // must be idempotent
        ack.acknowledge();      // commit only after success
    }

    private void process(String payloadJson) {
        // record the event id in a table first, and skip duplicates
    }
}
```

Set `spring.kafka.listener.ack-mode=manual` when you use `Acknowledgment`. Spring's default container behaviour commits differently, so check the configured mode before relying on it.

### Error handling and dead-letter topics

When processing keeps failing, retrying forever blocks the partition. Spring Kafka's `DefaultErrorHandler` retries with a back-off, and a `DeadLetterPublishingRecoverer` publishes the failed record to a dead-letter topic (DLT) after the retries are exhausted. Spring Boot picks up a `CommonErrorHandler` bean automatically.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.util.backoff.FixedBackOff;

@Configuration
class KafkaErrorConfig {

    @Bean
    DefaultErrorHandler errorHandler(KafkaTemplate<Object, Object> template) {
        DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(template);
        return new DefaultErrorHandler(recoverer, new FixedBackOff(1_000L, 3L));
    }
}
```

Monitor the DLT. Messages there need a decision: fix and replay, or discard with a record of why.

### Schema management

Producers and consumers evolve independently, so the message format needs a contract. Avro, Protobuf, and JSON Schema are common. A schema registry stores versions and checks compatibility rules, so a producer cannot publish a change that breaks existing consumers. Add optional fields rather than renaming or removing them, and keep consumers tolerant of unknown fields.

### Kafka Streams and Kafka Connect

Kafka Streams is a Java library for stateful stream processing (aggregations, joins, windows) that runs inside your application and stores state locally with changelog topics for recovery. Kafka Connect moves data between Kafka and external systems (databases, object stores) using configured connectors, without custom consumer code.

## How it works / Step by step

1. A producer serialises the record and chooses a partition from the key.
2. The leader writes it to its log; with `acks=all`, the write waits until the in-sync replicas have it.
3. Consumers in a group are assigned partitions. Each reads from its committed offset.
4. After processing, the consumer commits its offset.
5. On failure, the error handler retries, then routes the record to a DLT if it still cannot be processed.

## Common pitfalls

- Using a key with few distinct values (for example, a country code), so one partition gets most of the traffic.
- Expecting global ordering across partitions.
- Setting more consumers than partitions and wondering why some are idle.
- Auto-committing offsets with slow processing, so a crash loses work.
- Retrying a poison message forever, which stalls the whole partition.
- Assuming "exactly once" means an external database write happens once.
- Changing a record schema in a way that old consumers cannot read.

!!! tip "Interview tip"
    **Q: How does Kafka guarantee order?**
    Only within a partition. Records with the same key go to the same partition, so events for one entity stay in order. If you need order across different keys, you need a single partition, which limits throughput, or you design the consumers so order does not matter.

## Quick recap

- Topics are split into partitions; order holds only within a partition.
- Consumer groups share partitions; parallelism is capped by partition count.
- Offsets and commit strategy decide between at-most-once and at-least-once delivery.
- Use `acks=all` and the idempotent producer for durability without duplicates.
- Route poison messages to a dead-letter topic instead of retrying forever.

**See also:** [RabbitMQ](rabbitmq.md) | [Event-Driven Architecture](event-driven-architecture.md) | [Testing with Testcontainers](../11-testing/integration-testing.md)
