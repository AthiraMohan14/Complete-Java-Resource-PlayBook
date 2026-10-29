# Replication, Sharding, and NoSQL

Replication keeps copies of data on several nodes, which helps with read load and availability. Sharding splits data across nodes, which helps with write load and data size. Choosing between SQL and NoSQL stores is the decision that frames both. Interviewers ask about these topics because every scaling answer eventually reaches the database, and the candidate must say what each choice costs in consistency, operations, and query flexibility.

## Core concepts

### SQL versus NoSQL

| Aspect | Relational (SQL) | NoSQL |
|---|---|---|
| Schema | Fixed tables and column types | Flexible, often per record |
| Scaling | Usually vertical first; horizontal needs extra work | Designed to spread across nodes |
| Consistency | Strong transactions by default | Often tunable, frequently eventual |
| Joins | Native and efficient | Limited or absent; denormalise instead |
| Strength | Relationships, integrity, ad hoc queries | Very large scale, high write rates, flexible shapes |

ACID transactions and the BASE model are covered in depth in [Databases and SQL](../06-databases-sql/index.md). The short version: ACID favours correctness inside one database, while BASE accepts looser guarantees in exchange for availability and scale.

Choosing a store is about access patterns, not fashion. Write the most important queries first. If they need joins and transactions across related rows, start relational. If they are key lookups or large append-heavy streams with a known partition key, a NoSQL store may fit better.

### NoSQL families

- **Key-value** (for example Redis, DynamoDB): get and put by key. Good for sessions, carts, and caches. Queries beyond the key are weak.
- **Document** (for example MongoDB, Couchbase): JSON-like documents, with indexes on fields inside them. Good when an aggregate is read as a whole, such as a product with its attributes.
- **Column-family** (for example Cassandra, HBase): wide rows partitioned by key and clustered by a sort column. Good for time-series and write-heavy logs with predictable query patterns.
- **Graph** (for example Neo4j): nodes and relationships, with traversal queries. Good for recommendations and social connections when traversal is the main query.

Each family makes some queries cheap and others expensive. Designing the data model around the query is the core skill, not the product name.

### Replication

Replication copies data from one node to others. It serves two purposes: spreading read traffic and surviving the loss of a node.

**Leader-follower (primary-replica)**: all writes go to one leader, which streams changes to followers. Reads can go to followers.

- **Asynchronous** replication acknowledges writes before followers have them. It is fast, but a failover can lose the most recent writes, and reads from followers can lag behind.
- **Synchronous** replication waits for at least one follower. It protects data but adds latency to every write.

**Failover** promotes a follower when the leader fails. Automatic failover is faster but must avoid split-brain, where two nodes both believe they are the leader. Manual failover is slower but gives a human the final decision.

**Multi-leader** replication accepts writes in several regions or nodes. It improves write locality and availability, but concurrent writes to the same record must be reconciled, by last-write-wins, version vectors, or business rules.

**Leaderless** replication, as in Dynamo-style stores, sends each write to several replicas and reads from several. Quorums decide success.

### Quorums

With `N` replicas, a write is acknowledged after `W` replicas confirm it, and a read contacts `R` replicas. When `R + W > N`, every read set overlaps every write set in at least one replica, so a read sees the latest acknowledged write, as long as the cluster has no unusual failures.

```text
N = 3, W = 2, R = 2  ->  R + W = 4 > 3, reads overlap writes
N = 3, W = 1, R = 1  ->  R + W = 2 <= 3, reads can be stale
```

Quorums are a tuning knob. Raising `W` improves durability and reduces availability during failures. Raising `R` improves freshness and costs more reads.

### Reads after writes

A user who updates a profile and immediately reloads the page may hit a lagging follower and see the old value. Common fixes are:

- Route the user's own reads to the leader for a short window after a write.
- Track the log position of the write and read only from replicas that have reached it.
- Return the written value in the response, so the client does not need to re-read.

### Sharding (horizontal partitioning)

Sharding splits rows across nodes by a **shard key**. Each shard holds a subset and can be stored, scaled, and backed up independently.

- **Range sharding**: keys in ranges, such as customer IDs 1 to 1 million on shard A. Range scans are easy, but new data often lands on the newest range, creating a hot spot.
- **Hash sharding**: the key is hashed and mapped to a shard. Load spreads evenly, but range queries must scan every shard.
- **Directory sharding**: a lookup table maps each key, or group of keys, to a shard. It is flexible, and the directory becomes a dependency to keep available.

