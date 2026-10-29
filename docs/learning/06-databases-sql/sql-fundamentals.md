# SQL Fundamentals

SQL (Structured Query Language) is the standard language for defining and querying relational databases. Interviewers start with the basics to check that you can design a table with the right constraints and write correct reads and writes before they move to joins and optimisation.

## Core concepts

### DDL: defining structure

Data Definition Language (DDL) creates and changes schema objects.

```sql
CREATE TABLE customer (
    customer_id  INT PRIMARY KEY,
    email        VARCHAR(255) NOT NULL UNIQUE,
    full_name    VARCHAR(120) NOT NULL,
    created_on   DATE NOT NULL DEFAULT CURRENT_DATE
);

ALTER TABLE customer ADD COLUMN phone VARCHAR(20);

DROP TABLE customer;          -- removes the table and its data
TRUNCATE TABLE audit_log;     -- removes all rows quickly; table structure stays
```

Key differences:

- `DROP` removes the table definition; `TRUNCATE` removes all rows and keeps the definition.
- `TRUNCATE` is usually not rollback-friendly across all databases, and it resets identity counters in many of them. Check your database before relying on rollback.
- `DELETE` removes rows one by one, can use a `WHERE` clause, and fires triggers.

### DML: reading and changing data

Data Manipulation Language (DML) reads and modifies rows.

```sql
INSERT INTO customer (customer_id, email, full_name)
VALUES (1, 'ana@example.com', 'Ana Silva');

SELECT customer_id, full_name
FROM customer
WHERE email = 'ana@example.com';

UPDATE customer
SET phone = '555-0100'
WHERE customer_id = 1;

DELETE FROM customer
WHERE customer_id = 1;
```

Always include a `WHERE` clause in `UPDATE` and `DELETE` unless you mean to change every row. Run the matching `SELECT` first.

### Constraints

Constraints enforce rules in the database, so bad data is rejected no matter which application writes it.

| Constraint | Purpose |
|---|---|
| `PRIMARY KEY` | Unique, not null identifier for each row; one per table |
| `FOREIGN KEY` | Value must exist in the referenced table's key |
| `UNIQUE` | No two rows share the value (NULLs follow database rules) |
| `NOT NULL` | Value must be present |
| `CHECK` | Value must satisfy a condition |
| `DEFAULT` | Value used when the insert omits the column |

```sql
CREATE TABLE orders (
    order_id     INT PRIMARY KEY,
    customer_id  INT NOT NULL REFERENCES customer (customer_id),
    total_cents  INT NOT NULL CHECK (total_cents >= 0),
    status       VARCHAR(20) NOT NULL DEFAULT 'NEW',
    created_on   DATE NOT NULL DEFAULT CURRENT_DATE
);
```

A foreign key with `ON DELETE CASCADE` deletes child rows automatically. Use it deliberately; it can delete more data than you expect.

### Data types

| Type | Use for | Note |
|---|---|---|
| `INT`, `BIGINT` | Whole numbers, identifiers | Watch for overflow on long-lived IDs; `BIGINT` is safer |
| `VARCHAR(n)` | Text with a maximum length | Length limit is part of the schema |
| `DATE`, `TIMESTAMP` | Calendar dates and points in time | Store timestamps with a time zone policy |
| `DECIMAL(p, s)` | Exact money and measures | Never use `FLOAT` or `DOUBLE` for currency |
| `BOOLEAN` | True or false | Some databases map it to `TINYINT(1)` |
| `JSON` | Semi-structured data | Behaviour varies; see [Specific Databases](specific-databases.md) |

### NULL semantics

`NULL` means unknown, not zero and not an empty string. Comparisons with `NULL` return unknown, so `WHERE x = NULL` matches nothing. Use `IS NULL` and `IS NOT NULL`.

```sql
SELECT customer_id FROM customer WHERE phone IS NULL;
```

## How it works / Step by step

A simple query runs in this logical order, which explains many surprises:

1. `FROM` (and joins) builds the rows to consider.
2. `WHERE` filters those rows.
3. `GROUP BY` groups them, and `HAVING` filters the groups.
4. `SELECT` computes the output columns.
5. `DISTINCT`, `ORDER BY`, then `LIMIT` or `OFFSET` apply.

Because `SELECT` runs after `WHERE`, you cannot use a column alias from `SELECT` inside `WHERE` in standard SQL.

## Common pitfalls

- Comparing to `NULL` with `=` or `<>`.
- Forgetting `WHERE` in `UPDATE` or `DELETE`.
- Storing money as `FLOAT`, which introduces rounding errors.
- Using `SELECT *` in application queries, which breaks when columns are added or reordered.
- Relying on the order of rows without `ORDER BY`. Relational tables have no inherent order.
- Treating `TRUNCATE` and `DELETE` as equivalent without checking triggers, logging, and rollback behaviour.

!!! tip "Interview tip"
    **Q: What is the difference between `DELETE`, `TRUNCATE`, and `DROP`?**
    `DELETE` removes selected rows, can be filtered, fires triggers, and is logged row by row. `TRUNCATE` removes all rows quickly and keeps the table. `DROP` removes the table definition too. Mention that rollback support for `TRUNCATE` depends on the database.

## Quick recap

- DDL defines structure; DML reads and changes data.
- Constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, NOT NULL) protect data in the database itself.
- Use `DECIMAL` for money; never `FLOAT`.
- `NULL` needs `IS NULL`; `= NULL` never matches.
- Logical query order: FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, LIMIT.

**See also:** [Intermediate SQL](intermediate-sql.md), [Normalisation and Modelling](normalisation-modelling.md)
