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
