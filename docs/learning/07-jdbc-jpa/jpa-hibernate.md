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

### Auditing timestamps with @CreationTimestamp and @UpdateTimestamp

Most tables need to record when a row was created and last changed. Writing those values by hand in every service is easy to forget. Hibernate's `@CreationTimestamp` and `@UpdateTimestamp` fill the columns for you when the entity is saved.

```java
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "invoices")
public class Invoice {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)   // written once, on insert
    private Instant createdAt;

    @UpdateTimestamp
    @Column(nullable = false)                      // refreshed on every update
    private Instant updatedAt;
}
```

The two annotations behave differently:

- `@CreationTimestamp` sets the value when the entity is inserted. Keeping `updatable = false` on the column protects it from later changes.
- `@UpdateTimestamp` sets the value on insert and again each time the entity is flushed with changes. Hibernate only writes it when a column is actually dirty, so an unchanged entity keeps its old value.

Both work with the `java.time` types such as `Instant`, `OffsetDateTime`, and `LocalDateTime`. Prefer `Instant` or `OffsetDateTime` for stored timestamps. A `LocalDateTime` has no zone, so it is ambiguous when the application runs in more than one time zone.

Some writes bypass the annotations, and this is the part interviewers test:

- A bulk JPQL or HQL update (`UPDATE Invoice i SET ...`) runs in the database and does not touch the entity, so `updatedAt` stays stale. Set it in the query yourself.
- Native SQL and direct JDBC writes do not go through Hibernate at all.
- Lifecycle callbacks such as `@PreUpdate` do not run for bulk updates either.

Spring Data offers a more portable option. `@CreatedDate` and `@LastModifiedDate` work with `@EntityListeners(AuditingEntityListener.class)` and `@EnableJpaAuditing`, and `@CreatedBy` and `@LastModifiedBy` take their values from an `AuditorAware` bean. The Hibernate annotations are simpler and need no configuration, but they are specific to Hibernate.

### The persistence context and first-level cache

