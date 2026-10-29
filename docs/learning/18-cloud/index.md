# Cloud Platforms

Cloud platforms rent compute, storage, databases, networking, and managed services on demand. Each major provider offers similar categories under different names, so the useful skill is knowing which category solves which problem. This section maps the main services on AWS, Azure, and Google Cloud to those categories, and ends with the trade-offs of working across more than one provider.

---

## Topics

### [Amazon Web Services (AWS)](aws.md)
**EC2 - ECS - EKS - Lambda - S3 - RDS - DynamoDB - VPC - IAM - CloudWatch**
The main AWS service families for compute, storage, databases, networking, identity, monitoring, messaging, and delivery pipelines.

### [Microsoft Azure](azure.md)
**Virtual Machines - App Service - AKS - Cosmos DB - Blob Storage - Entra ID - Azure Pipelines**
The main Azure service families and how they correspond to the AWS and GCP categories.

### [Google Cloud Platform (GCP)](gcp.md)
**Compute Engine - Cloud Run - GKE - BigQuery - Cloud Storage - Cloud Build - Cloud Monitoring**
The main Google Cloud service families, with notes on naming changes such as Datastore and Firestore.

### [Multi-Cloud Considerations](multi-cloud.md)
**vendor lock-in - portability - hybrid cloud - data residency - cost comparison**
Why organisations use more than one cloud, what it costs them in complexity, and how to keep applications portable.

### More in this section

### [Compute and Storage on AWS: EC2, Lambda, and S3](compute-and-storage.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Compute and storage are where most AWS design questions start: which machine runs the code, how it is launched and reached, and where the data lives. This page goes deeper on...

### [AWS Identity and Access Management (IAM) Basics](iam-and-security-basics.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
IAM decides who, or what, may perform which actions on which AWS resources. Interviewers ask about it because most cloud incidents trace back to over-broad permissions,...

