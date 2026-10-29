# Redis Advanced Patterns

Redis is an in-memory data store with rich data types, and it is often used for caching, sessions, rate limits, leaderboards, and locks. The basics of Spring integration and the core data types are in [Spring Cache and Redis](spring-cache-and-redis.md). This page covers the parts interviewers probe: which operations are atomic, how to build a lock and a rate limiter that survive failures, how replication and failover work, and how to run Redis safely.

## Core concepts

### Data types at the command level
Each Redis type suits a specific shape of data. The commands below are the ones you will reach for most often.

| Type | Core commands | Typical use |
|---|---|---|
| String | `SET key value EX seconds NX`, `GET`, `INCR`, `MGET` | Cached values, counters, flags |
| List | `LPUSH`, `RPUSH`, `LPOP`, `LRANGE`, `LTRIM` | Simple queues, recent-activity feeds |
| Set | `SADD`, `SISMEMBER`, `SINTER`, `SUNION` | Unique members, tags, deduplication |
| Sorted set | `ZADD`, `ZINCRBY`, `ZREVRANGE`, `ZREVRANK`, `ZREMRANGEBYSCORE` | Leaderboards, sliding windows, time-ordered indexes |
| Hash | `HSET`, `HGET`, `HINCRBY`, `HGETALL` | Object-like records such as a user profile |

A few details that matter in practice:

- `SET key value EX seconds NX` writes only if the key is absent and sets an expiry in one atomic step. This is the building block for locks.
- `LTRIM list 0 99` keeps the newest 100 items of a list, which bounds a feed.
- `INCR` is atomic, so concurrent counters need no application-side locking.
- `ZINCRBY` updates a score atomically, and `ZREVRANGE` with `WITHSCORES` returns a ranked list.

### Atomicity: single commands versus sequences
Each Redis command runs atomically. A sequence of commands from one client does not. If your code runs `INCR` and then `EXPIRE` as two separate calls, a crash between them leaves a counter with no expiry. Two ways to close that gap:

- Use a single command that does both, such as `SET ... EX ... NX`.
- Use a Lua script. Redis runs a script as one atomic step, so the check and the change cannot be interleaved by another client.

Lua scripts are the right tool when a decision depends on a read, such as "delete the lock only if it still holds my token".

## Distributed locks
A distributed lock stops two processes from doing the same work at once, for example two instances processing the same order. The lock is a key with an expiry, so a crashed holder does not block forever.

Two rules make the lock correct:

1. Acquire with `SET key token NX EX seconds`, where `token` is a random value unique to this holder.
2. Release only if the key still holds your token. A plain `GET` followed by `DEL` is racy: the lock can expire and be taken by someone else between the two calls, and you would then delete their lock. A Lua script does the compare and delete atomically.

```java
import java.time.Duration;
import java.util.List;
import java.util.UUID;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

@Component
public class OrderLock {

    private static final DefaultRedisScript<Long> RELEASE = new DefaultRedisScript<>(
        "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
        Long.class);

    private final StringRedisTemplate redis;

    public OrderLock(StringRedisTemplate redis) {
        this.redis = redis;
    }

    public String tryAcquire(String key, Duration ttl) {
        String token = UUID.randomUUID().toString();
        Boolean ok = redis.opsForValue().setIfAbsent(key, token, ttl);
        return Boolean.TRUE.equals(ok) ? token : null;
    }

    public boolean release(String key, String token) {
        Long removed = redis.execute(RELEASE, List.of(key), token);
        return Long.valueOf(1L).equals(removed);
    }
}
```

Use it like this:

```java
import java.time.Duration;

class OrderProcessor {

    // Stand-in for the lock client shown earlier on the page.
    interface OrderLock {
        String tryAcquire(String key, Duration ttl);
        void release(String key, String token);
    }

    private final OrderLock orderLock;

    OrderProcessor(OrderLock orderLock) {
        this.orderLock = orderLock;
    }

    void processOrder(int orderId) {
        // ... business logic ...
    }

    void handle() {
        String token = orderLock.tryAcquire("order:123:processing", Duration.ofSeconds(30));
        if (token == null) {
            throw new IllegalStateException("Order 123 is already being processed");
        }
        try {
            processOrder(123);
        } finally {
            orderLock.release("order:123:processing", token);
        }
    }
}
```

Limits to state in an interview:

- The lock expires after its TTL even if the work is still running. Keep the work well under the TTL, or extend the lock deliberately, and make the protected operation safe to retry.
- A lock on a single Redis node is lost if that node fails before the write replicates. Redlock extends the idea across several independent nodes, but its safety is debated; see [Spring Cache and Redis](spring-cache-and-redis.md) for the trade-off.
- When correctness matters more than availability, back the critical write with a database constraint or a fencing token, not with the lock alone.

