# Microservices Fundamentals

A microservice is a small, independently deployable service that owns one business capability and its data. The architecture is as much about organisation as code: teams own services end to end. Interviewers ask about microservices to test whether you know where to draw boundaries, why each service should own its database, when a monolith is the right answer, and how to observe a system spread across many processes.

## Core concepts

### Decomposition and bounded contexts

Domain-Driven Design gives a practical way to find boundaries. A bounded context is an area of the domain where a model and its terms have a single consistent meaning. "Order" in sales (a cart with prices) and "order" in shipping (a parcel with dimensions) are different models, so they belong in different contexts, each with its own service.

Common decomposition strategies:

- By business capability (billing, inventory, shipping)
- By subdomain, separating core differentiators from supporting and generic areas
- By data ownership: one service is the authority for a piece of data
- By change frequency: parts that change together stay together

A good boundary keeps related changes inside one service. If a single feature requires editing four services in lockstep, the boundary is wrong.

### Database per service

Each service owns its data store and exposes it only through its API or events. Other services never read its tables directly. This keeps services independently deployable and lets each team choose a suitable store. The cost is that queries spanning services need API calls, events, or a read model, and transactions cannot span services as easily (see [Distributed Transactions](distributed-transactions.md)).

Sharing one database between services is the most common way a "microservice" architecture becomes a distributed monolith: services look separate but cannot change independently.

### Monolith versus microservices

| Factor | Monolith | Microservices |
|---|---|---|
| Deployment | One unit | Many units, each independent |
| Consistency | Local transactions | Eventual consistency across services |
| Operations | Simpler | Needs service discovery, tracing, and more automation |
| Team scaling | Coordination cost grows with team size | Teams can own services |
| Latency | In-process calls | Network calls that can fail |

A well-structured modular monolith is often the right starting point. Split a module into a service when there is a clear reason: independent scaling, a different release cadence, a separate team, or a different technology need. Splitting too early creates the costs without the benefits.

### Observability

A request in a microservice system crosses several processes, so you need three kinds of signal to understand it:

- **Logs**: centralised, structured, and tagged with a trace ID. The ELK stack (Elasticsearch, Logstash, Kibana) is a common combination, and other log platforms work too.
- **Metrics**: counters, gauges, and histograms per service, scraped or pushed. Prometheus collects them and Grafana graphs them. Use Micrometer in Spring Boot to record them (see [Actuator and API Documentation](../09-spring-boot/actuator-and-api-docs.md)).
- **Traces**: one request's path across services, with timing for each hop. Zipkin and Jaeger store and display traces. OpenTelemetry is the vendor-neutral standard for generating them.

Health checks and readiness probes tell orchestrators whether an instance is alive and able to serve traffic. Application performance monitoring (APM) products combine these signals, usually for a fee.

Good observability needs consistent identifiers: pass the trace ID and correlation ID through every call and log line, so one request can be followed from the edge to the database.

### Context relationships and anti-corruption layers

Bounded contexts rarely exist alone. A context map describes how they relate. An upstream context publishes a model that a downstream context depends on. When the downstream model should not be shaped by someone else's model, put an anti-corruption layer (ACL) between them: a small translator that converts the external model into your own.

```java
// The shipping context's own model. Partner terms do not leak into it.
record Shipment(String shipmentId, String destinationCountry) {}

// Partner response shape, owned by someone else and likely to change.
record PartnerShipmentDto(String ref, String countryIsoCode) {}

// Anti-corruption layer: the only place that knows both shapes.
class PartnerShipmentTranslator {

    Shipment toDomain(PartnerShipmentDto dto) {
        return new Shipment(dto.ref(), dto.countryIsoCode());
    }
}
```

Other relationships you may be asked about include customer and supplier (the upstream team plans with the downstream team's needs in mind), conformist (the downstream team adopts the upstream model as-is), and shared kernel (two teams share a small, jointly owned model, which needs coordination).

### Migrating from a monolith

A rewrite of a whole system at once is risky. The strangler fig approach moves functionality gradually:

1. Put a routing layer (such as an API gateway) in front of the monolith.
2. Pick one capability with clear boundaries and build it as a service.
3. Route only that capability's traffic to the new service, and keep the rest on the monolith.
4. Keep data in sync while both exist, through events or a temporary read model, and decide which side owns the data.
5. Once the new service is trusted, retire the old code path. Repeat for the next capability.

The hardest step is data ownership. Moving code is usually easier than moving the tables it depends on.

### Ownership and operability checklist

A service is ready to run in production when a team can answer these questions:

- Who owns it, and who is on call for it?
- Does it own its data, with no other service writing to its tables?
- Does it expose health and readiness endpoints that reflect its real dependencies?
- Are its logs, metrics, and traces linked by a shared trace ID?
- Does it have timeouts, retries with limits, and a fallback for each remote call?
- Is there a runbook for its most likely failures?
- Can it be deployed and rolled back on its own pipeline?

Health checks deserve a note. Liveness should detect a broken process, and readiness can include dependencies, so that traffic stops reaching an instance that cannot serve it. The Spring Boot details are in [Actuator and API Documentation](../09-spring-boot/actuator-and-api-docs.md).

## How it works / Step by step

1. Identify business capabilities and bounded contexts from the domain.
2. Draw boundaries around data ownership and change patterns.
3. Give each service its own store, API, and deployment pipeline.
4. Add discovery, configuration, routing, and tracing (see [Spring Cloud](spring-cloud.md)).
5. Add resilience and monitoring before the first production incident, not after.

## Common pitfalls

- Creating services by technical layer (a "database service", a "validation service") instead of business capability.
- Shared databases across services.
- Chatty services that need five calls to answer one question.
- Splitting services before the domain is understood, then redrawing boundaries repeatedly.
- Deploying many services with no tracing, so incidents take hours to diagnose.
- Assuming the network is reliable. Every remote call needs a timeout and a failure plan.

!!! tip "Interview tip"
    **Q: When would you stay with a monolith?**
    When the team is small, the domain is still changing, the parts do not need independent scaling or deployment, and operational maturity is low. A modular monolith keeps clean boundaries without the distributed costs. Splitting later is much easier when the boundaries are already clear in the code.

## Quick recap

- Draw service boundaries around bounded contexts and data ownership.
- Each service owns its database; a shared database creates a distributed monolith.
- A monolith is often the right answer for a young or small system.
- Observability needs logs, metrics, and traces tied together by trace IDs.
- Plan for network failure from the start.

**See also:** [Spring Cloud](spring-cloud.md) | [Distributed Transactions](distributed-transactions.md) | [Observability](../20-observability/index.md)
