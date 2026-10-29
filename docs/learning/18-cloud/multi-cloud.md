# Multi-Cloud Considerations

Multi-cloud means using more than one public cloud provider, either by design or because different teams chose different providers. It can reduce dependence on one vendor and meet regulatory or customer requirements, but it adds operational complexity. Interviewers ask about it to see whether you can weigh portability against the cost of running several platforms.

## Core concepts

### Why organisations go multi-cloud
- **Resilience and leverage**: reduce dependence on a single provider's outages or pricing decisions. Full resilience across providers is hard, so be precise about what you are protecting against.
- **Best-fit services**: use a service that suits a workload better, such as a particular analytics platform.
- **Acquisitions and legacy**: inherit systems on another provider.
- **Customer or regulatory requirements**: some customers or regulators require specific hosting arrangements.
- **Hybrid cloud**: combine public cloud with on-premises systems, often for data that must stay local.

### Vendor lock-in and portability
Lock-in happens when moving away from a provider would be expensive. It usually comes from proprietary managed services, such as a specific queue, database, or serverless API, with APIs or behaviour that have no equivalent elsewhere.

Portability strategies reduce lock-in at a cost:

- **Containers and Kubernetes** give a common runtime across providers, although managed Kubernetes services differ in networking, storage, and identity integration.
- **Infrastructure as code** with Terraform describes resources with a common workflow, though each provider's resources remain different.
- **Standard protocols and databases**, such as PostgreSQL or message formats defined by open standards, are easier to move than proprietary APIs.
- **Hexagonal or ports-and-adapters design** isolates cloud-specific code behind interfaces, so the core application does not depend on one provider's SDK.

```java
import java.io.InputStream;
import java.util.Optional;

// The application depends on this port, not on any provider SDK
public interface ObjectStore {
    void put(String key, InputStream content);
    Optional<InputStream> get(String key);
}
```

Each provider gets an adapter, such as one backed by S3, one by Blob Storage, and one by Cloud Storage. The core code compiles and tests without any cloud SDK. Keep adapters thin, and accept that some features will not map cleanly.

### Cost comparison and optimisation
Comparing providers requires a like-for-like model: the same workload, the same region classes, the same commitment terms, and the cost of data transfer between providers. Pricing and discount structures change, so a comparison is only valid on the day it is made.

Hidden costs matter: data egress between clouds, duplicated tooling, training, and the engineering time spent maintaining several sets of deployment pipelines. Multi-cloud often costs more before it saves anything.

### Hybrid cloud
Hybrid cloud connects public cloud with on-premises infrastructure. Typical patterns include keeping regulated data on premises while running stateless services in the cloud, or extending an on-premises cluster into the cloud. It requires secure private connectivity, consistent identity across both sides, and a plan for how data moves.

### Data residency and compliance
Data residency rules can restrict where personal or regulated data may be stored and processed. Before choosing regions or providers, identify:

- Which data is subject to residency rules, and where it may live.
- Which compliance frameworks apply, and which providers and services are certified for them.
- Where backups, logs, and analytics copies of that data also go, since these are often forgotten.

Confirm the current certifications and regional options in each provider's compliance documentation. Do not rely on memory for these details.

### Service equivalents across providers
Most categories have a counterpart on each cloud. The names differ, and the boundaries do not always match. Use this table as a starting point, then check the feature details.

| Category | AWS | Azure | Google Cloud |
|---|---|---|---|
| Virtual machines | EC2 | Virtual Machines | Compute Engine |
| Managed web app platform | Elastic Beanstalk | App Service | App Engine (not covered in this section) |
| Serverless containers | ECS or Fargate (task model) | Container Instances, Container Apps | Cloud Run |
| Managed Kubernetes | EKS | AKS | GKE |
| Functions | Lambda | Azure Functions | Cloud Functions |
| Object storage | S3 | Blob Storage | Cloud Storage |
| Block storage | EBS | Managed disks | Persistent disks |
| Managed relational database | RDS, Aurora | Azure SQL Database | Cloud SQL |
| Wide-column or key-value NoSQL | DynamoDB | Cosmos DB | Bigtable, Firestore |
| Layer 7 load balancing | ALB | Application Gateway | Cloud Load Balancing |
| Identity and access | IAM | Entra ID, Azure RBAC | Cloud IAM, service accounts |
| Monitoring and logs | CloudWatch | Azure Monitor, Application Insights, Log Analytics | Cloud Monitoring, Cloud Logging |
| CI/CD | CodePipeline, CodeBuild | Azure Pipelines | Cloud Build |