## Rate limiting
A rate limiter caps how many requests a client makes in a time window. Two common designs:

- **Fixed window**: count requests per window using a key that includes the window number. It is simple and cheap, but a burst at the edge of two windows can pass twice the limit.
- **Sliding log**: keep one sorted-set member per request, scored by its timestamp, and count the members in the last window. It is accurate, and it uses memory proportional to the request rate.

The sliding log in Java, with `StringRedisTemplate`:

```java
import java.time.Duration;
import java.util.UUID;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class SlidingWindowLimiter {

    private final StringRedisTemplate redis;

    public SlidingWindowLimiter(StringRedisTemplate redis) {
        this.redis = redis;
    }

    public boolean allow(String clientId, int maxRequests, Duration window) {
        String key = "rate:" + clientId;
        long now = System.currentTimeMillis();

        redis.opsForZSet().removeRangeByScore(key, 0, now - window.toMillis());
        Long inWindow = redis.opsForZSet().zCard(key);
        if (inWindow != null && inWindow >= maxRequests) {
            return false;
        }

        redis.opsForZSet().add(key, UUID.randomUUID().toString(), now);
        redis.expire(key, window);
        return true;
    }
}
```

The UUID member matters: two requests in the same millisecond with a fixed member would collapse into one entry. This version still has a gap: two concurrent requests can both see room and both be added, so the limit can be exceeded by a few under heavy concurrency. For a strict limit, run the check, the trim, and the insert inside one Lua script.

Return HTTP 429 with a `Retry-After` header when `allow` returns false. The limiter is typically called from a `HandlerInterceptor` or a gateway filter, not from business code.

## Leaderboards
A sorted set gives a leaderboard with rank lookups in logarithmic time:

```java
import java.util.Set;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations.TypedTuple;
import org.springframework.stereotype.Component;

@Component
public class Leaderboard {

    private static final String KEY = "leaderboard:weekly";
    private final StringRedisTemplate redis;

    public Leaderboard(StringRedisTemplate redis) {
        this.redis = redis;
    }

    public void addPoints(String userId, double points) {
        redis.opsForZSet().incrementScore(KEY, userId, points);
    }

    public Set<TypedTuple<String>> topTen() {
        return redis.opsForZSet().reverseRangeWithScores(KEY, 0, 9);
    }

    public Long rankOf(String userId) {
        return redis.opsForZSet().reverseRank(KEY, userId); // 0 is the top
    }
}
```

Points to note: ranks are zero-based, `reverseRank` puts the highest score at 0, and members with equal scores are ordered lexicographically, so define a tie-break rule if ties matter. A weekly board is usually a new key per week with a TTL, not a deletion job.

## Pub/Sub and when to use Streams
Pub/Sub delivers each message to the subscribers connected at that moment. Nothing is stored, so a message published while a subscriber is down is lost. It suits notifications that can be missed, such as a cache invalidation hint, where the next read would correct the state anyway.

For work that must not be lost, use Redis Streams with consumer groups, which keep messages until they are acknowledged. For cross-service events, a message broker such as Kafka or RabbitMQ is often the better fit (see [Messaging](../13-messaging/index.md)).

## Caching patterns beyond the annotations
The cache-aside, write-through, and write-behind patterns are compared in [Distributed Caching](distributed-caching.md). With Redis as the store, cache-aside is the usual default: read the key, on a miss load from the database, then set the key with a TTL. Writes evict or update the key after the database commit. Write-behind is the riskiest, because a Redis failure before the flush loses writes, so use it only when that loss is acceptable.

## Configuration in Spring Boot
Spring Boot 3 uses the `spring.data.redis` prefix. The older `spring.redis` prefix is no longer the current form.

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      password: ${REDIS_PASSWORD}
      timeout: 2s
      lettuce:
        pool:
          max-active: 20
          max-idle: 10
          min-idle: 5
```

Connection pooling for Lettuce needs `commons-pool2` on the classpath. Read the password from the environment or a secrets store, never from source control.

Session storage moves HTTP sessions into Redis, so that any instance can serve any request:

```yaml
spring:
  session:
    store-type: redis
    timeout: 30m
