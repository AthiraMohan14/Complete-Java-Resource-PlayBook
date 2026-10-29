# High-Level Design

High-level design (HLD) describes the main components of a system, how they communicate, and where data lives. Interviewers expect you to choose an architecture style, place load balancers, caches, databases, queues, and CDNs, and justify each choice. This page covers the common building blocks and the trade-offs that decide between them.

## Core concepts

### Architecture styles
- **Layered (N-tier)**: presentation, business logic, and data access in separate layers. Simple to understand, and it is the usual starting point for a monolith.
- **MVC**: model, view, and controller separate the data, the presentation, and the input handling. It describes the structure of a web application more than a deployment shape.
- **Microservices**: independently deployed services, each owning its data. They allow independent scaling and team autonomy, at the cost of network calls, distributed data, and operational overhead.
- **Event-driven**: components communicate by publishing and consuming events through a broker. They decouple producers from consumers and make asynchronous processing natural.
- **Lambda architecture**: a batch layer and a speed layer process the same data, and a serving layer merges the results. It was designed for combining complete historical batch results with fast, approximate real-time results.

Start with the simplest style that meets the requirements. A modular monolith is often a better starting point than microservices.

### Load balancing
A load balancer distributes requests across healthy instances.

| Algorithm | How it chooses | Suits |
|---|---|---|
| Round-robin | Next server in turn | Similar servers, similar requests |
| Least connections | Server with the fewest active connections | Requests with uneven duration |
| Weighted | Servers with higher weight get more traffic | Mixed hardware capacity |
| IP hash | Hash of the client IP | Simple session affinity |
| Consistent hashing | Position on a hash ring | Caches and sharded stores that must move few keys when nodes change |

**Layer 4** load balancers route on transport information such as IP and port, which is fast and simple. **Layer 7** load balancers read application data such as HTTP headers and paths, which allows smarter routing and TLS termination at the cost of more processing.

Consistent hashing is worth knowing in code. The ring maps both servers and keys to positions, and each key goes to the next server clockwise. Adding a server moves only a fraction of keys:

```java
import java.util.SortedMap;
import java.util.TreeMap;

public class HashRing {
    private final TreeMap<Integer, String> ring = new TreeMap<>();

    public void addServer(String server) {
        ring.put(server.hashCode(), server);
    }

    public String serverFor(String key) {
        if (ring.isEmpty()) {
            throw new IllegalStateException("no servers on the ring");
        }
        SortedMap<Integer, String> tail = ring.tailMap(key.hashCode());
        Integer position = tail.isEmpty() ? ring.firstKey() : tail.firstKey();
        return ring.get(position);
    }

    public static void main(String[] args) {
        HashRing ring = new HashRing();
        ring.addServer("cache-a");
        ring.addServer("cache-b");
        System.out.println("user:42 goes to " + ring.serverFor("user:42"));
    }
}
```

Production rings add many virtual nodes per server to spread keys more evenly. This sketch omits that.

### Caching
A cache stores frequently read data closer to the caller. Three common write patterns:

- **Cache-aside**: the application reads the cache first; on a miss it loads from the database and fills the cache. Writes go to the database and the entry is invalidated or updated.
- **Write-through**: writes go to the cache and the database synchronously. Reads are consistent with the cache, but writes are slower.
- **Write-behind** (write-back): writes go to the cache and are persisted asynchronously. It is fast but risks losing data if the cache fails before the flush.

**TTL** (time to live) bounds how long an entry can be stale. **Invalidation** is the harder part: deleting or updating entries when the source changes, and handling races between readers and writers. A distributed cache such as a **Redis cluster** shares the cache across application instances and partitions keys across nodes.

```java
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

public class CacheAside<K, V> {
    private final Map<K, V> cache = new ConcurrentHashMap<>();
    private final Function<K, V> database;

    public CacheAside(Function<K, V> database) {
        this.database = database;
    }

    public V get(K key) {
        return Optional.ofNullable(cache.get(key))
                .orElseGet(() -> {
                    V value = database.apply(key);   // miss: load from the source of truth
                    cache.put(key, value);
                    return value;
                });
    }

    public void onUpdate(K key) {
        cache.remove(key);                           // invalidate on write
    }
}
```

