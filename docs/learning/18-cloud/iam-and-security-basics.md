# AWS Identity and Access Management (IAM) Basics

IAM decides who, or what, may perform which actions on which AWS resources. Interviewers ask about it because most cloud incidents trace back to over-broad permissions, long-lived access keys, or accounts without multi-factor authentication. Know the five building blocks (users, groups, roles, policies, and MFA) and how AWS decides whether a request is allowed.

## Core concepts

### Users and the root account
Every AWS account starts with a root user, created with the account itself. The root user has unrestricted access, so use it only for initial setup and for the few tasks that require it. Protect it with MFA and do not use it for daily work.

An IAM user is an identity for one person or one application. A user can sign in to the console with a password and can hold access keys for command-line or SDK use. The guideline is one physical person equals one IAM user, so that actions can be traced to a person.

### Groups
A group is a collection of users. Groups contain users only, not other groups. A user can belong to several groups, or to none. Attach permissions to groups rather than to individual users, so that a change of job becomes a change of group membership.

### Roles
A role has no permanent password or access key. A trusted entity assumes the role and receives temporary credentials. Trusted entities include an EC2 instance (through an instance profile), a Lambda function (through its execution role), CloudFormation (through a service role), and identities in another account.

Roles are the preferred way to give AWS services permission to act for you. An application running on EC2 that reads from S3 should use an instance role, not a stored access key.

