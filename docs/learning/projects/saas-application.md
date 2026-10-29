# Project 3: Multi-Tenant SaaS Application

A software-as-a-service product serves many customer organisations (tenants) from one platform. Each tenant's data must stay isolated, each has a subscription, and everything is exposed through a documented API and delivered automatically. This project practises the multi-tenancy, billing, API, and delivery concerns that enterprise employers ask about.

## Scope

Pick a simple domain for the business logic, such as a project tracker, a booking tool, or a small CRM. The point is the platform around it: tenancy, billing, API, tests, and delivery. Keep the domain small so these concerns get the attention.

## Feature list

- **Tenant onboarding:** sign up an organisation, create its first admin, and provision its data
- **Multi-tenant data isolation:** every row is scoped to a tenant, enforced in the data layer and tested
- **Authentication:** single sign-on for enterprise customers through an OpenID Connect provider (for example, Microsoft Entra ID), plus email login for smaller accounts
- **Subscription management and billing:** plans, seats or usage limits, upgrades and downgrades, and invoices, all in a payment provider's test mode
- **Analytics dashboard:** per-tenant usage and activity charts, with platform-wide figures for internal staff
- **API-first design:** an OpenAPI specification written first, with generated or hand-checked documentation, versioning, and rate limits per tenant
- **Audit log:** a record of who changed what, per tenant, that is queryable by administrators
- **Testing:** unit tests for domain rules, integration tests against a real database, and end-to-end tests for onboarding and billing
- **CI/CD:** build, test, scan, and deploy automatically on merge, with a staged rollout
- **Infrastructure as code:** cloud resources described in Terraform, applied from version control
- **Database migrations:** versioned, reviewed, and reversible where possible, applied automatically in each environment

## Suggested milestones

1. **Single-tenant core.** Build the domain model and a working API for one organisation first. Keep tenancy in mind in the schema.
2. **Tenancy.** Add a tenant identifier to every table and enforce it. Choose the isolation model (shared schema with a tenant column, schema per tenant, or database per tenant) and write a decision record explaining why.
3. **Isolation tests.** Write tests that try to read one tenant's data as another. These should fail the build if they ever pass.
4. **Authentication and authorisation.** Add OIDC login, tenant-aware roles, and token claims that carry the tenant.
5. **API specification.** Write the OpenAPI document, version the API, add per-tenant rate limits, and publish the documentation.
6. **Billing.** Create plans, connect to the payment provider's test mode, handle subscription webhooks idempotently, and enforce plan limits in the application.
7. **Migrations.** Set up a migration tool, a review process for schema changes, and a rule that migrations are backward-compatible during rolling deployments.
8. **Analytics.** Add a reporting model, either summary tables or a separate read store, and a dashboard that stays fast as tenants grow.
9. **CI/CD and infrastructure.** Pipeline stages for build, test, security scan, and deployment. Provision the cloud environment with Terraform, including staging and production.

## Skills practised

- **Multi-tenancy:** isolation models, tenant-scoped queries, and cross-tenant test coverage
- **Security:** OIDC, tenant-aware authorisation, and audit logging (see [API security](../../learning/21-api-design/api-security.md))
- **API design:** specification-first design, versioning, and pagination (see [REST principles and versioning](../../learning/21-api-design/rest-principles-versioning.md))
- **Billing integration:** webhooks, idempotency, plan enforcement, and test-mode data
- **Data:** migrations, indexes, and reporting queries
- **Testing:** unit, integration, and end-to-end layers with a clear pyramid
- **Delivery:** CI/CD pipelines, staged rollout, and infrastructure as code with Terraform

## Design notes

- Choose the isolation model deliberately. A shared schema is cheapest to operate but needs strict tenant filtering everywhere. A database per tenant gives stronger isolation at higher operating cost.
- Put the tenant in the token and resolve it once per request. Do not let a client choose the tenant through a parameter it can change.
- Make migrations safe for rolling deployments: add columns before code uses them, and remove them only after nothing reads them.
- Treat plan limits as product rules that are enforced on the server, not just hidden in the interface.
- Store audit events append-only, and keep them separate from the operational data they describe.

## Definition of done

- Two test tenants cannot read or change each other's data, proven by automated tests that run in CI.
- A tenant can subscribe in test mode, and a plan limit blocks an action when reached.
- The OpenAPI document is published, and a client can complete the main flow using only the documentation.
- A merge to the main branch deploys to staging automatically and to production after approval.
- The cloud environment can be recreated from the Terraform code alone.

## Common pitfalls

- Filtering by tenant in some queries but not all, leaking data across tenants
- Taking the tenant ID from a request parameter rather than the verified token
- Migrations that rename or drop columns still used by the running version
- Hard-coding plan limits in several places, so they drift apart
- Manual cloud changes that the Terraform code does not describe
- Pipelines that deploy without running the isolation tests

!!! tip "Interview tip"
    **Q: How do you make sure one tenant never sees another tenant's data?**
    A: Take the tenant from the verified token, not from client input. Enforce the tenant filter in one place, such as the data access layer or database row-level security where available, rather than in each query. Then prove it with automated tests that attempt cross-tenant reads and writes, and run them on every build.

## Quick recap

- Choose and document the tenant isolation model
- Resolve the tenant from the verified token and enforce it in one layer
- Test cross-tenant access on every build
- Enforce subscription limits on the server and handle billing webhooks idempotently
- Automate delivery with CI/CD and Terraform, and keep migrations backward-compatible

**See also:** [E-Commerce Platform](ecommerce-platform.md), [Social Feed System](social-feed-system.md), [Portfolio Requirements](portfolio-requirements.md)
