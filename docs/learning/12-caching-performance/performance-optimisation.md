# Performance Optimisation

Performance work starts with measurement. Find the slowest part of the system under realistic load, confirm the cause with a profiler or metrics, change one thing, and measure again. Interviewers ask about this to see whether you optimise based on evidence. The most common real bottlenecks in Java backends are database access patterns and connection pools, not the JVM itself.

## Core concepts

### Measure before changing anything

Start with a baseline: response time percentiles (p95 or p99, not only averages), throughput, error rate, CPU, heap, and GC pauses. Change one variable at a time. A change that improves a microbenchmark can make the system slower under real load, because real load involves I/O, contention, and caches.

### Profilers and diagnostic tools

| Tool | Use |
|---|---|
| JFR (Java Flight Recorder) | Low-overhead recording of CPU, allocation, locks, and GC events; works in production |
| VisualVM | Standalone monitoring of heap, threads, and sampling |
| JProfiler, YourKit | Commercial profilers with rich UI and analysis |
| async-profiler | Low-overhead sampling profiler (CPU, allocation, locks) for Linux and macOS |
| JMH | Microbenchmarks; use only for isolated code, and read its guidance on pitfalls |

Thread dumps (`jstack` or the actuator thread dump endpoint) show blocked and waiting threads. They help find lock contention and stuck pools.

### Database query optimisation and the N+1 problem

The N+1 problem happens when code loads a list (one query) and then loads a related collection for each item (N more queries). It is hidden by lazy loading. A list of 100 customers can produce 101 queries.

```java
import java.util.List;
import jakarta.persistence.*;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

@Entity
class Customer {
    @Id
    @GeneratedValue
    Long id;

    String name;

    @OneToMany(mappedBy = "customer", fetch = FetchType.LAZY)
    List<CustomerOrder> orders;

    protected Customer() {}
}

@Entity
class CustomerOrder {
    @Id
    @GeneratedValue
    Long id;

    String item;

    @ManyToOne(fetch = FetchType.LAZY)
    Customer customer;

    protected CustomerOrder() {}
}

interface CustomerRepository extends JpaRepository<Customer, Long> {

    // One query that fetches customers and their orders together.
    @Query("select distinct c from Customer c left join fetch c.orders")
    List<Customer> findAllWithOrders();
}
```

Fixes, in order of preference: fetch only the columns you need (a DTO projection), fetch-join or `@EntityGraph` when you always need the relation, and batch fetching when you cannot avoid it. Make sure the SQL is visible in testing (`spring.jpa.show-sql` is for debugging only, and a statistics or query-count assertion is better for tests). Check indexes for the filters and sorts the queries use, and read execution plans with `EXPLAIN`.

Eager loading everywhere is not the fix. It loads data nobody reads and can still cause N+1 patterns through other paths.

### Connection pool sizing

Each request that talks to the database holds a connection. Spring Boot uses HikariCP by default, with a default maximum pool size of 10. A bigger pool does not make the database faster; past the database's capacity, more connections add queuing and contention. The HikariCP project suggests a small pool as a starting point, roughly based on CPU cores and disk parallelism, and recommends measuring instead of guessing.

Watch for these symptoms: threads waiting for a connection, slow requests with low database CPU, and timeouts during spikes. Keep transactions short so connections return to the pool quickly.

### JVM tuning

Most applications do not need manual JVM tuning. Start with defaults and measure.

- Heap size: set `-Xms` and `-Xmx` (or container-aware percentage flags) so the heap fits the available memory. Oversized heaps can produce long pauses; undersized heaps cause frequent GC.
- Garbage collector: G1 is the default on most server-class machines. CMS was removed in Java 14, so you will not find it in current JDKs. ZGC targets very low pause times, and its trade-offs should be measured for your workload.
- GC logs: enable them (`-Xlog:gc*`) to see pause times and allocation rates before tuning.
- Allocation: reducing short-lived allocation often helps more than GC flags.

Virtual threads, final in Java 21, help I/O-bound workloads handle many concurrent requests with less thread overhead. They do not speed up CPU-bound code, and they do not remove the need to limit pool sizes for shared resources such as database connections.

### Load testing

Load tools generate realistic traffic: Apache JMeter (broad protocol support), Gatling (Scala DSL, good reporting), and k6 (JavaScript scripts, developer-friendly). Test with realistic data volumes and request mixes, ramp load gradually, and watch the database, pools, and GC during the test, not only the response times.

### Where to look first

A simple order for investigating a slow endpoint:

1. Is the database slow or are there too many queries? Check query logs and query counts.
2. Are connections exhausted? Check pool metrics.
3. Is a downstream call slow? Check timeouts and tracing.
4. Is the CPU busy? Profile with JFR or async-profiler.
5. Is memory or GC the problem? Check GC logs.

## How it works / Step by step

1. Define a target (for example, p95 latency under a set value at a set throughput).
2. Load test with realistic data and capture metrics.
3. Profile the slowest path, identify the top cost, and confirm the cause.
4. Make one change (a query, an index, a pool size, a cache).
5. Repeat the load test and compare with the baseline.

## Common pitfalls

- Optimising code that is not on the critical path.
- Averages hiding tail latency; look at p95 and p99.
- Raising pool sizes to fix timeouts that a slow query actually causes.
- Enabling SQL logging in production, which slows the system and may log sensitive data.
- Running microbenchmarks without JMH and drawing conclusions from them.
- Adding indexes without checking write cost and the queries they serve.
- Assuming virtual threads remove the need for backpressure or pool limits.

!!! tip "Interview tip"
    **Q: An endpoint is slow. What do you do?**
    Confirm it is slow with metrics and a realistic test, then find where the time goes: database queries (count and duration), connection waits, downstream calls, CPU, or GC. Fix the largest cost first, typically the query pattern, and measure again. Mention N+1 queries and pool exhaustion as frequent findings.

## Quick recap

- Measure first; compare percentiles, not averages.
- N+1 queries come from lazy loading in loops; fix them with fetch joins, projections, or entity graphs.
- Keep pools small and transactions short; more connections are not always faster.
- Use JFR or async-profiler for CPU and allocation questions, and GC logs for pause questions.
- Load test with realistic data and watch the whole system.

**See also:** [Spring Cache and Redis](spring-cache-and-redis.md) | [Distributed Caching](distributed-caching.md) | [Databases and SQL](../06-databases-sql/index.md)
