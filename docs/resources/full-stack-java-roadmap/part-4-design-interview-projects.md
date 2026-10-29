# Part 4: System Design, Interview & Projects

Phases 8 to 10 of the [Full Stack Java Developer Roadmap](index.md). Learn to design systems, observe them, specialise, prepare for interviews, and prove your skills with projects.

---

## Phase 8: System Design & Observability

### 19. System Design Fundamentals (2–3 weeks)

#### Core Concepts
- **Scalability:** vertical (bigger/powerful machine) vs horizontal (more servers); trade-offs
- **Availability:** redundancy, failover, replication; SLA, SLO, and SLI metrics
- **Consistency:** strong, eventual, causal; consensus algorithms (Raft, Paxos at a high level)
- **Performance:** latency, throughput, bandwidth optimization
- **CAP theorem:** consistency, availability, and partition tolerance; the trade-off during a partition

#### High-Level Design (HLD)
- Architecture styles: MVC, layered, microservices, event-driven, lambda
- **Load balancing:** round-robin, least connections, weighted, IP hash, consistent hashing; Layer 4 (transport) vs Layer 7 (application) load balancing
- **Caching:** cache-aside, write-through, write-behind; TTLs & expiration; cache invalidation strategies ; distributed caches(Redis cluster)
- **Database scaling:** read replicas for read scaling; sharding (range, hash, consistent hashing); shard-key choice; cross-shard queries; primary-replica and multi-primary replication(Master-slave replication | Master-master replication)
- **Message queues:** asynchronous work and task distribution
- **CDNs:** geographic distribution, edge caching, compression
- **OLTP vs OLAP:** separate transactional and analytical workloads

#### Low-Level Design (LLD)
- Object-oriented design; class hierarchies; API design
- Design patterns: Singleton, Factory, Observer, Strategy, and others
- Applying SOLID principles
- Error handling and graceful degradation

#### Practice Problems
- **URL shortener:** key generation, collision handling, redirects, analytics
- **Chat system:** real-time messaging, user presence, message history, notifications
- **E-commerce:** Product catalogue, inventory, orders, payments, recommendations
- **Social feed:** feed generation, caching, real-time updates, distributed tracing
- **Hotel booking:** availability, concurrency control, reservations, payments
- **Ride-sharing(Uber):** matching, location tracking, pricing, ratings
- **Search engine:** crawling, indexing, ranking, distributed architecture
- **Video streaming:** encoding, CDN, adaptive bitrate, live streaming

---

### 20. Observability & Monitoring (1–2 weeks)

