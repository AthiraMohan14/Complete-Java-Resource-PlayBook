# Logging Configuration and Performance Tuning

Logs and performance problems often show up together: too much logging slows a request, and a slow request produces more logs. This page covers how to configure logging in a Spring Boot service and the main levers for tuning memory, threads, caches, and database access. The basics of SLF4J and Logback are in [Logging](logging.md), and the profiler workflow is in [JIT and Performance Tools](../03b-jvm-internals/jit-and-performance-tools.md).

## Core concepts

### Logging in Spring Boot

Spring Boot logs through SLF4J and uses Logback as the default backend. You can set levels in `application.yml` without writing any Logback XML.

```yaml
logging:
  level:
    root: INFO
    com.example.orders: DEBUG
    org.hibernate.SQL: DEBUG
```

Levels apply per package and inherit from the closest parent. Set `DEBUG` on one package when you are investigating, not on the root logger, because root-level DEBUG floods the log with framework output.

For anything more detailed (separate files, JSON layout, async appenders, rolling rules), put the configuration in `logback-spring.xml`. The Spring-aware `<springProfile>` element lets you use a different appender per environment. The appender and layout details are in [Logging](logging.md).

### Changing levels at runtime

Spring Boot Actuator can change a logger's level while the application runs, without a restart. Expose the `loggers` endpoint first.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: loggers
```

Then send a POST request to `/actuator/loggers/com.example.orders` with a body of `{"configuredLevel": "DEBUG"}`. Send `"configuredLevel": null` to return to the inherited level. Treat the endpoint as sensitive: expose it only on an internal port or behind authentication.

### Logging cost

A disabled log call is cheap, but its arguments are still evaluated. Two rules keep logging cheap.

- Use `{}` placeholders so the message is formatted only when the level is enabled.
- Guard arguments that are expensive to compute, such as a `toJson()` call on a large object.

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderHandler {

    private static final Logger log = LoggerFactory.getLogger(OrderHandler.class);

    void handle(String orderId, int lineCount) {
        // Cheap: the placeholder is formatted only if DEBUG is on
        log.debug("Handling order {} with {} lines", orderId, lineCount);

        // Expensive argument: guard the call so it runs only when DEBUG is on
        if (log.isDebugEnabled()) {
            log.debug("Order detail: {}", describeOrder(orderId));
        }
    }

    private String describeOrder(String orderId) {
        return "order-" + orderId; // Imagine a costly serialization here
    }
}
```

Do not put logging inside a tight loop that runs millions of times per second. Log the summary (the count, the total, the failed items) instead of every element.

### Correlation and sensitive data

A correlation ID in the MDC ties all log lines from one request together. Set it at the edge of the service, and clear it when the request ends, because threads in a pool are reused. The MDC is covered in [Logging](logging.md).

Never log secrets, tokens, passwords, or full card numbers. Mask values that you must record for support, for example by keeping only the last four characters of an account number.

### Memory and heap sizing

Setting `-Xms` equal to `-Xmx` avoids heap resizing during startup and load changes, which gives more predictable latency. The cost is that the memory is reserved up front, so a heap that is larger than needed wastes capacity.

```bash
java -Xms2g -Xmx2g -jar orders-service.jar
```

Inside containers, prefer a percentage of the container limit so the heap follows the memory the orchestrator allows.

```bash
java -XX:MaxRAMPercentage=75.0 -jar orders-service.jar
```

Choosing the right heap size is a measurement question. Use GC logs and heap usage after load testing, and see [Garbage Collection](../03b-jvm-internals/garbage-collection.md) for how collectors respond to heap size and pause goals.

### Thread pool tuning

Spring Boot creates a task executor for `@Async` methods and for the scheduler. The main settings control how many threads run and how many tasks wait.

```yaml
spring:
  task:
    execution:
      pool:
        core-size: 8
        max-size: 32
        queue-capacity: 200
    scheduling:
      pool:
        size: 4
```

A `ThreadPoolExecutor` creates threads above the core size only when the queue is full. This matters for `queue-capacity`. If the queue is effectively unbounded, the pool never grows past the core size, and work piles up in memory instead. If the queue is bounded and full, and the pool is at its maximum, new tasks are rejected. Choose the rejection behaviour on purpose.

Too few threads leave CPU and I/O idle. Too many cause context switching and memory use. Start from the number of cores for CPU-bound work, and measure for I/O-bound work, where more threads can help until the downstream system is the bottleneck.

Virtual threads (final in Java 21) change this trade-off for blocking I/O. A pool sized to hold many blocking tasks is less necessary when each task can run on its own virtual thread. Check your framework version before enabling them.

### Caching strategies

A cache stores the result of an expensive read so the next read is cheap. The write strategy decides how the cache and the database stay in step.

| Strategy | How it works | Trade-off |
|----------|--------------|-----------|
| Cache-aside (lazy loading) | The app checks the cache, and on a miss reads the database and fills the cache | Simple and common; the first read after a miss is slow, and data can be stale until it expires |
| Write-through | A write updates the cache and the database together, synchronously | Cache and database stay consistent; every write is slower |
| Write-behind (write-back) | A write updates the cache, and a background job writes to the database later | Fast writes; data can be lost if the cache fails before the write lands |

