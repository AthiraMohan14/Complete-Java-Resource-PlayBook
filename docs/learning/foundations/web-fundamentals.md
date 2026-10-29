# Web Fundamentals

Web fundamentals cover the HTTP contract that every API depends on: methods, status codes, headers, caching, and the REST style built on them. Interviewers use these topics to check whether you can design an endpoint, pick the right status code, and explain how a request is secured and observed.

## Core concepts

### HTTP methods

Each method states the intent of a request. Two properties matter for design: **safe** (no state change on the server) and **idempotent** (repeating the request leaves the same state as doing it once).

| Method | Purpose | Safe | Idempotent | Typical use |
|--------|---------|------|------------|-------------|
| GET | Read a resource | Yes | Yes | Fetch data |
| HEAD | Same as GET without the body | Yes | Yes | Check existence or metadata |
| OPTIONS | Describe what the server allows | Yes | Yes | CORS preflight |
| POST | Process or create | No | No | Create a resource, submit a form |
| PUT | Replace a resource completely | No | Yes | Full update |
| PATCH | Change part of a resource | No | Not guaranteed | Partial update |
| DELETE | Remove a resource | No | Yes | Delete |

Idempotency is about the resulting state, not the response. A second DELETE may return 404 while the state is still "deleted", so it stays idempotent.

### HTTP status codes

**2xx: success**

- **200 OK**: success with a body.
- **201 Created**: a resource was created; the `Location` header gives its URL.
- **202 Accepted**: the request was accepted for asynchronous processing; it may not be done yet.
- **204 No Content**: success with no body, common after DELETE.
- **206 Partial Content**: a byte range was returned, used for resumable downloads and ranged reads.

**3xx: redirection**

- **301 Moved Permanently**: clients and caches may remember the new location.
- **302 Found** and **307 Temporary Redirect**: temporary. 307 keeps the request method; 302 is often changed to GET by clients.
- **304 Not Modified**: the cached copy is still valid; no body is sent.

**4xx: client error**

- **400 Bad Request**: malformed syntax, such as invalid JSON or a missing required field.
- **401 Unauthorized**: no valid credentials were presented. Despite the name, it means "unauthenticated".
- **403 Forbidden**: the caller is authenticated but lacks permission.
- **404 Not Found**: the resource does not exist, or the server hides its existence.
- **409 Conflict**: the request clashes with current state, for example a duplicate unique key.
- **422 Unprocessable Content** (called Unprocessable Entity in older specs): syntax is fine but the data breaks a business rule.
- **429 Too Many Requests**: rate limit exceeded; often sent with a `Retry-After` header.
- **431 Request Header Fields Too Large**: the headers alone exceed the server limit.

**5xx: server error**

- **500 Internal Server Error**: an unexpected failure on the server.
- **502 Bad Gateway**: a gateway or proxy got an invalid response from upstream.
- **503 Service Unavailable**: temporarily unable to serve, for example during maintenance or overload.
- **504 Gateway Timeout**: the upstream did not answer in time.

Distinguishing 401 from 403, and 400 from 422, is a frequent interview check.

### HTTP headers

Request headers the client sends:

```
Authorization: Bearer <token>        # credentials
Content-Type: application/json       # format of the body being sent
Accept: application/json             # format the client wants back
Accept-Encoding: gzip, deflate       # compression the client understands
If-None-Match: "33a64df551425fcc"    # ETag from a previous response
```

Response headers the server sends:

```
Content-Type: application/json       # format of the body returned
Cache-Control: max-age=3600          # how long caches may keep the response
ETag: "33a64df551425fcc"             # version identifier for the representation
Location: /users/123                 # new resource URL after 201, or redirect target
Set-Cookie: session=abc123           # cookie for the client to store
Access-Control-Allow-Origin: *       # CORS permission for browsers
```

### HTTP caching

`Cache-Control` directives control who may store a response and when it must be checked again:

- `public, max-age=3600`: shared caches may store it for one hour.
- `private, max-age=1800`: only the browser may store it, for 30 minutes.
- `no-cache`: it may be stored, but must be revalidated before reuse.
- `no-store`: never store it; use this for sensitive data.
- `must-revalidate`: once stale, it must not be used without checking.

An **ETag** is a validator. The server returns it; the client sends it back in `If-None-Match`; if the resource is unchanged the server answers 304 with no body, which saves bandwidth.

### REST

