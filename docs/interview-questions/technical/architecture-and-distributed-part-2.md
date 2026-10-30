# Architecture and Distributed Systems Questions (Part 2 of 3)

Questions on system design approach, service discovery, resilience, CAP and consistency, caching, load balancing, scaling the database, event sourcing, idempotency, and a worked design. Part 1 covers microservices, messaging, and distributed transactions. For system design rounds, state your assumptions first, then sketch the components, then discuss the trade-offs.

Continued in [Part 3](architecture-and-distributed-part-3.md): monorepo or multi-repo, architecture styles, and designing an issue tracker.

---

## 12. Walk me through how you would tackle an open-ended system design question.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Work through the problem in order: clarify the functional requirements, set the non-functional targets (latency, throughput, availability, consistency), estimate the scale, sketch the high-level components and the main API, deep-dive into the hardest part, and then discuss trade-offs. Say your assumptions out loud, because the reasoning is what interviewers score.

### Explanation
A worked estimate shows the habit. Suppose 10 million daily active users each make two requests a day. That is 20 million requests a day, which is about 230 requests per second on average (20,000,000 divided by 86,400 seconds). If peak traffic is about three times the average, plan for roughly 700 requests per second. Those numbers decide whether one database can serve the load, whether a cache is needed, and how many instances to plan for. Label such numbers as assumptions and change them when the interviewer changes the scale.

The usual order is:

1. Requirements: what the system does, and for whom.
2. Non-functional targets: latency, availability, consistency, durability.
3. Estimates: requests per second, storage, bandwidth, read-to-write ratio.
4. High-level design: clients, gateway, services, data stores, queues, caches.
5. Deep dive: the component with the hardest constraint.
6. Trade-offs: what you chose, what you gave up, and what would change at larger scale.

### When to use / pitfalls
- Starting with components before requirements. A design built on wrong assumptions wastes the session.
- Presenting estimates as facts. Say "assuming".
- Recommending a monolith first, then scaling out, is a sound answer when the requirements do not justify more. Explain why.

**See also:** [Practice problems](../../learning/19-system-design-fundamentals/practice-problems.md), [High-level design](../../learning/19-system-design-fundamentals/high-level-design.md)

</details>

---

## 13. A caller needs a service whose addresses keep changing. How does it find the right instance?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Service discovery lets a caller find the current addresses of a service by name. Instances register when they start and are removed when they stop or fail health checks. Without discovery, clients hard-code addresses that break when instances move, scale out, or are replaced during a deployment. Discovery is provided by a registry such as Eureka or Consul, or by the platform, such as Kubernetes DNS.

### Explanation
With client-side discovery, the caller queries the registry and picks an instance. With server-side discovery, the caller sends requests to a load balancer, which does the lookup. In Spring Cloud, a load-balanced client resolves a logical name:

```java
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
class PaymentClientConfig {

    @Bean
    @LoadBalanced
    WebClient.Builder loadBalancedBuilder() {
        return WebClient.builder();
    }
}
```

With this configuration, a call to `http://payment-service/...` uses the name, not a host. In Kubernetes, the same name works through a Service object and its DNS record.

### When to use / pitfalls
- Registry entries can be stale for a short time after a crash. Pair discovery with timeouts, retries, and a circuit breaker.
- Eureka can keep dead entries during a network partition (self-preservation). That protects against a mass false removal, but it means some calls go to dead instances for a while.
- In Kubernetes, the platform already provides discovery, so a separate registry is rarely needed.

**See also:** [Service discovery](../../learning/14-microservices/service-discovery.md), [Spring Cloud](../../learning/14-microservices/spring-cloud.md)

</details>

---

## 14. What is a bulkhead, and how does it differ from a circuit breaker?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A bulkhead limits how many resources one dependency may use at once, such as concurrent calls, threads in a pool, or connections. It is named after the compartments in a ship: if one compartment floods, the others stay dry. A circuit breaker watches the outcomes of calls to a dependency and stops calling it when failures pass a threshold. The bulkhead limits the damage from slowness and load; the circuit breaker stops calls to something that is failing. They are often used together.

### Explanation
Without bulkheads, one slow dependency can hold every thread in a shared pool, so calls to healthy dependencies also fail. With a bulkhead, the slow dependency can fill only its own share. Resilience4j provides the pattern as an annotation, which needs Spring AOP on the classpath:

```java
import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import org.springframework.stereotype.Service;

@Service
class InventoryClient {

    @Bulkhead(name = "inventory")   // at most max-concurrent-calls in flight for this name
    public String stockFor(String sku) {
        return "in stock: " + sku;  // a remote call would go here
    }
}
```