```

Store only small, serialisable values in the session, and remember that the session is copied on every change, so a large session costs bandwidth on each request.

## High availability and scaling

### Replication
A primary accepts writes and streams them to one or more replicas. Replicas serve reads and can be promoted by hand. Replication is asynchronous, so a failover can lose the most recent writes. Configure a replica with `replicaof <primary-host> <port>`; the older `slaveof` spelling is deprecated.

### Sentinel
Sentinel processes watch the primary and replicas, agree when the primary is down, and promote a replica. A quorum of sentinels must agree, so run an odd number, usually three or more, on separate machines.

```
sentinel monitor mymaster 10.0.0.10 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 10000
```

Clients ask Sentinel for the current primary. In Spring Boot, name the master and list the sentinel nodes:

```yaml
spring:
  data:
    redis:
      sentinel:
        master: mymaster
        nodes: 10.0.0.11:26379,10.0.0.12:26379,10.0.0.13:26379
```

### Cluster
Redis Cluster shards data across nodes. The keyspace has 16,384 hash slots, and each key maps to one slot. Each primary owns a range of slots and can have replicas, and the cluster handles failover for a failed primary.

```
redis-server --port 7000 --cluster-enabled yes
redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 --cluster-replicas 1
```

Multi-key commands and transactions require all keys to share a slot. Use a hash tag, such as `user:{42}:cart` and `user:{42}:wishlist`, so that only the part in braces decides the slot. Without this, multi-key operations fail with a cross-slot error.

Choosing between them: Sentinel adds failover to a single dataset that fits on one primary. Cluster adds capacity beyond one machine, at the cost of the cross-slot restrictions.

## Persistence
Redis holds data in memory, and persistence writes it to disk. Two mechanisms exist, and they can be combined.

| Mechanism | How it works | Data at risk on crash | Cost |
|---|---|---|---|
| RDB snapshot | Writes a point-in-time file at intervals | Everything since the last snapshot | Compact file; fast restart |
| AOF | Appends each write to a log, replayed on restart | Up to one second with `appendfsync everysec` | Larger file; more write work |

```
save 900 1
save 300 10
appendonly yes
appendfsync everysec
```

Recent Redis versions write an RDB snapshot at the start of the AOF file by default, which gives fast restarts and a small log. Persistence protects against restarts, not against a bad write, and it does not replace backups. Even with AOF, a replica failover can drop acknowledged writes. Treat Redis as a cache or a fast store of derived data, and keep the source of truth in a database.

## Monitoring and debugging

### INFO and memory
`INFO` groups server statistics into sections:

```bash
redis-cli INFO memory      # used memory, fragmentation ratio
redis-cli INFO stats       # commands processed, keyspace hits and misses
redis-cli INFO clients     # connected clients
```

Compare `keyspace_hits` with `keyspace_misses` to find the hit rate of the whole server. Watch `used_memory` against `maxmemory`, and set an eviction policy such as `maxmemory-policy allkeys-lru` if Redis is a cache. With `noeviction`, writes fail once memory is full, which is the right choice for data that must not be dropped.

### SLOWLOG
The slow log records commands that exceed a threshold:

```bash
redis-cli CONFIG SET slowlog-log-slower-than 10000   # microseconds
redis-cli SLOWLOG GET 10
redis-cli SLOWLOG RESET
```

Slow commands are usually `KEYS`, large `SMEMBERS` or `HGETALL` calls on big values, or Lua scripts that run too long. Replace `KEYS` with `SCAN`, which iterates in pages.

### MONITOR and key analysis
`MONITOR` streams every command the server receives. It is useful for a short debugging session, but it slows the server, so do not leave it running in production.

```bash
redis-cli --bigkeys               # largest key of each type
redis-cli MEMORY USAGE user:1     # bytes used by one key
redis-cli OBJECT ENCODING user:1  # internal encoding, such as listpack or hashtable
```

Big keys cause latency spikes when they are read or deleted, so split them, or delete them with `UNLINK`, which frees memory in the background.

## Best practices
These habits keep a Redis deployment predictable. Each one is about how the data is named, sized, expired, or read.

### Key naming
Use a consistent pattern: an application prefix, a version, the entity type, and the identifier, separated by colons. A readable key shows its purpose in `redis-cli` and makes pattern-based inspection possible.

```java
final class CacheKeys {

    private static final String APP = "orders";
    private static final String VERSION = "v2";

    private CacheKeys() {
    }

