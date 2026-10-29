# Security

Application security covers who a user is (authentication), what they may do (authorisation), how credentials and secrets are stored, how browsers are protected from cross-site attacks, and how data is kept safe in transit. These notes focus on Spring Security 6 and the practices interviewers expect a Java backend developer to know.

---

## Topics

### [Spring Security Authorisation](spring-security-authorisation.md)
**SecurityFilterChain - UserDetailsService - RBAC - @PreAuthorize - method security**
How requests pass through the filter chain, how users and roles are loaded, and how access rules are written at URL and method level.

### [Authentication: JWT, OAuth 2.0, and OpenID Connect](authentication-jwt-oauth.md)
**JWT - stateless tokens - OAuth 2.0 - PKCE - OpenID Connect - SAML - MFA**
Authentication mechanisms for APIs and single sign-on, their trade-offs, and where each one fits.

### [Password Security and OWASP](password-security-owasp.md)
**BCrypt - Argon2 - salts - peppers - rate limiting - OWASP Top 10 2021**
Safe password storage with adaptive hashes, and a practical map of the most common web application risks.

### [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md)
**CORS preflight - CSRF tokens - SameSite - HSTS - CSP - Permissions-Policy**
Controlling which origins can call your API, protecting cookie-based sessions, enforcing TLS, and setting browser security headers.

### [Secrets Management](secrets-management.md)
**environment variables - Vault - AWS Secrets Manager - Azure Key Vault - rotation**
Keeping credentials out of code and Git, injecting them at runtime, and rotating them without downtime.

---

**See also:** [Building REST APIs](../09-spring-boot/rest-apis.md) | [HTTP Clients and Testing](../09-spring-boot/http-clients-and-testing.md) | [Testing](../11-testing/index.md)

### More in this section

### [Secure Coding and Supply Chain](secure-coding-and-supply-chain.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Secure coding means writing code that resists common attacks, and supply-chain security means trusting only the third-party code you actually run. Interviewers ask about the...

