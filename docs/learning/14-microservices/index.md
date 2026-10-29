# Microservices

Microservices split a system into independently deployable services, each owning its data and a bounded piece of the business. The benefits (team autonomy, independent scaling) come with real costs: network failures, distributed data, and operational complexity. These notes cover decomposition and observability, the Spring Cloud building blocks, resilience patterns, communication styles, and distributed transactions. Interviewers ask about them to see whether you can weigh those costs honestly, not only describe the architecture.

---

## Topics

### [Microservices Fundamentals](microservices-fundamentals.md)
**bounded contexts - database per service - monolith versus microservices - observability**
How to decide service boundaries, when a monolith is the better choice, and how to see what a distributed system is doing.

### [Spring Cloud](spring-cloud.md)
**Eureka - LoadBalancer - Config Server - Spring Cloud Gateway - Micrometer Tracing**
The Spring Cloud components for service discovery, client-side load balancing, centralised configuration, routing, and tracing on Spring Boot 3.

### [Resilience Patterns](resilience-patterns.md)
**circuit breaker - retry - timeouts - bulkhead - rate limiting - Resilience4j**
Keeping one failing dependency from taking down the whole system, with the states and settings interviewers expect.

### [Inter-Service Communication](inter-service-communication.md)
**REST - gRPC - GraphQL - messaging - mTLS - token propagation - API versioning**
Choosing synchronous or asynchronous calls, securing service-to-service traffic, and changing APIs without breaking callers.

### [Distributed Transactions](distributed-transactions.md)
**CAP - eventual consistency - sagas - compensating transactions - two-phase commit - idempotency**
Keeping data consistent across services without distributed locks, and the trade-offs of each approach.

---

**See also:** [Messaging and Event-Driven Architecture](../13-messaging/index.md) | [Security](../10-security/index.md) | [Docker](../15-docker/index.md)
