# Spring Boot Basics and Configuration

Spring Boot removes most of the setup that a Spring application once needed: you get a running web server, sensible defaults, and configuration read from files and the environment. Interviewers ask about this because the "magic" of auto-configuration is easy to use without understanding, and that gap shows up quickly in debugging and design questions.

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

A starter is a curated set of dependencies for one purpose (for example, `spring-boot-starter-data-jpa`). Packaging with the Spring Boot Maven or Gradle plugin produces an executable "fat" JAR that contains the application, its dependencies, and an embedded server. Layered JARs let container builds reuse unchanged dependency layers.

## How it works / Step by step

1. `SpringApplication.run` creates the application context and reads the environment (command line, environment variables, property files, profiles).
2. Component scanning registers your beans.
3. Auto-configuration classes are evaluated against the conditions above and register default beans where allowed.
4. The embedded server starts, and the application is ready.

| Source (highest priority first) | Example |
|---|---|
| Command-line arguments | `--server.port=9090` |
| Environment variables | `SERVER_PORT=9090` |
| Profile-specific file | `application-prod.yml` |
| Default file | `application.yml` |

Higher sources override lower ones for the same key.

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
