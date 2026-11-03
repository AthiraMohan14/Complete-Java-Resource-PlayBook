# System Design Fundamentals

Good system design means building a service that copes with heavy traffic, keeps running through failures, and stays easy to reason about as it expands. This section walks through the main trade-offs (scalability, availability, consistency, performance), the large-scale building blocks used to lay out a whole system, the object-oriented design applied inside one service, and practice problems with sample outlines.

---

## Topics

### [Core Concepts](core-concepts.md)
**Scaling - uptime - SLA, SLO, SLI - consistency - consensus - CAP - latency - throughput**
The terms and compromises that come up in nearly every design conversation.

### [High-Level Design](high-level-design.md)
**Load balancers - cache layers - partitioning - replica sets - queues - CDN - OLTP vs OLAP**
The components that show up in the majority of architecture diagrams, plus guidance on picking among alternatives.

### [Low-Level Design](low-level-design.md)
**Class modeling - interfaces - patterns - SOLID - API shape - failure handling - degrading gracefully**
Object-oriented structure within one service, illustrated with Java examples that compile.

### [Practice Problems](practice-problems.md)
**URL shortener - chat app - hotel reservations - needs gathering - building blocks - compromises**
A step-by-step method for tackling design questions, plus sample outlines for three of the eight frequently asked problems.

### More in this section

### [Replication, Sharding, and NoSQL](replication-sharding-nosql.md)
**Key ideas - Mechanics, step by step - Frequent mistakes - Summary**
Replication stores duplicate copies of data across nodes to ease read traffic and improve uptime. Sharding divides the data among nodes to relieve write pressure and storage limits....

### [Scalability and Failover](scalability-and-failover.md)
**Key ideas - Java approaches to scaling - Mechanics, step by step - Frequent mistakes - Summary**
Scalability means absorbing more traffic by adding capacity, while failover means continuing to serve requests after a part breaks. Inside a Java service, these two ideas overlap in the...

## Topics

### [Fundamentals](fundamentals.md)
**Scaling - Traffic distribution - Cache usage - Data partitioning - Copies of data - Consistency**  
Core ideas: scaling out versus scaling up, spreading load, splitting data into partitions, consistency models (ACID, BASE, CAP theorem), and the availability-versus-consistency tradeoff.

### [Building Blocks](building-blocks.md)
**Traffic balancers - Caches - Data stores - Queues - CDN - Throttling - API Gateways**  
Key components, covering when each applies, typical configuration, failure behavior, observability, cost versus benefit, and how they integrate.

### [Scalability & Resilience](scalability-and-failover.md)
**Autoscaling - Circuit Breakers - Timeouts - Retry logic - Bulkheads - Failover - Degradation handling**  
Designing for resilience: coping with faults, ways to recover, tracking metrics such as latency, throughput, and error rates, setting alerts, and running chaos experiments.

### [Worked Examples](worked-examples.md)
**Twitter - YouTube - Uber - Payment flows - Alerts - Case studies**  
Case-based walkthroughs of real products: how the problem is split up, how the architecture changes over time, how components talk to each other, the trade-offs taken, and rough capacity math.

---

## Quick Interview Prep

**How a system design interview usually unfolds:**
1. Agree on what the system must do and the quality bars it must meet (feature needs and non-feature needs such as speed and uptime)
2. Put rough numbers on the load: how many people use it, how many requests per second, how much data it holds, and how much network traffic it sends
3. Sketch the big picture: the public interfaces, the main components, and where the data lives
4. Zoom into the hard parts, such as caching, message queues, data copies, and how data is split across machines
5. Find the weak spots and the ways to grow past them
6. Talk through the compromises between consistency, response time, and cost

**Numbers worth estimating:**
- Requests per second (QPS), P99 latency, and how much storage is needed
- Network bandwidth, simultaneous connections, and the cache hit ratio