#### Logging
- **SLF4J(Simple Logging Facade):** the logging facade your code should depend on | Abstraction layer
- **Logback** (Spring Boot's default): configuration, appenders, layouts, async logging
- **Log4j2:** async loggers and performance options, layout options
- **ELK stack:** Elasticsearch, Logstash, Kibana; log ingestion, full-text search, Visualization dashboards, alerts
- **Structured logging:** JSON output, correlation IDs, context fields (MDC)
- **Log sampling** Reduce volume for high-traffic services
- **Log levels:** TRACE, DEBUG, INFO, WARN, ERROR, FATAL. Never log secrets or personal data.

#### Metrics
- **Micrometer:** the metrics facade used by Spring Boot Actuator
- **Prometheus:** time-series storage, scraping, alerting rules
- **Grafana:** Visualization, dashboards and alerting
- **Key metrics:**
  - Throughput (requests per second)
  - Latency at p50, p95, and p99
  - Error rate and success rate; Apdex score
  - JVM: heap usage, GC pause time, thread count
  - Business metrics: active users, conversions, revenue

#### Distributed Tracing
- **Micrometer Tracing** (the Spring Boot 3 successor to Spring Cloud Sleuth)
- **Zipkin:** trace storage, latency analysis, dependency graphs
- **Jaeger:** Distributed tracing with sampling and storage backends
- **OpenTelemetry:** the vendor-neutral standard for traces, metrics, and logs
- **Trace propagation:** passing trace headers between services
- **Sampling Strategies:** head-based, tail-based, probabilistic

#### Alerting
- Alert thresholds and conditions; alert on symptoms users feel (latency, errors)
- Routing and escalation; on-call rotations
- PagerDuty and Opsgenie integrations
- Reducing alert fatigue; correlating related alerts

#### Health Checks
- Spring Boot Actuator health endpoints
- Custom health indicators
- Liveness and readiness probes; check frequency and timeouts

---

## Phase 9: Advanced Topics & Specialisation

### 21. API Design & REST Best Practices

#### REST Principles
- Stateless design; resource-oriented URLs
- HTTP methods: `GET` (safe, idempotent), `POST` (unsafe, not idempotent), `PUT` and `PATCH` ( conditional updates), `DELETE`, `HEAD`, `OPTIONS`
- Status codes: 2xx success, 3xx redirect, 4xx client error, 5xx server error
- Content negotiation with `Accept` and `Content-Type`

#### Versioning
- URL versioning (`/v1/`, `/v2/`), header versioning, query parameters
- Deprecation timelines; managing breaking changes
- Backward compatibility strategies

#### Pagination & Filtering
- Offset-based pagination; cursor-based (keyset) pagination; the seek method
- Filtering (exact, range, pattern); sorting (single, multiple fields)
- Partial responses (sparse fieldsets); batch operations

#### Error Handling
- A consistent error response format
- Error codes and messages
- Problem Details (RFC 9457) for standard error bodies
- Validation errors with field-level detail

#### Idempotency
- Idempotent operations; idempotency keys for `POST`
- Retry-safe design
- Idempotency middleware
- Preventing duplicate processing

#### Alternative Protocols
- **GraphQL:** queries, mutations, subscriptions, schema definition
- **gRPC:** Protocol Buffers, streaming, HTTP/2, performance
- **WebSockets:** real-time bidirectional communication; connection management

#### API Security
- API keys, tokens, JWTs; rate limiting
- CORS policies; HTTPS enforcement
- Input validation and sanitization

---

### 22. AI Integration (1 week)

#### LLM Integration
- LLM APIs from several providers (for example OpenAI(GPT), Anthropic(Claude), Google(Gemini), and open-weight models such as Llama(Meta))
- Prompt design; managing context
- Token limits and cost control
- Sampling parameters: temperature, top-k, top-p
- Streaming responses; function (tool) calling

#### Retrieval-Augmented Generation (RAG)
- Document ingestion; text splitting and chunking
- Embeddings and vector similarity search
- Semantic search; adding retrieved context to prompts
- Re-ranking techniques; hybrid search (keyword BM25 plus vector)

#### Vector Databases
- Options: pgvector, Pinecone, Weaviate, Milvus, Chroma, Qdrant
- Indexes: HNSW, IVF; approximate nearest-neighbour search
- Similarity metrics: cosine, Euclidean, dot product, Manhattan
- Scaling and performance trade-offs

#### Spring AI
- The Spring AI framework: chat models and embeddings
- Tool-using agents; conversation memory
- Structured output parsing

#### Use Cases
- Chatbots and conversational assistants
- Content generation; code analysis
- Search and recommendation systems
- Question answering over your own documents

---

### 23. Additional Specialisations (as needed)

#### Search & Analytics
- Elasticsearch: full-text search, aggregations, relevance tuning
- Apache Solr as an alternative search platform
- Real-time analytics and data warehousing basics

#### Advanced Patterns
- Event sourcing at scale; CQRS with eventual consistency
- Distributed saga orchestration; workflow engines such as Temporal
- Stream processing: Kafka Streams, Apache Flink

#### Machine Learning for Backend Engineers
- Core ML concepts (training, features, evaluation)
- TensorFlow.js
- Serving models behind REST or gRPC APIs
- Prediction APIs
- Java options: Deep Java Library (DJL) and ONNX Runtime

---

## Phase 10: Interview Preparation & Portfolio

### 24. Interview Preparation Strategy

#### DSA Practice
- 250–350 LeetCode problems across easy, medium, and hard
- Focus on frequently asked topics: arrays, linked lists, trees, graphs, DP
- Consistent practice: one or two problems a day
- Understand each solution, then optimise for time and space

#### Java Core Deep Dive
- `HashMap` internals: hashing, buckets, collision handling, resizing
- `ArrayList` vs `LinkedList` performance and node structure
- Concurrency tools: `ReentrantLock`, `Semaphore`, `CyclicBarrier`
- The JVM memory model and GC algorithms
- Exception-handling best practices
- String handling and performance

#### Spring Boot Mastery
- Real-world scenarios: multi-tenancy, caching strategies, error handling
- Performance optimisation; database query tuning
- Security implementation; microservice patterns
- Testing strategies; deployment considerations

#### System Design Practice
- Solve 3–5 design problems end to end
- Document trade-offs clearly
- Discuss scaling at each level
- Present with confidence and handle follow-up questions

#### Behavioural Interviews
- STAR method: Situation, Task, Action, Result
- Examples of leadership, conflict resolution, and learning
- Collaboration and impact, with numbers where you can

#### Mock Interviews
- Practise with peers or on interview platforms (LeetCode, InterviewBit)
- Record yourself and review your answers
- Ask for feedback on communication and technical depth

---

### 25. Real-World Projects (build 2–3 substantial projects)

#### Project 1: E-Commerce Platform
- Authentication and authorisation (JWT, OAuth 2.0)
- Product catalogue with search, filtering, and sorting
- Shopping cart; order management system
- Payment integration with a sandbox provider (for example Stripe/PayPal)
- Admin dashboard with analytics
- Deployed on AWS or Azure with monitoring
- Load testing & performance optimization
- Database optimization & query tuning

#### Project 2: Social Media / Feed System
- User profiles; follow and unfollow
- Feed generation with caching and personalisation
- Real-time notifications with WebSockets
- Microservices: user, feed, and notification services
- Message queues for asynchronous work
- Kubernetes deployment with scaling
- Distributed tracing and observability

#### Project 3: Multi-Tenant SaaS Application
- Multi-tenant data isolation
- Subscription management and billing (test mode)
- Analytics dashboard
- API-first design with full documentation
- Unit, integration, and end-to-end tests
- CI/CD pipeline with automatic deployment
- Infrastructure as code (Terraform)
- Database migration strategy

#### Portfolio Requirements
- **Code quality:** clean, maintainable, production-grade code
- **Documentation:** README, API docs (OpenAPI/Swagger), architecture diagrams
- **Git history:** clear commit messages that show incremental work
- **Live demo:** deployed with a domain name and HTTPS
- **Performance:** optimised queries, caching, load-test results
- **Security:** no hard-coded secrets; input validation; proper authentication
- **Scalability:** a design that can handle large load, with test data to prove it

---

## Hands-On Project Ladder

Build these in order. Each one reinforces the topics above.

| Level | Project | Skills practised |
|---|---|---|
| Beginner | CLI banking system | OOP, exceptions, file storage |
| Beginner | String utility toolkit | Strings, encodings, reversals |
| Beginner | Array analytics tool | Arrays, loops, basic statistics |
| Intermediate | Employee management system | Collections, streams, Optional |
| Intermediate | File-based task manager | I/O, serialisation |
| Intermediate | Multithreaded file downloader | Threads, executors, I/O |
| Advanced | In-memory order processing engine | Concurrency, streams, locking |
| Advanced | Generic cache framework | Generics, maps, eviction policies |
| Advanced | Producer-consumer messaging system | Blocking queues, threads, back pressure |
| Capstone | Mini Java backend core | Layered architecture, DTOs, services, exception handling, streams, concurrency, JVM performance notes |

---

## Must-Know Interview Checklist

For each topic, know the **definition**, a **short example**, and one **pitfall**. That is what interviewers look for.

### Core Java
- `==` vs `equals()`
- String immutability
- `final`, `finally`, and `finalize()` (`finalize` is deprecated for removal)
- Widening vs narrowing casting
- Checked vs unchecked exceptions

### OOP
- Runtime vs compile-time polymorphism
- Abstract class vs interface
- Why Java classes cannot extend more than one class (the diamond problem), and how default methods change the picture
- SOLID principles at a basic level

### Collections
- How `HashMap` works: hashing, buckets, collisions, treeification
- `List` vs `Set` vs `Map`
- `Comparable` vs `Comparator`
- `ConcurrentHashMap` vs `HashMap` vs `Collections.synchronizedMap`

### Java 8+
- Stream vs collection
- `map` vs `flatMap`
- Optional best practices (avoid it for fields and parameters; use it for return values)
- Functional interface rules (exactly one abstract method)

### Multithreading
- `Runnable` vs `Thread`
- Synchronisation
- Deadlock: the four conditions and how to avoid them
- `volatile` vs `synchronized`

### JVM
- Heap vs stack
- GC types and when each suits a workload
- JIT compiler

---

## Other Java APIs and Frameworks to Recognise

These are older or specialist technologies you may be asked about. Know what they are and when you would meet them.

- **Servlets and JSP:** the foundation under Spring MVC; JSP is largely replaced by template engines such as Thymeleaf
- **Swing:** Java desktop GUI toolkit; still found in legacy applications
- **AWS SDK for Java:** concepts of clients, credentials, and regions; the Java SDK v2 is the current version
- **JDBC:** covered in [Part 2](part-2-data-spring.md#jdbc)

---

## Back to the Start

Return to the [overview](index.md) to start again from Phase 1.
