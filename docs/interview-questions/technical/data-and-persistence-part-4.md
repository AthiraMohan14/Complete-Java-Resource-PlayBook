# Data and Persistence Questions (Part 4 of 4)

Continued from [Part 3](data-and-persistence-part-3.md).

---

## 35. What happens in persist(), save(), and merge() in the Hibernate or JPA lifecycle?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`persist()` takes a new object and makes it managed, so Hibernate will insert it. `merge()` takes an object that is detached (or new with an id) and copies its state onto a managed instance, then returns that managed instance. Spring Data's `save()` calls one or the other depending on whether the entity is new. Because `merge()` can return a different object, always use its return value.

### Explanation
**Entity states.** A *transient* object has never been saved and is not tracked. A *managed* (persistent) object belongs to the current persistence context, and Hibernate tracks its changes. A *detached* object was managed once, but its context has closed or it was evicted. A *removed* object is scheduled for deletion.

**persist().** The argument itself becomes managed, and nothing is returned. A new id is generated according to the strategy. With `IDENTITY`, the INSERT runs immediately, because the database must assign the id. With `SEQUENCE`, the id is fetched at `persist()` time and the INSERT waits for the flush. Passing a detached entity to `persist()` is an error.

**merge().** Hibernate finds the managed instance for the id. If the context does not have it, Hibernate loads it with a SELECT. It then copies the state of your object onto that instance and returns it. If the argument is already managed, the same instance comes back. If the argument is detached, the returned instance is a different object from the argument, so changes made to the argument afterwards are not tracked.

**save() in Spring Data.** The repository checks whether the entity is new. An entity with a null id (or a null `@Version`) is treated as new, and `save()` calls `persist()`. Any other entity gets `merge()`. The return value is the object to use from then on.

**Dirty checking.** A managed entity keeps a snapshot of the state it was loaded with. At flush time (before a commit, or before a query that touches the table), Hibernate compares each managed entity with its snapshot and issues an UPDATE for each changed entity. So a change to a managed entity inside a transaction is saved without any call to `save()`.

```java
import jakarta.persistence.EntityManager;
import org.springframework.transaction.annotation.Transactional;

class CustomerEditor {

    private EntityManager em;

    static class Customer {
        private String name;
        void setName(String name) { this.name = name; }
    }

    @Transactional
    public void rename(long id, String name) {
        Customer c = em.find(Customer.class, id);   // managed
        c.setName(name);                            // tracked; UPDATE at flush or commit
    }

    void detachAndMerge() {
        Customer detached = em.find(Customer.class, 7L);
        em.detach(detached);
        detached.setName("New");                        // not tracked
        Customer managed = em.merge(detached);          // managed != detached
    }
}
```

### When to use / pitfalls
- Without a transaction, changes to a loaded entity are not flushed, unless a persistence context is still open (for example, the open-in-view setting in a web request). Put the unit of work in a transactional service method rather than relying on that.
- Ignoring the return value of `merge()` or `save()` and then changing the original object loses those changes.
- Calling `save()` on an entity with a manually assigned id can trigger a SELECT before the INSERT, because the entity looks existing. Add a `@Version` field or implement `Persistable` to make the new/existing decision explicit.
- Prefer `persist()` for entities you just created. Use `merge()` for detached data, such as a request that refers to an existing row, and remember that it copies every field, including nulls.

**See also:** [JPA and Hibernate](../../learning/07-jdbc-jpa/jpa-hibernate.md), [Transactions in Spring](../../learning/08-spring-core/transactions.md)

</details>

---

## 36. When should you choose Hibernate or JPA over MyBatis, and vice versa?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Choose JPA with Hibernate when your code is organised around a domain model, most operations are standard create, read, update, and delete, and relationships between entities matter. Choose MyBatis when the SQL itself is the important part: complex reporting queries, tuned statements, legacy schemas that do not map cleanly to objects, or stored procedures. Neither is faster in general. The difference is who writes the SQL and how much control you keep over it.

### Explanation
**JPA and Hibernate** generate the SQL from mapped classes. You get change tracking, lazy loading, cascading, and caching for free, and less code for common operations. The cost is that the generated SQL is not always the SQL you would have written. Relationship loading is the usual trap, for example the N+1 problem when a list of parents loads each child in a separate query.

**MyBatis** maps SQL statements to methods and rows to objects. You write each query and control its joins, indexes, and batching. It needs more code, and it does not track changes, so updates are explicit. It works well when a team is comfortable with SQL and the access patterns are known in advance.

A common and sound design uses both. Standard writes and simple reads go through JPA, and the hard reporting or bulk queries go through MyBatis, in the same service layer and under the same transaction manager.

```text
// Pseudo-code: two styles side by side; types and wiring are omitted.
// JPA: standard lookup, relationships handled by the mapping
Customer customer = customers.findById(id).orElseThrow();

// MyBatis: a reporting query written and tuned by hand
@Select("SELECT region, SUM(total_cents) AS revenue FROM orders "
      + "WHERE placed_at >= #{since} GROUP BY region")
List<RegionRevenue> revenueSince(@Param("since") Instant since);
```

### When to use / pitfalls
- Use JPA for a domain-driven service with rich entities and frequent CRUD. Use MyBatis for analytics, bulk loads, or a schema you did not design.
- Do not expect either tool to fix a poor schema or missing indexes. Check the SQL either way.
- Mixing both is fine, but keep the boundaries clear, so a developer does not update the same row through two paths within one unit of work.
- Choose on the team's skills and the workload, and say so in the interview. The comparison table in the learning page covers the trade-offs in more detail.

**See also:** [MyBatis and JPA Comparison](../../learning/07-jdbc-jpa/mybatis-and-jpa-comparison.md), [JPA and Hibernate](../../learning/07-jdbc-jpa/jpa-hibernate.md)

</details>

---

## Quick recap

- Use `LEFT JOIN` with `IS NULL` to find unmatched rows, and put filters on the right table in `ON` when you want to keep them.
- `WHERE` filters rows, `HAVING` filters groups; keep the row filters in `WHERE`.
- Cache-aside: write the database, then invalidate the cache entry.
- CAP applies during a partition; choose consistency or availability per operation.
- ACID for money and stock, BASE for feeds and counters.
- Index for the filters you run, check `EXPLAIN`, and remember that every index costs writes.
- Denormalise only after measuring; `@Version` for optimistic locking; replicate for reads, shard for writes.
- `persist()` manages a new object, `merge()` returns the managed copy, and dirty checking flushes managed changes.
- Choose JPA for domain-centred CRUD and MyBatis for SQL-heavy work; a mix of both is common.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md), [Data and persistence part 2](data-and-persistence-part-2.md), [Architecture and distributed systems](architecture-and-distributed.md)
