# Actuator and API Documentation

Spring Boot Actuator adds operational endpoints (health, metrics, environment, and more) to a running application, and Micrometer provides the metrics backbone. springdoc-openapi generates OpenAPI documentation from your controllers. Interviewers ask about these to see whether you can run a service in production and whether you know which endpoints are dangerous to expose.

## Core concepts

### Enabling and exposing endpoints

Add `spring-boot-starter-actuator`. Actuator endpoints live under `/actuator`. Over HTTP, only a small set is exposed by default, and you choose what to add:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: when-authorized
```

`show-details: when-authorized` returns component details only to authenticated callers. Expose the minimum you need, and protect the rest with Spring Security (see the note below).

### Health checks

The `/actuator/health` endpoint aggregates health indicators. Each indicator is a bean that implements `HealthIndicator`. Its name, minus the suffix, becomes the component name in the output.

```java
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component
class PaymentProviderHealth implements HealthIndicator {

    @Override
    public Health health() {
        boolean reachable = checkProvider(); // replace with a cheap, bounded check
        return reachable
                ? Health.up().build()
                : Health.down().withDetail("reason", "provider unreachable").build();
    }

    private boolean checkProvider() {
        return true;
    }
}
```

Keep health checks cheap and time-bounded. A health check that calls a slow dependency can make the whole endpoint slow, and a load balancer may then remove a healthy instance.

### Liveness and readiness

Kubernetes distinguishes two probes. Liveness asks "should this process be restarted?", and readiness asks "should this instance receive traffic now?". Spring Boot exposes them when probes are enabled:

```yaml
management:
  endpoint:
    health:
      probes:
        enabled: true
```

The endpoints are `/actuator/health/liveness` and `/actuator/health/readiness`. Keep liveness independent of downstream services; otherwise a dependency outage restarts every pod. Readiness can reflect dependencies, so that traffic stops flowing to an instance that cannot serve it. Containers are covered in [Kubernetes](../16-kubernetes/index.md).

### Metrics with Micrometer

Micrometer is a metrics facade. You record metrics through `MeterRegistry`, and a registry implementation exports them to a backend such as Prometheus. Spring Boot configures the registry for you.

```java
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

@Service
class OrderMetrics {
    private final Counter created;

    OrderMetrics(MeterRegistry registry) {
        this.created = registry.counter("orders.created");
    }

    void recordCreated() {
        created.increment();
    }
}
```

Metric names should describe what is measured, not who measured it. Avoid high-cardinality tags such as user IDs or raw URLs, because each unique tag value creates a new time series.

### Other endpoints and their risk

| Endpoint | What it shows | Risk |
|---|---|---|
| `/actuator/env` | Configuration properties | Can reveal secrets unless sanitised |
| `/actuator/beans` | All beans in the context | Reveals internal structure |
| `/actuator/mappings` | Request mappings | Reveals routes |
| `/actuator/threaddump` | Thread states | Can reveal internal logic |
| `/actuator/heapdump` | Full memory snapshot | Can contain passwords and tokens |

Do not expose `heapdump` or `env` publicly. If you need them, restrict them to an internal management port or require strong authentication. A separate management port is set with `management.server.port`.

### API documentation with springdoc-openapi

For Spring Boot 3, the springdoc starter for Spring MVC is `springdoc-openapi-starter-webmvc-ui`. Choose the version that matches your Boot line. It scans controllers at runtime and serves the OpenAPI document at `/v3/api-docs`, with Swagger UI in the browser.

Annotations from `io.swagger.v3.oas.annotations` add descriptions:

```java
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/orders")
@Tag(name = "Orders", description = "Order lifecycle")
class OrderApiController {

    @Operation(summary = "Fetch an order by id")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Order found"),
            @ApiResponse(responseCode = "404", description = "Order not found")
    })
    @GetMapping("/{id}")
    String get(@Parameter(description = "Order identifier") @PathVariable long id) {
        return "order " + id;
    }
}
```

The docs are only as accurate as the code and annotations. Generate them from code, do not hand-maintain a separate spec, and review the generated output as part of the change.

### Securing docs and actuator

Swagger UI and `/actuator/**` are often left open by accident. Add rules for them in your security configuration, and decide per environment whether the docs are exposed at all. A common pattern is to serve docs in development and staging only, or behind authentication in production.

## How it works / Step by step

1. Actuator registers endpoints as beans and maps them under `/actuator` once they are exposed.
2. Health indicators are collected on each `/health` request, then combined into one status (the worst status wins).
3. Micrometer records metrics in the registry, and an exporter (for example Prometheus) scrapes or pushes them.
4. springdoc inspects controller mappings and annotations at startup and builds the OpenAPI document served at `/v3/api-docs`.

## Common pitfalls

- Exposing `*` (every endpoint) in production.
- Leaving actuator and Swagger UI unauthenticated.
- Health checks that call external services on every request without timeouts.
- Metrics with unbounded tag values such as user IDs.
- Trusting generated docs that describe responses your code no longer returns.
- Using liveness checks that depend on a database, which causes restart loops during database outages.

!!! tip "Interview tip"
    **Q: What is the difference between liveness and readiness?**
    Liveness decides whether a container should be restarted, so it should only detect a broken process. Readiness decides whether to send traffic, so it can include dependencies. Mixing them causes restarts during dependency outages, which makes things worse.

## Quick recap

- Expose only the actuator endpoints you need, and protect the rest.
- Implement `HealthIndicator` for custom checks; keep them cheap and bounded.
- Use liveness and readiness probes with different responsibilities.
- Record metrics via Micrometer with low-cardinality tags.
- Generate OpenAPI docs with springdoc, and do not expose them unguarded in production.

**See also:** [Building REST APIs](rest-apis.md) | [Observability](../20-observability/index.md) | [Spring Security Authorisation](../10-security/spring-security-authorisation.md)
