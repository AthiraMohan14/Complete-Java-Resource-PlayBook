# Query Optimisation

Query optimisation is the work of making a database return the same answer faster. Interviewers ask about it to see whether you can read an execution plan, choose an index on purpose, and recognise problems such as N+1 queries and unnecessary scans.

## Core concepts

### How the optimiser chooses a plan

Given a SQL statement, the database parser builds a logical query, and the optimiser picks a physical plan: which index to use, which join algorithm, and in which order to join tables. The optimiser estimates the cost of each option from table statistics (row counts, value distribution). When statistics are stale, the plan can be poor, so keep statistics current (`ANALYZE` in PostgreSQL, `ANALYZE TABLE` in MySQL).

Common join algorithms:

- **Nested loop:** for each outer row, look up matches in the inner table. Fast when the inner side has an index and the outer side is small.
- **Hash join:** build a hash table on one input and probe it with the other. Good for large unsorted inputs with equality conditions.
- **Merge join:** walk two sorted inputs together. Good when both inputs are already sorted by the join key.

### Indexes

An index is a separate structure that maps column values to row locations, so the database can find rows without scanning the table.

| Index type | Good for | Notes |
|---|---|---|
| B-tree | Equality and range queries, `ORDER BY` | Default in most relational databases |
| Hash | Exact equality lookups | Not useful for ranges; support varies by database |
| Full-text | Searching words in text | Language-aware matching; see [Specific Databases](specific-databases.md) |
| GIN, GiST (PostgreSQL) | Arrays, JSONB, full text, geometry | Specialised index methods |

Bitmap indexes are common in data-warehouse systems, but most transactional databases use bitmap scans internally rather than exposing them as user-defined indexes. Describe them as a warehouse technique if asked.

A composite index on `(customer_id, created_on)` supports queries that filter on `customer_id` alone or on both columns. It does not help a filter on `created_on` alone. The leftmost-prefix rule applies.

```sql
CREATE INDEX idx_orders_customer_date ON orders (customer_id, created_on);

-- Uses the index (leftmost column is filtered)
SELECT order_id FROM orders WHERE customer_id = 42 AND created_on >= DATE '2026-01-01';

-- Usually cannot use this index efficiently
SELECT order_id FROM orders WHERE created_on >= DATE '2026-01-01';
```

Indexes are not free. Each one slows inserts and updates, takes storage, and must be maintained. Add indexes for queries you actually run, and remove unused ones.

A unique index is also a constraint: it rejects duplicate values, and it is the target that upserts need (see [Intermediate SQL](intermediate-sql.md)). Dropping an index needs vendor-specific syntax. MySQL and SQL Server use `DROP INDEX idx_orders_customer_date ON orders;`, while PostgreSQL uses `DROP INDEX idx_orders_customer_date;`. PostgreSQL's `DROP INDEX CONCURRENTLY` avoids blocking writes on a busy table.

### Reading execution plans with EXPLAIN

`EXPLAIN` shows the plan the optimiser chose. Some databases also run the query with `EXPLAIN ANALYZE` (PostgreSQL, and MySQL 8.0.18 and later through `EXPLAIN ANALYZE`) and report actual timings and row counts.

```sql
EXPLAIN ANALYZE
SELECT customer_id, COUNT(*)
FROM orders
WHERE status = 'PAID'
GROUP BY customer_id;
```

What to look for:

- **Sequential (full table) scan** on a large table where you expected an index. Check whether the predicate is sargable (see below).
- **Estimated rows far from actual rows.** Stale statistics or correlated columns are usually the cause.
- **Sort or hash spilling to disk.** Work memory may be too small, or the query returns too many rows.
- **Nested loops over large inputs.** Often a missing index on the inner side.

Read the plan from the innermost node outward; the cost is cumulative.

### Sargable predicates

A predicate is sargable (search-argument-able) when the database can use an index for it. Wrapping the indexed column in a function or doing arithmetic on it usually prevents index use.

```sql
-- Not sargable: the function hides the column from the index
SELECT order_id FROM orders WHERE YEAR(created_on) = 2026;

-- Sargable: a range on the bare column
SELECT order_id FROM orders
WHERE created_on >= DATE '2026-01-01' AND created_on < DATE '2027-01-01';
```

Leading wildcards also block index use: `LIKE '%smith'` cannot use a B-tree; `LIKE 'smi%'` can.

### N+1 queries and tuning

The N+1 problem: one query fetches N parent rows, then N more queries fetch each parent's children. It is the most common performance bug in ORM-based applications. Fix it with a join, a batched `IN` query, or a fetch-join in JPA.

```sql
-- Instead of one query per customer:
SELECT o.*
FROM orders AS o
WHERE o.customer_id IN (1, 2, 3, 4);
```

Other tuning moves:

- Select only the columns you need.
- Push filters into subqueries or CTEs only when the optimiser cannot do it for you; check the plan first.
- Rewrite correlated subqueries as joins or window functions when the plan shows repeated work.
- Use `UNION ALL` instead of `UNION` when duplicates are impossible or acceptable.

### Denormalisation and materialised views

Denormalisation stores redundant data to avoid joins on hot read paths, for example a copied `customer_name` on orders. It makes writes and consistency harder, so measure first.

A materialised view stores the result of a query and refreshes it on demand or on a schedule. PostgreSQL supports `CREATE MATERIALIZED VIEW`; MySQL does not have native materialised views, so teams use summary tables refreshed by jobs.

### Partitioning

Partitioning splits a large table into smaller physical pieces that the database manages as one logical table.

| Type | Splits rows by | Example |
|---|---|---|
| Range | Value range | Orders per month |
| List | Explicit values | Orders per country |
| Hash | Hash of a key | Spreading customers evenly |
| Composite | Two methods combined | Range by month, hash by customer |

Partition pruning lets queries that filter on the partition key read only the relevant partitions. A query that does not filter on the key scans all partitions, which can be worse.

## How it works / Step by step

A tuning workflow that avoids guesswork:

1. Measure: find the slow query in logs, the slow query log, or APM traces.
2. Capture the plan with `EXPLAIN ANALYZE` against realistic data volumes.
3. Find the most expensive node and why it is expensive (scan, sort, spill, wrong estimate).
4. Change one thing: add or fix an index, make the predicate sargable, or reduce the rows returned.
5. Measure again and compare plans. Keep the change only if it helps.

## Common pitfalls

- Adding indexes without checking that the query uses them.
- Wrapping indexed columns in functions in `WHERE` clauses.
- Assuming an index on `(a)` helps a query that filters only on `(b)`.
- Tuning on a small development dataset where the plan differs from production.
- Using `SELECT *` on wide tables, which increases I/O.
- Ignoring N+1 queries because each one is fast on its own.

!!! tip "Interview tip"
    **Q: A query is slow. What do you do first?**
    Run `EXPLAIN ANALYZE` on realistic data and find the most expensive step. Then decide whether the fix is an index, a sargable predicate, fewer rows, or a different join. Say that you measure before and after, and that you check statistics if the estimated and actual rows differ.

## Quick recap

- The optimiser picks plans from statistics; keep statistics current.
- B-tree indexes serve equality, ranges, and ordering; composite indexes follow the leftmost-prefix rule.
- Read `EXPLAIN ANALYZE` for scans, sorts, and bad row estimates.
- Keep predicates sargable: no functions on indexed columns, no leading wildcards.
- Fix N+1 queries with joins, batched `IN` lists, or fetch joins.

**See also:** [Intermediate SQL](intermediate-sql.md), [Normalisation and Modelling](normalisation-modelling.md), [Specific Databases](specific-databases.md)
