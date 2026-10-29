# Microsoft Azure

Azure organises its services in the same broad categories as AWS and GCP, with different names and some different boundaries. Interviewers often ask how you would run a Java application on Azure, so the useful knowledge is which Azure service fits each category, and how identity works through Microsoft Entra ID.

This page describes service categories and purposes. It does not cover pricing, quotas, or regional availability.

## Core concepts

### Compute
- **Virtual Machines** provide full control over the operating system, the same model as EC2.
- **App Service** is a platform for hosting web apps and APIs. It manages the operating system and runtime, and supports Java applications directly, which makes it a common home for Spring Boot services.
- **Container Instances** runs a container without an orchestrator, for simple or short-lived workloads.
- **AKS** (Azure Kubernetes Service) is managed Kubernetes. Azure runs the control plane, and you manage the workloads.

A rough guide: App Service for a web API without infrastructure work, AKS for a microservice platform, Virtual Machines when you need the full machine.

### Data
- **Azure SQL Database** is a managed relational database based on SQL Server.
- **Cosmos DB** is a multi-model NoSQL database with global distribution and selectable consistency levels. Its consistency options are a useful interview topic in their own right.
- **Blob Storage** stores unstructured object data such as files, backups, and logs.

### Networking
- **Virtual networks** (VNets) are the isolated network boundary, divided into subnets, the equivalent of AWS VPC.
- **Application Gateway** is a layer 7 load balancer for HTTP and HTTPS, and can include a web application firewall.
- **Azure CDN** and **Azure Front Door** provide content delivery and global HTTP routing. Check current Microsoft guidance for which of these to use, as the offerings have evolved.

Network security groups filter traffic to subnets and network interfaces, similar to AWS security groups.

### Identity
- **Microsoft Entra ID** is the cloud identity service. It was previously called Azure Active Directory (Azure AD). Applications authenticate users and services against it using OAuth 2.0 and OpenID Connect.
- **Managed identities** give an Azure resource an identity without a stored secret. A service such as App Service can call Blob Storage or Key Vault using its managed identity.

Managed identities remove the need to store credentials in configuration, which is the pattern to prefer.

```java
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.core.credential.TokenRequestContext;

public class ManagedIdentityCheck {
    public static void main(String[] args) {
        // Uses a managed identity when running in Azure, or developer credentials locally
        var credential = new DefaultAzureCredentialBuilder().build();
        var request = new TokenRequestContext().addScopes("https://management.azure.com/.default");
        System.out.println("Credential type ready: " + (credential != null) + ", scope: " + request.getScopes());
    }
}
```

This example compiles only with the Azure Identity client library on the classpath. It shows the credential chain pattern, not a full token call.

### DevOps
- **Azure DevOps** is a suite that includes repositories, work item tracking, and pipelines.
- **Azure Pipelines** runs CI and CD pipelines defined in YAML, and can deploy to App Service, AKS, and other targets.

Azure Pipelines and GitHub Actions cover similar ground, and both can deploy to Azure.

### Monitoring
- **Application Insights** collects application telemetry: requests, dependencies, exceptions, and traces. It is commonly used for Java through an agent or SDK.
- **Log Analytics** stores logs in a workspace that you query with Kusto Query Language (KQL).

### Choosing a compute option

| Option | What you deploy | Who manages the host and runtime | Typical fit |
|---|---|---|---|
| Virtual Machines | An OS and everything on it | You | Full control, legacy software |
| App Service | A web app or API package | Azure | Web APIs with little infrastructure work |
| Container Instances | A container | Azure | Simple, single-container or short-lived workloads |
| AKS | Containers into a Kubernetes cluster | Shared | Many services, Kubernetes-native tooling |

The choice mostly depends on how much operational work the team wants to own. App Service is a common first step for a Spring Boot API, and AKS becomes worth its extra operational load when a platform runs many services.

### Java developers and identity
A Java service on App Service runs with the application settings you configure in the portal or in infrastructure as code. Keep those settings free of passwords when a managed identity can do the job. The identity model has two layers:

- **Who the user is**: Entra ID authenticates people and applications and issues tokens. Spring Security's OAuth 2.0 resource server support can validate those tokens in a Spring Boot service.
- **What the workload may touch**: Azure role assignments grant a managed identity access to a resource, such as read access to one storage container.

Keep these separate in design reviews, because a valid user token does not grant access to every Azure resource.

### Storage and data choices

