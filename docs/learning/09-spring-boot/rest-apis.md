# Building REST APIs with Spring Boot

A REST API maps HTTP verbs and URLs to controller methods, and turns request data into Java values and results back into HTTP responses. Interviewers ask about this to check that you understand HTTP semantics (idempotency, status codes, content types), not only the annotations.

## Core concepts

### @RestController and request mapping

`@RestController` is `@Controller` plus `@ResponseBody`: every return value is written to the response body, typically as JSON. The `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, and `@DeleteMapping` annotations are shortcuts for `@RequestMapping` with a fixed method.

```java
import java.net.URI;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

public record CreateOrderRequest(String item, int quantity) {}
public record OrderResponse(long id, String item, String status) {}

@RestController
@RequestMapping("/api/orders")
class OrderController {

    @GetMapping("/{id}")
    ResponseEntity<OrderResponse> get(@PathVariable long id) {
        return ResponseEntity.ok(new OrderResponse(id, "book", "NEW"));
    }

    @GetMapping
    List<OrderResponse> list(@RequestParam(defaultValue = "NEW") String status) {
        return List.of(new OrderResponse(1L, "book", status));
    }

    @PostMapping
    ResponseEntity<OrderResponse> create(@RequestBody CreateOrderRequest request) {
        OrderResponse created = new OrderResponse(42L, request.item(), "NEW");
        return ResponseEntity.created(URI.create("/api/orders/42")).body(created);
    }

    @DeleteMapping("/{id}")
    ResponseEntity<Void> delete(@PathVariable long id) {
        return ResponseEntity.noContent().build();
    }
}
```

### Binding request data

| Annotation | Reads from | Notes |
|---|---|---|
| `@PathVariable` | URL template (`/orders/{id}`) | Required by default |
| `@RequestParam` | Query string or form field | `defaultValue`, `required = false` |
| `@RequestHeader` | HTTP header | Use for `Authorization`, `If-Match`, and similar |
| `@RequestBody` | Request body | Deserialised by Jackson for JSON |
| `@ResponseBody` | Return value | Implicit with `@RestController` |

```java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

@RestController
class AuditController {
    @GetMapping("/whoami")
    String whoAmI(@RequestHeader(value = "X-Request-Id", required = false) String requestId) {
        return requestId == null ? "no request id" : requestId;
    }
}
```

### HttpEntity, ResponseEntity, and status codes

`ResponseEntity<T>` lets you set the status, headers, and body together. Pick status codes that match the outcome:

- `200 OK` for a successful read or update
- `201 Created` with a `Location` header after a create (`ResponseEntity.created(uri)`)
- `204 No Content` after a delete with no body
- `400 Bad Request` for invalid input, `404 Not Found` for an unknown resource, `409 Conflict` for a state conflict

`HttpEntity` is the parent type of `ResponseEntity`, and also the type you use to send headers and a body from a client.

### HTTP semantics that interviewers probe

- `GET` is safe and cacheable. `PUT` and `DELETE` are idempotent (repeating them gives the same server state). `POST` is neither in general. `PATCH` is not guaranteed to be idempotent.
- `PUT` replaces the resource; `PATCH` changes parts of it.
- Use `@PatchMapping` with a DTO that only carries the fields you accept to change, and document the semantics (for example, JSON Merge Patch).

### Content negotiation

Spring picks a message converter using the request `Accept` header and the method's `produces` attribute. Jackson handles JSON by default when it is on the classpath. XML needs an extra converter such as `jackson-dataformat-xml`.

```java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@PostMapping(path = "/api/orders", consumes = "application/json", produces = "application/json")
ResponseEntity<OrderResponse> createJson(@RequestBody CreateOrderRequest request) {
    return ResponseEntity.status(201).body(new OrderResponse(43L, request.item(), "NEW"));
}
```

A request with an unsupported media type gets `415 Unsupported Media Type`; one with an unacceptable `Accept` header gets `406 Not Acceptable`.

## How it works / Step by step

1. The `DispatcherServlet` receives the request and finds the handler method by path, verb, and media type.
2. Argument resolvers fill parameters (`@PathVariable`, `@RequestBody`, and so on). Jackson deserialises the body.
3. Validation runs if requested (see [Validation](validation.md)).
4. The method runs, and its return value goes through a message converter (Jackson for JSON).
5. Exceptions are routed to exception handlers (see [Exception Handling](exception-handling.md)).

## Common pitfalls

- Returning JPA entities directly. This exposes internal fields, can trigger lazy-loading errors during serialisation, and couples your API to your schema. Map to DTOs.
- Returning `200 OK` for a create, or `200` with an error message in the body.
- Assuming `PUT` is safe to retry without checking the semantics. It is idempotent by definition, but the server still has to implement it that way.
- Putting business logic in controllers. Keep controllers thin: parse, validate, delegate, map the response.
- Forgetting that `@RequestParam` is required unless you say otherwise, which turns a missing optional value into a `400`.
- Using verbs in URLs (`/createOrder`). Name resources with nouns and let the HTTP verb express the action.

!!! tip "Interview tip"
    **Q: Why is `PUT` idempotent but `POST` is not?**
    `PUT` targets a known resource URL and sets its full state, so sending the same request twice leaves the same result. `POST` usually asks the server to create a new resource each time, so repeating it can create duplicates. Clients that need safe retries of `POST` use an idempotency key sent in a header.

## Quick recap

- Controllers map verbs and paths to methods; `@RestController` writes return values to the body.
- Bind inputs with `@PathVariable`, `@RequestParam`, `@RequestHeader`, and `@RequestBody`.
- Use `ResponseEntity` to return the correct status, headers, and body.
- Know which verbs are safe and idempotent, and design `PUT` and `PATCH` accordingly.
- Use DTOs, not entities, at the API boundary.

**See also:** [Validation](validation.md) | [Exception Handling](exception-handling.md) | [Actuator and API Documentation](actuator-and-api-docs.md)
