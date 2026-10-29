# Part 2: Data, JDBC & Spring

Phases 3 and 4 of the [Full Stack Java Developer Roadmap](index.md). Build the project tooling and data layer first, then the Spring framework that sits on top of them.

---

## Phase 3: Build Tools & Database Layer

### 5. Build Tools & Dependency Management (3–5 days)

#### Maven
- POM structure: dependencies, plugins, properties
- Maven Central and repository configuration
- Build lifecycle: `validate`, `compile`, `test`, `package`, `install`, `deploy`
- Profiles for environment-specific builds; plugins and goals
- Dependency management: version ranges, exclusions, transitive dependencies
- Multi-module projects; Maven Surefire (tests); Maven Shade (fat JAR)

#### Gradle
- `build.gradle` (Groovy) and `build.gradle.kts` (Kotlin) configuration
- Tasks and task dependencies; the Gradle wrapper (`gradlew`)
- Multi-project builds; dependency management
- Plugins (Java, Spring Boot); custom tasks
- Gradle vs Maven: trade-offs and build performance

#### General
- Semantic versioning
- Dependency resolution strategies
- Private repositories and authentication
- Preventing "JAR hell" (conflicting versions on the classpath)

---

### 6. Databases & SQL (2–3 weeks)

#### SQL Fundamentals
- **DDL:** `CREATE TABLE`, `ALTER`, `DROP`, `TRUNCATE`
- **DML:** `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- **Constraints:** `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `CHECK`, `NOT NULL`, `DEFAULT`
- **Data types:** `INT`, `VARCHAR`, `DATE`, `DECIMAL`, `BOOLEAN`, `JSON`

