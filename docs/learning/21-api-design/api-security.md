# API Security

An API is reachable by anyone who can send it a request, so it is the first thing attackers probe. This page covers how callers prove who they are (tokens, JWTs, OAuth 2.0), how you limit abuse (rate limiting), how browsers are allowed to call you (CORS), and how you handle untrusted input. Interviewers ask about these to see whether you treat security as a design concern rather than a checklist at the end.

## Core concepts

### Authentication and authorisation

**Authentication** answers "who are you?". **Authorisation** answers "are you allowed to do this?". Check both on every request. A valid token for user A must not let user A read user B's order, which is a broken object-level authorisation issue and one of the most common API flaws (OWASP lists broken access control at the top of its Top 10 2021 categories).

### API keys, tokens, and JWTs

- **API keys** identify a client application. They are simple but long-lived and easy to leak. Store only a hash on the server, rotate them, and scope them narrowly.
- **Opaque tokens** are random strings the server looks up in a store. They can be revoked immediately.
- **JWTs (JSON Web Tokens)** are signed, self-contained tokens with claims such as subject (`sub`), issuer (`iss`), audience (`aud`), and expiry (`exp`). The server can verify them without a lookup, but they cannot be revoked instantly unless you add a deny-list.

A JWT is encoded, not encrypted, by default. Anyone holding the token can read its claims. Never put secrets or sensitive personal data in the payload.

Validate every claim that matters. Accepting any signature algorithm the token claims is a known pitfall, so pin the algorithm your server expects:

```java
import java.util.Map;

public class TokenPolicy {

    private static final String EXPECTED_ISSUER = "https://auth.example.com/";
    private static final String EXPECTED_AUDIENCE = "orders-api";

    // Claims would be read from a verified token by your JWT library.
    public static boolean isAcceptable(Map<String, Object> claims, long nowEpochSeconds) {
        Object iss = claims.get("iss");
        Object aud = claims.get("aud");
        Object exp = claims.get("exp");
        if (!EXPECTED_ISSUER.equals(iss) || !EXPECTED_AUDIENCE.equals(aud)) {
            return false;
        }
        return exp instanceof Number n && n.longValue() > nowEpochSeconds;
    }
}
```

In a real service, a mature library verifies the signature and standard claims. The point here is that issuer, audience, and expiry must all be checked.

### OAuth 2.0 and OpenID Connect

**OAuth 2.0** is an authorisation framework: a client obtains a limited access token from an authorisation server, on behalf of a user or itself. **OpenID Connect (OIDC)** adds an identity layer on top, with an ID token that says who the user is. For user login, use the authorisation code flow with PKCE for public clients. For service-to-service calls, use the client credentials flow.

Enterprise identity platforms such as **Microsoft Entra ID** (formerly Azure AD) implement these standards. A Spring resource server validates incoming bearer tokens against the issuer's keys. Do not build your own login or token format when a standard identity provider fits.

### Rate limiting

Rate limiting protects the service from abuse and from accidental overload. Limits are usually applied per API key, per user, or per IP, and return `429 Too Many Requests` with a `Retry-After` header.

A **token bucket** is a common algorithm. Each client has a bucket with a capacity; tokens refill at a steady rate; each request consumes one. A small single-node version:

```java
public final class TokenBucket {

    private final long capacity;
    private final double refillPerNano;
    private double tokens;
    private long lastRefillNanos;

    public TokenBucket(long capacity, double tokensPerSecond) {
        this.capacity = capacity;
        this.refillPerNano = tokensPerSecond / 1_000_000_000.0;
        this.tokens = capacity;
        this.lastRefillNanos = System.nanoTime();
    }

    public synchronized boolean tryConsume() {
        long now = System.nanoTime();
        tokens = Math.min(capacity, tokens + (now - lastRefillNanos) * refillPerNano);
        lastRefillNanos = now;
        if (tokens >= 1.0) {
            tokens -= 1.0;
            return true;
        }
        return false;
    }
}
```

With several instances, the bucket state must be shared, usually in Redis or at the API gateway. A per-instance limit multiplies across replicas.

