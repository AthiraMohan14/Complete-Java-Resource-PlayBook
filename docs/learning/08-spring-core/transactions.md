# Transactions in Spring

Spring manages transactions declaratively with `@Transactional`, or programmatically with `TransactionTemplate`. Both sit on a `PlatformTransactionManager`, which hides the differences between JDBC, JPA, and other resources. Interviewers ask about transactions to check that you know propagation, rollback rules, and why an annotation sometimes does nothing.

## Core concepts

### Declarative transactions with @Transactional

`@Transactional` marks a method (or class) as transactional. Spring wraps the bean in a proxy that starts a transaction before the method and commits or rolls back afterwards.

```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PaymentService {

    @Transactional
    public void capture(long orderId) {
        // all database work here commits together, or rolls back together
    }
}
```

Put the annotation on the service layer, where a unit of work is defined, rather than on repositories or controllers.

### Propagation

Propagation decides what happens when a transactional method is called while a transaction already exists.

| Propagation | Behaviour |
|---|---|
| `REQUIRED` (default) | Join the current transaction, or start one if none exists |
| `REQUIRES_NEW` | Suspend the current transaction and start a new, independent one |
| `NESTED` | Run inside a savepoint of the current transaction; needs savepoint support (JDBC) |
| `SUPPORTS` | Join if one exists; otherwise run without a transaction |
| `NOT_SUPPORTED` | Run without a transaction; suspend any existing one |
| `MANDATORY` | Require an existing transaction; fail if none |
| `NEVER` | Fail if a transaction exists |

```java
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

public class AuditService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordFailure(String message) {
        // commits even if the calling transaction later rolls back
    }
}
```

`REQUIRES_NEW` is useful for audit records that must persist even when the business operation fails. It takes a separate database connection, so it can exhaust a pool if overused.

### Rollback rules

By default, Spring rolls back when a method throws an unchecked exception (`RuntimeException` or `Error`). A checked exception commits the transaction unless you say otherwise. This surprises many people.

```java
import org.springframework.transaction.annotation.Transactional;

public class ImportService {

    @Transactional(rollbackFor = Exception.class)      // roll back on checked exceptions too
    public void importFile(String path) throws java.io.IOException {
        // any exception now rolls back the import
    }

    @Transactional(noRollbackFor = IllegalStateException.class)
    public void tolerateWarnings() {
        // this exception type does not roll back
    }
}
```

Catching an exception inside a transactional method and not rethrowing it commits the transaction, because Spring never sees the failure. If you must catch, mark the transaction for rollback with `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`, or rethrow.

### Isolation levels

The `isolation` attribute sets the database isolation level for the transaction (see [Advanced SQL and Transactions](../06-databases-sql/advanced-sql-transactions.md)). It is applied when the transaction starts and is only honoured if the database supports it.

```java
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

public class InventoryService {

    @Transactional(isolation = Isolation.REPEATABLE_READ)
    public int reserve(long itemId, int quantity) {
        return 0;   // placeholder body for illustration
    }
}
```

Use isolation levels sparingly. Stronger levels reduce anomalies but reduce concurrency. For counter updates, an atomic `UPDATE` or explicit locking is often clearer than a high isolation level.

### Read-only optimisation

`@Transactional(readOnly = true)` is a hint. Spring passes it to the transaction manager, which may let JPA skip dirty checking and let the driver route to a replica. It does not prevent writes at the database level in every setup, so do not rely on it for security.

```java
import java.util.List;
import org.springframework.transaction.annotation.Transactional;

public class OrderQueryService {

    @Transactional(readOnly = true)
    public List<String> recentOrderIds() {
        return List.of();   // placeholder for a read-only query
    }
}
```

### Programmatic transactions: TransactionTemplate

`TransactionTemplate` runs a block inside a transaction without a proxy. It is useful when you need a transaction boundary inside a method, or when self-invocation makes the annotation ineffective.

```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class SettlementService {

    private final TransactionTemplate tx;

    public SettlementService(PlatformTransactionManager transactionManager) {
        this.tx = new TransactionTemplate(transactionManager);
    }

    public void settle(long batchId) {
        tx.executeWithoutResult(status -> {
            // work inside the transaction
            if (batchId < 0) {
                status.setRollbackOnly();      // roll back without throwing
            }
        });
    }
}
```

