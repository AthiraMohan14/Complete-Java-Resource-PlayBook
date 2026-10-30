# Spring Boot Basics and Configuration

Spring Boot removes most of the setup that a Spring application once needed: you get a running web server, sensible defaults, and configuration read from files and the environment. Interviewers ask about this because the "magic" of auto-configuration is easy to use without understanding, and that gap shows up quickly in debugging and design questions.

## Spring versus Spring Boot

Spring Boot is not a replacement for Spring. It is a layer built on the Spring Framework that makes the usual choices for you. The table below shows what changes between the two.

| Topic | Spring Framework | Spring Boot |
|---|---|---|
| What it gives you | Dependency injection, AOP, MVC, data access, and transaction support | The same features, preconfigured for common cases |
| Wiring | You declare beans and infrastructure yourself, in Java or XML | Auto-configuration creates default beans based on the classpath |
| Web server | You deploy a WAR to an external servlet container | An embedded Tomcat, Jetty, or Undertow runs inside an executable JAR |
| Library versions | You choose compatible versions of each library | Starters and the parent POM or BOM align the versions |
| Configuration | Explicit beans, plus property files you load yourself | Standard `application` files, profiles, and typed properties |
| Operations | Health checks and metrics are your job to build | Actuator endpoints are available once you expose them |
| Testing | You assemble the context for each test | `@SpringBootTest` and test slices load only what a test needs |
| Boilerplate | More setup code and descriptors | Much less, because defaults cover the common path |

The short answer for an interview: Spring provides the building blocks, and Boot chooses sensible defaults for them and gets out of the way when you define your own.

## Core concepts

### @SpringBootApplication

`@SpringBootApplication` is a convenience annotation. It combines `@Configuration` (the class can declare beans), `@EnableAutoConfiguration` (turn on auto-configuration), and `@ComponentScan` (find components in this package and below).

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}
```

Place this class in the root package of your application. Component scanning starts from its package, so classes placed outside it are not picked up unless you configure scanning explicitly.

### How auto-configuration decides

Auto-configuration classes are listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` in each starter jar (this file replaced the older `spring.factories` entry for these classes in Spring Boot 2.7 and later). Each candidate is guarded by conditions:

- `@ConditionalOnClass`: the library is on the classpath
- `@ConditionalOnMissingBean`: you have not defined your own bean of that type
- `@ConditionalOnProperty`: a property is set to a given value

Because of `@ConditionalOnMissingBean`, a bean you define always wins over the default. This is the usual way to override Boot's behaviour.

```java
import javax.sql.DataSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class DataSourceOverride {
    // Boot's DataSource auto-configuration backs off when this bean exists.
    @Bean
    DataSource dataSource() {
        // return a custom, pre-configured DataSource here
        throw new UnsupportedOperationException("sketch only");
    }
}
```

### Embedded servers

`spring-boot-starter-web` brings in Tomcat as the default embedded servlet container, so the application runs as a plain `java -jar`. To switch servers, exclude the Tomcat starter and add another (for example, Jetty). Undertow has been supported in older Boot lines; check the support matrix for your Boot version before choosing it, because server support changes between releases.

### Profiles and environment abstraction

Profiles group configuration and beans per environment. Activate them with `spring.profiles.active` (or `SPRING_PROFILES_ACTIVE`). Profile-specific files such as `application-prod.yml` override the base file.

```java
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("dev")
class FakePaymentGateway implements PaymentGateway {
    @Override
    public boolean charge(String customerId, int amountCents) {
        return true; // never call a real provider in dev
    }
}

interface PaymentGateway {
    boolean charge(String customerId, int amountCents);
}
```

### Configuration binding

`@Value` injects a single value. `@ConfigurationProperties` binds a whole group of keys to a type, which is safer and easier to test. Records work well for this in Spring Boot 3.

```java
import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.payment")
public record PaymentProperties(String url, Duration timeout) {}
```

Register the class with `@ConfigurationPropertiesScan` on the application class, or with `@EnableConfigurationProperties(PaymentProperties.class)`.

```yaml
app:
  payment:
    url: https://payments.example.com
    timeout: 3s
```

Spring Boot uses relaxed binding: the environment variable `APP_PAYMENT_URL` maps to `app.payment.url`. Keep secrets out of files; see [Secrets Management](../10-security/secrets-management.md).

### Starters and packaging

A starter is a curated set of dependencies for one purpose (for example, `spring-boot-starter-data-jpa`). Starters carry no code of their own; they pull in the libraries and the auto-configuration that uses them. Because the versions are managed by Boot's parent POM or BOM, you leave the version off the starter.

