# Normalisation and Data Modelling

Normalisation organises tables so each fact is stored once and updates cannot leave data inconsistent. Data modelling (often as entity-relationship diagrams) is the step before writing `CREATE TABLE`. Interviewers ask about normal forms to check that you can spot redundancy and justify when to break the rules.

## Core concepts

### Functional dependencies and keys

A functional dependency `X -> Y` means that for any two rows with the same `X`, `Y` must also match. Normal forms are defined by which dependencies a table allows.

A **candidate key** is a minimal set of columns that uniquely identifies a row. The **primary key** is the candidate key you choose. A **superkey** is any set that includes a candidate key.

### First normal form (1NF)

A table is in 1NF when every column holds atomic (indivisible) values and each row is unique.

Not in 1NF:

| order_id | items |
|---|---|
| 1 | `pen, notebook, ink` |

Fix: one row per item.

| order_id | item |
|---|---|
| 1 | pen |
| 1 | notebook |
| 1 | ink |

### Second normal form (2NF)

A table is in 2NF when it is in 1NF and every non-key column depends on the whole candidate key, not on part of it. This matters only for composite keys.

Problem: a table keyed by `(order_id, product_id)` that also stores `product_name`. `product_name` depends only on `product_id`. Move it to a `product` table.

### Third normal form (3NF)

A table is in 3NF when it is in 2NF and no non-key column depends on another non-key column (no transitive dependency).

Problem: `orders(order_id, customer_id, customer_city)`. `customer_city` depends on `customer_id`, not on `order_id`. Move the city to `customer`.

### Boyce-Codd normal form (BCNF)

A table is in BCNF when, for every functional dependency `X -> Y` that is not trivial, `X` is a superkey. BCNF is slightly stricter than 3NF. It matters when a table has overlapping candidate keys, for example a table where `(student, course)` and `(student, tutor)` are both keys but a tutor teaches only one course.

### Denormalisation trade-offs

Normal forms protect writes. Denormalisation trades that protection for faster reads. Typical reasons:

- A reporting or read-heavy path needs a join that is too slow.
- A derived value (such as an order total) is read often and recalculated rarely.

The cost: updates must change every copy, and a missed copy becomes a silent bug. Add a constraint, trigger, or job to keep copies in sync, and document the decision.

### Entity-relationship modelling

An entity-relationship (ER) model names the things the system stores (entities), their attributes, and how they relate.

| Relationship | Implementation |
|---|---|
| One-to-one | Foreign key with a `UNIQUE` constraint, or the same primary key in both tables |
| One-to-many | Foreign key on the "many" side |
| Many-to-many | Junction (associative) table with two foreign keys and a composite primary key |

```sql
CREATE TABLE student (
    student_id INT PRIMARY KEY,
    full_name  VARCHAR(120) NOT NULL
);

CREATE TABLE course (
    course_id  INT PRIMARY KEY,
    title      VARCHAR(160) NOT NULL
);

-- Many-to-many: a student can enrol in many courses and a course has many students
CREATE TABLE enrolment (
    student_id  INT NOT NULL REFERENCES student (student_id),
    course_id   INT NOT NULL REFERENCES course (course_id),
    enrolled_on DATE NOT NULL,
    PRIMARY KEY (student_id, course_id)
);
```

The junction table can carry attributes of the relationship itself (`enrolled_on`, `grade`). If it does, it is a real entity; give it a name that reflects that.

### Design principles

- Give every table a primary key.
- Name things consistently (singular or plural, snake_case) and stick to the convention.
- Use foreign keys to protect relationships, not only application code.
- Store one fact in one place unless you have a measured reason not to.
- Model time explicitly: `created_on`, `updated_on`, and effective date ranges for history.
- Decide on soft delete versus hard delete early; it affects every query.

## How it works / Step by step

Designing a schema for a feature:

1. List the nouns (entities) and the questions the system must answer.
2. Draw the relationships and their cardinality (one-to-one, one-to-many, many-to-many).
3. Choose primary keys and natural or surrogate keys.
4. Normalise to 3NF (or BCNF) by checking each non-key column against each key.
5. Denormalise only where a measured read path needs it, and record the sync rule.
6. Write the constraints (foreign keys, unique, check) before writing application code.

## Common pitfalls

- Storing comma-separated lists in one column; they break 1NF and make queries hard.
- Duplicating a customer's name on every order, so a name change updates some rows but not others.
- Using a many-to-many relationship without a junction table.
- Choosing a mutable value (such as an email address) as the primary key without a plan for changes.
- Normalising so far that every query needs ten joins, without measuring.
- Making every column nullable, which hides missing-data rules.

!!! tip "Interview tip"
    **Q: When would you denormalise a schema?**
    When a measured read path is too slow because of joins, and the duplicated data changes rarely or can be kept in sync reliably. State the cost (write complexity, risk of drift) and the mechanism that keeps copies consistent, such as a constraint, a trigger, or an event-driven update.

## Quick recap

- 1NF: atomic values. 2NF: no partial dependency on a composite key. 3NF: no transitive dependency.
- BCNF: every non-trivial dependency's left side is a superkey.
- Many-to-many needs a junction table; one-to-many puts the foreign key on the many side.
- Denormalise for measured read needs, and document how copies stay in sync.
- Put rules in constraints, not only in application code.

**See also:** [SQL Fundamentals](sql-fundamentals.md), [Query Optimisation](query-optimisation.md), [Specific Databases](specific-databases.md)
