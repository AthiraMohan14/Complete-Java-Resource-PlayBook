# Validation in Spring Boot

Validation checks that incoming data meets your rules before it reaches business logic. Spring Boot uses Jakarta Bean Validation (the `jakarta.validation` package), which replaced `javax.validation` in Spring Boot 3. Interviewers ask about this to see whether you know where validation happens, what exception each path throws, and why service-layer checks still matter.

## Core concepts

### Constraint annotations

Constraints sit on fields, record components, or parameters. Common ones are `@NotNull`, `@NotBlank` (non-null and at least one non-whitespace character), `@NotEmpty`, `@Email`, `@Pattern`, `@Min`, `@Max`, and `@Size`.

```java
import jakarta.validation.constraints.*;

public record CreateUserRequest(
        @NotBlank @Size(max = 80) String name,
        @NotBlank @Email String email,
        @Min(18) int age,
        @Pattern(regexp = "^[A-Z]{2}\\d{4}$") String memberCode) {}
```

Annotations on record components are propagated to the canonical constructor's parameters, which is where Bean Validation checks them.

### @Valid and @Validated

Add `@Valid` to a `@RequestBody` parameter to validate it when the request is bound. If it fails, Spring throws `MethodArgumentNotValidException`, which turns into a `400` by default.

```java
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
class UserController {

    @PostMapping
    ResponseEntity<Void> create(@Valid @RequestBody CreateUserRequest request) {
        // request is already valid here
        return ResponseEntity.accepted().build();
    }
}
```

`@Validated` (from Spring) does two jobs. Placed on a class, it enables method validation for constraints on that class's parameters. Placed on a parameter with a group, it selects which validation groups to apply.

```java
import jakarta.validation.constraints.Min;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

@Validated
@RestController
@RequestMapping("/api/items")
class ItemController {

    @GetMapping("/{id}")
    String byId(@Min(1) @PathVariable long id) {
        return "item " + id;
    }
}
```

Validation groups let one DTO have different rules for create and update:

```java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Null;

public interface OnCreate {}
public interface OnUpdate {}

public record ProductRequest(
        @Null(groups = OnCreate.class) Long id,
        @NotBlank(groups = {OnCreate.class, OnUpdate.class}) String name) {}
```

```java
// in a controller method
// void save(@Validated(OnCreate.class) @RequestBody ProductRequest request) { ... }
```

### Method validation

`MethodValidationPostProcessor` (auto-configured by Spring Boot when a validator is present) adds validation to any Spring bean annotated with `@Validated`. This is the way to protect service methods, not only controllers. Method validation signals failures with `ConstraintViolationException`. In newer Spring Framework versions (6.1 and later), controller method-parameter constraints can surface as `HandlerMethodValidationException` instead, so check which one your version throws before writing a handler for it.

### Custom constraints

A custom constraint is an annotation linked to a validator class.

```java
import jakarta.validation.Constraint;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import jakarta.validation.Payload;
import java.lang.annotation.*;
import java.util.Set;

@Documented
@Constraint(validatedBy = AllowedCountryValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.RECORD_COMPONENT})
@Retention(RetentionPolicy.RUNTIME)
@interface AllowedCountry {
    String message() default "country is not supported";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

class AllowedCountryValidator implements ConstraintValidator<AllowedCountry, String> {
    private static final Set<String> ALLOWED = Set.of("IN", "US", "GB");

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        return value == null || ALLOWED.contains(value); // null is handled by @NotNull
    }
}
```

Keep validators stateless and free of I/O. A check that needs a database lookup belongs in the service layer.

### Messages

Default messages come from `ValidationMessages.properties` and can be localised. Override the message on the annotation for a short, clear default, and keep user-facing wording out of validator code.

## How it works / Step by step

1. A request is bound to the method parameter (for example, JSON to a record via Jackson).
2. Because `@Valid` is present, the validator checks every constraint on the object graph.
3. If any constraint fails, Spring throws `MethodArgumentNotValidException` (for request bodies) or `ConstraintViolationException` or `HandlerMethodValidationException` (for method and parameter constraints).
4. Your exception handler, or Spring's default handling, turns this into a `400` response. See [Exception Handling](exception-handling.md).

Use `@Valid` on nested objects to validate the object graph, because validation does not descend into fields unless you ask it to.

## Common pitfalls

- Forgetting `@Valid`. Constraints are ignored silently, so bad data gets through.
- Using `@NotNull` on strings where `@NotBlank` is what you mean. `"   "` passes `@NotNull`.
- Relying only on controller validation. Services called from other entry points (messages, schedulers) also need checks.
- Putting database checks (for example, "email already exists") in a constraint. Those belong in the service, with a `409 Conflict` response.
- Validating the same rules in two places that drift apart.
- Leaking internal field names or stack traces in the error response.

!!! tip "Interview tip"
    **Q: Where would you validate an order request, and why not just in the controller?**
    Validate shape and format at the boundary with `@Valid` (cheap, no I/O). Validate business rules in the service, because those depend on state (stock, limits, ownership), and the service is reachable from more than one entry point. The controller is a convenience layer, not the only gate.

## Quick recap

- Use Jakarta constraints (`jakarta.validation.*`) on DTO fields and record components.
- `@Valid` triggers request-body validation; `@Validated` enables method validation and groups.
- Method validation protects service beans too, and throws its own exception types.
- Write custom constraints as an annotation plus a stateless validator.
- Keep stateful business rules in the service layer.

**See also:** [Building REST APIs](rest-apis.md) | [Exception Handling](exception-handling.md) | [Boot Basics and Configuration](boot-basics-configuration.md)
