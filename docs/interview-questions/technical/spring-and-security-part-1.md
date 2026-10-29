# Spring, Spring Boot, and Security Questions (Part 1 of 2)

Questions on the Spring container, dependency injection, transactions, Spring Boot auto-configuration, and application security. The examples target Spring Boot 3 and Spring Security 6, which use the `jakarta.*` namespace.

---


This page is split into 2 parts. Continue to [Part 2](spring-and-security-part-2.md).

## 1. What are inversion of control and dependency injection?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Inversion of control means the framework creates objects and controls their lifecycle, instead of your code calling `new`. Dependency injection is the mechanism: the container supplies the collaborators a class needs, usually through its constructor. The result is code that is easier to test, because you can pass in fakes.

### Explanation
```java
import org.springframework.stereotype.Service;

interface PaymentGateway {
    void charge(String orderId, long cents);
}

@Service
class CheckoutService {
    private final PaymentGateway gateway;

    CheckoutService(PaymentGateway gateway) {   // one constructor: Spring injects it
        this.gateway = gateway;
    }

    void checkout(String orderId, long cents) {
        gateway.charge(orderId, cents);
    }
}
```

In a unit test you call `new CheckoutService(fakeGateway)` without starting Spring at all.

### When to use / pitfalls
- Prefer constructor injection. It makes dependencies explicit and allows `final` fields.
- Avoid service locator calls such as `applicationContext.getBean(...)` in business code.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 2. Which bean scopes exist, and is a singleton bean thread-safe?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The default scope is `singleton`: one instance per container. `prototype` creates a new instance each time it is requested. `request`, `session`, `application`, and `websocket` are web-aware scopes. A singleton is not automatically thread-safe; it is shared by every request, so any mutable field is a shared state problem.

### Explanation
```java
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;
import java.util.concurrent.atomic.AtomicInteger;

@Component                                   // singleton by default
class VisitCounter {
    private final AtomicInteger visits = new AtomicInteger();   // safe shared state

    int hit() {
        return visits.incrementAndGet();
    }
}

@Component
@Scope("prototype")                          // new instance every time it is injected
class ReportBuilder {
    private final StringBuilder buffer = new StringBuilder();   // per-use state
}
```

A `prototype` bean is not destroyed by the container; the caller is responsible for cleanup.

### When to use / pitfalls
- Do not store request data in a singleton's fields. Pass it as method parameters.
- Injecting a `prototype` bean into a singleton gives you one instance only, unless you use `ObjectProvider` or a scoped proxy.

