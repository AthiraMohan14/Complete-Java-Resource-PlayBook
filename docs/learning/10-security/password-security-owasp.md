# Password Security and the OWASP Top 10

Password storage is one of the first things an interviewer checks, because a database leak is the worst case for a login system. The correct answer is an adaptive, salted hash, never plain text and never a fast hash such as MD5 or SHA-256 on its own. The OWASP Top 10 is the standard list of web application risk categories, and interviewers use it to check whether you can name the common risks and their defences.

## Core concepts

### Hashing, encryption, and HMAC

These three terms are easy to mix up:

- **Hashing** is one-way. A hash cannot be reversed, which suits password storage (with a salt and an adaptive algorithm) and integrity checks, such as the SHA-256 of a downloaded file.
- **Encryption** is reversible with a key. Symmetric algorithms such as AES use one key for both directions. Asymmetric algorithms such as RSA and ECC use a public and a private key. Encryption gives confidentiality, but it does not by itself prove who sent a message.
- **HMAC** is a keyed hash. Only holders of the secret can produce or check the tag, so it shows that a message is intact and came from a party with the key. Webhook providers commonly sign payloads this way.

When you check an HMAC, compare the expected and received tags in constant time. An ordinary `equals` returns early at the first mismatch, and the timing can reveal how much of the tag was correct.

```java
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class PayloadSigner {

    public static String sign(byte[] secret, String payload) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret, "HmacSHA256"));
        return HexFormat.of().formatHex(mac.doFinal(payload.getBytes(StandardCharsets.UTF_8)));
    }

    public static boolean isValid(byte[] secret, String payload, String receivedHex) throws Exception {
        byte[] expected = sign(secret, payload).getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(expected, receivedHex.getBytes(StandardCharsets.UTF_8));
    }
}
```

`HexFormat` needs Java 17 or later. The same constant-time rule applies to API keys, reset tokens, and any other secret you compare.

### Why fast hashes are wrong for passwords

A general-purpose hash (SHA-256, for example) is designed to be fast. An attacker with a leaked table and a GPU can test billions of guesses per second. A password hash must be slow and tunable, so that each guess costs real computation. Adaptive algorithms let you raise the cost as hardware improves.

### Salts and peppers

A salt is random data unique to each password. It is stored with the hash, and it stops identical passwords from producing identical hashes and defeats precomputed tables. A pepper is a secret value kept outside the database (in a secrets store or configuration). It is applied on top of the hash, so a database leak alone is not enough to attack the passwords. Losing the pepper makes existing hashes unverifiable, so plan key management for it.

### Choosing an algorithm

| Algorithm | Notes |
|---|---|
| BCrypt | Widely used and well understood; input is limited to 72 bytes |
| Argon2 (Argon2id) | Memory-hard; the modern recommendation where available. Spring's encoder needs Bouncy Castle on the classpath |
| SCrypt | Memory-hard; tunable CPU and memory cost |
| PBKDF2 | Standard, FIPS-approved; needs a high iteration count |

The exact cost parameters should follow current guidance from OWASP's password storage cheat sheet, which is updated over time.

### Spring Security password encoders

`PasswordEncoder` hides the algorithm. `DelegatingPasswordEncoder` prefixes each stored hash with its algorithm id (for example `{bcrypt}`), so you can migrate algorithms without forcing a password reset for every user.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
class PasswordConfig {

    @Bean
    PasswordEncoder passwordEncoder() {
        return PasswordEncoderFactories.createDelegatingPasswordEncoder();
    }
}
```

```java
import org.springframework.security.crypto.password.PasswordEncoder;

class Registration {
    private final PasswordEncoder encoder;

    Registration(PasswordEncoder encoder) {
        this.encoder = encoder;
    }

    String hashForStorage(String rawPassword) {
        return encoder.encode(rawPassword);   // stores something like "{bcrypt}$2a$..."
    }

