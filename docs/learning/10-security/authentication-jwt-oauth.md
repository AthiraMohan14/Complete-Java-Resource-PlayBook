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