#### Intermediate SQL
- `WHERE`, `ORDER BY`, `LIMIT`, `OFFSET`, `DISTINCT`
- Joins: inner, left, right, full outer, cross; self-joins
- Aggregates: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`; `GROUP BY` and `HAVING`
- Subqueries: scalar, inline views, correlated; `IN`, `EXISTS`, `NOT EXISTS`
- `UNION`, `INTERSECT`, `EXCEPT`; `CASE` expressions

#### Advanced SQL
- **Window functions:** `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`
- **CTEs:** common table expressions, including recursive CTEs
- **Transactions:** `COMMIT`, `ROLLBACK`, `SAVEPOINT`
- **ACID properties** and isolation levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable
- Locking mechanisms; deadlock resolution

#### Query Optimisation
- Indexes: B-tree, hash, bitmap, full-text; choosing the right index
- Query Execution plans with `EXPLAIN`; cost analysis
- Query Tuning: avoiding N+1 queries, rewriting subqueries
- Denormalisation strategies; materialised views
- Partitioning: range, hash, list, composite

#### Normalisation & Design
- 1NF, 2NF, 3NF, BCNF; denormalisation trade-offs
- Entity-relationship (ER) modelling
- Database design principles

#### Specific Databases
- **MySQL:** InnoDB vs MyISAM; replication; sharding strategies; performance tuning
- **PostgreSQL:** JSONB; full-text search; window functions; extensions
- **Redis:** strings, lists, sets, hashes, sorted sets; pub/sub; transactions
- **NoSQL awareness:** MongoDB, Cassandra, DynamoDB (basic understanding)

---

### 7. JDBC & Java Persistence (1–2 weeks)

#### JDBC
- JDBC architecture; driver types (1, 2, 3, 4); `DriverManager`
- Connection management; connection pooling with HikariCP (the Spring Boot default) and  Tomcat, C3P0
- `PreparedStatement` for parameterised queries (protection against SQL injection). Statement execution modes
- `ResultSet`: forward-only, scrollable, updatable
- Batch operations; `CallableStatement` for stored procedures
- Resource management with try-with-resources
- Transactions: `setAutoCommit`, `commit`, `rollback`, savepoints

#### JPA & Hibernate
- Entity annotations: `@Entity`, `@Table`, `@Id`, `@GeneratedValue`, `@Column`
- Relationships: `@OneToOne`, `@OneToMany`, `@ManyToMany`; cascade options
- Fetch strategies: `LAZY` vs `EAGER`; `JOIN FETCH` in JPQL; Hibernate's `@Fetch`
- JPQL (Java Persistence Query Language); HQL((Hibernate Query Language)); the Criteria API; native SQL queries
- Lifecycle callbacks: `@PrePersist`, `@PostPersist`, `@PreUpdate`, `@PostUpdate`, `@PreRemove`, `@PostRemove`
- Session management; first-level cache (session cache)
- Lazy loading; proxy objects; detached entities

#### Spring Data JPA
- Repository pattern: `JpaRepository`, `PagingAndSortingRepository`
- Derived query methods (`findBy…`, `countBy…`, `deleteBy…`); custom queries with `@Query`
- Specifications for dynamic queries; named queries
- Pagination with `Page` and `Pageable`; sorting; projections

#### DTOs & Mapping
- The DTO pattern and its benefits
- MapStruct (compile-time mapping) vs ModelMapper (reflection-based)
- Bean mapping strategie
- Performance considerations for each approach

#### Database Migrations
- **Flyway:** versioned migrations, callbacks, validation
- **Liquibase:** XML, YAML, or SQL changelogs
- Schema versioning; rollback strategies; testing migrations

---

## Phase 4: Spring Framework & Boot

### 8. Spring Core & Fundamentals (2–3 weeks)

#### Inversion of Control (IoC)
- `ApplicationContext` types - ClassPathXmlApplicationContext, AnnotationConfigApplicationContext; XML, Java, and annotation-based configuration
- Bean definitions and bean scopes: `singleton`, `prototype`, `request`, `session`, `application`, `websocket`
- Bean lifecycle: instantiation, property setting, initialisation, destruction

#### Dependency Injection
- Constructor injection (preferred), setter injection, field injection, method injection
- Autowiring modes: no, byName, byType, constructor
- Autowiring: `@Autowired`, `@Resource`, `@Inject`
- Disambiguation with `@Qualifier` and `@Primary`
- Circular dependencies: Spring Boot 2.6+ prohibits them by default. Know how to redesign around them.
- Optional dependencies

#### Stereotype Annotations
- `@Component`, `@Service`, `@Repository`, `@Controller`
- `@Configuration` and `@Bean`
- Component scanning; include and exclude filters

#### Aspect-Oriented Programming (AOP)
- Aspects, pointcuts, join points
- Advice: `@Before`, `@After`, `@Around`, `@AfterReturning`, `@AfterThrowing`
- Weaving: compile-time, load-time, runtime; Spring uses proxy-based AOP
- Cross-cutting concerns: logging, security, transactions, validation

#### Spring MVC
- `DispatcherServlet`, handler mapping, view resolution
- `@Controller`, `@RequestMapping`, `RequestContext`, `ModelAndView`
- Interceptors vs filters; locale and theme resolution

#### Transactions
- `@Transactional`; propagation levels (`REQUIRED`, `REQUIRES_NEW`, `NESTED`, and others)
- Isolation levels; rollback rules; read-only optimisation
- `TransactionTemplate` and `PlatformTransactionManager`

---

### 9. Spring Boot (3–4 weeks)

#### Boot Basics
- `@SpringBootApplication` and auto-configuration (`@EnableAutoConfiguration`)
- Embedded Tomcat, Jetty, or Undertow
- `application.properties` and `application.yml`
- Profiles (`dev`, `test`, `prod`); environment abstraction
- Configuration binding: `@ConfigurationProperties`, `@Value`
- Spring Boot Starters; executable (fat) JAR packaging

#### Building REST APIs
- `@RestController`; `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`
- `@RequestBody`, `@ResponseBody`, `@PathVariable`, `@RequestParam`, `@RequestHeader`
- `HttpEntity`, `ResponseEntity` and HTTP status codes
- Content negotiation (JSON, XML); media types

#### Validation
- JSR-303/JSR-380, Jakarta Bean Validation (`jakarta.validation`, formerly `javax.validation` before Spring Boot 3): `@NotNull`, `@NotBlank`, `@Email`, `@Pattern`, `@Min`, `@Max`, `@Size`
- `@Valid` and `@Validated`; custom validators
- `MethodValidationPostProcessor`; validation messages

#### Exception Handling
- `@ExceptionHandler`; `@RestControllerAdvice` and `@ControllerAdvice`
- A global exception handler mapping exceptions to status codes
- Custom exception classes; error response DTOs
- See [Problem Details](https://www.rfc-editor.org/rfc/rfc9457) (RFC 9457) for a standard error format

#### Spring Boot Actuator
- Health checks (`/actuator/health`); metrics (`/actuator/metrics`)
- Custom health indicators
- Other endpoints: `/beans`, `/env`, `/mappings`, `/threaddump`. Expose only what you need, and secure the rest.
- Micrometer integration

#### API Documentation
- Swagger/OpenAPI with springdoc (`springdoc-openapi-starter-webmvc-ui` for Spring Boot 3)
- Annotations: `@Operation`, `@ApiResponse`, `@Parameter`
- Auto-Generated API documentation at runtime

#### HTTP Clients
- `RestTemplate` (blocking, deprecated) is in maintenance mode. Know it, but prefer `RestClient` (synchronous) or `WebClient` (reactive, recommended).
- Declarative clients: OpenFeign
- Retry mechanisms; timeouts; error handling in HTTP calls

#### Testing
- `@SpringBootTest`
- Slice tests: `@DataJpaTest`, `@WebMvcTest`, `@RestClientTest`
- `MockMvc` for REST endpoints; REST Assured for API testing
- Embedded databases (H2, in-memory) and Testcontainers

---

## Next

Continue to [Part 3: Production Engineering](part-3-production-engineering.md).
