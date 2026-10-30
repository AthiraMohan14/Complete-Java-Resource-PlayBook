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

### The twelve-factor app

The twelve-factor method is a set of practices for building software-as-a-service applications that are portable and easy to run in the cloud. It was written by engineers at Heroku, and it still describes the habits that make cloud-native services easy to operate. Know the ideas, even if you do not recite the numbering.

| Factor | Practice | What it looks like in Java |
|---|---|---|
| Codebase | One repository per service, many deploys | The same artefact runs in dev, test, and production |
| Dependencies | Declare every dependency and isolate it | Maven or Gradle lists all libraries; no reliance on the server's libraries |
| Config | Keep config out of the code and read it from the environment | Spring properties overridden by environment variables; no secrets in Git |
| Backing services | Treat databases, queues, and caches as attached resources | Connection details come from configuration, so a service can swap providers |
| Build, release, run | Separate the stages strictly | CI builds the artefact once; deployment combines it with config |
| Processes | Stay stateless; keep state in backing services | Sessions in Redis; uploads in object storage |
| Port binding | Export the service by binding a port | Embedded Tomcat or Netty serves HTTP directly |
| Concurrency | Scale out with more processes | More pods or instances, not bigger threads |
| Disposability | Start fast and stop gracefully | Graceful shutdown in Spring Boot lets in-flight requests finish |
| Dev/prod parity | Keep environments as similar as possible | Local containers that match production's database version |
| Logs | Write logs as a stream to standard output | The platform or a log agent collects and ships them |
| Admin processes | Run one-off tasks as separate processes | Database migrations run as a job, not at application startup |

Config deserves emphasis. Prefer configuration and conventions over code branches for environment differences, so the same binary behaves correctly everywhere. For secrets, see [Secrets management](../10-security/secrets-management.md).

### Cloud service models and where data lives

Cloud offerings are often grouped by how much of the stack the provider runs:

- **IaaS** (infrastructure as a service): virtual machines, storage, and networks on demand. You manage the operating system and above.
- **PaaS** (platform as a service): a ready runtime for deploying code; you manage the application and its data.
- **SaaS** (software as a service): finished applications, used rather than built.
- **BPaaS** (business process as a service): outsourced business processes delivered from the cloud, usually automated and shared across customers.

For storage, the common AWS pair shows the trade-off. A managed relational database (RDS) suits transactional data with relationships, consistency needs, and complex queries. Object storage (S3) suits files, backups, logs, and static assets, where capacity and durability matter more than query power.

| Need | Typical choice | Reason |
|---|---|---|
| Orders, accounts, inventory | Relational database | Transactions, constraints, and joins |
| User-uploaded images or documents | Object storage | Cheap, large, and served by key |
| Application logs at high volume | Object storage, or a log platform | Unstructured and retained for a period |
| Database backups | Object storage | Durable and inexpensive over long retention |
| Real-time analytics queries | A store built for analytics | Scans and aggregations across large data |

In microservices, each service usually gets its own relational database, while object storage can be a shared resource for files, backups, and audit exports. Details of specific cloud services are in [AWS](../18-cloud/aws.md).

### Deployment strategies

Deployment strategies describe how a new version replaces an old one. They trade downtime, risk, cost, and rollback speed:

- **Big bang**: stop the old version, deploy the new one. Simple and cheap, but downtime is visible and rollback is slow. Suits non-critical systems in quiet windows.
- **Blue-green**: run two identical environments. Deploy to the idle one, check it, and switch traffic. Rollback means switching back. The cost is roughly double the infrastructure while both run.
- **Canary**: send a small share of traffic, for example 5 percent, to the new version. Watch error rates and latency, then increase the share or roll back. Limits the blast radius of a bad release.
- **Rolling**: replace instances in batches, so the service stays up while the pool changes. Kubernetes uses this as its default Deployment strategy, controlled by `maxSurge` and `maxUnavailable`.
- **Shadow** (dark launch): copy live requests to the new version and discard its responses. It validates behaviour under real traffic at double cost. Shadow traffic must not trigger side effects such as charges or emails, so the new version needs a read-only path or a sandboxed dependency.

```yaml
# Rolling update settings on a Kubernetes Deployment
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # at most one extra pod during the rollout
      maxUnavailable: 0    # never drop below the desired count
```

| Strategy | Downtime | Risk | Cost | Rollback | Typical use |
|---|---|---|---|---|---|
| Big bang | High | High | Low | Slow | Low-stakes systems during a quiet window |
| Blue-green | None | Medium | About 2x while both run | Instant | Critical systems needing a fast switch |
| Canary | None | Low | Near normal | Quick | High-traffic production services |
| Rolling | None, with health checks | Low | Near normal | Quick | Stateless services on Kubernetes |
| Shadow | None | Very low | About 2x during testing | Not needed | Validating a new version before users see it |

Database changes complicate every strategy. Make schema changes backward compatible, deploy the code that tolerates both shapes, and only then remove the old shape. The pipeline side of this is covered in [CI/CD](../17-cicd/index.md).

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

## Monorepo or multi-repo

A monorepo keeps all services, shared libraries, contracts, and deployment files in one repository. A multi-repo layout gives each service its own repository and pipeline. Neither choice defines the architecture; the service boundary and the API contract do.

| Concern | Monorepo | Multi-repo |
|---|---|---|
| Cross-service change | One commit can update a library and all its callers | Coordinated releases across repositories |
| Shared code | Used directly from the same tree | Published as versioned artifacts |
| Ownership | Coarser access control | Clear per-service ownership |
| Build and CI | Needs path filters or a build graph to stay fast | Simple per service, but CI config is duplicated |
| Version drift | Less likely, one place to pin versions | Likely unless dependencies are updated regularly |

A typical monorepo has a parent build file that pins framework versions, a `libs/` folder for technical code (error handling, logging, messaging setup), a `contracts/` folder for API descriptions, and one folder per service. CI builds only the services affected by a change.

```
platform/
  pom.xml
  libs/common-web/
  contracts/orders-api.yaml
  services/order-service/
  services/payment-service/
  deploy/
```

Share technical libraries and contracts, not domain entities. If services share domain classes, a change to one forces releases of the others, and the system becomes a distributed monolith.

!!! tip "Interview tip"
    **Q: Monorepo or multi-repo for a large Spring Boot codebase?**
    Pick by ownership and change frequency. A small team that changes services together benefits from one repository and atomic changes. Many autonomous teams usually prefer separate repositories, with versioned shared libraries and published contracts. In either case, pin versions in one place and keep domain classes out of the shared code.

## Quick recap

- Draw service boundaries around bounded contexts and data ownership.
- Each service owns its database; a shared database creates a distributed monolith.
- A monolith is often the right answer for a young or small system.
- Observability needs logs, metrics, and traces tied together by trace IDs.
- Plan for network failure from the start.

**See also:** [Spring Cloud](spring-cloud.md) | [Distributed Transactions](distributed-transactions.md) | [Observability](../20-observability/index.md)
