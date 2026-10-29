# Data and Persistence Questions (Part 1 of 2)

Questions on SQL, indexing, transactions and isolation, JDBC, JPA and Hibernate, Spring Data, schema migrations, and the common data stores. Expect follow-ups that ask you to explain a query plan or a slow endpoint.

---


This page is split into 2 parts. Continue to [Part 2](data-and-persistence-part-2.md).

## 1. What is the difference between a primary key, a unique key, and a foreign key?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A primary key uniquely identifies each row and cannot be `NULL`. A table has one primary key. A unique constraint also forbids duplicates, but it allows `NULL` (the rules for multiple `NULL`s vary by database), and a table can have several. A foreign key requires a value to exist in the referenced table's key column, which protects referential integrity.

### Explanation
```sql
CREATE TABLE customers (
    id    BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE orders (
    id          BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers (id)
);
```

Deleting a customer with orders fails unless you define `ON DELETE CASCADE` or remove the orders first.

### When to use / pitfalls
- Add an index on the foreign key column in most databases. Joins and deletes on the parent otherwise scan the child table. MySQL InnoDB creates one automatically; PostgreSQL does not.
- Surrogate keys (generated IDs) are common; natural keys like email change over time.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 2. What is the difference between `INNER JOIN` and `LEFT JOIN`, and between `WHERE` and `HAVING`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`INNER JOIN` returns only rows that match on both sides. `LEFT JOIN` returns every row from the left table and fills unmatched right-side columns with `NULL`. `WHERE` filters individual rows before grouping; `HAVING` filters groups after `GROUP BY`.

### Explanation
```sql
-- Customers with their order count, including customers who have no orders
SELECT c.id, c.email, COUNT(o.id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.email
HAVING COUNT(o.id) >= 0      -- HAVING acts on the groups
ORDER BY order_count DESC;
```

A condition on the right table placed in `WHERE` turns a `LEFT JOIN` into an effective inner join, because `NULL` rows fail the test. Put that condition in the `ON` clause instead when you want to keep the unmatched rows.

### When to use / pitfalls
- `COUNT(*)` counts rows including `NULL`s; `COUNT(column)` skips `NULL`s.
- Joining without a condition on a large table produces a cross product, which is a common cause of slow queries.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 3. What are window functions, and how do they differ from `GROUP BY`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A window function computes a value across a set of related rows but keeps every row in the output. `GROUP BY` collapses rows into one row per group. `ROW_NUMBER`, `RANK`, and `DENSE_RANK` number rows within a partition, and `LAG` and `LEAD` read values from neighbouring rows.

### Explanation
```sql
-- Top two salaries in each department
SELECT dept, name, salary
FROM (
    SELECT dept, name, salary,
           ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS rn
    FROM employees
) ranked
WHERE rn <= 2;
```

`ROW_NUMBER` gives unique numbers even on ties. `RANK` leaves gaps after ties (1, 1, 3). `DENSE_RANK` does not leave gaps (1, 1, 2).

### When to use / pitfalls
- You cannot filter on a window function in `WHERE`, because it runs after `WHERE`. Wrap the query in a subquery or CTE, as above.
- Window functions over large partitions can be expensive; index the partition and order columns.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 4. What is a common table expression, and when is a recursive CTE useful?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A CTE is a named query defined with `WITH` that you can reference in the main query, which makes complex SQL readable. A recursive CTE refers to itself and is used for hierarchies and graphs, such as an organisation chart or a bill of materials.

### Explanation
```sql
WITH RECURSIVE reports AS (
    SELECT id, name, manager_id, 0 AS depth
    FROM staff
    WHERE id = 1                             -- the starting manager
    UNION ALL
    SELECT s.id, s.name, s.manager_id, r.depth + 1
    FROM staff s
    JOIN reports r ON s.manager_id = r.id    -- walk one level down each pass
)
SELECT name, depth FROM reports;
```

