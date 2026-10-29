# Docker and Containerisation

Containers package an application with the runtime pieces it needs, so the same artifact runs on a laptop, in CI, and on a server. This section covers what a container really is, how images are built and run, how Compose wires several containers together, and how to containerise a Spring Boot service safely.

---

## Topics

### [Docker Fundamentals](docker-fundamentals.md)
**containers - namespaces - cgroups - images - layers - Dockerfile - multi-stage builds**
What a container is compared with a virtual machine, how Linux isolates it, how image layers work, and how Dockerfiles build images.

### [Containers and Compose](containers-and-compose.md)
**docker run - volumes - bridge networks - health checks - Compose**
Operating containers day to day, keeping data in volumes, container networking, and multi-container setups with Compose.

### [Spring Boot in Containers](spring-boot-in-containers.md)
**layered JARs - buildpacks - JVM memory limits - non-root - graceful shutdown**
Packaging a Spring Boot service as an image, making the JVM respect container limits, and stopping cleanly on SIGTERM.
