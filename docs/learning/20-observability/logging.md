# Logging

Logs are the narrative record of what your application did. An interviewer asks about logging to see whether you can write logs that help during an incident, not just logs that exist.

## Core concepts

### Facade and implementation: SLF4J and Logback

Your code should depend on **SLF4J** (Simple Logging Facade for Java), which is an abstraction. The implementation underneath is a separate choice. Spring Boot uses **Logback** by default. Keeping the facade in your code means you can change the backend without rewriting classes.

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    public void placeOrder(String orderId, int itemCount) {
        // Placeholders are only formatted if the level is enabled
        log.debug("Placing order {} with {} items", orderId, itemCount);
        log.info("Order {} accepted", orderId);
    }
}
```

Use `{}` placeholders rather than string concatenation. With concatenation, the message is built even when DEBUG is off.

### Log levels

| Level | Use it for |
|---|---|
| TRACE | Very fine-grained flow, usually off outside debugging |
| DEBUG | Developer detail, such as intermediate values |
| INFO | Normal business events: order accepted, job finished |
| WARN | Something unexpected that the system recovered from |
| ERROR | A failed operation that needs attention |

SLF4J has no FATAL level. Some frameworks define one, but in practice you log FATAL conditions as ERROR and then shut down.

Never log secrets (passwords, API keys, session tokens) or personal data. Log an identifier, not the record. If you must reference a token, log a masked form:

```java
public final class Masking {

    private Masking() {
    }

    // Show only the last four characters of a token
    public static String maskToken(String token) {
        if (token == null || token.length() <= 4) {
            return "****";
        }
        return "****" + token.substring(token.length() - 4);
    }
}
```

### Configuration: Logback, appenders, and layouts

Logback is configured with `logback-spring.xml` in Spring Boot. An **appender** decides where log events go (console, file, network). A **layout** or **encoder** decides the format. Asynchronous logging puts an `AsyncAppender` in front of slow appenders so request threads do not wait on I/O.

```xml
<configuration>
  <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>%d{ISO8601} %-5level [%thread] %logger{36} traceId=%X{traceId:-} - %msg%n</pattern>
    </encoder>
  </appender>

  <appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
    <appender-ref ref="CONSOLE"/>
    <queueSize>8192</queueSize>
  </appender>

  <root level="INFO">
    <appender-ref ref="ASYNC"/>
  </root>
</configuration>
```

Asynchronous appenders can drop events when the queue is full, depending on configuration. Know that trade-off before you rely on them for audit logs.

### Log4j2

**Log4j2** is an alternative backend. It is known for its asynchronous loggers, which use a lock-free ring buffer and can give high throughput. Its configuration and layout options are richer than Logback's. Use it when logging throughput is a measured bottleneck, and keep the SLF4J facade so the switch stays small.

### Structured logging, correlation IDs, and MDC

A **structured log** is a machine-readable record, usually one JSON object per line. Log platforms can then filter on `orderId` or `traceId` instead of running regular expressions over free text.

**MDC** (Mapped Diagnostic Context) is a per-thread map whose values appear in every log line written by that thread. Put a correlation ID in MDC at the edge of the request, so every line for that request carries it.

```java
import org.slf4j.MDC;

import java.util.UUID;

public class CorrelationContext {

    public static final String HEADER = "X-Correlation-Id";

    public void handle(String incomingId, Runnable work) {
        String correlationId = (incomingId != null) ? incomingId : UUID.randomUUID().toString();
        MDC.put("correlationId", correlationId);
        try {
            work.run();
        } finally {
            // Thread pools reuse threads. Without this, the next request inherits the value.
            MDC.clear();
        }
    }
}
```

Two rules follow from this. First, always clear MDC in a `finally` block. Second, MDC is thread-local, so it does not follow work handed to another thread unless you copy it. Executors and reactive pipelines need explicit propagation.

### Log sampling

For high-traffic services, logging every successful request costs money and hides the important lines. **Sampling** keeps a fraction of routine events while always keeping errors. A minimal counter-based sampler looks like this:

```java
import java.util.concurrent.atomic.AtomicLong;

public final class SampledLogger {

    private final AtomicLong counter = new AtomicLong();
    private final long everyN;

    public SampledLogger(long everyN) {
        if (everyN <= 0) {
            throw new IllegalArgumentException("everyN must be positive");
        }
        this.everyN = everyN;
    }

    public boolean shouldLog() {
        return counter.incrementAndGet() % everyN == 0;
    }
}
```

Apply sampling to routine INFO lines only. Never sample away ERROR logs or audit events.

### The ELK stack

The **ELK stack** is Elasticsearch (storage and full-text search), Logstash (ingestion and transformation), and Kibana (search UI and dashboards). In many setups a lightweight shipper such as Filebeat sits on each host and forwards logs. The stack gives you log ingestion, full-text search, dashboards, and alerts on log patterns. Retention and index size are the usual cost drivers.

## How it works

1. The application writes events through SLF4J to Logback (or another backend).
2. The encoder writes each event as a line of text or JSON.
3. A shipper reads the output and forwards it to the log platform.
4. The platform indexes fields, such as level, service name, and correlation ID.
5. Dashboards and alerts query those fields during incidents.

## Common pitfalls

- Logging personal data, tokens, or full request bodies
- String concatenation inside log calls, which builds messages even when the level is off
- Logging the same exception at every layer, which creates duplicate stack traces
- Leaving DEBUG on in production, which fills disks and hides real signals
- Forgetting to clear MDC, so one request's ID appears on another request's logs
- Using logs as metrics: counting log lines to get a rate is expensive and fragile

!!! tip "Interview tip"
    **Q: How would you trace one user's request through several services?**
    A: Generate a correlation ID at the edge, or accept one from an incoming header. Put it in MDC, so every log line includes it, and pass it to downstream calls as a header. Tracing systems carry the same idea further with a trace ID and span IDs (see [distributed tracing](distributed-tracing.md)).

## Quick recap

- Code against SLF4J; Logback is Spring Boot's default backend
- Use `{}` placeholders and pick the correct level
- Never log secrets or personal data; mask what you must reference
- Structured JSON plus MDC makes logs searchable by correlation ID
- Clear MDC in `finally`; propagate it across threads explicitly
- Sample routine logs, never errors or audit events

**See also:** [Metrics](metrics.md), [Distributed Tracing](distributed-tracing.md), [Alerting and Health Checks](alerting-health-checks.md)
