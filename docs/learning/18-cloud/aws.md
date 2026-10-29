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

Check current AWS pricing documentation before making any cost decision.

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
