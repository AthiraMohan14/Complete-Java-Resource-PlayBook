# Glossary

A quick, plain-language reference for the terms used across this Java interview playbook.

## A

**ACID** - four properties (atomicity, consistency, isolation, durability) that keep database transactions reliable.

**Actuator** - a Spring Boot feature that exposes health checks and metrics endpoints for a running app.

**AOP** - aspect-oriented programming, which adds shared work such as logging or security around methods without changing their code.

**API gateway** - a single entry point that routes client requests to the right backend services and can also handle auth and rate limits.

**Auto-configuration** - Spring Boot's ability to set up beans automatically based on the libraries it finds on the classpath.

## B

**B-tree** - a balanced tree that keeps keys sorted so a database can find rows quickly on disk.

**Bean** - an object whose creation and wiring are handled by the Spring container.

**Big O** - a notation that describes how an algorithm's time or memory use grows as the input grows.

## C

**Cache** - a fast copy of data kept close to the code so repeated reads are quicker.

**CAP theorem** - a rule stating that a distributed system can keep only two of consistency, availability, and partition tolerance during a network split.

**CDN** - a network of servers placed near users that stores static content so it loads faster.

**CI/CD** - the practice of automatically building, testing, and releasing code each time it changes.

**Circuit breaker** - a pattern that stops calls to a failing service for a while so the failure does not spread to other services.

**Class loader** - the JVM component that finds class files and loads them into memory when they are first needed.

**ConfigMap** - a Kubernetes object that stores non-secret configuration values for pods.

**Connection pool** - a set of reusable open database connections that avoids the cost of opening a new one for every request.

**Consumer group** - a set of consumers that share the work of reading a topic so each message is handled once by the group.

**Container** - a lightweight, isolated package that runs an application together with its dependencies.

**CORS** - a browser rule, controlled by response headers, that decides which other websites may call your API.

**CSRF** - an attack that tricks a logged-in browser into sending an unwanted request to a site.

## D

**Dead letter queue** - a holding queue for messages that failed processing too many times, so they can be inspected later.

**Deadlock** - a situation where two or more threads wait forever for locks that each other holds.

**Dependency injection** - a technique where an object receives the collaborators it needs from outside instead of creating them itself.

**Deployment** - in Kubernetes, an object that keeps the right number of identical pods running and manages updates to them.

**Docker** - a tool for building images and running them as containers.

**DTO** - a data transfer object, a plain object that carries data between layers or across the network.

**Dynamic programming** - a technique that solves a problem by storing answers to smaller subproblems so they are not recomputed.

## E

**Eventual consistency** - a model where copies of data may disagree for a short time but all settle on the same value over time.

## G

**Garbage collection (GC)** - the JVM process that frees memory held by objects the program can no longer reach.

**Generics** - a way to write classes and methods that work with a type parameter, such as a list of strings, with checks at compile time.

**Gradle** - a build tool that uses Groovy or Kotlin scripts to compile, test, and package Java projects.

**Graph** - a set of nodes connected by edges, used to model networks and relationships.

**Greedy** - an approach that makes the best local choice at each step and hopes it leads to a good overall answer.

**gRPC** - a fast remote call framework that uses Protocol Buffers over HTTP/2.

## H

**Hash map** - a Java collection that stores key-value pairs and finds values quickly by hashing the key.

**Hash table** - a data structure that maps keys to slots in an array using a hash function.

**Health check** - an endpoint that reports whether an app is alive and ready to receive traffic.

**Heap** - in Java, the memory area where objects live at runtime, and in algorithms, a tree that keeps the largest or smallest item on top.

**Helm** - a package manager for Kubernetes that bundles resource definitions into reusable charts.

## I

**Idempotency key** - a unique token a client sends so that a retried request is processed only once.

**Idempotent** - describes an operation that gives the same result no matter how many times it runs.

**Image** - a read-only template, built from layers, that a container starts from.

**Immutable** - describes an object whose state cannot change after it is created.

**Index** - a database structure that speeds up lookups on a column at the cost of extra storage and slower writes.

**Integration test** - a test that checks several real components together, such as the app working with a real database.

**IoC** - inversion of control, the principle that a framework rather than your own code controls object creation and flow.

**Isolation level** - a database setting that controls how much one transaction can see the uncommitted or concurrent changes of others.

**Iterator** - an object that walks through a collection one element at a time.

## J

**JIT** - the just-in-time compiler, which turns frequently run bytecode into native machine code while the app is running.

**JPA** - the Java standard for mapping Java objects to database tables.

