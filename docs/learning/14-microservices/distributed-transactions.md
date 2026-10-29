# Distributed Transactions

When one business operation changes data in several services, a single database transaction cannot cover it. Distributed transactions are the approaches for keeping that data consistent: the classic two-phase commit (2PC), and the saga pattern built on compensating actions. Interviewers ask about this because it is one of the hardest parts of microservices, and because the answer is always a trade-off between consistency, availability, and complexity.

## Core concepts

### CAP theorem and eventual consistency

The CAP theorem says that during a network partition, a distributed system must choose between consistency (every read sees the latest write) and availability (every request gets a response). Partitions happen, so the real choice is what the system does when they do. PACELC extends this: even without a partition, there is a trade-off between latency and consistency.

Most microservice systems accept eventual consistency: after a change, other services converge on the new state within a bounded, acceptable time. That is a business decision. Ask what staleness the business can tolerate for each piece of data.

### Two-phase commit

2PC coordinates a transaction across resources in two phases:

1. **Prepare**: the coordinator asks each participant whether it can commit. Participants lock their resources and vote yes or no.
2. **Commit or abort**: if all voted yes, the coordinator tells everyone to commit; otherwise it tells everyone to abort.

Its limits explain why microservices avoid it:

- Participants hold locks during the protocol, so throughput drops and contention rises.
- The coordinator is a single point of failure. If it fails after prepare, participants may wait with locks held.
- Many modern systems (NoSQL stores, message brokers, and many cloud services) do not offer the XA interface it needs.
- Latency increases with every participant and every network round trip.

JTA (Jakarta Transactions) and XA support exist for legacy cases, but they are rarely the right answer for new services.

### The saga pattern

A saga breaks a business transaction into local transactions, one per service. Each step commits locally and publishes an event or returns a result. If a later step fails, the saga runs compensating transactions for the steps already completed. A compensation is a new business action that undoes an effect, such as refunding a payment. It cannot always restore the exact prior state; for example, an email already sent cannot be unsent.

Two coordination styles:

- **Choreography**: services react to each other's events. The order service publishes `OrderCreated`, inventory reserves stock and publishes `StockReserved`, payment charges and publishes `PaymentCaptured`. If payment fails, inventory listens for a failure event and releases the stock. Simple for short flows, but the full process is spread across services.
- **Orchestration**: a saga orchestrator sends commands to each participant and tracks state. The flow is explicit and easier to change or observe, but the orchestrator must be designed, persisted, and kept available.

```java
class CheckoutSaga {

    void execute(String orderId, int amountCents) {
        reserveStock(orderId);
        try {
            charge(orderId, amountCents);
        } catch (PaymentDeclinedException declined) {
            releaseStock(orderId);      // compensation for the completed step
            throw declined;
        }
    }

    private void reserveStock(String orderId) {
        // call the inventory service; must be idempotent
    }

    private void charge(String orderId, int amountCents) {
        // call the payment provider; must be idempotent
    }

    private void releaseStock(String orderId) {
        // compensation; must be idempotent and safe to retry
    }
}

class PaymentDeclinedException extends RuntimeException {
    PaymentDeclinedException(String message) {
        super(message);
    }
}
```

The orchestrator must persist its progress. If it crashes mid-saga, it needs to resume or compensate, not start over.

### Compensations and their limits

A compensation must be idempotent, because it may run more than once. It should also be retryable until it succeeds, which usually means it is driven by a durable state machine or message retries. Some steps are not compensable (a shipment already dispatched), so the design needs a "pivot" step after which the saga only moves forward, with retries rather than rollback.

### Idempotency and deduplication

Every step and compensation in a saga can run more than once, because messages are redelivered and retries happen. Use an idempotency key (for example, the saga ID plus the step name) and store it with the result, so repeated calls return the same outcome. The same approach applies to payments, where the provider's idempotency key header prevents double charges. See [Event-Driven Architecture](../13-messaging/event-driven-architecture.md) for the processed-events table and the transactional outbox.

### Choosing an approach

| Option | Consistency | Availability | Complexity | Typical use |
|---|---|---|---|---|
| Single local transaction | Strong | Depends on one database | Low | Everything in one service |
| Two-phase commit | Strong across resources | Reduced during failures | High operational risk | Legacy, few resources, XA-capable systems |
| Saga (choreography) | Eventual | High | Medium, spread out | Short flows across few services |
| Saga (orchestration) | Eventual | High | Medium, centralised | Longer flows, complex rules |

### Saga state and timeouts

The orchestrator needs durable state. A minimal table records each saga instance and where it stopped:

```sql
CREATE TABLE saga_instance (
    saga_id      UUID PRIMARY KEY,
    saga_type    VARCHAR(64)  NOT NULL,
    current_step VARCHAR(64)  NOT NULL,
    status       VARCHAR(16)  NOT NULL,  -- RUNNING, COMPLETED, COMPENSATING, FAILED
    deadline_at  TIMESTAMP    NOT NULL,
    updated_at   TIMESTAMP    NOT NULL
);
```

Each step updates the row in the same local transaction as its business change, so state and effect cannot disagree. A scheduled job then looks for sagas that are `RUNNING` or `COMPENSATING` past their `deadline_at`. It retries the current step if it is safe to do so, or starts compensation if it is not. Without this sweeper, a lost message leaves a saga stuck forever with no one noticing.

Each saga step should also have its own timeout. A step that does not answer within its budget is treated as a failure, which makes the saga either retry or compensate, rather than hold resources open.

Saga status is also a product feature. Expose it to support staff and, where appropriate, to users (for example, "payment pending"), so people can see what is happening while the system converges.

## How it works / Step by step

1. Model the business process as steps, each with a compensation (or a marker that it is a pivot).
2. Give each step an idempotency key and make it safe to repeat.
3. Run each step as a local transaction in its service, and publish the outcome (through the outbox).
4. On failure, run the compensations for completed steps in reverse order, retrying until they succeed.
5. Record the saga's state so it can resume after a crash, and expose its status so support teams can see it.

## Common pitfalls

- Using 2PC across microservices because it looks like a normal transaction.
- Sagas without persisted state, so a crash loses track of which steps ran.
- Compensations that are not idempotent or that assume the original step's exact result.
- Ignoring the window in which other services see intermediate states, and not designing for it.
- Dual writes (update the database, then publish) without an outbox.
- No timeouts on saga steps, so one stuck participant holds the whole process open.
- Overusing sagas when a single service could own the data and the transaction.

!!! tip "Interview tip"
    **Q: How do you keep order and payment consistent across services?**
    Use a saga. The order is created as pending, a payment step runs in its own local transaction, and each step has a compensation: if payment is declined, the order is cancelled. Steps are idempotent, the saga state is persisted, and events go out through an outbox. Explain that the system is eventually consistent, and say what the user sees while it is pending.

## Quick recap

- CAP is about what happens during partitions; most microservice systems choose eventual consistency.
- 2PC gives strong consistency but blocks resources and adds a coordinator failure mode.
- Sagas use local transactions and compensations; choose choreography or orchestration deliberately.
- Make every step and compensation idempotent, and persist saga state.
- Avoid distributed transactions unless the data truly must be in one place.

**See also:** [Event-Driven Architecture](../13-messaging/event-driven-architecture.md) | [Microservices Fundamentals](microservices-fundamentals.md) | [Databases and SQL](../06-databases-sql/index.md)
