# Architecture and Distributed Systems Questions (Part 3 of 3)

Questions on repository layout for microservices, architecture styles (layered, hexagonal, and clean), and a worked design for an issue tracker. Start with [Part 1](architecture-and-distributed-part-1.md) and [Part 2](architecture-and-distributed-part-2.md) if you have not read them.

Continued from [Part 2](architecture-and-distributed-part-2.md).

---

## 25. Should a large Spring Boot codebase live in a monorepo or in multiple repos? Describe how you would structure it for microservices.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A monorepo suits a team that owns several related services and wants shared code, one build toolchain, and atomic changes across services. Multiple repos suit teams that need independent ownership, release cadence, and access control per service. Either choice works. Decide by asking who owns what, how often services change together, and how much shared code you have. Whichever you pick, the real boundary between services is the API contract and the deployment unit, not the repository.

### Explanation
A monorepo layout for a few Spring Boot services might look like this:

```
platform/
  pom.xml                 parent POM: Spring Boot version and dependency management
  libs/
    common-web/           shared error handling (problem details), logging setup
    common-messaging/     shared event envelope and serialisation config
  contracts/
    orders-api.yaml       OpenAPI description, reviewed like code
  services/
    order-service/        its own Spring Boot application
    payment-service/
    notification-service/
  deploy/                 Helm charts or Terraform, one folder per service
```

In a monorepo, CI uses path filters or a build graph so that a change to one service builds and tests only that service and the libraries it depends on. Maven multi-module and Gradle multi-project builds, with build caching, keep this fast. In a multi-repo setup, each service has its own repository and pipeline. Shared code is published as versioned artifacts to an internal artifact repository, and contracts are published as versioned packages or schemas.

Trade-offs to state:
- **Monorepo:** one change can update a shared library and all its callers in a single commit; refactoring is easier; there is one set of tooling. The cost is that the build must stay fast, the clone grows, and access control is usually coarser.
- **Multi-repo:** clear ownership, independent deployments, and fine-grained access. The cost is version drift between services, duplicated CI configuration, and harder cross-cutting changes.

Whatever the layout, share only technical libraries and API contracts. Sharing domain classes across services couples their release cycles and turns the system into a distributed monolith.

### When to use / pitfalls
- A team of one or two that changes services together usually benefits from a monorepo; a large organisation with many autonomous teams often prefers multi-repo.
- Pin dependency versions in one place (a parent POM or BOM, or a Gradle version catalog) so services do not drift.
- Version shared libraries with semantic versioning and avoid breaking changes in minor releases.
- Do not put a shared "common" module full of domain entities into every service.