### CORS

**Cross-Origin Resource Sharing (CORS)** is a browser mechanism. A page on one origin (scheme, host, port) calling an API on another origin needs the API to send headers such as `Access-Control-Allow-Origin`. The browser sends a preflight `OPTIONS` request for non-simple calls.

CORS is not an authentication mechanism. It only tells browsers which origins may read responses. Allow specific origins, not `*`, and never combine `*` with credentials (browsers reject it). Keep allowed methods and headers as narrow as your clients need.

### HTTPS enforcement

Serve everything over TLS and redirect plain HTTP. Send `Strict-Transport-Security` (HSTS) so browsers refuse plain HTTP after the first visit. Terminate TLS at a load balancer or gateway if you must, but then secure the hop from there to the service too.

### Input validation and sanitisation

Treat every request body, parameter, header, and file name as hostile. Validate types, lengths, formats, and ranges at the boundary. Bean Validation annotations in Spring Boot 3 come from `jakarta.validation`:

```java
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record SignUpRequest(
        @NotBlank @Email String email,
        @NotBlank @Size(min = 12, max = 128) String password) {
}
```

The minimum password length (12 here) is a policy choice for your system. Current guidance (NIST SP 800-63B) favours length over complex composition rules, and checking passwords against known-breached lists.

Validation is not the only defence. Use parameterised queries to prevent SQL injection, encode output for the context it is rendered in, and avoid passing user input to shell commands or to deserialisation of untrusted data.

### OWASP as a reference

The **OWASP Top 10** lists the most critical web application risk categories. The 2021 edition is the reference used here, and OWASP updates the list periodically, so check the current version when you need it. The categories most relevant to APIs include:

- **A01 Broken Access Control:** object-level and function-level checks (for example, users reading other users' records)
- **A02 Cryptographic Failures:** weak TLS, plaintext secrets, weak hashing
- **A03 Injection:** SQL, command, and other injections through untrusted input
- **A05 Security Misconfiguration:** permissive CORS, debug endpoints left on, default credentials
- **A07 Identification and Authentication Failures:** weak login, token handling mistakes

OWASP also publishes a dedicated API Security Top 10, which is worth reading for API-specific risks.

## How it works

1. A client obtains a token from an identity provider (OAuth 2.0 / OIDC) or uses an API key.
2. It sends the token in the `Authorization: Bearer` header.
3. The gateway or service validates the signature, issuer, audience, and expiry.
4. Rate limits are checked per client; excess requests get `429`.
5. The handler checks authorisation for the specific resource, then validates input and runs the operation.
6. Responses carry security headers, and errors do not reveal internals.

## Common pitfalls

- Checking that a token is valid but not checking whether the caller may access this object
- Accepting tokens without checking issuer, audience, or expiry
- Putting secrets in JWT payloads, which are readable by anyone holding the token
- Rate limiting per instance only, so limits multiply with the number of replicas
- Using `Access-Control-Allow-Origin: *` on endpoints that use cookies or credentials
- Returning stack traces, SQL errors, or internal IDs in error bodies

!!! tip "Interview tip"
    **Q: A user reports they can see another user's order by changing the ID in the URL. What is the bug?**
    A: This is broken object-level authorisation (OWASP A01). The endpoint authenticates the caller but does not check that the order belongs to them. The fix is to load the resource scoped to the caller, for example by querying with both the order ID and the owner's ID, and to return `404` for resources the caller may not see.

## Quick recap

- Authenticate every request and authorise every object access
- Validate JWT issuer, audience, and expiry; never put secrets in the payload
- Use OAuth 2.0 / OIDC with a standard identity provider rather than custom login
- Rate-limit with shared state across instances; return `429` with `Retry-After`
- CORS is a browser policy, not authentication; never pair `*` with credentials
- Validate all input at the boundary and use the OWASP Top 10 as a checklist

**See also:** [REST Principles and Versioning](rest-principles-versioning.md), [Pagination, Errors, and Idempotency](pagination-errors-idempotency.md), [Alternative Protocols](alternative-protocols.md)
