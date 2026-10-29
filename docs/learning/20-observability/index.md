# Observability and Monitoring

Observability means you can answer "what is my system doing right now, and why?" from the data it emits. This section covers logs, metrics, traces, alerts, and health checks for Java services.

---

## Topics

### [Logging](logging.md)
**SLF4J - Logback - structured logs - MDC - sampling**
Write useful log lines, structure them as JSON, attach correlation IDs, and keep secrets out of the logs.

### [Metrics](metrics.md)
**Micrometer - Prometheus - Grafana - percentiles - JVM metrics**
Measure throughput, latency, errors, and JVM health, and choose metric names and tags that stay affordable at scale.

### [Distributed Tracing](distributed-tracing.md)
**Micrometer Tracing - OpenTelemetry - Zipkin - trace propagation - sampling**
Follow one request across several services and find where the time goes.

### [Alerting and Health Checks](alerting-health-checks.md)
**Actuator - liveness - readiness - alert fatigue - on-call**
Decide what should wake someone up, expose health endpoints for orchestrators, and route alerts to the right people.

**See also:** [Part 4 roadmap, section 20](../../resources/full-stack-java-roadmap/part-4-design-interview-projects.md)
