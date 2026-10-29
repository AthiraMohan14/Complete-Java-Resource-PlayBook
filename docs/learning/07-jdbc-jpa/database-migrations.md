# Database Migrations

A database migration is a versioned, repeatable change to a schema or reference data, applied in order. Migration tools such as Flyway and Liquibase store which changes have run, so every environment reaches the same schema. Interviewers ask about migrations to see whether you can change a live schema safely, not just create it once.

## Core concepts

### Why migrations exist

Hand-run SQL drifts: one developer's database has a column that production lacks, and a deployment fails. A migration tool keeps the schema in version control, applies pending changes in order, and records each applied change in a history table so re-running is safe.

### Flyway: versioned migrations

Flyway applies SQL (or Java) migrations named by version. The default naming is `V<version>__<description>.sql`, with two underscores.

```text
src/main/resources/db/migration/
    V1__create_customer.sql
    V2__create_orders.sql
    V3__add_phone_to_customer.sql
```

```sql
-- V1__create_customer.sql
CREATE TABLE customer (
    customer_id INT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE
);
```

```sql
-- V3__add_phone_to_customer.sql
ALTER TABLE customer ADD COLUMN phone VARCHAR(20);
```

Flyway records each migration in a `flyway_schema_history` table with a checksum. Key behaviours:

- **Versioned migrations** run once, in version order.
- **Repeatable migrations** (`R__name.sql`) run again when their content changes; useful for views and stored procedures.
- **Validation:** if an applied migration's file has changed, Flyway fails with a checksum mismatch. Do not edit applied migrations.
- **Callbacks:** SQL or Java hooks that run before or after migrations, for example to refresh statistics.
- **Undo migrations:** rolling back by writing a reverse migration is the safer approach. Check the current Flyway edition for undo support before relying on it.

With Spring Boot, Flyway runs at startup when it is on the classpath and `spring.flyway.enabled` is not false.

### Liquibase: changelogs

Liquibase describes changes in changelogs written as XML, YAML, JSON, or SQL. Each change is a **changeSet** with an author and ID; Liquibase records applied changesets in the `DATABASECHANGELOG` table.

```yaml
# db/changelog/changelog-master.yaml
databaseChangeLog:
  - changeSet:
      id: 1-create-customer
      author: platform-team
      changes:
        - createTable:
            tableName: customer
            columns:
              - column:
                  name: customer_id
                  type: INT
                  constraints:
                    primaryKey: true
              - column:
                  name: email
                  type: VARCHAR(255)
                  constraints:
                    nullable: false
                    unique: true
```

Liquibase can express changes portably (`createTable`, `addColumn`) or run raw SQL in a `sql` change. Each changeSet can declare a `rollback` block, which makes rollbacks explicit and testable.

### Flyway or Liquibase

| Concern | Flyway | Liquibase |
|---|---|---|
| Authoring | Plain SQL files (simplest) | XML, YAML, JSON, or SQL changelogs |
| Portability | You write database-specific SQL | Abstract change types for many databases |
| Rollback | Forward-only is the norm | Rollback blocks per changeSet |
| Mental model | Ordered files | Changesets with IDs and authors |

Both work well with Spring Boot. Pick one per project and do not run both against the same schema.

### Schema versioning and rollback strategies

Rollbacks are hard once data has been written. Practical strategies:

- **Expand and contract:** add the new column or table first (expand), deploy code that writes both, backfill, switch reads, then remove the old column in a later release (contract). Each step is backward compatible, so you can roll back the application.
- **Forward fix:** when a migration is wrong, write a new migration that corrects it. Reverting applied migrations rewrites history that other environments have already run.
- **Backups before risky changes:** a tested backup and restore procedure is the real rollback for destructive changes.

Never rename or drop a column that the currently running application still reads.

### Testing migrations

- Run all migrations against an empty database in CI, so the full history is proven to apply.
- Run them against a copy or fixture with realistic data for large or data-changing migrations.
- Use Testcontainers to start a real database of the same engine and version as production, rather than an in-memory substitute that behaves differently.
- Check the migration's runtime on realistic volume: a `ALTER TABLE` that rewrites a large table can lock it for a long time.

## How it works / Step by step

When the application starts with Flyway enabled:

1. Flyway connects and creates its history table if it is missing.
2. It reads the migration files and compares them with the history table.
3. It validates checksums of applied migrations.
4. It runs each pending migration in version order, recording success.
5. If a migration fails, the application does not start; the failure is recorded for diagnosis.

## Common pitfalls

- Editing a migration after it has been applied in any environment.
- Running schema changes by hand in production and not recording them.
- Adding a `NOT NULL` column without a default to a populated table.
- Dropping or renaming a column in the same release that stops using it.
- Relying on an in-memory database for tests when production uses a different engine.
- Running Flyway and Liquibase against the same schema.

!!! tip "Interview tip"
    **Q: How do you change a column in a live system without downtime?**
    Use expand and contract. Add the new column, write to both, backfill existing rows, move reads to the new column, and remove the old one in a later release. Every step must be compatible with the application version that is still running, so you can roll back the code at any point.

## Quick recap

- Migrations are versioned, ordered, and recorded in a history table.
- Flyway uses `V<version>__name.sql` files; Liquibase uses changesets in XML, YAML, JSON, or SQL.
- Never edit an applied migration; write a forward fix.
- Use expand and contract for schema changes on live systems.
- Test migrations on an empty database and on a production-like engine with realistic data.

**See also:** [JDBC](jdbc.md), [Normalisation and Modelling](../06-databases-sql/normalisation-modelling.md), [Index](index.md)
