# Technical Questions

Conceptual questions on Java, Spring, data, architecture, and DevOps, with answers you can check. Start with Core Java, then move to the domain pages.

---

## Topics

### [Core Java Questions (Part 1 of 3)](core-java-part-1.md)
**OOP - Strings - equals vs == - exceptions - collections - HashMap**
Language fundamentals and the questions interviewers ask first.

### [Core Java Questions (Part 2 of 3)](core-java-part-2.md)
Continues from Part 1.

### [Advanced Java: Concurrency, JVM Memory, and GC (Part 1 of 2)](advanced-java-concurrency-part-1.md)
**Threads - synchronisation - volatile - executors - CompletableFuture - virtual threads - JVM memory - GC**
Shared state, the concurrency toolkit, and how the JVM manages memory.

### [Advanced Java: Concurrency, JVM Memory, and GC (Part 2 of 2)](advanced-java-concurrency-part-2.md)
Continues from Part 1.

### [Spring, Spring Boot, and Security Questions (Part 1 of 4)](spring-and-security-part-1.md)
**IoC - dependency injection - bean scopes - Boot auto-configuration - transactions - Spring Security - JWT - OAuth**
The Spring container, transactions, and the security concepts behind a typical API.

### [Spring, Spring Boot, and Security Questions (Part 2 of 4)](spring-and-security-part-2.md)
Continues from Part 1.

### [Data and Persistence Questions (Part 1 of 4)](data-and-persistence-part-1.md)
**SQL - indexes - isolation levels - JDBC - JPA - N+1 - Flyway - Redis**
Query design, transactions, and how Java talks to the database.

### [Data and Persistence Questions (Part 2 of 4)](data-and-persistence-part-2.md)
Continues from Part 1.

### [Architecture and distributed systems](architecture-and-distributed.md)
**Microservices - Kafka - saga - outbox - CAP - resilience - caching - system design**
Service boundaries, messaging, consistency, and designing for failure.

### [DevOps, Cloud, Observability, and AI Questions (Part 1 of 3)](devops-cloud-and-ai-part-1.md)
**Docker - Kubernetes - CI/CD - cloud - observability - LLM - RAG**
Packaging, running, shipping, and observing services, plus the basics of AI features.

### [DevOps, Cloud, Observability, and AI Questions (Part 2 of 3)](devops-cloud-and-ai-part-2.md)
Continues from Part 1.


### [AI and Machine Learning Questions](ai-and-machine-learning.md)
**What is the difference between supervised and unsupervised learning? - What is overfitting, and how do you prevent it? - What is the bias-variance tradeoff? - How do convolutional neural networks work, and when would you use one? - Explain the transformer architecture and the attention mechanism.**
Core machine learning, deep learning, LLM, and production questions, with answers you can say out loud. Each answer gives a direct response first, then the reasoning and the...

### [Architecture and Distributed Systems Questions (Part 1 of 3)](architecture-and-distributed-part-1.md)
**When is a monolith the better choice than microservices? - How do you decide service boundaries, and why does each service own its data? - When do you use synchronous calls and when do you use asynchronous messaging? - How does Kafka organise data, and where is ordering guaranteed? - How do consumer groups share partitions, and what do offsets track?**
Questions on monolith versus microservices, service boundaries, synchronous and asynchronous communication, Kafka and RabbitMQ, and distributed transactions. Part 2 covers...

### [Architecture and Distributed Systems Questions (Part 2 of 3)](architecture-and-distributed-part-2.md)
**Walk me through how you would tackle an open-ended system design question. - A caller needs a service whose addresses keep changing. How does it find the right instance? - What is a bulkhead, and how does it differ from a circuit breaker? - What is the CAP theorem, and what does it mean in practice? - What consistency models should you know, and what does consensus do?**
Questions on system design approach, service discovery, resilience, CAP and consistency, caching, load balancing, scaling the database, event sourcing, idempotency, and a...

