# DevOps, Cloud, Observability, and AI Questions (Part 1 of 3)

Questions on containers, Kubernetes, CI/CD, cloud platforms, observability, and the basics of LLM and retrieval-augmented generation (RAG) work. Cloud product names change often; learn the categories first and the product names second.

---


This page is split into 2 parts. Continue to [Part 2](devops-cloud-and-ai-part-2.md).

## 1. What is the difference between a container and a virtual machine?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A virtual machine runs its own guest operating system kernel on virtualised hardware. A container shares the host kernel and isolates processes with Linux namespaces (what a process can see) and cgroups (how much it can use). Containers start faster and use less memory, but they offer a weaker isolation boundary than a VM.

### Explanation
| | Virtual machine | Container |
|---|---|---|
| Kernel | Own guest kernel | Shared host kernel |
| Start time | Seconds to minutes | Usually well under a second |
| Isolation | Strong (hypervisor) | Process-level (namespaces, cgroups) |
| Size | Gigabytes (OS included) | Often megabytes to hundreds of megabytes |

### When to use / pitfalls
- Containers running untrusted multi-tenant code need extra hardening, such as user namespaces, seccomp profiles, or a sandboxed runtime.
- Containers do not replace an OS patching process; base images still need updates.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 2. How do Docker images and layers work, and how do you make images small?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Each Dockerfile instruction that changes the filesystem creates a layer, and layers are cached and shared between images. Put rarely changing steps first so that cache is reused. A multi-stage build compiles in a full build image and copies only the artefact into a smaller runtime image.

### Explanation
```dockerfile
# Build stage: full JDK and Maven, discarded afterwards
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q dependency:go-offline
COPY src ./src
RUN mvn -q package -DskipTests

# Runtime stage: a JRE-sized base image and the built jar only
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/app.jar app.jar
USER 10001                       # run as a non-root user ID
ENTRYPOINT ["java", "-jar", "app.jar"]
```

Copy `pom.xml` before `src` so the dependency layer is reused when only code changes. `EXPOSE` documents a port but does not publish it; use `-p` at run time.

### When to use / pitfalls
- Prefer `COPY` over `ADD` unless you need its extraction or URL features.
- Never put secrets in a `RUN` or `ENV` instruction; they remain in the image history. Use build secrets or runtime injection.
- Pin base image versions so builds are repeatable.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 3. How do you run a Java service well inside a container?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Modern JVMs read container CPU and memory limits, so the heap follows the container limit. Set heap size as a percentage of available memory with `-XX:MaxRAMPercentage`, leave room for non-heap memory, run as a non-root user, and handle `SIGTERM` for graceful shutdown.

### Explanation
```bash
java -XX:MaxRAMPercentage=75.0 -jar app.jar
```

Leave headroom: a 75% heap leaves space for metaspace, thread stacks, and native buffers. Spring Boot can also build layered jars so Docker caches the dependency layers separately from application code.

For graceful shutdown in Spring Boot, set `server.shutdown=graceful`. Kubernetes sends `SIGTERM` and waits `terminationGracePeriodSeconds` before killing the container.

### When to use / pitfalls
- A heap set to `-Xmx` larger than the container limit leads to the OOM killer stopping the process, not a Java error.
- Measure container memory with the orchestrator's metrics, not the JVM's view alone.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 4. How do you use Docker Compose for local development?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Docker Compose describes several containers, their networks, volumes, and environment in one YAML file, so a developer can start the application and its database, cache, and broker with one command. Use health checks and `depends_on` with a health condition so the app starts after its dependencies are ready.

### Explanation
```yaml
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/shop
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: shop
      POSTGRES_PASSWORD: local-only-password
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 10
volumes:
  pgdata:
```

Use a separate override file for environment-specific changes. Do not use development passwords like this in shared environments.

### When to use / pitfalls
- Compose is for development and tests, not a production orchestrator.
- Named volumes persist data between runs; `docker compose down -v` removes them.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 5. What are the parts of a Kubernetes cluster?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The control plane holds the desired state and makes decisions: the API server receives requests, etcd stores cluster state, the scheduler places pods on nodes, and the controller manager runs control loops that drive actual state to desired state. Each worker node runs the kubelet, which starts containers, kube-proxy (or an equivalent) for service networking, and a container runtime.

