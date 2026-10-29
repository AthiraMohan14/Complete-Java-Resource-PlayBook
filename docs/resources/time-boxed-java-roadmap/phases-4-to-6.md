# Phases 4 to 6: Spring, Security and Messaging

This part covers weeks 15 to 49 of the plan. Phase 4 builds the Spring stack from the container up to REST APIs. Phase 5 adds security, testing, and caching. Phase 6 moves to messaging and microservices. Use the Spring Boot 3 line throughout, which needs Java 17 or later and the `jakarta.*` namespace.

---

## Phase 4: Spring Framework and Boot (weeks 15-28)

Phase 4 has two topics: Spring Core in two to three weeks, and Spring Boot in three to four weeks.

### Topic 8: Spring Core (2-3 weeks)

**Week 1: Inversion of control and dependency injection**

- The `ApplicationContext`, and the difference between `AnnotationConfigApplicationContext` and XML-based configuration.
- Bean definitions and scopes: singleton (the default), prototype, request, and session.
- Injection with constructors, setters, and `@Autowired`, `@Resource`, and `@Inject`. Constructor injection is the preferred style.
- Circular dependencies. Since Spring Boot 2.6, circular references fail at startup by default. Refactor the design rather than enabling them.

```java
import org.springframework.stereotype.Service;

@Service
public class OrderService {
    private final PaymentClient payments;

    public OrderService(PaymentClient payments) {   // constructor injection
        this.payments = payments;
    }
}

interface PaymentClient { }
```

**Week 2: Stereotypes, configuration, and AOP**

- `@Component`, `@Service`, `@Repository`, and `@Controller`. They are all components, and each one marks a layer.
- `@Configuration` and `@Bean` methods, and component scanning.
- Aspect-oriented programming with `@Aspect`, `@Pointcut`, and the advice types `@Before`, `@After`, and `@Around`.
- Cross-cutting concerns such as logging, security checks, and transactions. Spring's proxies apply AOP to beans called through the container, so a call from inside the same class bypasses the advice.

**Week 3: Spring MVC and transactions**

- The `DispatcherServlet`, handler mapping, and view resolution.
- `@Controller`, `@RequestMapping`, interceptors, and servlet filters, and the order they run in.
- `@Transactional`: propagation (`REQUIRED`, `REQUIRES_NEW`, `NESTED`), isolation levels, and rollback rules. By default, only unchecked exceptions roll back.
- `TransactionTemplate` for programmatic transactions, and `PlatformTransactionManager` as the underlying abstraction.

**Interview tip:** explain why `@Transactional` on a method called from inside the same class does not start a transaction. The answer is the proxy, and the fix is to move the call through another bean or to use a different design.

### Topic 9: Spring Boot (3-4 weeks)

**Week 1: Boot basics**

- `@SpringBootApplication`, which combines configuration, component scanning, and auto-configuration.
- `application.properties` and `application.yml`, and how the two are merged.
- Profiles for `dev`, `test`, and `prod`.
- `@ConfigurationProperties` for typed configuration, and `@Value` for single values.
- The embedded server (Tomcat by default) and the executable JAR.

**Week 2: REST APIs**

