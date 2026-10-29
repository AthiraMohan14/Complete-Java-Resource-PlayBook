# Exception Handling in Spring Boot

Exception handling in a REST API decides what the client sees when something goes wrong. A good design returns a consistent, machine-readable error body with the right status code, and hides internal details. Interviewers ask about this to test whether you can keep controllers clean and errors predictable.

## Core concepts

### @ExceptionHandler and @RestControllerAdvice

`@ExceptionHandler` marks a method that handles one or more exception types. Placed inside a controller, it applies only to that controller. Placed on a class annotated with `@RestControllerAdvice` (or `@ControllerAdvice`), it applies globally.

```java
import java.net.URI;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

class OrderNotFoundException extends RuntimeException {
    OrderNotFoundException(long id) {
        super("Order " + id + " was not found");
    }
}

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail handleNotFound(OrderNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Order not found");
        problem.setType(URI.create("https://example.com/problems/order-not-found"));
        return problem;
    }
}
```

### ProblemDetail and RFC 9457

`ProblemDetail` is Spring Framework's implementation of RFC 9457 ("Problem Details for HTTP APIs"), which replaces RFC 7807. It defines standard fields: `type`, `title`, `status`, `detail`, and `instance`. You can add your own properties. Returning `ProblemDetail` gives clients a predictable shape, and the response uses the `application/problem+json` media type.

Spring Boot 3 can apply `ProblemDetail` to Spring MVC's own exceptions (for example, a malformed body) when you set `spring.mvc.problemdetails.enabled=true`.

### Extending ResponseEntityExceptionHandler

`ResponseEntityExceptionHandler` is a base class that already handles Spring MVC's standard exceptions (such as `MethodArgumentNotValidException` and `HttpMessageNotReadableException`) and returns `ProblemDetail` bodies. Extend it, then add your own handlers, to avoid rewriting the defaults.

```java
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
class GlobalHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(IllegalStateException.class)
    ResponseEntity<Object> handleConflict(IllegalStateException ex, WebRequest request) {
        return handleExceptionInternal(ex, null, new HttpHeaders(),
                org.springframework.http.HttpStatus.CONFLICT, request);
    }
}
```

`handleExceptionInternal` is the hook the base class uses to build every error response, so calling it keeps your errors consistent with the framework's.

### Choosing the right status

| Situation | Status |
|---|---|
| Malformed JSON or bad parameter type | `400 Bad Request` |
| Failed validation | `400 Bad Request` (sometimes `422`, if your API uses it) |
| Not authenticated | `401 Unauthorized` |
| Authenticated but not allowed | `403 Forbidden` |
| Resource does not exist | `404 Not Found` |
| State conflict (duplicate, version mismatch) | `409 Conflict` |
| Unexpected server fault | `500 Internal Server Error` |

Authentication and authorisation failures are usually handled by Spring Security's filters, not by your advice class. See [Spring Security Authorisation](../10-security/spring-security-authorisation.md).

### Field-level validation errors

Clients need to know which field failed, not just that something did. Add field errors to the `ProblemDetail` as a custom property. Use this handler instead of extending `ResponseEntityExceptionHandler` for `MethodArgumentNotValidException`, because two advice classes handling the same exception is a source of confusion.

```java
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
class ValidationErrorHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail handleInvalid(MethodArgumentNotValidException ex) {
        Map<String, String> fields = ex.getBindingResult().getFieldErrors().stream()
                .collect(Collectors.toMap(e -> e.getField(), e -> e.getDefaultMessage(), (a, b) -> a));

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.BAD_REQUEST, "One or more fields are invalid");
        problem.setTitle("Validation failed");
        problem.setProperty("fields", fields);
        return problem;
    }
}
```

The merge function `(a, b) -> a` keeps the first message when one field has several violations, so `toMap` does not throw on duplicate keys.

### Logging without leaking

Log the full exception on the server, including a correlation or trace ID, and return that ID to the client so support can find the log line. Keep the response body generic for `500` errors. Log `4xx` responses at a lower level, because bad input from clients is expected traffic, not a server fault.

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
class ServerErrorHandler {

    private static final Logger log = LoggerFactory.getLogger(ServerErrorHandler.class);

    @ExceptionHandler(RuntimeException.class)
    ProblemDetail handleUnexpected(RuntimeException ex) {
        String errorId = java.util.UUID.randomUUID().toString();
        log.error("unhandled error {}", errorId, ex);
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred. Reference: " + errorId);
        problem.setTitle("Internal error");
        return problem;
    }
}
```

In production, use the trace ID from the tracing library rather than a random UUID, so the reference links directly to the trace. Tests for these responses fit the MockMvc approach in [API Testing and Code Coverage](../11-testing/api-testing-and-coverage.md).

### A base exception that carries its HTTP status

Throwing a domain exception from deep in the service layer should not require the service to know about HTTP. A common middle ground is an abstract base exception that stores the status it should map to. The advice class then needs one handler for the whole family, and each subclass only decides its status.

```java
import org.springframework.http.HttpStatus;

abstract class ApiException extends RuntimeException {

