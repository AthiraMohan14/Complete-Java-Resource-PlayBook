# Databases and SQL

The relational model, SQL from basics to window functions, transactions, query tuning, schema design, and the specific databases you are likely to meet. This section covers roadmap section 6.

---

## Topics

### [SQL Fundamentals](sql-fundamentals.md)
**DDL - DML - constraints - data types - NULL**
Creating tables, writing reads and changes, enforcing rules with constraints, and handling NULL correctly.

### [Intermediate SQL](intermediate-sql.md)
**joins - aggregates - GROUP BY - subqueries - set operations**
Joins of every kind, grouping and filtering groups, correlated subqueries, and `NOT EXISTS`.

### [Advanced SQL and Transactions](advanced-sql-transactions.md)
**window functions - CTEs - ACID - isolation levels - locking**
Ranking and analytical functions, recursive queries, transactions, anomalies, and deadlock prevention.

### [Query Optimisation](query-optimisation.md)
**indexes - EXPLAIN - sargable predicates - N+1 - partitioning**
Reading execution plans, choosing indexes, and tuning queries and data layout.

### [Normalisation and Modelling](normalisation-modelling.md)
**1NF to BCNF - ER modelling - junction tables - denormalisation**
Normal forms with examples, relationship design, and when to break the rules.

### [Specific Databases](specific-databases.md)
**InnoDB - replication - JSONB - full-text search - Redis - NoSQL**
MySQL, PostgreSQL, and Redis features, plus when to consider MongoDB, Cassandra, or DynamoDB.
