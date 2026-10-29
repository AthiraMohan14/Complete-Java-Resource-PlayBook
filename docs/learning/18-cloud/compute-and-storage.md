# Compute and Storage on AWS: EC2, Lambda, and S3

Compute and storage are where most AWS design questions start: which machine runs the code, how it is launched and reached, and where the data lives. This page goes deeper on three services: EC2 for virtual servers, Lambda for event-driven functions, and S3 for object storage. The overview of every service family is in [AWS](aws.md).

## Core concepts

### EC2 virtual servers
Amazon EC2 (Elastic Compute Cloud) rents virtual servers, called instances, with chosen amounts of CPU, memory, storage, and networking. An instance starts from an **AMI** (Amazon Machine Image), which holds the operating system, installed software, and default configuration. You can use an AWS-provided AMI, a community AMI, or one you built yourself, for example with your application already installed.

Storage attached to an instance comes in two kinds. **EBS** (Elastic Block Store) volumes are network-attached disks that persist after a stop. **Instance store** is physical disk on the host, fast but lost when the instance stops or fails. Keep data that must survive on EBS or in S3, not on instance store.

### Instance families
Instance types group into families by what they optimise for. The family letter tells you the purpose, and a `g` suffix (such as `m7g`) marks Arm-based AWS Graviton processors.

| Family | Optimised for | Typical use |
|---|---|---|
| T | Burstable CPU with a baseline and accumulated credits | Small web servers, dev and test |
| M | Balanced CPU and memory | General application servers, mid-size databases |
| C | High CPU per unit of cost | Batch processing, CPU-heavy services, scientific work |
| R, X, Z | Large memory | In-memory databases, caches, analytics |
| I, D, H | High local storage throughput | Data warehouses, databases on local disks |
| P, G, Inf, Trn | Hardware accelerators (GPUs, Inferentia, Trainium) | Machine learning training and inference, graphics |
| Hpc | Tightly coupled high-performance computing | Simulations, large numerical models |

Choose from the workload: its CPU, memory, storage, and network needs, its performance target, its cost limit, and whether it must scale out. Measure with a realistic load before committing.

### Purchasing options
| Option | Commitment | Good for |
|---|---|---|
| On-Demand | None; pay per second of running time | Unpredictable or short workloads |
| Savings Plans | A consistent spend per hour for one or three years | Steady usage across instance types |
| Reserved Instances | A specific configuration (type and Region) for one or three years | Steady, predictable usage of one configuration |
| Spot Instances | None; spare capacity that AWS can reclaim with a short warning | Interruptible batch, stateless workers |
| Dedicated Hosts | A physical server for your use | Software licensed per socket or core, compliance rules |
| Dedicated Instances | Single-tenant hardware, billed by the hour | Isolation without managing a whole host |
| Capacity Reservations | Reserved capacity in one Availability Zone | Guaranteeing room to launch at a known time |

Savings Plans and Reserved Instances reduce cost but reduce flexibility, so buy them for the baseline you are confident about, and use On-Demand for the rest. Check current AWS pricing before deciding.

### User data
User data is a script or set of directives passed to an instance at launch. It runs during the first boot: as root on Linux, or as administrator on Windows. Use it to install packages, write configuration, start services, or read instance metadata such as the instance ID or tags.

Design user data with these rules in mind:

- **Never put secrets in it.** User data is readable through the instance metadata service and the console. Fetch credentials from Secrets Manager or Parameter Store at runtime, using the instance role.
- **Make it idempotent.** A script that might run twice should not break on the second run.
- **Log and check errors.** On Linux, cloud-init writes its logs under `/var/log`. Read them first when an instance is misconfigured.
- **Respect the size limit.** Raw user data is limited to 16 KB. For larger setups, use a configuration management tool or bake the software into the AMI.

### Security groups for EC2
A security group is a stateful virtual firewall attached to instances or network interfaces. It holds allow rules for inbound and outbound traffic. Each rule names a protocol, a port or port range, and a source (for inbound) or destination (for outbound), given as an IP range, a CIDR block, or another security group.

Important behaviours:

