# JDBC and Java Persistence

Talking to a relational database from Java: raw JDBC, the JPA and Hibernate object mapping, Spring Data repositories, DTO mapping, and schema migrations. This section covers roadmap section 7.

---

## Topics

### [JDBC](jdbc.md)
**DriverManager - connection pools - PreparedStatement - ResultSet - transactions**
The low-level API under every persistence tool, including parameter binding, batches, and manual transactions.

### [JPA and Hibernate](jpa-hibernate.md)
**@Entity - relationships - LAZY vs EAGER - JOIN FETCH - persistence context**
Object-relational mapping, fetch strategies, the N+1 problem, and how entity state changes are flushed.

### [Spring Data JPA](spring-data-jpa.md)
**JpaRepository - derived queries - @Query - Specification - Pageable**
Repository interfaces, custom queries, dynamic filters, pagination, and projections.

### [DTOs and Mapping](dto-mapping.md)
**DTO pattern - records - MapStruct - ModelMapper - projections**
Keeping entities out of the API, compile-time versus reflection-based mapping, and performance trade-offs.

### [Database Migrations](database-migrations.md)
**Flyway - Liquibase - versioned changes - expand and contract - testing**
Versioned schema changes, tool choice, rollback strategies, and migration testing.
