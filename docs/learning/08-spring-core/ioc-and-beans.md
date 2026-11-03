# IoC Container and Beans

!!! note "In simple words"
    Your class usually builds the objects it needs. With Spring, the container builds them, connects them together, and decides how long they live. Each object the container manages is called a bean.

## Why it matters

Inversion of Control (IoC) moves the job of creating objects from your code to the framework. Almost every other Spring topic depends on it: injection, transactions, AOP, and web handling all work on beans. If you understand how a bean is defined, how many copies exist, and when its setup and cleanup run, you can reason about real bugs, such as a singleton that keeps request data, or a cleanup method that never runs.

## How it works

When a Spring context starts, the container follows a fixed sequence. The Spring snippets on this page show the shape of the code; they are not compiled as part of this page. The plain Java snippets are written for Java 21.

1. The container reads bean definitions from `@Configuration` classes, from XML files, or from classes found by component scanning.
2. Bean factory post-processors adjust those definitions before any bean is created. A common example is resolving `@Value` placeholders.
3. For each singleton that is not lazy, the container creates the bean, creates and injects its dependencies first, runs the lifecycle callbacks, and stores the bean.
4. When startup finishes, the context publishes a refresh event. Spring Boot then runs any `ApplicationRunner` and `CommandLineRunner` beans.

```mermaid
flowchart LR
    A[Read bean definitions] --> B[Post processors adjust definitions]
    B --> C[Create singleton beans]
    C --> D[Inject dependencies]
    D --> E[Run lifecycle callbacks]
    E --> F[Context ready]
```

### Inversion of control

Without IoC, a class decides how its collaborators are built. That makes the class hard to test, because you cannot easily replace a collaborator with a fake. With IoC, the class declares what it needs in its constructor, and the container supplies it. Control over creation has moved from the class to the framework. That shift is the principle.

```java
class PaymentClient {
    private final String baseUrl;

    PaymentClient(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}

// Without IoC: the class builds its own dependency
class OrderServiceWithoutIoc {
    private final PaymentClient payments = new PaymentClient("https://payments.example.com");
}

// With IoC: the dependency arrives through the constructor
class OrderService {
    private final PaymentClient payments;

    OrderService(PaymentClient payments) {
        this.payments = payments;
    }
}
```

### ApplicationContext types

`ApplicationContext` is the container interface. It extends `BeanFactory` and adds event publishing, message resources, and environment support. Spring Boot creates the context for you, so you seldom build one yourself.

| Implementation | Reads configuration from | Typical use |
|---|---|---|
| `AnnotationConfigApplicationContext` | Java `@Configuration` classes | Plain Spring applications and tests |
| `ClassPathXmlApplicationContext` | XML files on the classpath | Legacy applications |
| `AnnotationConfigWebApplicationContext` | Java configuration in a web app | Non-Boot web applications |
| `GenericApplicationContext` | Programmatic registration | Advanced setups |

A plain Spring program (Spring API, not compiled here) looks like this:

```java
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

public class Main {
    public static void main(String[] args) {
        try (var ctx = new AnnotationConfigApplicationContext(AppConfig.class)) {
            OrderService orders = ctx.getBean(OrderService.class);
            System.out.println(orders != null);
        }   // close() destroys singleton beans and runs their destroy callbacks
    }
}
```

`AppConfig` is a `@Configuration` class, covered in [Stereotypes and Configuration](stereotypes-and-configuration.md). Closing the context matters: it is what triggers `@PreDestroy` and custom destroy methods.

### Configuration styles

- **Java configuration:** `@Configuration` classes with `@Bean` methods. Type-safe and easy to refactor. This is the modern default.
- **Annotation-based:** `@Component` and its relatives on classes, found by component scanning.
- **XML:** `<bean>` elements. Still supported, but rarely written for new code.

The three styles can be mixed. Pick one primary style per project so readers know where beans come from.

### Bean definitions and scopes

A bean definition records the class, constructor arguments, properties, scope, and lifecycle callbacks. The scope decides how many instances exist.

| Scope | Instances | Available in |
|---|---|---|
| `singleton` (default) | One per container | Every context |
| `prototype` | A new instance each time one is requested | Every context |
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

Two points to remember:

- A singleton that depends on a prototype keeps the one prototype it received. It never gets a new one. Use `ObjectProvider<ReportBuilder>` when you need a fresh instance per call.
- Singletons are shared across threads, so they must be stateless or thread-safe. A request-scoped bean is created per request, so this concern does not apply to it.

```java
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Service;

@Service
class ReportRunner {

    private final ObjectProvider<ReportBuilder> builders;

    ReportRunner(ObjectProvider<ReportBuilder> builders) {
        this.builders = builders;
    }

    void runOnce() {
        ReportBuilder builder = builders.getObject();   // a new prototype on every call
    }
}
```

### Bean lifecycle

Spring performs these steps for each bean:

1. **Instantiation:** the constructor (or a factory method) runs.
2. **Dependency injection:** properties and collaborators are set.
3. **Aware callbacks:** beans implementing `BeanNameAware`, `ApplicationContextAware`, and similar interfaces receive container information.
4. **Initialisation:** `@PostConstruct` runs first, then `InitializingBean.afterPropertiesSet()`, then any custom `init-method`. Bean post-processors can wrap the bean here. This is how proxies for `@Transactional` and `@Async` are added.
5. **Use:** the bean serves requests.
6. **Destruction:** when the context closes, `@PreDestroy` runs, then `DisposableBean.destroy()`, then any custom `destroy-method`. Only singletons get destruction callbacks. The container does not call destroy methods on prototypes after handing them out.

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
        System.out.println("Flushing catalogue");      // runs when the context closes
    }
}
```

In Spring Boot 3, `@PostConstruct` and `@PreDestroy` come from the `jakarta.annotation` package. Older code uses `javax.annotation`.

### Lazy initialisation

`@Lazy` on a bean, or `spring.main.lazy-initialization=true` in Boot, delays creating a singleton until something first uses it. Startup gets faster, but a broken bean can stay hidden until a user hits it. Use laziness deliberately.

## Where it is used

- **Every Spring application:** controllers, services, repositories, and clients are all beans.
- **Tests:** a test context loads only the beans it needs, and you can replace a bean with a fake.
- **Plain Spring programs:** `AnnotationConfigApplicationContext` builds the container directly.
- **Legacy applications:** XML configuration is still found in older codebases.

## Benefits

- Classes depend on constructor parameters and interfaces, so implementations are easy to swap.
- One container controls object lifetime, scope, and shared state.
- Lifecycle callbacks give a clear place for setup and cleanup.
- Eager singletons surface missing dependencies at startup, not in the middle of a request.

## Cons and limits

- Wiring is partly hidden. Reading a class does not show where its collaborators come from.
- Eager creation adds startup time. Lazy creation moves configuration errors to runtime.
- Shared singletons need care with mutable state.
- Objects created with `new` are outside the container. They get no injection, proxies, or lifecycle callbacks.

## Best practices

- Use one primary configuration style per project.
- Keep singletons stateless. Keep per-request data in method parameters or in request-scoped beans.
- Put setup in `@PostConstruct` and cleanup in `@PreDestroy`. In tests, close the context when you finish.
- Let the container create collaborators instead of calling `new` on them.
- Use `@Lazy` on rarely used beans, not as a way to hide wiring problems.

!!! tip "Interview tip"
    **Q: What is the difference between a singleton bean and a singleton pattern class?**
    A Spring singleton means one instance per container, not one per JVM. Two `ApplicationContext` objects in the same JVM each get their own singleton. The container creates it, manages it, and injects it. A classic singleton is a class that holds a static instance and controls its own creation. In tests, starting several contexts gives you several separate instances.

## Quick recap

- IoC moves object creation and wiring from your classes to the container.
- Singleton is the default scope. Prototype creates a new instance per request.
- Lifecycle order: instantiate, inject, aware callbacks, initialise, use, destroy.
- `@PostConstruct` and `@PreDestroy` run during initialisation and destruction.
- Closing the context runs destroy callbacks for singletons.

## Official documentation

- [Spring Framework reference](https://docs.spring.io/spring-framework/reference/)
- [Spring Boot reference](https://docs.spring.io/spring-boot/reference/index.html)

**See also:** [Dependency Injection](dependency-injection.md), [Stereotypes and Configuration](stereotypes-and-configuration.md), [Index](index.md)