REST (Representational State Transfer) is an architectural style, not a protocol. A RESTful API:

1. Separates client and server concerns.
2. Is **stateless**: each request carries everything the server needs, so any instance can handle it.
3. Uses a **uniform interface**: resources are named by URLs and changed through representations (usually JSON), with standard methods.
4. Allows responses to be **cacheable** where appropriate.
5. Works in **layers**, so proxies, gateways, and load balancers can sit in between.
6. Optionally supports **code on demand**, where the server sends executable code to the client. This is rare in APIs.

**Resource naming** uses nouns and plural collections, with methods carrying the verb:

```
GET    /api/orders             list orders
GET    /api/orders/731         read order 731
POST   /api/orders             place a new order
PUT    /api/orders/731         replace order 731
PATCH  /api/orders/731         change the shipping address of order 731
DELETE /api/orders/731         cancel and remove order 731
GET    /api/orders/731/lines   nested collection of line items
GET    /api/lines?sku=SKU-88   filter by query parameter
```

Keep nesting shallow. Two levels is usually enough; deeper paths are better expressed as filters.

**POST idempotency** needs an extra mechanism. Clients send a unique key with the request, commonly in an `Idempotency-Key` header. The server stores the outcome for that key and replays it for a retry instead of creating a duplicate. The header name is a convention rather than a settled standard, so check what an API documents.

### REST best practices

**Versioning** can live in the path (`/api/v1/users`), in a custom media type sent through `Accept`, or in a query parameter. Path versioning is the easiest to see and route; header versioning keeps URLs stable but is harder to test in a browser.

**Pagination** keeps responses bounded:

```
GET /api/products?page=2&size=50&sort=price,asc

{
  "items": [ ... ],
  "total": 412,
  "page": 2,
  "size": 50,
  "hasMore": true
}
```

Offset paging is simple but slow on large tables and unstable when rows change. Cursor-based paging is the usual alternative.

**Filtering and searching** use query parameters, such as `GET /api/users?role=ADMIN&status=active` or `GET /api/shipments?carrier=DHL&status=delayed`.

**HATEOAS** (Hypermedia as the Engine of Application State) embeds navigation links in each response, so a client can follow them rather than hard-coding URLs:

```json
{
  "id": 731,
  "status": "PAID",
  "links": {
    "self": { "href": "/api/orders/731", "method": "GET" },
    "cancel": { "href": "/api/orders/731", "method": "DELETE" }
  }
}
```

HATEOAS is part of the full REST definition but is rarely implemented in practice. Mention that trade-off if asked.

### Web service styles

- **SOAP**: XML messages over HTTP (or other transports), described by a WSDL contract, with the WS-* standards for security and reliability. It is strictly typed and verbose, and it persists in enterprise and legacy integrations.
- **REST**: resources and HTTP methods, usually with JSON. Simple, cache-friendly, and the default for public web APIs and mobile backends.
- **GraphQL**: a single endpoint (commonly `POST /graphql`) where the client asks for exactly the fields it needs. The schema is strongly typed. It reduces over-fetching and under-fetching, but caching and rate limiting need more care.
- **gRPC**: HTTP/2 with Protocol Buffers defined in `.proto` files. It is binary, strongly typed, and supports streaming in both directions. It suits internal service-to-service calls.
- **WebSocket**: a persistent, full-duplex connection started from an HTTP upgrade. It fits chat, live dashboards, and notifications where the server must push data.

### Error handling

Return errors in one consistent shape with a machine-readable code, a human message, and enough detail to act on:

```json
{
  "type": "https://api.example.com/problems/insufficient-stock",
  "title": "Insufficient stock",
  "status": 409,
  "detail": "Only 2 units of SKU-88 remain",
  "instance": "/api/orders/731/lines/4"
}
```

RFC 9457 (Problem Details for HTTP APIs) defines a standard JSON shape with `type`, `title`, `status`, `detail`, and `instance` fields. It replaced RFC 7807 and is worth knowing for interviews.

A Java record is a compact way to model that payload:

```java
import java.time.Instant;

record ApiError(String code, String message, String path, Instant timestamp) {
}

class ApiErrorDemo {
    public static void main(String[] args) {
        ApiError error = new ApiError(
                "NOT_FOUND",
                "User 123 does not exist",
                "/api/users/123",
                Instant.parse("2024-01-15T10:30:00Z"));

        System.out.println(error.code() + " at " + error.path());
        System.out.println(error);
    }
}
```

