# Alerting and Health Checks

Alerts tell a person that something needs action. Health checks tell an orchestrator whether an instance should receive traffic or be restarted. Interviewers ask about these to see whether you can separate noise from signal and whether you understand what liveness and readiness mean.

## Core concepts

### SLI, SLO, error budget, and SLA
These four terms describe how reliability is measured and promised:

- **SLI (service level indicator)**: a measured signal, usually a ratio of good events to valid events. Example: the share of HTTP requests that return a non-5xx response in under 300 ms.
- **SLO (service level objective)**: the target for an SLI over a time window. Example: 99.9% of requests are good over 30 days.
- **Error budget**: the allowed amount of failure, which is 100% minus the SLO. It is the room the team has to take risks, such as deploying or running experiments, before users are affected too often.
- **SLA (service level agreement)**: a contract with customers that includes consequences, such as credits, if the promise is missed. An SLA is usually looser than the internal SLO, so the team sees trouble before the contract is breached.

Worked example for an order API with a 99.9% SLO over 30 days:

```text
Valid requests in the window:  10,000,000
Good requests (non-5xx, <300 ms): 9,995,000
SLI = 9,995,000 / 10,000,000 = 99.95%          -> meets the 99.9% SLO

Error budget = 100% - 99.9% = 0.1% of 10,000,000 = 10,000 allowed bad requests
Bad requests so far = 10,000,000 - 9,995,000  = 5,000
Budget consumed = 5,000 / 10,000 = 50%
```

Half the budget is already spent, so the team might slow risky releases until the window recovers. The budget turns a reliability target into a decision rule: release freely while budget remains, and focus on reliability work when it runs out.

### Alert on symptoms, not causes

Alert on what users feel: high latency, failed requests, a missing feature. Causes such as high CPU are useful on dashboards, but an alert on CPU wakes someone up even when users are fine. A symptom alert usually ties to an SLO (service level objective), such as "99.9% of requests succeed over 30 days". Alerting on how fast the error budget is burning is a common approach, because it fires quickly for a severe incident and slowly for a minor one.

### Thresholds and conditions

An alert condition has three parts:

1. **Expression:** what is measured, such as the error ratio over five minutes
2. **Threshold:** the value that counts as bad
3. **Duration:** how long the condition must hold before firing

The duration matters. Without it, a single spike pages someone. Here is a Prometheus-style rule as an example of the shape. It fires when the five-minute error ratio stays above 5% for ten minutes:

```text
alert: HighErrorRate
expr: |
  sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m]))
    /
  sum(rate(http_server_requests_seconds_count[5m])) > 0.05
for: 10m
labels:
  severity: page
annotations:
  summary: "Error ratio above 5% for 10 minutes"
```

The 5% threshold is an example. Choose thresholds from your SLO and from past incidents, not from a number you read somewhere.

### Routing, escalation, and on-call

An alert needs a route: which team, which channel, and what happens if nobody acknowledges it. An **on-call rotation** is a schedule of people who respond to pages. **Escalation** moves an unacknowledged page to a second responder after a set time.

Alerting platforms such as **PagerDuty** and **Opsgenie** handle schedules, acknowledgement, escalation, and notification channels. Prometheus sends alerts to **Alertmanager**, which groups, silences, and routes them to receivers like these.

### Reducing alert fatigue

Alert fatigue happens when people receive so many pages that they ignore them. Remedies:

- Delete alerts nobody acts on. Every page should lead to an action.
- Group related alerts. One outage should produce one page, not fifty.
- Use the `for` duration so transient spikes do not page.
- Separate **pages** (act now, day or night) from **tickets** (act during working hours).
- Review alerts after each incident and tune them.

### Health checks with Spring Boot Actuator

Spring Boot Actuator exposes health information at `/actuator/health`. It aggregates **health indicators**, one per component (database, disk space, message broker). You can add your own indicator:

```java
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {

    private final Gateway gateway;

    public PaymentGatewayHealthIndicator(Gateway gateway) {
        this.gateway = gateway;
    }

    @Override
    public Health health() {
        try {
            return gateway.ping()
                    ? Health.up().build()
                    : Health.down().withDetail("reason", "ping returned false").build();
        } catch (RuntimeException e) {
            return Health.down(e).build();
        }
    }

    // A small abstraction over the external provider, so the indicator can be tested
    public interface Gateway {
        boolean ping();
    }
}
```

Keep the check cheap. A health endpoint that calls three external systems on every probe can itself cause an outage.

### Liveness and readiness probes

Orchestrators such as Kubernetes use two different probes:

| Probe | Question it answers | If it fails |
|---|---|---|
| Liveness | Is the process stuck or broken beyond recovery? | The instance is restarted |
| Readiness | Can this instance serve traffic right now? | The instance is removed from load balancing, but not restarted |

Spring Boot exposes these as separate health groups. Enable them with `management.endpoint.health.probes.enabled=true`, and they appear at `/actuator/health/liveness` and `/actuator/health/readiness`.

Liveness should not depend on external systems. If the database is down, restarting the app does not fix it, and a restart loop makes things worse. Readiness can check dependencies, so traffic stops reaching an instance that cannot serve it.

Tune the probe timing. Set an initial delay long enough for startup, a timeout shorter than the period, and a failure threshold that tolerates a brief hiccup.

## How it works

1. Metrics or logs show an unusual condition, such as rising 5xx responses.
2. An alert rule evaluates the condition every interval and waits for the `for` duration.
3. The alert fires and goes to Alertmanager or a similar router.
4. The router groups the alert, applies silences, and pages the on-call person.
5. If unacknowledged, the page escalates to the next responder.
6. Orchestrator probes run separately: liveness restarts broken processes, and readiness controls traffic.

## Common pitfalls

- Alerting on causes (CPU, memory) instead of symptoms users feel
- No `for` duration, so a single data point pages someone
- Health checks that are slow, call many services, or are exposed without protection
- Using a dependency check in liveness, which causes restart loops during an external outage
- Paging for things that do not need action right now
- Never reviewing alerts, so noise accumulates

!!! tip "Interview tip"
    **Q: What is the difference between liveness and readiness?**
    A: Liveness answers "should this process be restarted?" Readiness answers "should this instance receive traffic?" A process can be alive but not ready while it warms caches or waits for a database. Keep dependency checks in readiness, and keep liveness limited to internal health, so an external outage does not cause a restart storm.

## Quick recap

- Alert on symptoms tied to SLOs, not on raw causes
- Every alert needs a threshold, a duration, a route, and an action
- Reduce fatigue by grouping, tuning, and separating pages from tickets
- Actuator aggregates health indicators; add custom ones for key dependencies
- Liveness restarts broken processes; readiness controls traffic

**See also:** [Logging](logging.md), [Metrics](metrics.md), [Distributed Tracing](distributed-tracing.md)
