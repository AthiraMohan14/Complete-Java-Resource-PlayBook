# Config, Storage and Health

Applications on Kubernetes need three things from the platform: configuration injected from outside the image, storage that outlives pods, and accurate signals about whether each container is alive and ready. This page covers those mechanisms, plus the workload types for one-off and scheduled jobs and the resource limits that keep one workload from starving the others.

## Core concepts

### ConfigMaps
A **ConfigMap** holds non-sensitive configuration as key-value pairs or files. Pods consume it as environment variables or as mounted files. Changing the ConfigMap does not restart pods, so applications that read values only at startup need a rollout.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orders-config
data:
  GREETING: "Hello"
  application.yml: |
    server:
      shutdown: graceful
```

```java
public class GreetingFromEnv {
    public static void main(String[] args) {
        // Injected from the ConfigMap as an environment variable
        String greeting = System.getenv().getOrDefault("GREETING", "Hello");
        System.out.println(greeting + ", configuration loaded");
    }
}
```

### Secrets
A **Secret** holds sensitive values such as passwords, tokens, and certificates. By default, Secret data is only base64-encoded, not encrypted, so anyone who can read the object can decode it. Protect Secrets with:

- RBAC that limits who can read Secrets in each namespace.
- Encryption at rest for etcd, configured on the API server.
- An external secret store, such as a cloud key vault or HashiCorp Vault, synchronised into the cluster.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: orders-db
type: Opaque
stringData:
  DB_PASSWORD: "change-me"
```

`stringData` lets you write plain text; the API server stores it base64-encoded. Do not commit real Secret manifests to version control.

### PersistentVolumes, PersistentVolumeClaims, and StorageClasses
Storage is split into two roles:

- A **PersistentVolume (PV)** is a piece of storage in the cluster, provisioned by an administrator or dynamically.
- A **PersistentVolumeClaim (PVC)** is a pod's request for storage: size and access mode.

A **StorageClass** describes a kind of storage. When a PVC references a class, the cluster can create a matching PV on demand. This is **dynamic provisioning**.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: orders-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: standard
  resources:
    requests:
      storage: 5Gi
```

The access mode and the storage class name must match what the cluster offers. Available classes depend on the cluster or provider.

### Workloads for jobs and node agents
- **Jobs** run a task to completion, such as a data migration.
- **CronJobs** create Jobs on a schedule written in cron syntax.
- **DaemonSets** run one pod on every node, which suits log collectors and monitoring agents.
- **Init containers** run to completion before the app containers start, for steps such as waiting for a dependency or preparing files.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-cleanup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: cleanup
              image: orders-tools:1.0.0
              command: ["java", "-jar", "cleanup.jar"]
```

### Resource requests and limits
A **request** is what the scheduler reserves for a container. A **limit** is the most it may use. CPU above its limit is throttled. Memory above its limit gets the container OOM-killed.

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    memory: "512Mi"
```

A **ResourceQuota** caps total usage in a namespace, and a **LimitRange** sets default requests and limits for containers that do not declare them. Together they keep one team from consuming the whole cluster.

### Health probes
Kubernetes uses three probes, each answering a different question:

| Probe | Question | Failure result |
|---|---|---|
| Liveness | Is the container stuck or broken? | The container is restarted |
| Readiness | Can the pod take traffic now? | The pod is removed from Service endpoints |
| Startup | Has a slow app finished starting? | Other probes wait; no premature restarts |

```yaml
startupProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  failureThreshold: 30
  periodSeconds: 2
readinessProbe:
  httpGet: { path: /actuator/health/readiness, port: 8080 }
  periodSeconds: 5
livenessProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  periodSeconds: 10
```

The paths match Spring Boot Actuator's probe groups. Keep liveness checks simple. A liveness probe that calls a database can restart healthy pods during a database outage.

### Graceful shutdown
When a pod is deleted, Kubernetes sends SIGTERM to each container, waits up to `terminationGracePeriodSeconds` (30 seconds by default), then sends SIGKILL. Meanwhile the pod is removed from Service endpoints, but that removal propagates with a delay, so requests can still arrive.

To shut down cleanly:

- Run the app in exec form so it receives SIGTERM.
- Enable `server.shutdown=graceful` in Spring Boot so in-flight requests finish.
- Optionally add a `preStop` hook (for example, a short sleep) to let endpoint removal propagate before SIGTERM.
- Set `terminationGracePeriodSeconds` longer than the application's shutdown timeout.

A JVM shutdown hook runs when the JVM receives SIGTERM, which is useful for releasing resources:

```java
public class ShutdownDemo {
    public static void main(String[] args) throws InterruptedException {
        Runtime.getRuntime().addShutdownHook(new Thread(() ->
                System.out.println("Releasing resources before exit")));
        System.out.println("Running; send SIGTERM to stop");
        Thread.sleep(Long.MAX_VALUE);
    }
}
```

## Scaling
Kubernetes can change the size or the resource settings of a workload while it runs. Two autoscalers handle the two directions:

- The **Horizontal Pod Autoscaler (HPA)** changes the number of replicas.
- The **Vertical Pod Autoscaler (VPA)** changes the CPU and memory requests of each pod.

### Horizontal Pod Autoscaler
The HPA is part of core Kubernetes. It reads a metric, compares it with a target, and adjusts `replicas` on the target Deployment within a minimum and maximum. For CPU and memory targets, utilisation is measured against the container's **request**, so the pods must declare requests or the HPA has nothing to compare against.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orders-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orders
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

The HPA needs a metrics source, such as the metrics server, installed in the cluster. Custom metrics, such as requests per second, use the same `metrics` list with a different metric type.

### Vertical Pod Autoscaler
The VPA is not part of core Kubernetes. It is an add-on that you install separately. It watches actual usage and recommends requests for each container. With `updateMode: "Auto"` it applies those values by evicting and recreating pods. With `updateMode: "Off"` it only publishes recommendations, which is a safe way to learn the right numbers first.

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: orders-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orders
  updatePolicy:
    updateMode: "Off"
```

### When to use each
| Situation | Use |
|---|---|
| Load varies, and the app handles more replicas well | HPA |
| Requests are guessed wrongly, or pods are over-provisioned | VPA in `Off` mode to read recommendations |
| Stateful workloads where adding replicas is hard | VPA, with care about restarts |
| Replica count and size both need to adapt | HPA on one metric plus VPA on a different one, or VPA only |

Pitfalls for Java workloads:

- Do not point HPA and VPA at the same CPU or memory metric for one workload. They fight each other.
- A VPA `Auto` update restarts pods, so it can cause brief disruption unless replicas are spread out.
- A JVM sized from a small memory request may need heap settings that follow the container limit, such as `-XX:MaxRAMPercentage`, so that scaling the request also scales the heap.

## How it works / Step by step
1. The pod spec references ConfigMaps and Secrets, which are injected as environment variables or files at start.
2. The PVC asks for storage; the StorageClass provisions a PV, which is bound and mounted.
3. The startup probe gates the other probes until the app is up.
4. Readiness decides whether the pod receives traffic; liveness decides whether it gets restarted.
5. On deletion, the pod stops receiving new traffic, SIGTERM is sent, and the app drains until it exits or the grace period ends.

## Common pitfalls
- Storing credentials in a ConfigMap, or assuming base64 means encrypted.
- Expecting ConfigMap edits to reach running pods without a restart.
- Using a liveness probe that depends on external systems.
- Setting memory limits below what the JVM needs, causing OOM kills.
- Leaving out requests, which makes scheduling and autoscaling unpredictable.
- Setting a grace period shorter than the application's shutdown timeout.

!!! tip "Interview tip"
    **Q: What is the difference between liveness and readiness probes?**
    Liveness decides whether to restart a container; a failure restarts it. Readiness decides whether the pod gets traffic; a failure removes it from the Service without restarting it. Mixing them up causes restart loops during slow startups or dependency outages.

## Quick recap
- ConfigMaps hold plain configuration; Secrets hold sensitive data, which is only base64-encoded by default.
- PVCs request storage and StorageClasses provision it dynamically.
- Jobs, CronJobs, DaemonSets, and init containers cover one-off, scheduled, per-node, and setup work.
- Requests drive scheduling; limits cap usage; quotas cap namespaces.
- Use startup, readiness, and liveness probes, and shut down gracefully within the grace period.

**See also:** [Kubernetes Architecture and Objects](kubernetes-architecture-objects.md), [Spring Boot in Containers](../15-docker/spring-boot-in-containers.md), [Networking, Helm and Operators](networking-helm-operators.md)