| Need | Service |
|---|---|
| Managed relational database with SQL Server engine | Azure SQL Database |
| Globally distributed NoSQL with selectable consistency | Cosmos DB |
| Files, backups, logs as objects | Blob Storage |

Cosmos DB's partition key choice is the decision that affects scale and cost the most, so plan it from the access patterns rather than the data shape.

### Observability workflow
Application Insights records requests, dependency calls, and exceptions, which lets you follow one slow request across services. Log Analytics holds the logs, and KQL queries answer questions such as which endpoint produced the most errors in the last hour. Dashboards and alerts on error rate and latency turn that data into action.

### Messaging and events
The roadmap lists Azure's core compute, data, and networking services. For messaging, the commonly used services are:

- **Service Bus** provides queues and topics with subscriptions, suited to reliable enterprise messaging between services, similar in role to SQS and SNS.
- **Event Hubs** ingests high volumes of streaming events, similar in role to Kinesis.
- **Event Grid** routes discrete events from sources such as storage or resource changes to handlers, similar in role to an event bus.

The distinction to explain in an interview is between a queue for work to be done, a stream for ordered event data that consumers may replay, and an event router for reacting to something that happened.

### Scaling and telemetry in a Java service
App Service and AKS both support scaling out to more instances. Scale rules usually react to a metric such as CPU or request queue length, with minimum and maximum instance counts as guardrails. Keep the application stateless so any instance can serve any request, and keep session data in a shared store if needed.

Application Insights can be attached to a Java application through an agent, without code changes, which records requests and dependency calls automatically. Add custom telemetry for business events that matter, such as a completed order, so dashboards reflect the business and not only the infrastructure.

### Configuration and environments
Use separate resource groups or subscriptions per environment, so access and cost can be separated and a mistake in one environment cannot reach another. Keep environment-specific values in application settings or a configuration store, and keep the artifact identical across environments. Infrastructure definitions in Bicep, Terraform, or another IaC tool keep the environments comparable.

### Private connectivity
Databases and storage should not be reachable from the public internet when the application does not need that. Azure offers private endpoints, which give a service a private IP address inside a virtual network. Combined with network security group rules that allow only the application's subnet, this limits exposure. Check current documentation for which services support private endpoints, since coverage changes.

### Deployment checklist for a Java service
- Use a managed identity for database and storage access, not connection-string passwords.
- Put runtime settings such as the active profile in application settings, and keep secrets in a key vault.
- Turn on Application Insights so failures and slow dependency calls are visible from day one.
- Route deployments through a pipeline (Azure Pipelines or GitHub Actions) that builds the artifact once.
- Define a rollback path, such as redeploying the previous package or using deployment slots where available.

## How it works / Step by step
A typical Spring Boot service on Azure:
1. The application runs on App Service or AKS.
2. It authenticates users against Microsoft Entra ID.
3. It reaches Azure SQL Database or Cosmos DB through a managed identity, without a stored password.
4. Application Insights records requests and failures; Log Analytics keeps the logs for querying.
5. Azure Pipelines builds the artifact and deploys it to the target environment.

## Common pitfalls
- Confusing Entra ID with on-premises Active Directory, which is a separate product, even though they can be connected.
- Storing connection strings with passwords in App Service settings when a managed identity would work.
- Using Cosmos DB without understanding its partitioning and consistency choices, which drive cost and behaviour.
- Assuming a CDN product name from an older guide is still the recommended choice.
- Deploying to AKS when App Service would meet the need, which adds operational work.

!!! tip "Interview tip"
    **Q: How does a service on Azure access a database without a password in its configuration?**
    Give the service a managed identity, grant that identity a role on the database, and have the application obtain a token at runtime through the Azure Identity library. The credential never appears in code or configuration.

## Quick recap
- Virtual Machines, App Service, Container Instances, and AKS span control versus convenience.
- Azure SQL Database, Cosmos DB, and Blob Storage cover relational, global NoSQL, and object storage.
- Microsoft Entra ID (formerly Azure AD) handles identity; managed identities avoid stored secrets.
- Application Insights and Log Analytics provide telemetry and queryable logs.
- Azure Pipelines provides YAML-based CI and CD.

**See also:** [Amazon Web Services](aws.md), [Google Cloud Platform](gcp.md), [Multi-Cloud Considerations](multi-cloud.md), [Git Workflows](../17-cicd/git-workflows.md)
