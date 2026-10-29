# Caching and Performance

Caching stores the result of expensive work so it can be reused, and performance work finds out where time and memory actually go before changing anything. These notes cover Spring's cache abstraction, Redis as a shared cache and data store, profiling and JVM tuning, and the invalidation strategies that keep caches consistent with the database. Interviewers ask about these because cache bugs cause stale data, and optimisation without measurement wastes effort.

---

## Topics

### [Spring Cache and Redis](spring-cache-and-redis.md)
**@Cacheable - @CacheEvict - @CachePut - CacheManager - Redis - RedisTemplate - Spring Session**
Adding caching to service methods with Spring's annotations, backing it with Redis, and using Redis for sessions, pub/sub, streams, and locks.

### [Performance Optimisation](performance-optimisation.md)
**profilers - JFR - N+1 queries - connection pools - JVM tuning - load testing**
Measuring first, then fixing the real bottleneck in database access, pools, JVM settings, and concurrency.

### [Distributed Caching](distributed-caching.md)
**Memcached - cache-aside - write-through - write-behind - invalidation - stampede**
Keeping caches consistent across many instances, choosing an invalidation strategy, and coordinating writes between cache and database.

---

**See also:** [Redis Caching in Spring Boot](spring-cache-and-redis.md) | [Testing](../11-testing/index.md) | [Databases and SQL](../06-databases-sql/index.md)