Spring's cache abstraction implements cache-aside with annotations. It needs `@EnableCaching` on a configuration class.

```java
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    @Cacheable(cacheNames = "users", key = "#id")
    public User findUser(long id) {
        return loadFromDatabase(id); // Runs only on a cache miss
    }

    @CachePut(cacheNames = "users", key = "#result.id()")
    public User updateUser(User user) {
        return saveToDatabase(user); // Always runs; refreshes the cache entry
    }

    @CacheEvict(cacheNames = "users", key = "#id")
    public void deleteUser(long id) {
        removeFromDatabase(id);
    }

    private User loadFromDatabase(long id) { return new User(id, "name"); }
    private User saveToDatabase(User user) { return user; }
    private void removeFromDatabase(long id) { }
}

record User(long id, String name) { }
```

The annotations work only for calls that pass through the Spring proxy. A method that calls `findUser` from inside the same class skips the cache. Caches in process (for example Caffeine) are fast but are not shared between instances. A shared store such as Redis is slower but consistent across instances. See [Spring Cache and Redis](../12-caching-performance/spring-cache-and-redis.md) and [Distributed Caching](../12-caching-performance/distributed-caching.md).

### Database access

Two problems cause most database slowness in Java services.

- **The N+1 problem.** Loading a list of parents and then touching a lazy association on each one runs one query for the list and one more per parent. Fix it with a join fetch or a batch load. The full example is in [Performance Optimisation](../12-caching-performance/performance-optimisation.md).
- **Missing indexes.** Add an index on columns that appear often in `WHERE` clauses, and check the query plan before you add more.

Connection pool size needs care. Each connection holds a database resource, and a pool that is too large overloads the database. A small pool is often faster than a large one. In Spring Boot with HikariCP, the setting is `spring.datasource.hikari.maximum-pool-size`, and the right value comes from load testing.

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 12
      minimum-idle: 3
```

### Object pooling and interning

Pool objects that are expensive to create and have no per-use state, such as database connections and thread pools. Do not pool cheap objects. The JVM allocates small objects quickly, and a pool adds synchronization and bookkeeping that can cost more than allocation.

`String.intern()` returns a canonical copy of a string from the JVM's string pool. It can reduce memory when the same strings repeat many times, but it is slower than a normal construction and the pool itself uses memory. Measure before you intern.

## How it works / Step by step

A practical tuning loop for a slow service:

1. Define the symptom: latency at the 99th percentile, CPU, memory, or throughput.
2. Measure with metrics and a profiler before changing anything. See [Metrics](metrics.md).
3. Find the bottleneck category using the table below.
4. Make one change and measure again. Keep the change only if the numbers improve.
5. Record the setting and the reason, so the next person does not revert it.

| Symptom | Likely cause | First thing to check |
|---------|--------------|----------------------|
| High latency under load | Blocking calls, slow queries, no cache | Database query count per request, downstream call timings |
| High CPU | Hot loops, excessive logging, GC work | Profiler output, log volume at DEBUG, GC logs |
| Memory growth | Leak, unbounded collections or caches, large payloads | Heap dump and retained-size analysis |
| Requests queue or are rejected | Thread pool or connection pool too small or unbounded | Pool metrics and queue depth |
| Network-heavy calls | Chatty APIs, large responses without compression | Number of calls per user action, response size |

## Common pitfalls

- **Tuning without a baseline.** A change that looks better may be noise. Record the numbers before the change.
- **DEBUG on the root logger in production.** It slows the service and fills the disk. Scope DEBUG to a package, and turn it off after the investigation.
- **Unbounded caches.** A cache without a size limit or expiry is a memory leak. Set both.
- **Caching with the wrong key.** Keys that include too much data reduce the hit rate; keys that include too little return wrong results.
- **Ignoring the self-invocation trap.** `@Cacheable` and `@Transactional` do not apply to calls made from inside the same class.
- **Large connection pools.** More connections can slow the database and the application at the same time.
- **Logging full objects.** Logging an entity can trigger lazy loading and expose sensitive fields.

!!! tip "Interview tip"
    "A service is slow under load. Where do you start?" Start with measurement, not a setting. Say that you check metrics for latency and pool usage, take a thread dump or profile, look at database query counts, and only then adjust pool sizes, heap, or caching. Name the N+1 problem as a common cause of slowness that tuning cannot fix.

## Quick recap

- Configure Spring Boot logging with `logging.level.*` and `logback-spring.xml`; change levels at runtime through Actuator's `loggers` endpoint.
- Use placeholders and guards to keep logging cheap, and never log secrets or PII.
- Set heap size on purpose; in containers, use a percentage of the memory limit.
- Thread pool and queue settings decide whether work runs, waits, or is rejected.
- Choose a cache write strategy by weighing consistency against write speed.
- Fix N+1 queries and size connection pools by measurement, not by guesswork.

**See also:** [Logging](logging.md), [Metrics](metrics.md), [Performance Optimisation](../12-caching-performance/performance-optimisation.md), [Garbage Collection](../03b-jvm-internals/garbage-collection.md), [Annotations and Reflection](../03c-tooling-utilities/annotations-and-reflection.md)
