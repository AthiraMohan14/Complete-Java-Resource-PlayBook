# Spring Boot in Containers

A Spring Boot service becomes a container image by packaging its executable JAR into a base image. The hard part is the JVM: it must respect container memory and CPU limits, stop cleanly on SIGTERM, and run without root privileges. Interviewers often ask why a Java container is killed even though the heap looks small.

## Core concepts

### Building the image
There are two common routes.

1. **Cloud Native Buildpacks** (no Dockerfile needed). Spring Boot's Maven and Gradle plugins can build the image directly:
   ```bash
   ./mvnw spring-boot:build-image
   ./gradlew bootBuildImage
   ```
2. **A hand-written Dockerfile**, which gives full control over the base image, user, and layers.

The Spring Boot application class is ordinary Java. It needs only the web and actuator starters on the classpath:

```java
package com.example.orders;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class OrdersApplication {

    public static void main(String[] args) {
        SpringApplication.run(OrdersApplication.class, args);
    }
}

@RestController
class PingController {

    @GetMapping("/ping")
    String ping() {
        return "pong";
    }
}
```

### Layered JARs
A Spring Boot fat JAR is a single large file. Any code change rebuilds it, so the whole JAR is a new layer. Spring Boot can split the JAR into layers that change at different rates: third-party dependencies, the Spring Boot loader, snapshot dependencies, and application classes. Dependencies rarely change, so their layer stays cached.

```dockerfile
# Extract the layers
FROM eclipse-temurin:21-jre AS builder
WORKDIR /builder
COPY target/app.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

# Assemble the runtime image, least-changing layers first
FROM eclipse-temurin:21-jre
RUN useradd --system app
WORKDIR /app
COPY --from=builder /builder/dependencies/ ./
COPY --from=builder /builder/spring-boot-loader/ ./
COPY --from=builder /builder/snapshot-dependencies/ ./
COPY --from=builder /builder/application/ ./
USER app
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

The launcher class name depends on the Spring Boot version. Its package changed in newer Spring Boot 3.x releases, so check the documentation for your version before copying this line.

### Choosing a base image
The base image sets the size and attack surface of the runtime. Three options are common:

| Base image | Typical use | Trade-off |
|---|---|---|
| Full JDK (`eclipse-temurin:21`) | Building, not running | Largest; includes compilers and tools you do not need at runtime |
| JRE on a general Linux base (`eclipse-temurin:21-jre`) | Simple production images | Includes a shell and package tools, which helps debugging |
| Distroless Java (`gcr.io/distroless/java21-*`) | Hardened production images | Only the Java runtime and your app; no shell, so `docker exec sh` fails |

Distroless images suit production because they hold fewer packages that can carry known vulnerabilities. Their cost is debugging: you cannot open a shell in the container. Use a debug variant of the image in a test environment, or attach an ephemeral debug container (for example, `kubectl debug`) to a running pod. Pin the image tag, and check the tag list for a Debian base that is still maintained, because old tags stop receiving security updates.

### JVM memory in containers
Modern JVMs read the container's memory limit (cgroup) instead of the host's total memory. Even so, a fixed heap size is fragile. Prefer percentages:

```bash
JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:InitialRAMPercentage=50"
```

Keep headroom for non-heap memory. The container limit covers all of the process's memory, including:

- Metaspace (loaded classes)
- Thread stacks (one per thread)
- The code cache (JIT-compiled code)
- Direct buffers and native libraries

If the heap is set to the full limit, the process can exceed the limit and be killed by the kernel's OOM killer. Kubernetes reports this as `OOMKilled`, and Docker shows exit code 137.

The JVM also sizes its thread pools and garbage-collector threads from the available processors. Check what it sees:

```java
public class ContainerInfo {
    public static void main(String[] args) {
        Runtime rt = Runtime.getRuntime();
        System.out.println("Processors visible to the JVM: " + rt.availableProcessors());
        System.out.println("Max heap (MiB): " + rt.maxMemory() / (1024 * 1024));
    }
}
```

Run it with and without a `--cpus` limit to see the difference. `-XX:ActiveProcessorCount` overrides the detected value when you need to.

### Graceful shutdown
Orchestrators and `docker stop` send SIGTERM and then wait before killing the process. Spring Boot can finish in-flight requests during that window:

```yaml
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

For this to work, the Java process must receive SIGTERM. That is why the exec form of `ENTRYPOINT` matters. The platform's grace period must be longer than the Spring timeout, otherwise the process is killed first.

### Health endpoints for probes
With Spring Boot Actuator, the health endpoint can expose separate liveness and readiness groups:

```yaml
management:
  endpoint:
    health:
      probes:
        enabled: true
```