    private final HttpStatus status;

    protected ApiException(HttpStatus status, String message) {
        super(message);
        this.status = status;
    }

    HttpStatus status() {
        return status;
    }
}

class MissingOrderException extends ApiException {
    MissingOrderException(long orderId) {
        super(HttpStatus.NOT_FOUND, "Order " + orderId + " was not found");
    }
}

class PaymentDeclinedException extends ApiException {
    PaymentDeclinedException(String reason) {
        super(HttpStatus.PAYMENT_REQUIRED, "Payment declined: " + reason);
    }
}
```

```java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
class ApiExceptionAdvice {

    @ExceptionHandler(ApiException.class)
    ResponseEntity<ProblemDetail> handle(ApiException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(ex.status(), ex.getMessage());
        return ResponseEntity.status(ex.status()).body(problem);
    }
}
```

The status is set in one place, next to the exception that knows what went wrong. A simpler alternative is `@ResponseStatus` on the exception class itself, but that gives you no way to read the status in code, such as for logging.

### @ExceptionHandler on a single controller

A handler method inside a controller applies only to that controller's requests. Use it for an error that only one endpoint produces, and keep it out of the global advice so the global mapping stays small.

```java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

record RefundRequest(String orderId, long cents) { }

class RefundLimitExceededException extends RuntimeException {
    RefundLimitExceededException(long cents) {
        super("Refund of " + cents + " exceeds the allowed limit");
    }
}

@RestController
@RequestMapping("/api/refunds")
class RefundController {

    @PostMapping
    String create(@RequestBody RefundRequest request) {
        if (request.cents() > 100_000) {
            throw new RefundLimitExceededException(request.cents());
        }
        return "accepted";
    }

    // Applies only to RefundController. Other controllers never reach it.
    @ExceptionHandler(RefundLimitExceededException.class)
    ProblemDetail limitExceeded(RefundLimitExceededException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.UNPROCESSABLE_ENTITY, ex.getMessage());
    }
}
```

When a controller and an advice both handle the same exception type, the controller's method wins. The advice is consulted only for exceptions the controller does not handle. Use this ordering on purpose: put the endpoint-specific wording in the controller and the general rule in the advice.

### An error DTO with custom fields

`ProblemDetail` covers the RFC 9457 fields, and you can add more with `setProperty`. Some teams already have a client that expects its own error shape, though, and then a plain record is simpler to keep stable. Here the record includes a timestamp, the request path, and optional field errors. Empty field errors are left out of the JSON.

```java
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

record ApiError(
        int status,
        String message,
        Instant timestamp,
        String path,
        @JsonInclude(JsonInclude.Include.NON_EMPTY) Map<String, String> fieldErrors) {
}

@RestControllerAdvice
class LegacyShapeAdvice {

    @ExceptionHandler(MissingOrderException.class)
    ResponseEntity<ApiError> notFound(MissingOrderException ex, HttpServletRequest request) {
        ApiError body = new ApiError(HttpStatus.NOT_FOUND.value(), ex.getMessage(),
                Instant.now(), request.getRequestURI(), Map.of());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }
}
```

Choose one error shape for the whole API and document it. A new API should normally start with `ProblemDetail`, because clients and tooling already understand it. Use a custom DTO when a fixed contract must be kept.

## How it works / Step by step

1. A controller or service throws an exception.
2. Spring searches for an `@ExceptionHandler` in the controller first, then in `@RestControllerAdvice` beans.
3. The most specific matching exception type wins.
4. The handler builds a response, usually a `ProblemDetail`, and Spring writes it with the status you set.
5. Exceptions that no handler matches become `500` responses. Those should be logged with a correlation ID and returned without internal detail.

When several advice classes match, use `@Order` to control precedence.

## Common pitfalls

- Catching `Exception` in one broad handler. It hides bugs and maps every failure to the same status.
- Returning `200 OK` with `{"error": "..."}` in the body. Clients and monitoring tools treat it as success.
- Exposing stack traces, SQL, class names, or hostnames in the response body.
- Mixing error body shapes across controllers, so clients need special cases.
- Logging the error at the wrong level (for example, `ERROR` for every `404`).
- Writing try/catch in every controller method instead of centralising the mapping.

!!! tip "Interview tip"
    **Q: How do you return consistent errors across a large API?**
    Map domain exceptions to HTTP status codes in one `@RestControllerAdvice`, return RFC 9457 `ProblemDetail` bodies, and extend `ResponseEntityExceptionHandler` so framework exceptions follow the same format. Log server-side detail, but return only what the client needs.

## Quick recap

- `@RestControllerAdvice` with `@ExceptionHandler` centralises error mapping.
- `ProblemDetail` implements RFC 9457, which replaces RFC 7807.
- Extend `ResponseEntityExceptionHandler` to keep framework errors in the same format.
- Use accurate status codes; never return `200` for an error.
- Never leak internal details in error bodies.

**See also:** [Building REST APIs](rest-apis.md) | [Validation](validation.md) | [Security Headers and CORS](../10-security/cors-csrf-tls-headers.md)