### Policies
A policy is a JSON document that lists permissions. Policies attach to identities (users, groups, and roles) or to resources, such as an S3 bucket policy.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadArchiveBucket",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::orders-archive",
        "arn:aws:s3:::orders-archive/*"
      ]
    }
  ]
}
```

| Element | Purpose |
|---|---|
| `Version` | Policy language version. Always `2012-10-17`. |
| `Id` | Optional identifier for the policy. |
| `Statement` | One or more individual statements (required). |
| `Sid` | Optional identifier for one statement. |
| `Effect` | `Allow` or `Deny`. |
| `Principal` | The account, user, or role the statement applies to (used in resource policies). |
| `Action` | The API actions allowed or denied, such as `s3:GetObject`. |
| `Resource` | The ARNs the actions apply to. |
| `Condition` | Optional rules for when the statement applies, such as a source IP range or MFA present. |

Evaluation order matters. An explicit `Deny` always wins. Without an `Allow`, the request is denied by default. The bucket ARN and the object ARN (with `/*`) are separate resources, which is a common source of "access denied" surprises.

### How people and programs reach AWS
There are three ways in:

- **Management console**: a password, protected by MFA.
- **AWS CLI**: a command-line tool authenticated with access keys.
- **AWS SDKs**: libraries used in code, also authenticated with access keys or with temporary credentials from a role.

An access key is a pair of an access key ID and a secret access key. Treat the secret like a password. Do not commit it to source control, do not paste it into tickets or chat, and rotate it on a schedule. Prefer short-lived credentials from SSO, or roles on compute, over long-lived keys.

### Multi-factor authentication (MFA)
MFA combines something you know (the password) with something you have (a device or security key). Enable it on the root user and on every user who signs in to the console. Organisations often enforce it through a policy condition, so that sensitive actions are denied unless the session used MFA.

### Auditing permissions
Two IAM tools answer different questions:

- **Credentials report** (account level): a downloadable report listing every user and the state of their password, access keys, and MFA devices. Use it to find unused or unrotated credentials.
- **Access Advisor** (user or role level): shows which services a principal was granted and when each was last used. Use it to remove permissions that are never exercised.

To see who made a change, use CloudTrail (see [AWS](aws.md)). IAM tells you what is allowed, and CloudTrail tells you what happened.

### Shared responsibility for identity
AWS secures the cloud itself: the physical facilities, the hardware, the global network, the managed service infrastructure, and the independent compliance audits. The customer secures what is done in the cloud. For IAM, that means managing users, groups, roles, and policies; enabling MFA everywhere; rotating keys; granting only the access needed; and reviewing access patterns regularly.

### Trust policies and cross-account access
A role has two policies. The **permissions policy** says what the role may do. The **trust policy** says who may assume it. A role in a production account that a CI system in another account may assume would carry a trust policy like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::111122223333:role/ci-deployer" },
      "Action": "sts:AssumeRole",
      "Condition": { "Bool": { "aws:MultiFactorAuthPresent": "true" } }
    }
  ]
}
```

The caller then calls `sts:AssumeRole` and receives temporary credentials that expire, typically after an hour unless configured otherwise. Cross-account roles avoid sharing a user's keys between accounts, and they leave a clear record in CloudTrail of which role acted.

### Conditions: adding context to a rule
A `Condition` block narrows when a statement applies. The statement below allows deleting objects only when the caller has signed in with MFA in the current session, which is a common control for destructive actions:

```json
{
  "Effect": "Allow",
  "Action": "s3:DeleteObject",
  "Resource": "arn:aws:s3:::orders-archive/*",
  "Condition": {
    "Bool": { "aws:MultiFactorAuthPresent": "true" }
  }
}
```

Other common condition keys restrict a request by source network (`aws:SourceIp`), by the time of the request, or by the tags on the target resource. Conditions are the main tool for narrowing a broad role without writing many separate policies.

### Permission boundaries and least privilege
A **permission boundary** is a managed policy that caps the maximum permissions a user or role can receive, even if an administrator attaches a broader policy later. Teams use boundaries to let developers create roles for their own services without being able to grant themselves full access. The effective permission is the overlap of the identity policy and the boundary.

Least privilege means granting only the actions and resources the work needs. In practice:

- Start from the actions the code actually calls, which you can read from CloudTrail or the Access Advisor.
- Name resources explicitly, and use prefixes for groups of resources, such as `arn:aws:s3:::orders-*`, instead of `*`.
- Separate read-only roles from write roles, and separate deploy roles from runtime roles.
- Review the policy when the code changes, not only when someone complains about an access error.

### Access key lifecycle
Long-lived access keys are the weakest link in most AWS accounts, so manage them as a lifecycle:

1. **Avoid creating them.** Use IAM Identity Center (single sign-on) for people, and roles for workloads.
2. **If you must have one**, create it for a single purpose, store it in a secrets store, and record its owner.
3. **Rotate** it on a schedule, by creating a new key, switching the consumer, then deleting the old key.
4. **Deactivate** keys that have not been used, using the credentials report to find them.
5. **Delete** keys when the owner leaves or the job is retired.

An account should have at most two access keys per user at any moment, which makes rotation possible without downtime.

### Password policy
The account password policy sets the minimum length, character rules, reuse limits, and expiry for IAM user passwords. A strong policy is a baseline, but it does not replace MFA. Passwords can still be phished, which is why MFA is the stronger control for console access.

## How it works / Step by step
When a request reaches an AWS service:

1. The request is signed with credentials, either from a user's access key or from temporary role credentials.
2. AWS identifies the principal behind the signature.
3. AWS gathers every policy that applies: identity policies, resource policies, and any permission boundary or session policy.
4. An explicit `Deny` in any of them ends the evaluation and the request is refused.
5. Otherwise, an `Allow` in at least one policy permits the request. If there is none, the request is refused by default.

## Common pitfalls
- Giving an application role `AdministratorAccess` because a narrower policy was tedious to write.
- Writing `"Resource": "*"` for actions that can target specific resources.
- Putting access keys in source code, container images, or CI variables that many people can read, instead of using roles.
- Using the root account for routine tasks, or leaving it without MFA.
- Sharing one IAM user between several people, which destroys the audit trail.
- Leaving unused access keys active after the owner has left the team.

!!! tip "Interview tip"
    **Q: How does an EC2 application read from S3 without storing keys?**
    Attach an IAM role with a least-privilege S3 policy to the instance through an instance profile. The SDK on the instance obtains temporary credentials from the instance metadata service and rotates them automatically. No secret is stored in the application or its configuration.

## Quick recap
- Users are individual identities; groups hold users and carry shared permissions.
- Roles give temporary credentials to services and trusted identities, and are preferred over access keys.
- A policy is a JSON document of Allow and Deny statements; an explicit Deny always wins, and the default is deny.
- MFA on the root user and on all console users is a baseline control.
- Use the credentials report and Access Advisor to find unused credentials and excess permissions.

**See also:** [AWS](aws.md), [Compute and Storage on AWS](compute-and-storage.md), [Secrets Management](../10-security/secrets-management.md)
