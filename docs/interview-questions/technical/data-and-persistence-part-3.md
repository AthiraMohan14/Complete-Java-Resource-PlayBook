# Data and Persistence Questions (Part 3 of 4)

Continued from [Part 2](data-and-persistence-part-2.md). These questions cover joins and set operators, caching, consistency models, indexes, normalisation, concurrent writes, query tuning, and scaling out a database.

---

## 21. How do INNER JOIN, LEFT JOIN, and UNION differ?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An `INNER JOIN` keeps only the rows that match in both tables. A `LEFT JOIN` keeps every row from the left table and fills the right-hand columns with `NULL` when nothing matches. `UNION` stacks the results of two queries that have the same number and types of columns, then removes duplicate rows. `UNION ALL` does the same stacking but keeps duplicates, so it is cheaper.

### Explanation
Assume a `customers` table and an `orders` table linked by `orders.customer_id`.

```sql
-- Only customers who have at least one order
SELECT cu.name, ord.id AS order_id
FROM customers cu
INNER JOIN orders ord ON ord.customer_id = cu.id;

-- Every customer; order_id is NULL for a customer with no orders
SELECT cu.name, ord.id AS order_id
FROM customers cu
LEFT JOIN orders ord ON ord.customer_id = cu.id;
```

A common pattern uses `LEFT JOIN` to find rows with no match:

```sql
SELECT cu.name
FROM customers cu
LEFT JOIN orders ord ON ord.customer_id = cu.id
WHERE ord.id IS NULL;        -- customers with no orders
```

`UNION` works on whole result sets rather than on joined rows:

```sql
SELECT city FROM stores
UNION
SELECT city FROM warehouses;  -- each distinct city once
```

### When to use / pitfalls
- A filter on the right-hand table placed in `WHERE` removes the `NULL` rows that `LEFT JOIN` created, so the query behaves like an `INNER JOIN`. Put that condition in the `ON` clause if you want to keep the unmatched rows.
- A join on a column that is not unique multiplies rows. Check the row count against the expected result.
- `UNION` must sort or hash the combined rows to remove duplicates, so `UNION ALL` is faster when duplicates are acceptable or impossible.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md)

</details>

---

## 22. How do WHERE and HAVING differ?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`WHERE` filters individual rows before grouping, and it cannot contain aggregate functions such as `COUNT` or `SUM`. `HAVING` filters groups after aggregation, so its conditions can use aggregates.

### Explanation
```sql
SELECT customer_id, COUNT(*) AS total_orders
FROM orders
WHERE order_date >= DATE '2025-01-01'   -- row filter, applied first
GROUP BY customer_id
HAVING COUNT(*) > 5;                    -- group filter, applied after grouping
```

Writing `WHERE COUNT(*) > 5` is an error, because aggregates are not allowed in `WHERE`. Put every condition that does not need an aggregate in `WHERE`, so the database groups fewer rows.

### When to use / pitfalls
- Filtering early in `WHERE` reduces the work done by the grouping step. Use `HAVING` only for conditions on aggregates.
- An alias defined in the `SELECT` list cannot be used in `WHERE` in standard SQL. Some databases also allow aliases in `HAVING`, so check the database you are using.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md)

</details>

---

## 23. What are the common database caching patterns?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The four patterns in common use are cache-aside, read-through, write-through, and write-behind. Cache-aside is the most common in interviews and in practice: the application checks the cache, reads the database on a miss, and fills the cache. Write-through writes the cache and the database together. Write-behind acknowledges the write once the cache has it and writes the database later, which is faster but can lose data if the cache fails first.

### Explanation
| Pattern | Read path | Write path | Main risk |
|---------|-----------|------------|-----------|
| Cache-aside | Application checks cache, loads from database on a miss | Application writes the database, then invalidates the cache entry | Stale data between write and invalidation |
| Read-through | Cache library loads from the database on a miss | Usually handled by the application | Tight coupling to the cache library |
| Write-through | Read from cache | Write to cache and database before returning | Slower writes |
| Write-behind | Read from cache | Write to cache, flush to database later | Data loss if the cache fails before the flush |

A cache-aside sketch:

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

interface ProductStore {
    String findNameById(long id);       // reads the database
    void saveName(long id, String name); // writes the database
}

