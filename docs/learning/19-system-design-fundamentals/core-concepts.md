# Core Concepts

System design discussions reuse a small set of ideas: how a system grows (scalability), how it keeps working during failures (availability), what data it promises to return (consistency), and how fast it responds (performance). Interviewers ask about these to see whether you can name a trade-off precisely, and whether you know that the CAP theorem describes behaviour during a network partition, not a permanent choice.

## Core concepts

### Scalability: vertical and horizontal
- **Vertical scaling** (scaling up) gives one machine more CPU, memory, or disk. It is simple, requires no code changes, and has a ceiling set by the largest machine you can buy or rent. It also leaves a single point of failure.
- **Horizontal scaling** (scaling out) adds more machines and spreads the work across them. It removes the ceiling and improves fault tolerance, but requires the system to handle distribution: load balancing, shared state, and partial failures.

Stateless services scale horizontally by adding instances behind a load balancer. Stateful components, such as databases, need partitioning or replication to scale the same way.

### Availability arithmetic
Availability composes in two directions, and interviewers expect you to reason about both.

- **In series** (every component must work): the overall availability is the product of the parts. Two independent components at 99% each give 0.99 × 0.99 = 98.01%, which is lower than either part.
- **In parallel** (any one replica is enough): the probability that all replicas fail is the product of their failure probabilities. Two independent replicas at 99% each fail together with probability 0.01 × 0.01 = 0.0001, which gives 99.99% availability.

The arithmetic assumes independent failures, which is rarely fully true. Correlated causes such as a shared network, a shared deployment, or a shared dependency reduce the real benefit of redundancy. This is why a dependency on one external provider can cap the availability of the whole system even when everything else is redundant.

### Availability: redundancy, failover, and replication
**Availability** is the share of time a system can serve requests. It improves through:

- **Redundancy**: no single component whose failure stops the service.
- **Failover**: automatically switching to a standby when the primary fails.
- **Replication**: keeping copies of data on more than one node.

Redundancy only helps if failures are independent. Two replicas in the same rack or availability zone can fail together.

### SLA, SLO, and SLI
These three terms describe reliability in layers:

| Term | Meaning | Example form |
|---|---|---|
| **SLI** (indicator) | A measured quantity | Share of requests that succeed |
| **SLO** (objective) | A target for the indicator | Successful requests stay above a set level over a rolling window |
| **SLA** (agreement) | A contract with consequences | Credits or penalties if the target is missed |

Engineers set SLOs tighter than the SLA, so they have warning before a contract is breached. An **error budget** is the allowed failure within an SLO; when it runs out, the team slows feature work to improve reliability.

### Consistency models
Consistency describes what a read sees after a write.

- **Strong consistency**: every read returns the latest write. Simple to reason about, but needs coordination that adds latency and reduces availability during partitions.
- **Eventual consistency**: replicas converge over time. Reads can be stale for a while, which suits counters, feeds, and caches.
- **Causal consistency**: operations that are causally related are seen in order by everyone; unrelated operations may be seen in different orders.

Pick the weakest model that the business rule tolerates. A bank balance usually needs stronger guarantees than a view count.

### Consensus: Raft and Paxos
**Consensus** lets a group of nodes agree on a value, such as which node is the leader or what the next log entry is, even when some nodes fail. **Paxos** is the original algorithm and is known for being hard to understand. **Raft** was designed for understandability: it elects a leader, replicates a log through that leader, and commits entries once a majority acknowledges them. Systems such as etcd use Raft-based consensus. At an interview level, explain the majority-quorum idea and why an odd number of nodes is common.

### CAP theorem
The CAP theorem says that during a **network partition**, a distributed system must choose between **consistency** (every node gives the same, latest answer) and **availability** (every non-failing node answers). Partition tolerance is required in any real distributed system, because networks do fail.

- A CP system refuses or delays some requests during a partition to stay consistent.
- An AP system keeps answering during a partition and reconciles later.

The theorem says nothing about behaviour when there is no partition. **PACELC** extends it: if there is a partition, choose availability or consistency; else, choose latency or consistency. This is a more useful framing for everyday trade-offs.

### Performance: latency, throughput, and bandwidth
- **Latency** is the time for one request to complete. Users feel latency, and tail latency (high percentiles) often matters more than the average.
- **Throughput** is the number of requests or operations completed per unit of time.
- **Bandwidth** is the capacity of the network path. A system can have high bandwidth and still high latency, and the two are optimised differently.

