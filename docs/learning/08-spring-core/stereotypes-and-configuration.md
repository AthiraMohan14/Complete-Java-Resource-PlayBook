# Stereotypes and Configuration

Stereotype annotations mark classes as beans, and configuration classes declare beans explicitly with `@Bean`. Component scanning finds the annotated classes. Interviewers ask about this to check that you know which annotation to use, how scanning decides what to include, and what `@Configuration` does differently from a plain class.

## Core concepts

### Stereotype annotations

A stereotype annotation tells Spring that a class is a bean and what role it plays. All of them are meta-annotated with `@Component`, so component scanning finds them.

| Annotation | Role | Extra behaviour |
|---|---|---|
| `@Component` | Any managed component | None beyond registration |
| `@Service` | Business logic | Semantic marker; useful for AOP pointcuts |
| `@Repository` | Data access | Translates persistence exceptions into Spring's `DataAccessException` hierarchy |
| `@Controller` | Web request handling | Used by Spring MVC to find request-handling methods |

```java
import org.springframework.stereotype.Repository;
import org.springframework.stereotype.Service;

@Repository
class JdbcOrderRepository {
    // persistence code; exceptions are translated to DataAccessException
}

@Service
class OrderService {
    private final JdbcOrderRepository orders;

    OrderService(JdbcOrderRepository orders) {
        this.orders = orders;
    }
}
```

`@Repository` gets its exception translation from a post-processor that proxies the bean. This works for JDBC templates and JPA repositories alike. In Spring Boot, `@RestController` is `@Controller` plus `@ResponseBody`.

### Java configuration: @Configuration and @Bean

A `@Configuration` class declares beans with `@Bean` methods. The method's return value becomes a bean, and its name defaults to the method name.

```java
import java.time.Clock;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ClockConfig {

    @Bean
    public Clock clock() {
        return Clock.systemUTC();
    }
}
```

Use `@Bean` for classes you do not own (a third-party client, `Clock`, an `ObjectMapper`), since you cannot annotate them. Use stereotypes for your own classes.

### Full mode vs lite mode

By default (`proxyBeanMethods = true`), a `@Configuration` class is subclassed with CGLIB so that calling one `@Bean` method from another returns the same singleton instead of creating a new one.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DataConfig {

    @Bean
    public DataSourceHolder primary() {
        return new DataSourceHolder(dataSource());   // goes through the proxy: singleton
    }

    @Bean
    public DataSourceHolder reporting() {
        return new DataSourceHolder(dataSource());   // same dataSource instance
    }

    @Bean
    public Object dataSource() {
        return new Object();
    }
}

record DataSourceHolder(Object ds) { }
```

With `@Configuration(proxyBeanMethods = false)`, the class is "lite": calls between `@Bean` methods create new objects, but startup is faster. Use it when beans do not call each other.

A `@Bean` method on a plain class with no `@Configuration` (lite mode) still registers a bean, but inter-method calls are not intercepted.

### Component scanning

`@ComponentScan` tells Spring which packages to search for stereotype-annotated classes. Spring Boot's `@SpringBootApplication` includes `@ComponentScan` for the package of the main class and its subpackages.

```java
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.ComponentScan.Filter;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.FilterType;

@Configuration
@ComponentScan(
    basePackages = "com.example.orders",
    excludeFilters = @Filter(type = FilterType.REGEX, pattern = ".*Legacy.*"),
    includeFilters = @Filter(type = FilterType.ASSIGNABLE_TYPE, classes = PaymentGateway.class)
)
public class OrdersScanConfig {
}

interface PaymentGateway { }
```

Filter types include `ANNOTATION`, `ASSIGNABLE_TYPE`, `ASPECTJ`, `REGEX`, and `CUSTOM`. Exclusions are useful in tests; in production, prefer keeping the package structure simple so scanning needs no filters.

### Choosing where a bean comes from

| Situation | Use |
|---|---|
| Your own class with one implementation | `@Service`, `@Component`, or `@Repository` |
| Third-party class | `@Bean` in a `@Configuration` class |
| Conditional bean (depends on a property or class on the classpath) | `@Bean` plus `@ConditionalOnProperty` or `@Profile` |
| Several implementations of one interface | Stereotype or `@Bean` with `@Qualifier` or `@Primary` |

### Profiles and conditions

`@Profile("prod")` includes a bean only when that profile is active. Spring Boot's auto-configuration uses `@Conditional` annotations so that library beans appear only when needed. Use `@Profile` for environment differences; use properties for values.

## How it works / Step by step

During context startup:

1. The container scans the configured packages for stereotype-annotated classes and registers their definitions.
2. It processes `@Configuration` classes, creating their bean definitions from `@Bean` methods.
3. It applies `@Profile` and `@Conditional` filters, dropping definitions that do not apply.
4. It instantiates beans as described in [IoC and Beans](ioc-and-beans.md).

## Common pitfalls

- Placing the main class in a package above the code it needs, or below it, so components are not scanned.
- Using `@Component` on a class that has a second implementation without a qualifier, causing ambiguity.
- Calling a `@Bean` method directly on an object created with `new`, bypassing the container.
- Making a `@Configuration` class `final`, which prevents the CGLIB proxy.
- Putting heavy work in `@Bean` methods, which runs at startup for every bean.
- Scanning too broadly, which picks up test or legacy components unintentionally.

!!! tip "Interview tip"
    **Q: What is the difference between `@Component` and `@Bean`?**
    `@Component` goes on your own class; Spring finds it through scanning and creates it. `@Bean` goes on a method inside a configuration class and is how you register an object you did not write or need to construct yourself. Both produce singleton beans by default.

## Quick recap

- `@Service`, `@Repository`, and `@Controller` are specialised `@Component` annotations; `@Repository` also translates exceptions.
- `@Configuration` with `@Bean` methods declares beans explicitly; the default full mode returns singletons across inter-method calls.
- Component scanning finds stereotypes in the configured packages; filters include and exclude candidates.
- Use `@Profile` for environment-specific beans and `@Conditional` for auto-configuration.

**See also:** [IoC and Beans](ioc-and-beans.md), [Dependency Injection](dependency-injection.md), [AOP](aop.md)
