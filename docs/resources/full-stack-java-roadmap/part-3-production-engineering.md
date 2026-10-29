# Part 3: Production Engineering

Phases 5 to 7 of the [Full Stack Java Developer Roadmap](index.md). Learn to secure, test, speed up, connect, package, ship, and run your services.

---

## Phase 5: Security, Testing & Caching

### 10. Security (2 weeks)

#### Spring Security Fundamentals
- Authentication vs authorisation
- `SecurityContext`, `UserDetails`, `UserDetailsService`
- The security filter chain: requests pass through a chain of filters before they reach your controllers
- DispatcherFilter pattern
- Authentication providers

#### Authorisation & Access Control
- Role-based access control (RBAC); `GrantedAuthority`
- Method security: `@Secured`, `@PreAuthorize`, `@PostAuthorize`

#### Authentication Mechanisms
- HTTP Basic authentication; form-based login
- **JWT (JSON Web Tokens):** header, payload, signature; creation and validation; expiry; refresh tokens; stateless authentication; token storage strategies
- **OAuth 2.0:** authorisation code flow (with PKCE for public clients), client credentials. The resource owner password grant is removed from OAuth 2.1; avoid it in new designs.
- **OpenID Connect:** ID tokens; the user info endpoint
- **SAML:** assertions and bindings (common in enterprise single sign-on)
- **Multi-factor authentication (MFA):** TOTP, SMS, push notifications
  
#### Password Security
- Hashing with BCrypt, Argon2, SCrypt, or PBKDF2 (never plain or fast hashes)
- Salts; the role of a pepper
- Password strength rules; rate limiting on login attempts

#### CORS & CSRF
- Cross-Origin Resource Sharing (CORS) and preflight requests
- `@CrossOrigin` and `CorsConfigurationSource`
- CSRF tokens (needed for cookie-based sessions); the `SameSite` cookie attribute

#### HTTPS & TLS
- SSL/TLS protocols; certificate management; cipher suites
- HSTS (HTTP Strict Transport Security)

#### OWASP Top 10 (2021 edition; check the latest version)
| Category | Example defence |
|---|---|
| A01 Broken Access Control | Deny by default; check permissions on the server |
| A02 Cryptographic Failures | Encrypt data in transit and at rest; use current algorithms |
| A03 Injection (including XSS) | Parameterised queries; output encoding |
| A04 Insecure Design | Threat modelling before coding |
| A05 Security Misconfiguration | Hardened defaults; remove unused features and endpoints |
| A06 Vulnerable Components | Dependency scanning (SCA); keep libraries updated |
| A07 Identification & Authentication Failures | MFA; strong password hashing; session management |
| A08 Software & Data Integrity Failures | Avoid unsafe deserialisation; verify artefact signatures |
| A09 Logging & Monitoring Failures | Log security events; alert on them |
| A10 Server-Side Request Forgery (SSRF) | Allow-list outbound destinations |

#### Secrets Management
- Environment variables; Spring Cloud Vault
- AWS Secrets Manager; Azure Key Vault
- HashiCorp Vault; secret rotation
- Never commit secrets to Git

#### Security Headers
- `Content-Security-Policy` (CSP), `X-Frame-Options`, `X-Content-Type-Options`
- `Referrer-Policy`, `Permissions-Policy`

---

### 11. Testing (1–2 weeks)

#### Unit Testing with JUnit 5(Jupiter)
- `@Test`, `@BeforeEach`, `@AfterEach`, `@BeforeAll`, `@AfterAll`
- Parameterised tests (`@ParameterizedTest`); dynamic tests
- Assertions (`Assertions.*`, AssertJ for readable fluent assertions)
- TestInfo & TestReporter injection

#### Mocking with Mockito
- `@Mock`, `@InjectMocks`, `@Spy`
- Stubbing with `when(...).thenReturn(...)`
- Verification with `verify(...)`; argument matchers (`any()`, `eq()`, `argThat()`)
- Argument captors
- Mocks vs spies vs real objects. Mock only what you do not own, and avoid over-mocking.

