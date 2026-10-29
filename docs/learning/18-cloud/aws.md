# Amazon Web Services (AWS)

AWS is one of the three major cloud platforms and is a common reference point in interviews. You do not need to memorise every product. You need to know each service family, the problem it solves, and how the pieces fit together: compute runs the code, storage and databases hold data, VPC and load balancers control traffic, IAM controls access, and CloudWatch shows what is happening.

This page describes service categories and purposes. It does not cover pricing, quotas, or regional availability, which change and depend on your account and region.

## Core concepts

### Compute
Compute services run application code. The options differ in how much of the server you manage.

- **EC2** (Elastic Compute Cloud) provides virtual servers. An **AMI** (Amazon Machine Image) is the template used to launch an instance.
- **Elastic Beanstalk** deploys web applications and manages the underlying EC2, load balancing, and scaling, while leaving you in control of the application.
- **ECS** (Elastic Container Service) is AWS's own container orchestrator.
- **EKS** (Elastic Kubernetes Service) is managed Kubernetes.
- **Lambda** runs functions in response to events, without you managing servers.

A simple way to choose: EC2 when you need full control of the machine, Beanstalk for a web app with little infrastructure work, ECS or EKS for containers, and Lambda for event-driven functions.

### Storage
- **S3** (Simple Storage Service) stores objects, such as files and backups, in buckets. It is accessed over HTTP and is not a file system.
- **EBS** (Elastic Block Store) provides block storage that attaches to an EC2 instance, like a disk.
- **EFS** (Elastic File System) is a shared, network file system that many instances can mount.

Object storage suits static content and data lakes. Block storage suits databases on a single instance. Shared file storage suits content that several instances must read and write.

### Databases
- **RDS** (Relational Database Service) runs managed relational engines, including MySQL, PostgreSQL, and Oracle. AWS handles provisioning, patching, and backups; you still design the schema.
- **Aurora** is an AWS-built relational engine compatible with MySQL and PostgreSQL.
- **DynamoDB** is a managed NoSQL key-value and document database designed for predictable low-latency access by key.

### Networking
- **VPC** (Virtual Private Cloud) is your isolated network, divided into subnets. Subnets can be public or private.
- **Security groups** are stateful firewalls attached to instances or network interfaces. They allow rules and track return traffic.
- **ALB** (Application Load Balancer) routes HTTP and HTTPS at layer 7, using host and path rules.
- **NLB** (Network Load Balancer) balances TCP and UDP traffic at layer 4.
- **CloudFront** is a content delivery network that caches content at edge locations.
- **Route 53** is the DNS service.

A typical web tier places load balancers in public subnets, and application and database instances in private subnets.

### Identity and access
- **IAM** (Identity and Access Management) defines users, groups, roles, and policies. Policies are JSON documents that allow or deny actions on resources. Roles are assumed by services or people, and they are preferred over long-lived access keys.
- **KMS** (Key Management Service) creates and manages encryption keys used by other services.

The principle of least privilege applies: grant only the actions a role needs.

### Monitoring and logging
- **CloudWatch** collects metrics and logs, and raises alarms on thresholds.
- **CloudTrail** records API calls made in the account, which answers who changed what and when.

Use CloudWatch to observe the system and CloudTrail to audit it.

### Messaging
- **SQS** (Simple Queue Service) is a managed message queue for decoupling producers and consumers.
- **SNS** (Simple Notification Service) is publish-subscribe, fanning one message out to many subscribers.
- **Kinesis** ingests and processes streams of records in real time.

Queues fit work distribution. Pub-sub fits notifications to several consumers. Streams fit ordered, high-volume event data that consumers replay.

### CI/CD
- **CodePipeline** orchestrates release stages.
- **CodeBuild** runs managed builds and tests.
- **CodeDeploy** deploys to EC2, ECS, Lambda, and on-premises servers, with rollback support.

These services can be replaced by external CI tools, and many teams use GitHub Actions or GitLab CI with AWS instead.

### Cost optimisation concepts
The main levers are conceptual, and the details change over time:

- **Reserved capacity** trades a commitment for a lower rate on steady workloads.
- **Spot capacity** uses spare capacity that can be reclaimed, suiting interruptible batch work.
- **Right-sizing** matches instance and database sizes to measured usage.
- Stopping or deleting unused resources, and tagging resources to see who owns them.

Check current AWS pricing documentation before making any cost decision. Set billing alerts, so that unexpected spend is noticed in days rather than at the end of the month.

### Choosing a compute option

