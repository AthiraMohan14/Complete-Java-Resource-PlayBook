# Advanced Patterns

These patterns appear when a system spans several services, stores, or machines and a single database transaction is no longer enough. Interviewers ask about them to see whether you understand consistency trade-offs, failure handling across services, and when a pattern is worth its complexity.

## Core concepts

### Event sourcing

In **event sourcing**, you store the sequence of events that happened to an entity, not just its current state. The current state is derived by replaying the events. An account is "opened, deposited 50, withdrew 20", not "balance 30".

Benefits: a full audit trail, the ability to rebuild state or compute new views from history, and a natural fit for asynchronous integration. Costs: more complex queries, event schema evolution, and the need for snapshots when replay gets long.

Java 21 makes the event model concise. A sealed interface lists the allowed events, and an exhaustive switch folds them into state:

```java
import java.math.BigDecimal;
import java.util.List;

public class AccountEvents {

    public sealed interface AccountEvent permits Deposited, Withdrawn {}

    public record Deposited(String accountId, BigDecimal amount) implements AccountEvent {}

    public record Withdrawn(String accountId, BigDecimal amount) implements AccountEvent {}

    public record Account(BigDecimal balance) {

        public static Account empty() {
            return new Account(BigDecimal.ZERO);
        }

        public Account apply(AccountEvent event) {
            return switch (event) {
                case Deposited d -> new Account(balance.add(d.amount()));
                case Withdrawn w -> new Account(balance.subtract(w.amount()));
            };
        }
    }

    public static Account replay(List<AccountEvent> history) {
        Account account = Account.empty();
        for (AccountEvent event : history) {
            account = account.apply(event);
        }
        return account;
    }
}
```

The compiler checks that the switch covers every permitted event, so adding a new event type produces a compile error wherever you have not handled it.

### CQRS

**Command Query Responsibility Segregation (CQRS)** separates the write model (commands that change state and enforce rules) from the read model (queries shaped for screens and reports). The two can use different stores and different schemas. Events published by the write side update one or more read models, called projections.

Because projections are updated asynchronously, reads can lag behind writes. That is **eventual consistency**. Design the user experience for it: show "processing" states, or read your own write from the command response.

CQRS and event sourcing are often used together, but neither requires the other. CQRS alone can be useful when read and write loads differ greatly.

### Distributed sagas

A **saga** coordinates a business transaction across several services, where each step commits locally and no distributed lock or two-phase commit is used. If a later step fails, earlier steps are undone by **compensating actions** (refund a payment, release reserved stock).

Two styles:

- **Choreography:** each service listens for events and reacts. Simple for short flows; hard to see the whole flow and to change it.
- **Orchestration:** a coordinator tells each service what to do next and handles failures. Clearer flow and easier to monitor; the coordinator is an extra component to run.

A minimal in-memory orchestrator shows the compensation logic. Production sagas persist their state, so a restart can resume or compensate:

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;

public final class OrderSaga {

    public interface Step {
        void execute();

        void compensate();
    }

    private OrderSaga() {
    }

    public static void run(List<Step> steps) {
        Deque<Step> completed = new ArrayDeque<>();
        try {
            for (Step step : steps) {
                step.execute();
                completed.push(step);
            }
        } catch (RuntimeException failure) {
            // Undo completed steps in reverse order
            while (!completed.isEmpty()) {
                completed.pop().compensate();
            }
            throw failure;
        }
    }
}
```

Compensations can fail too. Make them idempotent, retry them with backoff, and alert when one cannot complete. Some actions cannot be undone (an email sent), so model them as steps that come last or that have compensating messages instead.

### Workflow engines: Temporal

A **workflow engine** runs long-lived business processes durably. **Temporal** lets you write the workflow as ordinary code. The engine persists each step's progress, so a workflow survives process restarts and resumes where it stopped. Retries, timers, and timeouts are part of the platform. Activities (the side-effecting steps) must still be idempotent, because retries can repeat them.

Temporal suits sagas, multi-day approvals, and scheduled processes. For a simple two-step flow, a queue and a database table may be enough.

### Stream processing: Kafka Streams and Apache Flink

**Stream processing** computes results continuously over an unbounded sequence of events.

- **Kafka Streams** is a Java library. You write a topology of operators (filter, map, join, aggregate) that runs inside your application and reads from and writes to Kafka topics. It is a good fit when the data lives in Kafka and you want a library rather than a cluster.
- **Apache Flink** is a distributed processing engine with its own cluster. It handles large-scale stateful processing, event-time windows, and checkpointing.

The core concepts are windows (tumbling, sliding, session), event time versus processing time, watermarks for late data, and state stored for each key. Choose Kafka Streams for application-embedded processing and Flink for larger, more complex pipelines.

## How it works

1. An event-sourced aggregate stores events; its state is rebuilt by folding them.
2. Commands are validated against current state and produce new events.
3. Projections subscribe to events and update read models asynchronously.
4. A saga runs steps across services; on failure, compensations run in reverse order.
5. A stream processor consumes events, keeps per-key state, and emits derived events or results.

## Common pitfalls

- Using event sourcing for simple CRUD where it adds cost without value
- Changing event schemas without versioning, which breaks replay
- Expecting read models to be up to date immediately after a write
- Sagas with non-idempotent compensations, or no plan for a compensation that fails
- Choosing choreography for long flows that need visibility
- Using distributed transactions to avoid eventual consistency, which often costs more than it saves
- Ignoring late and out-of-order events in stream processing

!!! tip "Interview tip"
    **Q: How do you handle a payment that succeeds but a later stock reservation fails?**
    A: Use a saga. The reservation step fails, so the saga runs the compensation for the payment (a refund or void), in reverse order. Each step and compensation is idempotent and persisted, so the saga can resume after a crash. The customer sees an order that failed cleanly, not a partial state.

## Quick recap

- Event sourcing stores history and rebuilds state by replay; use sealed types and exhaustive switches
- CQRS separates reads and writes; projections are eventually consistent
- Sagas replace distributed transactions with local steps and compensations
- Workflow engines like Temporal persist long-running processes
- Kafka Streams is embedded; Flink is a distributed engine; both handle stateful stream processing

**See also:** [Search and Analytics](search-analytics.md), [Machine Learning for Backend Engineers](ml-for-backend-engineers.md), [Distributed Tracing](../20-observability/distributed-tracing.md)