Identity needs care in any comparison. A managed identity, a service account, and an IAM role solve the same problem with different models, so translate policies deliberately rather than copying them.

### Testing against a portable interface
Core business logic should run in tests without any cloud. The in-memory adapter below satisfies the `ObjectStore` interface from earlier, so unit tests need no cloud account:

```java
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

interface ObjectStore {
    void put(String key, InputStream content);
    Optional<InputStream> get(String key);
}

class InMemoryObjectStore implements ObjectStore {
    private final Map<String, byte[]> data = new HashMap<>();

    @Override
    public void put(String key, InputStream content) {
        try {
            data.put(key, content.readAllBytes());
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    @Override
    public Optional<InputStream> get(String key) {
        return Optional.ofNullable(data.get(key)).map(ByteArrayInputStream::new);
    }
}
```

Cloud adapters are tested separately, against emulators or a test account, so the contract is verified on each provider.

### Disaster recovery across providers
Failing over to a second provider is a recovery plan, not a free feature. It needs:

- **Recovery point objective (RPO)**: how much data loss is acceptable, which decides how often data is replicated across providers.
- **Recovery time objective (RTO)**: how long the service may be down, which decides whether the standby is cold, warm, or running.
- **Traffic switching**: DNS or a global router that moves users, with health checks that trigger it.
- **Tested runbooks**: a failover that has never been rehearsed usually fails in production.

Active-passive setups are simpler than active-active ones, which must handle writes in two places and resolve conflicts.

### Exit planning
Before adopting a provider-specific service, write down how you would replace it. For each managed dependency, note the data format, the export path, and the rough effort to move. This exercise is cheap, and it turns lock-in from a vague worry into a list of decisions the team can accept or avoid.

### Operational overhead
Every extra provider multiplies work: separate identity federation, network connectivity between clouds, separate logging and metrics, and different skills in the team. Consolidate observability into one tool that can read from each provider, and share pipeline templates so each service does not reinvent its deployment.

## How it works / Step by step
A pragmatic multi-cloud decision process:
1. State the business reason: resilience, a specific service, a customer requirement, or an acquisition.
2. List the workloads and the data classes they handle, including residency constraints.
3. Choose a common runtime and deployment model, usually containers with infrastructure as code.
4. Isolate provider-specific code behind interfaces, and keep the core application portable.
5. Set up one pipeline pattern that deploys to each provider, with monitoring that works across all of them.
6. Review the cost and operational overhead every year, and remove a provider if its reason has gone.

## Common pitfalls
- Going multi-cloud without a clear reason, which doubles operational work.
- Assuming a multi-cloud setup gives automatic disaster recovery. Failover needs tested runbooks and data replication.
- Ignoring data egress and cross-provider network costs in comparisons.
- Building a portability layer so generic that it hides useful features and performs poorly.
- Using a different tool per cloud for the same job, which fragments skills and monitoring.
- Forgetting that backups, logs, and analytics copies are also subject to residency rules.

!!! tip "Interview tip"
    **Q: Would you use multiple clouds for this system?**
    Ask first what problem it solves. If the answer is resilience, explain what would actually fail over, how data is replicated, and how it is tested. If the answer is a specific service, consider whether that service justifies a second platform's overhead. Portability through containers, IaC, and ports-and-adapters design is worth having even when you stay on one provider.

## Quick recap
- Multi-cloud is chosen for resilience, best-fit services, requirements, or hybrid needs, and costs more operational effort.
- Lock-in comes from proprietary managed services; containers, IaC, and standard data formats reduce it.
- Ports-and-adapters design keeps provider SDKs out of core business logic.
- Compare costs like for like, including data transfer and maintenance overhead.
- Check data residency and compliance requirements for every copy of the data.

**See also:** [Amazon Web Services](aws.md), [Microsoft Azure](azure.md), [Google Cloud Platform](gcp.md), [Continuous Deployment and IaC](../17-cicd/continuous-deployment-iac.md)
