# Architecture and Distributed Systems Questions

Questions on microservices, messaging with Kafka, distributed transactions, resilience, caching, and the basics of system design. For system design rounds, state your assumptions first, then sketch the components, then discuss the trade-offs.

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

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 2. How do you decide service boundaries, and why does each service own its data?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Find bounded contexts from Domain-Driven Design: areas of the business with their own language and rules, such as "ordering" and "billing". Each service owns its data, so other services reach that data through its API or its events, not through its tables. Shared databases couple services at the storage level, and a schema change in one breaks the others.

### Explanation
Signs of a bad boundary: two services that must change together for every feature, or one service that calls another for almost every request. Signs of a good one: a team can change most of its work without touching other services.

### When to use / pitfalls
- A shared "customer" table across services is a common source of hidden coupling. Let each service keep the fields it needs, copied through events.
- Reporting across services needs a separate read model or a data platform, not direct joins into other services' tables.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 3. When do you use synchronous calls and when do you use asynchronous messaging?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use synchronous calls (REST, gRPC, GraphQL) when the caller needs the answer to continue, such as a price lookup during checkout. Use asynchronous messaging (Kafka, RabbitMQ, SQS) when the caller only needs to hand off work or announce something happened, such as "order placed". Asynchronous messaging decouples availability and load, at the cost of eventual consistency and harder debugging.

### Explanation
A chain of synchronous calls is only as available as its weakest link: if five services each have 99.9% availability in series, the chain is roughly 99.5% available. Async handoffs keep the caller working when a downstream service is slow or down, as long as messages are stored durably.

### When to use / pitfalls
- Set timeouts on every synchronous call, or one slow dependency will hold threads across the whole system.
- gRPC suits internal, low-latency calls with strong contracts; REST suits public APIs that many clients consume.

**See also:** [Spring and security](spring-and-security-part-1.md)

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

Consumer offsets record how far each group has read. Kafka retains records for a configured time or size, independent of whether consumers read them, so consumers can replay.

### When to use / pitfalls
- Adding partitions changes the key-to-partition mapping for new records; plan partition counts up front.
- Ordering across different keys is not guaranteed. Do not design logic that needs global order.
- A single hot key sends all its traffic to one partition, which limits throughput for that key.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 5. What are Kafka delivery semantics, and how do you consume messages safely?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
At-most-once means a message can be lost but is never processed twice. At-least-once means it is never lost but may be processed more than once. Exactly-once, within Kafka itself, uses idempotent producers and transactions; end-to-end exactly-once with an external database still needs idempotent processing. Most systems use at-least-once and make consumers idempotent.

### Explanation
```java
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
class OrderEventListener {
    @KafkaListener(topics = "orders", groupId = "billing")
    void onOrder(String payload) {
        System.out.println("received: " + payload);
    }
}
```

An idempotent consumer records the IDs it has already handled, and skips duplicates:

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

The in-memory set is a demonstration only. In production, store the processed IDs in the same database transaction as the business change, so a crash cannot separate them.

### When to use / pitfalls
- With auto-commit offsets, a crash after commit but before processing loses the message. Commit offsets after processing when loss is unacceptable.
- Failed messages that retry forever block a partition. Send them to a dead-letter topic after a bounded number of attempts.
- Schema changes need compatibility rules (Avro, Protobuf, or JSON Schema with a registry).

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 6. What is the saga pattern, and what is the difference between choreography and orchestration?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A saga breaks a business transaction across services into local transactions, each followed by a compensating action if a later step fails. In choreography, services react to each other's events with no central controller. In orchestration, one coordinator service calls each step and decides what to compensate. Sagas give eventual consistency, not the isolation of a single ACID transaction.

### Explanation
A place-order saga: reserve stock, charge payment, create shipment. If payment fails, the saga releases the stock reservation (the compensation). Choreography suits a few steps with clear events. Orchestration suits longer flows where you need one place to see the state and handle timeouts, retries, and manual intervention. Workflow engines such as Temporal implement orchestration.

