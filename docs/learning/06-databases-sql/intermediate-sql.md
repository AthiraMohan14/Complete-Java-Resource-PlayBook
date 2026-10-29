# Intermediate SQL

Intermediate SQL covers the queries most applications need: filtering and sorting, joins across tables, aggregation, subqueries, and set operations. Interviewers use these to see whether you can translate a business question into a correct query, and whether you notice duplicate rows or missing data.

## Core concepts

### Filtering, sorting and paging

```sql
SELECT DISTINCT customer_id
FROM orders
WHERE status IN ('PAID', 'SHIPPED')
  AND total_cents BETWEEN 1000 AND 50000
ORDER BY customer_id DESC
LIMIT 20 OFFSET 40;
```

`LIMIT` and `OFFSET` are not standard SQL. SQL Server uses `TOP` and `OFFSET ... FETCH`; Oracle uses `FETCH FIRST`. Large `OFFSET` values are slow because the database still reads the skipped rows. For deep pagination, use keyset pagination (`WHERE id > :lastSeenId ORDER BY id LIMIT 20`).

### Joins

A join combines rows from two tables on a condition.

```sql
SELECT c.full_name, o.order_id, o.total_cents
FROM customer AS c
INNER JOIN orders AS o ON o.customer_id = c.customer_id;
```

| Join | Returns |
|---|---|
| `INNER JOIN` | Rows that match in both tables |
| `LEFT JOIN` | All rows from the left table; matching right rows or NULLs |
| `RIGHT JOIN` | All rows from the right table; matching left rows or NULLs |
| `FULL OUTER JOIN` | All rows from both; NULLs where there is no match (not in MySQL) |
| `CROSS JOIN` | Every combination of rows (Cartesian product) |
| Self-join | A table joined to itself, using two aliases |

Find customers with no orders:

```sql
SELECT c.customer_id
FROM customer AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;
```

Put a condition on the right table inside the `ON` clause of a `LEFT JOIN`, not in `WHERE`. A `WHERE` filter on the right table turns the join into an inner join.

Self-join example: employees and their managers.

```sql
SELECT e.full_name AS employee, m.full_name AS manager
FROM employee AS e
LEFT JOIN employee AS m ON m.employee_id = e.manager_id;
```

### Aggregates and GROUP BY

Aggregates collapse many rows into one: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`. `COUNT(*)` counts rows; `COUNT(column)` skips NULLs.

```sql
SELECT customer_id,
       COUNT(*)         AS order_count,
       SUM(total_cents) AS spent_cents
FROM orders
WHERE status = 'PAID'
GROUP BY customer_id
HAVING COUNT(*) >= 3;
```

`WHERE` filters rows before grouping; `HAVING` filters groups after aggregation. Every column in `SELECT` must be in `GROUP BY` or inside an aggregate.

### Subqueries

- **Scalar subquery:** returns one value, used like a column or constant.
- **Inline view:** a subquery in `FROM`, given an alias.
- **Correlated subquery:** refers to the outer query and runs per outer row.

```sql
-- Orders above the average for their own customer (correlated)
SELECT o.order_id
FROM orders AS o
WHERE o.total_cents > (
    SELECT AVG(o2.total_cents)
    FROM orders AS o2
    WHERE o2.customer_id = o.customer_id
);
```

`EXISTS` checks whether a subquery returns any row and often beats `IN` for large sets:

```sql
SELECT c.customer_id
FROM customer AS c
WHERE NOT EXISTS (
    SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id
);
```

Prefer `NOT EXISTS` over `NOT IN` with a subquery. If the subquery returns any NULL, `NOT IN` returns no rows at all.

### Set operations

`UNION` combines results and removes duplicates; `UNION ALL` keeps them and is faster. `INTERSECT` returns rows in both results; `EXCEPT` (called `MINUS` in Oracle) returns rows in the first result but not the second. Both sides must have the same number of columns with compatible types.

### CASE expressions

`CASE` works like an if-else inside a query:

```sql
SELECT order_id,
       CASE
           WHEN total_cents >= 10000 THEN 'large'
           WHEN total_cents >= 1000  THEN 'medium'
           ELSE 'small'
       END AS size_band
FROM orders;
```

## How it works / Step by step

To write a multi-table query:

1. Identify the grain: one row per what? (per order, per customer, per day).
2. Start with the main table and add joins one at a time, checking the row count after each.
3. Add `WHERE` filters on the main table where possible.
4. Aggregate with `GROUP BY` at the grain you chose.
5. Add `HAVING`, `ORDER BY`, and paging last.

If a count looks too high after a join, a one-to-many relationship is multiplying rows. Aggregate before joining, or use `COUNT(DISTINCT ...)`.

## Common pitfalls

- Filtering a `LEFT JOIN`'s right table in `WHERE`, which silently makes it an inner join.
- Using `NOT IN` with a subquery that can return NULL.
- Using `DISTINCT` to hide a join that multiplied rows. Fix the join.
- Writing `COUNT(column)` when you meant `COUNT(*)`, and missing NULL rows.
- Assuming `UNION` preserves order. Add `ORDER BY` at the end.
- Using `OFFSET` for deep pagination on large tables.

!!! tip "Interview tip"
    **Q: How do you find rows in one table with no matching rows in another?**
    Use `LEFT JOIN` and filter on `IS NULL`, or `NOT EXISTS`. Both work; `NOT EXISTS` avoids the `NOT IN` NULL trap and reads clearly. State which one you chose and why.

## Quick recap

- Joins combine tables; `LEFT JOIN` plus `IS NULL` finds unmatched rows.
- `WHERE` filters rows before grouping; `HAVING` filters groups after.
- Use `NOT EXISTS` rather than `NOT IN` when NULLs are possible.
- Check row counts after each join; one-to-many joins multiply rows.
- Keyset pagination scales better than large `OFFSET` values.

**See also:** [SQL Fundamentals](sql-fundamentals.md), [Advanced SQL and Transactions](advanced-sql-transactions.md), [Query Optimisation](query-optimisation.md)