- A new custom group allows no inbound traffic and allows all outbound traffic. Responses to allowed inbound requests are permitted automatically because the group is stateful.
- Security groups are region- and VPC-scoped, and one group can attach to many instances.
- A timeout usually means a security group blocks the traffic. A "connection refused" usually means the application is not listening, which is a different problem.
- Keep a separate group for administrative access, and avoid leaving the default group in use for active resources.

Good practice is to scope each rule to the smallest source that works. Referencing another security group, such as "the web tier group", is safer than opening a port to `0.0.0.0/0`. Avoid large port ranges, and review and delete rules and groups that no longer serve a purpose.

Ports worth knowing for interviews:

| Port | Protocol | Purpose |
|---|---|---|
| 21 | FTP | File transfer (unencrypted; prefer SFTP or FTPS) |
| 22 | SSH | Encrypted remote shell |
| 23 | Telnet | Old remote shell with no encryption; avoid |
| 25 | SMTP | Mail transfer between servers |
| 53 | DNS | Name resolution |
| 80 | HTTP | Unencrypted web traffic |
| 443 | HTTPS | Encrypted web traffic |

### Connecting to an instance
There are four common ways to get a shell on an instance:

1. **SSH with a key pair.** Simple and widely supported. You manage the private key, and SSH gives you no built-in audit of sessions, so the access trail is weaker.
2. **EC2 Instance Connect.** AWS pushes a short-lived public key to the instance, then you connect with SSH or from the console. Key management is simpler, and the key is no longer a long-term secret.
3. **Systems Manager Session Manager.** Needs the SSM Agent on the instance and suitable IAM permissions. No inbound port is opened and no key is needed, and sessions can be logged. It does not provide direct file transfer, and some port-forwarding and SSH-over-SSM traffic is not logged the same way, so check the current documentation.
4. **EC2 Serial Console.** A low-level console for boot and network troubleshooting, reached from the EC2 console. It has connection limits, so use it for recovery, not as a daily method.

Prefer Session Manager for routine access because it needs no open inbound ports.

### Lambda functions
AWS Lambda runs functions without you provisioning or managing servers. You upload code, choose a runtime and memory size, and Lambda runs it in response to events. Typical triggers are S3 uploads, DynamoDB streams, API Gateway requests, SQS messages, Kinesis records, EventBridge schedules, and SNS notifications.

Key properties:

- **Scaling** is automatic: Lambda runs as many concurrent instances of the function as the event rate needs, subject to account concurrency limits.
- **Billing** is by request count and by compute duration, measured in 1 ms increments, with the memory size as a factor.
- **Timeouts**: the default is 3 seconds and the maximum is 15 minutes. A workload that runs longer than that does not fit Lambda.
- **Cold starts** happen when a new execution environment initialises. Keep dependencies small, avoid heavy framework start-up where possible, and consider provisioned concurrency for latency-sensitive paths. Java cold starts are longer than Node.js or Python, so measure them.
- **VPC attachment** lets a function reach private resources such as RDS, but it adds start-up time. Attach only when the function needs it.

A minimal Java handler, which needs the `aws-lambda-java-core` library on the classpath:

```java
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import java.util.Map;

public class OrderEventHandler implements RequestHandler<Map<String, Object>, String> {

    @Override
    public String handleRequest(Map<String, Object> event, Context context) {
        context.getLogger().log("Request " + context.getAwsRequestId() + " received");
        Object orderId = event.getOrDefault("orderId", "unknown");
        return "processed " + orderId;
    }
}
```

Keep the handler thin. Put business logic in plain classes that you can unit test without Lambda. Store secrets in Secrets Manager or Parameter Store, not in environment variables, where they are visible to anyone who can read the function configuration.

### S3 object storage
S3 (Simple Storage Service) stores objects, which are files plus metadata, inside buckets. Bucket names are globally unique, and each bucket lives in one Region. An object is identified by its key, which is the full path string. S3 is not a file system: there are no real directories, and a "folder" is only a shared prefix in the key.

Features to know:

- **Versioning** keeps earlier versions of an object, which protects against accidental overwrites and deletes.
- **Lifecycle rules** move objects to cheaper classes or delete them after a set age.
- **Replication** copies objects to another bucket, in the same or another Region, for resilience or compliance.

Storage classes trade cost against retrieval speed:

| Class | Relative cost | Retrieval | Use |
|---|---|---|---|
| S3 Standard | Highest storage cost | Immediate | Frequently accessed data |
| S3 Intelligent-Tiering | Varies | Immediate | Access patterns you cannot predict |
| S3 Standard-IA | Lower storage cost | Immediate, with a retrieval fee | Infrequently accessed data |
| S3 Glacier classes | Low | Minutes to hours | Archives and backups |
| S3 Glacier Deep Archive | Lowest | Hours (typically 12 or more) | Long-term retention |

### Access control and encryption
- **Block Public Access** is on by default for new buckets. Keep it on unless a bucket truly must serve the public, such as a static site behind a CDN.
- **Bucket policies** grant access to principals, and **IAM policies** grant access to roles and users. Use them rather than per-object ACLs, which AWS now disables by default on new buckets.
- **Pre-signed URLs** grant temporary access to a single private object, valid for a set time.
- Objects are encrypted at rest. S3 applies server-side encryption by default; you can choose SSE-KMS with a customer-managed key for audit and key control. Requests should use HTTPS, which can be enforced in the bucket policy.
- **MFA Delete** can require MFA to permanently delete object versions or change versioning.

A short Java example with the AWS SDK for Java v2 (the `s3` module):

```java
import java.net.URL;
import java.nio.file.Path;
import java.time.Duration;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;

public class ArchiveClient {

    public static void main(String[] args) {
        try (S3Client s3 = S3Client.create()) {
            s3.putObject(
                PutObjectRequest.builder().bucket("orders-archive").key("2024/report.csv").build(),
                Path.of("report.csv"));

            s3.getObject(
                GetObjectRequest.builder().bucket("orders-archive").key("2024/report.csv").build(),
                Path.of("downloaded.csv"));
        }

        try (S3Presigner presigner = S3Presigner.create()) {
            GetObjectPresignRequest request = GetObjectPresignRequest.builder()
                .signatureDuration(Duration.ofHours(1))
                .getObjectRequest(GetObjectRequest.builder()
                    .bucket("orders-archive").key("2024/report.csv").build())
                .build();
            URL url = presigner.presignGetObject(request).url();
            System.out.println("Temporary link: " + url);
        }
    }
}
```

## How it works / Step by step
A typical request that uses these services:

1. An API Gateway route invokes a Lambda function.
2. The function's execution role lets it read a secret and write one object to S3.
3. The function stores the upload in a bucket with versioning and Block Public Access enabled.
4. A lifecycle rule later moves the object to an archive class.
5. CloudWatch Logs captures the function's output for troubleshooting.

## Common pitfalls
- Expecting EC2 instance store to keep data after a stop or host failure.
- Putting passwords into user data or Lambda environment variables.
- Opening port 22 or 3389 to `0.0.0.0/0` for convenience.
- Picking a large EC2 family, or On-Demand, for a steady baseline that a Savings Plan would cover at lower cost.
- Choosing Lambda for a job that runs longer than the 15-minute limit, or for steady high-throughput work that a container runs more cheaply.
- Treating S3 prefixes as directories, then expecting a rename of a "folder" to be cheap. It copies and deletes every object.
- Publishing a bucket to the internet by turning off Block Public Access without a reason.
- Keeping the only backup in the same Region as the data. A Region-level outage then takes both copies. Replicate backups to another Region if the recovery target requires it.

!!! tip "Interview tip"
    **Q: When would you choose EC2, Lambda, or containers for a service?**
    EC2 when you need full control of the operating system, specialised software, or steady capacity. Containers (ECS or EKS) when you have several services that should be packaged and scaled the same way. Lambda for event-driven, short-running work with spiky traffic and no server to manage. Support the answer with the cost and timeout trade-offs.

## Quick recap
- An EC2 instance starts from an AMI; instance families are chosen by workload, and purchasing options trade commitment for price.
- User data runs once at first boot and must never carry secrets.
- Security groups are stateful instance-level firewalls; a timeout points to the network, a refusal points to the application.
- Lambda scales automatically with a 15-minute maximum runtime; keep handlers thin and watch cold starts.
- S3 stores objects in buckets; storage classes trade cost for retrieval speed, and Block Public Access and IAM policies control access.

**See also:** [AWS](aws.md), [IAM and Security Basics](iam-and-security-basics.md), [Multi-Cloud Considerations](multi-cloud.md)
