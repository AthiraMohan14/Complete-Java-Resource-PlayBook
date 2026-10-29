# Authentication: JWT, OAuth 2.0, and OpenID Connect

Authentication mechanisms decide how a caller proves its identity. For APIs, that usually means a bearer token; for single sign-on, it means delegating login to an identity provider. Interviewers ask about JWT, OAuth 2.0, and OpenID Connect because they are often confused. The key distinction is that OAuth 2.0 is about authorisation to call an API, while OpenID Connect adds identity on top of it.

## Core concepts

### Basic auth and form login

HTTP Basic sends the username and password with every request, encoded but not encrypted, so it must only be used over TLS. Form login uses a login page and a session cookie. Both are fine for internal tools and server-rendered apps, but they are session-based (or credential-based on every call), which matters for stateless APIs.

### JWT (JSON Web Tokens)

A JWT has three base64url-encoded parts separated by dots: a header (algorithm and token type), a payload (claims such as `sub`, `iss`, `aud`, `exp`, and custom claims), and a signature computed over the first two parts.

```text
eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEiLCJleHAiOjE3MDAwMDAwMDB9.<signature>
```

Key points:

- The payload is readable by anyone who holds the token. Do not put secrets in it.
- The signature proves integrity, not secrecy. The server must verify it with the expected key.
- Validate `iss` (issuer), `aud` (audience), `exp` (expiry), and the algorithm. Reject tokens signed with `none`, and never accept whatever algorithm the token header claims.
- Stateless validation means the server does not look up a session, so revoking a token before it expires is hard. Keep access tokens short-lived.

A refresh token is a longer-lived credential used only to obtain new access tokens. Rotate refresh tokens on use, and bind them to the client.

Spring Boot 3 can act as a JWT resource server. It needs a `JwtDecoder` (configured here from an issuer URI) and the `spring-boot-starter-oauth2-resource-server` dependency.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
class ResourceServerConfig {

