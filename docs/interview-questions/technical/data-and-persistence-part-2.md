# Data and Persistence Questions (Part 2 of 4)

Continued from [Part 1](data-and-persistence-part-1.md). Continue to [Part 3](data-and-persistence-part-3.md).

---

## 13. What is the difference between LAZY and EAGER fetching, and what is the N+1 problem?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`LAZY` loads a related entity or collection only when you first access it. `EAGER` loads it together with the owning entity. The N+1 problem happens when you load N parents and then run one extra query per parent to load their children: one query for the list, plus N queries for the relation. It is the most common performance bug in JPA code.

### Explanation
```java
import jakarta.persistence.*;
import java.util.List;

@Entity
class Author {
    @Id @GeneratedValue Long id;
    String name;

    @OneToMany(mappedBy = "author", fetch = FetchType.LAZY)
    List<Book> books;
}

@Entity
class Book {
    @Id @GeneratedValue Long id;
    String title;

    @ManyToOne(fetch = FetchType.LAZY)
    Author author;
}
```

If you loop over 100 authors and call `getBooks()` on each, Hibernate issues 1 query for authors and 100 for books. Fix it by fetching both in one query:

```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

interface AuthorRepository extends JpaRepository<Author, Long> {
    @Query("select a from Author a left join fetch a.books")
    List<Author> findAllWithBooks();
}
```

An `@EntityGraph` on a repository method does the same without writing JPQL.

