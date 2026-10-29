# DevOps, Cloud, Observability, and AI Questions (Part 2 of 2)

Continued from [Part 1](devops-cloud-and-ai-part-1.md).

---

## 15. How do the major cloud providers map to the core building blocks?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Each provider offers the same categories under different names: virtual machines, containers and managed Kubernetes, serverless functions, object storage, managed relational and NoSQL databases, virtual networks and load balancers, identity and access management, and monitoring. Learn the categories and map product names when you need them.

### Explanation
| Category | AWS | Microsoft Azure | Google Cloud |
|---|---|---|---|
| Virtual machines | EC2 | Virtual Machines | Compute Engine |
| Managed Kubernetes | EKS | AKS | GKE |
| Serverless functions | Lambda | Azure Functions | Cloud Functions |
| Object storage | S3 | Blob Storage | Cloud Storage |
| Managed relational DB | RDS, Aurora | Azure SQL Database | Cloud SQL |
| Identity | IAM | Microsoft Entra ID, managed identities | Cloud Identity, service accounts |
| Monitoring | CloudWatch | Azure Monitor, Application Insights | Cloud Monitoring, Cloud Logging |

Identity is the most important category to get right. Use roles or managed identities for services rather than long-lived keys stored in code.

### When to use / pitfalls
- Cost surprises come from data transfer, idle resources, and over-sized databases. Tag resources and review costs regularly.
- Using many proprietary services increases lock-in. Keep a clear reason for each one.

