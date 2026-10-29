# Secure Coding and Supply Chain

Secure coding means writing code that resists common attacks, and supply-chain security means trusting only the third-party code you actually run. Interviewers ask about the OWASP Top 10 to see whether you can name the common risks, match each one to a defence, and reason about dependencies that you did not write.

## Core concepts

### OWASP Top 10 (2021)

The OWASP Top 10 is a consensus list of the most critical categories of web application security risk. The 2021 edition is the reference used here. OWASP updates the list periodically, so check the current edition before quoting it in an interview.

1. **Broken access control.** Users can act outside their permissions, such as viewing another customer's order by changing an ID.
2. **Cryptographic failures.** Sensitive data is sent or stored without adequate encryption, or with weak algorithms and keys. This category was previously called "sensitive data exposure".
3. **Injection.** Untrusted input is interpreted as code or query syntax, including SQL, OS commands, and LDAP.
4. **Insecure design.** The flaw is in the design itself; no implementation can fix a missing control.
5. **Security misconfiguration.** Default accounts, verbose errors, open cloud storage, or unnecessary features are left enabled.
6. **Vulnerable and outdated components.** Libraries or platforms with known flaws remain in use.
7. **Identification and authentication failures.** Weak passwords, missing brute-force protection, or poor session handling.
8. **Software and data integrity failures.** Code or data is trusted without verifying its origin or integrity, for example unsigned updates or untrusted deserialisation.
9. **Security logging and monitoring failures.** Attacks go unnoticed because events are not logged or alerts are not raised.
10. **Server-side request forgery (SSRF).** The server is tricked into requesting URLs chosen by an attacker, often to reach internal services.

### Common attacks and defences

| Attack | Primary defence |
|--------|-----------------|
| SQL injection | Parameterised queries (prepared statements) and ORMs that bind parameters |
| Cross-site scripting (XSS) | Context-aware output encoding, a Content Security Policy, and input sanitising where HTML is allowed |
| Cross-site request forgery (CSRF) | Anti-CSRF tokens and `SameSite` cookie attributes |
| SSRF | Allow-list outbound hosts and block internal address ranges |
| Broken access control | Server-side authorisation on every request, deny by default |
| Sensitive data exposure | TLS in transit, encryption at rest, and masking personal data in logs |

Parameterised queries separate code from data. The database receives the SQL text and the values separately, so input can never change the statement's structure:

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

class CustomerLookup {
    // Unsafe alternative: "SELECT ... WHERE email = '" + email + "'" lets input rewrite the query.
    String findName(Connection connection, String email) throws SQLException {
        String sql = "SELECT full_name FROM customers WHERE email = ?";
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, email);
            try (ResultSet rows = statement.executeQuery()) {
                return rows.next() ? rows.getString("full_name") : null;
            }
        }
    }
}
```

An outbound-request allow-list defends against SSRF. The check runs on the parsed host, and the list is explicit:

```java
import java.net.URI;
import java.util.Set;

class OutboundUrlPolicy {
    private static final Set<String> ALLOWED_HOSTS = Set.of("api.payments.example.com");

    boolean isAllowed(String rawUrl) {
        URI uri = URI.create(rawUrl);
        return "https".equalsIgnoreCase(uri.getScheme())
                && uri.getHost() != null
                && ALLOWED_HOSTS.contains(uri.getHost());
    }
}
```

Real SSRF defence also resolves the host and blocks private, loopback, and link-local addresses, and it guards against redirects that leave the allow-list. The snippet shows the shape of the check, not a complete control.

### Validating input at the boundary

Validate input as soon as it crosses into the system, and accept only what you expect. An allow-list of a known format is stronger than a block-list of bad characters, because the attacker only has to find one character you forgot.

```java
import java.util.regex.Pattern;

class OrderIdValidator {
    private static final Pattern ORDER_ID = Pattern.compile("ORD-\\d{4}-[A-Z]{2}");

