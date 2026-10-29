# Project 2: Social Media and Feed System

A social application where users publish posts, follow other users, and see a feed of recent posts from the people they follow, with live notifications. This project focuses on scale and distribution: fan-out, caching, real-time delivery, asynchronous processing, and observability across several services.

## Scope

Start with a modular monolith or two services, then split along the seams the design makes obvious. Splitting too early creates distributed problems before you have a product to protect. The feed is the hardest part, so plan it early and measure it.

## Feature list

- **User profiles:** create and edit profiles, avatars by reference, privacy settings
- **Follow and unfollow:** follow graph stored efficiently, counts maintained, rate limits on follow actions
- **Posts:** create, edit, delete, and attach media references
- **Feed generation:** a timeline of posts from followed accounts, ordered by time, with personalised ranking added later
- **Caching:** cached timelines, invalidation when a followed account posts, and cache warm-up for active users
- **Real-time notifications:** likes, comments, and new followers delivered over WebSockets, with a fallback poll for clients that cannot connect
- **Asynchronous work:** background fan-out, thumbnail generation, and notification delivery through message queues
- **Microservices:** user, feed, and notification services, each with its own data store
- **Deployment:** containers on Kubernetes with horizontal scaling based on load
- **Observability:** distributed tracing across services, correlated logs, and dashboards for feed latency

## Suggested milestones

1. **Core data model.** Users, follows, and posts. Decide the keys and indexes for "posts by author" and "follows by user".
2. **Basic feed (pull).** Build a feed by querying followed authors at read time. Measure how it behaves with a large follow count.
3. **Feed with caching (push or hybrid).** Fan out to follower timelines on write for typical accounts, and fall back to a pull for accounts with very many followers. Document the trade-off in a design note.
4. **Notifications.** Publish events for likes, comments, and follows. Deliver them through a queue to a notification service, then to connected clients over WebSockets.
5. **Service split.** Separate user, feed, and notification services with their own schemas. Communicate through events and synchronous calls with timeouts.
6. **Kubernetes deployment.** Container images, deployments, a horizontal autoscaler, and readiness and liveness probes.
7. **Tracing and observability.** Propagate trace context through HTTP and queue messages. Build a dashboard for feed latency and queue lag.
8. **Load and resilience tests.** Simulate a popular account posting, and a burst of follows. Verify that the system degrades gracefully.

## Skills practised

- **Data modelling for fan-out:** trade-offs between push, pull, and hybrid feeds
- **Caching:** cache keys, TTLs, invalidation, and stampede protection (see [system design](../../resources/full-stack-java-roadmap/part-4-design-interview-projects.md))
- **Real-time:** WebSocket connection management, heartbeats, reconnection, and multi-instance fan-out (see [alternative protocols](../../learning/21-api-design/alternative-protocols.md))
- **Messaging:** at-least-once delivery, idempotent consumers, and dead-letter handling
- **Microservices:** service boundaries, data ownership, and event contracts
- **Containers and orchestration:** Kubernetes deployments, probes, and autoscaling (see [observability](../../learning/20-observability/alerting-health-checks.md))
- **Observability:** distributed tracing and metrics for latency and lag (see [distributed tracing](../../learning/20-observability/distributed-tracing.md))

## Design notes

- Feed reads must be fast; writes can be slower. Decide which side does the work based on your read-to-write ratio.
- A celebrity account with millions of followers breaks pure fan-out on write. A hybrid design handles it.
- Make consumers idempotent: a notification sent twice is an annoyance, and a counter incremented twice is a bug.
- Use a consistent key (for example, the user ID) for partitioning related events, so ordering holds where it matters.
- Cache invalidation is the hard part. Prefer versioned or short-TTL caches over elaborate invalidation logic.

## Definition of done

- A user can follow others, post, and see a feed that updates within a short, stated delay.
- A notification appears live in a connected client and is still recorded if the client was offline.
- Traces show one post's journey from the API to the feed and notification services.
- A load-test report includes feed latency at p95 and p99 under a realistic follow distribution.
- The design note explains the fan-out choice and its failure modes.

## Common pitfalls

- Splitting into microservices before the boundaries are clear
- Pure fan-out on write for accounts with huge follower counts
- Caches with no invalidation plan, so stale feeds persist
- WebSocket servers that cannot broadcast across instances
- Retrying queue messages without idempotency, duplicating notifications
- No tracing across the queue, so asynchronous delays are invisible

!!! tip "Interview tip"
    **Q: How do you generate a feed for a user who follows thousands of accounts?**
    A: Explain the two options. Fan-out on write precomputes each follower's timeline when a post is created, which makes reads cheap but writes expensive for popular accounts. Fan-out on read merges recent posts from followed accounts at request time, which is cheap to write but costly to read. A hybrid pushes for typical accounts and pulls for celebrity accounts, then merges at read time. Name the trade-off and how you would measure it.

## Quick recap

- Decide fan-out (push, pull, or hybrid) early and document it
- Feed latency is the key metric; cache timelines and invalidate carefully
- Deliver real-time updates over WebSockets with a fallback
- Process events asynchronously with idempotent consumers
- Trace requests across services and queues

**See also:** [E-Commerce Platform](ecommerce-platform.md), [Multi-Tenant SaaS Application](saas-application.md), [Portfolio Requirements](portfolio-requirements.md)