#### Integration Testing
- `@SpringBootTest`; Spring test context caching
- `@DirtiesContext`; test execution listeners
- Testcontainers for real databases, Kafka, Redis, and more

#### API Testing
- `MockMvc`: `perform()`, `andExpect()`, `andReturn()`
- REST Assured: `given().when().then()` style
- Postman collections; automation with Newman (CLI)
- Contract testing with Spring Cloud Contract

#### Code Coverage
- JaCoCo for line, branch, and method coverage
- Coverage goals that make sense (coverage shows what ran, not whether the test checks anything)
- SonarQube quality gates

---

### 12. Caching & Performance Optimisation (1–2 weeks)

#### Spring Cache Abstraction
- `@Cacheable`, `@CacheEvict`, `@CachePut`, `@Caching`
- Cache managers: simple, concurrent, composite
- Cache keys and key generation
- Conditional caching: `@Cacheable(condition = ...)`

#### Redis
- Data structures: strings, lists, sets, hashes, sorted sets, streams, bitmaps
- Spring Data Redis: `StringRedisTemplate`, `RedisTemplate`
- Session storage with Spring Session and Redis
- Pub/sub and Redis Streams
- Distributed locks (Redlock; Lua scripts for atomic operations)
- Redis Cluster and replication; persistence (RDB snapshots, AOF log)

#### Performance Optimisation
- Profilers: JVisualVM, JProfiler, YourKit, async-profiler
- Finding bottlenecks: measure before you change anything
- Database query optimisation: N+1 problems, eager vs lazy loading
- Connection pool sizing
- JVM tuning: heap sizing, GC choice, GC flags
- Metrics and analysis; load testing with JMeter, Gatling, or k6

#### Distributed Caching
- Memcached; cache coherence across nodes
- Invalidation strategies: cache-aside, write-through, write-behind
- Coordinating writes between cache and database

---

## Phase 6: Messaging & Microservices

### 13. Messaging & Event-Driven Architecture (1–2 weeks)

#### Apache Kafka
- Architecture: brokers, topics, partitions, replicas, leaders
- Producers: key-based serialization, partitioning; acknowledgements (`acks`)
- Consumers: consumer groups, offsets, rebalancing, commit strategies (auto vs manual)
- Delivery semantics: at-most-once, at-least-once, exactly-once
- Ordering is guaranteed only within a partition; tombstone messages for compaction
- Spring for Apache Kafka: `KafkaTemplate`, `@KafkaListener`
- Error handling and dead-letter topics (DLT)
- Schema management: Avro, Protobuf, JSON Schema
- Kafka Streams; Kafka Connect

#### RabbitMQ
- AMQP protocol; exchanges, queues, bindings, routing keys
- Exchange types: direct, topic, fanout, headers
- Message TTL; queue length limits
- Dead-letter exchanges; RPC over RabbitMQ
- Spring AMQP: `@RabbitListener`, `RabbitTemplate`
- Acknowledgements (auto vs manual); `nack` handling

#### Event-Driven Architecture
- Event sourcing: event store and replay
- CQRS(Command Query Responsibility Segregation): separate command (write) and query (read) models
- Saga pattern: choreography vs orchestration
- Event ordering, eventual consistency
- Event versioning and upcasting

#### Message Patterns
- Publish/subscribe; request/reply; routing and filtering
- Message deduplication; idempotent consumers

---

### 14. Microservices Architecture (3–4 weeks)

#### Microservices Fundamentals
- Service decomposition strategies; bounded contexts (Domain-Driven Design)
- Database per service
- Monolith vs microservices: trade-offs and when a monolith is the right answer

#### Spring Cloud
- **Service discovery:** Netflix Eureka (client & server-side discovery); awareness of Consul and etcd; Service registration and deregistration
- **Load balancing:** Spring Cloud LoadBalancer (Ribbon is no longer maintained); round-robin, least-connections, random strategies
- **Configuration:** Spring Cloud Config Server, Centralized configuration; environment profiles; refresh with `@RefreshScope`; Git-backed configuration
- **API gateway:** Spring Cloud Gateway; routing, filters, rate limiting, Load balancing at gateway level, path rewriting
- **Distributed tracing:** Micrometer Tracing with Zipkin, Jaeger, or OpenTelemetry. Spring Cloud Sleuth is no longer available in Spring Boot 3.Trace ID & span ID propagation | Sampling strategies