**See also:** [Microservices fundamentals](../../learning/14-microservices/microservices-fundamentals.md), [Monorepo or multi-repo](../../learning/14-microservices/microservices-fundamentals.md#monorepo-or-multi-repo), [Spring and security](spring-and-security-part-1.md)

</details>

---

## 26. What are the key differences between layered, hexagonal (ports and adapters), and clean architecture?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Layered architecture stacks presentation, business logic, and persistence, and each layer usually depends on the one below it. Hexagonal architecture puts the domain and use cases at the centre, defines ports (interfaces) that the core needs, and plugs in adapters for HTTP, databases, and messaging. Clean architecture uses concentric rings with a strict dependency rule: source code dependencies point only inward, towards entities and use cases. Hexagonal and clean share the same goal, a domain that does not depend on frameworks, and differ mostly in terminology and how many rings they name.

### Explanation
In a typical layered Spring application, a controller calls a service, the service calls a JPA repository, and the entities are the same classes everywhere. This is simple and fits many CRUD systems. The weakness is that business rules leak into services and persistence annotations shape the domain.

Hexagonal architecture inverts the dependency for outside systems. The core defines an outbound port, and an adapter implements it:

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

record Order(String id, boolean placed) {}

// Port: an interface the domain needs, owned by the core
interface OrderRepository {
    Optional<Order> findById(String id);
    void save(Order order);
}

// Use case: depends only on the port, not on JPA or HTTP
class PlaceOrderUseCase {
    private final OrderRepository orders;

    PlaceOrderUseCase(OrderRepository orders) {
        this.orders = orders;
    }

    Order place(String id) {
        Order order = new Order(id, true);
        orders.save(order);
        return order;
    }
}

// Adapter: an in-memory implementation; a JPA adapter would replace it in production
class InMemoryOrderRepository implements OrderRepository {
    private final Map<String, Order> store = new HashMap<>();

    @Override
    public Optional<Order> findById(String id) {
        return Optional.ofNullable(store.get(id));
    }

    @Override
    public void save(Order order) {
        store.put(order.id(), order);
    }
}
```

Clean architecture names the rings: entities (enterprise rules), use cases (application rules), interface adapters (controllers, presenters, gateways), and frameworks and drivers (the database, the web framework). The dependency rule says nothing in an inner ring may name anything in an outer ring. Hexagonal architecture describes the same idea as driving adapters (which call the core, such as a REST controller) and driven adapters (which the core calls, such as a repository).

### When to use / pitfalls
- Layered is the right default for a simple CRUD service. Do not add ports and adapters to every small service out of habit.
- Hexagonal and clean pay off when there are several inputs (HTTP, messages, batch jobs), several outputs, or complex rules that must be tested without a database.
- Mapping between domain objects and persistence or API objects adds code. Accept that cost only where it protects the domain.
- In interviews, avoid saying the three are different products. They are ways of drawing dependencies, and a real codebase often mixes them.

**See also:** [Software design principles](../../learning/foundations/software-design-principles.md), [Layered, hexagonal, and clean architecture](../../learning/foundations/software-design-principles.md#layered-hexagonal-and-clean-architecture), [Architecture and distributed systems, part 2](architecture-and-distributed-part-2.md)

</details>

---

## 27. How would you design a system like Jira? Cover projects, issues, workflows, permissions, search, and notifications.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Start by agreeing on the requirements: many projects per organisation, issues with fields and comments, a configurable workflow per issue type, role-based permissions, fast search, and notifications to watchers. Split the system into a project and configuration service, an issue service with its own database, a workflow engine that validates transitions, a permission check used by every call, a search index fed by change events, and a notification service fed by a queue. Keep the issue write path simple and transactional, and let search and notifications be eventually consistent.

### Explanation
High-level components:
- **API gateway** that authenticates the user and routes requests.
- **Project and configuration service** that stores projects, issue types, custom fields, and workflow definitions.
- **Issue service** that creates and updates issues. It keeps issues in a relational database partitioned by tenant or project, and it allocates a per-project sequence for keys such as PROJ-123.
- **Workflow engine** that holds each workflow as states and transitions, with optional conditions and validators, and rejects an invalid transition on the server.
- **Permission service** that answers whether a user can view, edit, or transition an issue, based on project roles and issue security levels. It caches role assignments.
- **Activity log** that appends every change to an immutable history for audit and for the activity feed.
- **Search index** (for example, OpenSearch or Elasticsearch) that receives change events and serves filtered queries, similar to JQL.
- **Notification service** that consumes issue events from a queue, works out watchers and mentions, and sends in-app, email, or chat messages in batches.
- **Object storage** for attachments, referenced from the issue record.

A typical update flows like this: the gateway authenticates the user, the issue service checks permission and runs the workflow transition in one database transaction, writes the history row, and publishes an event. The search indexer and notification service consume that event later.

### Trade-offs
- **Search consistency:** an indexed search lags a few seconds behind writes. Acceptable for most users, but a user who just edited an issue may need to see the change from the database directly.
- **Permissions in search:** results must be filtered by what the user may see. Filtering at query time is correct but costs extra work per query; pre-computing visibility per user is faster but must be updated when roles change.
- **Custom fields:** a flexible schema (JSON columns or an entity-attribute-value table) supports per-project fields, but it is harder to index and query than fixed columns.
- **Workflows:** a data-driven workflow engine lets administrators change states without a deploy, at the cost of more validation logic to test.
- **Notifications:** a user watching a busy issue can receive many messages. Batching and digest emails reduce noise and load, but add delay.

### When to use / pitfalls
- Do not let the search index be the source of truth. Rebuild it from the database and the event log when needed.
- Enforce permissions and workflow rules in the service, not only in the UI.
- Make the event consumers idempotent, because a queue may deliver the same event twice.
- Plan multi-tenancy early. Tenant identifiers in every table and index affect the whole design.

**See also:** [Practice problems](../../learning/19-system-design-fundamentals/practice-problems.md), [Event-driven architecture](../../learning/13-messaging/event-driven-architecture.md), [Architecture and distributed systems, part 2](architecture-and-distributed-part-2.md)

</details>

---

## Quick recap

- A monorepo or multi-repo choice depends on ownership and change frequency; share libraries and contracts, not domain classes.
- Layered architecture is simple; hexagonal and clean architecture invert dependencies so the domain does not depend on frameworks.
- A design for an issue tracker separates configuration, issues, workflows, permissions, search, and notifications, and makes everything except the write path eventually consistent.
- Always check permissions on the server, and make event consumers idempotent.

**See also:** [Architecture and distributed systems, part 1](architecture-and-distributed-part-1.md), [Architecture and distributed systems, part 2](architecture-and-distributed-part-2.md), [Interview preparation](../interview-process.md), [Technical questions index](index.md)