### Rate limiting

Servers announce limits in headers so clients can back off. Common names are `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`; the IETF is standardising `RateLimit` header fields. Exceeding the limit returns 429 with a `Retry-After` hint.

### Asynchronous work and bulk operations

- **202 Accepted** tells the client that work is queued. Return a `Location` pointing to a status resource (for example `/api/jobs/abc123`) that answers 202 while running and 200 with the result once finished.
- **Bulk operations** accept many items in one request. The response can be 207 Multi-Status with a per-item status, so one failed item does not hide the others.

### Deprecation

Announce retirement before removing an endpoint. A `Deprecation` header marks the endpoint as deprecated, a `Sunset` header gives the date it will stop working, and a `Link` header with `rel="successor-version"` points to the replacement.

### Security

- **TLS everywhere** in production. Encrypt in transit and validate certificates; do not disable verification to make a test pass.
- **Authentication** establishes identity. API keys suit simple, public-facing or server-to-server access. Bearer tokens (often JWTs) are stateless. OAuth 2.0 delegates access to third parties. Mutual TLS authenticates services by certificate.
- **Authorisation** decides what the identity may do. Role-based access control (RBAC) grants permissions through roles; attribute-based access control (ABAC) evaluates policies on attributes. Never trust authorisation data sent by the client.
- **Input validation** checks size, type, and format, then rejects bad input early with 400 or 422.
- **CORS** is enforced by browsers, not by servers. A cross-origin browser call that is not "simple" triggers an OPTIONS preflight. The server answers with the allowed origin, methods, and headers. Credentialed requests cannot use a wildcard origin.

```
OPTIONS /api/orders
Origin: https://shop.example.org
Access-Control-Request-Method: PATCH
Access-Control-Request-Headers: Content-Type, X-Request-Id

Response:
Access-Control-Allow-Origin: https://shop.example.org
Access-Control-Allow-Methods: GET, POST, PATCH
Access-Control-Allow-Headers: Content-Type, X-Request-Id
Access-Control-Max-Age: 600
```

### Observability

- **Logs** record each request with method, path, status, and duration. Avoid logging secrets or personal data.
- **Traces** follow one request across services. A trace ID is shared by all hops; each operation gets its own span ID. The W3C `traceparent` header is the standard carrier.
- **Metrics** capture request rate, error rate, latency, and payload size. Latency is best read as percentiles (p50, p95, p99), because averages hide slow tails.

## How it works / Step by step

Designing an endpoint, for example "create an order":

1. Pick the resource and the URL: `POST /api/orders`.
2. Validate the body; return 400 for malformed JSON and 422 for rule violations.
3. Require authentication (401) and check permission (403).
4. Create the order; return 201 with `Location: /api/orders/{id}`.
5. If processing is slow, return 202 with a job URL instead.
6. Document the error shape, the idempotency key, and the paging and rate-limit rules.

## Common pitfalls

- Returning 200 with an error body. Clients, proxies, and monitoring rely on the status code.
- Using 401 when the user is logged in but not allowed. That case is 403.
- Retrying a POST after a timeout without an idempotency key, which can create duplicate orders.
- Putting verbs in URLs, such as `/api/getUsers`.
- Enabling CORS with `*` and credentials, which browsers reject.
- Exposing internal stack traces in error responses.
- Forgetting that `Cache-Control: no-cache` still allows storage; use `no-store` for sensitive responses.

!!! tip "Interview tip"
    **Q: PUT or PATCH for an update?**
    Use PUT when the client sends the full representation and the server replaces the resource; PUT is idempotent. Use PATCH when the client sends only the changed fields. Mention that PATCH is not idempotent by definition, although a particular PATCH call can be made idempotent.

## Quick recap

- Know which methods are safe and idempotent; they drive retries and caching.
- Use 401 for missing identity, 403 for insufficient permission, 400 for bad syntax, 422 for rule violations.
- ETags and `Cache-Control` let clients and caches avoid repeat downloads.
- REST is a set of constraints: stateless, uniform interface, cacheable, layered.
- Use one error shape; RFC 9457 is the standard to point to.
- CORS is a browser rule enforced through headers and preflight requests.

**See also:** [Computer Networking](computer-networking.md), [Testing and QA](testing-and-qa.md), [Secure Coding and Supply Chain](../10-security/secure-coding-and-supply-chain.md), [API Design](../21-api-design/index.md)
