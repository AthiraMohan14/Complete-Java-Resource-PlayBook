# Documenting APIs with OpenAPI and springdoc

OpenAPI is a standard, machine-readable format for describing HTTP APIs. It was formerly called Swagger. A spec lists the paths, methods, parameters, request and response bodies, status codes, and security schemes. Interviewers ask about it to see whether you treat the API contract as a product, and whether your documentation can stay in step with the code.

## Core concepts

### What the spec contains

An OpenAPI document is a JSON or YAML file with a few top-level sections:

- `info` gives the title, version, and description.
- `servers` lists base URLs, such as production and local development.
- `paths` maps each URL and method to an operation, its parameters, and its responses.
- `components` holds reusable schemas, parameters, responses, and security schemes.

Tools read the spec to render interactive documentation, generate client libraries, and test requests. The spec can be written first (design-first) or generated from the code (code-first). Spring projects usually take the code-first route with springdoc.

### Setup with springdoc-openapi

Add `springdoc-openapi-starter-webmvc-ui`. Use the 2.x line for Spring Boot 3. With the dependency on the classpath, the application serves:

- `/v3/api-docs`: the spec as JSON
- `/v3/api-docs.yaml`: the spec as YAML
- `/swagger-ui/index.html`: an interactive UI where you can send requests

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version><!-- use the 2.x release for Spring Boot 3 --></version>
</dependency>
```

### Annotating operations

springdoc reads the controller mappings automatically. Annotations add the descriptions that the code cannot express.

```java
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "Users", description = "Read and manage user accounts")
public class UserDocController {

    public record UserView(long id, String name) {}

    @GetMapping("/{id}")
    @Operation(summary = "Get a user", description = "Returns one user by ID")
    @ApiResponse(responseCode = "200", description = "User found")
    @ApiResponse(responseCode = "404", description = "No user with this ID")
    public ResponseEntity<UserView> get(
            @Parameter(description = "User identifier", example = "123") @PathVariable long id) {
        return ResponseEntity.ok(new UserView(id, "Sample user"));
    }
}
```

The main annotations, and what they add to the spec:

| Annotation | Purpose |
|---|---|
| `@Tag` | Groups operations under one heading in the UI |
| `@Operation` | Summary, description, and deprecation flag for one operation |
| `@Parameter` | Description and example for a path, query, or header parameter |
| `@ApiResponse` | A documented status code and what it means; can include an example body |
| `@Schema` | Description, example, and constraints for a model or field |
| `@SecurityRequirement` | Which security scheme protects an operation |

Use `@Operation(deprecated = true)` to mark an operation as deprecated in the spec. The Java `@Deprecated` annotation is for the compiler and callers in code, not for the published contract.

Do not put annotations on a `@RequestBody` parameter to describe its example. The example belongs on the schema, which the next section covers.

### Documenting models

`@Schema` on a model's fields adds descriptions, examples, and constraints. It works on record components as well as on classes.

```java
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "A request to create a user")
public record CreateUserRequest(
        @Schema(description = "Full name", example = "Jane Doe", minLength = 1, maxLength = 100)
        String name,

        @Schema(description = "Contact address", example = "jane@example.com")
        String email) {
}
```

Bean Validation annotations such as `@NotBlank` and `@Email` are also reflected in the schema, so the documented constraints match what the code enforces.

### Example responses with @ExampleObject

A schema shows the shape of a body. An example shows a realistic instance, and reviewers and client developers use examples to understand the contract quickly. `@ExampleObject` attaches one or more examples to a response's `@Content`, and each example can carry a name and a summary so the UI lists them separately.

```java
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

record InvoiceView(long id, String status, long totalCents) { }

@RestController
class InvoiceApi {

