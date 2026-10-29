# Advanced SQL and Transactions

Advanced SQL adds window functions and common table expressions (CTEs) for analytical and hierarchical queries, and transactions control how changes commit or roll back under concurrency. Interviewers ask about ACID and isolation levels to find out whether you can reason about race conditions, not just write queries.

## Core concepts

### Window functions

A window function computes a value across a set of related rows without collapsing them, unlike `GROUP BY`. The `OVER` clause defines the window.

```sql
SELECT customer_id,
       order_id,
       total_cents,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_cents DESC) AS rn,
       RANK()       OVER (PARTITION BY customer_id ORDER BY total_cents DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY total_cents DESC) AS drnk
FROM orders;
```

| Function | Behaviour |
|---|---|
| `ROW_NUMBER` | Unique sequence 1, 2, 3 with no ties |
| `RANK` | Ties share a rank; the next rank is skipped (1, 1, 3) |
| `DENSE_RANK` | Ties share a rank; no gaps (1, 1, 2) |
| `LAG(col, n)` | Value from `n` rows earlier |
| `LEAD(col, n)` | Value from `n` rows later |
| `FIRST_VALUE`, `LAST_VALUE` | First or last value in the window frame |

A common use is "latest order per customer":

```sql
SELECT customer_id, order_id, total_cents
FROM (
    SELECT o.*,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_on DESC) AS rn
    FROM orders AS o
) AS ranked
WHERE rn = 1;
```

`LAST_VALUE` needs an explicit frame (`ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`); without it, the default frame ends at the current row and the result often surprises people.

### Common table expressions (CTEs)

A CTE names a subquery with `WITH`, which makes long queries readable.

```sql
WITH paid AS (
    SELECT customer_id, total_cents
    FROM orders
    WHERE status = 'PAID'
)
SELECT customer_id, SUM(total_cents) AS spent_cents
FROM paid
GROUP BY customer_id;
```

A **recursive CTE** walks a hierarchy, such as an org chart. It has an anchor member and a recursive member joined with `UNION ALL`:

```sql
WITH RECURSIVE reports AS (
    SELECT employee_id, manager_id, full_name, 1 AS depth
    FROM employee
    WHERE manager_id IS NULL                       -- anchor: top of the hierarchy
    UNION ALL
    SELECT e.employee_id, e.manager_id, e.full_name, r.depth + 1
    FROM employee AS e
    JOIN reports AS r ON e.manager_id = r.employee_id   -- recursive member
)
SELECT full_name, depth FROM reports;
```

Guard against cycles in the data; a cycle makes the recursion run forever in some databases.

### Transactions

A transaction groups statements so they succeed or fail together.

```sql
BEGIN;                                  -- or START TRANSACTION in MySQL
UPDATE account SET balance = balance - 100 WHERE account_id = 1;
UPDATE account SET balance = balance + 100 WHERE account_id = 2;
COMMIT;                                 -- or ROLLBACK to undo everything
```

`SAVEPOINT` marks a point inside a transaction you can roll back to:

```sql
SAVEPOINT before_fee;
UPDATE account SET balance = balance - 5 WHERE account_id = 1;
ROLLBACK TO SAVEPOINT before_fee;       -- undoes only the fee
COMMIT;
```

### ACID

| Property | Meaning |
|---|---|
| Atomicity | All statements in the transaction apply, or none do |
| Consistency | The database moves from one valid state to another, respecting constraints |
| Isolation | Concurrent transactions do not see each other's partial work, to the degree the isolation level allows |
| Durability | Committed data survives a crash (typically through a write-ahead log) |

### Isolation levels and anomalies

Concurrent transactions can cause anomalies:

- **Dirty read:** reading another transaction's uncommitted change.
- **Non-repeatable read:** the same row, read twice, returns different values.
- **Phantom read:** the same query, run twice, returns different sets of rows.
- **Lost update:** two transactions read the same value and both write, so one update is overwritten.

| Isolation level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | Possible | Possible | Possible |
| Read Committed | No | Possible | Possible |
| Repeatable Read | No | No | Possible in the SQL standard |
| Serializable | No | No | No |

Implementations differ. PostgreSQL's Repeatable Read is snapshot-based and does not allow phantoms; PostgreSQL treats Read Uncommitted as Read Committed. MySQL InnoDB's default is Repeatable Read. Check your database's documentation rather than the standard alone.

### Locking and deadlocks

Databases use locks to prevent conflicting writes:

- **Shared (read) lock:** many readers may hold it.
- **Exclusive (write) lock:** one writer, no other readers of the same row under locking isolation.
- **Pessimistic locking:** `SELECT ... FOR UPDATE` locks rows until commit.
- **Optimistic locking:** a version column is checked on update; if it changed, the update fails and the application retries.

A **deadlock** happens when transactions wait on each other in a cycle. The database detects it and aborts one transaction. Prevent deadlocks by acquiring locks in a consistent order and keeping transactions short.

```sql
-- Pessimistic: lock the row before changing it
BEGIN;
SELECT balance FROM account WHERE account_id = 1 FOR UPDATE;
UPDATE account SET balance = balance - 100 WHERE account_id = 1;
COMMIT;
```

## How it works / Step by step

Handling a concurrent update safely:

1. Decide which level of protection the business rule needs (lost update, double spend, overbooking).
2. Use a single atomic statement when possible (`UPDATE ... SET qty = qty - 1 WHERE qty > 0`) and check the affected row count.
3. Otherwise, lock the rows (`FOR UPDATE`) or use optimistic versioning.
4. Keep the transaction short and acquire locks in the same order everywhere.
5. Retry on deadlock or serialization failure.

## Common pitfalls

- Running a long transaction that holds locks while waiting for an external HTTP call.
- Assuming Read Committed prevents lost updates. It does not; use an atomic update or locking.
- Reading a value in the application, computing, and writing it back without locking.
- Forgetting that auto-commit is on in many drivers, so each statement commits on its own.
- Not retrying deadlock errors.
- Using `LAST_VALUE` without a full frame clause.

!!! tip "Interview tip"
    **Q: How would you prevent two customers from buying the last item?**
    Make the decrement atomic, for example `UPDATE stock SET qty = qty - 1 WHERE item_id = ? AND qty > 0`, and check the row count. Alternatively, lock the row with `SELECT ... FOR UPDATE` inside a transaction. Mention that a read-then-write in application code is the classic race condition.

## Quick recap

- Window functions compute per-row results over partitions without collapsing rows.
- Recursive CTEs walk hierarchies; guard against cycles.
- ACID covers atomicity, consistency, isolation, and durability.
- Isolation levels trade anomalies for concurrency; check your database's actual behaviour.
- Use atomic updates, `FOR UPDATE`, or optimistic versioning to prevent lost updates.

**See also:** [Intermediate SQL](intermediate-sql.md), [Query Optimisation](query-optimisation.md), [JDBC](../07-jdbc-jpa/jdbc.md)
