# Phases 7 to 9: Delivery, Design and Advanced Topics

This part starts at week 50. Phase 7 is about packaging and running services: containers, Kubernetes, pipelines, and cloud platforms. Phase 8 covers system design and observability. Phase 9 covers API design and the advanced topics you pick up as your work requires them.

---

## Phase 7: DevOps and Cloud Deployment (weeks 50-63)

Phase 7 contains four topics and takes about fourteen weeks. Docker and Kubernetes come up most often in interviews from this phase.

### Topic 15: Docker (1-2 weeks)

**Fundamentals (3-4 days)**

- Containers share the host's kernel and isolate processes with namespaces, while cgroups cap their resources. A virtual machine boots its own kernel.
- Image layers and base images. Every Dockerfile instruction creates a layer, and layers that have not changed come from the build cache.
- Dockerfile instructions: `FROM`, `RUN`, `COPY`, `EXPOSE`, `ENTRYPOINT`, and `CMD`. `ENTRYPOINT` fixes the executable, and `CMD` supplies its default arguments.
- Multi-stage builds: compile in one stage, then copy only the result into a slimmer runtime image.
- Image tags and registries.

**Running containers (2-3 days)**

- `docker run` with ports, volumes, environment variables, and networks.
- Named volumes versus bind mounts, and the situations that suit each.
- Health checks, logs, and `docker exec` for debugging.

**Docker Compose (2-3 days)**

- Describing several containers in a single `docker-compose.yml` file.
- Service dependencies and startup order based on health.
- Overriding environment settings through files and variables.

**Spring Boot and Docker (1-2 days)**

- Layered JARs, so Docker can cache dependency layers apart from application code.
- JVM settings inside containers. Current JVMs read container memory limits, but heap sizing still needs checking.
- Running as a non-root user, and setting resource limits.

### Topic 16: Kubernetes (2-3 weeks)

**Week 1 focus: control plane and basic objects**

- The control plane: API server, scheduler, controller manager, and etcd.
- The worker nodes: kubelet, kube-proxy, and a container runtime.
- Pods, the smallest unit you can deploy. Containers in one pod share a network namespace.
- Deployments and ReplicaSets, and the mechanics of rolling updates and rollbacks.

**Week 2: configuration and workloads**

- ConfigMaps and Secrets. A Secret is only base64-encoded unless the cluster encrypts data at rest.
- PersistentVolumes and PersistentVolumeClaims.
- StatefulSets for stable identities, DaemonSets for one pod per node, and Jobs and CronJobs for batch work.
- Services: ClusterIP, NodePort, and LoadBalancer.
- Ingress, which routes HTTP traffic through an ingress controller.

**Week 3: operations and packaging**