    @Bean
    SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/**").authenticated()
                .anyRequest().permitAll())
            .oauth2ResourceServer(oauth -> oauth.jwt(Customizer.withDefaults()));
        return http.build();
    }
}
```

With `spring.security.oauth2.resourceserver.jwt.issuer-uri` set, Spring fetches the issuer's signing keys and validates the token's signature and standard claims.

### Where to store tokens in a browser

`localStorage` is readable by any script on the page, so one XSS bug can steal the token. An `HttpOnly`, `Secure`, `SameSite` cookie is not readable by scripts, but it is sent automatically, which brings CSRF into play (see [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md)). There is no single perfect answer; the choice is a trade-off you should be able to explain.

### OAuth 2.0

OAuth 2.0 is a delegation framework. A client obtains an access token from an authorisation server and uses it to call a resource server. Common grants:

- **Authorisation code with PKCE**: for browser apps and mobile apps (public clients). PKCE (Proof Key for Code Exchange) prevents an intercepted code from being used by someone else.
- **Client credentials**: for service-to-service calls where no user is involved.
- **Resource owner password grant**: removed in OAuth 2.1. Avoid it in new designs.

Spring Boot's OAuth2 client support is configured under `spring.security.oauth2.client.registration.<id>`, and the authorisation server can be one you run (for example, with the Spring Authorization Server project) or a hosted provider. Microsoft Entra ID (formerly Azure AD) is an example of a hosted provider.

### OpenID Connect

OpenID Connect (OIDC) is an identity layer on top of OAuth 2.0. Requesting the `openid` scope returns an ID token: a JWT that tells the client who authenticated and when. The user info endpoint returns more profile claims for the access token. Use the ID token to establish identity and the access token to call APIs; do not send ID tokens to resource servers as if they were access tokens.

Spring Security supports OIDC login with `oauth2Login()`, which maps the identity to the `SecurityContext`.

### SAML

SAML 2.0 exchanges XML assertions between an identity provider and a service provider. It is common in enterprise single sign-on, especially in older systems. Spring Security supports SAML 2.0 service-provider login (`saml2Login()`). Most new APIs choose OIDC instead, but you will meet SAML in enterprise integrations.

### Multi-factor authentication

MFA combines factors: something you know (password), something you have (a device), or something you are. Common second factors:

- TOTP (time-based one-time codes, RFC 6238), from an authenticator app. Generally a strong choice.
- Push notifications: convenient, but users can be tricked into approving unexpected prompts.
- SMS: weaker, because of SIM-swap and interception risks.

Spring Security does not ship a full MFA product, so MFA is usually added through an identity provider or a dedicated library.

## Comparison

| Mechanism | Typical use | Key risk |
|---|---|---|
| Basic auth | Internal tools, quick scripts | Credentials on every request; needs TLS |
| Session cookie | Server-rendered web apps | CSRF; session storage at scale |
| JWT bearer | Stateless APIs | Hard to revoke; token leakage |
| OAuth 2.0 + PKCE | Browser and mobile apps calling APIs | Misconfigured redirect URIs |
| OIDC | User login and single sign-on | Using ID tokens as API tokens |
| SAML | Enterprise single sign-on | XML complexity; certificate rotation |

### Validating issuer, audience, and expiry together

The default JWT validation checks the signature and the timestamps. An API should also check that the token was meant for it. The audience (`aud`) claim names the intended resource, and a token issued for another API must be rejected even when its signature is valid.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2TokenValidatorResult;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtValidators;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;

@Configuration
class JwtConfig {

    @Bean
    JwtDecoder jwtDecoder() {
        String issuer = "https://auth.example.com/realms/shop";
        NimbusJwtDecoder decoder = NimbusJwtDecoder.withIssuerLocation(issuer).build();

        OAuth2TokenValidator<Jwt> audience = jwt -> jwt.getAudience().contains("orders-api")
                ? OAuth2TokenValidatorResult.success()
                : OAuth2TokenValidatorResult.failure(
                        new OAuth2Error("invalid_token", "token is not for this API", null));

        decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
                JwtValidators.createDefaultWithIssuer(issuer), audience));
        return decoder;
    }
}
```

The default validator checks the issuer and the time window (`exp`, `nbf`). The custom audience check adds the part the default does not know about. Custom claims such as roles or tenant IDs follow the same pattern, and should be checked on the server, never trusted because the client sent them.

## Sessions versus JWTs

Server-side sessions and JWTs both carry a logged-in user between requests, but they store the state in different places. The choice mostly comes down to revocation and scaling.

| Aspect | Server-side session | JWT |
|---|---|---|
| Where the state lives | On the server, keyed by a session ID | In the token itself |
| Logout or revocation | Immediate: delete the session | Needs a deny-list or a short lifetime |
| Scaling | Needs a shared session store or sticky routing | Any instance can verify the token |
| Size on each request | A small session ID cookie | A longer token sent with every call |
| Fit | Server-rendered web apps | APIs, single-page apps, mobile apps, service-to-service calls |

Sessions suit server-rendered applications where an immediate logout matters. JWTs suit stateless APIs. Neither is better in every case, so explain the trade-off rather than naming a winner.

## Issuing and verifying your own JWT

When you issue tokens yourself, the JJWT library (version 0.12 and later) builds and parses them. The signing key must be at least 256 bits for HS256, and it must come from configuration, not from source code.

```java
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Date;
import java.util.List;
import javax.crypto.SecretKey;

public class JwtIssuer {

    private static final Duration ACCESS_TTL = Duration.ofMinutes(15);

    private final SecretKey key;

    public JwtIssuer(String secret) {
        // Throws if the secret is shorter than 256 bits
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    public String issue(String username, List<String> roles) {
        Date now = new Date();
        return Jwts.builder()
                .subject(username)
                .claim("roles", roles)
                .issuedAt(now)
                .expiration(new Date(now.getTime() + ACCESS_TTL.toMillis()))
                .signWith(key)
                .compact();
    }

    public Claims verify(String token) {
        // Throws a JwtException subclass for a bad signature, expiry, or malformed token
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
```

Older examples use `setSigningKey(String)` and `signWith(SignatureAlgorithm, String)`. Those methods were removed in JJWT 0.12, so check the version you depend on. Catch `JwtException` in the filter that calls `verify`, and reject the request. Do not log the token itself.

## A bearer token filter for stateless APIs

A filter reads the `Authorization: Bearer` header, verifies the token, and places the caller in the `SecurityContext` for this request only. It runs once per request and performs no session lookup.

```java
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

public class BearerTokenFilter extends OncePerRequestFilter {

    private final JwtIssuer jwtIssuer;

    public BearerTokenFilter(JwtIssuer jwtIssuer) {
        this.jwtIssuer = jwtIssuer;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            try {
                Claims claims = jwtIssuer.verify(header.substring(7));
                List<?> roles = claims.get("roles", List.class);
                List<SimpleGrantedAuthority> authorities = (roles == null ? List.<Object>of() : roles)
                        .stream()
                        .map(r -> new SimpleGrantedAuthority("ROLE_" + r))
                        .toList();
                SecurityContextHolder.getContext().setAuthentication(
                        new UsernamePasswordAuthenticationToken(claims.getSubject(), null, authorities));
            } catch (JwtException | IllegalArgumentException ex) {
                // Leave the context empty; the authorisation rules then return 401
            }
        }
        chain.doFilter(request, response);
    }
}
```

The filter is wired into a stateless filter chain. Disabling CSRF is safe here only because this API accepts no cookie credentials (see [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md)).

```java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
class ApiSecurityConfig {

    @Bean
    JwtIssuer jwtIssuer(@Value("${app.jwt.secret}") String secret) {
        return new JwtIssuer(secret);
    }

    @Bean
    SecurityFilterChain apiChain(HttpSecurity http, JwtIssuer jwtIssuer) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/auth/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .addFilterBefore(new BearerTokenFilter(jwtIssuer), UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
```

Create the filter with `new` inside the configuration rather than making it a bean. Spring Boot registers every `Filter` bean with the servlet container as well, so a filter declared as a bean would run twice.

## Refresh token flow

An access token lives minutes. A refresh token lives days and is used only at the token endpoint. The client trades a valid refresh token for a new access token, and the server controls whether that is allowed.

1. Login returns a short-lived access token and a refresh token.
2. The client calls the API with the access token until it expires.
3. The client sends the refresh token to the refresh endpoint.
4. The server checks that the refresh token is stored, unexpired, and unused. It marks that token as used and issues a new pair (rotation).
5. Logout deletes the refresh token on the server, so it cannot be used again.

```java
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

// Minimal stand-in for the issuer described earlier on the page.
interface JwtIssuer {
    String issue(String username, List<String> roles);
}

public record TokenPair(String accessToken, String refreshToken) {}

interface RefreshTokenStore {

    /** Returns the username for an unused, unexpired token, and marks it as used. */
    Optional<String> consume(String refreshToken);

