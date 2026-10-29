# JPA and Hibernate

JPA (Jakarta Persistence API) is the specification for mapping Java objects to relational tables. Hibernate is the most common implementation. Interviewers ask about JPA to see whether you understand what happens behind `save()`, why lazy loading breaks outside a transaction, and how to avoid N+1 queries.

## Core concepts

### Entities and mapping

An entity is a class mapped to a table. The specification is in the `jakarta.persistence` package (Jakarta EE); Spring Boot 3 uses this namespace, and older code uses `javax.persistence`.

```java
import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 20)
    private String status = "NEW";

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderLine> lines = new ArrayList<>();

    protected Order() {                        // JPA requires a no-argument constructor
    }

    public Order(String status) {
        this.status = status;
    }

    public Long getId() { return id; }
    public String getStatus() { return status; }
    public List<OrderLine> getLines() { return lines; }

    public void addLine(OrderLine line) {
        lines.add(line);
        line.setOrder(this);                  // keep both sides of the relationship in sync
    }
}
```

```java
import jakarta.persistence.*;

@Entity
public class OrderLine {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id")
    private Order order;

    private String sku;
    private int quantity;

    protected OrderLine() {
    }

    public OrderLine(String sku, int quantity) {
        this.sku = sku;
        this.quantity = quantity;
    }

    void setOrder(Order order) { this.order = order; }
}
```

`@Table`, `@Id`, `@GeneratedValue`, and `@Column` control the table and column mapping. `GenerationType.IDENTITY` relies on an auto-increment column; `SEQUENCE` uses a database sequence and allows batching of inserts.

### Relationships and cascades

| Annotation | Default fetch | Typical use |
|---|---|---|
| `@OneToOne` | EAGER | One-to-one |
| `@OneToMany` | LAZY | Parent to children |
| `@ManyToOne` | EAGER | Child to parent (set LAZY explicitly) |
| `@ManyToMany` | LAZY | Many-to-many through a join table |

`mappedBy` marks the inverse side; the side with `@JoinColumn` owns the foreign key. `cascade` propagates operations (persist, remove, merge) to the related entities. `orphanRemoval = true` deletes children that are removed from the collection.

Make `@ManyToOne` lazy explicitly. The JPA default is eager, which can load far more data than you need.

### Fetch strategies and JOIN FETCH

`LAZY` loads an association when it is first accessed; `EAGER` loads it with the parent. Lazy loading uses proxy objects that query the database on first access. Accessing a lazy association after the session has closed throws `LazyInitializationException`.

Load what you need in one query with `JOIN FETCH`:

```java
import jakarta.persistence.EntityManager;
import java.util.List;

// JPQL: returns orders with their lines in one SQL statement
List<Order> orders = entityManager.createQuery(
        "select distinct o from Order o join fetch o.lines where o.status = :status", Order.class)
    .setParameter("status", "NEW")
    .getResultList();
```

`distinct` removes duplicate parent rows that the join produces. Do not fetch-join two collections at once; the result becomes a cross product and Hibernate may reject it with a `MultipleBagFetchException`. Hibernate's `@Fetch` annotation controls the SQL strategy (for example, `SUBSELECT` or `BATCH`) and is a useful tuning tool for collections.

### Queries

- **JPQL:** queries over entities and their attributes, not tables. Portable across JPA providers.
- **HQL:** Hibernate's superset of JPQL. Mostly compatible for everyday queries.
- **Criteria API:** builds queries as typed Java objects. Useful for dynamic filters; verbose.
- **Native SQL:** raw SQL with `createNativeQuery`. Use it when you need database-specific features, and map results carefully.

Always bind parameters (`:name` or `?1`). String concatenation in JPQL is the same injection risk as in JDBC.

### Lifecycle and callbacks

An entity moves through states: **new** (not persisted), **managed** (attached to a persistence context), **detached** (was managed, now not), and **removed**. Changes to a managed entity are written to the database at flush time, without an explicit `update` call (dirty checking).

Lifecycle callbacks run on state changes:

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import java.time.Instant;

@Entity
public class Customer {

    @Id
    private Long id;

    private Instant createdAt;
    private Instant updatedAt;

    @PrePersist
    void onCreate() {
        createdAt = Instant.now();
        updatedAt = createdAt;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }
}
```

Callbacks are methods on the entity (or on a separate listener class registered with `@EntityListeners`). Keep them simple; a callback that calls other services is hard to test and easy to get wrong.

### The persistence context and first-level cache

The `EntityManager` (Hibernate's `Session`) holds the **persistence context**, which is also the first-level cache. Within one context, loading the same ID twice returns the same Java object. The cache lasts only for the context, usually one transaction.

A second-level cache is optional and shared across sessions. It needs explicit configuration and cache invalidation rules.

### Detached entities and merge

An entity is detached once its context closes. Changes to a detached object are not saved automatically. `merge()` copies a detached object's state onto a managed copy and returns that copy; use the returned instance, not the original.

## How it works / Step by step

What happens during `entityManager.persist(order)` inside a transaction:

1. The entity becomes managed and gets an ID (immediately for `IDENTITY`, at flush for `SEQUENCE` with batching).
2. Cascades run: child entities marked with `CascadeType.PERSIST` are persisted too.
3. At flush (before commit or before a query that needs it), Hibernate computes SQL from the changes and sends it.
4. On commit, the transaction ends; the context closes, and the entities become detached.

## Common pitfalls

- Accessing a lazy collection outside the transaction (`LazyInitializationException`). Fetch it inside the transaction, or fetch-join it.
- The N+1 problem: loading parents, then one query per parent for children. Use `JOIN FETCH`, `@EntityGraph`, or batch fetching.
- Fetch-joining two `List` collections in one query, which causes a cross product or an exception.
- Using `EAGER` on `@ManyToOne` and `@OneToOne` without thinking, which pulls in extra tables.
- Implementing `equals` and `hashCode` from mutable fields or the generated ID before it is assigned. Base equality on a stable business key, or on identity with care.
- Relying on `merge()` but then using the original detached object.
- Enabling open-session-in-view and assuming it is free. Spring Boot enables it by default and logs a warning; many teams turn it off and fetch explicitly.

!!! tip "Interview tip"
    **Q: What is the N+1 problem and how do you fix it?**
    Loading N parents, then running one query for each parent's children, produces N+1 queries. Fix it with a `JOIN FETCH` in JPQL, an `@EntityGraph`, or batch fetching with `@BatchSize` or `hibernate.default_batch_fetch_size`. Measure the SQL with logging before and after the change.

## Quick recap

- JPA is the specification; Hibernate is a common implementation.
- Mark `@ManyToOne` as `LAZY`; a lazy association must be loaded inside a transaction.
- `JOIN FETCH` fixes N+1 but do not fetch two bag collections at once.
- The persistence context is a first-level cache and tracks changes through dirty checking.
- After a context closes, entities are detached; use the instance returned by `merge()`.

**See also:** [JDBC](jdbc.md), [Spring Data JPA](spring-data-jpa.md), [DTO Mapping](dto-mapping.md)