class CacheAsideProducts {
    private final Map<Long, String> cache = new ConcurrentHashMap<>();
    private final ProductStore store;

    CacheAsideProducts(ProductStore store) {
        this.store = store;
    }

    String getName(long id) {
        String name = cache.get(id);
        if (name == null) {                    // miss: load and fill the cache
            name = store.findNameById(id);
            if (name != null) {
                cache.put(id, name);
            }
        }
        return name;
    }

    void rename(long id, String newName) {
        store.saveName(id, newName);           // write the source of truth first
        cache.remove(id);                      // invalidate; the next read reloads it
    }
}
```

### When to use / pitfalls
- Write-through keeps the two stores in step after a successful write, but it does not give you transactions across them. If the cache write succeeds and the database write fails, you still need a recovery step.
- With cache-aside, a reader can load an old value just before a writer updates the database and invalidates the entry. Set a short time-to-live as a backstop.
- Write-behind suits counters and metrics where losing a few seconds of writes is acceptable. It does not suit money.

**See also:** [Data and persistence part 2](data-and-persistence-part-2.md), [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 24. What does the CAP theorem say, and what does it mean in practice?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
CAP says that a distributed data store cannot guarantee both consistency (every read sees the latest write) and availability (every request gets a non-error response) while a network partition is happening. Partition tolerance is not optional in a real distributed system, because partitions do happen. So the practical choice during a partition is between consistency and availability. "Pick any two of three" is a common shortcut, but it misleads, because a system cannot give up partition tolerance.

### Explanation
Take two replicas in different data centres, and suppose the link between them breaks.

- A **CP** system refuses writes on the side that cannot reach the majority. Readers see consistent data, but some clients get errors.
- An **AP** system accepts writes on both sides and reconciles them when the link returns. Every request gets an answer, but the two sides can disagree for a while.

A system with no partitions, such as a single-node relational database, can be both consistent and available. That is the usual meaning of "CA", and it is not a choice for a distributed system.

Classify a system by its configuration, not its name. DynamoDB, for example, offers strongly consistent reads per request, and ZooKeeper and HBase favour consistency.

### When to use / pitfalls
- CAP says nothing about normal operation. PACELC extends it: without a partition, a system still trades latency against consistency.
- Explain the trade-off in business terms. A payment ledger usually favours consistency; a like counter usually favours availability.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md), [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 25. What is the difference between ACID and BASE?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
ACID is the set of guarantees that a transactional database gives for each transaction: atomicity, consistency, isolation, and durability. BASE is the looser model common in distributed stores: basically available, soft state, and eventual consistency. ACID favours correctness, and BASE favours availability and scale.

### Explanation
**ACID, in one line each**
- Atomicity: all of a transaction's changes happen, or none do.
- Consistency: the transaction moves the data from one valid state to another, respecting constraints.
- Isolation: concurrent transactions behave as if they ran one at a time, at the chosen isolation level.
- Durability: once a commit returns, the change survives a crash.

A bank transfer is the classic example. Both the debit and the credit must succeed or both must fail.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

class Transfers {
    void transfer(Connection con, long from, long to, long amount) throws SQLException {
        con.setAutoCommit(false);
        try (PreparedStatement debit = con.prepareStatement(
                 "UPDATE accounts SET balance = balance - ? WHERE id = ?");
             PreparedStatement credit = con.prepareStatement(
                 "UPDATE accounts SET balance = balance + ? WHERE id = ?")) {
            debit.setLong(1, amount);
            debit.setLong(2, from);
            debit.executeUpdate();
            credit.setLong(1, amount);
            credit.setLong(2, to);
            credit.executeUpdate();
            con.commit();
        } catch (SQLException e) {
            con.rollback();
            throw e;
        }
    }
}
```

**BASE, in one line each**
- Basically available: the system responds, even if some parts are failing.
- Soft state: a replica's state can change over time without a new write from the client.
- Eventual consistency: if writes stop, all replicas converge to the same value.

A like counter that shows 1,204 on one device and 1,206 on another for a few seconds is a BASE example.

