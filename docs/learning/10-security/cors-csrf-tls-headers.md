# CORS, CSRF, TLS, and Security Headers

These four topics protect the boundary between the browser and your server. CORS controls which other origins a browser may call your API from. CSRF stops other sites from making authenticated requests on a user's behalf. TLS protects data in transit, and security headers tell the browser to enforce extra rules. Interviewers ask about these because the terms are easy to mix up, and the wrong configuration can silently weaken an application.

## Core concepts

### Same-origin policy and CORS

Browsers enforce the same-origin policy: a script on one origin (scheme, host, and port) cannot read responses from another origin. CORS is the controlled way to relax that. The server sends headers such as `Access-Control-Allow-Origin` to say which origins may read its responses.

For requests that are not "simple" (for example, a `PUT`, or a JSON body with an `Authorization` header), the browser first sends a preflight `OPTIONS` request. The server answers with the allowed methods and headers, and the browser sends the real request only if the answer permits it.

CORS is enforced by browsers, not servers. A `curl` request ignores it, so CORS is not an access-control mechanism for your API. Authentication and authorisation still apply.

Spring Security applies CORS through a `CorsConfigurationSource` bean, which must run before authentication so that preflight requests are answered without credentials.

```java
import java.util.List;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
class CorsConfig {

    @Bean
    SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
        http.cors(cors -> cors.configurationSource(corsSource()));
        return http.build();
    }

    @Bean
    CorsConfigurationSource corsSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("https://app.example.com"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowedHeaders(List.of("Content-Type", "Authorization"));
        config.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return source;
    }
}
```

A wildcard origin (`*`) cannot be combined with credentials. List the exact origins you need, and avoid reflecting the request's `Origin` header back without checking it against an allow-list.

### CSRF

Cross-Site Request Forgery tricks a logged-in browser into sending a request to your site. It works when the browser attaches credentials automatically, which is the case for cookies. The defence is a token that the attacker's page cannot read: the server issues a CSRF token, and state-changing requests (`POST`, `PUT`, `DELETE`) must include it.

Spring Security enables CSRF protection by default. For a server-rendered app that uses cookies, keep it on. A cookie-based CSRF repository lets a single-page app read the token and send it back in a header:

```java
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;

class CsrfSetup {
    void configure(HttpSecurity http) throws Exception {
        http.csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()));
    }
}
```

A stateless API that authenticates with an `Authorization` bearer token is not exposed to classic CSRF, because the browser does not attach that header automatically. Such APIs often disable CSRF protection. That is only safe when no cookie authenticates the request. If an API accepts both cookies and bearer tokens, keep CSRF protection on for cookie-based requests.

### SameSite cookies

The `SameSite` cookie attribute tells the browser when to send a cookie on cross-site requests:

- `Strict`: never sent on cross-site requests. Strongest, but it can break links from other sites.
- `Lax`: sent on top-level navigations with safe methods. A common default.
- `None`: sent on all cross-site requests, and requires `Secure`.

`SameSite` is a strong second layer against CSRF, not a replacement for tokens. In Spring Boot, set the session cookie attribute with `server.servlet.session.cookie.same-site`, and set `secure` and `http-only` on the same cookie.

### TLS

TLS encrypts traffic between client and server and authenticates the server with a certificate. Key points for interviews:

- Use TLS 1.2 or later; disable older protocols and weak cipher suites.
- Certificates need a trusted chain, a correct host name, and an expiry plan. Expired certificates are a common outage cause.
- Spring Boot can terminate TLS itself with `server.ssl.*` properties (key store, type, and password). Many deployments terminate TLS at a load balancer or ingress instead; then the internal hop needs its own decision.
- Mutual TLS (mTLS) adds client certificates, so both sides authenticate. It is common for service-to-service traffic (see [Inter-Service Communication](../14-microservices/inter-service-communication.md)).

Keep key store passwords out of files. Load them from a secrets store (see [Secrets Management](secrets-management.md)).

### HSTS

HTTP Strict Transport Security (`Strict-Transport-Security` header) tells the browser to use HTTPS for your site for a given time, which prevents downgrade attacks and SSL stripping. Spring Security adds HSTS on secure requests by default. Only enable `includeSubDomains` and `preload` once every subdomain is ready for HTTPS.

### Security headers

Spring Security writes several headers by default (such as `X-Content-Type-Options` and `X-Frame-Options`). You can tighten them:

```java
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.header.writers.ReferrerPolicyHeaderWriter;

class HeaderSetup {
    void configure(HttpSecurity http) throws Exception {
        http.headers(headers -> headers
                .contentSecurityPolicy(csp -> csp
                        .policyDirectives("default-src 'self'; frame-ancestors 'none'"))
                .referrerPolicy(ref -> ref
                        .policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN))
                .permissionsPolicy(perm -> perm
                        .policy("camera=(), microphone=(), geolocation=()")));
    }
}
```

| Header | Purpose |
|---|---|
| `Content-Security-Policy` (CSP) | Restricts where scripts, styles, and frames may load from. Reduces XSS impact |
| `X-Content-Type-Options: nosniff` | Stops browsers from guessing a content type |
| `X-Frame-Options` | Blocks clickjacking by refusing framing (`DENY` or `SAMEORIGIN`); the CSP `frame-ancestors` directive is the modern equivalent |
| `Referrer-Policy` | Controls how much of the URL is sent in the `Referer` header |
| `Permissions-Policy` | Disables browser features (camera, microphone, location) the page does not need |

CSP is easy to get wrong. Start in report-only mode when you can, and avoid `unsafe-inline` for scripts.

## How it works / Step by step

1. The browser sends a preflight `OPTIONS` request if the cross-origin call is non-simple. Spring's CORS filter answers using the `CorsConfigurationSource`.
2. For the actual request, the browser attaches cookies only if `SameSite` and origin rules allow it.
3. Spring Security checks the CSRF token on state-changing requests.
4. The response carries CORS, HSTS, CSP, and other headers the browser enforces.

## Common pitfalls

- Treating CORS as API authentication. It only governs browsers.
- Allowing `*` origins with credentials, or reflecting any `Origin` header.
- Disabling CSRF globally for an app that uses session cookies.
- Assuming `SameSite` alone makes CSRF tokens unnecessary.
- Setting HSTS `preload` before every subdomain supports HTTPS.
- Writing a CSP with `unsafe-inline` and believing it protects against XSS.
- Letting certificates expire because nobody owns the renewal.

!!! tip "Interview tip"
    **Q: What is the difference between CORS and CSRF?**
    CORS is a browser rule that decides whether a script on one origin may read a response from another. CSRF is an attack in which another site triggers a state-changing request that the browser authenticates with cookies. CORS does not stop requests from being sent; it stops them from being read. CSRF tokens and `SameSite` cookies stop the forged request itself.

## Quick recap

- CORS is a browser-enforced read permission; configure exact origins and never combine `*` with credentials.
- Keep CSRF protection on for cookie-authenticated requests; bearer-only APIs have different needs.
- `SameSite`, `Secure`, and `HttpOnly` harden cookies.
- Use TLS 1.2 or later, and plan certificate renewal.
- Set CSP, `nosniff`, frame protection, `Referrer-Policy`, and `Permissions-Policy` deliberately.

**See also:** [Password Security and OWASP](password-security-owasp.md) | [Authentication: JWT, OAuth 2.0, and OpenID Connect](authentication-jwt-oauth.md) | [Exception Handling](../09-spring-boot/exception-handling.md)