| Option | What you deploy | Who manages the host and runtime | Typical fit |
|---|---|---|---|
| EC2 | An instance from an AMI | You | Full control, legacy or specialised software |
| Elastic Beanstalk | An application package | AWS, with you still in control of the app | Web applications without deep infrastructure work |
| ECS | Containers in tasks | AWS (the orchestrator is AWS's own) | Container services with a simpler model than Kubernetes |
| EKS | Containers in a Kubernetes cluster | Shared | Kubernetes-native tooling and portability |
| Lambda | A function handler | AWS | Event-driven, short, bursty work |

A common route is to start with the most managed option that fits the workload and move down only when a specific requirement forces it.

### Organising accounts and resources
Tags are key-value labels on resources. Consistent tags such as `owner`, `environment`, and `cost-centre` let you find what is running, who owns it, and where the spend goes. Use separate accounts for separate environments or teams, so permissions and billing boundaries match the organisation. Structure and governance tools vary, so check the current AWS guidance for your organisation's setup.

### Reliability features to know
- **Multiple Availability Zones**: AWS regions contain several isolated zones. Spreading instances and database replicas across zones protects against a single zone failing.
- **Load balancer health checks**: unhealthy targets stop receiving traffic, which pairs with auto scaling.
- **Backups and snapshots**: managed databases and block volumes support backups, so know how to restore, not only how to take them.

Describe these as concepts. Check the current documentation for specific features and their limits.

### Infrastructure as code
CloudFormation templates and Terraform both describe these resources. CloudFormation integrates natively with AWS, and Terraform works across providers. Keep templates in version control, review plans before applying, and avoid making manual console changes that drift from the code.

### Auto scaling
Auto Scaling groups keep a set of EC2 instances within a minimum and maximum size, and a desired count adjusts within those bounds. **Target tracking** policies aim to hold a metric, such as average CPU use, near a chosen value. Scaling works best with stateless instances behind a load balancer, with health checks that replace unhealthy ones. Scaling in too slowly or too quickly are both problems, so tune cooldowns against the real startup time of the application. The Spring Boot startup time from the Docker section is one input to that tuning.

### Security groups versus network ACLs
Both filter traffic, at different levels:

| Feature | Security group | Network ACL |
|---|---|---|
| Attaches to | Instances and network interfaces | Subnets |
| Rules | Allow rules only | Allow and deny rules, evaluated in order |
| State | Stateful: return traffic is allowed automatically | Stateless: return traffic needs its own rule |

Most designs rely on security groups, which reference other groups rather than IP ranges. Use network ACLs as a coarse subnet-level guard when you need explicit deny rules.

### Secrets and configuration
Store database passwords and API keys in a managed secrets service, and grant the application's role permission to read only the secrets it needs. Reference them at runtime rather than copying them into environment files. Rotate them on a schedule, and make the application reload or restart cleanly when rotation happens.

### Global infrastructure
A **Region** is a geographic area, such as a country or a cluster of cities, and most services are scoped to one Region. Choose a Region by compliance and data-residency rules, proximity to users, which services it offers, and price.

Each Region has several **Availability Zones** (AZs), which are separate data-centre groups with independent power, cooling, and networking. Zones are linked by fast, low-latency connections, so a design can survive one zone failing. AWS documents that a Region has at least three AZs. **Edge locations** sit in many more cities and serve cached content through CloudFront, which brings responses closer to users without changing the Region that holds the data.

### Managed databases: RDS and DynamoDB
**RDS** runs managed relational engines. The main choices are:

- **Single-AZ**: one instance, with no automatic failover.
- **Multi-AZ**: a standby in another zone takes over automatically if the primary fails. The standby is for availability, not for scaling reads.
- **Read replicas**: asynchronous copies that offload read traffic. They can live in the same Region or another one, and replication lag means they can serve slightly old data.

RDS takes automated daily backups with a retention period of up to 35 days, and supports manual snapshots and point-in-time restore within the backup window. Encryption at rest uses AWS KMS and in-transit uses TLS. Place the instance in a DB subnet group inside private subnets, control access with security groups, and use IAM database authentication where the engine supports it, so that no password sits in code. The trade-off is less control over the operating system and some engine settings.

**DynamoDB** is a fully managed key-value and document database. A table holds items, and each item has a partition key and an optional sort key. Access by key is fast and predictable; a scan reads the whole table and gets expensive as the table grows.

- **Capacity**: on-demand mode bills per request and suits unpredictable traffic. Provisioned mode bills for reserved read and write capacity units. One read capacity unit reads up to 4 KB strongly consistent, or two eventually consistent reads per second. One write capacity unit writes up to 1 KB per second.
- **Queries and scans**: use `Query` with the partition key, optionally narrowed by a sort-key condition. Use `Scan` only for rare full-table jobs.
- **Global tables** replicate a table across Regions, so you can read and write locally, with eventual consistency between Regions.
- **TTL** deletes items after a time stored as a Unix epoch timestamp in a chosen attribute. Deletion happens in the background and can lag, so filter expired items in queries if it matters.

```java
import java.time.Instant;
import java.util.Map;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.PutItemRequest;
import software.amazon.awssdk.services.dynamodb.model.QueryRequest;

public class SessionStore {

    public static void main(String[] args) {
        try (DynamoDbClient ddb = DynamoDbClient.create()) {
            long expiresAt = Instant.now().plusSeconds(86_400).getEpochSecond();
            ddb.putItem(PutItemRequest.builder()
                .tableName("sessions")
                .item(Map.of(
                    "userId", AttributeValue.fromS("12345"),
                    "sessionId", AttributeValue.fromS("abc"),
                    "expiresAt", AttributeValue.fromN(String.valueOf(expiresAt))))
                .build());

            ddb.query(QueryRequest.builder()
                .tableName("sessions")
                .keyConditionExpression("userId = :uid")
                .expressionAttributeValues(Map.of(":uid", AttributeValue.fromS("12345")))
                .build());
        }
    }
}
```

### VPC layout
A **VPC** (Virtual Private Cloud) is your isolated network inside a Region. You give it an IP range in CIDR notation, such as `10.0.0.0/16`, and divide that range into subnets. Each subnet lives in one AZ.

- A **public subnet** has a route to an **internet gateway**, so resources with public addresses can be reached from outside.
- A **private subnet** has no direct route to the internet. Its outbound traffic goes through a **NAT gateway** in a public subnet, which allows connections out but not unsolicited connections in. The NAT gateway needs an Elastic IP address.
- A **route table** decides where each subnet's traffic goes. The `local` route keeps traffic inside the VPC, a `0.0.0.0/0` route to the internet gateway serves public subnets, and a route to a VPN or Transit Gateway reaches an on-premises network.
- **VPC peering** connects two VPCs privately. The CIDR ranges must not overlap, and peering is not transitive: if A peers with B and B peers with C, A cannot reach C through B.

Example route table for a public subnet:

```
Destination     Target
10.0.0.0/16     local
0.0.0.0/0       igw-<id>
```

Security groups and network ACLs both filter traffic, as described earlier in this page.

### Edge and supporting services
- **CloudFront** is a CDN that caches content at edge locations. Its origins include S3 buckets and load balancers, and AWS Shield Standard protection is included.
- **ElastiCache** is a managed in-memory service running Redis or Memcached. It reduces load on the database and suits sessions, leaderboards, and short-lived data. See [Redis Advanced Patterns](../12-caching-performance/redis-advanced-patterns.md) for the Redis side.
- **AWS X-Ray** traces requests across services, which shows where latency comes from in a distributed call chain.
- **Auto Scaling** adds and removes instances against a metric, and pairs with load balancer health checks, as described in the auto scaling section above.

## How it works / Step by step
A typical three-tier application on AWS:
1. A Route 53 record points the domain to an ALB.
2. The ALB, in public subnets, forwards requests to application instances or containers in private subnets.
3. The application reads and writes to RDS in private subnets, and stores files in S3.
4. The application's IAM role grants it only the permissions it needs, with no stored keys.
5. CloudWatch collects logs and metrics; CloudTrail records the API activity.

## Common pitfalls
- Opening security groups to all addresses for convenience, such as port 22 to the world.
- Using long-lived access keys in code or pipelines instead of roles.
- Confusing S3 object storage with a mountable file system.
- Putting databases in public subnets.
- Leaving resources running after a test, which makes the bill grow silently.
- Choosing Lambda for long-running, steady workloads that suit containers better.

!!! tip "Interview tip"
    **Q: How would you deploy a web app with a database on AWS?**
    Describe the layers: a load balancer in public subnets, application compute in private subnets, the database in private subnets with restricted security groups, secrets managed by a secrets service or IAM roles, and CloudWatch for monitoring. Justify the compute choice: EC2 for control, ECS or EKS for containers, Lambda for events.

## Quick recap
- Compute options range from EC2 (full control) to Lambda (no servers); containers run on ECS or EKS.
- S3 is object storage, EBS is block storage, EFS is shared file storage.
- RDS and DynamoDB cover managed relational and key-value workloads.
- VPC, security groups, and load balancers shape network access; IAM roles grant identity.
- CloudWatch observes; CloudTrail audits.

**See also:** [Microsoft Azure](azure.md), [Google Cloud Platform](gcp.md), [Multi-Cloud Considerations](multi-cloud.md), [Continuous Deployment and IaC](../17-cicd/continuous-deployment-iac.md)
