# System Design Fundamentals

System design asks how to build a service that handles large load, survives failures, and stays understandable as it grows. This section covers the core trade-offs (scalability, availability, consistency, and performance), the high-level building blocks used to design a whole system, the object-oriented design used inside a service, and a set of practice problems with worked outlines.

---

## Topics

### [Core Concepts](core-concepts.md)
**scalability - availability - SLA SLO SLI - consistency - consensus - CAP - latency - throughput**
The vocabulary and trade-offs that every design discussion relies on.

### [High-Level Design](high-level-design.md)
**load balancing - caching - sharding - replication - message queues - CDN - OLTP OLAP**
The building blocks that appear in most architecture diagrams, and how to choose between the options.

### [Low-Level Design](low-level-design.md)
**classes - interfaces - design patterns - SOLID - API design - error handling - graceful degradation**
Object-oriented design inside a service, with compiling Java examples of common patterns.

### [Practice Problems](practice-problems.md)
**URL shortener - chat system - hotel booking - requirements - components - trade-offs**
How to approach a design problem step by step, with worked outlines for three of the eight common problems.

### More in this section

### [Replication, Sharding, and NoSQL](replication-sharding-nosql.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Replication keeps copies of data on several nodes, which helps with read load and availability. Sharding splits data across nodes, which helps with write load and data size....

### [Scalability and Failover](scalability-and-failover.md)
**Core concepts - Java scaling patterns - How it works / Step by step - Common pitfalls - Quick recap**
Scalability is the ability to handle more load by adding resources, and failover is the ability to keep serving when a component fails. In a Java service the two meet in the...