- `@RestController`, `@RequestMapping`, and the shortcut annotations `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, and `@PatchMapping`.
- Binding with `@RequestBody`, `@PathVariable`, and `@RequestParam`.
- `ResponseEntity` for setting the status code and headers.
- Content negotiation between JSON and XML, and which formats the default setup supports.

**Week 3: Validation, errors, and monitoring**

- Jakarta Bean Validation, which was previously called JSR-303 and JSR-380. Use `@NotNull`, `@Email`, `@Pattern`, and `@Valid` on the request body.
- `@ExceptionHandler` and `@RestControllerAdvice` for a single error-handling point.
- Error responses in the RFC 9457 "Problem Details" format. RFC 9457 replaces RFC 7807.
- Spring Boot Actuator endpoints such as `/actuator/health` and `/actuator/metrics`, and custom health indicators.
- Micrometer as the metrics facade that Actuator uses.

**Week 4: API documentation and testing**

- OpenAPI documentation with the springdoc-openapi starter for Spring Boot 3, and annotations such as `@Operation`, `@ApiResponse`, and `@Parameter`.
- Test slices: `@SpringBootTest` for the full context, `@WebMvcTest` for the web layer, and `@DataJpaTest` for the persistence layer.
- `MockMvc` for controller tests, REST Assured for black-box API tests, and Testcontainers for real databases in Docker.

**Project:** an e-commerce API with controllers, services, repositories, validation, error handling, Actuator, and OpenAPI documentation.

---

## Phase 5: Security, Testing and Caching (weeks 29-35)

Phase 5 has three topics that take about seven weeks in total.

### Topic 10: Security (2 weeks)

**Week 1: authentication and authorization**

- Spring Security basics: the `SecurityContext`, `UserDetails`, and `Authentication`.
- The filter chain. Spring Security 6 configures a `SecurityFilterChain` bean. `WebSecurityConfigurerAdapter` was removed in Spring Security 6.
- Role-based access control and method security with `@PreAuthorize` and `@PostAuthorize`. `@Secured` also works but is less flexible.

**Week 1 to 2: authentication mechanisms**

- **JWT:** the three parts (header, payload, signature), how a server checks the signature, token expiry, and refresh tokens. A JWT is signed, not encrypted, so do not put secrets in its payload.
- **OAuth 2.0:** the authorization code flow, access tokens, and refresh tokens.
- **OpenID Connect:** an identity layer on top of OAuth 2.0 that adds ID tokens and a user-info endpoint.
- **Multi-factor authentication:** what each factor proves, and where it is weakest.

**Week 2: advanced security**

- Password storage with an adaptive hash such as bcrypt or Argon2. A salt is stored with each hash. A pepper is a secret kept outside the database.
- CORS and CSRF. CSRF protection matters most for cookie-based sessions. A stateless API that uses bearer tokens usually disables CSRF on purpose.
- HTTPS and TLS: certificates, the handshake, and what a certificate chain proves.
- The OWASP Top 10 and the prevention for each category.
- Secrets management with environment variables, a secrets manager such as HashiCorp Vault, or a cloud provider's secret store.

**Projects:** a secure REST API that issues and checks JWTs, an OAuth 2.0 login with a public identity provider, and a multi-tenant application with role checks per tenant.

### Topic 11: Testing (1-2 weeks)

**Unit tests**

- JUnit 5 (Jupiter): `@Test`, `@BeforeEach`, `@AfterEach`, and `@ParameterizedTest` for data-driven cases.
- Assertions and matchers. AssertJ gives more readable failure messages than the JUnit assertions.

**Mocking**

- Mockito: `@Mock`, `@InjectMocks`, and `@Spy`.
- Stubbing with `when(...).thenReturn(...)`, argument captors, and verification with `verify`.
- Mock the collaborators of the class under test, not the class itself.

**Integration tests**

- `@SpringBootTest` and the test context cache. A changed configuration creates a new context, which is slow.
- Testcontainers for real databases and message brokers in Docker.
- `@DirtiesContext` when a test changes shared state that the cache cannot reset.

**API tests**

- `MockMvc`: `perform()`, `andExpect()`, and `andReturn()`.
- REST Assured: `given().when().then()` for calls to a running service.
- Contract testing with Spring Cloud Contract, to check that a provider and its consumers agree on a request and response format.

**Coverage**

- JaCoCo for line and branch coverage reports.
- SonarQube for coverage together with code-quality rules.
- Coverage shows what ran, not whether the assertions were useful. Look at tests that assert nothing.

### Topic 12: Caching and Performance (1-2 weeks)

**Spring Cache abstraction**

- `@Cacheable`, `@CachePut`, `@CacheEvict`, and `@Caching` to combine them.
- Cache managers and key generation. Caching is applied through the proxy, so the same self-invocation caveat applies as with `@Transactional`.
- Conditional caching with `condition` and `unless`.

**Redis**

- Data types: strings, lists, sets, hashes, and sorted sets.
- Spring Data Redis and `RedisTemplate`.
- Session storage with Spring Session backed by Redis.
- Distributed locks and Pub/Sub. A lock needs a timeout and a safe release.

**Performance**

- Profiling with VisualVM, JProfiler, or async-profiler.
- Database problems such as the N+1 query pattern, and how to fix it with fetch joins or entity graphs.
- JVM tuning and connection pool sizing. A larger pool is not always faster.
- Load testing with JMeter or Gatling.

---

## Phase 6: Messaging and Microservices (weeks 36-49)

Phase 6 has two topics: messaging in one to two weeks, and microservices in three to four weeks.

### Topic 13: Messaging and Event-Driven Design (1-2 weeks)

**Apache Kafka (3-4 days)**

- Architecture: brokers, topics, partitions, and replicas.
- Producers: serialization, partition keys, and acknowledgment settings (`acks`).
- Consumers: consumer groups, offsets, and rebalancing.
- Three delivery guarantees: at most once, at least once, and exactly once. Exactly-once in Kafka applies to Kafka-to-Kafka processing. A side effect in a database still needs an idempotent write.
- Spring Kafka: `KafkaTemplate` for sending and `@KafkaListener` for receiving.
- Error handling with retries and a dead-letter topic.

**RabbitMQ (2-3 days)**

- The AMQP model: exchanges, queues, and bindings.
- Exchange types: direct, topic, fanout, and headers.
- Spring AMQP for sending and listening.
- Message TTL and manual or automatic acknowledgments.

**Event-driven patterns (2-3 days)**

- Event sourcing: an append-only event store and rebuilding state by replaying events.
- CQRS: separating the write model from the read model.
- The saga pattern, in two styles. In choreography, services react to each other's events. In orchestration, a coordinator tells each service what to do.
- Eventual consistency, and how to show it to users.

### Topic 14: Microservices (3-4 weeks)

**Week 1: fundamentals**

- Decomposing a system by bounded context from domain-driven design.
- A database per service, and why shared tables couple services.
- Trade-offs between a monolith and microservices. A monolith is often the right first choice for a small team.

**Week 2: Spring Cloud and the platform around it**

- **Service discovery:** Eureka, Consul, and etcd. Kubernetes DNS is an alternative when the services run in Kubernetes.
- **Client-side load balancing:** Spring Cloud LoadBalancer.
- **Configuration:** Spring Cloud Config Server, usually backed by a Git repository.
- **API gateway:** Spring Cloud Gateway for routing and filtering.
- **Distributed tracing:** Micrometer Tracing, with Zipkin or Jaeger as the backend. Spring Cloud Sleuth is no longer the current choice; Micrometer Tracing replaced it.

**Week 3: resilience patterns**

- **Circuit breaker:** closed, open, and half-open states. Use Resilience4j. Netflix Hystrix is retired.
- **Retry:** exponential backoff with a limit. Retry only operations that are safe to repeat.
- **Timeouts:** every remote call needs one, and a deadline can be passed along the call chain.
- **Bulkheads:** separate thread pools or semaphores so that one slow dependency cannot exhaust the others.
- **Rate limiting:** token bucket and sliding window algorithms.

```java
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import java.time.Duration;
import java.util.function.Supplier;