    void store(String refreshToken, String username, Instant expiresAt);
}

class TokenService {

    private final RefreshTokenStore refreshTokens;
    private final JwtIssuer jwtIssuer;

    public TokenService(RefreshTokenStore refreshTokens, JwtIssuer jwtIssuer) {
        this.refreshTokens = refreshTokens;
        this.jwtIssuer = jwtIssuer;
    }

    public Optional<TokenPair> refresh(String presentedRefreshToken) {
        return refreshTokens.consume(presentedRefreshToken).map(username -> {
            String access = jwtIssuer.issue(username, List.of());   // reload roles here
            String next = UUID.randomUUID().toString();
            refreshTokens.store(next, username, Instant.now().plus(Duration.ofDays(7)));
            return new TokenPair(access, next);
        });
    }
}
```

Store refresh tokens hashed, the same way you would store a password, so that a database read does not reveal usable tokens. If a token that was already used comes back, treat it as theft: revoke every refresh token for that user and require a new login.

## Logout and revocation

A JWT stays valid until it expires, so logout needs a deny-list. Store the token's `jti` (the JWT ID claim) with its expiry time. Once the expiry has passed, the entry can be dropped.

```java
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class TokenDenyList {

    private final Map<String, Instant> revokedUntil = new ConcurrentHashMap<>();

    public void revoke(String jti, Instant tokenExpiresAt) {
        revokedUntil.put(jti, tokenExpiresAt);
    }

    public boolean isRevoked(String jti) {
        Instant until = revokedUntil.get(jti);
        if (until == null) {
            return false;
        }
        if (until.isBefore(Instant.now())) {
            revokedUntil.remove(jti);   // the token has expired anyway
            return false;
        }
        return true;
    }
}
```

An in-memory map works for one instance only, and it is lost on restart. With several instances, keep the deny-list in a shared store such as Redis, with a time-to-live equal to the token's remaining life. A plain `HashSet` is not safe under concurrent requests, and it grows without bound.

## Multi-tenant claims

A tenant ID in the token lets one API serve several organisations. Read it from the claims after the signature has been verified, and use it to scope every query. Never take the tenant from a request header or parameter that the client controls.

```java
class TenantLookup {

