# Specific Databases

Each database makes different trade-offs, and interviewers often ask you to justify a choice. This page covers the features roadmap section 6 names: MySQL storage engines, replication, and sharding; PostgreSQL's JSONB, full-text search, and extensions; Redis data structures and pub/sub; and an overview of NoSQL stores.

## Core concepts

### MySQL

**InnoDB vs MyISAM.** InnoDB is the default storage engine in MySQL 5.5 and later. It supports transactions, row-level locking, and foreign keys, and it uses crash recovery. MyISAM does not support transactions and uses table-level locks for writes, so it suits only read-mostly, non-transactional workloads. For new tables, use InnoDB.

```sql
CREATE TABLE payment (
    payment_id INT PRIMARY KEY,
    amount_cents INT NOT NULL
) ENGINE = InnoDB;
```

**Replication.** A source (formerly "master") records changes in its binary log, and one or more replicas (formerly "slaves") apply them. Replication is asynchronous by default, so a replica can lag and a failover can lose recent commits. Semi-synchronous and group replication reduce that risk at the cost of latency. Read replicas scale reads but do not reduce write load, and reads from a replica may be stale.

**Sharding.** Sharding splits data across several database servers by a key, such as a customer ID. Each shard holds a subset of rows. Sharding adds complexity: cross-shard joins and transactions are hard, and resharding requires a plan. Shard only after vertical scaling, indexing, caching, and read replicas have been tried.

**Performance tuning.** Check the slow query log, use `EXPLAIN`, size the InnoDB buffer pool to fit the hot data, and keep the primary key short, because InnoDB stores secondary index entries that include the primary key.

### PostgreSQL

**JSONB.** `JSON` stores the text as written. `JSONB` stores a decomposed binary form that can be indexed and queried efficiently. Use `JSONB` when you need to filter on fields inside the document.

```sql
CREATE TABLE product (
    product_id INT PRIMARY KEY,
    attributes JSONB NOT NULL
);

CREATE INDEX idx_product_attributes ON product USING GIN (attributes);

SELECT product_id
FROM product
WHERE attributes @> '{"colour": "red"}';   -- containment, uses the GIN index
```

Do not turn every table into JSON. Fields you query and join on belong in columns.

**Full-text search.** PostgreSQL converts text into `tsvector` values and matches them with `tsquery`, using language rules such as stemming. A GIN index on the `tsvector` makes searches fast. This covers many search needs without an external search engine, though dedicated engines offer more ranking and language tooling.

```sql
SELECT product_id
FROM product
WHERE to_tsvector('english', attributes->>'description')
      @@ to_tsquery('english', 'waterproof & jacket');
```

**Window functions.** PostgreSQL supports the full window function set described in [Advanced SQL and Transactions](advanced-sql-transactions.md).

**Extensions.** PostgreSQL extends through extensions loaded with `CREATE EXTENSION`. Common examples include `pgcrypto` (cryptographic functions), `uuid-ossp` or built-in UUID generation, and PostGIS (geospatial data). Check that an extension is available on your managed service before you rely on it.

### Redis

Redis is an in-memory data store that keeps data in RAM and optionally persists it. Its value is in its data structures:

| Type | Typical use |
|---|---|
| Strings | Cache entries, counters (`INCR`), feature flags |
| Lists | Simple queues, recent-items feeds |
| Sets | Unique members, tags, membership tests |
| Hashes | Objects with several fields (a user profile) |
| Sorted sets | Leaderboards, time-ordered indexes, rate-limit windows |

```text
SET session:42 "active" EX 900      # string with a 15-minute expiry
INCR page:views                      # atomic counter
ZADD leaderboard 1520 "ana"          # sorted set: score 1520 for member "ana"
ZREVRANGE leaderboard 0 9            # top ten members
```

**Pub/sub.** Publishers send messages to channels and subscribers receive them. Pub/sub is fire-and-forget: a subscriber that is offline misses the message. Use streams or a message broker when you need durability.

**Transactions.** `MULTI` queues commands and `EXEC` runs them as one unit without interleaving from other clients. Redis does not roll back on a runtime error; a command that fails at run time is reported, and the others still run. Use `WATCH` for optimistic check-and-set.

Redis is usually a cache or a fast secondary store, not the system of record, unless you configure persistence and accept its trade-offs.

### NoSQL awareness

Know these at the level of "what kind of data model, and when would you consider it":

- **MongoDB:** document store. Stores JSON-like documents in collections. Suits variable-shaped records; supports secondary indexes and multi-document transactions.
- **Cassandra:** wide-column store designed for write-heavy workloads spread across many nodes. Data is modelled around the queries you need, and joins are not supported.
- **DynamoDB:** managed key-value and document service. Access is through partition keys and sort keys; design access patterns first.

The common trade-off: relational databases give joins, constraints, and transactions; NoSQL stores give horizontal scale and flexible schemas, but you design for specific access patterns in advance.

## How it works / Step by step

Choosing a database for a feature:

1. List the queries and their frequency, and the consistency the business needs.
2. Start with a relational database unless a clear requirement says otherwise.
3. Add Redis for caching, rate limits, or short-lived state.
4. Consider a document or wide-column store when the access pattern is known, the scale is high, and joins are not needed.
5. Write down the trade-off you accepted (consistency, operations, cost, lock-in).

## Common pitfalls

- Using MyISAM for tables that need transactions or foreign keys.
- Treating read replicas as up to date. Replication lag makes them stale.
- Sharding too early, before indexing and caching were tried.
- Using Redis as the only copy of data without persistence and a backup plan.
- Relying on pub/sub for messages that must not be lost.
- Putting every query field inside JSON and then scanning the whole table.
- Choosing NoSQL because it is fashionable, without defining the access patterns.

!!! tip "Interview tip"
    **Q: How would you scale reads on a relational database?**
    Add indexes and fix the slow queries first. Then add a cache such as Redis for hot, rarely changing data. Then add read replicas, and send only reads that tolerate some staleness to them. Sharding is the last step, and it changes how you write joins and transactions.

## Quick recap

- MySQL: use InnoDB; replication is asynchronous by default; sharding is a last resort.
- PostgreSQL: JSONB is indexable with GIN; full-text search uses `tsvector` and `tsquery`.
- Redis: rich data structures in memory; pub/sub does not persist messages.
- NoSQL stores trade joins and constraints for scale and flexible or query-specific models.
- Choose a database from the access patterns, not from its popularity.

**See also:** [Query Optimisation](query-optimisation.md), [Normalisation and Modelling](normalisation-modelling.md), [JDBC](../07-jdbc-jpa/jdbc.md)