### [Core Java Questions (Part 3 of 3)](core-java-part-3.md)
**What is the difference between HashMap and ConcurrentHashMap? - What happens when an int overflows Integer.MAX_VALUE? - What is the value of `a++ + ++a` when `a` is 5? - What is the difference between `0.0 / 0.0` and `1 / 0` in Java? - What is the difference between Comparable and Comparator?**
Continued from [Part 2](core-java-part-2.md). Questions 19 to 27 cover collections, numeric edge cases, ordering, streams, memory, and enums.

### [Data and Persistence Questions (Part 3 of 4)](data-and-persistence-part-3.md)

### [Data and Persistence Questions (Part 4 of 4)](data-and-persistence-part-4.md)
Continues the data and persistence questions: Hibernate lifecycle and JPA versus MyBatis.

**How do INNER JOIN, LEFT JOIN, and UNION differ? - How do WHERE and HAVING differ? - What are the common database caching patterns? - What does the CAP theorem say, and what does it mean in practice? - What is the difference between ACID and BASE?**
Continued from [Part 2](data-and-persistence-part-2.md). These questions cover joins and set operators, caching, consistency models, indexes, normalisation, concurrent writes,...

### [Design Patterns Interview Questions (Part 1 of 2)](design-patterns-part-1.md)
**What is the Factory pattern and when should you use it? - What is the difference between Factory and Abstract Factory? - Explain the Builder pattern with a real example. - What is the Singleton pattern and when is it problematic? - Explain the Strategy pattern and give a use case.**
Factory, Abstract Factory, Builder, Singleton, Strategy, and Observer from the Gang of Four catalogue, with the Java examples interviewers usually expect. Answer each one aloud...

### [Design Patterns Interview Questions (Part 2 of 2)](design-patterns-part-2.md)
**Explain the Decorator pattern with an example. - What is the difference between Strategy and State? - What is the difference between a Proxy and a Decorator? - What is the Template Method pattern, and how does it differ from Strategy? - Which design patterns does the JDK itself use?**
Decorator, Strategy versus State, Proxy, Template Method, patterns in the JDK, and how Observer compares with publish/subscribe. Start with [Part 1](design-patterns-part-1.md)...

### [Spring, Spring Boot, and Security Questions (Part 3 of 4)](spring-and-security-part-3.md)
**What are the types of dependency injection, and why prefer constructor injection? - How does `@Transactional` work, and what are its rollback rules? - What are Spring bean scopes, and what is the bean lifecycle? - What is the difference between `@Component` and `@Bean`? - How do you secure a Spring Boot REST API?**
Continued from [Part 2](spring-and-security-part-2.md). These questions cover dependency injection, transactions, bean scopes, stereotypes, API security, and REST design.


### [Architecture and Distributed Systems Questions (Part 3 of 3)](architecture-and-distributed-part-3.md)
**Should a large Spring Boot codebase live in a monorepo or in multiple repos? Describe how you would structure it for microservices. - What are the key differences between layered, hexagonal (ports and adapters), and clean architecture? - How would you design a system like Jira? Cover projects, issues, workflows, permissions, search, and notifications. - Quick recap**
Questions on repository layout for microservices, architecture styles (layered, hexagonal, and clean), and a worked design for an issue tracker. Start with [Part...

### [DevOps, Cloud, Observability, and AI Questions (Part 3 of 3)](devops-cloud-and-ai-part-3.md)
**What is orchestration in software and DevOps, and how does it differ from automation? - Which Linux commands and scripts help deploy and maintain a Java application? - How do you automate log rotation or backups on a Linux server? - What is IRSA (IAM Roles for Service Accounts), and how does a pod assume an IAM role without credentials? - Quick recap**
Questions on orchestration compared with automation, Linux commands and scripts for deploying and maintaining a Java service, log rotation and backups, and how IAM Roles for...

### [Spring and Security Questions (Part 4 of 4)](spring-and-security-part-4.md)
**What is the purpose of @ModelAttribute in Spring Boot? - What is @EntityScan and when do you need it? - What are the performance implications of using AOP in Spring? - What is Thymeleaf or FreeMarker, and when would you use server-side templating instead of REST JSON? - Quick recap**
Continued from [Part 3](spring-and-security-part-3.md).