### When to use / pitfalls
- A recursive CTE without a stop condition loops forever in some databases. Check that each pass moves toward the end of the data.
- CTEs are not always materialised; behaviour differs between databases and versions. Check `EXPLAIN` before assuming a CTE is cached.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 5. How do B-tree indexes work, and what is the leftmost-prefix rule?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A B-tree index keeps keys sorted in a balanced tree, so the database finds a value or a range in a few page reads. A composite index on `(a, b, c)` can serve queries that filter on `a`, on `a` and `b`, or on all three. It cannot efficiently serve a query that filters only on `b` or only on `c`.

### Explanation
```sql
CREATE INDEX idx_orders_customer_date ON orders (customer_id, created_at);

-- Uses the index: leftmost column is filtered
SELECT * FROM orders WHERE customer_id = 42 AND created_at >= '2026-01-01';

-- Usually cannot use the index efficiently: the leading column is missing
SELECT * FROM orders WHERE created_at >= '2026-01-01';
```

A covering index includes every column the query reads, so the database can answer from the index alone.

### When to use / pitfalls
- Every index slows inserts, updates, and deletes, and takes disk space. Index what your queries filter, join, and sort on, not every column.
- Functions on indexed columns, such as `WHERE LOWER(email) = ...`, block a plain index on `email`. Create a functional index or store the normalised value.
- Low-selectivity columns, such as a boolean flag, rarely benefit from a standalone index.
- Hash, bitmap, and full-text indexes exist for specific workloads; choose by the query pattern.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 6. How do you read a query plan with `EXPLAIN`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`EXPLAIN` shows how the database intends to run a query: which scan method it uses, in which order it joins tables, and its estimated cost and row counts. `EXPLAIN ANALYZE` (in PostgreSQL, and in MySQL 8.0.18 and later) also runs the query and shows the actual timings. Look for full table scans on large tables and large differences between estimated and actual row counts.

### Explanation
```sql
EXPLAIN ANALYZE
SELECT o.id, o.total
FROM orders o
WHERE o.customer_id = 42
ORDER BY o.created_at DESC
LIMIT 20;
```

Typical things to check:

- A sequential or full scan on a large table where you expected an index scan.
- A sort step that could be avoided with an index in the right order.
- Estimated rows far from actual rows. Run `ANALYZE` (or the database's statistics update) so the planner has current statistics.

### When to use / pitfalls
- Test with production-like data volumes. A query that is fast on 100 rows can choose a different plan at scale.
- Do not add indexes blindly. Measure the query before and after the change.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 7. What do ACID properties mean?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Atomicity means a transaction either completes entirely or has no effect. Consistency means each transaction moves the data from one valid state to another, respecting constraints. Isolation means concurrent transactions do not interfere in ways the chosen isolation level forbids. Durability means committed data survives a crash.

### Explanation
A bank transfer is the classic example: debit one account and credit another in one transaction. If the credit fails, the debit must roll back, so money is never lost or duplicated.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;   -- or ROLLBACK on error
```

### When to use / pitfalls
- Durability depends on configuration. Some databases allow relaxed flush settings for speed; know the trade-off before you choose them.
- Distributed transactions across services do not get ACID for free. See [Architecture and distributed systems](architecture-and-distributed.md) for sagas.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 8. What are the isolation levels, and which anomalies does each one prevent?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The SQL standard defines four isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable. Higher levels prevent more anomalies (dirty reads, non-repeatable reads, and phantom reads) at a cost in concurrency. Actual behaviour varies by database, so check the documentation of the one you use.

### Explanation
| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | possible | possible | possible |
| Read Committed | prevented | possible | possible |
| Repeatable Read | prevented | prevented | possible in the standard |
| Serializable | prevented | prevented | prevented |

Defaults worth knowing: PostgreSQL uses Read Committed, and MySQL InnoDB uses Repeatable Read. PostgreSQL's Repeatable Read is snapshot-based, and InnoDB uses next-key locking, so each behaves differently from the standard table.

In Spring: `@Transactional(isolation = Isolation.READ_COMMITTED)` sets the level for that method.

### When to use / pitfalls
- Serializable is the safest and the slowest; it can cause more retries and deadlocks.
- Many bugs are "lost updates" from read-modify-write logic. Isolation alone may not fix them; use a locking strategy (question 9).

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 9. What is the difference between optimistic and pessimistic locking?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Pessimistic locking takes a database lock on the row at read time, such as `SELECT ... FOR UPDATE`, so other writers wait. Optimistic locking does not lock; it adds a version column and the update succeeds only if the version has not changed since it was read. Optimistic locking suits low contention, and pessimistic locking suits high contention on short transactions.

### Explanation
```java
import jakarta.persistence.*;

@Entity
class Product {
    @Id
    @GeneratedValue
    Long id;

    int stock;

    @Version                  // JPA increments this on each update and checks it
    Long version;
}
```

If two transactions update the same row, the second one fails with an optimistic locking exception, and the application retries or reports a conflict. Pessimistic locking in JPA uses `entityManager.find(Product.class, id, LockModeType.PESSIMISTIC_WRITE)` or `@Lock` on a repository method.

### When to use / pitfalls
- Retry optimistic failures with a bounded retry count, not an infinite loop.
- Keep pessimistic lock scopes short; holding a lock across a remote call invites deadlocks and timeouts.
- Lock rows in a consistent order to avoid deadlocks between transactions.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 10. What are the normal forms, and when would you denormalise?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
First normal form requires atomic values and no repeating groups. Second normal form removes partial dependencies on part of a composite key. Third normal form removes transitive dependencies (a non-key column depends on another non-key column). BCNF is a stricter version of 3NF. You denormalise when reads are far more frequent than writes and a join is too costly, accepting redundant data and more complex updates.

### Explanation
A table of order lines that stores `customer_city` next to `customer_id` has a transitive dependency: the city depends on the customer, not on the order line. Moving the city into a `customers` table fixes that under 3NF.

Denormalisation options include storing a computed total on the order, keeping a summary table, or using a materialised view that the database refreshes.

### When to use / pitfalls
- Denormalise after you measure a real problem, not by default.
- Every copy of the data is a place where it can drift. Document which copy is authoritative.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 11. How does JDBC work, and why must you use `PreparedStatement`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
JDBC is the Java API for talking to relational databases. You obtain a `Connection` through a driver, create a statement, execute it, and read the `ResultSet`. `PreparedStatement` sends the SQL once with placeholders and binds values separately, which prevents SQL injection and lets the database reuse the plan.

### Explanation
```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

class CustomerLookup {
    static String emailFor(Connection conn, long id) throws SQLException {
        String sql = "SELECT email FROM customers WHERE id = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);                       // bound value, never concatenated
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getString("email") : null;
            }
        }
    }
}
```

Connections are expensive to create, so production code uses a pool. Spring Boot uses HikariCP by default.

### When to use / pitfalls
- Never build SQL with string concatenation from user input.
- Always close statements and result sets; try-with-resources does this for you.
- Size the pool to the database's capacity, not to the number of application threads. A pool that is too large overloads the database.

**See also:** [Core Java](core-java-part-1.md), [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 12. How do you manage transactions in plain JDBC?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A JDBC connection autocommits by default. Turn that off with `setAutoCommit(false)`, run the statements, call `commit()` on success, and call `rollback()` on failure. Savepoints let you roll back part of a transaction.

### Explanation
```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

class Transfers {
    static void move(Connection conn, long from, long to, long cents) throws SQLException {
        conn.setAutoCommit(false);
        try (PreparedStatement debit = conn.prepareStatement(
                 "UPDATE accounts SET balance = balance - ? WHERE id = ?");
             PreparedStatement credit = conn.prepareStatement(
                 "UPDATE accounts SET balance = balance + ? WHERE id = ?")) {
            debit.setLong(1, cents);
            debit.setLong(2, from);
            debit.executeUpdate();

            credit.setLong(1, cents);
            credit.setLong(2, to);
            credit.executeUpdate();

            conn.commit();
        } catch (SQLException e) {
            conn.rollback();
            throw e;
        } finally {
            conn.setAutoCommit(true);
        }
    }
}
```

### When to use / pitfalls
- A transaction that is open for a long time holds locks and blocks other sessions.
- Spring's `@Transactional` does this for you. Know the plain JDBC version, because interviewers ask how the framework does it.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---


**Next:** [Part 2](data-and-persistence-part-2.md)