The endpoints are `/actuator/health/liveness` and `/actuator/health/readiness`. Map them to the container's health check or to Kubernetes probes.

### Configuration and secrets
Spring's relaxed binding lets environment variables override properties. For example, `SPRING_DATASOURCE_URL` sets `spring.datasource.url`. Secrets can be mounted as files and loaded with `spring.config.import`. Keep credentials out of the image and out of `application.yml` committed to version control.

### Running as a non-root user
Set `USER` to a non-root account and make sure the directories the app writes to are owned by that user. Running as non-root limits the damage from a compromised process. Combined with a read-only root filesystem, it reduces attack surface further.

## Container security best practices
A container image is a package that runs with whatever rights you grant it. Four habits cover most of the risk for a Spring Boot service.

### 1. Run as a non-root user
Create a system user in the Dockerfile and switch to it before the entrypoint. Use a numeric UID if the platform enforces `runAsNonRoot`.

```dockerfile
FROM eclipse-temurin:21-jre
RUN groupadd --system app && useradd --system --gid app app
WORKDIR /app
COPY target/app.jar app.jar
USER app
ENTRYPOINT ["java", "-jar", "app.jar"]
```

Give the user write access only to the directories it needs, such as a temporary directory.

### 2. Scan images for known vulnerabilities
Base images and Java libraries carry known CVEs. Scan each image in the build pipeline with a scanner such as Trivy, Grype, or the scanner built into your registry, and fail the build on high-severity findings that have fixes. Scanning is a point-in-time check, so rescan images that are already deployed, because new CVEs appear after a build.

### 3. Keep secrets out of the image
Anything written in a `RUN`, `COPY`, or `ARG` step stays in the image history, and anyone who pulls the image can read it. Passwords, tokens, and private keys belong at runtime instead:

- Inject them as environment variables or mounted files, from a Secret or a vault.
- For a secret needed only during build, such as a private repository token, use a BuildKit secret mount, which does not persist in a layer:

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=repo_token \
    ./mvnw -s settings.xml dependency:go-offline
```

Also add a `.dockerignore` file so that local `.env` files and key material are never copied into the build context.

### 4. Use a read-only root filesystem
Most services need to write only to a few paths. Mount the root filesystem as read-only, and give writable `emptyDir` volumes to the paths that need them. Spring Boot's embedded Tomcat and temporary-file handling use `/tmp`, so that path is the usual one to make writable.

```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
volumeMounts:
  - name: tmp
    mountPath: /tmp
volumes:
  - name: tmp
    emptyDir: {}
```

The same idea works outside Kubernetes with `docker run --read-only --tmpfs /tmp`.

### Also keep images small and tags pinned
Pin the base image to a specific tag rather than a floating one such as `latest`, so the build is repeatable and updates are deliberate. Multi-stage builds and a minimal runtime base reduce the number of packages that can carry vulnerabilities.

## How it works / Step by step
1. The build produces an executable JAR, or the buildpack builds one for you.
2. The image gets a JRE base, a non-root user, and the application layers, least-changing first.
3. At start, the JVM detects the container's memory and CPU limits and sizes the heap and thread pools.
4. Actuator exposes liveness and readiness endpoints for the platform to probe.
5. On SIGTERM, the server stops accepting new requests, finishes in-flight ones within the timeout, and exits.

## Common pitfalls
- Setting `-Xmx` to the full container limit. Non-heap memory then pushes the process over the limit.
- Using shell-form `ENTRYPOINT`, so SIGTERM never reaches the JVM and requests are cut off.
- Running as root, or writing to directories the non-root user cannot access.
- Copying the whole build directory into the image, including tests and build caches.
- Logging to a file inside the container instead of stdout, so logs disappear with the container.
- Baking configuration and credentials into the image, which forces a rebuild for every environment.

!!! tip "Interview tip"
    **Q: Why is my Java container killed with exit code 137 when the heap is small?**
    Exit code 137 means SIGKILL, usually from the OOM killer. The container limit covers the whole process, including metaspace, thread stacks, and direct buffers, not just the heap. Set `MaxRAMPercentage` with headroom, and measure native memory with `-XX:NativeMemoryTracking=summary` to see where it goes.

## Quick recap
- Build with buildpacks or a Dockerfile; layered JARs keep dependency layers cached.
- Use percentage-based heap settings and leave room for non-heap memory.
- The JVM reads container limits, but processor and memory sizing still need checking.
- Exec-form `ENTRYPOINT` plus `server.shutdown=graceful` gives clean shutdowns.
- Actuator probe endpoints feed liveness and readiness checks; run as a non-root user.

**See also:** [Docker Fundamentals](docker-fundamentals.md), [Containers and Compose](containers-and-compose.md), [Config, Storage and Health](../16-kubernetes/config-storage-health.md)