`PlatformTransactionManager` is the abstraction Spring uses for all transaction resources. Spring Boot configures one automatically (for JPA, `JpaTransactionManager`; for JDBC, `DataSourceTransactionManager`).

### Multiple databases and transaction managers

When an application writes to two databases, each database needs its own transaction manager, and Spring cannot make one `@Transactional` method commit both atomically. Name the managers, mark one as `@Primary`, and choose the other explicitly on the annotation.

```java
import jakarta.persistence.EntityManagerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.transaction.PlatformTransactionManager;

@Configuration
class TransactionManagers {

    @Bean
    @Primary
    PlatformTransactionManager ordersTx(@Qualifier("ordersEmf") EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }

    @Bean
    PlatformTransactionManager auditTx(@Qualifier("auditEmf") EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }
}
```

```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class OrderWithAudit {

    @Transactional                                        // uses the primary manager
    public void placeOrder() { }

    @Transactional(transactionManager = "auditTx")        // separate transaction on the audit database
    public void recordAudit() { }
}
```

Two points come up in interviews. First, Boot's JPA auto-configuration backs off once you define your own `EntityManagerFactory` and transaction manager, so you take responsibility for both. Second, if the audit write must match the order write, a single transaction is not possible. Use an outbox table in the primary database, or a saga with compensation, instead of two commits that can disagree.

### Wiring a DataSource and EntityManagerFactory per database

A transaction manager is only half of a second database. Each database also needs its own `DataSource` and its own `EntityManagerFactory`, and the factory must be pointed at the right entity package. Boot's auto-configuration creates one set of these, and it steps back once you define your own, so you define both sets explicitly. The pattern below keeps Boot's Hibernate settings by taking the `EntityManagerFactoryBuilder` that Boot provides.

```java
import javax.sql.DataSource;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.autoconfigure.orm.jpa.EntityManagerFactoryBuilder;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;

@Configuration
class OrdersDatabaseConfig {

    @Bean
    @Primary
    @ConfigurationProperties("app.orders.datasource")
    DataSourceProperties ordersDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    @Primary
    DataSource ordersDataSource(@Qualifier("ordersDataSourceProperties") DataSourceProperties props) {
        return props.initializeDataSourceBuilder().build();
    }

    @Bean
    @Primary
    LocalContainerEntityManagerFactoryBean ordersEmf(
            @Qualifier("ordersDataSource") DataSource dataSource,
            EntityManagerFactoryBuilder builder) {
        return builder.dataSource(dataSource)
                .packages("com.example.orders.domain")   // only the orders entities
                .persistenceUnit("orders")
                .build();
    }
}

@Configuration
class AuditDatabaseConfig {

    @Bean
    @ConfigurationProperties("app.audit.datasource")
    DataSourceProperties auditDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    DataSource auditDataSource(@Qualifier("auditDataSourceProperties") DataSourceProperties props) {
        return props.initializeDataSourceBuilder().build();
    }

    @Bean
    LocalContainerEntityManagerFactoryBean auditEmf(
            @Qualifier("auditDataSource") DataSource dataSource,
            EntityManagerFactoryBuilder builder) {
        return builder.dataSource(dataSource)
                .packages("com.example.audit.domain")
                .persistenceUnit("audit")
                .build();
    }
}
```

Each factory gets its own persistence unit name and its own entity package, so Hibernate never maps an entity to the wrong database. The transaction managers from the previous section then use these factories by name. Keep the two packages disjoint: an entity picked up by both factories is mapped twice.

Two cautions. Repositories also need to be bound to the right factory, which Spring Data does with `@EnableJpaRepositories` and the `entityManagerFactoryRef` and `transactionManagerRef` attributes, one configuration per database. And a JPA entity that references an entity in the other database cannot be joined in SQL, so the link must be a plain id.

### Read-write split with a routing DataSource

When one database has a read replica, you can send reads to the replica and writes to the primary. Spring's `AbstractRoutingDataSource` picks a `DataSource` per connection, based on a lookup key. Use the transaction's `readOnly` flag as that key, so a method annotated `@Transactional(readOnly = true)` reads from the replica without any change to the repository code.

