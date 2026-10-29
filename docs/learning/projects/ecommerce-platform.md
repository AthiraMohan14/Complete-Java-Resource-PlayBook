# Project 1: E-Commerce Platform

A storefront where customers browse, search, buy, and track orders, and where staff manage the catalogue and see sales figures. It exercises most of the backend stack in one place: security, data modelling, search, transactions, third-party integration, deployment, and performance. Build it after the Spring, database, and API design topics.

## Scope

Keep the first version to a single deployable Spring Boot application with a relational database, then split out pieces only if you have a reason. A good first release is a working end-to-end purchase, not every feature at once.

## Feature list

- **Authentication and authorisation:** registration and login, JWT access tokens, OAuth 2.0 sign-in with a third-party identity provider, and roles for customer and administrator
- **Product catalogue:** categories, variants, prices, stock levels, images by reference
- **Search, filtering, sorting:** keyword search, filters by category and price, sorting by price and rating, and pagination with keyset cursors
- **Shopping cart:** add, update, and remove items; persist the cart for logged-in users; recalculate totals server-side
- **Order management:** place an order from the cart, reserve stock, move through statuses (placed, paid, shipped, delivered, cancelled), and show history
- **Payments:** integration with a payment provider's sandbox; webhooks for payment results; idempotent charge requests
- **Admin dashboard:** manage products and orders; show sales totals, top products, and conversion figures
- **Deployment and monitoring:** a cloud deployment with HTTPS, logs, metrics, and health checks
- **Performance work:** query tuning, caching for catalogue reads, and load-test results

## Suggested milestones

1. **Domain and persistence.** Model products, customers, carts, and orders. Write migrations for the schema. Add repository tests against a real database.
2. **Accounts and security.** Registration, login, token issuing and validation, and role-based access. Test that customers cannot read other customers' orders.
3. **Catalogue and search.** CRUD for products, keyword search, filters, sorting, and cursor-based pagination. Index the columns used for filters.
4. **Cart and checkout.** Server-side cart, price calculation, and stock reservation with a transactional boundary. Write the order in one transaction.
5. **Payments.** Sandbox integration, webhook handling with signature checks, idempotency keys on charge requests, and a retry path for failed webhooks.
6. **Admin and analytics.** Admin endpoints and screens for products and orders, plus aggregate queries for sales. Consider a read replica or a separate reporting table.
7. **Deployment and observability.** Containerise the app, deploy to a managed cloud, add HTTPS, health checks, metrics, and tracing.
8. **Performance.** Run a load test against realistic data volumes, find the slowest endpoints, fix them, and record before and after numbers.

## Skills practised

- **Security:** JWT validation, OAuth 2.0 flows, authorisation checks on each object (see [API security](../../learning/21-api-design/api-security.md))
- **API design:** resource URLs, status codes, Problem Details errors, and idempotent payment calls (see [pagination, errors, and idempotency](../../learning/21-api-design/pagination-errors-idempotency.md))
- **Data:** schema design, indexes, transactions, and query tuning
- **Integration:** calling an external provider with timeouts, retries, and webhook verification
- **Testing:** unit tests for pricing and rules; integration tests for checkout; contract tests for the payment adapter
- **Operations:** cloud deployment, logs, metrics, and health checks (see [observability](../../learning/20-observability/index.md))
- **Performance:** load testing, caching, and query analysis

## Design notes

- Compute prices and totals on the server; never trust a total sent by the client.
- Reserve stock with a time limit so abandoned carts do not hold inventory forever.
- Keep the payment provider behind an adapter interface so tests use a fake and the sandbox is swapped without touching order logic.
- Make every webhook handler idempotent, because providers deliver events more than once.
- Do not store card data yourself. Use the provider's hosted fields or tokens.

## Definition of done

- A customer can register, search, buy with a sandbox payment, and see the order status change.
- An administrator can add a product and see the order in the dashboard.
- Access rules are tested, and an object-level authorisation test exists for orders.
- A load-test report exists with the scenario, data size, and results before and after tuning.
- The service is deployed with HTTPS, a live URL, and dashboards for latency and errors.

## Common pitfalls

- Building every feature before a single purchase works end to end
- Trusting client-side prices or stock counts
- Double charging after a timeout because the charge call was not idempotent
- Filter queries with no supporting indexes, which fail under load
- Storing secrets in the repository instead of a secrets manager

!!! tip "Interview tip"
    **Q: Walk me through what happens when a customer pays for an order.**
    A: The checkout creates the order in a pending state and reserves stock. The payment call uses an idempotency key. On success the provider sends a webhook, which the service verifies and processes idempotently, marking the order paid and releasing or confirming the reservation. If the webhook never arrives, a reconciliation job queries the provider for pending orders.

## Quick recap

- Build one working purchase flow first, then widen it
- Keep prices and stock decisions on the server
- Make payment calls and webhooks idempotent
- Prove security and performance with tests and load-test numbers
- Deploy with HTTPS, health checks, and dashboards

**See also:** [Social Feed System](social-feed-system.md), [Multi-Tenant SaaS Application](saas-application.md), [Portfolio Requirements](portfolio-requirements.md)
