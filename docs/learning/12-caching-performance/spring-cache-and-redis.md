# Spring Cache Abstraction and Redis

Spring's cache abstraction lets you add caching to methods with annotations, while a `CacheManager` decides where the data lives. Redis is a common backing store: an in-memory data-structure server that many instances can share. Interviewers ask about this to see whether you know how caching interacts with transactions and invalidation, and whether you understand what Redis can and cannot guarantee.

## Core concepts

### Enabling caching

Add `@EnableCaching` to a configuration class, and a cache starter (or `spring.cache.type`) to choose the provider. Without a provider, Spring falls back to a simple in-memory map that has no size limit or expiry, which is rarely what production needs.

```java
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableCaching
class CacheConfig {
}
```

### @Cacheable, @CachePut, and @CacheEvict

- `@Cacheable` returns the cached value if present; otherwise it runs the method and stores the result.
- `@CachePut` always runs the method and updates the cache with the result.
- `@CacheEvict` removes entries. `allEntries = true` clears the whole cache.
- `@Caching` groups several of these on one method.

```java
import java.util.Optional;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

record Product(long id, String name, long priceCents) {}

interface ProductRepository {
    Optional<Product> findById(long id);
    Product save(Product product);
    void deleteById(long id);
}

@Service
class ProductService {

    private final ProductRepository repository;

    ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Cacheable(cacheNames = "products", key = "#id", unless = "#result == null")
    public Product findById(long id) {
        return repository.findById(id).orElse(null);
    }

    @CachePut(cacheNames = "products", key = "#result.id()")
    public Product update(Product product) {
        return repository.save(product);
    }

    @CacheEvict(cacheNames = "products", key = "#id")
    public void delete(long id) {
        repository.deleteById(id);
    }
}
```

`unless = "#result == null"` stops Spring caching "not found" results, so a later insert is visible immediately. Caching nulls can hide new data behind a stale miss.

Conditional caching uses `condition` (decided before the call, can use arguments) and `unless` (decided after, can use the result):

```java
import org.springframework.cache.annotation.Cacheable;

@Cacheable(cacheNames = "products", key = "#id", condition = "#id > 0")
public Product findCached(long id) {
    return repository.findById(id).orElse(null);
}
```

### Cache keys

By default, Spring builds a key from the method arguments (`SimpleKeyGenerator`). A single argument is used as the key itself; several arguments form a composite key. Set `key` with SpEL for control, such as `key = "#customerId + ':' + #page"`. Write a custom `KeyGenerator` bean when keys follow a shared rule across many methods. Key expressions that include mutable objects or inconsistent `toString()` output cause silent misses.

### Cache managers

`CacheManager` implementations include `ConcurrentMapCacheManager` (in-memory, simple, no eviction), `SimpleCacheManager` (you register the caches yourself), and `CompositeCacheManager` (tries several managers in order). Production setups usually use a library such as Caffeine for local memory caching, or Redis for a shared cache.

### Redis as a cache

Set `spring.cache.type=redis` (with the Redis starter) and configure TTLs per cache with a `RedisCacheManager`:

```java
import java.time.Duration;
import org.springframework.cache.CacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;

@Configuration
class RedisCacheConfig {

    @Bean
    CacheManager cacheManager(RedisConnectionFactory connections) {
        RedisCacheConfiguration defaults = RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(10))
                .disableCachingNullValues();
        return RedisCacheManager.builder(connections)
                .cacheDefaults(defaults)
                .build();
    }
}
```

A TTL is the main protection against stale data when an update path forgets to evict. Choose it from how stale the data is allowed to be, not from how often you expect it to change.

### Redis data structures

| Structure | Typical use |
|---|---|
| Strings | Cached values, counters (`INCR`), flags |
| Lists | Queues, recent-activity feeds |
| Sets | Unique membership, tags |
| Hashes | Objects with several fields (a user profile) |
| Sorted sets | Leaderboards, time-ordered indexes |
| Streams | Append-only logs with consumer groups |
| Bitmaps | Compact flags such as daily active users |

Spring Data Redis exposes these through `StringRedisTemplate` (string keys and values) and `RedisTemplate` (typed serialisation). For simple string values, `StringRedisTemplate` is clearer.

```java
import java.time.Duration;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
class SessionFlags {

    private final StringRedisTemplate redis;

    SessionFlags(StringRedisTemplate redis) {
        this.redis = redis;
    }

    void markSeen(String userId) {
        redis.opsForValue().set("seen:" + userId, "1", Duration.ofHours(1));
    }

    boolean wasSeen(String userId) {
        return redis.hasKey("seen:" + userId);
    }
}
```

### Sessions, pub/sub, streams, and locks

- Spring Session with Redis stores HTTP sessions in Redis, so any instance can serve any user. Add `spring-session-data-redis`.
- Pub/sub delivers messages to current subscribers only. Nothing is stored, so offline subscribers miss messages.
- Redis Streams store entries and let consumer groups read and acknowledge them, which is closer to a durable queue.
- Distributed locks coordinate work across instances. A single-instance lock with `SET key value NX PX` is common. Redlock extends the idea across several Redis nodes, but it is debated, and it does not replace fencing tokens in a strict correctness setting. Use Lua scripts when several commands must be atomic.

### Persistence and clustering

Redis keeps data in memory. Persistence options are RDB snapshots (periodic point-in-time copies) and AOF (an append-only log of writes, replayed on restart). Both trade durability for speed differently. Replication copies data to replicas; Redis Cluster shards keys across nodes. Treat a cache as losable, and treat Redis as a durable store only with a deliberate persistence and failover design.

## How it works / Step by step

1. A `@Cacheable` method is called through the Spring proxy.
2. The proxy builds the key and checks the cache.
3. On a hit, the cached value is returned and the method body does not run.
4. On a miss, the method runs, the result passes the `unless` check, and the value is stored with its TTL.
5. `@CacheEvict` or `@CachePut` changes entries when data changes.

## Common pitfalls

- Self-invocation: calling a cached method from within the same class bypasses the proxy, so caching silently does nothing.
- Forgetting to evict on every write path, including batch jobs and direct repository writes.
- Caching mutable objects and then modifying them, which changes the cached copy.
- Serialisation changes after a deploy, which make old cache entries unreadable. Version your cache names or keys.
- Using `@Cacheable` on methods that depend on the current user without including the user in the key.
- Assuming pub/sub is durable. Use Streams or a broker when messages must not be lost.
- Non-atomic Redis sequences, such as `INCR` followed by `EXPIRE` in separate calls, which can leave keys without a TTL if the process dies between them.

!!! tip "Interview tip"
    **Q: Why might `@Cacheable` not seem to work?**
    The most common cause is self-invocation: the call goes directly to the method on `this`, so there is no proxy to intercept it. Other causes are a missing `@EnableCaching`, a method that is not public (depending on proxy mode), or a key that never matches. Move the cached method to another bean, or call it through the proxy.

## Quick recap

- `@Cacheable`, `@CachePut`, and `@CacheEvict` add caching through the proxy; watch for self-invocation.
- Use `condition` and `unless` to control what is cached; avoid caching misses that hide new data.
- Set TTLs on Redis caches as a safety net for missed evictions.
- Choose Redis data structures to match the access pattern.
- Redis pub/sub is not durable; Streams and brokers are.

**See also:** [Distributed Caching](distributed-caching.md) | [Performance Optimisation](performance-optimisation.md) | [Spring Core](../08-spring-core/index.md)
