# Metrics

Metrics are numbers sampled over time: request rate, error rate, latency percentiles, heap usage. An interviewer asks about metrics to check that you know which numbers matter, how to record them cheaply, and why averages mislead.

## Core concepts

### Micrometer: the facade for metrics

**Micrometer** is the metrics facade used by Spring Boot Actuator. You record metrics through Micrometer's `MeterRegistry`, and a registry implementation (Prometheus, Datadog, and others) exports them. This is the same idea as SLF4J for logs: your code does not change when the backend does.

```java
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

public class CheckoutMetrics {

    private final Counter ordersPlaced;
    private final Timer checkoutTimer;

    public CheckoutMetrics(MeterRegistry registry) {
        this.ordersPlaced = Counter.builder("orders.placed")
                .description("Orders successfully placed")
                .register(registry);

        this.checkoutTimer = Timer.builder("checkout.duration")
                .description("Time to complete checkout")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(registry);
    }

    public void checkout(Runnable work) {
        checkoutTimer.record(work);
        ordersPlaced.increment();
    }
}
```

Build meters once, in the constructor, and reuse them. Creating meters inside a hot request path is slow and easy to get wrong.

### Prometheus: storage, scraping, and alert rules

**Prometheus** is a time-series database. It pulls (scrapes) metrics from an HTTP endpoint on a schedule. In a Spring Boot app, add the Prometheus registry and expose the endpoint through Actuator. Micrometer names such as `orders.placed` are converted to Prometheus-style names, with dots replaced by underscores. Counters get a `_total` suffix.

Prometheus also evaluates **alerting rules** over the stored series. The rule language is PromQL, and the rule itself is covered in [alerting](alerting-health-checks.md).

### Grafana: dashboards

**Grafana** reads from Prometheus (and many other sources) to draw dashboards. A good service dashboard has the same panels for every service: traffic, errors, latency, saturation (CPU, memory, pool usage), and business signals. Consistency lets an on-call engineer read a new service's dashboard in seconds.

### The key metrics

- **Throughput:** requests per second, per route and per status class
- **Latency:** p50, p95, and p99 of request duration. The median shows typical behaviour; p99 shows what your unluckiest users feel.
- **Errors:** error rate as errors divided by total requests, and success rate as its complement
- **Apdex:** a satisfaction score. With a target threshold T, a response is satisfied if it takes at most T, tolerating if it takes up to 4T, and frustrated otherwise. Apdex = (satisfied + tolerating / 2) / total.
- **JVM:** heap usage, GC pause time, live thread count. Spring Boot binds these automatically (names such as `jvm.memory.used`, `jvm.gc.pause`, `jvm.threads.live`).
- **Business:** active users, conversions, revenue. These show whether the system is doing its job, not just running.

### RED and USE: two checklists
Two short methods help you decide which metrics to build dashboards and alerts on.

- **RED** (Rate, Errors, Duration) suits request-driven services. For each endpoint or service, chart the request rate, the share of failed requests, and the latency distribution.
- **USE** (Utilization, Saturation, Errors) suits resources such as CPU, memory, disks, network links, and connection pools. Utilization shows how busy the resource is. Saturation shows queued work that cannot be served yet, such as threads waiting for a connection. Errors count failed operations on the resource.

For a Java service, RED covers the HTTP layer and USE covers the JVM heap, GC, thread pool, and database connection pool. On Kubernetes, add object-level signals too: pod restart counts, pods not ready, and desired versus available replicas for each Deployment. Kubernetes exposes these through kube-state-metrics and the metrics API, so they are not Micrometer metrics.

### Percentiles: why averages mislead

An average hides the tail. If 99 requests take 10 ms and one takes 5 seconds, the mean looks fine. A percentile exposes the tail. Two practical points:

1. You cannot average percentiles from several instances. Averaging p99 values is wrong. Publish **histogram buckets** and let the query engine compute quantiles across instances.
2. Client-side percentiles (computed inside the app) are cheap but cannot be aggregated. Server-side histograms (buckets) can be aggregated, which is usually what you want with several replicas.

A PromQL query for p99 latency across all instances, using histogram buckets:

```text
histogram_quantile(0.99, sum by (le) (rate(http_server_requests_seconds_bucket[5m])))
```

Spring Boot can publish histogram buckets for HTTP timings. Set `management.metrics.distribution.percentiles-histogram.http.server.requests=true` to enable them.

### Tags and cardinality

Each unique combination of metric name and tag values creates a separate time series. This is **cardinality**. Tagging by route template (`/orders/{id}`) is fine. Tagging by raw URL, user ID, or order ID creates millions of series, which slows and costs the monitoring system.

```java
import io.micrometer.core.instrument.MeterRegistry;

public class PaymentMetrics {

    private final MeterRegistry registry;

    public PaymentMetrics(MeterRegistry registry) {
        this.registry = registry;
    }

    public void recordFailure(String provider, String reasonCode) {
        // Bounded values only: a fixed provider name and a small set of reason codes.
        registry.counter("payments.failed", "provider", provider, "reason", reasonCode).increment();
    }
}
```

Keep tag values to a small, known set. Put high-cardinality detail in logs or traces instead.

## How it works

1. Code records values into meters (counters, timers, gauges, histograms) through `MeterRegistry`.
2. Actuator exposes them on an endpoint, such as `/actuator/prometheus`.
3. Prometheus scrapes that endpoint on a fixed interval and stores the samples.
4. Rules compute rates and quantiles, and alert when thresholds are crossed.
5. Grafana plots the results for people to read.

## Common pitfalls

- Averaging latency instead of looking at percentiles
- Unbounded tag values (user IDs, raw paths), which explode cardinality
- Reporting only the mean for latency
- Mixing up a counter (only goes up) with a gauge (goes up and down)
- Measuring only server-side time and ignoring queueing in a client or load balancer
- Treating metrics as an audit log; metrics are aggregated and lose individual events

!!! tip "Interview tip"
    **Q: Why do we look at p99 latency and not the average?**
    A: The average hides outliers, and a few very slow requests can ruin the experience of a noticeable fraction of users while the mean barely moves. Percentiles show the distribution. Histograms let you compute percentiles across many instances, which you cannot do by averaging per-instance percentiles.

## Quick recap

- Record through Micrometer; export through a registry such as Prometheus
- Track throughput, latency percentiles, errors, saturation, and business signals
- Publish histograms when you need percentiles across several instances
- Keep tags bounded to protect cardinality
- Alert on symptoms (see [alerting](alerting-health-checks.md))

**See also:** [Logging](logging.md), [Distributed Tracing](distributed-tracing.md), [Alerting and Health Checks](alerting-health-checks.md)