The `EntityManager` (Hibernate's `Session`) holds the **persistence context**, which is also the first-level cache. Within one context, loading the same ID twice returns the same Java object. The cache lasts only for the context, usually one transaction.

A second-level cache is optional and shared across sessions. It needs explicit configuration and cache invalidation rules.

### Detached entities and merge

An entity is detached once its context closes. Changes to a detached object are not saved automatically. `merge()` copies a detached object's state onto a managed copy and returns that copy; use the returned instance, not the original.

### ID generation strategies

The `@GeneratedValue` strategy decides where an identifier comes from. Pick it with the target database in mind.

| Strategy | Source of the ID | Notes |
|---|---|---|
| `IDENTITY` | Auto-increment column | Simple. Hibernate must run the INSERT to learn the ID, so insert batching is limited |
| `SEQUENCE` | Database sequence | Preferred on PostgreSQL, Oracle, and similar. `allocationSize` must match the sequence's increment |
| `TABLE` | Rows in a helper table | Portable, but slow under contention; rarely the right choice now |
| `AUTO` | Chosen by the dialect | Convenient, but the strategy can change when you switch databases |
| Assigned in code | Your application | Used for UUIDs created in the application and for imports that carry their own IDs |

```java
import jakarta.persistence.*;

@Entity
public class Invoice {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "invoice_seq")
    @SequenceGenerator(name = "invoice_seq", sequenceName = "invoice_seq", allocationSize = 50)
    private Long id;   // the sequence must be created with INCREMENT BY 50
}
```

A UUID assigned in code needs no database round trip and stays unique across services:

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.util.UUID;

@Entity
public class Shipment {

    @Id
    private UUID id = UUID.randomUUID();   // assigned before persist
}
```

### Persisting: persist, save, merge, and update

Four operations come up in interviews. They differ in the state the entity must be in when you call them.

| Operation | Expected input | Result | Typical use |
|---|---|---|---|
| `persist` (JPA `EntityManager`) | New (transient) | Managed; INSERT at flush or commit | Creating new entities |
| `save` (Spring Data) | New or detached | Returns the managed instance | Everyday repository writes |
| `merge` (JPA) | Detached | Returns a new managed copy; the argument stays detached | Writing back a detached object |
| `update` (Hibernate `Session`) | Detached | Reattaches the same object for an UPDATE | Rare. It is a Hibernate-native API; `EntityManager` has no `update` method |

Spring Data's `save` calls `persist` when the entity is new (its ID is null, or it has no version value) and `merge` otherwise. With `SEQUENCE`, the ID is fetched at `persist` time. With `IDENTITY`, Hibernate runs the INSERT straight away to get the ID.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Id;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Entity
class Customer {
    @Id
    private Long id;
    private String name;

    void setName(String name) { this.name = name; }
}

@Service
class CustomerWriter {

    private final EntityManager em;

    CustomerWriter(EntityManager em) {
        this.em = em;
    }

    @Transactional
    public Customer rename(Long id, String newName) {
        Customer managed = em.find(Customer.class, id);
        managed.setName(newName);     // dirty checking writes the UPDATE at commit
        return managed;
    }

    @Transactional
    public Customer saveDetached(Customer detached) {
        return em.merge(detached);    // use the returned instance, not the argument
    }
}
```

### Dirty checking and flush

Hibernate keeps a snapshot of each managed entity's state. At flush, it compares the current state with the snapshot and writes SQL for the differences. That is why a managed entity needs no explicit save.

- A flush runs before commit. In the default `AUTO` mode it also runs before a query, so the query sees the pending changes.
- `em.flush()` sends pending SQL now, still inside the transaction. `em.clear()` detaches everything, which helps in long batch jobs that would otherwise grow the persistence context.
- Without a transaction there is no commit point. A read returns a detached entity (unless open-session-in-view is active), so later changes are never written.

### Cascade types

`cascade` says which operations on the parent also apply to its children.

| Type | Effect on children |
|---|---|
| `PERSIST` | Persisted with the parent |
| `MERGE` | Merged with the parent |
| `REMOVE` | Removed with the parent |
| `REFRESH` | Reloaded with the parent |
| `DETACH` | Detached with the parent |
| `ALL` | All of the above |

`orphanRemoval = true` goes further: a child removed from the collection is deleted. Use cascades for children the parent owns, such as order lines. Cascading `REMOVE` across a shared association deletes rows that other parents still use.

### Many-to-many and one-to-one

A many-to-many association needs a join table. One side owns it with `@JoinTable`; the other side points back with `mappedBy`.

```java
import jakarta.persistence.*;
import java.util.HashSet;
import java.util.Set;

@Entity
class Student {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @ManyToMany
    @JoinTable(name = "student_course",
            joinColumns = @JoinColumn(name = "student_id"),
            inverseJoinColumns = @JoinColumn(name = "course_id"))
    Set<Course> courses = new HashSet<>();
}

@Entity
class Course {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @ManyToMany(mappedBy = "courses")
    Set<Student> students = new HashSet<>();
}
```

A one-to-one works the same way: the side with `@JoinColumn` owns the foreign key, and the inverse side uses `mappedBy`. Update both sides in code, as the `addLine` helper above does.

### Composite keys with @EmbeddedId and @MapsId

A join entity can use a composite key built from the two foreign keys. `@MapsId` says that the `order` association supplies one part of that key.

```java
import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
class OrderItemKey implements Serializable {
    Long orderId;
    Long productId;

    @Override
    public boolean equals(Object o) {
        return o instanceof OrderItemKey k
                && Objects.equals(orderId, k.orderId)
                && Objects.equals(productId, k.productId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(orderId, productId);
    }
}

@Entity
class OrderItem {
    @EmbeddedId
    OrderItemKey id;

    @ManyToOne(optional = false)
    @MapsId("orderId")
    Order order;   // the Order entity shown earlier on this page
}
```

The embedded key must implement `Serializable`, and `equals` and `hashCode` must use every field.

### Choosing identifiers

- Use a surrogate key (a `Long` from `IDENTITY` or `SEQUENCE`, or a `UUID`) as the primary key.
- Keep natural keys such as e-mail addresses as unique constraints, not as primary keys. If the value changes, it would have to change in every foreign key.
- Use UUIDs when IDs are created outside the database, for example by distributed services or offline clients. They are larger and index less compactly than sequential numbers.

### Batch fetching and extra-lazy collections

When a join fetch is not possible (for example, you need pagination), batch fetching loads children for several parents in one query.

```java
import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;
import org.hibernate.annotations.BatchSize;

@Entity
class Department {
    @Id
    Long id;

    @OneToMany(mappedBy = "department")
    @BatchSize(size = 20)
    List<Employee> employees = new ArrayList<>();
}

@Entity
class Employee {
    @Id
    Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    Department department;
}
```

`@BatchSize` is Hibernate-specific. The portable setting is `hibernate.default_batch_fetch_size` in configuration. Hibernate's `@LazyCollection(LazyCollectionOption.EXTRA)` can count or check a collection without loading all of it, but it is Hibernate-only, so use it with care.

## How it works / Step by step

What happens during `entityManager.persist(order)` inside a transaction:

1. The entity becomes managed and gets an ID (immediately for `IDENTITY`, at flush for `SEQUENCE` with batching).
2. Cascades run: child entities marked with `CascadeType.PERSIST` are persisted too.
3. At flush (before commit or before a query that needs it), Hibernate computes SQL from the changes and sends it.
4. On commit, the transaction ends; the context closes, and the entities become detached.

## StatelessSession

A `StatelessSession` is a Hibernate session without a persistence context: no first-level cache, no dirty checking, no cascades, and no lazy loading. It suits bulk inserts and updates where tracking every entity wastes memory. Changes are not saved automatically, so call `update()` yourself. Entity listeners are not called. Open it with `emf.unwrap(SessionFactory.class).openStatelessSession()`, and for speed set `hibernate.jdbc.batch_size` and commit in chunks.

```java
import java.util.List;
import org.hibernate.SessionFactory;
import org.hibernate.StatelessSession;
import org.hibernate.Transaction;

class RowImporter {

    static <T> void insertAll(SessionFactory sessionFactory, List<T> rows) {
        StatelessSession session = sessionFactory.openStatelessSession();
        try {
            Transaction tx = session.beginTransaction();
            for (T row : rows) {
                session.insert(row);
            }
            tx.commit();
        } finally {
            session.close();
        }
    }
}
```

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