**See also:** [Core Java](core-java-part-1.md), [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 3. What is the bean lifecycle, and how do initialisation and destruction callbacks work?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The container instantiates the bean, injects its dependencies, runs initialisation callbacks (`@PostConstruct`, then `InitializingBean.afterPropertiesSet()`, then any custom `initMethod`), and uses the bean. On shutdown it runs `@PreDestroy` and then `DisposableBean.destroy()` for singletons.

### Explanation
```java
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Component;

@Component
class CacheWarmer {
    @PostConstruct
    void warm() {
        System.out.println("warming cache after dependencies are injected");
    }

    @PreDestroy
    void flush() {
        System.out.println("flushing before shutdown");
    }
}
```

`@PostConstruct` is part of Jakarta annotations, which are in the `jakarta.annotation` package in Spring Boot 3.

### When to use / pitfalls
- Do not call other beans from a constructor, because they may not be fully set up yet. Use `@PostConstruct` for that work.
- Long-running work in `@PostConstruct` delays application startup.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 4. What is the difference between `@Component`, `@Service`, `@Repository`, and `@Controller`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
All four are stereotypes that tell component scanning to register the class as a bean. `@Service` and `@Controller` add no extra behaviour; they document intent. `@Repository` also marks the persistence layer, and Spring translates its database exceptions into the `DataAccessException` hierarchy. `@Controller` (and `@RestController`) makes the class handle web requests.

### Explanation
```java
import org.springframework.stereotype.Repository;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@Repository
class OrderRepository {
    // database access goes here
}

@Service
class OrderService {
    private final OrderRepository repository;

    OrderService(OrderRepository repository) {
        this.repository = repository;
    }
}

@RestController
class OrderController {
    private final OrderService service;

    OrderController(OrderService service) {
        this.service = service;
    }

    @GetMapping("/orders/ping")
    String ping() {
        return "ok";
    }
}
```

### When to use / pitfalls
- Put business rules in the service layer, not in the controller or the repository.
- A `@Repository` only gets exception translation when a `PersistenceExceptionTranslationPostProcessor` is active, which Spring Boot configures for you.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 5. What is a circular dependency, and how do you fix it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A circular dependency happens when bean A needs B and B needs A. Constructor injection cannot resolve it, and Spring Boot 2.6 and later refuses it by default. The fix is to redesign: extract the shared behaviour into a third class, or use an event to decouple the two.

### Explanation
```java
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;

record OrderPlaced(String orderId) {}

@Service
class OrderService {
    private final ApplicationEventPublisher events;

    OrderService(ApplicationEventPublisher events) {   // no reference to NotificationService
        this.events = events;
    }

    void place(String orderId) {
        events.publishEvent(new OrderPlaced(orderId));
    }
}
```

`NotificationService` listens with `@EventListener` for `OrderPlaced`, so the dependency points one way only.

### When to use / pitfalls
- Switching from constructor to setter or field injection does not remove the cycle; the design problem remains.
- `spring.main.allow-circular-references=true` is a last resort that hides a design problem.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 6. How do `@Qualifier` and `@Primary` resolve multiple candidates?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
When two beans implement the same interface, injection by type is ambiguous. `@Primary` marks one bean as the default choice. `@Qualifier` names the bean to inject at a specific injection point, and overrides `@Primary`.

### Explanation
```java
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

interface Notifier {
    void send(String text);
}

@Component
@Primary
class EmailNotifier implements Notifier {
    public void send(String text) { System.out.println("email: " + text); }
}

@Component("smsNotifier")
class SmsNotifier implements Notifier {
    public void send(String text) { System.out.println("sms: " + text); }
}

@Service
class AlertService {
    private final Notifier primary;
    private final Notifier sms;

    AlertService(Notifier primary, @Qualifier("smsNotifier") Notifier sms) {
        this.primary = primary;   // gets EmailNotifier because it is @Primary
        this.sms = sms;           // explicitly named
    }
}
```

### When to use / pitfalls
- Injecting a `List<Notifier>` or `Map<String, Notifier>` gives you all implementations, which is useful for strategy-style code.
- Bean names come from the class name unless you set them explicitly; renaming a class can break `@Qualifier` strings.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 7. How does Spring AOP work, and why does self-invocation bypass it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Spring AOP creates a proxy around the bean (a JDK dynamic proxy for interfaces, or a CGLIB subclass otherwise). Advice such as `@Transactional` or `@Cacheable` runs in the proxy before or after your method. A call from one method of the bean to another method of the same bean goes directly to `this`, skipping the proxy, so the advice does not run.

### Explanation
```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class ReportService {

    public void generate() {
        saveDraft();          // this.saveDraft(): no proxy, so no transaction here
    }

    @Transactional(propagation = org.springframework.transaction.annotation.Propagation.REQUIRES_NEW)
    public void saveDraft() {
        // runs in a new transaction only when called through the proxy
    }
}
```

Fix it by moving `saveDraft` into another bean and injecting that bean, or by restructuring so the outer method is the transactional entry point.

### When to use / pitfalls
- Proxy-based AOP only intercepts `public` methods on the proxy by default; private and package-private methods are not advised.
- `final` classes and methods cannot be proxied by CGLIB.
- Aspects are a good home for cross-cutting concerns such as logging, timing, and auditing.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 8. How does `@Transactional` work, including propagation and rollback rules?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@Transactional` begins a transaction before the method runs and commits it afterwards, or rolls it back if an exception escapes. The default propagation is `REQUIRED`: join an existing transaction or start one. By default, the transaction rolls back for unchecked exceptions (`RuntimeException` and `Error`) but not for checked exceptions, unless you set `rollbackFor`.

### Explanation
```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class TransferService {

    @Transactional(rollbackFor = Exception.class)   // roll back on checked exceptions too
    public void transfer(long fromId, long toId, long cents) throws Exception {
        debit(fromId, cents);
        credit(toId, cents);                       // if this fails, debit is rolled back
    }

    private void debit(long id, long cents) { /* SQL update */ }
    private void credit(long id, long cents) { /* SQL update */ }
}
```

Common propagation values: `REQUIRED` (default), `REQUIRES_NEW` (always a new transaction, suspending the outer one), `NESTED` (a savepoint inside the outer transaction, needs JDBC savepoint support), `SUPPORTS`, `MANDATORY`, `NEVER`, and `NOT_SUPPORTED`.

### When to use / pitfalls
- Self-invocation skips the proxy (see question 7).
- Only `public` methods are transactional with the default proxy setup.
- Mark read-only queries with `@Transactional(readOnly = true)`. It is a hint to the driver and the ORM, not a guarantee.
- Keep transactions short. Do not call slow remote services while holding a database transaction open.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 9. How does Spring Boot auto-configuration work?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@SpringBootApplication` combines `@Configuration`, `@EnableAutoConfiguration`, and `@ComponentScan`. Auto-configuration classes are listed in the `AutoConfiguration.imports` file on the classpath. Each one is guarded by conditions such as `@ConditionalOnClass` and `@ConditionalOnMissingBean`, so Boot configures a feature only when its library is present and you have not defined your own bean.

### Explanation
```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@SpringBootApplication
public class ShopApplication {
    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }
}

@Configuration
class ClockConfig {
    @Bean
    @ConditionalOnMissingBean          // used only if no other Clock bean is defined
    java.time.Clock clock() {
        return java.time.Clock.systemUTC();
    }
}
```

Run with `--debug` or set `debug=true` to print the condition evaluation report and see which auto-configurations matched.

### When to use / pitfalls
- Exclude an auto-configuration you do not want with `@SpringBootApplication(exclude = ...)` or `spring.autoconfigure.exclude`.
- Your own `@Bean` definitions usually replace the auto-configured ones. Check the report when a bean behaves unexpectedly.
- Boot 3 requires Java 17 or later.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 10. How do `@ConfigurationProperties`, `@Value`, and profiles differ?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@Value` injects one property into one field or parameter. `@ConfigurationProperties` binds a whole group of properties to a type, with validation and relaxed naming. Profiles let you activate a set of configuration (`application-prod.yml`, a `@Profile` bean) per environment.

### Explanation
```java
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;

@ConfigurationProperties(prefix = "payments")   // binds payments.* from application.yml
record PaymentProperties(String apiUrl, int timeoutSeconds) {}

@Component
class Greeter {
    private final String greeting;

    Greeter(@Value("${app.greeting:Hello}") String greeting) {   // default if missing
        this.greeting = greeting;
    }

    String greet(String name) {
        return greeting + ", " + name;
    }
}
```

Records as `@ConfigurationProperties` types need `@EnableConfigurationProperties(PaymentProperties.class)` or `@ConfigurationPropertiesScan`.

### When to use / pitfalls
- Prefer `@ConfigurationProperties` for groups of settings; it is easier to test and validate.
- Never commit secrets to `application.yml`. Use environment variables or a secrets manager.
- Profile-specific beans with `@Profile("prod")` can hide differences between environments; keep them small.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---


**Next:** [Part 2](spring-and-security-part-2.md)
