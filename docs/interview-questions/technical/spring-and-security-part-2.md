# Spring, Spring Boot, and Security Questions (Part 2 of 2)

Continued from [Part 1](spring-and-security-part-1.md).

---

## 11. What is the difference between a servlet filter, a Spring interceptor, and an AOP aspect?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A servlet filter sits in the servlet container and sees every request, including static resources and the security chain. A `HandlerInterceptor` runs inside Spring MVC around the controller and can see the matched handler. An AOP aspect advises any Spring bean method, not only web requests.

### Explanation
| Mechanism | Works on | Typical use |
|---|---|---|
| Servlet filter | Every HTTP request, before `DispatcherServlet` | Request IDs, CORS, security filters |
| `HandlerInterceptor` | Spring MVC requests, before and after the controller | Logging the handler, auth checks that need the controller |
| AOP aspect | Method calls on Spring beans | Timing, auditing, transactions |

```java
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.UUID;
import org.springframework.stereotype.Component;

@Component
class RequestIdFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        String id = UUID.randomUUID().toString();
        ((HttpServletRequest) req).setAttribute("requestId", id);
        chain.doFilter(req, res);
    }
}
```

### When to use / pitfalls
- Use a filter for anything that must run before Spring MVC, such as security or request rewriting.
- Use an aspect for business-level cross-cutting concerns, but avoid putting core logic in aspects where it is hard to see.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 12. How does Spring Security process a request?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Spring Security is a chain of servlet filters. Each request passes through the `SecurityFilterChain` before reaching your controller. The authentication filters read credentials or a token and place an `Authentication` in the `SecurityContext`. The authorisation rules then decide whether the request may continue, and an unauthenticated request gets `401`, while an authenticated user without permission gets `403`.

### Explanation
```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .httpBasic(basic -> {});
        return http.build();
    }
}
```

In Spring Security 6, you define a `SecurityFilterChain` bean instead of extending `WebSecurityConfigurerAdapter`, which was removed.

### When to use / pitfalls
- Order matters: put the most specific request matchers first.
- Keep `anyRequest().authenticated()` (or `denyAll()`) as the last rule so new endpoints are not public by accident.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 13. What is the difference between authentication and authorisation, and how do you protect methods?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Authentication establishes who the caller is. Authorisation decides what that caller may do. Spring Security enables method-level checks with `@EnableMethodSecurity`, then `@PreAuthorize` evaluates an expression before the method runs, and `@PostAuthorize` checks the return value.

### Explanation
```java
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Service;

@Configuration
@EnableMethodSecurity
class MethodSecurityConfig { }

@Service
class InvoiceService {

    @PreAuthorize("hasRole('FINANCE')")
    public void approve(long invoiceId) {
        // only finance users reach this line
    }

    @PreAuthorize("#ownerId == authentication.name")
    public void viewOwn(String ownerId) {
        // checks the caller owns the data
    }
}
```

### When to use / pitfalls
- Checking roles in controllers only is fragile; a second route to the same service may skip the check. Enforce critical rules in the service layer too.
- Object-level checks (is this user the owner of this record?) need the record, so they usually belong in the service.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 14. How should passwords be stored?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Store passwords with a slow, salted, adaptive hash such as BCrypt, scrypt, Argon2, or PBKDF2, never with plain text or a fast hash such as MD5 or SHA-256 on its own. The salt is random per password and stored with the hash, so identical passwords get different hashes. A pepper is a secret key kept outside the database.

### Explanation
```java
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

class PasswordDemo {
    public static void main(String[] args) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();   // default strength
        String stored = encoder.encode("correct horse battery staple");  // includes salt
        System.out.println(encoder.matches("correct horse battery staple", stored)); // true
        System.out.println(encoder.matches("wrong guess", stored));                  // false
    }
}
```

Spring Security's `DelegatingPasswordEncoder` stores an algorithm prefix (for example `{bcrypt}`), which lets you migrate to a stronger algorithm later.

### When to use / pitfalls
- BCrypt truncates input after 72 bytes; do not rely on it for very long passphrases without a pre-hash.
- Rate-limit login attempts and add account lockout or MFA. Hashing alone does not stop online guessing.
- Never log passwords or put them in URLs.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 15. How does a JWT work, and what are the common mistakes?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A JSON Web Token has three base64url-encoded parts: a header, a payload with claims, and a signature. The server signs the first two parts; anyone can read the payload, but only the signer can produce a valid signature. Servers verify the signature and the expiry (`exp`) on each request, which makes authentication stateless.

### Explanation
```java
import java.nio.charset.StandardCharsets;
import java.util.Base64;

class JwtPeek {
    public static void main(String[] args) {
        String token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0MiJ9.signature";
        String[] parts = token.split("\\.");
        // Decoding the payload is not verification. Always verify the signature first.
        String payload = new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
        System.out.println(payload);   // {"sub":"42"}
    }
}
```

Mistakes interviewers look for:

- Trusting the payload before verifying the signature.
- Accepting the `none` algorithm, or letting the token choose an algorithm the server did not expect.
- Storing secrets or personal data in the payload; it is readable by anyone who holds the token.
- Long lifetimes with no revocation. Use short access tokens and a refresh-token flow, and rotate refresh tokens.
- Putting tokens in `localStorage`, which any injected script can read. An `HttpOnly`, `Secure`, `SameSite` cookie is the usual alternative, but then CSRF defences are needed.