**JVM** - the Java Virtual Machine, which runs compiled Java bytecode on any supported operating system.

**JWT** - a signed token that carries claims about a user, letting a service check identity without a database lookup.

## K

**Kafka** - a distributed log system for storing and streaming large volumes of events.

**Kubernetes** - a system that runs, scales, and heals containers across a cluster of machines.

## L

**Lambda** - a short anonymous function written with arrow syntax, often passed to streams or other methods.

**Latency** - the time it takes for one request to receive a response.

**Lazy loading** - loading related data only at the moment it is first accessed.

**Linked list** - a chain of nodes where each node stores a value and a reference to the next node.

**Load balancer** - a component that spreads incoming requests across several servers.

**Lock** - a mechanism that lets one thread at a time access a shared resource.

**Log** - a record of events written by an application, used for debugging and auditing.

## M

**Maven** - a build tool that manages dependencies and build steps using a pom.xml file.

**Message queue** - a buffer where producers place messages and consumers take them out later.

**Metric** - a numeric measurement, such as request count or response time, tracked over time.

**Microservice** - a small service that owns one business capability and can be deployed on its own.

**Mock** - a fake object used in tests that records calls or returns preset answers.

**Mockito** - a Java library for creating mock objects in unit tests.

**Monolith** - an application where all features are built and deployed together as one unit.

## N

**N+1 problem** - a performance issue where one query loads a list and then one extra query runs for each item in it.

**Normalisation** - splitting tables to remove duplicated data so that updates stay consistent.

## O

**OAuth** - an authorization standard that lets an app get limited access to a user's resources without the user's password.

**Observability** - the ability to understand a running system from its logs, metrics, and traces.

**OIDC** - OpenID Connect, an identity layer on top of OAuth that tells the app who the user is.

**Optional** - a Java wrapper that may or may not hold a value, used to reduce null checks.

**ORM** - object-relational mapping, a tool that converts database rows into objects and back.

## P

**Pagination** - splitting a long list of results into smaller pages that the client requests one at a time.

**Partition** - a slice of a Kafka topic that holds part of its messages and allows parallel reads.

**Pod** - the smallest deployable unit in Kubernetes, made of one or more containers that share network and storage.

## Q

**Queue** - a first-in, first-out collection where items leave in the order they arrived.

## R

**Race condition** - a bug where the result depends on the timing of threads that access shared data.

**Rate limiter** - a control that caps how many requests a client can make in a set time window.

**Record** - a Java class with a compact syntax for holding data, with common methods generated automatically.

**Recursion** - a function that solves a problem by calling itself on a smaller version of that problem.

**REST** - an architectural style that models resources as URLs and uses HTTP verbs to act on them.

**Reverse proxy** - a server that sits in front of backend servers and forwards client requests to them.

## S

**Saga** - a sequence of local transactions where each step has a compensating action that undoes it if a later step fails.

**Schema migration** - a versioned script that changes database structure in a controlled and repeatable way.

**Sealed class** - a class that limits which other classes may extend it, with the allowed subclasses listed in its declaration.

**Secret** - a Kubernetes object that stores sensitive values such as passwords or keys.

**Serialisation** - turning an object into bytes or text so it can be stored or sent, and turning it back again.

**Service mesh** - an infrastructure layer that manages service-to-service traffic, security, and metrics using sidecar proxies.

**Span** - a single timed step of work inside a distributed trace.

**Spring Boot** - a layer on top of Spring that sets up a runnable application with sensible defaults.

**Stack** - a last-in, first-out collection where the most recently added item is removed first.

**Stream** - a Java API for processing a sequence of elements with operations such as map, filter, and reduce.

**Synchronized** - a Java keyword that lets only one thread at a time run a block of code guarded by the same lock.

## T

**Thread** - the smallest unit of work the scheduler can run, with its own call stack inside a process.

**Throughput** - the number of requests or messages a system handles in a given amount of time.

**TLS** - Transport Layer Security, the protocol that encrypts traffic between a client and a server.

**Topic** - a named stream of messages in a broker such as Kafka that consumers subscribe to.

**Trace** - the full record of one request as it moves across services, made up of spans.

**Transaction** - a group of database operations that either all succeed or all get undone.

**Tree** - a hierarchical structure made of a root and child nodes, with no cycles.

**Trie** - a tree that stores strings character by character so prefix lookups are fast.

**TTL** - time to live, how long a cached entry or message stays valid before it expires.

## V

**Virtual thread** - a lightweight thread managed by the JVM that lets an app run many blocking tasks cheaply.

**Volatile** - a Java keyword that makes a variable's writes visible to all threads straight away.