### When to use / pitfalls
- BASE does not mean "no consistency". It means consistency comes later and has no fixed deadline.
- Choose ACID for money, inventory, and anything that must not oversell. Choose BASE for feeds, analytics, and counters that tolerate lag.

**See also:** [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 26. What are idempotency and statelessness, and why do they matter?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An operation is idempotent when running it several times leaves the system in the same state as running it once. This makes retries safe after a timeout. A stateless server keeps no per-client session in its own memory, so each request carries what the server needs, usually a signed token. Any instance can then serve any request.

### Explanation
Idempotency depends on the HTTP method and on what the handler does:

| Request | Idempotent | Reason |
|---------|------------|--------|
| `GET /users/123` | Yes | Reading does not change state |
| `PUT /users/123` with a full body | Yes | Setting the same value again changes nothing |
| `DELETE /users/123` | Yes | The second call leaves the same state, though it may return 404 |
| `POST /transfers` | No | Each call can create another transfer |

A `POST` can be made safe to retry with a client-generated key:

```
POST /transfers
Idempotency-Key: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

The server stores the key with the result of the first call. A repeated key returns the stored result and does not transfer the money again. The key must be unique per logical operation, and the stored record needs an expiry.

Statelessness gives three benefits: any server can take any request, load balancers need no sticky sessions, and a crashed server loses no session data. A bearer token such as a JWT carries the identity, and the server checks its signature on each call.

### When to use / pitfalls
- Stateless does not mean the system has no state. The database still holds it. The point is that the application servers hold none.
- Tokens that are valid until they expire are hard to revoke early. Keep lifetimes short, and use a denylist or a token version check for urgent cases.
- Idempotency keys need storage and a rule for concurrent duplicates, not just a check.

**See also:** [Security and authentication](../technical/spring-and-security-part-1.md), [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 27. How do indexes speed up queries, and what do they cost?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Most relational indexes are B-trees. A B-tree keeps keys sorted in a balanced tree, so the database can find matching rows in O(log n) steps instead of scanning every row in O(n). The cost is extra storage, slower writes because every index must be updated, and the maintenance work that comes with that.

### Explanation
```sql
CREATE INDEX idx_members_last_first ON members (last_name, first_name);

-- Can use the index: the leading column is filtered
SELECT id FROM members WHERE last_name = 'Okafor' AND first_name = 'Ada';
SELECT id FROM members WHERE last_name = 'Okafor';

-- Usually cannot use it efficiently: the leading column is missing
SELECT id FROM members WHERE first_name = 'Ada';
```

This is the leftmost-prefix rule: a composite index is useful for filters on its leading columns, in order. Some databases can skip through an index in special cases, so confirm with the query plan.

Two more cases that defeat an index:

```sql
-- A function on the column prevents a plain index on email being used
SELECT id FROM users WHERE LOWER(email) = 'ann@example.com';

-- A leading wildcard prevents a range seek on the index
SELECT id FROM users WHERE last_name LIKE '%mith';
```

### When to use / pitfalls
- Index columns that appear in `WHERE`, `JOIN`, and `ORDER BY`, and that have many distinct values.
- Avoid indexing low-selectivity columns, such as a boolean flag, on their own.
- Every extra index slows each insert, update, and delete on that table. Remove indexes that no query uses.
- Check the plan with `EXPLAIN` before and after adding an index. Do not assume it helps.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md), [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 28. When would you choose a NoSQL database over a relational one?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Choose NoSQL when you need to scale writes or storage across many machines, when the shape of the data changes often, or when the data is naturally a document, a graph, or a key-value pair. Choose a relational database when you need joins, multi-row transactions, enforced constraints, and reporting queries over a stable schema. The access pattern matters more than the label.

### Explanation
The main NoSQL families and where they fit:

- **Document** (for example MongoDB): JSON-like records with flexible fields, such as user profiles.
- **Key-value** (for example Redis, DynamoDB): fast lookups by key, such as sessions and caches.
- **Wide-column** (for example Cassandra): very high write throughput across many nodes, such as event or activity feeds.
- **Graph** (for example Neo4j): relationships are first-class, such as recommendations and fraud rings.
- **Time-series** (for example InfluxDB, TimescaleDB): timestamped metrics and sensor data.


### When to use / pitfalls
- NoSQL is not faster by default. A well-indexed relational table often outperforms a poorly modelled document store.
- Many NoSQL stores limit transactions to one item or one partition. Check that the write you need fits inside that limit.
- Moving the schema out of the database does not remove it. The application must now check the shape of each document.

**See also:** [Data and persistence part 2](data-and-persistence-part-2.md), [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 29. Why normalise a database, and what are the normal forms?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Normalisation splits data so that each fact is stored in one place. This prevents update, insert, and delete anomalies, where a change has to be made in many rows and one of them is missed. First normal form requires atomic values and no repeating groups. Second normal form removes partial dependencies on part of a composite key. Third normal form removes transitive dependencies, where a non-key column depends on another non-key column.

### Explanation
Consider an `order_items` table that stores the customer's name and address on every row. A customer with 50 orders has the address 50 times. Changing the address means updating 50 rows, and missing one leaves the data contradictory.

Moving the customer's details into a `customers` table fixes this:

```sql
CREATE TABLE customers (
    id      BIGINT PRIMARY KEY,
    name    VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL
);

CREATE TABLE orders (
    id          BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers (id),
    placed_on   DATE NOT NULL
);
```

Now the address is stored once, and `orders` refers to it by key.

### When to use / pitfalls
- Over-normalising spreads data across many tables. Each read then needs many joins, which can cost more than the anomalies it prevents.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md)

</details>

---

## 30. When would you denormalise a database?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Denormalise on purpose when reads are slow because of expensive joins or aggregations, and you have measured it. The method is to copy a value into another table, store a precomputed total, or keep a summary table. The cost is that every copy must be kept in step, usually by the application or by triggers.

### Explanation
Common techniques:

- **Duplicate a column.** Store the customer name on `orders` so an order list needs no join to `customers`.
- **Precompute an aggregate.** Keep a `order_count` column on `customers`, updated when orders change.
- **Summary table.** A nightly job or stream writes daily sales totals to a table that reports read directly.

```sql
ALTER TABLE orders ADD COLUMN customer_name VARCHAR(100);

UPDATE orders o
SET customer_name = (SELECT c.name FROM customers c WHERE c.id = o.customer_id);
```

In production, the code that changes the name must update the copy too.

### When to use / pitfalls
- Measure first. Show the query plan and the timing before and after. A denormalised column that saves 2 ms rarely justifies the risk.
- A copy can drift from its source. Decide which side is authoritative and write a reconciliation query.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md), [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 31. What is the difference between clustered and non-clustered indexes?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A clustered index decides the physical order of the table's rows, so a table can have at most one. A non-clustered index is a separate structure that holds the indexed values and a pointer back to the row. A table can have many non-clustered indexes. Lookups through a non-clustered index usually need a second step to reach the full row, unless the index covers the query.

### Explanation
The meaning of "clustered" depends on the database:

- **SQL Server** and **MySQL InnoDB** store the table in the order of its clustered index, which is usually the primary key. Without one, SQL Server stores the table as a heap.
- **InnoDB** secondary indexes store the primary key value as the row pointer. A lookup through a secondary index therefore reads the secondary index first, then the clustered index.
- **PostgreSQL** does not maintain a clustered index. `CLUSTER` reorders the table once, and the order is not kept as rows change.

A covering index holds every column the query needs, so the database never reads the table:

```sql
CREATE INDEX idx_orders_customer_total ON orders (customer_id, total);

-- Served from the index alone, if the database can do an index-only scan
SELECT total FROM orders WHERE customer_id = 42;
```

### When to use / pitfalls
- Keep the clustered key narrow and increasing where you can. In InnoDB, random primary keys such as unordered UUIDs often cause page splits and fragmentation.
- Every non-clustered index adds write cost and storage. Do not add one per column.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md), [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 32. How would you stop lost updates when many writers change one row?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Pick a strategy by how often writers collide. Use a single atomic `UPDATE` when the change is simple. Use pessimistic locking (`SELECT ... FOR UPDATE`) when a longer read-then-write must not interleave with another writer. Use optimistic locking with a version column when collisions are rare, and retry or reject the stale update when one happens. Whichever you choose, keep transactions short and lock rows in a consistent order.

### Explanation
An atomic update avoids a read-modify-write race because the database does the arithmetic under its own lock:

```sql
UPDATE inventory
SET quantity = quantity - 1
WHERE id = 42 AND quantity > 0;
-- Check the affected row count: 0 means the item sold out
```

Optimistic locking with JPA uses a `@Version` field. Hibernate adds the version to the `UPDATE` and fails the update if the row changed:

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Version;

@Entity
class Inventory {
    @Id
    Long id;

    int quantity;

    @Version
    long version;     // incremented on every successful update
}
```

Pessimistic locking takes a lock when the row is read:

```java
import jakarta.persistence.EntityManager;
import jakarta.persistence.LockModeType;

class InventoryService {
    void reserveOne(EntityManager em, Long id) {
        Inventory item = em.find(Inventory.class, id, LockModeType.PESSIMISTIC_WRITE);
        if (item.quantity > 0) {
            item.quantity--;            // flushed at commit; other writers wait for the lock
        }
    }
}
```

### When to use / pitfalls
- With optimistic locking, catch the exception (`OptimisticLockException` in JPA) and retry the whole business operation, not just the save.
- Two transactions that lock the same rows in different orders can deadlock. Always lock rows in one agreed order, such as ascending ID.
- Long transactions that hold locks hurt throughput. Do external calls outside the transaction.
- The isolation level changes which anomalies are possible, so state which one your code relies on.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md), [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 33. How do you optimise a slow query?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Measure before you change anything. Run `EXPLAIN` (or `EXPLAIN ANALYZE` where supported) on the query to see which step is slow: a full table scan, a large sort, or a join that multiplies rows. Then fix that step. Typical fixes are an index that matches the filter, fewer columns and rows returned, a rewritten predicate that can use an index, and removing N+1 queries from the application. Check the plan again after each change.

### Explanation
A checklist that works for most cases:

1. Look at the plan. Note the estimated and actual row counts. A large gap often means stale statistics.
2. Return only the columns you need. `SELECT *` pulls data you may not use and can prevent index-only scans.
3. Make predicates indexable. Avoid functions on indexed columns and leading wildcards.
4. Page with a key rather than a large `OFFSET`. A deep offset makes the database read and discard every skipped row.

```sql
-- Keyset pagination: each page starts after the last ID the client saw
SELECT id, title
FROM articles
WHERE id > :lastSeenId
ORDER BY id
LIMIT 20;
```

5. In the application, fix N+1 queries, usually by fetching the related rows in one query.

### When to use / pitfalls
- Test with data of production size. A query that is fast on 1,000 rows can be slow on 100 million.
- Every index speeds reads and slows writes. Adding one to fix a single query can hurt the rest of the system.

**See also:** [Data and persistence part 1](data-and-persistence-part-1.md), [Data and persistence part 2](data-and-persistence-part-2.md)

</details>

---

## 34. What is the difference between replication and sharding?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Replication keeps copies of the same data on several nodes, which improves availability and read capacity. Sharding (or partitioning across nodes) gives each node a different subset of the rows, which spreads write load and storage. The two are often combined: each shard is itself replicated.

### Explanation
**Replication.** A primary takes the writes, and one or more replicas copy its changes. Replication can be synchronous, which waits for the replica before committing, or asynchronous, which does not. With asynchronous replication, a replica can lag behind, so a read sent to the replica may miss a recent write. Clients that need to read their own writes should read from the primary or check the replica's position.

**Sharding.** A shard key decides which node holds each row, for example by hashing a customer ID. Each node stores only its share of the data, so both storage and write throughput grow with the number of nodes.

The costs of sharding:
- Queries that span shards need scatter-gather work, and joins across shards are hard.
- Transactions across shards need extra protocols or are avoided altogether.
- A poor shard key creates hot shards, where one node takes most of the traffic.
- 
### When to use / pitfalls
- Replicate first. Sharding adds complexity that a single large node or a read replica often avoids.
- Pick a shard key with many distinct values that matches the most common query, so most queries touch one shard.
- Replica lag is a correctness issue for user-facing flows, not just a performance metric. Monitor it.

**See also:** [Data and persistence part 2](data-and-persistence-part-2.md), [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

**Next:** [Part 4](data-and-persistence-part-4.md)