    // Stand-in for the JJWT Claims type used earlier on the page.
    interface Claims {
        <T> T get(String name, Class<T> type);
    }

    static String tenantOf(Claims claims) {
        // After verify(token) has succeeded
        return claims.get("tenant_id", String.class);
    }
}
```

## Role checks

Put role rules on the handler, not in the token parser. A short example, with the full set of rules described in [Spring Security Authorisation](spring-security-authorisation.md):

```java
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
class AdminController {

    @GetMapping("/admin/users")
    @PreAuthorize("hasRole('ADMIN')")
    String listUsers() {
        return "admin only";
    }
}
```

Roles in a JWT are a hint for the client. The server must still check them on each request, because a role may have been removed after the token was issued.

## Other authentication mechanisms

- **API keys** identify a client application. Send them in a header, store only a hash on the server, and give each key a scope and an owner. A leaked key compromises everything it can reach.
- **Mutual TLS (mTLS)** uses client certificates, so both sides authenticate. It is common between services. See [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md).
- **HMAC request signing** proves a request came from a holder of a shared secret and was not changed. Verify the signature in constant time; the method is shown in [Password Security and OWASP](password-security-owasp.md).
- **Session cookies** are described above; they remain the right default for server-rendered applications.

## OAuth 2.0 grant types at a glance

The implicit grant, which returned tokens in the browser URL for single-page apps, is deprecated; use the authorisation code grant with PKCE instead. The resource owner password grant is removed in OAuth 2.1. Client credentials serve service-to-service calls, and the refresh token grant renews access tokens, as in the flow above.

## Configuration

Read signing keys and lifetimes from configuration. Do not give the secret a default value, because a missing variable would then fall back to a known key.

```yaml
app:
  jwt:
    secret: ${JWT_SECRET}          # no default: startup fails if it is missing
    access-token-ttl: PT15M
    refresh-token-ttl: P7D
```

Spring's `Duration` binding reads these ISO-8601 values. Store the secret in a secrets manager and inject it at runtime (see [Secrets Management](secrets-management.md)).

## Common pitfalls

- Trusting JWT contents without verifying the signature, issuer, audience, and expiry.
- Long-lived access tokens with no revocation path.
- Using the implicit flow or the password grant in new designs.
- Loose redirect URI matching, which allows authorisation codes to be redirected to attacker-controlled hosts.
- Storing tokens in `localStorage` without accounting for XSS.
- Logging full tokens or authorisation headers.

!!! tip "Interview tip"
    **Q: What is the difference between OAuth 2.0 and OpenID Connect?**
    OAuth 2.0 lets a client get an access token to call an API on a user's behalf. It says nothing standard about who the user is. OpenID Connect adds an ID token that identifies the user and how they logged in. Use OIDC for login, and access tokens for API calls.

## Quick recap

- JWTs are signed, not encrypted; always verify issuer, audience, expiry, and algorithm.
- Keep access tokens short-lived; rotate refresh tokens.
- Use authorisation code with PKCE for browser and mobile clients, and client credentials for service-to-service calls.
- OIDC adds identity on top of OAuth 2.0 via the ID token.
- Prefer TOTP-style MFA over SMS where you can.

**See also:** [Spring Security Authorisation](spring-security-authorisation.md) | [Inter-Service Communication](../14-microservices/inter-service-communication.md) | [Secrets Management](secrets-management.md)