```java
import java.util.List;

class ShardRouter {

    private final List<String> shards;

    ShardRouter(List<String> shards) {
        this.shards = List.copyOf(shards);
    }

    String shardFor(long customerId) {
        // floorMod keeps the result non-negative even for negative keys
        return shards.get((int) Math.floorMod(customerId, (long) shards.size()));
    }

    public static void main(String[] args) {
        ShardRouter router = new ShardRouter(List.of("shard-0", "shard-1", "shard-2"));
        System.out.println(router.shardFor(42L));   // 42 mod 3 = 0, so shard-0
    }
}
```

Modulo routing is simple, but adding a shard changes `size()` and remaps almost every key. That is why production systems use consistent hashing or a directory when the shard count will change. The ring idea is covered in [High-Level Design](high-level-design.md).

### Choosing a shard key

The shard key decides almost everything about a sharded system, and it is hard to change later. A good key has three properties:

- **High cardinality**: many distinct values, so data and traffic can spread across shards.
- **Even access**: no single value receives a large share of reads or writes.
- **Locality for the main query**: the queries that run most often touch one shard. A customer ID often works for an e-commerce system, because a customer's orders, addresses, and carts can live together.

A timestamp is a poor key for write-heavy data, because every new record lands on the newest shard. A country code is a poor key because a few countries dominate. When no single key fits, consider a composite key, such as customer ID followed by order date, or keep a small directory that routes the rare cross-cutting queries.

### Vertical partitioning

Vertical partitioning splits a table by columns or by access pattern: frequently read columns in one table, large rarely read blobs in another, or sensitive fields in a separate store. It reduces row width and I/O, without changing the number of shards.

### The costs of sharding

- **Cross-shard queries** need scatter-gather, which calls every shard and merges results, or a separate read model built from events.
- **Cross-shard transactions** are expensive. Keep related data on one shard, or use a saga (see [Distributed Transactions](../14-microservices/distributed-transactions.md)).
- **Hot shards** appear when one key or one range receives most of the traffic. A shard key with few distinct values, such as a country code, is a common cause.
- **Rebalancing** moves data when the shard count or the key distribution changes. Plan it while the system is small enough that moves are cheap.

### CAP applied to storage

During a network partition, a store must either refuse some requests to stay consistent (CP) or keep answering and reconcile later (AP). Replication choices decide which side a system takes. Leader-based stores with synchronous replication tend toward CP. Leaderless stores with tunable quorums can be tuned either way. The theory and PACELC are in [Core Concepts](core-concepts.md).

### Caching in front of the database

Most read traffic does not need to reach the database. A cache of hot data, such as Redis, absorbs repeated reads and buys time for the database. The caching strategies and invalidation rules are described in [High-Level Design](high-level-design.md) and in [Caching and Performance](../12-caching-performance/index.md).

## How it works / Step by step

1. Write down the main queries and their frequency, including the read-to-write ratio.
2. Choose a store family that makes those queries cheap, and accept the trade-offs.
3. Add replication for read scale and failover. Choose asynchronous or synchronous per workload.
4. Pick a shard key that matches the main access pattern and spreads load evenly.
5. Use consistent hashing or a directory if the number of shards will change.
6. Route reads that must be fresh to the leader or to replicas that have caught up.
7. Monitor replication lag, shard size, and per-shard request rates.

## Common pitfalls

- Sharding before a single well-tuned database has been tried. Indexes, query fixes, and replicas often come first.
- Choosing a shard key by convenience (such as a timestamp) that sends all new writes to one shard.
- Assuming a replica is always current, then showing users stale data right after they write.
- Using modulo sharding and then adding shards without a migration plan.
- Writing queries that join across shards in the request path.
- Treating NoSQL as schema-free. The access patterns still decide the design, and the schema moves into the application code.

!!! tip "Interview tip"
    **Q: How would you scale a database that is slow on writes?**
    Check first whether a single node can be tuned or scaled up. If not, shard by a key that matches the main writes, such as customer ID, and explain how you will route queries and rebalance. Name the cost: cross-shard reads now need scatter-gather or a read model, and cross-shard transactions need a saga or must be avoided.

## Quick recap

- SQL and NoSQL differ in schema, scaling model, and consistency; the access pattern decides.
- Replication scales reads and adds failover, with lag or write latency as the trade-off.
- With `N`, `W`, and `R`, `R + W > N` means reads overlap the latest writes.
- Sharding scales writes by key; modulo routing breaks when shards change, so use consistent hashing or a directory.
- Cross-shard queries and transactions are the main costs of sharding.

**See also:** [Core Concepts](core-concepts.md) | [High-Level Design](high-level-design.md) | [Databases and SQL](../06-databases-sql/index.md) | [Scalability and Failover](scalability-and-failover.md)