    static String requireOrderId(String raw) {
        if (raw == null || !ORDER_ID.matcher(raw).matches()) {
            // Do not echo the raw value back; it may be used for injection.
            throw new IllegalArgumentException("Invalid order id");
        }
        return raw;
    }
}
```

Validation does not replace output encoding or parameterised queries. Each sink still needs its own protection, because the same string can be safe in one context and dangerous in another.

### Secrets and configuration

- Keep passwords, API keys, and signing keys out of source control, container images, and logs.
- Inject secrets at runtime from a vault or the platform's secret store, and limit which services can read each one.
- Use separate credentials per environment, so a leak from development does not expose production.
- Revoke and rotate credentials after an employee leaves or a value may have been exposed.
- Turn off debug endpoints, sample accounts, and verbose stack traces in production builds.

### Dependency and supply-chain security

Most of a modern application is code you did not write. Its security is the weakest link you import.

- **Scan dependencies for known vulnerabilities.** Tools such as OWASP Dependency-Check, Snyk, Wiz, or Prisma Cloud compare your versions with vulnerability databases.
- **Pin versions and upgrade deliberately.** Use a lock file or a dependency management section so every build resolves the same, known-good versions. Move to a non-vulnerable version when a fix is published.
- **Watch advisories.** Log4Shell (CVE-2021-44228) showed how a single widely used library can expose thousands of systems within days. The CISA Known Exploited Vulnerabilities catalogue lists flaws that attackers are actively using and should be prioritised.
- **Verify what you download.** Check checksums or signatures, and prefer packages from trusted repositories.
- **Limit the attack surface.** Remove unused dependencies; a library you do not ship cannot be exploited through your application.
- **Know what you ship.** A software bill of materials (SBOM) lists the components in a release, so you can answer "are we affected?" quickly when a new advisory appears.
- **Protect the build.** Restrict who can publish or change pipeline steps and secrets. A compromised build can inject code without touching the source.

### Secure coding principles

- **Least privilege.** Give each user, service, and database account only the access it needs.
- **Defence in depth.** Do not rely on one control; layer validation, authorisation, encryption, and monitoring.
- **Fail securely.** When a check errors out, deny the request rather than allowing it.
- **Validate at trust boundaries.** Check input where it enters the system: HTTP requests, message consumers, files, and third-party responses.
- **Never trust client input.** Hidden form fields, client-side checks, and client-supplied roles are all under the attacker's control.
- **Keep secrets in a vault, not in code.** Use a secrets manager and inject values at runtime. Rotate credentials on a schedule and after any suspected exposure.
- **Use constant-time comparison for secrets.** Comparing tokens or MACs with a normal equality check can leak timing information. In Java, `MessageDigest.isEqual` performs a constant-time comparison of byte arrays.
- **Log security events, not secrets.** Record logins, failed attempts, and permission changes with enough context to investigate, but never log passwords, tokens, or full card numbers.

## How it works / Step by step

When reviewing a change for security:

1. Identify every input that comes from outside the trust boundary.
2. Check each input for the right validation and encoding for where it will be used (SQL, HTML, URL, shell).
3. Confirm every endpoint enforces authorisation on the server side.
4. Check the new or changed dependencies: are they needed, current, and free of known advisories?
5. Confirm secrets come from the vault and that errors do not leak stack traces or internal hostnames.
6. Make sure the new behaviour produces logs and alerts useful for detecting abuse.

## Common pitfalls

- Relying on a web application firewall alone instead of fixing the code.
- Building SQL with string concatenation, even for "internal" values.
- Trusting a role or price sent by the client.
- Checking authorisation in the UI but not in the API.
- Upgrading a library without checking whether the transitive dependencies changed.
- Leaving debug endpoints or default credentials enabled in production.
- Logging a full request body, which may contain passwords or tokens.

!!! tip "Interview tip"
    **Q: How do you prevent SQL injection in a Java application?**
    Use parameterised queries through `PreparedStatement` or an ORM that binds parameters. Never build SQL by concatenating user input. Add least-privilege database accounts so that any residual flaw does less damage.

## Quick recap

- Know the OWASP Top 10 (2021) categories and map each one to a defence.
- Parameterised queries stop SQL injection by separating code from data.
- SSRF defences allow-list outbound destinations and block internal address ranges.
- Scan dependencies, pin versions, watch advisories, and keep an SBOM.
- Apply least privilege, defence in depth, fail-secure behaviour, and server-side validation.
- Store secrets in a vault and compare them in constant time.

**See also:** [Authentication, JWT, and OAuth](authentication-jwt-oauth.md), [Secrets Management](secrets-management.md), [CORS, CSRF, TLS, and Headers](cors-csrf-tls-headers.md), [Web Fundamentals](../foundations/web-fundamentals.md)
