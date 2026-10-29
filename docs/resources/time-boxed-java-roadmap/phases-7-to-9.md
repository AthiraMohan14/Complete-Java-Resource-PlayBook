# Phases 7 to 9: Delivery, Design and Advanced Topics

This part covers weeks 50 onward. Phase 7 packages and runs services: containers, Kubernetes, pipelines, and cloud platforms. Phase 8 covers system design and observability. Phase 9 covers API design and the advanced topics you pick up as needed.

---

## Phase 7: DevOps and Cloud Deployment (weeks 50-63)

Phase 7 has four topics and takes about fourteen weeks. Docker and Kubernetes are the most common interview subjects in this phase.

### Topic 15: Docker (1-2 weeks)

**Fundamentals (3-4 days)**

- Containers share the host kernel. They isolate processes with namespaces and limit resources with cgroups. A virtual machine runs its own kernel.
- Image layers and base images. Each instruction in a Dockerfile adds a layer, and unchanged layers are reused from the cache.
- Dockerfile instructions: `FROM`, `RUN`, `COPY`, `EXPOSE`, `ENTRYPOINT`, and `CMD`. `ENTRYPOINT` sets the executable, and `CMD` gives its default arguments.
- Multi-stage builds, which compile in one stage and copy only the output into a smaller runtime image.
- Image tags and registries.

**Running containers (2-3 days)**

- `docker run` with ports, volumes, environment variables, and networks.
- Named volumes and bind mounts, and when each one fits.
- Health checks, logs, and `docker exec` for debugging.

**Docker Compose (2-3 days)**

- Describing several containers in one `docker-compose.yml` file.
- Service dependencies and health-based startup order.
- Environment overrides with files and variables.

**Spring Boot and Docker (1-2 days)**

- Layered JARs, which let Docker cache the dependency layers separately from the application code.
- JVM settings inside containers. The JVM reads container memory limits in current versions, but heap settings still need a check.
- Run as a non-root user, and set resource limits.

### Topic 16: Kubernetes (2-3 weeks)

**Week 1: architecture and core objects**

- The control plane: the API server, the scheduler, the controller manager, and etcd.
- The worker nodes: the kubelet, kube-proxy, and a container runtime.
- Pods, the smallest deployable unit. Containers in a pod share a network namespace.
- Deployments and ReplicaSets, and how rolling updates and rollbacks work.

**Week 2: configuration and workloads**

- ConfigMaps and Secrets. A Secret is base64-encoded, not encrypted, unless the cluster enables encryption at rest.
- PersistentVolumes and PersistentVolumeClaims.
- StatefulSets for stable identities, DaemonSets for one pod per node, and Jobs and CronJobs for batch work.
- Services: ClusterIP, NodePort, and LoadBalancer.
- Ingress, which routes HTTP traffic through an ingress controller.

**Week 3: operations and packaging**

- Probes: liveness, readiness, and startup. A failing liveness probe restarts the container. A failing readiness probe removes the pod from service endpoints.
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

**Branching models (2-3 days)**

- Git Flow: long-lived `main` and `develop` branches with release and hotfix branches.
- GitHub Flow: short feature branches merged through pull requests into `main`.
- Trunk-based development: small changes merged to the trunk often, with feature flags for unfinished work.
- Commit message conventions, which make release notes easier to generate.

**Continuous integration (3-4 days)**

- GitHub Actions: workflows, events, jobs, and steps.
- Jenkins: scripted and declarative pipelines.
- GitLab CI: `.gitlab-ci.yml` and runners.
- Build, unit tests, and static analysis on every change.
- Quality gates with SonarQube or Checkmarx, set to block a merge when they fail.

**Continuous deployment (3-4 days)**

- Deployment strategies: blue-green, canary, rolling, and shadow. Each trades cost, speed, and risk differently.
- Infrastructure as code with Terraform, CloudFormation, or Ansible.
- Secrets in the pipeline: use the CI system's secret store, and never print secrets in logs.
- Post-deployment checks and automatic rollback when health checks fail.

### Topic 18: Cloud Platforms (2-3 weeks)

**AWS (about one week)**

- Compute: EC2, Elastic Beanstalk, ECS, EKS, and Lambda.
- Storage: S3, EBS, and EFS.
- Databases: RDS, DynamoDB, and Aurora.
- Networking: VPC, Application and Network Load Balancers, and Route 53.
- Identity: IAM and KMS.
- Monitoring: CloudWatch for metrics and logs, and CloudTrail for API activity.

**Azure (2-3 days)**

- Compute: virtual machines, App Service, and AKS.
- Data: Azure SQL Database and Cosmos DB.
- Networking: virtual networks and Application Gateway.
- DevOps: Azure Pipelines and Azure DevOps. For identity, Microsoft Entra ID replaces Azure Active Directory in current documentation.

**GCP (2-3 days)**

- Compute: Cloud Run, GKE, and Cloud Functions.
- Data: BigQuery, Firestore, and Cloud SQL.
- Networking: Cloud Load Balancing and Cloud CDN.
- DevOps: Cloud Build and Artifact Registry.

**Interview tip:** compare the three clouds by the service that matches a job, not by the list of products. For example, "run a container without managing servers" maps to Fargate, Cloud Run, or Azure Container Apps.