This in-memory version has no TTL and no size bound. A real cache adds both, and a distributed cache is needed when several instances must share entries.

### Database scaling
- **Read replicas** copy data from a primary and serve reads. They scale read-heavy workloads, but replicas lag behind the primary, so reads after a write may be stale.
- **Sharding** splits data across several databases. Common strategies are **range** (by key range, simple but can create hot spots), **hash** (even spread, but range queries get harder), and **consistent hashing** (adding shards moves few keys).
- **Shard key choice** determines whether load spreads evenly. A key with many accesses concentrated on a few values creates hot shards.
- **Cross-shard queries** need scatter-gather or a separate read model, and cross-shard transactions are costly.
- **Primary-replica** (master-slave) replication has one writer. **Multi-primary** (master-master) accepts writes in several places and must resolve conflicts.

### Message queues
Queues decouple producers from consumers and turn slow work into asynchronous tasks. A producer enqueues a message and returns; workers consume at their own pace. Queues smooth traffic spikes, allow retries, and distribute tasks across workers. They also mean the caller no longer knows when the work finished, so design for eventual completion and idempotent consumers.

### CDNs
A **content delivery network** caches static and cacheable content at edge locations near users. Benefits include lower latency, reduced origin load, and built-in protection against some traffic spikes. Compression and cache headers improve the effect. Dynamic, personalised responses are harder to cache and need careful rules.

### Synchronous versus asynchronous communication
A synchronous call waits for the response, so the caller's latency includes the callee's work, and a slow callee slows the caller. An asynchronous message returns immediately, so the caller is decoupled, but the result arrives later and the caller must handle that. Use synchronous calls where the user needs the answer now, such as showing a price. Use asynchronous work where the user does not wait, such as sending a confirmation email or updating a search index.

### OLTP versus OLAP
- **OLTP** (online transaction processing) handles many small, concurrent transactions, such as placing orders. It favours normalised schemas, indexes for point lookups, and strong consistency.
- **OLAP** (online analytical processing) runs large scans and aggregations for reporting. It favours denormalised or columnar storage and is often fed by a copy of the transactional data.

Keep analytics off the transactional database. Replicate or stream changes into an analytical store so long reports do not slow checkout.

## How it works / Step by step
Designing the path of a read request in a typical web system:
1. A DNS entry and a CDN serve static assets from the edge.
2. A Layer 7 load balancer routes the API call to a healthy service instance.
3. The service checks a distributed cache; on a miss it reads a replica or the shard that owns the key.
4. Writes go to the primary or the correct shard, and an event is published to a queue.
5. Consumers update derived data, such as search indexes or analytics stores, asynchronously.

## Common pitfalls
- Adding microservices before the team and the domain need them.
- Caching without a plan for invalidation, which serves stale data indefinitely.
- Choosing a shard key that concentrates traffic on one shard.
- Reading from a replica immediately after a write and expecting to see it.
- Sending analytical queries to the primary transactional database.
- Assuming a queue gives exactly-once processing. Design consumers to be idempotent.

!!! tip "Interview tip"
    **Q: How would you scale the read path of a product catalogue?**
    Put a CDN in front of cacheable pages and images, add a distributed cache with cache-aside and a TTL, and serve remaining reads from replicas. Name the consistency trade-off: a price change may take the TTL to appear, so decide whether that is acceptable or whether writes must invalidate the cache.

## Quick recap
- Pick an architecture style that matches the team and domain; start simple.
- Load balancers choose algorithms and layers; consistent hashing minimises key movement.
- Cache-aside, write-through, and write-behind trade freshness, speed, and durability.
- Replicas scale reads with lag; sharding scales writes with hot-spot and cross-shard costs.
- Queues decouple work; CDNs serve edge content; keep OLTP and OLAP apart.

**See also:** [Core Concepts](core-concepts.md), [Low-Level Design](low-level-design.md), [Practice Problems](practice-problems.md), [Redis and Caching](../12-caching-performance/index.md)
