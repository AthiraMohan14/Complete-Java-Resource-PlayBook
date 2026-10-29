# Integration Testing

Integration tests check that the parts of an application work together: Spring wiring, persistence mappings, transactions, and messaging. They are slower than unit tests, so the trade-off is scope against speed. Interviewers ask about this because a green unit suite can still hide broken SQL, wrong transaction boundaries, or misconfigured beans.

## Core concepts

### @SpringBootTest and the test context

`@SpringBootTest` starts an application context close to production. It is the widest standard test scope, so use it for a focused set of end-to-end flows rather than for every case.

```java
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.http.ResponseEntity;

@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderFlowIT {

    @Autowired
    TestRestTemplate rest;

    @Test
    void health() {
        ResponseEntity<String> response = rest.getForEntity("/actuator/health", String.class);
        assertEquals(200, response.getStatusCode().value());
    }
}
```

`RANDOM_PORT` starts a real server on a free port, which is useful when you need the full HTTP stack. `TestRestTemplate` is a convenience for calling it. Note that `TestRestTemplate` is a test helper and is not related to the production `RestTemplate` deprecation discussed in [HTTP Clients](../09-spring-boot/http-clients-and-testing.md).

### Context caching

Spring caches test contexts. Tests that share the same configuration (the same annotations and properties) reuse one context, which saves startup time. Any difference, such as a different `@MockBean` set or a `@TestPropertySource`, creates a new context. Many different configurations in one suite make it slow, and memory use grows with each cached context.

### @DirtiesContext

`@DirtiesContext` discards the cached context after a test or class, so the next test starts clean. It fixes state leaks, but every use adds startup cost. Prefer resetting data (see below) over dirtying the context.

### Resetting data between tests

Common options, from lightest to heaviest:

- `@Transactional` on the test rolls back changes after each test. It is convenient, but it does not exercise commits, flushes, or separate transactions.
- `@Sql` runs scripts before or after a method.
- Truncate or delete tables in `@BeforeEach` through a repository.
- Recreate the database container for a class (costly, but fully isolated).

```java
import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

@SpringBootTest
class CleanStateExample {

    @Autowired
    JdbcTemplate jdbc;

    @BeforeEach
    void clean() {
        jdbc.update("DELETE FROM orders");
    }
}
```

### Slice tests for focused integration

Between a unit test and `@SpringBootTest` sit the slice tests from [HTTP Clients and Testing](../09-spring-boot/http-clients-and-testing.md): `@DataJpaTest` for repositories, `@WebMvcTest` for controllers, and `@RestClientTest` for clients. Use them when they cover the risk, because they start faster.

### Testcontainers

Testcontainers starts real services (PostgreSQL, Kafka, Redis, and others) in Docker for a test run. It is more faithful than an in-memory database, which can accept SQL that production rejects, or behave differently with locking, JSON types, or dialects.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.boot.test.context.SpringBootTest;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

@SpringBootTest
@Testcontainers
class OrderRepositoryIT {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @Autowired
    OrderRepository orders;

    @Test
    void savesOrder() {
        orders.save(new OrderEntity("book", 2));
        org.junit.jupiter.api.Assertions.assertEquals(1, orders.count());
    }
}

interface OrderRepository extends org.springframework.data.jpa.repository.JpaRepository<OrderEntity, Long> {}

@jakarta.persistence.Entity
class OrderEntity {
    @jakarta.persistence.Id
    @jakarta.persistence.GeneratedValue
    Long id;
    String item;
    int quantity;

    protected OrderEntity() {}

    OrderEntity(String item, int quantity) {
        this.item = item;
        this.quantity = quantity;
    }
}
```

`@ServiceConnection` (Spring Boot 3.1 and later) wires the container's connection details into the application, so you do not set URLs by hand. It needs the `spring-boot-testcontainers` module. Testcontainers' Java package names for database modules have changed between major versions, so check the import for the version you use. The `postgres:16` tag is an example; pin a tag your production system runs.

Startup of a container costs seconds, so share one container across a suite where possible. Ryuk (the Testcontainers cleanup container) removes containers after the run.

### Testing Kafka and other messaging

The same pattern works for Kafka and RabbitMQ: a Testcontainers container and a test that publishes a message, then waits for the listener to act. Use a bounded wait such as `Awaitility` rather than `Thread.sleep`, and avoid asserting on timing.

## How it works / Step by step

1. The test class declares its scope with annotations (`@SpringBootTest`, `@DataJpaTest`, and so on).
2. Spring builds the context, or reuses a cached one.
3. Testcontainers starts any declared containers before the context is created, and `@ServiceConnection` injects their connection details.
4. Tests run against the real components.
5. Data is reset, and containers stop at the end of the run.

## Common pitfalls

- Testing everything with `@SpringBootTest`, making the suite slow.
- Many small configuration variations, which creates many cached contexts and exhausts memory.
- Relying on `@Transactional` rollback to test commit behaviour.
- Using H2 when production runs PostgreSQL, then discovering SQL differences in production.
- Hard-coding ports or hostnames instead of letting containers assign them.
- `Thread.sleep` in tests, which makes them flaky.
- Running Docker-based tests in CI without Docker available, so tests are silently skipped or fail intermittently.

!!! tip "Interview tip"
    **Q: How do you test a repository against a real database?**
    Use a Testcontainers container for the same database engine as production, wire it with `@ServiceConnection` or `@DynamicPropertySource`, and keep the context and test data scope controlled. An in-memory database is faster but can hide dialect and SQL differences.

## Quick recap

- `@SpringBootTest` is the broadest scope; use it sparingly and keep configurations consistent to reuse the context.
- Reset data deliberately; `@Transactional` rollback is not a substitute for real commits.
- Testcontainers provides production-like dependencies in Docker.
- `@ServiceConnection` removes manual wiring of connection details.
- Avoid sleeps; wait for conditions with bounded timeouts.

**See also:** [HTTP Clients and Testing](../09-spring-boot/http-clients-and-testing.md) | [Kafka](../13-messaging/kafka.md) | [Databases and SQL](../06-databases-sql/index.md)
