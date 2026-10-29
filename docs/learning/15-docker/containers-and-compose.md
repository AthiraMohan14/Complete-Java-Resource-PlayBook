# Containers and Compose

Running one container is simple. Running an application that needs a database, a cache, and a broker, with data that survives restarts and services that can find each other, requires understanding volumes, networks, health checks, and Compose. Interviewers often ask how containers reach each other and where data lives after a container is removed.

## Core concepts

### Running containers with `docker run`
A typical run command combines the options that matter most in practice:

```bash
docker run -d --name orders \
  -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=prod \
  -v orders-data:/var/lib/orders \
  --network app-net \
  --memory 512m --cpus 1 \
  --restart unless-stopped \
  orders-service:1.4.0
```

| Option | Meaning |
|---|---|
| `-d` | Run detached, in the background |
| `--name` | Give the container a stable name for DNS and commands |
| `-p host:container` | Publish a container port on a host port |
| `-e` | Set an environment variable |
| `-v` | Mount a volume or bind mount |
| `--network` | Attach to a named network |
| `--rm` | Remove the container when it exits |
| `--memory`, `--cpus` | Set cgroup limits |
| `--restart` | Restart policy after exit or daemon restart |

`-p` publishes a port to the host. Publishing a database port this way exposes it on the host's interfaces, which is a common production mistake.

### Volumes: bind mounts, named volumes, tmpfs
A container's writable layer disappears with the container. Use a volume for any data that must survive.

| Type | Where data lives | Typical use |
|---|---|---|
| Bind mount | A path you choose on the host | Mounting source code during development |
| Named volume | Managed by Docker | Database files and other state |
| tmpfs | Host memory, never written to disk | Temporary secrets or scratch space |

Bind mounts depend on the host's directory layout and file ownership. Named volumes are the portable default for state.

### Container networking
Docker provides several network drivers.

- **bridge**: the default for a single host. A *user-defined* bridge network also gives containers DNS resolution by container or service name. The default bridge does not.
- **host**: the container shares the host's network stack. There is no port isolation.
- **overlay**: spans several Docker hosts and is used by orchestrators.
- **none**: no networking.

Inside a container, `localhost` means the container itself. A service in one container cannot reach a database on the host or in another container through `localhost`. Use the service name on a shared network instead. The following check connects using the Compose service name `postgres`, which Docker's DNS resolves:

```java
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DbCheck {
    public static void main(String[] args) throws SQLException {
        // "postgres" is the Compose service name, resolved by Docker's DNS
        String url = "jdbc:postgresql://postgres:5432/orders";
        String password = System.getenv("DB_PASSWORD");
        try (Connection c = DriverManager.getConnection(url, "app", password)) {
            System.out.println("Connected: " + c.isValid(2));
        }
    }
}
```

The class compiles with the JDK alone. Running it needs the PostgreSQL JDBC driver on the classpath.

### Health checks, logs, and exec
A Dockerfile can declare a health check. Docker then reports the container as `starting`, `healthy`, or `unhealthy`.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS http://localhost:8080/actuator/health || exit 1
```

The image must contain `curl` for this to work. Docker's health status is useful for Compose dependency conditions and for humans. Orchestrators such as Kubernetes use their own probes instead (see the Kubernetes section).

Everyday debugging commands:

- `docker logs -f orders` follows the container's stdout and stderr.
- `docker exec -it orders sh` opens a shell inside a running container. Use `bash` if the image has it.
- `docker inspect orders` shows the full configuration, networks, mounts, and health status.

### Docker Compose
Compose describes a multi-container application in one YAML file that follows the Compose Specification. Modern Compose does not require the old top-level `version:` key. The preferred file name is `compose.yaml`, and `docker-compose.yml` is still supported.

```yaml
services:
  orders:
    build: .
    ports:
      - "8080:8080"
    environment:
      DB_PASSWORD: ${DB_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
    networks: [app-net]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: orders
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d orders"]
      interval: 5s
      retries: 10
    networks: [app-net]

volumes:
  pg-data:

networks:
  app-net:
```

Key points:

- `services`, `networks`, and `volumes` are the three main top-level sections.
- `depends_on` with `condition: service_healthy` waits for the database health check. A plain `depends_on` only controls start order, not readiness.
- `${DB_PASSWORD}` is substituted from the shell or a `.env` file. Do not commit real values.
- Compose creates the networks and volumes if they are missing and gives each service a DNS name.

### Environment-specific configuration
Compose offers three ways to vary a setup:

- **Multiple files**: `docker compose -f compose.yaml -f compose.prod.yaml up` merges the files in order, with later files overriding earlier ones.
- **Override file**: a `compose.override.yaml` in the same directory is merged automatically for local development.
- **Profiles**: services tagged with `profiles:` start only when that profile is enabled, which suits optional tools such as admin consoles.

## Common pitfalls
- Connecting to `localhost` from inside a container.
- Assuming `depends_on` waits for the database to be ready. Add a `condition` and a health check.
- Running `docker compose down -v`, which deletes named volumes and their data.
- Bind-mounting a host directory whose ownership does not match the container user.
- Publishing internal ports such as a database to all host interfaces.
- Committing secrets into `compose.yaml` instead of using an environment file or a secrets mechanism.

!!! tip "Interview tip"
    **Q: How do two containers on the same host find each other?**
    Put both on a user-defined bridge network. Docker's embedded DNS resolves container and service names to their addresses. Follow-up: why does a connection to `localhost` fail? Because `localhost` is the calling container's own network namespace, not the other container.

## Quick recap
- `docker run` options control ports, environment, volumes, networks, and resource limits.
- Named volumes hold state that must outlive a container; bind mounts suit development.
- User-defined bridge networks provide DNS by container or service name.
- Compose declares services, networks, and volumes in one file, with health-based dependencies.
- Keep data safe: avoid `down -v` and keep secrets out of version control.

**See also:** [Docker Fundamentals](docker-fundamentals.md), [Spring Boot in Containers](spring-boot-in-containers.md), [Config, Storage and Health](../16-kubernetes/config-storage-health.md)