#### Resilience Patterns
- **Circuit breaker:** closed, open, and half-open states; failure thresholds; recovery. Hystrix is retired; use Resilience4j.
- **Retry:** exponential backoff, max retries; Spring Retry's `@Retryable`
- **Timeouts:** request timeouts; deadline propagation
- **Bulkhead:** thread-pool isolation; semaphore isolation
- **Rate limiting & Throttling:** token bucket algorithm; sliding window; distributed rate limiting

#### Inter-Service Communication
- **Synchronous:** REST(HTTP), gRPC, GraphQL
- **Asynchronous:** Kafka, RabbitMQ, AWS SQS
- **Service-to-service security:** mTLS; propagating JWTs
- **API versioning:** backward-compatible change strategies

#### Distributed Transactions
- CAP theorem; eventual consistency
- Saga pattern: choreography and orchestration
- Compensating transactions; limits of two-phase commit (2PC)
- Idempotency and deduplication

#### Monitoring & Observability
- Centralised logging: ELK stack (Elasticsearch, Logstash, Kibana)
- Metrics: Prometheus and Grafana
- Distributed tracing: Zipkin, Jaeger
- Health checks and readiness probes
- Application performance monitoring (APM)

---

## Phase 7: DevOps & Cloud Deployment

### 15. Docker & Containerisation (1–2 weeks)

#### Docker Fundamentals
- Containers vs virtual machines; namespaces and cgroups
- Docker Images and layers; base images; image size reduction
- Dockerfile instructions: `FROM`, `RUN`, `COPY`, `ADD`, `EXPOSE`, `ENTRYPOINT`, `CMD`
- Multi-stage builds
- Tags and registries (Docker Hub, private registries)
- Container lifecycle: create, start, stop, remove

#### Container Operations
- `docker run` options: ports, volumes, environment variables, networks
- Volumes: bind mounts, named volumes, tmpfs
- Container Networking: bridge, host, overlay
- Health checks; logs; `docker exec`

#### Docker Compose
- Multi-container setups; the `docker-compose.yml` (Compose Specification) format
- Services, networks, and volumes definitions
- Service dependencies and health checks
- Override files for different environments

#### Spring Boot in Containers
- Containerising Spring Boot applications
- Layered JARs and Spring Boot's Docker support
- JVM memory settings in containers (container-aware JVM flags)
- CPU and memory limits; running as a non-root user

---

### 16. Kubernetes & Orchestration (2–3 weeks)

#### Architecture
- Control plane: API server, scheduler, controller manager, etcd
- Worker nodes: kubelet, kube-proxy, container runtime
- Clusters, namespaces, RBAC (role-based access control)

#### Core Objects
- **Pods:** the smallest deployable unit(Atomic unit); containers, volumes, networking
- **Deployments:** replicas, rolling updates, rollbacks
- **ReplicaSets:** keeping the desired number of pods running
- **StatefulSets:** Ordered, stable identities and persistent storage
- **Services:** ClusterIP, NodePort, LoadBalancer, ExternalName
- **Ingress:** HTTP and HTTPS routing. The Gateway API is the successor to Ingress for new work.

#### Configuration & Storage
- **ConfigMaps:** non-sensitive configuration
- **Secrets:** credentials, tokens, certificates (encrypt at rest; they are base64-encoded, not encrypted, by default)
- **PersistentVolumes (PV):** Storage resources and **PersistentVolumeClaims (PVC):** Storage requests
- **StorageClasses:** dynamic provisioning

#### Workloads
- **DaemonSets:** one pod per node (logging, monitoring agents)
- **Jobs** for one-off tasks; **CronJobs** for scheduled tasks
- **Init containers:** setup steps before app containers start

#### Health & Lifecycle
- **Liveness probe:** restart the container if it is stuck/unhealthy
- **Readiness probe:** route traffic only when the pod is ready
- **Startup probe:** allow slow starts without premature restarts
- **Graceful shutdown:** `terminationGracePeriodSeconds` and handling `SIGTERM` in Spring (`server.shutdown=graceful`)

