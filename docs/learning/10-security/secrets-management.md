# Secrets Management

A secret is any value that grants access: database passwords, API keys, signing keys, certificates, and tokens. Secrets management is about getting them to the running application without storing them in source code, images, or logs, and about changing them when they leak. Interviewers ask about this because a committed credential is one of the most common causes of real breaches.

## Core concepts

### Rule one: never commit secrets

Once a secret is in Git, assume it is compromised. Deleting the line in a later commit does not remove it from history, and clones and forks keep it. The fix is to rotate the secret, not only to edit the file.

Practical defences:

- Keep local config files with credentials out of Git (`.gitignore`).
- Run secret scanning in pull requests and on the server side, so commits with credentials are blocked.
- Use `.env.example`-style templates that contain placeholders, not values.

### Config from the environment

The twelve-factor approach stores config in environment variables, which keeps secrets out of the artefact. Spring Boot maps environment variables to properties with relaxed binding, so `DB_PASSWORD` can supply `spring.datasource.password` or a custom property.

```java
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.db")
public record DbProperties(String url, String username, String password) {

    // Records generate toString() from every component, which would print the password.
    // Override it so logs and error messages never show the value.
    @Override
    public String toString() {
        return "DbProperties[url=" + url + ", username=" + username + ", password=****]";
    }
}
```

Environment variables are better than files in the repository, but they are still visible to anyone who can inspect the process or its deployment definition. They are a starting point, not the end state.

### Dedicated secrets stores

A secrets manager encrypts secrets at rest, controls who can read them with access policies, records who accessed them, and supports rotation.

| Store | Notes |
|---|---|
| HashiCorp Vault | Self-hosted or managed; dynamic credentials and leases |
| AWS Secrets Manager | Managed AWS service; rotation with supported integrations |
| Azure Key Vault | Managed Azure service; keys, secrets, and certificates |
| Spring Cloud Vault | Spring integration that reads secrets from Vault into the Spring Environment |

Spring Boot 3 can import external configuration with `spring.config.import`, which lets a secret source feed properties at startup. Spring Cloud Vault builds on this for HashiCorp Vault. Check the current Spring Cloud documentation for the exact property names, because they change between releases.

### Kubernetes Secrets

Kubernetes `Secret` objects store values base64-encoded. Base64 is an encoding, not encryption. Unless encryption at rest is enabled for the cluster's data store, the values are readable by anyone with API access to the cluster. Restrict RBAC on Secret objects, and consider an external secrets operator that syncs from a managed store. Containers are covered in [Kubernetes](../16-kubernetes/index.md).

### Least privilege and short-lived credentials

Give each service its own credentials with only the permissions it needs. A payments service should not read the user-profile database password. Where possible, use short-lived credentials (dynamic database users, cloud IAM roles, workload identity) so there is nothing long-lived to steal.

### Rotation

Rotation replaces a secret on a schedule or after an incident. Plan it so that rotation does not cause downtime:

1. Create the new secret and make it valid alongside the old one.
2. Deploy consumers so they pick up the new value (restart or refresh).
3. Revoke the old secret once nothing uses it.

For signing keys (such as JWT keys), publish the new public key before signing with it, and keep the old key valid until tokens signed with it have expired.

### Keeping secrets out of logs and errors

Secrets leak through logs, stack traces, metrics labels, and error responses. Avoid logging request bodies and headers that contain credentials, mask values in configuration output, and keep actuator endpoints such as `/actuator/env` locked down (see [Actuator and API Documentation](../09-spring-boot/actuator-and-api-docs.md)).

### Wiring secrets into Spring Boot

Reference secrets by placeholder and do not give them defaults:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/orders
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}   # no default: startup fails if the variable is missing
```

A default such as `${DB_PASSWORD:changeme}` is a bug waiting to happen: a missing variable silently falls back to a known password. Failing at startup is the safer behaviour.

When secrets are mounted as files (a common Kubernetes pattern), Spring Boot can import a directory as properties with `configtree`:

```yaml
spring:
  config:
    import: "optional:configtree:/run/secrets/"
```

Each file name becomes a property key, and the file content becomes its value. Mark the import `optional:` only where a missing directory is acceptable (for example, local development).

### Rotating without downtime in practice

A rotation that works in staging can still fail in production if consumers cache the old value. Check these before rotating:

- Every consumer reads the secret at startup or through a refresh path you have tested.
- Connection pools that hold old credentials are recycled after the change.
- The old credential stays valid until the last consumer has switched.
- The rotation is recorded, with the owner and the date, so the next rotation is not a surprise.

For database passwords, many teams create a second database user, move services to it, and then disable the first one. That avoids changing the password under live connections.

### Scanning and prevention

Prevention is cheaper than cleanup:

- Enable secret scanning on the repository host and in CI, so a push with a credential-shaped string fails.
- Install a local pre-commit hook for scanning, for developers who want feedback before the push.
- Block committed `.env` files and key files by pattern in `.gitignore`.
- Give scanning findings an owner and a process to rotate, not only an alert.

## How it works / Step by step

1. The secret is created in a secrets store, with an access policy for the service.
2. At startup, the application (or its platform) authenticates to the store with an identity such as a workload role, not a stored password.
3. The store returns the secret, which is loaded into the Spring Environment or mounted as a file.
4. The application uses the secret without writing it to logs or source code.
5. On rotation, the store issues a new value, consumers reload, and the old value is revoked.

## Common pitfalls

- Committing a secret, then "fixing" it with a new commit and assuming it is gone.
- Storing secrets in Docker images or in build arguments that persist in image layers.
- Printing configuration objects, including records with default `toString()`.
- Sharing one database account across every service.
- Treating base64 Kubernetes Secrets as encrypted.
- Rotating a key in one place without updating consumers, causing an outage.
- Long-lived API keys with no owner and no expiry.

!!! tip "Interview tip"
    **Q: A developer accidentally committed a database password. What do you do?**
    Treat the password as compromised and rotate it immediately, in the database and in every consumer. Then remove it from the repository's history if policy requires, check access logs for misuse, and add secret scanning so the next commit is blocked. Removing the line alone is not a fix.

## Quick recap

- Never commit secrets; rotate any that were exposed.
- Inject secrets at runtime from environment variables or a secrets manager.
- Use least-privilege, short-lived credentials where possible.
- Plan rotation so it does not cause downtime.
- Keep secrets out of logs, errors, actuator output, and images.

**See also:** [Boot Basics and Configuration](../09-spring-boot/boot-basics-configuration.md) | [Password Security and OWASP](password-security-owasp.md) | [CI/CD Pipelines](../17-cicd/index.md)
