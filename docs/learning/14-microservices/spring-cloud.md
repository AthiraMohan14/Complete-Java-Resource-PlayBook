# Spring Cloud

Spring Cloud provides the infrastructure that a microservice system needs around the services themselves: finding them, balancing calls between instances, storing shared configuration, routing external traffic, and tracing requests. Interviewers ask about these components because each one solves a specific problem, and because many older tutorials use components that have changed or been retired. Check the Spring Cloud release train that matches your Spring Boot version before choosing components.

## Core concepts

### Service discovery with Eureka

Instances register their network location with a registry, and clients look up the current instances of a service by name. Netflix Eureka is one registry; Spring Cloud integrates with it through the Eureka client and server. Consul and etcd are other common registries. Kubernetes also provides service discovery through its own DNS and Service objects, so in a Kubernetes deployment you often do not need Eureka at all.

Instances register on startup and deregister on shutdown. Registries also rely on heartbeats, so a crashed instance is removed after its lease expires. Clients cache the list, which means discovery is eventually consistent.

```yaml
eureka:
  client:
    service-url:
      defaultZone: http://discovery.example.com:8761/eureka/
```

### Client-side load balancing

Spring Cloud LoadBalancer selects an instance for each call from the list discovered by name. Round-robin is the default, random selection is also built in, and other strategies (such as least-connections) need a custom implementation. The `ReactorLoadBalancer` interface is the extension point.

A load-balanced `WebClient` builder uses a logical service name in the URI:

```java
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
class ClientConfig {

    @Bean
    @LoadBalanced
    WebClient.Builder loadBalancedWebClientBuilder() {
        return WebClient.builder();
    }
}
```

```java
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
class InventoryClient {

    private final WebClient web;

    InventoryClient(WebClient.Builder builder) {
        this.web = builder.baseUrl("http://inventory-service").build();
    }

    Mono<String> stockFor(String sku) {
        return web.get().uri("/stock/{sku}", sku).retrieve().bodyToMono(String.class);
    }
}
```

`inventory-service` is a logical name resolved by discovery, not a host name.

### Centralised configuration

The Spring Cloud Config Server serves configuration over HTTP, usually backed by a Git repository. Clients fetch their configuration at startup, by application name and profile. Git gives history, review, and rollback for configuration changes.

```java
import org.springframework.cloud.config.server.EnableConfigServer;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

Beans that must pick up new values without a restart are marked `@RefreshScope`, and a refresh endpoint or bus message triggers the reload. Secrets should not sit in plain configuration files; combine the config server with a secrets store (see [Secrets Management](../10-security/secrets-management.md)).

### API gateway with Spring Cloud Gateway

Spring Cloud Gateway is the edge router for external traffic. It matches requests with predicates, applies filters, and forwards them to a URI. A `lb://` URI uses load balancing through discovery.

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders
          uri: lb://order-service
          predicates:
            - Path=/orders/**
          filters:
            - StripPrefix=1
```

Gateways commonly handle authentication, rate limiting, request size limits, and routing. Keep business logic out of the gateway; it should route and enforce policy, not decide what an order is. Gateway rate limiting usually uses a Redis-backed limiter, which makes it shared across gateway instances.

### Distributed tracing with Micrometer Tracing

Spring Cloud Sleuth is no longer available in Spring Boot 3. Its replacement is Micrometer Tracing, which creates trace and span IDs and propagates them across HTTP and messaging calls. You add a bridge to a tracing library (Brave or OpenTelemetry) and an exporter for Zipkin, Jaeger, or an OTLP-compatible backend.

```yaml
management:
  tracing:
    sampling:
      probability: 0.1
```

Sampling decides what fraction of requests are recorded. A low rate reduces cost and overhead; always-on sampling is useful in development and for specific routes. Trace and span IDs should also appear in log lines, so one request can be found across services.

## How it works / Step by step

1. A service instance starts and registers with discovery.
2. A client or gateway resolves the logical name to the list of healthy instances.
3. The load balancer picks one instance per call.
4. Configuration is loaded from the config server at startup; `@RefreshScope` beans reload on demand.
5. Tracing headers travel with each call, and spans are exported to the tracing backend.

## Common pitfalls

- Hard-coding host names in clients, which defeats discovery.
- Storing secrets in the config repository.
- Putting business rules into the gateway, which turns it into a bottleneck and a hidden service.
- Assuming a `@RefreshScope` bean updates everywhere; references held elsewhere keep the old value.
- Using outdated tutorials that rely on Sleuth, Ribbon, or Hystrix on Spring Boot 3.
- Sampling at 100% in production without considering overhead and cost.
- Relying on discovery without health checks, so dead instances keep receiving traffic.

!!! tip "Interview tip"
    **Q: Do you need Eureka on Kubernetes?**
    Usually not. Kubernetes Services already give you name-based discovery and load balancing. Spring Cloud components are still useful for configuration and routing, but the discovery role overlaps with the platform. Choose one discovery mechanism per environment and be clear about which one applies.

## Quick recap

- Eureka (or Consul, or Kubernetes DNS) maps logical service names to instances.
- Spring Cloud LoadBalancer picks an instance per call; round-robin is the default.
- The Config Server serves Git-backed configuration; `@RefreshScope` reloads selected beans.
- Spring Cloud Gateway routes external traffic with predicates and filters.
- Micrometer Tracing replaces Sleuth on Spring Boot 3, with a bridge and an exporter.

**See also:** [Resilience Patterns](resilience-patterns.md) | [Inter-Service Communication](inter-service-communication.md) | [Kubernetes](../16-kubernetes/index.md)
