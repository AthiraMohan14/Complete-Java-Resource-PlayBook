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

## Quick recap

- Containers share the host kernel; use multi-stage builds, non-root users, and no secrets in images.
- Inside containers, size the JVM heap with percentages and shut down gracefully.
- In Kubernetes, use Deployments for stateless services, separate liveness from readiness, and treat Secrets as sensitive.
- Deploy with rolling, blue-green, canary, or shadow strategies, and make database changes compatible with both versions.
- Observe with logs, metrics, and traces; alert on user-facing symptoms.
- RAG needs good chunking, filtered retrieval, and validation of model output.

**See also:** [Spring and security](spring-and-security-part-1.md), [Architecture and distributed systems](architecture-and-distributed.md), [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)
