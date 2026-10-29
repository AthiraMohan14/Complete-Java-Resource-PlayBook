# Local Caching with Caffeine and EhCache

A local cache keeps values in the memory of one JVM, so a lookup costs no network round trip. It is the fastest cache you can build, and it is also the most private: each instance has its own copy. This page covers the expiry and eviction rules that govern a local cache, how to configure Caffeine and EhCache, and the staleness trade-offs that interviewers probe. For shared caches, see [Distributed Caching](distributed-caching.md) and [Spring Cache and Redis](spring-cache-and-redis.md).

## Core concepts

### Why cache in the JVM
Reading from an in-process map takes nanoseconds to microseconds. Reading from Redis takes a network hop, which is typically around a millisecond. A local cache removes that hop for hot, read-mostly data such as reference tables, configuration, or a product's public details.

The costs are real. Each instance caches separately, so two instances can return different values after an update. The cache is lost on restart, and it is bounded by the heap, so an unbounded cache is a memory leak.

### Expiry: TTL versus TTI
Expiry decides when an entry is removed regardless of memory pressure.

| Policy | Rule | Caffeine | EhCache 3 |
|---|---|---|---|
| Time-to-live (TTL) | Expires a fixed time after it was written, whether or not it is read | `expireAfterWrite` | `ttl` in XML, `timeToLiveExpiration` in code |
| Time-to-idle (TTI) | Expires after a period without any access | `expireAfterAccess` | `tti` in XML, `timeToIdleExpiration` in code |

TTL is the safer default for data that changes on a schedule, because the entry always ends its life within a known window. TTI suits data that is reused heavily, but it has a trap: an entry that is read constantly never expires, so a stale value can live as long as traffic keeps it warm. Use TTI only when staleness is acceptable or when the source is also refreshed.

### Eviction: what goes when the cache is full
Eviction removes entries to stay within a size bound. Common strategies are:

- **LRU** (least recently used): drop the entry untouched for the longest time.
- **LFU** (least frequently used): drop the entry with the fewest accesses.
- **FIFO** (first in, first out): drop the oldest inserted entry, regardless of use.

Caffeine uses a window-based policy that combines recency and frequency (W-TinyLFU), so you rarely need to choose one. EhCache 3 does not expose a simple switch between these by name in the configuration shown here. Treat the exact eviction order as an implementation detail, and rely on a size bound and an expiry policy as your real controls.

Always set a maximum size. Without one, the cache grows until the heap runs out.

### Spring cache abstraction with a local provider
Spring's `@Cacheable`, `@CachePut`, and `@CacheEvict` annotations work the same way over every provider. The provider you pick decides where entries live. Caffeine and EhCache are local, and Redis is shared. The annotation and key rules are covered in [Spring Cache and Redis](spring-cache-and-redis.md).

Enable caching once with `@EnableCaching`, then add the provider dependency. For Caffeine, the starter `spring-boot-starter-cache` plus the `caffeine` library is enough.

### Caffeine in Spring Boot
Configure Caffeine through a string in `application.yml`, which needs no Java code:

```yaml
spring:
  cache:
    type: caffeine
    caffeine:
      spec: maximumSize=10000,expireAfterWrite=10m
```

Or configure it in Java when you need more control:

```java
import com.github.benmanes.caffeine.cache.Caffeine;
import java.util.concurrent.TimeUnit;
import org.springframework.cache.CacheManager;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CacheConfig {

    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager manager = new CaffeineCacheManager("users", "orders");
        manager.setCaffeine(Caffeine.newBuilder()
            .maximumSize(10_000)
            .expireAfterWrite(10, TimeUnit.MINUTES)
            .recordStats());
        return manager;
    }
}
```

`recordStats()` turns on hit and miss counters. Without it, there is nothing to report.

A service method that uses the cache:

```java
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    @Cacheable(value = "users", key = "#id", unless = "#result == null")
    public User findUser(long id) {
        return loadFromDatabase(id);
    }

    private User loadFromDatabase(long id) {
        return new User(id, "placeholder");
    }

    public record User(long id, String name) {}
}
```

`unless = "#result == null"` stops a missing user from being cached, so a later insert is visible immediately.

### Reporting statistics
Expose hit rate and size on a schedule or through a metrics endpoint. The native Caffeine cache behind a Spring cache can be read directly:

```java
import com.github.benmanes.caffeine.cache.stats.CacheStats;
import java.util.Map;
import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class CacheStatsReporter {

    private final CacheManager cacheManager;

    public CacheStatsReporter(CacheManager cacheManager) {
        this.cacheManager = cacheManager;
    }

    @Scheduled(fixedRate = 60_000)
    public void report() {
        for (String name : cacheManager.getCacheNames()) {
            Cache cache = cacheManager.getCache(name);
            if (cache != null && cache.getNativeCache() instanceof com.github.benmanes.caffeine.cache.Cache<?, ?> caffeine) {
                CacheStats stats = caffeine.stats();
                System.out.printf("%s size=%d hitRate=%.2f%n",
                    name, caffeine.estimatedSize(), stats.hitRate());
            }
        }
    }
}
```

This needs `@EnableScheduling` on the application and `recordStats()` in the configuration. A production setup would send these figures to a metrics system rather than print them.