### Explanation
When you apply a Deployment, the API server stores it in etcd, the Deployment controller creates a ReplicaSet, the scheduler assigns each new pod to a node, and the kubelet on that node starts the containers. If a pod dies, the controller creates a replacement. Everything works through this loop of watching and reconciling.

### When to use / pitfalls
- Managed services (EKS, AKS, GKE) run the control plane for you, but you still own workloads, configuration, and upgrades of nodes.
- Use RBAC to give each service account only the permissions it needs.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 6. Which Kubernetes workload should you use for each job?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a Deployment for stateless services with rolling updates; it manages a ReplicaSet for you. Use a StatefulSet for workloads that need stable identities and storage per replica, such as a database cluster member. Use a DaemonSet for one pod per node, such as a log collector. Use a Job for a one-off task and a CronJob for a scheduled one.

### Explanation
A pod is the smallest deployable unit: one or more containers that share network and storage. You rarely create pods directly; the workload object creates and replaces them.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orders
  template:
    metadata:
      labels:
        app: orders
    spec:
      containers:
        - name: orders
          image: registry.example.com/orders:1.4.0
          ports:
            - containerPort: 8080
```

### When to use / pitfalls
- Pin image tags to a version or digest. `latest` makes rollbacks and audits unclear.
- Do not run a stateful database as a plain Deployment with shared volumes.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 7. How do Services, Ingress, and the Gateway API route traffic?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A Service gives a stable name and virtual IP to a set of pods selected by labels. Its types are ClusterIP (internal only), NodePort (a port on every node), LoadBalancer (a cloud load balancer), and ExternalName (a DNS alias). An Ingress routes external HTTP and HTTPS traffic to Services by host and path. The Gateway API is the newer, more expressive successor to Ingress for new work.

### Explanation
Pods come and go and get new IP addresses, so clients connect to the Service name, not to pod IPs. Kubernetes DNS resolves `orders.shop.svc.cluster.local` to the Service's virtual IP within the cluster.

### When to use / pitfalls
- Use ClusterIP for internal traffic and a single entry point (Ingress or Gateway) for external traffic.
- A LoadBalancer Service per microservice creates many cloud load balancers and costs money.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 8. What are liveness, readiness, and startup probes?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A liveness probe tells the kubelet whether to restart a container that is stuck. A readiness probe decides whether the pod receives traffic from Services; a failing readiness probe removes the pod from the endpoints without restarting it. A startup probe disables the other two until a slow application has started, so a long startup is not killed as unhealthy.

### Explanation
```yaml
containers:
  - name: orders
    image: registry.example.com/orders:1.4.0
    startupProbe:
      httpGet:
        path: /actuator/health/liveness
        port: 8080
      failureThreshold: 30
      periodSeconds: 5
    readinessProbe:
      httpGet:
        path: /actuator/health/readiness
        port: 8080
    livenessProbe:
      httpGet:
        path: /actuator/health/liveness
        port: 8080
```

Spring Boot exposes separate liveness and readiness groups when probes are enabled.

### When to use / pitfalls
- Do not make liveness depend on a downstream database. If the database is down, restarting every pod makes things worse.
- A readiness check that calls other services can cause a cascading outage; keep it cheap.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 9. How should configuration and secrets be handled in Kubernetes?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Put non-sensitive configuration in ConfigMaps and sensitive values in Secrets. A Secret's values are base64-encoded, not encrypted, by default. Enable encryption at rest for the API store, restrict access with RBAC, and ideally pull secrets from an external manager such as HashiCorp Vault or a cloud secrets service.

### Explanation
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orders-config
data:
  LOG_LEVEL: "INFO"
---
apiVersion: v1
kind: Secret
metadata:
  name: orders-secrets
type: Opaque
stringData:
  DB_PASSWORD: "set-by-pipeline-not-in-git"
```

Reference both with `envFrom` or `valueFrom` in the pod spec. Environment variables are visible to anyone who can read the pod spec, so restrict that access too.