Common optimisations include caching, reducing round trips, batching, compression, and moving data closer to users. Measure before optimising, and report percentiles rather than averages.

```java
import java.util.Arrays;

public class LatencyPercentiles {
    public static void main(String[] args) {
        // Response times in milliseconds for a small sample
        long[] samples = {12, 15, 14, 220, 13, 16, 18, 15, 14, 300};
        long[] sorted = samples.clone();
        Arrays.sort(sorted);
        double mean = Arrays.stream(samples).average().orElse(0);
        int p90Index = (int) Math.ceil(0.9 * sorted.length) - 1;
        System.out.printf("mean=%.1f ms, p90=%d ms, max=%d ms%n",
                mean, sorted[p90Index], sorted[sorted.length - 1]);
    }
}
```

The example shows why the mean hides the slow tail: the average is pulled up by a few outliers while the typical request is much faster.

### Stateless and stateful components
A **stateless** service keeps no per-client data between requests, so any instance can serve any request. Stateless services scale out and recover from crashes easily. A **stateful** component, such as a database, holds data that must be kept correct and available. Scaling it requires partitioning the data and replicating it. Good designs push state to a small number of well-understood stores and keep the rest of the application stateless.

### Idempotency and retries
Networks fail in ways where the caller cannot tell whether the operation happened: a timeout after the server already processed the request looks the same as a request that never arrived. Clients therefore retry, and the server must tolerate repeats. An **idempotent** operation gives the same result however many times it runs. Setting a status to "shipped" is idempotent; adding 10 to a balance is not.

A common technique is an **idempotency key**: the client sends a unique key with a create request, and the server stores the result for that key and returns it for any repeat. Retries should use exponential backoff with jitter, so many clients do not hammer a recovering service in lockstep.

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class IdempotentCreate {
    private final Map<String, String> resultsByKey = new ConcurrentHashMap<>();
    private int nextId = 1;

    public synchronized String createOrder(String idempotencyKey) {
        // A repeated key returns the original result instead of creating a second order
        return resultsByKey.computeIfAbsent(idempotencyKey, k -> "order-" + nextId++);
    }

    public static void main(String[] args) {
        IdempotentCreate service = new IdempotentCreate();
        System.out.println(service.createOrder("req-abc"));
        System.out.println(service.createOrder("req-abc")); // same result, no duplicate
    }
}
```

In production the key store must be durable and shared across instances, and it needs an expiry policy. The in-memory map here only illustrates the contract.

## How it works / Step by step
A reasoning checklist for any design question:
1. Define the availability target as an SLO, and the expected load.
2. Decide which parts scale vertically and which horizontally.
3. Remove single points of failure with redundancy and replication.
4. For each piece of data, choose the weakest acceptable consistency model.
5. State what happens during a partition: which side answers, and what the user sees.
6. Measure latency at the tail, not only the average.

## Common pitfalls
- Saying "we will use strong consistency everywhere" without considering the latency and availability cost.
- Treating CAP as choosing two of three permanently.
- Quoting an SLA without defining the SLI that measures it.
- Adding replicas without checking that failures are independent.
- Optimising average latency while the p99 is poor.

!!! tip "Interview tip"
    **Q: Explain CAP with an example.**
    Suppose two data centres lose contact. A system that must always return the latest balance has to refuse some reads or writes until they reconnect (CP). A system that keeps serving a product catalogue from both sides accepts that the answers may differ briefly (AP). Then mention PACELC: the same trade-off exists without a partition, in the form of latency versus consistency.

## Quick recap
- Vertical scaling is simple but capped; horizontal scaling needs distribution-aware design.
- Availability comes from redundancy, failover, and replication, and SLO and error budget make it measurable.
- Consistency models range from strong to eventual; choose the weakest that the requirement allows.
- Raft and Paxos achieve agreement through majority quorums; CAP applies during partitions, and PACELC covers normal operation.
- Report tail latency and throughput, not just averages.

**See also:** [High-Level Design](high-level-design.md), [Low-Level Design](low-level-design.md), [Practice Problems](practice-problems.md), [Redis and Caching](../12-caching-performance/index.md)