- Probes: liveness, readiness, and startup. A failing liveness probe restarts the container, while a failing readiness probe pulls the pod out of service endpoints.
- Network policies, and service meshes such as Istio or Linkerd.
- RBAC, resource quotas, and namespaces.
- Helm for packaging charts with templated values.
- Operators and custom resource definitions for extending the API.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orders
  template:
    metadata:
      labels:
        app: orders
    spec:
      containers:
        - name: orders
          image: registry.example.com/orders:1.0.0
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
```

### Topic 17: CI/CD Pipelines (1-2 weeks)

**Branching patterns (2-3 days)**

- Git Flow: long-lived `main` and `develop` branches, with release and hotfix branches.
- GitHub Flow: short feature branches that reach `main` through pull requests.
- Trunk-based development: small changes merged to the trunk frequently, with feature flags hiding unfinished work.
- Commit message conventions, which make release notes easier to generate.

**CI stage (3-4 days)**

- GitHub Actions: workflows, triggers, jobs, and steps.
- Jenkins: scripted and declarative pipelines.
- GitLab CI: `.gitlab-ci.yml` files and runners.
- Build, unit tests, and static analysis on every change.
- Quality gates with SonarQube or Checkmarx, configured to block a merge when they fail.

**Release automation (3-4 days)**

- Rollout approaches: blue-green, canary, rolling, and shadow. Each trades cost, speed, and risk differently.
- Infrastructure as code with Terraform, CloudFormation, or Ansible.
- Secrets in the pipeline: rely on the CI system's secret store, and never print secrets to logs.
- Post-deployment checks, with automatic rollback when health checks fail.

### Topic 18: Cloud Platforms (2-3 weeks)

**AWS (one week, roughly)**

- Compute: EC2, Elastic Beanstalk, ECS, EKS, and Lambda.
- Storage: S3, EBS, and EFS.
- Databases: RDS, DynamoDB, and Aurora.
- Networking: VPC, Application and Network Load Balancers, and Route 53.
- Identity: IAM and KMS.
- Monitoring: CloudWatch for metrics and logs, CloudTrail for API activity.

**Azure (2-3 days)**

- Compute: virtual machines, App Service, and AKS.
- Data: Azure SQL Database and Cosmos DB.
- Networking: virtual networks and Application Gateway.
- DevOps: Azure Pipelines and Azure DevOps. In current documentation, Microsoft Entra ID has taken over the name Azure Active Directory.

**GCP (2-3 days)**

- Compute services: Cloud Run, GKE, Cloud Functions.
- Data stores: BigQuery, Firestore, Cloud SQL.
- Networking: Cloud Load Balancing plus Cloud CDN.
- DevOps: Cloud Build and Artifact Registry.

**Interview tip:** compare the three clouds by the service that fits a job, rather than by a product catalog. For example, "run a container without managing servers" maps to Fargate, Cloud Run, or Azure Container Apps.

---

## Phase 8: System Design and Observability (weeks 64-70)

Phase 8 has two topics that take about seven weeks.

### Topic 19: System Design (2-3 weeks)

**Week 1 focus: key ideas**

- **Scalability:** vertical scaling makes one machine bigger. Horizontal scaling adds more machines.
- **Availability:** redundancy and failover. An SLI is a measured value, an SLO is the target for that value, and an SLA is a contract with consequences attached.
- **Consistency:** strong, eventual, and causal. Each model gives up some latency or availability in exchange for stronger guarantees.
- **CAP theorem:** when a network partition occurs, a system has to pick consistency or availability.
- **Performance:** latency, throughput, and bandwidth, and how they differ from one another.

**Week 2: high-level building blocks**

- **Load balancing:** round robin, least connections, and hashing. Layer 4 balances connections, while layer 7 balances individual requests.
- **Caching:** cache-aside, write-through, and write-behind. Pick a TTL and an invalidation rule for each cache.
- **Database scaling:** read replicas, sharding, and replication lag.
- **Message queues:** take slow work off the request path.
- **CDN:** serve static content from edge locations near users.

**Week 3: design problems**

Practise a complete design for each of these. Begin with requirements and estimates, draw the components, then go deeper into the hardest part.

- **URL shortener:** key generation, collisions, and redirect paths.
- **Chat system:** real-time delivery, presence, and message history.
- **E-commerce:** catalog, inventory, orders, and payments.
- **Social feed:** feed generation (push or pull), caching, and real-time updates.
- **Ride sharing:** matching drivers to riders, location updates, and pricing.
- **Hotel booking:** availability, concurrent reservations, and holds.

**Interview tip:** for each design, name the bottleneck first. A design that scales the wrong component does not answer the question.

### Topic 20: Observability and Monitoring (1-2 weeks)

**Log handling (2-3 days)**

- SLF4J as the abstraction layer over Logback or Log4j2.
- The Elastic stack for search and dashboards: Elasticsearch, Logstash, and Kibana.
- Structured JSON logs, and correlation IDs that tie together the lines belonging to one request.
- Log levels, and sampling for high-volume paths.

**Metrics (2-3 days)**

- Micrometer as the metrics facade.
- Prometheus, which scrapes and stores time-series data.
- Grafana for dashboards and alert rules.
- The key signals: throughput, latency at p50, p95, and p99, error rate, and JVM metrics.

**Distributed tracing (2-3 days)**

- Micrometer Tracing, which replaced Spring Cloud Sleuth, creates trace and span IDs and passes them between services.
- Zipkin and Jaeger store and display traces.
- OpenTelemetry is the vendor-neutral standard covering traces, metrics, and logs.

**Alerting and health (2 days)**

- Alert thresholds, routing, and escalation. Alert on symptoms users feel, such as error rate and latency, and use causes for diagnosis.
- Health checks and liveness and readiness probes.
- Paging tools such as PagerDuty or Opsgenie.

---

## Phase 9: Advanced Topics and Specialization (weeks 71 onward)

Phase 9 has no fixed end date. Choose topics that match the roles you are aiming for.

### Topic 21: API Design and REST Practice (ongoing)

**REST principles**

- Resource-oriented URLs, and a stateless design in which each request carries everything it needs.
- HTTP methods: `GET` is safe and idempotent. `PUT` and `DELETE` are idempotent. `POST` is neither by default. `PATCH` changes part of a resource.
- Status codes in the 2xx, 3xx, 4xx, and 5xx ranges, and the most useful code for each case.
- Content negotiation through the `Accept` header.

**Versioning**

- URL versioning such as `/v1/` and `/v2/` is easy to spot and to route.
- Header or media-type versioning keeps URLs stable.
- Backward compatibility rules, and a published deprecation timeline.

**Pagination, filtering, and errors**

- Offset pagination is simple but gets slow on large tables. Cursor (seek) pagination scales better.
- Filtering, sorting, and partial responses.
- Errors in one consistent format. RFC 9457 "Problem Details" is the current standard, replacing RFC 7807.
- Idempotency keys, so that a retried `POST` does not create a duplicate.

**Other protocols**

- GraphQL for flexible queries shaped by the client.
- gRPC for typed, binary calls between services.
- WebSockets for two-way messages over a single connection.

### Topic 22: AI Integration (ongoing)

**LLM integration**

- Calling model APIs from OpenAI, Anthropic Claude, or Google Gemini. Each provider has its own SDK and request format.
- Prompt design and context management. Keep instructions separate from user data.
- Token limits, temperature, and other sampling parameters, and what each one changes.
- Handle timeouts, rate limits, and partial failures the same way you handle any remote call.

**Retrieval-augmented generation (RAG)**

- Ingest documents, split them into chunks, and store them with metadata.
- Generate embeddings for each chunk, and search by vector similarity.
- Add the retrieved chunks to the prompt, and check that the answer cites them.

**Vector databases**

- Options include Pinecone, Weaviate, Milvus, and Chroma. Each has different hosting and filtering features.
- Similarity metrics such as cosine similarity and dot product.
- Approximate nearest neighbour indexes give up a little recall in exchange for much faster search.

**Spring AI**

- Chat models and embedding models exposed through one interface.
- Tool calling, where the model asks the application to run a function and then uses the result.
- Structured output, which maps a model response onto a Java type.

### Topic 23: Specializations (as needed)

**Search and analytics**

- Elasticsearch for full-text search and aggregations.
- Real-time analytics and data warehouses for reporting workloads.

**Advanced patterns**

- Event sourcing at scale, with snapshots and retention rules.
- CQRS with eventually consistent read models.
- Saga orchestration across several services.
- Stream processing with Kafka Streams or Apache Flink.

**Machine learning for backend engineers**

- Model concepts, so you can discuss trade-offs with data scientists.
- Serving models behind a prediction API, with versioning and monitoring.

---

## Phase 7 to 9 Deliverables

- A service packaged as a container image, with a multi-stage Dockerfile and a Compose file for local runs.
- A Kubernetes deployment with probes, a service, and a config map, applied through a pipeline.
- A pipeline that builds, tests, scans, and deploys to a staging environment, with a rollback step.
- One written system design with estimates, a diagram, and a list of trade-offs.
- One small feature that uses an LLM API or a RAG pipeline, with timeouts and error handling.

**See also:** [Phases 4 to 6](phases-4-to-6.md), [Overview](index.md), [DevOps interview questions](../../interview-questions/technical/devops-cloud-and-ai-part-1.md), [System design interview questions](../../interview-questions/technical/architecture-and-distributed.md)
