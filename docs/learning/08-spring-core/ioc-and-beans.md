# IoC Container and Beans

Inversion of Control (IoC) means the framework, not your code, creates objects and wires them together. In Spring, the IoC container (an `ApplicationContext`) manages beans: objects that Spring instantiates, configures, and destroys. Interviewers start here because every other Spring topic depends on how beans are defined, scoped, and given a lifecycle.

## Core concepts

### Inversion of Control

Without IoC, a class creates its own collaborators (`new PaymentClient()`), so it is hard to test and to change. With IoC, the class declares what it needs, and the container supplies it. Control over object creation moves from the class to the framework: that inversion is the principle.

```java
class PaymentClient {
    PaymentClient(String baseUrl) { }
}

// Without IoC: the class decides how its dependency is built
class OrderServiceWithoutIoc {
    private final PaymentClient payments = new PaymentClient("https://payments.example.com");
}

// With IoC: the container builds PaymentClient and passes it in
class OrderService {
    private final PaymentClient payments;

    public OrderService(PaymentClient payments) {
        this.payments = payments;
    }
}
```

### ApplicationContext types

`ApplicationContext` is the container interface. It extends `BeanFactory` and adds events, message resources, and environment support. Common implementations:

| Implementation | Reads configuration from | Typical use |
|---|---|---|
| `AnnotationConfigApplicationContext` | Java `@Configuration` classes | Plain Spring applications and tests |
| `ClassPathXmlApplicationContext` | XML files on the classpath | Legacy applications |
| `AnnotationConfigWebApplicationContext` | Java configuration in a web app | Non-Boot web applications |
| `GenericApplicationContext` | Programmatic registration | Advanced setups |

Spring Boot creates the context for you, so you rarely construct one. Plain Spring code looks like this:

```java
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

public class Main {
    public static void main(String[] args) {
        try (AnnotationConfigApplicationContext ctx =
                 new AnnotationConfigApplicationContext(AppConfig.class)) {
            OrderService orders = ctx.getBean(OrderService.class);
            System.out.println(orders != null);
        }   // close() destroys singleton beans and runs their destroy callbacks
    }
}
```

`AppConfig` is a `@Configuration` class, covered in [Stereotypes and Configuration](stereotypes-and-configuration.md). Closing the context matters: it is what triggers `@PreDestroy` and destroy methods.

### Configuration styles

- **Java configuration:** `@Configuration` classes with `@Bean` methods. Type-safe and refactor-friendly. The modern default.
- **Annotation-based:** `@Component` and friends on classes, found by component scanning.
- **XML:** `<bean>` elements. Still supported but rarely written today.

The three styles can be mixed. Choose one primary style per project so readers know where beans come from.

### Bean definitions and scopes

A bean definition records the class, constructor arguments, properties, scope, and lifecycle callbacks. The scope controls how many instances exist:

| Scope | Instances | Available in |
|---|---|---|
| `singleton` (default) | One per container | Every context |
| `prototype` | A new instance each time it is requested | Every context |
| `request` | One per HTTP request | Web-aware contexts |
| `session` | One per HTTP session | Web-aware contexts |
| `application` | One per `ServletContext` | Web-aware contexts |
| `websocket` | One per WebSocket session | WebSocket-aware contexts |

```java
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

@Component
@Scope("prototype")
public class ReportBuilder {
    // a fresh instance is created every time one is requested or injected
}
```

Two notes on scopes:

- A singleton that depends on a prototype gets one prototype instance, forever, because the singleton is created once. Use `ObjectProvider<ReportBuilder>` or a scoped proxy when you need a fresh instance per call.
- Singletons are shared across threads, so they must be stateless or thread-safe. A request-scoped bean is per request, so it does not have this problem.

### Bean lifecycle

Spring performs these steps for each bean:

1. **Instantiation:** the constructor runs (or a factory method).
2. **Dependency injection:** properties and collaborators are set.
3. **Aware callbacks:** beans that implement `BeanNameAware`, `ApplicationContextAware`, and similar receive container information.
4. **Initialisation:** `@PostConstruct`, then `InitializingBean.afterPropertiesSet()`, then a custom `init-method`. Bean post-processors can wrap the bean at this point (this is how proxies such as `@Transactional` are added).
5. **Use:** the bean serves requests.
6. **Destruction:** on context close, `@PreDestroy`, then `DisposableBean.destroy()`, then a custom `destroy-method`. Only singleton destruction callbacks run; the container does not manage the lifecycle of prototype beans after creating them.

```java
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Component;

@Component
public class CatalogCache {

    @PostConstruct
    void load() {
        System.out.println("Loading catalogue");       // runs after injection
    }

    @PreDestroy
    void flush() {
        System.out.println("Flushing catalogue");      // runs on context close
    }
}
```

`@PostConstruct` is in the `jakarta.annotation` package in Spring Boot 3. Older code imports `javax.annotation`.

### Lazy initialisation

`@Lazy` (or `spring.main.lazy-initialization=true` in Boot) delays creating a singleton until first use. It speeds up startup and can hide configuration errors until runtime, so use it on purpose.

## How it works / Step by step

When the context starts:

1. Spring reads bean definitions from configuration classes, XML, or scanned annotations.
2. Bean factory post-processors can change the definitions (for example, resolving `@Value` placeholders).
3. For each singleton (unless lazy), Spring creates the bean, injects dependencies (creating them first if needed), runs the lifecycle callbacks, and registers it.
4. The context publishes a refresh event; Spring Boot then runs `ApplicationRunner` and `CommandLineRunner` beans.

## Common pitfalls

- Creating collaborators with `new` inside a managed bean, which bypasses injection, AOP, and transactions.
- Storing mutable state in a singleton bean and sharing it across threads.
- Injecting a prototype into a singleton and expecting new instances each time.
- Expecting `@PreDestroy` to run on a prototype bean.
- Relying on lazy initialisation to find configuration errors; they surface later.
- Mixing configuration styles without a clear reason.

!!! tip "Interview tip"
    **Q: What is the difference between a singleton bean and a singleton pattern class?**
    A Spring singleton is one instance per container, not one per JVM. Multiple `ApplicationContext` instances in the same JVM each have their own singleton. The container manages its lifecycle and injects it; a classic singleton uses a static instance and controls its own creation. Mention that testing with several contexts gives you separate instances.

## Quick recap

- IoC moves object creation and wiring from your classes to the container.
- Singleton is the default scope; prototype creates a new instance per request.
- Lifecycle: instantiate, inject, aware callbacks, initialise, use, destroy.
- `@PostConstruct` and `@PreDestroy` run at initialisation and destruction.
- Closing the context runs destroy callbacks for singletons.

**See also:** [Dependency Injection](dependency-injection.md), [Stereotypes and Configuration](stereotypes-and-configuration.md), [Index](index.md)