    @Operation(summary = "Fetch an invoice")
    @ApiResponse(
            responseCode = "200",
            description = "Invoice found",
            content = @Content(
                    mediaType = "application/json",
                    schema = @Schema(implementation = InvoiceView.class),
                    examples = {
                            @ExampleObject(name = "paid", summary = "A settled invoice",
                                    value = "{\"id\": 42, \"status\": \"PAID\", \"totalCents\": 1999}"),
                            @ExampleObject(name = "open", summary = "An invoice awaiting payment",
                                    value = "{\"id\": 43, \"status\": \"OPEN\", \"totalCents\": 4500}")
                    }))
    @GetMapping("/api/invoices/{id}")
    InvoiceView get(@PathVariable long id) {
        return new InvoiceView(id, "OPEN", 4500);
    }
}
```

Three points about examples:

- They are documentation, not tests. Springdoc does not check that the example matches the schema, so keep examples in step with the code by generating them from a real response where you can.
- Use fake data only. An example is public once the UI is published, so it must not contain real customer details, tokens, or internal identifiers.
- Give each example a name when a response has more than one meaningful case, such as a paid and an open invoice. Clients then see the variants side by side instead of guessing.

### Configuring paths and the UI

Most defaults are fine. The properties below control where the documents are served and which paths are included:

```yaml
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
    operations-sorter: alpha
  paths-to-match: /api/**
  paths-to-exclude: /internal/**
```

Keep internal and administrative paths out of the public spec. Hiding them in the UI is not enough, so exclude them in configuration and protect the UI itself in production.

### Global information and bearer security

A bean that builds the `OpenAPI` object sets the title, servers, and security scheme for the whole API. Add a `SecurityRequirement` to the operations that need a token.

```java
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI orderApi() {
        return new OpenAPI()
                .info(new Info().title("Order API").version("1.0.0")
                        .description("Places and tracks orders"))
                .components(new Components().addSecuritySchemes("bearerAuth",
                        new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")))
                .addSecurityItem(new SecurityRequirement().addList("bearerAuth"));
    }
}
```

`addSecurityItem` applies the requirement to every operation. For a mixed API, leave it off and add `@SecurityRequirement(name = "bearerAuth")` to the protected operations instead.

### Documenting error responses

Document the error bodies as carefully as the success bodies. If errors use Problem Details (see [Pagination, Errors, and Idempotency](pagination-errors-idempotency.md)), describe that schema once and reference it from each `@ApiResponse` that can fail. Clients generate their error handling from these entries, so a missing `401` or `409` is a bug in the contract.

### Generating clients and servers

The OpenAPI Generator tool reads the spec and writes client code. Point it at the running service's spec, or at a file in the repository, and pick a generator:

```bash
openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g typescript-axios \
  -o generated/orders-client
```

Generated clients track the contract, so a breaking change shows up in the client build rather than in production. Generate into a separate directory, and commit the spec, not hand edits to the output.

## Code-first versus design-first

| Aspect | Code-first (springdoc) | Design-first (spec written before code) |
|---|---|---|
| Source of truth | The controllers and models | The OpenAPI file |
| Drift risk | Low, because the spec comes from code | Higher, unless the code is checked against the spec |
| Review of the design | Happens after the code exists | Happens before any code is written |
| Good fit | Internal services, quick iteration | Public APIs with many consumers |

Many teams combine them: design the public surface in a spec, review it, and check the implementation against it in tests.

## How it works

1. At startup, springdoc scans the controllers, request and response types, and annotations.
2. It builds the OpenAPI model and serves it at the configured paths.
3. The UI and generators read that document; nothing else needs to change.

## Common pitfalls

- Exposing internal or administrative endpoints in the public spec.
- Including real secrets, tokens, or personal data in examples.
- Documenting only the success response, so clients never handle `401`, `403`, or `409`.
- Marking operations deprecated only in prose, so no tool or client reports it.
- Writing the spec by hand and letting it drift from the code.
- Leaving the Swagger UI open in production without any protection.

!!! tip "Interview tip"
    **Q: Code-first or design-first OpenAPI, and why?**
    For an internal service that changes often, code-first keeps the spec true with little effort. For a public API with many consumers, design-first lets the team review the contract before building it, and generated clients follow the same contract. I would say which I chose and what check keeps the spec honest.

## Quick recap

- OpenAPI describes paths, operations, schemas, and security; springdoc generates it from Spring code.
- Annotate operations and models for descriptions, examples, and status codes, and document error responses too.
- Add a bearer security scheme for protected APIs, and keep internal paths out of the public spec.
- Generate clients from the spec so contract changes break the build, not production.
- Choose code-first for speed or design-first for public contracts, and check the spec in tests.

**See also:** [REST Principles and Versioning](rest-principles-versioning.md), [API Security](api-security.md), [Pagination, Errors, and Idempotency](pagination-errors-idempotency.md)