    boolean isCorrect(String rawPassword, String storedHash) {
        return encoder.matches(rawPassword, storedHash);   // constant-time comparison
    }
}
```

Never compare hashes with `equals`. Always use `matches`, which handles salts and runs in constant time.

### Password policy and login protection

Current guidance (NIST SP 800-63B) favours length over composition rules, such as "one symbol and one digit". It also recommends checking new passwords against lists of known-breached passwords, and not forcing periodic changes without a reason. Pair the hashing with:

- Rate limiting on login attempts, per account and per source address.
- Progressive delays or temporary lockouts, with care to avoid locking out real users as a denial-of-service path.
- Generic error messages, so the response does not reveal whether an account exists.
- MFA (see [Authentication](authentication-jwt-oauth.md)).

### OWASP Top 10 (2021 edition)

The OWASP Top 10 is a list of the most critical web application risk categories. The 2021 edition is the reference for this section. OWASP updates the list periodically, so check the current version before quoting it in an interview.

| Category | Example defence |
|---|---|
| A01 Broken Access Control | Deny by default; check permissions on the server for every request |
| A02 Cryptographic Failures | Encrypt data in transit and at rest; use current algorithms and key management |
| A03 Injection (including XSS) | Parameterised queries; context-aware output encoding |
| A04 Insecure Design | Threat modelling before coding; secure design patterns |
| A05 Security Misconfiguration | Hardened defaults; remove unused features and endpoints |
| A06 Vulnerable and Outdated Components | Dependency scanning (software composition analysis); keep libraries updated |
| A07 Identification and Authentication Failures | MFA; strong password hashing; secure session management |
| A08 Software and Data Integrity Failures | Avoid unsafe deserialisation; verify artefact signatures |
| A09 Security Logging and Monitoring Failures | Log security events; alert on them |
| A10 Server-Side Request Forgery (SSRF) | Allow-list outbound destinations; block internal address ranges |

### Injection in Java, in one example

SQL injection happens when user input is concatenated into a query. Parameterised queries prevent it because the driver sends the value separately from the SQL text.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

class CustomerLookup {
    String findName(Connection conn, String email) throws SQLException {
        String sql = "SELECT name FROM customer WHERE email = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, email);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getString("name") : null;
            }
        }
    }
}
```

The same principle applies to JPA and JPQL: use named or positional parameters, never string concatenation.

## How it works / Step by step

1. At registration, the server calls `encode(rawPassword)`, which generates a random salt and runs the adaptive algorithm.
2. The encoded string (algorithm id, cost parameters, salt, and hash) is stored. The raw password is discarded.
3. At login, `matches(raw, stored)` re-derives the hash with the stored salt and parameters and compares the results in constant time.
4. If the algorithm or cost changed, you can re-hash the password on the user's next successful login.

## Defensive checklist

Most application defences fall into a few families. Use this table when you review a design.

| Risk | Defence | Where to read more |
|---|---|---|
| SQL injection | Parameterised queries; allow-lists for identifiers | [JDBC](../07-jdbc-jpa/jdbc.md) |
| Cross-site scripting (XSS) | Output encoding for the context; a Content Security Policy | [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md) |
| Cross-site request forgery (CSRF) | Anti-CSRF tokens for cookie-authenticated requests; `SameSite` cookies | [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md) |
| Excess privilege | Least privilege per service and per user; deny by default | [Spring Security Authorisation](spring-security-authorisation.md) |
| Leaked credentials | A secrets store, injection at runtime, and rotation | [Secrets Management](secrets-management.md) |
| Eavesdropping | TLS 1.2 or later everywhere; HSTS | [CORS, CSRF, TLS, and Security Headers](cors-csrf-tls-headers.md) |
| Personal data in logs | Mask or omit personal data and secrets in logs and error responses | [Secrets Management](secrets-management.md) |
| Vulnerable libraries | Dependency scanning in the build; timely upgrades | [Secure Coding and Supply Chain](secure-coding-and-supply-chain.md) |
| Timing attacks on secrets | Constant-time comparison (`MessageDigest.isEqual`) | [Hashing, encryption, and HMAC](#hashing-encryption-and-hmac) |
| Brute force on login | Rate limiting per account and per source; careful lockouts | [Password policy and login protection](#password-policy-and-login-protection) |

Mask personal data as well as credentials in logs. An e-mail address or a card number in a log line is a breach in its own right.

## Common pitfalls

- Storing passwords with reversible encryption instead of a one-way hash.
- Using SHA-256 or MD5 for passwords.
- BCrypt with very long passwords: input beyond 72 bytes is ignored, so a long passphrase may be truncated. Limit the maximum length or pre-hash.
- Hard-coded salts, or one salt shared across users.
- Logging passwords, even on failed login attempts.
- Enumerating accounts through different error messages or timing.
- Treating the OWASP list as a checklist to finish rather than a set of categories to reason about.

!!! tip "Interview tip"
    **Q: How would you store user passwords?**
    Hash each password with an adaptive, memory-hard or cost-tunable algorithm (Argon2id, BCrypt, or SCrypt). Each hash gets a unique random salt, and the algorithm is stored with it so you can migrate later. Use `matches` for verification, add rate limiting on login, and consider a pepper kept outside the database.

## Quick recap

- Use adaptive, salted password hashes; never fast hashes or reversible encryption.
- Spring's `DelegatingPasswordEncoder` lets you migrate algorithms over time.
- Rate-limit logins and return generic errors.
- Know the OWASP Top 10 categories and one concrete defence for each.
- Parameterise every query; injection is still a top risk.

**See also:** [Spring Security Authorisation](spring-security-authorisation.md) | [Authentication: JWT, OAuth 2.0, and OpenID Connect](authentication-jwt-oauth.md) | [Secrets Management](secrets-management.md)