### When to use / pitfalls
- JPA defaults `@ManyToOne` and `@OneToOne` to `EAGER`. Set `LAZY` explicitly.
- Fetching several collections with `JOIN FETCH` in one query causes a Cartesian product, and Hibernate rejects multiple bag fetches. Use sets, or separate queries, or batch fetching (`hibernate.default_batch_fetch_size`).
- Verify with SQL logging in tests so the query count is a checked property.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 14. What is the persistence context, and what are entity states?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The persistence context is the first-level cache of a JPA `EntityManager` (Hibernate's `Session`). It holds managed entities, so repeated lookups for the same ID within the session return the same instance without another query. An entity is transient (new, not saved), managed (tracked by the context), detached (was managed, but the context is closed), or removed. Changes to managed entities are written at flush time through dirty checking, with no explicit `save`.

### Explanation
```java
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;

class Demo {
    public static void main(String[] args) {
        EntityManagerFactory emf = Persistence.createEntityManagerFactory("demo");
        EntityManager em = emf.createEntityManager();
        em.getTransaction().begin();
        // Entities loaded here are managed; setting a field is enough to update them at commit.
        em.getTransaction().commit();
        em.close();                // the context ends; entities become detached
        emf.close();
    }
}
```

The `"demo"` persistence unit must exist in `persistence.xml` for this to run; Spring Boot creates it for you.

### When to use / pitfalls
- A detached entity changed outside a session will not be saved unless you `merge` it.
- A long-lived persistence context grows memory use. Keep sessions short; in web apps the request scope is typical.
- Open Session in View keeps the session open during rendering and can trigger lazy loads in views. Many teams disable it with `spring.jpa.open-in-view=false`.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 15. How do cascade types and `orphanRemoval` work?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`cascade` propagates an operation from a parent to its children: `PERSIST`, `MERGE`, `REMOVE`, `REFRESH`, `DETACH`, or `ALL`. `orphanRemoval = true` deletes a child when it is removed from the parent's collection. Both are owned by the parent side of the relationship.

### Explanation
```java
import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
class Order {
    @Id @GeneratedValue Long id;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    List<OrderLine> lines = new ArrayList<>();
}

@Entity
class OrderLine {
    @Id @GeneratedValue Long id;

    @ManyToOne
    Order order;

    String sku;
}
```

Saving an `Order` saves its lines. Removing a line from `order.lines` deletes its row at flush.

### When to use / pitfalls
- Do not cascade `REMOVE` from a shared child, such as a country lookup, into everything that refers to it.
- Keep both sides of a bidirectional relationship in sync in your code (`line.setOrder(order)` and `order.getLines().add(line)`).

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 16. How do Spring Data repositories handle queries and pagination?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Spring Data generates queries from method names (derived queries), from `@Query` annotations, or from named queries and `Specification` objects for dynamic filters. `Pageable` adds paging and sorting; a `Page` return type also runs a count query. Projections return only the fields you need.

### Explanation
```java
import jakarta.persistence.*;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

@Entity
class Order {
    @Id @GeneratedValue Long id;
    String reference;
    long customerId;
}

interface OrderRepository extends JpaRepository<Order, Long> {
    Optional<Order> findByReference(String reference);

    Page<Order> findByCustomerId(long customerId, Pageable pageable);
}
```

Call it with `PageRequest.of(0, 20, Sort.by("id"))`. Offset paging gets slower as the page number grows, because the database still reads and discards the earlier rows. For deep scrolling, use keyset pagination: `WHERE id > :lastSeenId ORDER BY id LIMIT 20`.

### When to use / pitfalls
- Method names get unreadable fast. Use `@Query` once a query has more than two conditions.
- A `Page` triggers an extra count query. Use `Slice` when you do not need the total.
- Returning entities from a controller can leak fields and trigger lazy loads. Use DTOs or projections.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 17. How do DTOs and mapping libraries fit in, and how do MapStruct and ModelMapper differ?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A DTO (data transfer object) is a plain object shaped for an API or a use case, so the entity's internal fields do not leak. MapStruct generates mapping code at compile time, so it is fast and type-checked at build time. ModelMapper maps at runtime through reflection, which is more flexible to configure but slower and fails later.

### Explanation
```java
import org.mapstruct.Mapper;

record OrderDto(Long id, String reference) {}

@Mapper(componentModel = "spring")
interface OrderMapper {
    OrderDto toDto(Order order);      // MapStruct generates the implementation
}
```

Here `Order` is the entity from question 16, with getters for its fields (MapStruct maps through accessors). The generated code is ordinary Java you can read and debug.

### When to use / pitfalls
- With MapStruct, an unmapped target property is usually reported as a compile-time warning. With reflection-based mappers, a mismatch can show up only at runtime as a null value.
- Do not map entities with lazy collections in a way that triggers queries outside the transaction.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 18. How do Flyway and Liquibase manage schema changes?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Both tools apply versioned database changes in order and record what has run in a history table, so every environment ends up with the same schema. Flyway uses versioned SQL files (for example `V2__add_orders_index.sql`). Liquibase uses changelogs in XML, YAML, JSON, or SQL. Both can validate that applied migrations have not been edited.

### Explanation
```sql
-- V1__create_orders.sql
CREATE TABLE orders (
    id          BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    created_at  TIMESTAMP NOT NULL
);

-- V2__index_orders_by_customer.sql
CREATE INDEX idx_orders_customer ON orders (customer_id, created_at);
```

Flyway runs pending versions at application startup when `spring.flyway.enabled` is on (the default with the starter). Keep the naming pattern: `V<version>__<description>.sql`, with two underscores.

### When to use / pitfalls
- Never edit a migration that has already run anywhere. Write a new one instead; a checksum mismatch will stop startup.
- Make migrations backward-compatible during rolling deployments: add columns first, then move code, then remove old columns.
- Test migrations on a copy of production-like data. A long `ALTER TABLE` can lock a busy table.
- Repeatable migrations (`R__`) suit views and stored routines that are rerun when they change.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 19. What is the difference between replication, sharding, and partitioning?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Replication copies the same data to other servers, which improves read scaling and availability. Sharding splits rows across servers by a shard key, so each server holds part of the data and writes scale out. Partitioning splits one large table into pieces inside a single database, by range, hash, or list, which helps maintenance and pruning.

### Explanation
- Replication: a primary takes writes; replicas serve reads. Replicas can lag behind, so reads right after a write may be stale.
- Sharding: a shard key such as `customer_id` decides the server. Queries that do not include the key must query every shard, and cross-shard transactions are hard.
- Partitioning: `PARTITION BY RANGE (created_at)` lets old partitions be dropped in one step.

### When to use / pitfalls
- Scale reads with replicas before you shard. Sharding is hard to undo.
- Pick a shard key that matches your most frequent query, and that spreads load evenly.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 20. When would you choose Redis, and what persistence options does it offer?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Redis is an in-memory data store with structures such as strings, lists, sets, hashes, sorted sets, and streams. Use it for caching, sessions, rate limiting, counters, leaderboards, and pub/sub. It persists data optionally: RDB writes periodic snapshots, and AOF logs every write, which can be replayed after a restart.

### Explanation
```java
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import java.time.Duration;

@Service
class LoginRateLimiter {
    private final StringRedisTemplate redis;

    LoginRateLimiter(StringRedisTemplate redis) {
        this.redis = redis;
    }

    boolean allow(String userKey) {
        Long attempts = redis.opsForValue().increment("login:" + userKey);
        if (attempts != null && attempts == 1L) {
            redis.expire("login:" + userKey, Duration.ofMinutes(15));   // window starts at first attempt
        }
        return attempts != null && attempts <= 5;
    }
}
```

### When to use / pitfalls
- Redis is not a replacement for your primary database unless you accept its durability trade-offs.
- Expired keys and eviction policies affect correctness of caches and rate limits. Set them deliberately.
- The example above is a simple fixed window; it is not atomic across the increment and expire calls. Use a Lua script or a dedicated library for strict limits.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## Quick recap

- Index the columns your queries filter, join, and sort on, and check with `EXPLAIN`.
- Know the four isolation levels and that each database's defaults differ.
- Use `PreparedStatement` and a connection pool; use transactions for multi-step writes.
- Fix N+1 with `JOIN FETCH` or `@EntityGraph`, and set `LAZY` explicitly.
- Use `@Version` for optimistic locking; keep pessimistic lock scopes short.
- Never edit an applied Flyway migration; write a new version.

**See also:** [Core Java](core-java-part-1.md), [Spring and security](spring-and-security-part-1.md), [Architecture and distributed systems](architecture-and-distributed.md)
