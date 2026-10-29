# REST Principles and Versioning

REST is an architectural style built on HTTP: resources are identified by URLs, and the standard methods and status codes carry most of the meaning. Interviewers ask about REST to see whether you use HTTP correctly and whether you can change an API without breaking the people who call it.

## Core concepts

### Resources and statelessness

Model your API around **resources** (nouns) rather than actions (verbs). `/orders/42` identifies an order. Actions are expressed through methods, or through sub-resources when a state change is a real thing, such as `POST /orders/42/cancellation`.

**Stateless** means each request carries everything the server needs to process it: authentication, parameters, and representation. The server does not keep a conversation in memory between requests. Statelessness lets any instance handle any request, which makes horizontal scaling and load balancing straightforward. Session state, when needed, lives in a store such as a database or cache.

### HTTP methods and their properties

| Method | Purpose | Safe | Idempotent |
|---|---|---|---|
| `GET` | Read a resource | Yes | Yes |
| `HEAD` | Read headers only | Yes | Yes |
| `OPTIONS` | Describe what is allowed (used in CORS preflight) | Yes | Yes |
| `PUT` | Replace a resource at a known URL | No | Yes |
| `PATCH` | Partially change a resource | No | Not necessarily |
| `POST` | Create, or trigger processing | No | No |
| `DELETE` | Remove a resource | No | Yes |

**Safe** means the method does not change server state. **Idempotent** means doing it twice has the same effect as doing it once. `PUT` replaces the whole representation, so repeating it gives the same result. `PATCH` can be non-idempotent, for example "increment the counter by one". `POST` is neither, so retries of a `POST` can create duplicates (see [idempotency](pagination-errors-idempotency.md#idempotency)).

### Status codes

- **2xx success:** `200 OK`, `201 Created` (include a `Location` header), `204 No Content`
- **3xx redirect:** `301` and `308` for permanent moves, `304` for cache validation
- **4xx client error:** `400` malformed request, `401` not authenticated, `403` authenticated but not allowed, `404` not found, `409` conflict, `422` semantically invalid input, `429` too many requests
- **5xx server error:** `500` unexpected failure, `503` temporarily unavailable

Use the code that describes the problem. Returning `200` with an error in the body breaks monitoring, caches, and client libraries.

A Spring MVC controller showing these conventions:

```java
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderV1Controller {

    public record CreateOrderRequest(String sku, int quantity) {}

    public record OrderV1Response(long id, String status) {}

    @GetMapping("/{id}")
    public ResponseEntity<OrderV1Response> get(@PathVariable long id) {
        return ResponseEntity.ok(new OrderV1Response(id, "PLACED"));
    }

    @PostMapping
    public ResponseEntity<OrderV1Response> create(@RequestBody CreateOrderRequest request) {
        long newId = 1001L; // would come from the service layer
        return ResponseEntity
                .created(URI.create("/api/v1/orders/" + newId))
                .body(new OrderV1Response(newId, "PLACED"));
    }
}
```

### Content negotiation

The client sends `Accept` to say which representation it wants (`application/json`). The server sends `Content-Type` to say what it returned or what it is receiving. If the server cannot produce an acceptable type, it returns `406 Not Acceptable`. Spring picks converters based on these headers.

### Versioning

APIs change. Versioning lets you introduce breaking changes without forcing every client to move at once. Three common approaches:

| Approach | Example | Pros | Cons |
|---|---|---|---|
| URL path | `/api/v1/orders` | Visible, easy to route and cache | Duplicates URLs over time |
| Header or media type | `Accept: application/vnd.example.order.v2+json` | Keeps URLs stable | Harder to test in a browser |
| Query parameter | `/orders?version=2` | Easy to add | Easy to forget, mixes with filters |

URL versioning is the most common choice because it is explicit. The media-type style is what purists prefer. A media-type version can be matched in Spring with `produces`:

```java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/orders")
public class OrderVersionedController {

    public record OrderV2Response(long id, String status, String currency) {}

    @GetMapping(value = "/{id}", produces = "application/vnd.example.order.v2+json")
    public OrderV2Response getV2(@PathVariable long id) {
        return new OrderV2Response(id, "PLACED", "EUR");
    }
}
```

### Backward compatibility and deprecation

Some changes are **non-breaking**: adding an optional field to a response, adding a new endpoint, adding an optional query parameter. Clients that ignore unknown fields keep working. **Breaking** changes include removing or renaming a field, changing a type, making an optional input required, or changing the meaning of a status code.

When you must break something:

1. Publish the new version alongside the old one.
2. Document the change and a deprecation timeline.
3. Signal deprecation to clients with headers such as `Deprecation` and `Sunset` (RFC 8594 defines `Sunset`).
4. Track which clients still call the old version, and contact them.
5. Remove the old version only after the timeline ends and usage is clear.

## How it works

1. A client sends a request with a method, URL, headers, and optionally a body.
2. The server checks authentication and authorisation, then routes to a handler.
3. The handler performs the operation and chooses a status code that describes the outcome.
4. The response carries a representation that matches the `Accept` header.
5. Clients rely on the contract. Changes go through a version bump or a non-breaking extension.

## Common pitfalls

- Verbs in URLs (`/getOrder`, `/createOrder`) that fight with HTTP methods
- Using `POST` for everything, which removes safety and idempotency signals
- Returning `200` with an error payload
- Breaking responses by renaming fields without a new version
- Exposing database IDs and internal structure directly as the public contract
- Forgetting the `Location` header on `201 Created`

!!! tip "Interview tip"
    **Q: What is the difference between `PUT` and `PATCH`?**
    A: `PUT` replaces the full resource at a URL, so sending it twice leaves the same final state. `PATCH` applies a partial change, described either as a set of fields or as a patch document (JSON Patch is one format). A `PATCH` is not guaranteed to be idempotent, so design it so repeated application is safe, or treat it like `POST` for retries.

## Quick recap

- Model resources as nouns; use HTTP methods and status codes for their intended meanings
- Know which methods are safe and idempotent
- Return the status code that matches the outcome
- Version with a URL, header, or query parameter, and keep the choice consistent
- Prefer additive, non-breaking changes; deprecate with a timeline

**See also:** [Pagination, Errors, and Idempotency](pagination-errors-idempotency.md), [API Security](api-security.md), [Alternative Protocols](alternative-protocols.md)
