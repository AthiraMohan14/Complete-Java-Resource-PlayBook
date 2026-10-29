# Spring, Spring Boot, and Security Questions (Part 3 of 3)

Continued from [Part 2](spring-and-security-part-2.md). These questions cover dependency injection, transactions, bean scopes, stereotypes, API security, and REST design.

---

## 19. What are the types of dependency injection, and why prefer constructor injection?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Spring supports constructor, setter, and field injection, with method injection as a rarer variant. Constructor injection is the default for required dependencies because it makes fields `final`, builds a complete object, makes tests possible with plain `new`, and fails at startup when a dependency is missing.

### Explanation
With a single constructor, Spring injects through it without `@Autowired`:

```java
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }

    public String nameOf(long id) {
        return repository.findName(id);
    }
}

interface UserRepository {
    String findName(long id);
}
```

A unit test passes a fake without starting Spring:

```java
interface UserRepository {
    String findName(long id);
}

class UserService {
    UserService(UserRepository repository) {
    }
}

class UserServiceTestDemo {
    static void demo() {
        UserService service = new UserService(id -> "test-user");
    }
}
```

Field injection hides the dependency from the constructor, prevents `final`, and forces tests to use reflection or a Spring context. Setter injection suits optional dependencies that can be replaced after construction, and it leaves the object half-built until the setter runs.

### When to use / pitfalls
- Use constructor injection for every required collaborator, and use setter injection (or `Optional<T>` parameters) for truly optional ones.
- If a class has several constructors, mark the one Spring should use with `@Autowired`.
- Constructor injection cannot resolve a cycle. Spring Boot 2.6 and later refuses circular references by default, so redesign the classes (see question 5 in [Part 1](spring-and-security-part-1.md)).
- Field injection in new code is a review finding; it is usually a shortcut that costs testability.

**See also:** [Dependency Injection](../../learning/08-spring-core/dependency-injection.md), [Spring Core](../../learning/08-spring-core/index.md)

</details>

---

## 20. How does `@Transactional` work, and what are its rollback rules?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@Transactional` works through a proxy: the proxy starts a transaction before the method, commits when the method returns normally, and rolls back when the method throws an unchecked exception (`RuntimeException` or `Error`). A checked exception commits by default, so you must name it in `rollbackFor` to roll back.

### Explanation
Here the checked exception would commit the debit unless `rollbackFor` is set:

```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

class InsufficientFundsException extends Exception {
    InsufficientFundsException(String message) {
        super(message);
    }
}

@Service
public class PaymentService {

    private final LedgerRepository ledger;

    public PaymentService(LedgerRepository ledger) {
        this.ledger = ledger;
    }

    @Transactional(rollbackFor = InsufficientFundsException.class)
    public void debit(long accountId, long cents) throws InsufficientFundsException {
        ledger.debit(accountId, cents);
        if (cents > 1_000_000) {
            throw new InsufficientFundsException("limit exceeded");   // rolled back
        }
    }
}

interface LedgerRepository {
    void debit(long accountId, long cents);
}
```

Propagation decides what happens when a transactional method is called inside another transaction. `REQUIRED` (the default) joins the existing transaction. `REQUIRES_NEW` suspends it and starts an independent one, which suits audit records that must survive a rollback. `NESTED` uses a savepoint and depends on the transaction manager supporting savepoints. `MANDATORY` fails when no transaction exists, and `SUPPORTS` runs with or without one.

Several things stop the annotation from working:

- Self-invocation bypasses the proxy, so an annotated method called from the same class runs without a transaction.
- A caught exception that is not rethrown never reaches the proxy, so the transaction commits.
- Non-public methods are not proxied by default.

### When to use / pitfalls
- Put the annotation on the service layer, where a unit of work is defined.
- Use `readOnly = true` for queries as an optimisation hint, not as a security control.
- Do not hold a transaction open across a network call; the connection stays busy for the whole call.
- `REQUIRES_NEW` takes a second connection, so using it in a loop can exhaust the pool.