### When to use / pitfalls
- Use a maintained library to verify tokens. Do not write your own parser or signature check.
- Validate `iss`, `aud`, and `exp` as well as the signature.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 16. What are the OAuth 2.0 grant types you should use, and how do OpenID Connect and PKCE fit in?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use the authorisation code flow with PKCE for user-facing apps, including single-page and mobile apps. Use the client credentials flow for service-to-service calls with no user. OpenID Connect adds an identity layer on top of OAuth 2.0: it returns an ID token that says who signed in. The resource owner password grant was removed in OAuth 2.1 and should not be used in new designs.

### Explanation
Authorisation code flow with PKCE, in short:

1. The client creates a random `code_verifier` and sends its hash, the `code_challenge`, to the authorisation server.
2. The user signs in and the server redirects back with a short-lived `code`.
3. The client exchanges the `code` plus the original `code_verifier` for tokens. An attacker who intercepts the code cannot do this without the verifier.

In Spring, a resource server validates incoming JWT access tokens like this:

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
class ApiSecurity {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
            .oauth2ResourceServer(oauth -> oauth.jwt(jwt -> {}));   // validates bearer JWTs
        return http.build();
    }
}
```

Microsoft Entra ID (formerly Azure AD) is one identity provider that implements these flows.

### When to use / pitfalls
- Do not use the implicit flow in new work; OAuth 2.1 removes it.
- Access tokens are for APIs; ID tokens are for the client to learn who the user is. Do not send ID tokens to APIs as access tokens.
- SAML is common in enterprise single sign-on. Know what it is, and that OIDC is the more common choice for new web and mobile APIs.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 17. What is the difference between CORS and CSRF, and what does `SameSite` do?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
CORS is a browser rule that blocks a web page on one origin from reading responses from another origin unless the server allows it, using headers such as `Access-Control-Allow-Origin`. CSRF is an attack where a malicious site makes the victim's browser send a state-changing request with the victim's cookies. CSRF defences such as tokens matter most when the app authenticates with cookies. `SameSite` is a cookie attribute that limits when the browser sends the cookie on cross-site requests.

### Explanation
```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("https://app.example.com")   // explicit list, not "*"
                .allowedMethods("GET", "POST");
    }
}
```

With cookie-based sessions, keep CSRF protection on. With a bearer token in the `Authorization` header and no cookies, CSRF is generally not a concern, and many APIs disable it for that reason.

### When to use / pitfalls
- CORS is not an access control mechanism. A non-browser client ignores it.
- Do not combine `allowCredentials(true)` with a wildcard origin; the browser rejects it.
- Set cookies with `HttpOnly`, `Secure`, and an explicit `SameSite` value.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 18. Which OWASP risks should a Java web service defend against first?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Start with the OWASP Top 10 2021 categories: broken access control, cryptographic failures, injection, insecure design, security misconfiguration, vulnerable components, identification and authentication failures, software and data integrity failures, logging and monitoring failures, and server-side request forgery. The list is updated periodically, so check the current version before quoting it.

### Explanation
| Risk | Java-specific defence |
|---|---|
| Broken access control | Check permissions on the server with method security; deny by default |
| Injection | Use `PreparedStatement` or JPA parameter binding; never concatenate SQL |
| Cryptographic failures | Use TLS, current algorithms, and managed keys; never roll your own crypto |
| Security misconfiguration | Expose only needed Actuator endpoints; turn off debug output in production |
| Vulnerable components | Run dependency scanning (SCA) in CI |
| Auth failures | Strong password hashing, MFA, rate limiting |
| Integrity failures | Avoid Java native deserialisation of untrusted data |
| Logging failures | Log security events; never log secrets |
| SSRF | Allow-list outbound hosts for any URL the user supplies |

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

class SafeQuery {
    static boolean userExists(Connection conn, String username) throws SQLException {
        try (PreparedStatement ps = conn.prepareStatement("SELECT 1 FROM users WHERE username = ?")) {
            ps.setString(1, username);          // bound parameter, not concatenated
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        }
    }
}
```

### When to use / pitfalls
- A scanner alone does not prove security. Combine it with code review and threat modelling.
- Deserialising objects from untrusted sources is a known remote-code-execution risk. Prefer JSON with explicit DTOs.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## Quick recap

- Use constructor injection; keep singletons stateless or thread-safe.
- Self-invocation bypasses Spring proxies, so `@Transactional` and other advice are skipped.
- `@Transactional` rolls back on unchecked exceptions by default; add `rollbackFor` for checked ones.
- Spring Boot auto-configuration is conditional; use the condition report to debug.
- Spring Security 6 uses a `SecurityFilterChain` bean and `@EnableMethodSecurity`.
- Hash passwords with BCrypt, Argon2, scrypt, or PBKDF2. Verify JWTs before trusting claims.

**See also:** [Core Java](core-java-part-1.md), [Data and persistence](data-and-persistence-part-1.md), [Architecture and distributed systems](architecture-and-distributed.md)