### When to use / pitfalls
- Never commit a Secret manifest with real values to Git.
- Changing a ConfigMap does not restart pods that read it as environment variables; mounted files update, but the application must reload them.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 10. Why set resource requests and limits, and what does autoscaling use?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Requests are what the scheduler reserves for a pod when it places it on a node. Limits are the maximum a container may use; exceeding a memory limit gets the container killed, and exceeding a CPU limit throttles it. The Horizontal Pod Autoscaler adds or removes replicas based on observed metrics such as CPU or custom metrics.

### Explanation
Without requests, the scheduler packs pods too tightly and one busy pod can starve its neighbours. Set requests from measured usage, and set memory limits with care: a limit below the real working set causes repeated restarts.

### When to use / pitfalls
- A CPU limit can cause latency spikes through throttling, even when the node has spare capacity. Measure before setting one.
- Autoscaling a service whose bottleneck is the database just adds more load to the database.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 11. What does a typical CI/CD pipeline contain?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A pipeline runs automatically on each change: it builds the code, runs unit and integration tests, runs static and dependency security scans, builds and tags an artefact, deploys it to a test environment, runs smoke tests, and then deploys to production with an approval or automatic gate. Each stage stops the pipeline on failure, so a bad change never reaches production.

### Explanation
Typical stages, in order:

1. Build and unit tests (fast feedback first).
2. Static analysis and SAST; dependency scanning (SCA).
3. Package the artefact and push it to a registry.
4. Deploy to staging; run integration and smoke tests.
5. Deploy to production with the chosen strategy, then run health checks and watch metrics.

GitHub Actions, GitLab CI, and Jenkins all express these as pipelines; the concepts transfer between them.

### When to use / pitfalls
- Slow pipelines get bypassed. Cache dependencies and run tests in parallel.
- Build once and promote the same artefact through environments; rebuilding per environment means you test something different from what you ship.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 12. What are blue-green, canary, rolling, and shadow deployments?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Rolling replaces instances a few at a time, with no downtime. Blue-green runs two full environments and switches traffic from the old (blue) to the new (green), which makes rollback a traffic switch. Canary sends a small share of users to the new version and increases it if metrics stay healthy. Shadow sends a copy of production traffic to the new version without returning its responses to users, for comparison.

### Explanation
| Strategy | Risk exposure | Rollback | Cost |
|---|---|---|---|
| Rolling | Gradual, mixed versions during rollout | Roll back the update | Low |
| Blue-green | All users switch at once | Switch traffic back | Two environments |
| Canary | Small group first | Shift traffic back | Moderate, needs good metrics |
| Shadow | None for users | Not needed; nothing was served | Duplicate load |

### When to use / pitfalls
- Rolling and canary mean two versions run at the same time; database changes must be compatible with both.
- Shadow traffic can cause side effects, such as sending emails or charging cards twice. Disable external side effects in the shadow copy.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 13. What is infrastructure as code, and how do Terraform and Ansible differ?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Infrastructure as code describes infrastructure in versioned files so it can be reviewed, reproduced, and reverted. Terraform declares cloud resources and tracks them in a state file, and `plan` shows the changes before `apply` makes them. Ansible configures machines by running tasks over SSH, and is often used for software installation and configuration on servers.

### Explanation
Terraform works best with a remote state backend that supports locking, so two people cannot change the same stack at once. Keep state files out of Git because they can contain secrets. Use modules to reuse common patterns, such as a network or a database module.

### When to use / pitfalls
- Changes made by hand in the console drift from the code; the next `plan` shows the difference.
- Review the `plan` output in pull requests before applying in production.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 14. What is the difference between SAST, DAST, and SCA, and where do they run?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
SAST (static application security testing) analyses source code or bytecode without running it, and runs early in the pipeline. DAST (dynamic application security testing) attacks a running application from outside, and runs against a deployed test environment. SCA (software composition analysis) checks third-party dependencies against known vulnerability databases.

### Explanation
Each finds different things. SAST can flag a SQL string built by concatenation, but misses a misconfigured server. DAST finds runtime issues such as missing security headers, but needs a running app and can miss code paths it never reaches. SCA finds a vulnerable library version, but says nothing about your own code.

### When to use / pitfalls
- Tune the rules; a scanner that reports hundreds of false positives gets ignored.
- Fail the build on high-severity findings that have a fix, and track the rest.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---


**Next:** [Part 2](devops-cloud-and-ai-part-2.md)