### EhCache 3 configuration
EhCache is a mature local cache with more tiers and persistence options. Its settings are usually written in an XML file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.ehcache.org/v3">
    <cache alias="users">
        <key-type>java.lang.Long</key-type>
        <value-type>com.example.User</value-type>
        <expiry>
            <tti unit="minutes">30</tti>
        </expiry>
        <resources>
            <heap unit="entries">10000</heap>
        </resources>
    </cache>
    <cache alias="orders">
        <key-type>java.lang.Long</key-type>
        <value-type>com.example.Order</value-type>
        <expiry>
            <ttl unit="hours">1</ttl>
        </expiry>
        <resources>
            <heap unit="entries">5000</heap>
        </resources>
    </cache>
</config>
```

Spring Boot reaches EhCache 3 through the JCache (JSR-107) API. Configure `spring.cache.type` to `jcache` and point `spring.cache.jcache.config` at the XML file, with the EhCache and JCache dependencies on the classpath. The exact artifacts depend on the Spring Boot generation, so confirm them in the Boot reference before you rely on them.

The same cache built directly with the EhCache API is useful for code that runs outside Spring:

```java
import java.time.Duration;
import org.ehcache.Cache;
import org.ehcache.CacheManager;
import org.ehcache.config.builders.CacheConfigurationBuilder;
import org.ehcache.config.builders.CacheManagerBuilder;
import org.ehcache.config.builders.ExpiryPolicyBuilder;
import org.ehcache.config.builders.ResourcePoolsBuilder;

public class EhCacheDemo {

    public static void main(String[] args) {
        CacheManager manager = CacheManagerBuilder.newCacheManagerBuilder()
            .withCache("users", CacheConfigurationBuilder
                .newCacheConfigurationBuilder(Long.class, String.class, ResourcePoolsBuilder.heap(100))
                .withExpiry(ExpiryPolicyBuilder.timeToIdleExpiration(Duration.ofMinutes(30)))
                .build())
            .build(true);

        Cache<Long, String> users = manager.getCache("users", Long.class, String.class);
        users.put(1L, "John");
        System.out.println(users.get(1L));
        users.remove(1L);

        manager.close();
    }
}
```

Tiers extend a cache beyond the heap. Heap is fastest and sized in entries. Off-heap uses native memory and is slower. Disk persists to files and is slowest. Values stored off-heap or on disk must be serialisable, and the cost of serialising them should be measured.

## Local versus distributed
| Aspect | Local (Caffeine, EhCache) | Distributed (Redis, Memcached) |
|---|---|---|
| Latency | Nanoseconds to microseconds, no network | Typically around a millisecond, with a network hop |
| Scope | One instance | Shared by all instances |
| Consistency | Can differ between instances | One copy for all readers |
| Capacity | Bounded by the JVM heap | A separate server with its own memory |
| Survives restart | No | Yes, if the server keeps data |
| Serialisation | Not needed on heap | Needed for every value |
| Best for | Hot reads where a short staleness window is fine | Shared state and consistency-sensitive data |

Many systems combine them: a short-TTL local cache in front of a shared cache. The local TTL bounds how long any one instance can serve an outdated value.

## How it works / Step by step
1. The first call with a given key misses, runs the method, and stores the result.
2. Later calls hit the local map and return without touching the database.
3. Each write path evicts the entry, or the entry expires by TTL or TTI.
4. When the size bound is reached, the eviction policy removes an entry to make room.
5. Hit rate and evictions are monitored; a low hit rate means the cache is too small, too short-lived, or keyed poorly.

## Common pitfalls
- Creating a cache with no maximum size, then running out of heap under load.
- Using TTI for data that must be fresh, so a busy entry never expires.
- Assuming all instances agree after an update. Each instance holds its own copy until its expiry or eviction.
- Caching `null`, so a missing record stays missing after it is created. Use `unless` to prevent this.
- Calling a `@Cacheable` method from another method in the same class. The call bypasses the Spring proxy, so no caching happens.
- Using the same key for two caches, or forgetting to name caches separately, so entries overwrite each other.
- Storing large mutable objects, then modifying them in place. The cached copy changes for every reader.

!!! tip "Interview tip"
    **Q: Why not cache everything in memory on each instance?**
    Local caches are fast but private. Each instance can disagree with the others, the data is lost on restart, and memory is limited to one heap. Use a local cache for hot, read-mostly data where a short staleness window is acceptable. Use a shared cache like Redis when instances must see the same value, and put a short TTL on the local layer either way.

## Quick recap
- A local cache is the fastest tier, but it is private to one instance and bounded by heap.
- TTL expires entries after a fixed time from write; TTI expires them after a period without access, and can keep stale data alive.
- Always set a maximum size, and use `unless` to stop nulls being cached.
- Caffeine is configured with a spec string or a `CaffeineCacheManager`; EhCache 3 uses XML or its own builders, and Spring Boot reaches it through JCache.
- Monitor hit rate and evictions; a cache you do not measure is a guess.

**See also:** [Distributed Caching](distributed-caching.md), [Spring Cache and Redis](spring-cache-and-redis.md), [Redis Advanced Patterns](redis-advanced-patterns.md), [Performance Optimisation](performance-optimisation.md)