### When to use / pitfalls
- Compensations are not always exact undos: a refund is a new transaction, not a reversal. Design compensations as business actions.
- Make each step idempotent, because the saga engine will retry it.
- Other readers can see intermediate states. Show them as "pending" in the user interface.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 7. What is the transactional outbox pattern, and why is it needed?

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

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 8. What is the CAP theorem, and what does it mean in practice?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
CAP says that when a network partition happens between nodes in a distributed system, you must choose between consistency (every read sees the latest write, or an error) and availability (every request gets a non-error response, possibly stale). Partitions are a fact of networks, so partition tolerance is not optional in a distributed system; the real choice is between C and A while the partition lasts.

### Explanation
- CP systems refuse or delay some requests during a partition to keep data consistent. Coordination-heavy stores and leader-based systems often behave this way.
- AP systems keep answering during a partition, and reconcile later. Many caches and dynamic-replication stores behave this way.

CAP says nothing about behaviour when the network is healthy. The PACELC extension covers that: even without a partition, you trade latency against consistency.

### When to use / pitfalls
- Do not describe a database as "CA" in a distributed deployment; that choice only exists on one node.
- Choose per use case. A shopping cart can tolerate staleness; a payment ledger usually cannot.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 9. What consistency models should you know, and what does consensus do?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Strong consistency means every read returns the most recent write. Eventual consistency means replicas converge if writes stop, but reads may be stale in the meantime. Causal consistency keeps related operations in order for each observer. Consensus algorithms such as Raft and Paxos let a group of nodes agree on one value, such as the current leader or the next log entry, even when some nodes fail.

### Explanation
Raft elects a leader, and the leader replicates log entries; an entry is committed once a majority of nodes store it. This is why etcd and similar coordination services run with an odd number of nodes, usually three or five.

You rarely implement consensus yourself. You choose a system that provides it, and you check its failure behaviour.

### When to use / pitfalls
- Eventual consistency needs a plan for conflicting updates: last-write-wins, version vectors, or business rules.
- A "read your own writes" requirement often needs routing reads to the primary, or waiting for replicas.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 10. How do you make a service call resilient?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Combine these tools: a timeout on every call, retries with exponential backoff and jitter for transient failures, a circuit breaker that stops calling a failing dependency, and a bulkhead that limits concurrent calls so one dependency cannot exhaust all threads. Hystrix is retired; use Resilience4j in Spring applications.

### Explanation
A circuit breaker has three states. Closed: calls pass through and failures are counted. Open: calls fail fast without reaching the dependency. Half-open: a few trial calls test whether it has recovered.

```java
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Supplier;

class Retry {
    static <T> T withBackoff(Supplier<T> call, int maxAttempts) throws InterruptedException {
        long delayMs = 100;
        for (int attempt = 1; ; attempt++) {
            try {
                return call.get();
            } catch (RuntimeException e) {
                if (attempt >= maxAttempts) {
                    throw e;
                }
                long jitter = ThreadLocalRandom.current().nextLong(delayMs / 2 + 1);
                Thread.sleep(delayMs + jitter);       // jitter spreads retries out
                delayMs = Math.min(delayMs * 2, 5_000);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println(withBackoff(() -> "ok", 3));
    }
}
```

### When to use / pitfalls
- Retry only idempotent operations, or operations that carry an idempotency key.
- Retries multiply load during an outage. Combine them with a circuit breaker and a retry budget.
- Pair timeouts with deadline propagation so a request does not keep working after the caller gave up.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 11. How do rate limiters work, and what is a token bucket?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A token bucket holds up to a fixed number of tokens and refills at a steady rate. Each request takes one token; if none is available, the request is rejected or delayed. This allows short bursts up to the bucket size while keeping the average rate fixed. Sliding window counters are another common approach with smoother limits.

