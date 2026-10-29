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