```java
import java.util.Map;
import javax.sql.DataSource;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.datasource.LazyConnectionDataSourceProxy;
import org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource;
import org.springframework.transaction.support.TransactionSynchronizationManager;

enum Route { WRITE, READ }

class ReadWriteRouter extends AbstractRoutingDataSource {

    @Override
    protected Object determineCurrentLookupKey() {
        return TransactionSynchronizationManager.isCurrentTransactionReadOnly()
                ? Route.READ
                : Route.WRITE;
    }
}

@Configuration
class ReadWriteConfig {

    @Bean("primaryDataSource")
    DataSource primaryDataSource() {
        return DataSourceBuilder.create().url("jdbc:postgresql://primary-host/orders").build();
    }

    @Bean("replicaDataSource")
    DataSource replicaDataSource() {
        return DataSourceBuilder.create().url("jdbc:postgresql://replica-host/orders").build();
    }

    @Bean
    @Primary
    DataSource routingDataSource(@Qualifier("primaryDataSource") DataSource primary,
                                 @Qualifier("replicaDataSource") DataSource replica) {
        ReadWriteRouter router = new ReadWriteRouter();
        router.setTargetDataSources(Map.of(Route.WRITE, primary, Route.READ, replica));
        router.setDefaultTargetDataSource(primary);
        return new LazyConnectionDataSourceProxy(router);   // pick the connection after the flag is known
    }
}
```

The `LazyConnectionDataSourceProxy` wrapper matters. It delays acquiring the physical connection until the first statement, so the routing decision sees the transaction's read-only flag. Without it, the connection can be opened before the flag is set and every query goes to the primary.

Three cautions for an interview answer:

- Replicas lag behind the primary. A read right after a write, from a read-only transaction, can miss the write. Send read-your-own-write flows to the primary.
- Check the routing with a test that asserts which database a read-only query used. The exact timing depends on the transaction manager, and the flag can be set after a JPA transaction has already taken a connection, so confirm it for your setup rather than assuming it.
- Mark only truly read-only methods as `readOnly = true`. A write sent through a read-only transaction goes to the replica and fails.

### Self-invocation and visibility

Two common reasons an annotation has no effect:

- **Self-invocation:** calling a `@Transactional` method from the same class skips the proxy. See [AOP](aop.md).
- **Non-public methods:** the proxy cannot intercept private methods, and by default only public methods are transactional.

## How it works / Step by step

When a `@Transactional` method is called through the proxy:

1. The transaction interceptor asks the `PlatformTransactionManager` for a transaction, applying propagation rules.
2. If a new transaction starts, the manager obtains a connection (or EntityManager) and begins it.
3. The method runs.
4. On normal return, the transaction commits (or joins the outer one, which commits later).
5. On an exception matching the rollback rules, the transaction rolls back and the exception propagates.

Nested calls with `REQUIRED` do not commit on return; only the outermost transaction commits.

## Common pitfalls

- Expecting a checked exception to roll back. It does not, unless `rollbackFor` says so.
- Catching and swallowing an exception inside a transactional method, which commits partial work.
- Calling a `@Transactional` method from the same class.
- Putting `@Transactional` on a private method.
- Making an external HTTP call inside a transaction, which holds a database connection for the duration.
- Using `REQUIRES_NEW` in a loop, which exhausts the connection pool.
- Relying on `readOnly = true` as a security boundary.

!!! tip "Interview tip"
    **Q: Why did my `@Transactional` method not roll back when an exception was thrown?**
    Check three things: whether the exception is checked (it commits by default), whether the exception was caught inside the method, and whether the call bypassed the proxy through self-invocation. Mention `rollbackFor` as the fix for checked exceptions.

## Quick recap

- `@Transactional` is applied by a proxy; it wraps calls, not internal calls.
- `REQUIRED` joins or starts a transaction; `REQUIRES_NEW` always starts a new one.
- By default, runtime exceptions roll back; checked exceptions commit unless `rollbackFor` is set.
- `TransactionTemplate` gives explicit control over the boundary.
- Keep transactions short; do not hold them open during network calls.

**See also:** [AOP](aop.md), [Dependency Injection](dependency-injection.md), [JDBC](../07-jdbc-jpa/jdbc.md)
