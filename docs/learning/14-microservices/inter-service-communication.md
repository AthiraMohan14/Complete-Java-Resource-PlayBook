# Inter-Service Communication

Microservices talk to each other either synchronously (a caller waits for a reply) or asynchronously (a caller publishes a message and moves on). Each style suits different needs, and both need security and a plan for changing APIs. Interviewers ask about this to see whether you choose the style for a reason, and whether you can keep callers working when the provider changes.

## Core concepts

### Synchronous styles

| Style | Strengths | Trade-offs |
|---|---|---|
| REST over HTTP | Ubiquitous, easy to debug, cache-friendly for reads | Text payloads, loosely typed contracts unless documented |
| gRPC | Binary Protocol Buffers, strongly typed contracts, streaming, deadlines | Less convenient from browsers; needs generated code |
| GraphQL | Clients ask for the fields they need, one endpoint | Complex caching and authorisation; query cost must be controlled |

Synchronous calls couple availability: if the callee is down, the caller fails unless it has a fallback. Keep the number of synchronous hops in a user request small.

REST is the default for most services. Pick gRPC for internal, high-volume, or streaming traffic where typed contracts matter. Pick GraphQL when a client aggregates many resources and the team can manage the query cost.

### Asynchronous styles

Messaging (Kafka, RabbitMQ, or a cloud queue such as AWS SQS) decouples producers from consumers in time. The producer does not wait for the consumer, and the consumer can process at its own pace. This absorbs traffic spikes and survives short outages. The cost is eventual consistency and the need for idempotent consumers (see [Event-Driven Architecture](../13-messaging/event-driven-architecture.md)).

Use asynchronous messages for notifications and workflows that do not need an immediate answer. Use synchronous calls when the caller needs the result to continue.

### Service-to-service security

Traffic between services must be authenticated and encrypted, even inside a private network.

- **Mutual TLS (mTLS)**: both sides present certificates, so each service knows the other's identity. Service meshes and certificate authorities commonly manage this.
- **Token propagation**: the caller forwards the end user's JWT, so downstream services can check authorisation. Alternatively, the caller uses its own identity with the client credentials grant when the user is not involved.
- **Least privilege**: each service accepts calls only from the services that need them.

Do not trust a request only because it comes from inside the network. Forwarding a token blindly can also let a downstream service accept requests the user should not make; check the audience and scopes at each hop.

```java
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
class ShipmentClient {

    private final WebClient web;

    ShipmentClient(WebClient.Builder builder) {
        this.web = builder.baseUrl("http://shipping-service").build();
    }

    // Forward the caller's bearer token so shipping can authorise the same user.
    Mono<String> status(String shipmentId, String bearerToken) {
        return web.get()
                .uri("/shipments/{id}", shipmentId)
                .headers(h -> h.setBearerAuth(bearerToken))
                .retrieve()
                .bodyToMono(String.class);
    }
}
```

### API versioning and backward compatibility

Consumers deploy on their own schedule, so a provider change must not break them. Backward-compatible changes include adding optional fields, adding endpoints, and adding optional request parameters. Breaking changes include removing or renaming fields, changing types or meanings, and making optional inputs required.

When you must break compatibility:

- Version the API (in the path, such as `/v2/`, or through a header or media type). Path versioning is the easiest to see and route.
- Run old and new versions side by side for a deprecation period.
- Use expand and contract: add the new field, migrate callers, then remove the old one.
- Use consumer-driven contract tests so the provider learns what its consumers depend on (see [API Testing and Code Coverage](../11-testing/api-testing-and-coverage.md)).

Tolerant readers ignore unknown fields. Consumers that fail on new fields force providers to coordinate every change.

### Choosing a style for a call

Ask four questions:

1. Does the caller need the answer to continue? If yes, synchronous.
2. Can the callee be unavailable for a while? If yes, asynchronous.
3. Is the traffic high or latency-sensitive? Consider gRPC.
4. Does a user-facing client need flexible queries? Consider GraphQL at the edge.

### Versioned endpoints in practice

Suppose a shipment response needs a new `carrier` field. Adding a field is backward-compatible for tolerant readers, so `v1` can keep its shape and gain the field. A breaking change, such as splitting `status` into two fields, needs a new version:

```java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

record ShipmentV1(String id, String status) {}
record ShipmentV2(String id, String state, String substate, String carrier) {}

@RestController
class ShipmentApi {

    @GetMapping("/v1/shipments/{id}")
    ShipmentV1 getV1(@PathVariable String id) {
        return new ShipmentV1(id, "IN_TRANSIT");
    }

    @GetMapping("/v2/shipments/{id}")
    ShipmentV2 getV2(@PathVariable String id) {
        return new ShipmentV2(id, "IN_TRANSIT", "WITH_CARRIER", "acme-freight");
    }
}
```

Both versions can share the same service logic and differ only in their mapping to response types. Keep the v1 mapping stable until the deprecation date you announced, and make the deprecation visible in responses (for example, a `Deprecation` header) and in documentation. Removing a version is itself a breaking change, so it needs the same coordination as a release.

## How it works / Step by step

1. The caller chooses a style based on the questions above.
2. For synchronous calls, the request carries credentials (token or mTLS identity), a timeout, and a trace ID.
3. The callee authorises, processes, and responds; the caller handles errors and fallbacks.
4. For asynchronous calls, the producer publishes an event, and consumers process it later with idempotency.
5. When the API changes, the team checks compatibility, versions if needed, and removes old behaviour only after callers have moved.

## Common pitfalls

- Chains of synchronous calls, where one user request waits on five services.
- Calling without timeouts or retries designed for idempotency.
- Forwarding user tokens to services that should not receive them, or without checking audience.
- Trusting internal traffic by network location alone.
- Breaking consumers by renaming a field, with no deprecation period.
- Using gRPC or GraphQL because they are fashionable, without a need that REST does not meet.
- Versioning every small change, which multiplies maintenance.

!!! tip "Interview tip"
    **Q: REST or messaging between two services?**
    Use REST when the caller needs an immediate answer to continue, such as a price lookup during checkout. Use messaging when the caller only needs to announce a fact or start work, such as sending a confirmation email after an order. Many systems use both, and the choice should follow the business need, not the tool.

## Quick recap

- Synchronous styles (REST, gRPC, GraphQL) fit immediate answers; asynchronous messaging fits decoupled work.
- Secure service-to-service traffic with mTLS or forwarded, audience-checked tokens.
- Make backward-compatible changes by default; use versioning and expand-and-contract for breaking ones.
- Keep synchronous hops per request small and always set timeouts.
- Choose the style per call, based on whether the caller needs the answer now.

**See also:** [Resilience Patterns](resilience-patterns.md) | [Authentication: JWT, OAuth 2.0, and OpenID Connect](../10-security/authentication-jwt-oauth.md) | [Apache Kafka](../13-messaging/kafka.md)