#### Networking
- Pod-to-pod communication; service discovery through DNS
- **Network policies:** control ingress and egress traffic
- **Service meshes:** Istio, Linkerd

#### Advanced Topics
- Resource requests and limits; quotas, memory constraints
- Namespaces for multi-tenancy and resource isolation
- **Helm:** packaging, charts, templating
- **Operators:** custom resource definitions (CRDs) and controller patterns

---

### 17. CI/CD Pipelines (1–2 weeks)

#### Version Control Workflows
- Git: branches, commits, merges, rebasing
- **Git Flow:** main, develop, release, and hotfix branches
- **GitHub Flow:** main plus short-lived feature branches and pull requests
- **Trunk-based development:** very short-lived branches, frequent merges to main
- Commit message conventions; code review practice

#### Continuous Integration
- **GitHub Actions:** workflows, events, jobs, steps
- **Jenkins:** declarative and scripted pipelines; stages; agents
- **GitLab CI:** `.gitlab-ci.yml`, runners, Docker-based builds
- Build automation; compilation; unit tests
- **Quality gates:** SonarQube, Checkmarx, Prisma Cloud
- **SAST and DAST:** static and dynamic security testing
- **SCA( Software Composition Analysis):** dependency scanning
- Artefact management: Nexus, Artifactory

#### Continuous Deployment
- **Deployment strategies:**
  - Blue-green: two environments; switch traffic
  - Canary: gradual rollout to a subset of users
  - Rolling: incremental updates with no downtime
  - Shadow: the new version receives a copy of production traffic
- **Infrastructure as code (IaC):** Terraform (HCL syntax, state management, modules); CloudFormation (AWS); Ansible for configuration
- **Secrets in pipelines:** GitHub Secrets, GitLab CI variables, Vault integration, Encrypted environment variables
- **After deployment:** smoke tests; health checks; automatic rollback; approvals and notifications

---

### 18. Cloud Platforms (2–3 weeks)

#### AWS
- **Compute:** EC2 (instances, AMIs), Elastic Beanstalk, ECS, EKS, Lambda
- **Storage:** S3 (buckets, objects), EBS (block storage), EFS (shared file storage)
- **Database:** RDS (MySQL, PostgreSQL, Oracle), DynamoDB, Aurora
- **Networking:** VPC (subnets, security groups), ALB, NLB, CloudFront, Route 53
- **Identity & Access:** IAM (roles, policies, users), KMS (key management)
- **Monitoring & Logging:** CloudWatch, CloudTrail
- **Messaging:** SQS, SNS, Kinesis
- **CI/CD:** CodePipeline, CodeBuild, CodeDeploy
- **Cost Optimization:** reserved and spot instances; right-sizing

#### Microsoft Azure
- **Compute:** Virtual Machines, App Service, Container Instances, AKS
- **Data:** Azure SQL Database, Cosmos DB(NoSQL), Blob Storage
- **Networking:** virtual networks, Application Gateway, Azure CDN
- **Identity:** Microsoft Entra ID (formerly Azure AD), managed identities
- **DevOps:** Azure DevOps, Azure Pipelines
- **Monitoring:** Application Insights, Log Analytics

#### Google Cloud Platform (GCP)
- **Compute:** Compute Engine(VMs), Cloud Run, Google Kubernetes Engine (GKE), Cloud Functions
- **Data:** Cloud SQL, Firestore, Datastore, Bigtable, BigQuery
- **Storage:** Cloud Storage(GCS), persistent disks
- **Networking:** Cloud VPC, Cloud Load Balancing, Cloud CDN
- **Identity:** Cloud Identity, service accounts
- **DevOps:** Cloud Build, Artifact Registry
- **Monitoring:** Cloud Monitoring, Cloud Logging

#### Multi-Cloud Considerations
- Avoiding vendor lock-in; portability strategies
- Cost comparison & optimization; hybrid cloud
- Data residency and compliance requirements

---

## Next

Continue to [Part 4: System Design, Interview & Projects](part-4-design-interview-projects.md).
