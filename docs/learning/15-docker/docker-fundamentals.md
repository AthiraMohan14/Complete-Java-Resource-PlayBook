# Docker Fundamentals

A container is an isolated process, or group of processes, started from an image and sharing the host's Linux kernel. Interviewers ask about Docker to see whether you understand what a container actually is, why it differs from a virtual machine, and how image layers affect builds, not just which commands to type.

## Core concepts

### Containers versus virtual machines
A virtual machine runs a full guest operating system on a hypervisor. A container runs as an ordinary host process that is restricted with kernel features. Because containers do not boot an OS, they start faster and carry less overhead. A VM gives a stronger isolation boundary and can run a different kernel.

| Aspect | Container | Virtual machine |
|---|---|---|
| Kernel | Shared with the host | Its own guest kernel |
| Isolation | Process level, via kernel features | Hardware level, via a hypervisor |
| Startup | Usually fast, since no OS boots | Usually slower, since a full OS boots |
| Image contents | Application plus its libraries | Application plus a full OS |

### Namespaces and cgroups
Two Linux features make containers work.

- **Namespaces** control what a process can see. Docker uses PID, network, mount, UTS (hostname), IPC, and user namespaces.
- **cgroups** (control groups) control and account for what a process can use, such as CPU, memory, I/O, and process count.

You can see the PID namespace at work. Inside the container, the first process is PID 1:

```bash
docker run --rm alpine ps
```

### Images and layers
An image is a stack of read-only layers plus metadata, such as the default command, environment variables, and exposed ports. Each Dockerfile instruction that changes the filesystem adds a layer. When you run a container, Docker adds a thin writable layer on top. Anything written there is lost when the container is removed.

Layers are cached and shared between images. Order matters: put slow, rarely changing steps (installing dependencies) before fast, frequently changing steps (copying source code). Otherwise every source edit invalidates the cache for the dependency download.

Image tags are mutable pointers, so `my-app:1.4.0` can be moved to a different image. A digest (`my-app@sha256:...`) identifies exact content and never changes.

### Dockerfile instructions

| Instruction | Purpose |
|---|---|
| `FROM` | Base image. Every build stage starts with one. |
| `RUN` | Runs a command at build time and records the result as a layer. |
| `COPY` | Copies files from the build context into the image. Predictable. |
| `ADD` | Like `COPY`, plus URL fetching and automatic tar extraction. Use `COPY` unless you need extraction. |
| `WORKDIR` | Sets the working directory for later instructions. |
| `ENV` | Sets an environment variable in the image. |
| `EXPOSE` | Documents a listening port. It does not publish the port. |
| `USER` | Sets the user the container runs as. |
| `ENTRYPOINT` | The executable that always runs. |
| `CMD` | Default arguments, or the command when no `ENTRYPOINT` is set. Overridable at `docker run`. |

Prefer the **exec form** (a JSON array) for `ENTRYPOINT` and `CMD`. The exec form runs your process directly as PID 1, so it receives signals such as SIGTERM. The **shell form** wraps the command in `/bin/sh -c`, and signals may never reach your application.

```dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY target/app.jar app.jar
USER 1001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

A tiny Java program to run inside such an image:

```java
public class Main {
    public static void main(String[] args) {
        String greeting = System.getenv().getOrDefault("GREETING", "Hello");
        System.out.println(greeting + " from inside a container");
    }
}
```

### Multi-stage builds
A multi-stage build uses one stage to compile and a second stage that holds only the runtime. Compilers, build tools, and source code stay out of the final image. The result is smaller and has less attack surface.

```dockerfile
# Stage 1: build with the full JDK
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY . .
RUN ./mvnw -q package -DskipTests

# Stage 2: runtime only
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/app.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

This example assumes the build produces `target/app.jar`. Dependencies are re-downloaded whenever `COPY . .` changes. A later refinement copies only the build descriptor first so the dependency layer stays cached.

### Image references, tags, and registries
A full image reference has the form `[registry/]namespace/name[:tag][@digest]`. Docker Hub is the default registry. Teams also use private registries, hosted by a cloud provider or run themselves. The commands are `docker pull`, `docker tag`, and `docker push`.

Pin specific tags in production and avoid `latest`, which changes without warning.

### Container lifecycle
A container moves through the states *created*, *running*, *stopped* (exited), and *removed*. `docker run` is shorthand for `docker create` followed by `docker start`.

- `docker stop` sends SIGTERM, waits for a timeout, then sends SIGKILL.
- `docker kill` sends a signal immediately, SIGKILL by default.
- `docker rm` removes a stopped container and its writable layer.

### Build context and `.dockerignore`
The build context is the directory sent to the Docker daemon when you build. Everything in it is available to `COPY`, and a large context slows every build. A `.dockerignore` file excludes paths from the context:

```text
.git
target/
*.log
.env
```

Excluding `.env` and `.git` keeps local secrets and history out of the image, even when a later `COPY . .` would otherwise pick them up.

### Build arguments versus environment variables
`ARG` defines a value available only during the build, such as a version number used in a label. `ENV` persists into the running container. Do not pass secrets through either: build arguments can appear in the image history, so use build-time secret mounts instead when a build needs a credential.

### Reading layers with `docker history`
`docker history <image>` lists each layer with its size and the instruction that created it. It is the quickest way to find which step made an image large, and it would also reveal a secret that was copied in and then deleted.

### Resource limits
`docker run --memory 512m --cpus 1` sets cgroup limits on the container. Memory above the limit causes the kernel's OOM killer to stop the process, and Docker reports exit code 137 for a SIGKILL. CPU limits throttle the container rather than killing it. Without limits, one container can starve the others on the same host. The JVM-specific details are in the Spring Boot in Containers page.

### PID 1 and signals
The first process in a container is PID 1, and the Linux kernel treats it specially: it does not get default signal handling, so a signal with no handler can be ignored. An application that is not written to handle SIGTERM may keep running until Docker escalates to SIGKILL after the timeout. Two fixes help:

- Use the exec form so the application is PID 1 and can install a handler.
- Use a small init process, such as Docker's `--init` flag, which forwards signals and reaps zombie processes.

The JVM handles SIGTERM by running shutdown hooks, which makes it well suited to this model when it is PID 1.

## Common pitfalls
- Using the `latest` tag in production, which makes deployments non-reproducible.
- Running as root, which is the default unless you set `USER`.
- Copying all source before installing dependencies, which defeats layer caching.
- Putting secrets in `ENV`, `ARG`, or a `COPY`'d file. Deleting a file in a later layer does not remove it from the earlier layer, so the secret stays in the image history.
- Using shell-form `CMD` or `ENTRYPOINT`, which can stop SIGTERM from reaching the Java process.
- Skipping `.dockerignore`, which sends large or sensitive directories in the build context.

!!! tip "Interview tip"
    **Q: What is the difference between a container and a VM?**
    A container is a process isolated with namespaces and limited with cgroups, sharing the host kernel. A VM runs its own kernel on a hypervisor. Containers are lighter and start faster; VMs isolate more strongly and can run a different kernel.

## Quick recap
- A container is a host process isolated by namespaces and limited by cgroups.
- Images are stacks of cached, read-only layers; order instructions for cache reuse.
- Prefer exec-form `ENTRYPOINT` so the app receives SIGTERM.
- Multi-stage builds keep build tools out of the runtime image.
- Pin tags, run as a non-root user, and keep secrets out of layers.

**See also:** [Containers and Compose](containers-and-compose.md), [Spring Boot in Containers](spring-boot-in-containers.md), [Kubernetes Architecture and Objects](../16-kubernetes/kubernetes-architecture-objects.md)