### Explanation
```java
class TokenBucket {
    private final long capacity;
    private final double refillPerSecond;
    private double tokens;
    private long lastNanos;

    TokenBucket(long capacity, double refillPerSecond) {
        this.capacity = capacity;
        this.refillPerSecond = refillPerSecond;
        this.tokens = capacity;
        this.lastNanos = System.nanoTime();
    }

    synchronized boolean tryAcquire() {
        long now = System.nanoTime();
        double elapsedSeconds = (now - lastNanos) / 1_000_000_000.0;
        tokens = Math.min(capacity, tokens + elapsedSeconds * refillPerSecond);
        lastNanos = now;
        if (tokens >= 1) {
            tokens -= 1;
            return true;
        }
        return false;
    }

    public static void main(String[] args) {
        TokenBucket bucket = new TokenBucket(2, 1.0);
        System.out.println(bucket.tryAcquire()); // true
        System.out.println(bucket.tryAcquire()); // true
        System.out.println(bucket.tryAcquire()); // false: bucket is empty
    }
}
```

### When to use / pitfalls
- In a cluster, a per-instance limit is not a global limit. Use a shared store such as Redis, with an atomic script, for a global limit.
- Return `429 Too Many Requests` with a `Retry-After` header when you reject.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 12. What caching strategies exist, and how do you invalidate a cache?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
In cache-aside, the application reads the cache first, loads from the database on a miss, and fills the cache. Write-through writes to the cache and the database together, so the cache is always current. Write-behind writes to the cache first and flushes to the database later, which is fast but risks loss. Invalidation is the hard part: delete or update the cached entry when the source changes, and set a TTL as a safety net.

### Explanation
```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

class ProductCache {
    private final Map<String, String> cache = new ConcurrentHashMap<>();

    String get(String id) {
        String value = cache.get(id);
        if (value == null) {
            value = loadFromDatabase(id);     // cache-aside: load on a miss...
            cache.put(id, value);             // ...then fill the cache
        }
        return value;
    }

    void onProductChanged(String id) {
        cache.remove(id);                                            // invalidate on write
    }

    private String loadFromDatabase(String id) {
        return "row for " + id;                                      // placeholder for a query
    }
}
```

In Spring, `@Cacheable`, `@CachePut`, and `@CacheEvict` implement these patterns on methods.

### When to use / pitfalls
- A cache stampede happens when a popular key expires and many requests reload it at once. Use request coalescing, staggered TTLs, or a lock per key.
- `computeIfAbsent` runs its function while holding a lock on the map bin. Do not make slow remote calls inside it in production code; load outside the map and then put the value.
- Cache keys must include every input that changes the result, such as the tenant or locale.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 13. What is the difference between Layer 4 and Layer 7 load balancing, and what is consistent hashing?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A Layer 4 load balancer routes by transport information (IP address and port) and does not read the request. A Layer 7 load balancer reads the application protocol, such as HTTP headers and paths, so it can route by URL, host, or cookie. Consistent hashing maps keys and servers onto a ring, so adding or removing a server moves only a small share of keys.

### Explanation
With plain modulo hashing (`hash(key) % servers`), changing the number of servers remaps almost every key, which empties caches. With consistent hashing, each server owns an arc of the ring, and a new server takes only the keys from its neighbour's arc. Virtual nodes spread the load more evenly.

### When to use / pitfalls
- Layer 7 costs more CPU per request than Layer 4.
- Sticky sessions tie a user to one server, which hurts failover. Prefer stateless services with shared session storage such as Redis.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 14. How do you scale a database for a growing system?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Start by tuning queries and indexes, then add a cache for hot reads. Add read replicas to scale reads, accepting some replication lag. Partition large tables inside the database for maintenance. Shard across servers only when one primary can no longer handle writes or the data size, and then choose a shard key that matches the main access pattern.

### Explanation
Order of work, cheapest first:

1. Fix slow queries and missing indexes (`EXPLAIN`).
2. Cache hot reads in Redis or in memory.
3. Add read replicas and route read-only traffic to them.
4. Partition large tables by time or range.
5. Shard by key, with a routing layer or a shard map.

OLTP workloads (short transactions) and OLAP workloads (large scans and aggregates) often move to separate stores. Send analytics to a warehouse or a replica built for it.