```yaml
resilience4j:
  bulkhead:
    instances:
      inventory:
        max-concurrent-calls: 10
        max-wait-duration: 0
```

A bulkhead that is full can reject calls at once, which is usually better than queuing callers until they time out.

### When to use / pitfalls
- A semaphore bulkhead limits concurrency on the calling thread, but it cannot interrupt a call that is already blocked. A thread-pool bulkhead can.
- Size each bulkhead from the dependency's real capacity, not from the default.
- A bulkhead alone does not stop retries from piling onto a failing service. Add a circuit breaker and a timeout.

**See also:** [Resilience patterns](../../learning/14-microservices/resilience-patterns.md)

</details>

---

## 15. What is the CAP theorem, and what does it mean in practice?

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

**See also:** [Core concepts](../../learning/19-system-design-fundamentals/core-concepts.md), [Replication, sharding, and NoSQL](../../learning/19-system-design-fundamentals/replication-sharding-nosql.md)

</details>

---

## 16. What consistency models should you know, and what does consensus do?

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

**See also:** [Replication, sharding, and NoSQL](../../learning/19-system-design-fundamentals/replication-sharding-nosql.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 17. How do you make a service call resilient?

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

**See also:** [Resilience patterns](../../learning/14-microservices/resilience-patterns.md), [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 18. How do rate limiters work, and what is a token bucket?

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

**See also:** [High-level design](../../learning/19-system-design-fundamentals/high-level-design.md), [Spring and security](spring-and-security-part-1.md)

</details>

---

## 19. What caching strategies exist, and how do you invalidate a cache?

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
        cache.remove(id);                     // invalidate on write
    }

    private String loadFromDatabase(String id) {
        return "row for " + id;               // placeholder for a query
    }
}
```

In Spring, `@Cacheable`, `@CachePut`, and `@CacheEvict` implement these patterns on methods.

### When to use / pitfalls
- A cache stampede happens when a popular key expires and many requests reload it at once. Use request coalescing, staggered TTLs, or a lock per key.
- `computeIfAbsent` runs its function while holding a lock on the map bin. Do not make slow remote calls inside it in production code; load outside the map and then put the value.
- Cache keys must include every input that changes the result, such as the tenant or locale.

**See also:** [Caching and performance](../../learning/12-caching-performance/index.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 20. What is the difference between Layer 4 and Layer 7 load balancing, and what is consistent hashing?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A Layer 4 load balancer routes by transport information (IP address and port) and does not read the request. A Layer 7 load balancer reads the application protocol, such as HTTP headers and paths, so it can route by URL, host, or cookie. Consistent hashing maps keys and servers onto a ring, so adding or removing a server moves only a small share of keys.

### Explanation
With plain modulo hashing (`hash(key) % servers`), changing the number of servers remaps almost every key, which empties caches. With consistent hashing, each server owns an arc of the ring, and a new server takes only the keys from its neighbour's arc. Virtual nodes spread the load more evenly.

### When to use / pitfalls
- Layer 7 costs more CPU per request than Layer 4.
- Sticky sessions tie a user to one server, which hurts failover. Prefer stateless services with shared session storage such as Redis.

**See also:** [High-level design](../../learning/19-system-design-fundamentals/high-level-design.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 21. How do you scale a database for a growing system?

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
- A shard key with few distinct values creates hot shards.

**See also:** [Replication, sharding, and NoSQL](../../learning/19-system-design-fundamentals/replication-sharding-nosql.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 22. What are event sourcing and CQRS, and when do they fit?

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

**See also:** [Event-driven architecture](../../learning/13-messaging/event-driven-architecture.md)

</details>

---

## 23. Why do POST requests need idempotency keys?

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

**See also:** [Spring and security](spring-and-security-part-1.md), [Replication, sharding, and NoSQL](../../learning/19-system-design-fundamentals/replication-sharding-nosql.md)

</details>

---

## 24. How would you design a URL shortener?

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

**See also:** [Practice problems](../../learning/19-system-design-fundamentals/practice-problems.md), [Spring and security](spring-and-security-part-1.md)

</details>

---

## Quick recap

- Approach a design in order: requirements, targets, estimates, components, deep dive, trade-offs.
- Discovery finds live instances by name; bulkheads and circuit breakers contain failures; retries need jitter and idempotency.
- CAP is a choice during a partition; consistency models and consensus describe what a read may see.
- Caching, sharding, and replication scale reads and writes, each with a cost to consistency or operations.
- Idempotency keys make retried writes safe; event sourcing and CQRS fit audit-heavy or read-heavy designs.

**See also:** [Architecture and distributed systems, part 1](architecture-and-distributed-part-1.md), [Spring and security](spring-and-security-part-1.md), [Data and persistence](data-and-persistence-part-1.md), [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)