    static String order(long orderId) {
        return APP + ":" + VERSION + ":order:" + orderId;
    }
}
```

Including a version in the key handles schema changes. When the cached object's shape changes, bump the version. The old entries are no longer read and expire on their own, so no mass deletion is needed. Keep keys short, though. Very long keys waste memory on every entry.

### Avoid KEYS in production
`KEYS pattern` scans the whole keyspace in one command and blocks every other client while it runs. Use the incremental `SCAN` command instead. It returns a cursor and a batch of keys each call, so the server stays responsive:

```bash
SCAN 0 MATCH orders:v2:order:* COUNT 500
```

`SCAN` can return the same key more than once and can return zero keys in a batch while the cursor is still moving. Code that uses it must tolerate both. Use `SCAN` for maintenance tasks, not for the request path.

### Handle big keys
A big key is one with a very large value or a collection with millions of members. Reading, rewriting, or deleting it blocks the single Redis thread for longer. To find them and size them:

```bash
redis-cli --bigkeys                    # sampled report of the largest keys per type
MEMORY USAGE orders:v2:order:42        # bytes used by one key
```

Fixes:

- Split a large collection into several keys, such as one hash per time bucket.
- Store large documents in the database or object storage, and cache only what the request needs.
- Delete with `UNLINK` instead of `DEL`. `UNLINK` removes the key from the keyspace at once and frees its memory in the background.

### Set sensible TTLs
Every cache key should have a TTL unless it is a deliberate persistent structure, such as a leaderboard that is managed explicitly. Without a TTL, cache keys accumulate and memory fills up. Add jitter so that many keys written together do not expire at the same moment:

```java
import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;

final class Ttls {

    private Ttls() {
    }

    // A base of ten minutes plus up to one minute of random jitter
    static Duration cacheEntry() {
        long jitterSeconds = ThreadLocalRandom.current().nextLong(60);
        return Duration.ofMinutes(10).plusSeconds(jitterSeconds);
    }
}
```

Set the TTL in the same command as the value, for example with `SET key value EX seconds` or the `setIfAbsent` call with a duration, so a crash cannot leave a key without one.

### Keep values small and access them in batches
Keep each value small enough that reading it does not hold up other requests. Batch many reads into `MGET` or a pipeline rather than sending one round trip per key in a loop.

### Secure the instance
Enable authentication (`requirepass` or ACL users) and restrict network access, and use TLS when traffic crosses a network you do not fully control. Redis is not a durable store, so keep the system of record in a database and treat Redis as a copy.

### Replication is not the same as high availability on its own
Cluster provides sharding, which spreads keys across primaries. High availability for each shard comes from replicas and failover, through Sentinel or a managed service. Choose the topology for the failure you need to survive, not only for capacity.

## How it works / Step by step
When choosing a Redis pattern for a problem:

1. Decide whether the data is a cache, a derived store, or a source of truth. Only the first two suit Redis as the main store.
2. Pick the data type that matches the access pattern, such as a sorted set for ranks and a hash for a record.
3. Set a TTL on every key unless the key is a deliberate persistent structure.
4. Put any read-then-write decision inside one atomic command or a Lua script.
5. Choose a replication topology: a primary with replicas, Sentinel for failover, or Cluster for capacity.
6. Monitor memory, hit rate, slow commands, and big keys from day one.

## Common pitfalls
- Using `GET` then `DEL` to release a lock, which can delete another holder's lock.
- Setting a key and then its TTL in separate calls, which can leave a key that never expires.
- Calling `KEYS` in production, which blocks the server while it scans every key.
- Running many round trips in a loop. Batch them with `MGET`, a pipeline, or a Lua script.
- Storing very large values, such as whole documents, without compression or a size limit.
- Relying on Redis as the only copy of data that matters, then losing it on failover.
- Leaving the server without a password, or exposing its port to the public network.
- Using a single Redis node for everything, with no failover plan and no monitoring.

!!! tip "Interview tip"
    **Q: How would you make a Redis lock safe?**
    Acquire with `SET key token NX EX`, using a random token. Release with a Lua script that deletes the key only when it still holds your token. Keep the protected work shorter than the TTL, and make the operation idempotent or guarded by a database constraint, because a lock with a timeout cannot prove exclusivity on its own.

## Quick recap
- Single Redis commands are atomic; sequences of commands are not, so combine steps with `SET ... NX EX` or a Lua script.
- A safe lock uses a random token and a compare-and-delete release.
- Sliding-log rate limiting uses a sorted set; a strict limit needs a Lua script.
- Sentinel adds failover; Cluster adds sharding and needs related keys in one hash slot.
- Monitor memory, hit rate, the slow log, and big keys, and keep the source of truth in a database.

**See also:** [Spring Cache and Redis](spring-cache-and-redis.md), [Distributed Caching](distributed-caching.md), [Local Caching with Caffeine and EhCache](local-caching-ehcache-caffeine.md), [Resilience Patterns](../14-microservices/resilience-patterns.md), [AWS](../18-cloud/aws.md)
