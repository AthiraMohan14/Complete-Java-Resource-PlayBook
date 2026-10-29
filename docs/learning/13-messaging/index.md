# Messaging and Event-Driven Architecture

Messaging lets services communicate without waiting on each other, and lets work be spread across time and machines. This section covers Apache Kafka (a distributed log), RabbitMQ (a flexible message broker), and the patterns built on them: event sourcing, CQRS, sagas, and idempotent consumers. Interviewers ask about these to check that you understand delivery guarantees, ordering, and failure handling, which are where messaging systems go wrong.

---

## Topics

### [Apache Kafka](kafka.md)
**topics - partitions - consumer groups - offsets - acks - delivery semantics - Spring for Apache Kafka**
How Kafka stores and distributes events, the guarantees it gives for ordering and delivery, and how Spring consumes and produces messages.

### [RabbitMQ](rabbitmq.md)
**exchanges - queues - bindings - routing keys - acknowledgements - dead-letter exchanges - Spring AMQP**
Routing messages through exchanges to queues, handling acknowledgements and failures, and configuring Spring AMQP.

### [Event-Driven Architecture](event-driven-architecture.md)
**event sourcing - CQRS - sagas - eventual consistency - event versioning - idempotent consumers - outbox**
Designing systems around events, the patterns that coordinate them, and the failure modes they introduce.

---

**See also:** [Microservices](../14-microservices/index.md) | [Caching and Performance](../12-caching-performance/index.md) | [Testing](../11-testing/index.md)