### When to use / pitfalls
- Cross-shard joins and transactions are expensive or unsupported. Design the shard key to keep related data together.
- Resharding later is slow. Plan the key before the data grows.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 15. What are event sourcing and CQRS, and when do they fit?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Event sourcing stores the sequence of events that changed an entity, and rebuilds current state by replaying them. CQRS (Command Query Responsibility Segregation) separates the write model, which handles commands and enforces rules, from read models built for queries. The two often appear together, but each can be used alone.

### Explanation
A ledger is a natural event store: each deposit and withdrawal is recorded, and the balance is derived. Read models are updated from events asynchronously, so queries see eventually consistent data. Event versioning matters, because old events remain in the store forever; you handle changes with upcasting, which converts old event formats when they are read.

### When to use / pitfalls
- Both add real complexity. Use them where audit history or very different read and write shapes justify the cost, not for ordinary CRUD.
- Replaying a long history is slow; take snapshots.
- Changing an event's meaning later is hard. Treat events as public contracts.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 16. Why do POST requests need idempotency keys?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A `POST` is not idempotent: repeating it may create two orders or two payments. When a client times out and retries, it cannot tell whether the first request succeeded. An idempotency key, a unique value the client sends with each logical operation, lets the server recognise and replay the earlier result instead of processing the request again.

### Explanation
The server stores the key with the outcome, in the same transaction as the business change. A second request with the same key returns the stored response. Keys should be scoped to a client, and expire after a reasonable time. Many payment and order APIs use this pattern.

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

class PaymentApi {
    private final Map<String, String> results = new ConcurrentHashMap<>();

    String charge(String idempotencyKey, long cents) {
        return results.computeIfAbsent(idempotencyKey, k -> "charged " + cents + " cents");
    }

    public static void main(String[] args) {
        PaymentApi api = new PaymentApi();
        System.out.println(api.charge("key-1", 500));   // charged
        System.out.println(api.charge("key-1", 500));   // same result, no second charge
    }
}
```

The in-memory map is a demonstration. Real storage must survive restarts and be shared by all instances.

### When to use / pitfalls
- Reusing a key with a different request body should return an error, not the old result.
- Idempotency keys complement, not replace, unique constraints in the database.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 17. How would you design a URL shortener?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Start with requirements: create short links, redirect quickly, and collect click counts. Estimate the scale, for example writes per second and reads per second, and the storage per link. Generate a unique ID per link, encode it in base62 to get a short code, store the mapping in a key-value store, and cache the hot redirects. Count clicks asynchronously so redirects stay fast.

### Explanation
A seven-character base62 code gives 62^7 (about 3.5 trillion) possible values. Generate the code from a numeric ID, which avoids collisions by construction:

```java
class Base62 {
    private static final String ALPHABET =
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

    static String encode(long id) {
        if (id == 0) {
            return "0";
        }
        StringBuilder sb = new StringBuilder();
        while (id > 0) {
            sb.append(ALPHABET.charAt((int) (id % 62)));
            id /= 62;
        }
        return sb.reverse().toString();
    }

    public static void main(String[] args) {
        System.out.println(encode(125));   // "21"
    }
}
```

Components to draw: an API service for create and redirect; a key-value store for the mapping (reads far outnumber writes); a cache in front of it; a unique ID source (a database sequence or a range allocator per server); and an analytics pipeline that consumes click events from a queue.

### When to use / pitfalls
- Sequential IDs reveal how many links you have created. Obfuscate the code if that matters.
- Decide on link expiry, custom aliases, and whether a redirect should be 301 (cacheable by browsers) or 302 (lets you count every click).
- Validate target URLs to prevent the service being used for phishing or SSRF.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## Quick recap

- Monoliths are often the right first step; split along bounded contexts.
- Each service owns its data; share state through APIs and events.
- Ordering exists only within a Kafka partition; design consumers to be idempotent.
- Use sagas with compensations, and the outbox pattern to avoid dual writes.
- CAP is a choice during a partition; resilience is timeouts, retries with jitter, circuit breakers, and bulkheads.
- Cache-aside with explicit invalidation and TTLs is the usual starting point.

**See also:** [Spring and security](spring-and-security-part-1.md), [Data and persistence](data-and-persistence-part-1.md), [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)