---

## Phase 8: System Design and Observability (weeks 64-70)

Phase 8 has two topics that take about seven weeks.

### Topic 19: System Design (2-3 weeks)

**Week 1: core concepts**

- **Scalability:** vertical scaling adds resources to one machine. Horizontal scaling adds machines.
- **Availability:** redundancy and failover. SLI is a measured value, SLO is a target for it, and SLA is a contract with consequences.
- **Consistency:** strong, eventual, and causal. Each one trades latency and availability for stronger guarantees.
- **CAP theorem:** during a network partition, a system must choose between consistency and availability.
- **Performance:** latency, throughput, and bandwidth, and how they differ.

**Week 2: high-level building blocks**

- **Load balancing:** round robin, least connections, and hashing. Layer 4 balances connections, layer 7 balances requests.
- **Caching:** cache-aside, write-through, and write-behind. Choose a TTL and an invalidation rule for each cache.
- **Database scaling:** read replicas, sharding, and replication lag.
- **Message queues:** move slow work off the request path.
- **CDN:** serve static content from locations close to users.

**Week 3: design problems**

Practise a full design for each of these. Start with requirements and estimates, then draw the components, then go deeper on the hardest part.

- **URL shortener:** key generation, collisions, and redirect paths.
- **Chat system:** real-time delivery, presence, and message history.
- **E-commerce:** catalog, inventory, orders, and payments.
- **Social feed:** feed generation (push or pull), caching, and real-time updates.
- **Ride sharing:** matching drivers to riders, location updates, and pricing.
- **Hotel booking:** availability, concurrent reservations, and holds.

**Interview tip:** for each design, name the bottleneck first. A design that scales the wrong component is not an answer.

### Topic 20: Observability and Monitoring (1-2 weeks)

**Logging (2-3 days)**

- SLF4J as the facade, with Logback or Log4j2 underneath.
- The Elastic stack for search and dashboards: Elasticsearch, Logstash, and Kibana.
- Structured JSON logs and correlation IDs that link the lines of one request.
- Log levels, and sampling for high-volume paths.

**Metrics (2-3 days)**

- Micrometer as the metrics facade.
- Prometheus, which scrapes and stores time-series data.
- Grafana for dashboards and alert rules.
- The key signals: throughput, latency at p50, p95, and p99, error rate, and JVM metrics.

**Distributed tracing (2-3 days)**

- Micrometer Tracing, which replaced Spring Cloud Sleuth, creates trace and span IDs and passes them between services.
- Zipkin and Jaeger store and display traces.
- OpenTelemetry is the vendor-neutral standard for traces, metrics, and logs.

**Alerting and health (2 days)**

- Alert thresholds, routing, and escalation. Alert on symptoms users feel, such as error rate and latency, and use causes for diagnosis.
- Health checks and liveness and readiness probes.
- Paging tools such as PagerDuty or Opsgenie.

---

## Phase 9: Advanced Topics and Specialization (weeks 71 onward)

Phase 9 has no fixed end date. Pick topics that match the roles you are targeting.

### Topic 21: API Design and REST Practice (ongoing)

**REST principles**

- Resource-oriented URLs, and a stateless design where each request carries what it needs.
- HTTP methods: `GET` is safe and idempotent. `PUT` and `DELETE` are idempotent. `POST` is neither by default. `PATCH` changes part of a resource.
- Status codes in the 2xx, 3xx, 4xx, and 5xx ranges, and the most useful code for each case.
- Content negotiation with the `Accept` header.

**Versioning**

- URL versioning such as `/v1/` and `/v2/` is easy to see and to route.
- Header or media-type versioning keeps URLs stable.
- Backward compatibility rules, and a published deprecation timeline.

**Pagination, filtering, and errors**

- Offset pagination is simple but slows on large tables. Cursor (seek) pagination scales better.
- Filtering, sorting, and partial responses.
- Errors in one consistent format. RFC 9457 "Problem Details" is the current standard. It replaces RFC 7807.
- Idempotency keys so that a retried `POST` does not create a duplicate.

**Other protocols**

- GraphQL for flexible queries by the client.
- gRPC for typed, binary calls between services.
- WebSockets for two-way messages over one connection.

### Topic 22: AI Integration (ongoing)

**LLM integration**

- Calling model APIs from OpenAI, Anthropic Claude, or Google Gemini. Each has its own SDK and its own request format.
- Prompt design and context management. Keep the instructions separate from user data.
- Token limits, temperature, and other sampling parameters, and what each one changes.
- Handle timeouts, rate limits, and partial failures the same way you handle any remote call.

**Retrieval-augmented generation (RAG)**

- Ingest documents, split them into chunks, and store them with metadata.
- Generate embeddings for each chunk, and search by vector similarity.
- Add the retrieved chunks to the prompt, and check that the answer cites them.

**Vector databases**

- Options include Pinecone, Weaviate, Milvus, and Chroma. Each one has different hosting and filtering features.
- Similarity metrics such as cosine similarity and dot product.
- Approximate nearest neighbour indexes trade a little recall for much faster search.

**Spring AI**

- Chat models and embedding models behind one interface.
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