| Starter | Use it for | Brings in (main parts) |
|---|---|---|
| `spring-boot-starter-web` | REST APIs and MVC applications | Spring MVC, embedded Tomcat, Jackson |
| `spring-boot-starter-webflux` | Non-blocking web applications | Spring WebFlux, Reactor, embedded Netty |
| `spring-boot-starter-data-jpa` | Relational persistence with entities | Spring Data JPA, Hibernate, HikariCP |
| `spring-boot-starter-jdbc` | Plain JDBC with `JdbcTemplate` | Spring JDBC, HikariCP |
| `spring-boot-starter-data-r2dbc` | Reactive relational access | Spring Data R2DBC (add your database driver) |
| `spring-boot-starter-data-mongodb` | Document storage with MongoDB | Spring Data MongoDB |
| `spring-boot-starter-data-redis` | Redis as a cache or data store | Spring Data Redis, Lettuce client |
| `spring-boot-starter-security` | Authentication and authorisation | Spring Security |
| `spring-boot-starter-oauth2-resource-server` | Accepting bearer tokens such as JWTs | Spring Security resource-server support |
| `spring-boot-starter-validation` | Bean validation on requests and entities | Jakarta Bean Validation, Hibernate Validator |
| `spring-boot-starter-actuator` | Health, metrics, and operational endpoints | Actuator and Micrometer |
| `spring-boot-starter-cache` | The cache abstraction | Spring Cache; you add a provider such as Caffeine |
| `spring-boot-starter-amqp` | Messaging with RabbitMQ | Spring AMQP |
| `spring-boot-starter-aop` | Cross-cutting behaviour, such as timing around service methods | Spring AOP and AspectJ weaver |
| `spring-boot-starter-test` | Tests | JUnit 5, AssertJ, Mockito, Spring Test |

Your database driver is usually not in a starter. Add it yourself, for example the MySQL or PostgreSQL JDBC driver, and check its version against the Boot release.

Packaging with the Spring Boot Maven or Gradle plugin produces an executable "fat" JAR that contains the application, its dependencies, and an embedded server. Layered JARs let container builds reuse unchanged dependency layers.

### Startup and shutdown hooks

Boot publishes events as the application starts. A listener for `ApplicationReadyEvent` runs after the context is fully refreshed and the server is accepting requests, which makes it the right place for work that needs the whole application, such as warming a cache. Work that a bean needs before anything else uses a `@PostConstruct` method, which runs during bean creation.

```java
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
class CatalogWarmup {

    @EventListener(ApplicationReadyEvent.class)
    void warm() {
        // load reference data once the application can serve requests
    }
}
```

For cleanup, a `@PreDestroy` method runs when the context closes, which happens on SIGTERM and on a normal shutdown. Keep it short and bounded, because the container may stop it after a grace period.

```java
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Component;

@Component
class ConnectionReleaser {

    @PreDestroy
    void release() {
        // flush buffers and close outbound connections
    }
}
```

## How it works / Step by step

1. `SpringApplication.run` creates the application context and reads the environment (command line, environment variables, property files, profiles).
2. Component scanning registers your beans.
3. Auto-configuration classes are evaluated against the conditions above and register default beans where allowed.
4. The embedded server starts, and the application is ready.

| Source (highest priority first) | Example |
|---|---|
| Command-line arguments | `--server.port=9090` |
| `SPRING_APPLICATION_JSON` (inline JSON in an environment variable) | `{"server.port":9090}` |
| Java system properties | `-Dserver.port=9090` |
| OS environment variables | `SERVER_PORT=9090` |
| Profile-specific file | `application-prod.yml` |
| Default file | `application.yml` |
| `@PropertySource` on a configuration class | `@PropertySource("classpath:extra.properties")` |
| Built-in defaults (`SpringApplication` and the framework) | `server.port` defaults to 8080 |

Higher sources override lower ones for the same key. The exact list is in the Spring Boot reference documentation for your version; the order above is the one interviewers expect you to know.

Note that a profile-specific file beats the default file, but an environment variable beats both. This is why a secret injected by the platform wins over anything committed to the repository.

## @EntityScan and entity discovery

Spring Boot's JPA auto-configuration looks for `@Entity` classes in the packages registered by `@SpringBootApplication`: the application class's package and its subpackages. Entities outside that tree are not known to Hibernate until you tell it where to look.

- `@EntityScan(basePackages = "...")` or `basePackageClasses` extends the entity search to other packages.
- It affects only entities. Spring beans still come from component scanning, and repositories still come from `@EnableJpaRepositories`.
- Repositories outside the default package need `@EnableJpaRepositories` as well.
- A missing entity usually surfaces at first use as a "Not a managed type" error.

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication
@EntityScan(basePackages = "com.example.billing.model")
@EnableJpaRepositories(basePackages = "com.example.billing.repository")
public class ShopApplication {
    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }
}
```

## Common pitfalls

- Putting `@SpringBootApplication` in a sub-package, so most beans are never scanned.
- Excluding an auto-configuration without understanding what it provides, which causes confusing missing-bean errors.
- Hard-coding environment-specific values instead of using profiles or environment variables.
- Using `@Value` with many keys across classes, which scatters configuration. Prefer a typed properties class.
- Printing a configuration record with its default `toString`, which exposes secrets (see the override in the secrets page).
- Relying on `spring.factories` for new auto-configuration; use the `AutoConfiguration.imports` file in Boot 2.7 and later.

!!! tip "Interview tip"
    **Q: What happens when you add a library to the classpath?**
    Its auto-configuration becomes eligible. It only activates if the required classes are present, and it backs off if you define a bean of the same type. So the default is "use what is on the classpath, unless you say otherwise".

## Quick recap

- `@SpringBootApplication` = `@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan`.
- Auto-configuration is conditional, and user-defined beans take precedence.
- Profiles and property sources (with a defined precedence) drive environment-specific configuration.
- `@ConfigurationProperties` gives typed, testable configuration.
- Starters bundle dependencies; the fat JAR bundles the server and the app.

**See also:** [Spring Core](../08-spring-core/index.md) | [Building REST APIs](rest-apis.md) | [HTTP Clients and Testing](http-clients-and-testing.md)
