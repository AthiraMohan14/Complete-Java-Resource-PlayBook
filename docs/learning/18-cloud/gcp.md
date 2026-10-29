# Google Cloud Platform (GCP)

Google Cloud Platform groups its services into the same categories as AWS and Azure, and it is particularly known for managed Kubernetes and large-scale data analytics. Interviewers ask about GCP to check whether you can map concepts across providers and whether you know the difference between the compute options, not whether you remember every product name.

This page describes service categories and purposes. It does not cover pricing, quotas, or regional availability.

## Core concepts

### Compute
- **Compute Engine** provides virtual machines, the equivalent of EC2 or Azure Virtual Machines.
- **Cloud Run** runs stateless containers that scale with requests, including scaling to zero. You provide a container image; the platform manages the rest.
- **Google Kubernetes Engine (GKE)** is managed Kubernetes, with the control plane run by Google.
- **Cloud Functions** runs event-driven functions, similar to AWS Lambda.

Cloud Run is often the simplest route for a containerised Spring Boot service that does not need Kubernetes features. GKE suits platforms with many services and custom cluster needs.

### Data
- **Cloud SQL** is managed relational database hosting for MySQL, PostgreSQL, and SQL Server.
- **Firestore** is a managed document database with real-time sync and offline support for client apps.
- **Datastore** is the older name for a document database API. Google now presents this capability as Firestore in Datastore mode, so check current naming in the documentation before using the term in an interview.
- **Bigtable** is a wide-column NoSQL database built for very large, low-latency key-based workloads.
- **BigQuery** is a serverless data warehouse for SQL analytics over large datasets.

Cloud SQL is the managed relational default. Firestore and Bigtable are for different NoSQL access patterns. BigQuery is for analysis, not for transactional application writes.

### Storage
- **Cloud Storage (GCS)** stores objects in buckets, the equivalent of S3 or Blob Storage.
- **Persistent disks** provide block storage attached to Compute Engine VMs and GKE nodes.

### Networking
- **Cloud VPC** provides the virtual network, which is global in scope with regional subnets. This differs from AWS, where a VPC is regional.
- **Cloud Load Balancing** offers global and regional load balancers for HTTP(S) and TCP/UDP traffic.
- **Cloud CDN** caches content at Google's edge locations, typically in front of a load balancer.

### Identity
- **Cloud Identity** manages users and groups for an organisation, and integrates with Google Workspace.
- **Service accounts** are identities for applications and workloads. Grant them IAM roles, and let workloads such as Cloud Run or GKE use them without key files.

Prefer attaching a service account to a workload over downloading and shipping a key file. Downloaded keys are long-lived credentials that must be protected and rotated.

### DevOps
- **Cloud Build** runs builds and tests from configuration in a `cloudbuild.yaml` file or from a trigger on a repository.
- **Artifact Registry** stores container images and language packages such as Maven artifacts. It is the successor to Container Registry.

### Monitoring
- **Cloud Monitoring** collects metrics, builds dashboards, and raises alerts.
- **Cloud Logging** collects and searches logs from GCP resources and applications.

### Choosing a compute option

| Option | What you deploy | Who manages scaling and the host | Typical fit |
|---|---|---|---|
| Compute Engine | A virtual machine image or OS | You | Full control, legacy software |
| Cloud Run | A container image | Google | Stateless HTTP services and jobs |
| GKE | Containers into a Kubernetes cluster | Shared: you manage workloads and cluster settings | Many services, Kubernetes-native tooling |
| Cloud Functions | A function handler | Google | Small event-driven tasks |

The more the platform manages, the less you control. Pick the least-managed option that still supports what the service needs.

### Cloud Run expects a listening port
A container on Cloud Run must listen on the port given in the `PORT` environment variable. The example below uses the JDK's built-in HTTP server, so it has no framework dependency:

```java
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;

public class CloudRunHello {
    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/", exchange -> {
            byte[] body = "hello".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            try (var out = exchange.getResponseBody()) {
                out.write(body);
            }
        });
        server.start();
        System.out.println("Listening on " + port);
    }
}
```

Anything written to standard output or standard error inside the container appears in Cloud Logging, so structured log lines are easy to query.

### Choosing a data service

