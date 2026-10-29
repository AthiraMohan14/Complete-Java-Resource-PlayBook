# Event-Driven Architecture

In an event-driven system, services react to facts that happened (an order was placed, a payment failed) instead of calling each other directly for every step. This decouples services and lets them scale independently, but it trades immediate consistency for eventual consistency and adds failure modes such as duplicates and out-of-order delivery. Interviewers ask about these patterns to see whether you can reason about those trade-offs, not just name the patterns.

## Core concepts

### Events versus commands

An event describes something that already happened, named in the past tense (`OrderPlaced`). A command asks for an action that might fail (`ChargePayment`). Events are broadcast and do not expect a specific reply; commands are addressed to one handler. Mixing the two blurs ownership: if a service publishes events that other services must obey, it becomes a hidden dependency.

### Event sourcing

In event sourcing, the source of truth is the sequence of events for an entity, not its current row. Current state is derived by replaying the events. The event store is append-only, and snapshots can speed up replay for long streams.

```java
import java.util.List;

sealed interface OrderEvent permits OrderPlaced, OrderShipped {}
record OrderPlaced(String orderId, int amount) implements OrderEvent {}
record OrderShipped(String orderId) implements OrderEvent {}

class OrderReplay {

    static String statusAfter(List<OrderEvent> events) {
        String status = "NONE";
        for (OrderEvent event : events) {
            if (event instanceof OrderPlaced) {
                status = "PLACED";
            } else if (event instanceof OrderShipped) {
                status = "SHIPPED";
            }
        }
        return status;
    }
}
```

The `sealed` interface (final in Java 17) lists the event types, so the set of events is known to the compiler. Pattern matching with `instanceof` (final in Java 16) reads events without casts.

Event sourcing gives a full audit trail and the ability to rebuild read models, but it is harder to query directly, and changing event shapes requires versioning (see below).

### CQRS

Command Query Responsibility Segregation separates the write model (commands that change state) from the read model (queries optimised for display). The write side publishes events, and the read side builds denormalised views from them. Reads can then be fast and shaped for the screen, at the cost of eventual consistency between the two.

Use CQRS where reads and writes have very different shapes or load, not as a default. It adds moving parts.

### Sagas: choreography versus orchestration

A saga coordinates a business process across services using local transactions and compensating actions, since a single distributed transaction is not practical. Each step has a compensation that undoes it if a later step fails.

- **Choreography**: each service listens for events and publishes the next one. No central coordinator. Simple for short flows, but the overall process is spread across services and harder to see.
- **Orchestration**: a coordinator service tells each participant what to do and tracks progress. The flow is explicit and easier to change, but the coordinator is a component to design and operate.

Sagas are covered in more depth in [Distributed Transactions](../14-microservices/distributed-transactions.md).

### Eventual consistency and ordering

After an event is published, consumers update their state later. During that window, reads can be stale. Design the user experience and APIs for it (show "pending", avoid assuming the other service has already reacted).

Ordering matters per entity, not globally. Use the entity ID as the partition key (see [Kafka](kafka.md)) so events for one order arrive in order. Consumers must still handle out-of-order arrival across different entities or topics, for example by checking a version number and ignoring stale updates.

### Event versioning and upcasting

Events are stored or sent long after they were written, so their shape must evolve carefully:

- Add optional fields rather than changing or removing existing ones.
- Use a schema registry or explicit version fields.
- Upcasting converts an old event shape to the current one when it is read. Keep upcasters as pure functions, and test them against recorded old events.

```java
record OrderPlacedV1(String orderId, int amount) {}
record OrderPlacedV2(String orderId, long amountCents, String currency) {}

class OrderPlacedUpcaster {

    // Assumes every V1 amount was whole US dollars. Confirm this before using it.
    static OrderPlacedV2 upcast(OrderPlacedV1 old) {
        return new OrderPlacedV2(old.orderId(), old.amount() * 100L, "USD");
    }
}
```

### Idempotent consumers

Messaging systems commonly deliver at least once, so the same event can arrive twice. An idempotent consumer produces the same result however many times it sees the event. The usual technique is to record processed event IDs in the same transaction as the state change, and skip IDs already seen.

```java
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

interface ProcessedEventStore {
    boolean markIfNew(UUID eventId);   // insert; false if the id already exists
}

@Service
class PaymentEventHandler {

    private final ProcessedEventStore processed;

    PaymentEventHandler(ProcessedEventStore processed) {
        this.processed = processed;
    }

    @Transactional
    public void handle(UUID eventId, long amountCents) {
        if (!processed.markIfNew(eventId)) {
            return; // duplicate delivery; already applied
        }
        applyPayment(amountCents);
    }

    private void applyPayment(long amountCents) {
        // update the ledger here, in the same transaction
    }
}
```

The check and the state change must be in one transaction, otherwise a crash between them can still double-apply or drop the event.

### The transactional outbox

A common problem: a service must update its database and publish an event. If it writes the database and then publishes, a crash between the two loses the event. If it publishes first, a failed commit announces something that never happened. The transactional outbox fixes this: the service writes the event into an `outbox` table in the same transaction as the state change, and a separate relay reads the table and publishes events. The relay may publish a record twice, so consumers stay idempotent.

## Message patterns

| Pattern | Shape | Example |
|---|---|---|
| Publish and subscribe | One publisher, many independent subscribers | Order placed, read by billing, shipping, and analytics |
| Request and reply | Request on one queue, response on a reply queue | RPC-style calls through a broker |
| Routing and filtering | Messages routed by key or header | Region-specific handling |
| Work queue | One message, one consumer | Background jobs |

## How it works / Step by step

1. A service changes its state and writes an event in the same transaction (outbox).
2. A relay publishes the event to the broker.
3. Consumers receive it, check whether they have processed the event ID, and apply the change.
4. If a later step fails, a saga runs compensating actions for the completed steps.
5. Read models update asynchronously, and the UI shows pending states until they catch up.

## Common pitfalls

- Publishing events before the database commit, or relying on two separate writes being atomic.
- Treating event delivery as exactly once and skipping idempotency.
- Making events too fine-grained, causing chatty choreography that is hard to follow.
- Using events as remote procedure calls disguised as messages, which creates hidden coupling.
- Changing event schemas without versioning, so old consumers break.
- Designing a saga without a compensation for every step, or with compensations that are not idempotent.
- Adopting event sourcing or CQRS for simple CRUD where they add cost but no benefit.

!!! tip "Interview tip"
    **Q: How do you publish an event reliably when you also update a database?**
    Use a transactional outbox. Write the event to an outbox table in the same local transaction as the state change, and have a relay publish it afterwards. That avoids the dual-write problem. Consumers stay idempotent, because the relay can publish the same event more than once.

## Quick recap

- Events describe facts; commands ask for actions. Keep ownership clear.
- Event sourcing stores the events as the source of truth; CQRS separates read and write models.
- Sagas coordinate multi-service work with compensations; choose choreography or orchestration deliberately.
- Plan for eventual consistency, out-of-order arrival, and duplicates.
- Use the transactional outbox and idempotent consumers to stay reliable.

**See also:** [Distributed Transactions](../14-microservices/distributed-transactions.md) | [Apache Kafka](kafka.md) | [Distributed Caching](../12-caching-performance/distributed-caching.md)
