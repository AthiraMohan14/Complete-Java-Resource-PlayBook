# Spring Boot

Spring Boot turns the Spring Framework into something you can start quickly: auto-configuration, embedded servers, and production-ready features such as health checks. These notes cover the parts interviewers ask about most, from startup and configuration through REST, validation, error handling, observability, and testing.

---

## Topics

### [Boot Basics and Configuration](boot-basics-configuration.md)
**auto-configuration - starters - profiles - @ConfigurationProperties - fat JAR**
How `@SpringBootApplication` wires the context, how auto-configuration decides what to create, and how externalised configuration is bound.

### [Building REST APIs](rest-apis.md)
**@RestController - request mapping - ResponseEntity - content negotiation - HTTP semantics**
Mapping HTTP verbs to handler methods, binding request data, and returning the right status codes and bodies.

### [Validation](validation.md)
**Jakarta Bean Validation - @Valid - @Validated - custom constraints - method validation**
Declaring constraints on DTOs and parameters, triggering validation, and writing custom validators.

### [Exception Handling](exception-handling.md)
**@RestControllerAdvice - @ExceptionHandler - ProblemDetail - RFC 9457**
Turning exceptions into consistent, standards-based error responses without leaking internals.

### [Actuator and API Documentation](actuator-and-api-docs.md)
**health - metrics - Micrometer - custom health indicators - springdoc - OpenAPI**
Exposing operational endpoints safely, adding custom health and metrics, and generating API docs from code.

### [HTTP Clients and Testing](http-clients-and-testing.md)
**RestClient - WebClient - OpenFeign - retries - @SpringBootTest - slice tests - Testcontainers**
Calling other services with timeouts and retries, and testing Spring Boot applications at the right level of scope.

---

**See also:** [Spring Core](../08-spring-core/index.md) | [Security](../10-security/index.md) | [Testing](../11-testing/index.md)
