# JDBC

JDBC (Java Database Connectivity) is the standard Java API for running SQL against relational databases. Interviewers ask about it because every higher-level tool, including JPA and Spring's `JdbcTemplate`, runs on top of it, and the questions reveal whether you understand connections, statements, SQL injection, and transactions.

## Core concepts

### Architecture and drivers

The `java.sql` and `javax.sql` packages define the API. Each database vendor ships a **driver** that implements it. Your code depends on the interfaces, and the driver is a runtime dependency.

JDBC driver types:

| Type | Description | Status |
|---|---|---|
| 1 | JDBC-ODBC bridge | Removed in Java 8; do not use |
| 2 | Native API partly in Java | Needs client libraries installed on each machine |
| 3 | Network protocol (middleware) | Needs a middleware server |
| 4 | Pure Java, talks the database protocol directly | The usual choice today |

Since JDBC 4.0, drivers on the classpath register themselves through `ServiceLoader`, so you rarely call `Class.forName` by hand. `DriverManager` is the older entry point for getting a connection; in applications, you usually get connections from a `DataSource`.

```java
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class ConnectDemo {
    public static void main(String[] args) throws SQLException {
        String url = "jdbc:postgresql://localhost:5432/shop";   // example URL
        try (Connection conn = DriverManager.getConnection(url, "app_user", System.getenv("DB_PASSWORD"))) {
            System.out.println("Connected: " + !conn.isClosed());
        }
    }
}
```

Read the password from configuration or the environment, never from source code.

### Connection pooling

Opening a connection is expensive, so applications keep a pool of open connections and borrow them. HikariCP is the default pool in Spring Boot. Other pools include Apache Tomcat JDBC and C3P0.

Key pool settings are the maximum pool size and the connection timeout. A pool that is too large can overload the database; a pool that is too small makes requests queue. Size it from the database's capacity, not from the number of users.

### Statements

| Type | Use it for |
|---|---|
| `Statement` | Fixed SQL with no parameters. Avoid it for anything that takes input. |
| `PreparedStatement` | Parameterised SQL. The default choice. |
| `CallableStatement` | Stored procedures and functions, with IN, OUT, and INOUT parameters. |

Methods: `executeQuery()` returns a `ResultSet` for `SELECT`; `executeUpdate()` returns the row count for `INSERT`, `UPDATE`, `DELETE`; `execute()` returns a boolean for general statements.

### PreparedStatement and SQL injection

`PreparedStatement` sends the SQL text and the parameter values separately, so input is never parsed as SQL. Building SQL with string concatenation allows SQL injection.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class CustomerLookup {
    static void find(Connection conn, String email) throws SQLException {
        // Vulnerable: input such as "x' OR '1'='1" changes the query
        String bad = "SELECT * FROM customer WHERE email = '" + email + "'";

        // Safe: the value is bound as data
        String good = "SELECT * FROM customer WHERE email = ?";
        try (PreparedStatement ps = conn.prepareStatement(good)) {
            ps.setString(1, email);
            // ps.executeQuery() ...
        }
    }
}
```

Parameters cannot replace table or column names. Validate those against an allow-list.

### ResultSet

A `ResultSet` is a cursor over query results. Its type controls movement:

- `TYPE_FORWARD_ONLY` (default): move forward only. Lowest memory use.
- `TYPE_SCROLL_INSENSITIVE` or `TYPE_SCROLL_SENSITIVE`: move in both directions; support depends on the driver.

Concurrency: `CONCUR_READ_ONLY` (default) or `CONCUR_UPDATABLE`. Read columns by name or index, and check for SQL `NULL` with `wasNull()` after reading a primitive, because `getInt` returns `0` for NULL.

### Batches

Batching sends many statements in one round trip.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.List;

public class CustomerBatch {
    static void insertEmails(Connection conn, List<String> emails) throws SQLException {
        String sql = "INSERT INTO customer (email) VALUES (?)";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            for (String email : emails) {
                ps.setString(1, email);
                ps.addBatch();
            }
            ps.executeBatch();
        }
    }
}
```

Batching is faster only when the driver supports it and autocommit is off for large sets. Check the driver's batch options for rewriting.

### Stored procedures

`CallableStatement` calls a stored procedure. The `{call ...}` escape syntax is portable across drivers.

```java
import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Types;

public class CallProc {
    static long orderCount(Connection conn, long customerId) throws SQLException {
        try (CallableStatement cs = conn.prepareCall("{call count_orders(?, ?)}")) {
            cs.setLong(1, customerId);
            cs.registerOutParameter(2, Types.BIGINT);
            cs.execute();
            return cs.getLong(2);
        }
    }
}
```

### Resource management and transactions

Every `Connection`, `Statement`, and `ResultSet` holds resources. Close them with try-with-resources, and close them in the reverse order they were opened (try-with-resources does this for you).

JDBC runs in auto-commit mode by default: each statement commits on its own. For a unit of work, turn auto-commit off and call `commit()` or `rollback()` yourself, and use savepoints for partial rollback.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class Transfer {
    static void move(Connection conn, long from, long to, long cents) throws SQLException {
        conn.setAutoCommit(false);
        try (PreparedStatement debit = conn.prepareStatement(
                 "UPDATE account SET balance = balance - ? WHERE account_id = ?");
             PreparedStatement credit = conn.prepareStatement(
                 "UPDATE account SET balance = balance + ? WHERE account_id = ?")) {
            debit.setLong(1, cents);
            debit.setLong(2, from);
            debit.executeUpdate();
            credit.setLong(1, cents);
            credit.setLong(2, to);
            credit.executeUpdate();
            conn.commit();
        } catch (SQLException e) {
            conn.rollback();
            throw e;
        } finally {
            conn.setAutoCommit(true);   // restore the default for the pool
        }
    }
}
```

Returning a connection to a pool with auto-commit off, or with an open transaction, leaks state into the next user. Always restore it.

## How it works / Step by step

Running a query with JDBC:

1. Get a `Connection` from the `DataSource` (the pool lends one).
2. Prepare the SQL with `?` placeholders.
3. Bind parameters with the typed setters (`setLong`, `setString`).
4. Execute: `executeQuery` for reads, `executeUpdate` for writes.
5. Read the `ResultSet` into objects, then close all resources.
6. Commit or roll back if you turned auto-commit off.

## Common pitfalls

- Concatenating user input into SQL.
- Forgetting to close a `ResultSet` or `Connection`, which exhausts the pool.
- Calling `getInt` on a NULL column and getting `0`. Check `wasNull()` or use `getObject`.
- Leaving auto-commit off when a connection goes back to the pool.
- Opening a new connection per request instead of using a pool.
- Catching `SQLException` and ignoring it, which hides failed writes.

!!! tip "Interview tip"
    **Q: Why does a `PreparedStatement` prevent SQL injection?**
    The SQL structure is sent and parsed separately from the values, so bound values are treated as data and never as SQL keywords. It can also let the database reuse the query plan. Note that it does not protect identifiers such as table names; those need an allow-list.

## Quick recap

- JDBC is the base API; drivers are type 4 in modern use, and type 1 is gone.
- Use `PreparedStatement` for all input-driven SQL.
- Pools (HikariCP in Spring Boot) manage connections; always close and reset what you borrow.
- Batches reduce round trips; `CallableStatement` runs stored procedures.
- Turn auto-commit off for multi-statement units of work, and roll back on failure.

**See also:** [JPA and Hibernate](jpa-hibernate.md), [Spring Data JPA](spring-data-jpa.md), [SQL Advanced and Transactions](../06-databases-sql/advanced-sql-transactions.md)
