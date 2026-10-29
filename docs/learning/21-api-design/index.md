# API Design and REST Best Practices

An API is a contract that other teams and clients depend on. This section covers how to design HTTP APIs that are predictable, safe to retry, easy to evolve, and secure, along with the main alternatives to REST.

---

## Topics

### [REST Principles and Versioning](rest-principles-versioning.md)
**resources - HTTP methods - status codes - content negotiation - versioning**
Model APIs around resources, use HTTP semantics correctly, and change them without breaking clients.

### [Pagination, Errors, and Idempotency](pagination-errors-idempotency.md)
**offset - keyset - Problem Details (RFC 9457) - idempotency keys - retries**
Return large collections safely, report failures in a consistent format, and make retried writes safe.

### [Alternative Protocols](alternative-protocols.md)
**GraphQL - gRPC - Protocol Buffers - WebSockets - HTTP/2**
Know when a query language, a binary RPC protocol, or a persistent connection fits better than plain REST.

### [API Security](api-security.md)
**tokens - JWT - OAuth 2.0 - rate limiting - CORS - input validation**
Authenticate and authorise callers, limit abuse, and validate everything that comes in.

**See also:** [Part 4 roadmap, section 21](../../resources/full-stack-java-roadmap/part-4-design-interview-projects.md)