CircuitBreakerConfig config = CircuitBreakerConfig.custom()
        .failureRateThreshold(50)                  // open when half the calls fail
        .waitDurationInOpenState(Duration.ofSeconds(30))
        .build();

CircuitBreaker breaker = CircuitBreaker.of("payments", config);
Supplier<String> guarded = CircuitBreaker.decorateSupplier(breaker, () -> "ok");
```

**Week 4: advanced topics**

- Inter-service communication: REST, gRPC, and GraphQL, and when each one fits.
- Service-to-service authentication with mTLS or with JWTs passed along the call chain.
- Distributed transactions with sagas and compensating actions. Two-phase commit is rarely practical across services.
- Monitoring and observability with the ELK stack or the Elastic stack, Prometheus, and Grafana.

**Project:** three small services with a gateway, service discovery, a Kafka topic between two of them, and a circuit breaker on one remote call.

---

## Phase 4 to 6 Deliverables

- An e-commerce REST API with validation, error responses, Actuator, and OpenAPI documentation.
- A secured API with JWT or OAuth 2.0, and tests at the unit, slice, and integration levels.
- A caching layer in Redis, with one measured performance improvement.
- Three services that talk through a broker, with a resilience policy on one remote call.

**See also:** [Phases 1 to 3](phases-1-to-3.md), [Phases 7 to 9](phases-7-to-9.md), [Spring interview questions](../../interview-questions/technical/spring-and-security-part-1.md), [Microservices interview questions](../../interview-questions/technical/architecture-and-distributed.md)