| Need | Service |
|---|---|
| Relational schema, transactions, familiar SQL engine | Cloud SQL |
| Document data with real-time client sync | Firestore |
| Very large, low-latency key-based reads and writes | Bigtable |
| SQL analytics over large datasets | BigQuery |
| Files and backups | Cloud Storage |

BigQuery and Bigtable are often confused. BigQuery answers analytical questions with SQL; Bigtable serves single-key lookups for applications.

### Identity and least privilege
Grant each service account only the IAM roles its workload needs, such as read access to one bucket rather than project-wide editor rights. Assign the service account to the Cloud Run service or the GKE workload. The workload then obtains credentials from the metadata service at runtime, so no key file is stored in the image.

Cloud Identity handles people: users, groups, and organisation policies. Service accounts handle software. Keep those two uses separate in reviews.

### Operating the service
- Cloud Monitoring alerts on metrics such as error rate and request latency. Set alerts on symptoms users feel, not only on CPU.
- Cloud Logging stores logs and supports queries, which helps when investigating a single failed request.
- Artifact Registry keeps image versions, so a rollback redeploys a known tag or digest.

### Releasing new revisions safely
Each deployment to Cloud Run creates a new revision. Traffic can be split between revisions by percentage, so a new version receives a small share first, and rolling back means shifting traffic back to the previous revision. This is the canary pattern from the CI/CD section, provided by the platform. Cloud Run can also deploy directly from source using buildpacks, which skips writing a Dockerfile, though an explicit image is easier to reproduce in pipelines.

### Projects and organisation
Google Cloud groups resources into projects, which are the main unit for billing, APIs, and IAM policies. Organisations and folders above projects let you apply policies across many projects at once. Keep one project per environment or per team, and grant roles at the narrowest level that works. Check the current resource hierarchy guidance before designing the structure, since recommendations evolve.

### Networking specifics
A VPC network in Google Cloud is global, and its subnets are regional. Instances in any region can communicate over the same network if firewall rules allow it. Firewall rules are defined at the VPC level and can target instances by network tag or service account, which is a useful way to express "only the application tier can reach the database".

Private Google Access lets instances without external IP addresses reach Google APIs. Check the current documentation for how it interacts with your setup, as the options have evolved.

Cloud Load Balancing comes in global and regional forms, and the choice affects how traffic reaches your backends. Plan the entry point before choosing compute, because changing it later affects DNS and certificates.

## How it works / Step by step
A containerised Spring Boot service on GCP:
1. Cloud Build builds the container image and pushes it to Artifact Registry.
2. Cloud Run deploys the image with an attached service account.
3. The service reads data from Cloud SQL, using the service account's IAM permissions for the connection.
4. Cloud Logging captures stdout from the container; Cloud Monitoring alerts on error rate and latency.
5. The public endpoint is fronted by Cloud Load Balancing and optionally Cloud CDN for cacheable content.

## Common pitfalls
- Assuming VPCs are regional. In Google Cloud the VPC network is global, with regional subnets.
- Downloading service account key files and committing them to version control.
- Using BigQuery as an operational database for frequent small writes.
- Mixing up Datastore and Firestore names in an answer without checking the current naming.
- Choosing GKE for a single stateless service that Cloud Run would handle more simply.

!!! tip "Interview tip"
    **Q: When would you pick Cloud Run over GKE?**
    Choose Cloud Run for stateless containers that you want deployed and scaled without managing a cluster. Choose GKE when you need Kubernetes-specific features, many interacting services, custom node configuration, or the same tooling you use on other clusters.

## Quick recap
- Compute Engine, Cloud Run, GKE, and Cloud Functions span VM to function-level control.
- Cloud SQL, Firestore, Bigtable, and BigQuery serve relational, document, wide-column, and analytical needs.
- Cloud Storage and persistent disks cover object and block storage.
- Service accounts give workloads identity without downloaded key files.
- Cloud Build, Artifact Registry, Cloud Monitoring, and Cloud Logging cover delivery and observability.

**See also:** [Amazon Web Services](aws.md), [Microsoft Azure](azure.md), [Multi-Cloud Considerations](multi-cloud.md), [Networking, Helm and Operators](../16-kubernetes/networking-helm-operators.md)