**See also:** [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 16. What are the three pillars of observability, and how do the tools fit together?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The three pillars are logs (records of discrete events), metrics (numbers over time), and traces (the path of one request across services). Micrometer is the metrics facade used by Spring Boot, Prometheus scrapes and stores metrics, Grafana visualises them, and OpenTelemetry is the vendor-neutral standard for all three signals. Micrometer Tracing is the Spring Boot 3 successor to Spring Cloud Sleuth.

### Explanation
A useful signal set for a service: request rate, error rate, and latency at p50, p95, and p99 (the RED method), plus JVM heap use, GC pause time, and thread count. For infrastructure, track utilisation, saturation, and errors (the USE method). Logs should carry a correlation or trace ID so you can jump from an error log to the trace.

```java
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;

class OrderMetrics {
    private final Counter placed;

    OrderMetrics(MeterRegistry registry) {
        this.placed = Counter.builder("orders.placed")
                .description("Orders accepted by the service")
                .register(registry);
    }

    void onOrderPlaced() {
        placed.increment();
    }
}
```

### When to use / pitfalls
- Do not use unbounded values such as user IDs as metric tags; they create too many time series.
- Averages hide slow requests. Use percentiles.
- Never log passwords, tokens, or personal data.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 17. How should you design alerts?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Alert on symptoms that users feel, such as a high error rate or slow p99 latency, and use other signals for diagnosis. Every alert should be actionable and have a clear owner. Alerts that fire often and need no action cause alert fatigue, and people stop responding to them.

### Explanation
Prometheus evaluates alerting rules and sends firing alerts to Alertmanager, which groups, deduplicates, and routes them to a receiver such as a paging service. Use thresholds over a time window, not single samples, so brief spikes do not page anyone. Tie alerts to SLOs when you can: alert when the error budget burns too fast.

### When to use / pitfalls
- A cause-based alert (for example "CPU above 80%") is often noise. Keep it as a dashboard panel unless it predicts user impact.
- Review alerts after each incident and remove the ones that did not help.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 18. What health check should a Spring Boot service expose?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Spring Boot Actuator exposes `/actuator/health` and can add custom health indicators. A health indicator should be cheap and reflect whether this instance can serve traffic. Keep dependency checks for readiness, and keep liveness limited to the process itself.

### Explanation
```java
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component
class PaymentProviderHealth implements HealthIndicator {

    @Override
    public Health health() {
        boolean reachable = true;   // replace with a cheap, time-limited check
        return reachable
                ? Health.up().build()
                : Health.down().withDetail("reason", "provider unreachable").build();
    }
}
```

Expose only the Actuator endpoints you need, and secure the rest. Endpoints such as `/env` and `/heapdump` can leak secrets or memory contents.

### When to use / pitfalls
- A slow health check makes the probe time out and restarts healthy pods.
- Show details only to authorised users; anonymous callers should get a simple status.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 19. What are the basic LLM concepts an interviewer expects you to know?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A large language model predicts the next token given the previous tokens. Its context window limits how much text it can consider in one request, including your prompt and its answer. Temperature and top-p control how random the sampling is. Streaming returns tokens as they are generated, and function (tool) calling lets the model request a structured call to your code.

### Explanation
- **Tokens:** pieces of words. Cost and context limits are measured in tokens, not characters.
- **Temperature:** lower values give more predictable output; higher values give more variety.
- **Top-p (nucleus sampling):** the model samples from the smallest set of tokens whose probabilities add up to p.
- **Structured output:** ask for JSON that matches a schema, and validate it in code before you use it.
- **Tool calling:** you describe functions; the model returns a request to call one with arguments; your code runs it and returns the result.

### When to use / pitfalls
- LLMs can produce confident but wrong answers (hallucinations). Ground important answers in retrieved sources and verify them.
- Treat model output as untrusted input. Validate it before it touches a database, a shell, or a payment.
- Retrieved text and user input can contain prompt injection. Do not let content from documents override system instructions or grant permissions.
- Control cost with token limits, caching of repeated prompts, and smaller models for simple steps.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 20. How does retrieval-augmented generation (RAG) work?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
RAG answers a question with a model using your own documents. At indexing time, you split documents into chunks, convert each chunk to an embedding vector, and store the vectors. At query time, you embed the question, retrieve the most similar chunks, add them to the prompt as context, and ask the model to answer from that context.

### Explanation
Chunking matters: chunks that are too small lose context, and chunks that are too large dilute the match. Overlap between chunks keeps sentences that cross a boundary. The code below creates overlapping chunks:

```java
import java.util.ArrayList;
import java.util.List;

class Chunker {
    static List<String> chunk(String text, int size, int overlap) {
        if (overlap >= size) {
            throw new IllegalArgumentException("overlap must be smaller than size");
        }
        List<String> chunks = new ArrayList<>();
        for (int start = 0; start < text.length(); start += size - overlap) {
            chunks.add(text.substring(start, Math.min(text.length(), start + size)));
            if (start + size >= text.length()) {
                break;
            }
        }
        return chunks;
    }

    public static void main(String[] args) {
        System.out.println(chunk("abcdefghij", 4, 1));   // [abcd, defg, ghij]
    }
}
```

Improvements often used in practice: hybrid search (combine keyword BM25 with vector search), re-ranking the top results with a stronger model, and metadata filters such as document date or access group.

### When to use / pitfalls
- Filter retrieved documents by the user's permissions before they reach the prompt. Otherwise the model can reveal content the user should not see.
- Evaluate retrieval separately from generation: check whether the right chunk was retrieved before blaming the model.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 21. How do embeddings and vector databases find similar content?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An embedding is a list of numbers that represents the meaning of a piece of text, so similar texts have vectors that point in similar directions. Cosine similarity measures the angle between two vectors. A vector database stores embeddings and uses an approximate nearest-neighbour index, such as HNSW, to find close vectors quickly without comparing against every stored vector.

### Explanation
```java
class Similarity {
    static double cosine(double[] a, double[] b) {
        double dot = 0, normA = 0, normB = 0;
        for (int i = 0; i < a.length; i++) {
            dot += a[i] * b[i];
            normA += a[i] * a[i];
            normB += b[i] * b[i];
        }
        return dot / (Math.sqrt(normA) * Math.sqrt(normB));
    }

    public static void main(String[] args) {
        System.out.println(cosine(new double[]{1, 0}, new double[]{1, 0}));   // 1.0: same direction
        System.out.println(cosine(new double[]{1, 0}, new double[]{0, 1}));   // 0.0: unrelated
    }
}
```

Options include pgvector (inside PostgreSQL), Pinecone, Weaviate, Milvus, Chroma, and Qdrant. Approximate indexes trade a little recall for much faster search; HNSW and IVF are two common index types.

### When to use / pitfalls
- Embeddings from different models are not comparable. Re-embed everything if you change the model.
- Approximate search can miss the exact nearest neighbour. Measure recall on a test set.
- If your data is already in PostgreSQL and the volume is moderate, pgvector keeps the stack simple.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 22. What is the difference between a Docker image and a container?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An image is a read-only template: layers of files plus metadata such as the start command and exposed port. A container is a running instance started from an image, with a thin writable layer added on top. One image can start many containers, and running a container does not change the image.

### Explanation
Think of the image as a class and the container as an object. Build once, then start as many containers as the load requires:

```bash
docker build -t orders:1.4.1 .            # produces an immutable image
docker run -d --name orders-a orders:1.4.1
docker run -d --name orders-b orders:1.4.1   # second, independent container from the same image
docker rm -f orders-a                     # its writable layer is discarded with it
```

Anything written inside a container disappears when the container is removed. Data that must survive belongs in a volume, and a changed configuration should produce a new image tag rather than an edited running container.

### When to use / pitfalls
- Do not treat a running container as the source of truth. Rebuild the image and redeploy instead of editing files inside a container.
- Tag images with a version rather than `latest`, so you can tell which build is running.

**See also:** [Docker fundamentals](../../learning/15-docker/docker-fundamentals.md)

</details>

---

## 23. What is the difference between a Pod and a Deployment?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A Pod is the smallest unit Kubernetes schedules: one or more containers that share a network namespace and can share volumes. A Deployment manages a ReplicaSet, which keeps a fixed number of identical Pods running, and it performs rolling updates and rollbacks. A bare Pod is not recreated if it is deleted or its node fails.

### Explanation
You rarely create Pods directly. You describe the desired state in a Deployment, and the controllers do the rest:

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
          image: registry.example.com/orders:1.4.1
          ports:
            - containerPort: 8080
```

The hierarchy is Deployment, then ReplicaSet, then Pods. If a Pod crashes, the kubelet restarts its container according to the Pod's `restartPolicy`, but only the controller can replace a Pod that is gone. A standalone Pod is useful for a one-off debugging session. A StatefulSet fits workloads that need stable names and storage, such as a database.

### When to use / pitfalls
- A standalone Pod stays on a failed node and is never recreated. Use a Deployment for stateless services.
- A Deployment with `replicas: 1` is not highly available. Scale to at least two replicas and spread them across nodes.

**See also:** [Kubernetes architecture and objects](../../learning/16-kubernetes/kubernetes-architecture-objects.md)

</details>

---

## 24. How does GitOps work, and how does Argo CD implement it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
GitOps keeps the desired state of a cluster in a Git repository. Argo CD runs inside the cluster, compares the manifests in Git with the live objects, and reports any drift. It syncs the cluster to Git, either on demand or automatically, and with automated sync it can prune resources that were removed from Git and revert manual edits.

### Explanation
An Argo CD Application maps one Git path to one destination namespace:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: orders
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://git.example.com/platform/orders-config.git
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: orders
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

A change reaches production by commit. CI builds the image, then a commit updates the image tag in the staging overlay. After review, the same tag is promoted to production by another commit. The benefits are an audit trail in Git, review before change, and a rollback that is a `git revert`. Because the cluster pulls its state, CI does not need cluster credentials.

### When to use / pitfalls
- Secrets must not be stored in plain text in Git. Use encrypted secrets or reference a vault.
- Automated self-heal reverts manual hot fixes. Make the fix in Git first, or the controller removes it.

**See also:** [Continuous deployment and IaC](../../learning/17-cicd/continuous-deployment-iac.md)

</details>

---

## 25. How do you monitor an application running on Kubernetes?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Collect three kinds of signal. Metrics come from Micrometer endpoints and Kubernetes object state, scraped by Prometheus and shown in Grafana. Logs go to stdout as structured JSON, and a node-level agent ships them to a store such as OpenSearch or Loki. Traces come from OpenTelemetry-instrumented services and go to Jaeger or Tempo. Alert on user-facing symptoms and on platform failures such as restart loops.

### Explanation
Watch two layers. The platform layer covers pod restarts, pods that are not ready, replicas that differ from the desired count, and node memory or disk pressure. The application layer covers the RED signals (request rate, errors, latency) and JVM heap, GC, and connection pool use. Probes give the platform the health signals it needs:

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  periodSeconds: 5
```

Use the same correlation or trace ID in every log line so that a log search leads to the matching trace.

### When to use / pitfalls
- Alerting on CPU alone misses user-facing failures. Alert on error rate and latency against the SLO.
- Metric labels with unbounded values, such as request IDs, create too many time series.
- Logs written to files inside the container are lost when the pod is replaced.

**See also:** [Metrics](../../learning/20-observability/metrics.md), [Distributed tracing](../../learning/20-observability/distributed-tracing.md)

</details>

---

## Quick recap

- Containers share the host kernel; use multi-stage builds, non-root users, and no secrets in images.
- Inside containers, size the JVM heap with percentages and shut down gracefully.
- In Kubernetes, use Deployments for stateless services, separate liveness from readiness, and treat Secrets as sensitive.
- Deploy with rolling, blue-green, canary, or shadow strategies, and make database changes compatible with both versions.
- Observe with logs, metrics, and traces; alert on user-facing symptoms.
- Images are immutable templates; containers and Pods are running instances. Deployments keep Pods running and roll them out.
- GitOps tools such as Argo CD sync the cluster to a Git repository, so changes go through commits.
- RAG needs good chunking, filtered retrieval, and validation of model output.

**See also:** [Spring and security](spring-and-security-part-1.md), [Architecture and distributed systems](architecture-and-distributed.md), [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)