**See also:** [Transactions](../../learning/08-spring-core/transactions.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 21. What are Spring bean scopes, and what is the bean lifecycle?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The core scopes are `singleton` (one instance per container, the default), `prototype` (a new instance each time it is requested), and the web scopes `request`, `session`, `application`, and `websocket`. A singleton is shared across threads, so it must be stateless or thread-safe. The lifecycle runs: constructor, dependency injection, `@PostConstruct`, `afterPropertiesSet`, the custom init method, use, `@PreDestroy`, then `destroy`.

### Explanation
A request-scoped bean needs a scoped proxy when it is injected into a singleton, otherwise the singleton keeps the first request's instance forever:

```java
import java.util.UUID;
import org.springframework.context.annotation.ScopedProxyMode;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;
import org.springframework.web.context.WebApplicationContext;

@Component
@Scope(value = WebApplicationContext.SCOPE_REQUEST, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestTrace {

    private final String id = UUID.randomUUID().toString();

    public String id() {
        return id;
    }
}
```

A prototype bean is created on each lookup, but Spring does not call its destroy callbacks, so the code that asks for it owns its cleanup. A singleton that needs a fresh prototype on each use should inject an `ObjectProvider<T>` and call `getObject()`, rather than holding one instance from construction.

Lifecycle hooks, in order:

1. Constructor runs and the object exists.
2. Dependencies are injected.
3. `BeanPostProcessor` before-initialisation logic runs, including `@PostConstruct`.
4. `afterPropertiesSet()` runs (the `InitializingBean` contract).
5. A custom `initMethod`, if configured, runs.
6. The bean serves requests.
7. On shutdown, `@PreDestroy` runs, then `destroy()`, then a custom `destroyMethod`.

### When to use / pitfalls
- Keep singletons free of per-request state. A mutable field shared by all threads is a race condition.
- Prefer `@PostConstruct` and `@PreDestroy` over the Spring interfaces; they are portable and keep the class free of framework types.
- Do not put expensive work in a constructor that runs before dependencies are ready.
- Scope mismatches (request beans in singletons) fail subtly; test them.

**See also:** [IoC and Beans](../../learning/08-spring-core/ioc-and-beans.md), [Dependency Injection](../../learning/08-spring-core/dependency-injection.md)

</details>

---

## 22. What is the difference between `@Component` and `@Bean`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@Component` (and its specialisations `@Service`, `@Repository`, `@Controller`, `@RestController`) goes on a class you own, and component scanning registers it. `@Bean` goes on a method inside a `@Configuration` class, and the method's return value becomes the bean. Use `@Bean` for third-party classes you cannot annotate, or when construction needs logic, conditions, or configuration.

### Explanation
```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component                        // scanned automatically; you own the class
class OrderNumbers {
    String next() {
        return "ORD-1";
    }
}

@Configuration
class HttpConfig {

    @Bean                         // third-party type, built here
    RestClient paymentsClient() {
        return RestClient.builder()
                .baseUrl("https://payments.example.com")
                .build();
    }
}
```

A `@Configuration` class is proxied (full mode), so a `@Bean` method that calls another `@Bean` method receives the existing singleton rather than a new instance. A `@Bean` method declared in a plain `@Component` class is processed in lite mode, which has no such guarantee.

Stereotypes also express intent. `@Service` marks business logic, `@Repository` marks data access and enables persistence-exception translation, `@Controller` returns views, and `@RestController` adds `@ResponseBody` to every handler.

### When to use / pitfalls
- Prefer `@Component` for your own classes with simple constructors.
- Prefer `@Bean` when a library class needs configuration, when the instance depends on properties, or when you need conditional registration with `@ConditionalOnProperty` or `@Profile`.
- Do not call a `@Bean` method directly from a lite-mode class; you get a new object each time.
- A name collision between two beans of the same type needs `@Primary` or `@Qualifier`.

**See also:** [Stereotypes and Configuration](../../learning/08-spring-core/stereotypes-and-configuration.md), [Dependency Injection](../../learning/08-spring-core/dependency-injection.md)

</details>

---

## 23. How do you secure a Spring Boot REST API?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Put a Spring Security filter chain in front of the API, authenticate clients with short-lived bearer tokens (for example, JWTs), leave only login and public endpoints open, and authorise each route by role or authority. Store passwords with a strong adaptive hash such as BCrypt, serve everything over HTTPS, and restrict cross-origin access with CORS.

### Explanation
A stateless API configures a `SecurityFilterChain` bean. Spring Security 6 (used by Boot 3) replaced `antMatchers` and the chained `.and()` style with `requestMatchers` and lambda configuration, so older examples will not compile:

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
class ApiSecurity {

    @Bean
    SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
        return http
                .csrf(csrf -> csrf.disable())   // token-based API; no browser cookies carry auth
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/api/auth/**").permitAll()
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .anyRequest().authenticated())
                .addFilterBefore(new JwtFilter(), UsernamePasswordAuthenticationFilter.class)
                .build();
    }

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

The filter reads the `Authorization: Bearer` header, verifies the signature and expiry, and sets the authentication in the security context:

```java
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.web.filter.OncePerRequestFilter;

class JwtFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        // read the bearer token, verify it, and populate the SecurityContext
        chain.doFilter(request, response);
    }
}
```

Login issues the token after checking the password with the `PasswordEncoder`. Access tokens should expire within minutes, and refresh tokens should be rotated and revocable. Verify the signature and the issuer and audience claims on every request; an unverified token is just a string.

### When to use / pitfalls
- Disable CSRF only for token-only APIs. If a browser sends cookies, keep CSRF protection on.
- Do not store the JWT secret in code; load it from a secrets store.
- Use `@PreAuthorize` for object-level checks that the URL patterns cannot express.
- Read the authorisation rules in order: the first matching `requestMatchers` wins.

**See also:** [Spring Security Authorisation](../../learning/10-security/spring-security-authorisation.md), [Authentication, JWT, and OAuth](../../learning/10-security/authentication-jwt-oauth.md), [Part 2 on JWT](spring-and-security-part-2.md)

</details>

---

## 24. What are the strategies for API versioning?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The four common strategies are a version in the URL path, a custom request header, a version in the media type (content negotiation), and a query parameter. URL path versioning is the most visible and the easiest to route, cache, and test, so it is the usual choice for public APIs. The other strategies keep URLs cleaner but are harder to discover and test.

### Explanation
Path versioning maps each version to its own controller or method:

```java
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

record UserV1(long id, String name) { }
record UserV2(long id, String fullName, String email) { }

@RestController
@RequestMapping("/api/v1/users")
class UserV1Controller {
    @GetMapping
    List<UserV1> list() {
        return List.of(new UserV1(1, "Ada"));
    }
}

@RestController
@RequestMapping("/api/v2/users")
class UserV2Controller {
    @GetMapping
    List<UserV2> list() {
        return List.of(new UserV2(1, "Ada Lovelace", "ada@example.com"));
    }
}
```

Media-type versioning uses `produces` on the mapping, and clients choose the version in `Accept`:

```java
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
class UserNegotiatedController {
    @GetMapping(produces = "application/vnd.example.v2+json")
    List<String> listV2() {
        return List.of("ada@example.com");
    }
}
```

A header strategy reads a custom header such as `API-Version` through `@RequestHeader`, which keeps the path stable but hides the version from a casual browser.

### When to use / pitfalls
- Version only on breaking changes. Adding an optional field is not a new version.
- Keep the old version running for a published deprecation period, and announce it with a `Deprecation` or `Sunset` response header.
- Path versions multiply controllers and tests; share the service layer and version only the web contract.
- Query-parameter versions are easy to forget and can fragment caches, so avoid them for public APIs.

**See also:** [REST Principles and Versioning](../../learning/21-api-design/rest-principles-versioning.md), [Building REST APIs](../../learning/09-spring-boot/rest-apis.md)

</details>

---

## 25. When and how do you use HTTP 202 Accepted for asynchronous work?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `202 Accepted` when the server has taken responsibility for a request but has not finished it, such as a report that takes minutes. The response should point the client at a status resource (through `Location`), and the client polls it until the job finishes. The 202 does not promise that the work will succeed.

### Explanation
The submitting endpoint returns 202 and the job id, and the status endpoint reports progress:

```java
import java.net.URI;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

record ReportRequest(String month) { }
record JobStatus(String id, String state, String resultUrl) { }

@RestController
@RequestMapping("/api/reports")
class ReportController {

    private final Map<String, JobStatus> jobs = new ConcurrentHashMap<>();

    @PostMapping
    ResponseEntity<JobStatus> submit(@RequestBody ReportRequest request) {
        String id = UUID.randomUUID().toString();
        JobStatus pending = new JobStatus(id, "RUNNING", null);
        jobs.put(id, pending);
        // hand the work to a queue or an @Async method here
        return ResponseEntity.accepted()
                .location(URI.create("/api/reports/" + id))
                .body(pending);
    }

    @GetMapping("/{id}")
    ResponseEntity<JobStatus> status(@PathVariable String id) {
        JobStatus job = jobs.get(id);
        if (job == null) {
            return ResponseEntity.notFound().build();
        }
        if ("RUNNING".equals(job.state())) {
            return ResponseEntity.status(HttpStatus.ACCEPTED).body(job);   // still working
        }
        return ResponseEntity.ok(job);                                    // finished
    }
}
```

The in-memory map is only for illustration. A real job store must survive restarts, and the worker must be idempotent, because a client that retries the POST may create a second job. An `Idempotency-Key` header is the usual fix.

Polling is not the only option. Webhooks call the client when the job finishes, and server-sent events or WebSockets push progress. Pick polling when clients are simple, and push when latency or request volume matters.

### When to use / pitfalls
- Do not return 202 for work that is already done; return 200 or 201.
- Always provide a way to query the outcome, or the client cannot tell success from failure.
- Include `Retry-After` when suggesting a polling interval.
- Failed jobs should report their error in the status resource rather than by silently disappearing.

**See also:** [Pagination, Errors, and Idempotency](../../learning/21-api-design/pagination-errors-idempotency.md), [Spring Async and Threading](../../learning/09-spring-boot/spring-async-and-threading.md)

</details>

---

## 26. What are the key differences between SOAP and REST?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
SOAP is a messaging protocol with an XML envelope, a formal contract (WSDL), and a family of WS-* standards for security and reliability. REST is an architectural style that models resources and uses HTTP methods, status codes, and caching. REST is lighter and more common for web and mobile APIs; SOAP remains in regulated or legacy enterprise integrations that depend on its contracts and WS-* features.

### Explanation
A SOAP call wraps the operation in an envelope. This example uses the SOAP 1.1 namespace:

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetUser xmlns="urn:example:users">
      <userId>123</userId>
    </GetUser>
  </soap:Body>
</soap:Envelope>
```

The REST equivalent names the resource and uses the method to express intent:

```http
GET /api/users/123 HTTP/1.1
Accept: application/json
```

The practical differences:

| Aspect | SOAP | REST |
|---|---|---|
| Unit of design | Operations on a service contract | Resources identified by URIs |
| Message format | XML envelope (verbose) | Usually JSON; any media type |
| HTTP use | Often POST for every operation | Methods and status codes carry meaning |
| Contract | WSDL, with code generation | OpenAPI is common but optional |
| Caching | Hard, because requests are POSTs | HTTP caches work on GET responses |
| Security | WS-Security, message-level signing | TLS and token-based schemes |
| Java tooling | Spring Web Services, JAX-WS | Spring MVC, WebFlux |

Neither is a faster protocol by default. The cost of SOAP is mostly the verbose XML and the extra tooling; REST's cost is that the contract is less formal unless you add OpenAPI.

### When to use / pitfalls
- Choose SOAP when a partner or a regulated process requires its contract or WS-* features.
- Choose REST for new public, mobile, or internal service APIs.
- Do not assume every RPC-style API is SOAP; gRPC and JSON-RPC are also operation-based.
- Remember that REST over HTTP does not make an API stateless or well designed by itself.

**See also:** [Alternative Protocols](../../learning/21-api-design/alternative-protocols.md), [REST Principles and Versioning](../../learning/21-api-design/rest-principles-versioning.md)

</details>

---

## 27. What is the difference between HTTP PUT and PATCH?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`PUT` replaces the entire resource with the representation in the body, so a field left out is removed or reset. `PATCH` applies a partial change, and the body describes only what should change. `PUT` is defined as idempotent. `PATCH` is not required to be idempotent, because its meaning depends on the patch format.

### Explanation
Suppose the stored user is `{"name": "Ada", "email": "ada@old.example", "role": "USER"}`. A `PUT` must send the whole resource:

```http
PUT /api/users/1
Content-Type: application/json

{"name": "Ada", "email": "ada@new.example", "role": "USER"}
```

A `PATCH` sends only the change:

```http
PATCH /api/users/1
Content-Type: application/json

{"email": "ada@new.example"}
```

A controller that supports both can keep the two semantics separate:

```java
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

record UserRecord(String name, String email, String role) { }

@RestController
@RequestMapping("/api/users")
class UserWriteController {

    @PutMapping("/{id}")
    ResponseEntity<UserRecord> replace(@PathVariable long id, @RequestBody UserRecord user) {
        if (user.name() == null || user.email() == null || user.role() == null) {
            return ResponseEntity.badRequest().build();   // a full replacement needs every field
        }
        return ResponseEntity.ok(user);
    }

    @PatchMapping("/{id}")
    ResponseEntity<Map<String, Object>> update(@PathVariable long id,
                                               @RequestBody Map<String, Object> changes) {
        // apply only the keys present in the request; reject keys the client may not change
        return ResponseEntity.ok(changes);
    }
}
```

The `Map` approach distinguishes "not sent" from "sent as null", which a plain record cannot. Standards exist for patch bodies: JSON Merge Patch (RFC 7396) is simple, and JSON Patch (RFC 6902) describes explicit operations.

### When to use / pitfalls
- Prefer `PATCH` for most updates, but use `PUT` when the client really owns the whole representation.
- Do not use a record DTO for `PATCH` if you must distinguish a missing field from `null`.
- A JSON Patch `add` to an array is not idempotent, so retries can duplicate items. Use an `Idempotency-Key` for those calls.
- Validate the result after applying a patch, not only the incoming fields.

**See also:** [REST Principles and Versioning](../../learning/21-api-design/rest-principles-versioning.md), [Pagination, Errors, and Idempotency](../../learning/21-api-design/pagination-errors-idempotency.md)

</details>

---

## Quick recap

- Use constructor injection for required dependencies, and keep singletons stateless.
- `@Transactional` rolls back on unchecked exceptions by default; use `rollbackFor` for checked ones, and watch out for self-invocation and swallowed exceptions.
- Scopes and lifecycle hooks decide when beans are created and cleaned up; scoped proxies bridge short-lived beans into singletons.
- Use `@Bean` for third-party or configured objects, and `@Component` for your own classes.
- Secure stateless APIs with a `SecurityFilterChain`, bearer tokens, BCrypt, and HTTPS; Spring Security 6 uses `requestMatchers`.
- Version on breaking changes, prefer URL versions for public APIs, return 202 with a status resource for long jobs, and use PATCH for partial updates.

**See also:** [Spring and Security Part 1](spring-and-security-part-1.md) | [Spring and Security Part 2](spring-and-security-part-2.md) | [Data and persistence](data-and-persistence-part-1.md)
