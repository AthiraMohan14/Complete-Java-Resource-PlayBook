# Pagination, Errors, and Idempotency

Three everyday API problems: returning large lists without overloading the server, reporting failures in a form clients can act on, and making retried writes safe. Interviewers ask about all three because each one shows up in production as duplicate charges, timeouts, or confused clients.

## Core concepts

### Offset-based pagination

Offset pagination uses `?page=3&size=20` or `?offset=40&limit=20`. It is simple and lets clients jump to any page. The database skips the offset rows, so deep pages get slower. Rows inserted or deleted between requests can also cause items to appear twice or be missed.

### Cursor-based (keyset) pagination

Keyset pagination remembers the last item seen and asks for the rows after it. The **seek method** is the SQL form:

```sql
-- First page
SELECT id, created_at, total
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Next page, given the last row returned: (created_at, id) = (:lastCreatedAt, :lastId)
SELECT id, created_at, total
FROM orders
WHERE (created_at, id) < (:lastCreatedAt, :lastId)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The index on `(created_at, id)` lets the database jump straight to the position. Include a unique tie-breaker (`id`) so the ordering is total. Keyset pagination cannot jump to page 50 directly, which is the trade-off.

Clients receive an opaque cursor, not the raw key. A simple encoder:

```java
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public final class Cursor {

    private Cursor() {
    }

    public static String encode(long createdAtEpochMillis, long id) {
        String raw = createdAtEpochMillis + ":" + id;
        return Base64.getUrlEncoder().withoutPadding()
                .encodeToString(raw.getBytes(StandardCharsets.UTF_8));
    }

    public static long[] decode(String cursor) {
        String raw = new String(Base64.getUrlDecoder().decode(cursor), StandardCharsets.UTF_8);
        String[] parts = raw.split(":");
        if (parts.length != 2) {
            throw new IllegalArgumentException("invalid cursor");
        }
        return new long[] {Long.parseLong(parts[0]), Long.parseLong(parts[1])};
    }
}
```

An opaque cursor lets you change the underlying key later without breaking clients. Validate it on decode, because a malformed cursor is client input.

### Filtering, sorting, and partial responses

- **Filtering:** exact matches (`status=PAID`), ranges (`createdAfter=...`), and patterns (`name=ab*`). Whitelist the fields you allow.
- **Sorting:** single or multiple fields, such as `sort=-createdAt,total`. Whitelist sortable fields and back each with an index.
- **Partial responses (sparse fieldsets):** `fields=id,status` returns only those fields, which reduces payload size for list screens.
- **Batch operations:** accept a list of items in one request and return per-item results, so one bad item does not fail the whole batch silently.

### Problem Details for consistent errors

Clients should not have to parse a different error format from each endpoint. **Problem Details** (RFC 9457, which replaces RFC 7807) defines a standard JSON body with fields such as `type`, `title`, `status`, `detail`, and `instance`. You can add extension members, such as a list of invalid fields.

Spring Framework 6 provides a `ProblemDetail` class. Here is a handler that maps a missing resource to a Problem Details body:

```java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiErrorHandler {

    public static class OrderNotFoundException extends RuntimeException {
        public OrderNotFoundException(long id) {
            super("Order " + id + " was not found");
        }
    }

    @ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(OrderNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Order not found");
        problem.setType(java.net.URI.create("https://example.com/problems/order-not-found"));
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(problem);
    }
}
```

For validation errors, add a property with a list of field-level messages so the client knows which input to fix. Do not leak stack traces or internal class names in the body.

### Idempotency

A request is **idempotent** if repeating it has the same effect as one call. `GET`, `PUT`, and `DELETE` are idempotent by definition. `POST` is not, and that matters because networks time out after the server has already acted. The client does not know whether the first attempt worked, so it retries, and a naive server creates a second order or charges a card twice.

The standard fix is an **idempotency key**. The client generates a unique key (a UUID) per logical operation and sends it in a header such as `Idempotency-Key`. The server:

1. Looks up the key.
2. If it has a stored result, returns that result without repeating the work.
3. If not, performs the work and stores the key with the result, atomically with the business change.
4. Rejects a reused key that comes with a different request body.

A minimal in-memory sketch of the lookup. It shows the shape, not production safety:

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

public class IdempotencyStore {

    private final Map<String, String> responses = new ConcurrentHashMap<>();

    public String execute(String idempotencyKey, Supplier<String> action) {
        // Runs the action at most once per key, while this map holds the key
        return responses.computeIfAbsent(idempotencyKey, k -> action.get());
    }
}
```

This is not enough for production. The store must survive restarts and be shared across instances, so use a database table with a unique constraint on the key, written in the same transaction as the business change. Also, `computeIfAbsent` runs the action while holding a map lock, which is unsuitable for slow remote calls.

### Preventing duplicate processing and retry-safe design

Idempotency keys cover client retries. Consumers of queues need the same protection, because message delivery is usually at-least-once. Record processed message IDs, or design handlers so that re-processing is harmless (an upsert, or a state check before the change).

When clients retry, use **exponential backoff with jitter** so many clients do not retry in lockstep. Retry only errors that are plausibly transient (timeouts, `503`, `429` with a `Retry-After` hint), and not validation errors.

### Paging in Spring MVC

Spring Data binds `page`, `size`, and `sort` query parameters to a `Pageable`. `@PageableDefault` sets the defaults. Return a `Page` when clients need the total count, or a `Slice` when they only need to know whether another page exists.

```java
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderPageController {

    public record OrderSummary(long id, String status) {}

    @GetMapping
    public Page<OrderSummary> list(@PageableDefault(size = 20, sort = "id") Pageable pageable) {
        return Page.empty(pageable);   // replace with a repository query that maps to OrderSummary
    }
}
```

Spring Data recommends against serialising a `Page` object directly, because its JSON shape is not a stable contract. Map it to your own response record, with fields such as `items`, `page`, `size`, `totalElements`, and `hasNext`, or use Spring HATEOAS's `PagedModel`. Then a later change inside Spring Data does not change your API.

## How it works

1. A client requests a page and receives items plus a next cursor.
2. The client sends the cursor back; the server seeks to that position using an index.
3. Errors return a Problem Details body with a status that matches the cause.
4. A client sends `POST` with an `Idempotency-Key`. The server stores the outcome.
5. A retry with the same key returns the stored outcome rather than repeating the work.

## Common pitfalls

- Using offset pagination on large, changing tables, which skips and duplicates rows
- Exposing raw database keys in cursors, so changing the schema breaks clients
- Error bodies that differ by endpoint, or that leak stack traces
- Idempotency keys stored in memory only, or without a unique constraint
- Reusing an idempotency key with a different payload and silently returning the old result
- Retrying non-transient errors such as validation failures

!!! tip "Interview tip"
    **Q: A client times out on `POST /payments` and retries. How do you avoid charging twice?**
    A: The client sends the same `Idempotency-Key` on every retry. The server stores the key with the outcome in the same transaction as the payment record. On a retry it returns the stored result instead of charging again, and it rejects a reused key with a different body.

## Quick recap

- Keyset pagination scales better than offset; cursors should be opaque and validated
- Use Problem Details (RFC 9457) for one consistent error format
- `POST` needs an idempotency key to be safe to retry
- Store idempotency records durably, with a unique constraint, in the business transaction
- Retry only transient failures, with backoff and jitter

**See also:** [REST Principles and Versioning](rest-principles-versioning.md), [API Security](api-security.md), [Alternative Protocols](alternative-protocols.md)
