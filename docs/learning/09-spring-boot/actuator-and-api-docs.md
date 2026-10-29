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

### The info endpoint and build metadata

`/actuator/info` returns descriptive data about the running build. It is useful for confirming which version is deployed. Three sources feed it:

- Properties under the `info` prefix in your configuration files.
- Build metadata. If the build plugin writes `build-info.properties`, Boot includes a `build` section automatically. Maven projects produce this with the `build-info` goal of the Spring Boot plugin.
- Beans that implement `InfoContributor`, for values that are only known at runtime.

```yaml
info:
  app:
    name: order-service
    team: payments
management:
  info:
    env:
      enabled: true              # expose info.* values from the environment
```

Resource filtering can copy the project version into a property. The Boot parent POM enables this for the `application` files, so `version: @project.version@` in `application.yml` is replaced at build time.

```java
import org.springframework.boot.actuate.info.Info;
import org.springframework.boot.actuate.info.InfoContributor;
import org.springframework.stereotype.Component;

@Component
class RuntimeInfo implements InfoContributor {

    @Override
    public void contribute(Info.Builder builder) {
        builder.withDetail("region", "eu-west-1");   // known only at runtime, or from the platform
    }
}
```

Do not put secrets, connection strings, or internal hostnames in the info output. It is often public, even when other endpoints are protected.

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

### Prometheus and custom readiness

To scrape metrics with Prometheus, add the Micrometer registry and expose its endpoint. The endpoint then serves text in the Prometheus exposition format at `/actuator/prometheus`.

```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
```

Readiness is not only about the database being reachable. An application can tell the platform it should not receive traffic yet, for example while a cache loads. Publish an `AvailabilityChangeEvent` with `ReadinessState.REFUSING_TRAFFIC` and later switch back to `ACCEPTING_TRAFFIC`:

```java
import org.springframework.boot.availability.AvailabilityChangeEvent;
import org.springframework.boot.availability.ReadinessState;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;

@Component
class CatalogLoader {

    private final ApplicationEventPublisher publisher;

    CatalogLoader(ApplicationEventPublisher publisher) {
        this.publisher = publisher;
    }

    void reload() {
        publisher.publishEvent(new AvailabilityChangeEvent<>(this, ReadinessState.REFUSING_TRAFFIC));
        try {
            // load reference data here
        } finally {
            publisher.publishEvent(new AvailabilityChangeEvent<>(this, ReadinessState.ACCEPTING_TRAFFIC));
        }
    }
}
```

The readiness probe then reports the state, and the orchestrator stops routing traffic during the reload. Make sure the instance returns to `ACCEPTING_TRAFFIC` even when the load fails, or it stays out of service.

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

### Audit events and their security

Boot can record audit events through an `AuditEventRepository`. Spring Security publishes sign-in successes and failures, and Boot's audit listener stores them, so you get that trail without writing code. Its default repository is in memory, bounded, and lost on restart. For anything you must keep, export the events to a durable store.

Your own business events go through the same repository. The principal is the user or service that acted, and the data map holds only the detail you need to investigate:

```java
import java.util.Map;
import org.springframework.boot.actuate.audit.AuditEvent;
import org.springframework.boot.actuate.audit.AuditEventRepository;
import org.springframework.stereotype.Service;

@Service
class PriceAudit {

    private final AuditEventRepository audit;

    PriceAudit(AuditEventRepository audit) {
        this.audit = audit;
    }

    void priceChanged(String actor, String sku) {
        audit.add(new AuditEvent(actor, "PRICE_CHANGED", Map.of("sku", sku)));
    }
}
```

Audit data is personal data in many cases, because it records who did what and from where. Three rules follow. Do not write tokens, passwords, or full request bodies into an event. Set a retention period that matches your policy, and delete events when it ends. Restrict the `auditevents` endpoint, because it exposes the trail to anyone who can call it.

## How it works / Step by step

1. Actuator registers endpoints as beans and maps them under `/actuator` once they are exposed.
2. Health indicators are collected on each `/health` request, then combined into one status (the worst status wins).
3. Micrometer records metrics in the registry, and an exporter (for example Prometheus) scrapes or pushes them.
4. springdoc inspects controller mappings and annotations at startup and builds the OpenAPI document served at `/v3/api-docs`.

## Troubleshooting

Most actuator problems come down to one of four causes. Check them in this order.

| Symptom | Likely cause | What to check |
|---|---|---|
| `404` on an endpoint such as `/actuator/metrics` | The endpoint is not exposed, or the actuator starter is missing | `management.endpoints.web.exposure.include` and the dependency list |
| `401` or `403` on `/actuator/...` | Spring Security rules cover the actuator paths | The security filter chain, and whether the request carries credentials |
| Health is `DOWN` but the app works | One health indicator reports a failure | The component details in `/actuator/health`, shown to authorised callers |
| A metric is missing from `/actuator/metrics` | The meter has not been recorded yet, or the name is different | Whether the code has run once, and the exact name in the list |

Some details that cause confusion:

- A counter or timer usually appears only after its first recording, so a new metric can be absent right after a deploy. Trigger the code path once before you look.
- Prometheus renames dots to underscores in metric names. A metric called `orders.created` appears as `orders_created` in the scrape output.
- A `DOWN` health result from a slow dependency can make an orchestrator remove the instance. Check the timeout on the indicator before you blame the dependency.
- Probe endpoints such as `/actuator/health/readiness` appear only when probes are enabled. On a platform that reports them as missing, check the property first.

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
