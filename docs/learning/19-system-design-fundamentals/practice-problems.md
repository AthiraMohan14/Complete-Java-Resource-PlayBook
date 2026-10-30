# Practice Problems

Practice problems train the habit of structuring an open-ended design. The eight common problems below cover different parts of the topics in this section: key generation, real-time messaging, global-scale feeds, concurrency control, and more. This page gives a general approach and then worked outlines for nine of them: a URL shortener, a chat system, a hotel booking system, a rate limiter, a news feed, a payment system, a notification service, a video platform, and a ride-sharing system. The last four are shorter outlines that name the main decisions.

## Core concepts

### A repeatable approach
A 45-minute design interview rewards structure more than detail. Use this sequence:

1. **Requirements**: separate functional requirements (what it does) from non-functional ones (scale, latency, availability, consistency). Ask about the read-to-write ratio.
2. **Estimates**: rough numbers for users, requests per second, storage, and bandwidth. Label them as assumptions. Do not present them as facts.
3. **API and data model**: the main endpoints or operations, and the core entities with their keys.
4. **High-level design**: the components and the path of a main request.
5. **Deep dive**: pick the hardest part, such as key generation, ordering, or concurrency, and go into detail.
6. **Trade-offs**: state what you chose, what you gave up, and what would change at higher scale.

### The eight problems
- **URL shortener**: key generation, collision handling, redirects, analytics.
- **Chat system**: real-time messaging, user presence, message history, notifications.
- **E-commerce**: product catalogue, inventory, orders, payments, recommendations.
- **Social feed**: feed generation, caching, real-time updates, distributed tracing.
- **Hotel booking**: availability, concurrency control, reservations, payments.
- **Ride-sharing**: matching, location tracking, pricing, ratings.
- **Search engine**: crawling, indexing, ranking, distributed architecture.
- **Video streaming**: encoding, CDN, adaptive bitrate, live streaming.

The outlines below are a starting point. A good interview answer depends on the requirements you clarify.

### Pacing the interview
- Spend the first few minutes on requirements; a design built on the wrong assumptions wastes the rest of the session.
- Sketch the high-level diagram early, then move to the deep dive when the interviewer signals interest.
- Say the trade-off out loud as you make each decision, rather than saving all of them for the end.
- If you do not know a detail, state an assumption and continue. Interviewers usually value the reasoning more than the exact figure.

## Worked outline 1: URL shortener

### Requirements
- Functional: create a short URL for a long URL; redirect a short URL to the original; optional custom aliases; expiry; click analytics.
- Non-functional: redirects must be fast and highly available; short codes must not collide; the system is read-heavy, with many more redirects than creations.

### Estimates (assumptions)
Assume a stated number of new links per day and a read-to-write ratio well above one. Storage is the link record times the retention period. Key length determines capacity: a 7-character code from a 62-character alphabet (`[A-Za-z0-9]`) gives 62^7 possible keys, which is about 3.5 trillion, enough for most scenarios.

### API and data model
- `POST /links` with the long URL, optional alias and expiry, returns the short code.
- `GET /{code}` returns a 301 or 302 redirect to the original URL.
- Table `links(code PK, long_url, created_at, expires_at, owner_id)`.
- Table or stream `clicks(code, timestamp, referrer)` for analytics, written asynchronously.

### High-level components
- **Key generator**: produces unique codes. Options: a counter encoded in base 62 (simple, but the counter must be coordinated); random codes checked against the store (simple, needs collision handling); pre-generated key ranges handed to each app instance (avoids coordination on each write).
- **Application service**: validates input, creates the code, and handles redirects.
- **Key-value store** for the mapping, partitioned by code. Reads dominate, so a cache sits in front.
- **Cache** (cache-aside with a TTL) for hot codes.
- **Queue and analytics pipeline** receiving click events so redirects are not slowed by writes.
- **CDN or edge redirect** for very popular links, when the business allows caching redirects.

### Trade-offs
- Sequential counters avoid collisions but leak how many links exist and need a coordinator; random codes hide volume but need a uniqueness check.
- A 301 redirect is cached by browsers and lowers load but makes click counting unreliable; a 302 keeps counting accurate at higher load.
- Handling collisions by retrying on conflict is simple; a pre-allocated range is faster but needs careful recovery when an instance restarts.
- Storing click analytics asynchronously keeps redirects fast, at the cost of counts that lag slightly.

!!! tip "Interview tip"
    **Q: How do you prevent two users from getting the same short code?**
    Let the database's unique constraint on `code` be the final arbiter. Generate a candidate, insert, and retry on a duplicate-key error. For higher throughput, allocate disjoint ranges of a counter to each instance, so no two instances generate the same value.

## Worked outline 2: Chat system

### Requirements
- Functional: one-to-one and group messaging; message history; delivery and read status; user presence (online, offline); push notifications for offline users.
- Non-functional: messages are delivered promptly; no message is lost once acknowledged; history is durable; the design supports many concurrent connections.

### Estimates (assumptions)
Estimate concurrent connections, messages per second at peak, and average message size. The key number is concurrent connections, because it decides how many connection-holding servers you need.

### API and data model
- Persistent connections from clients, such as WebSocket, for real-time messages; REST for history retrieval.
- `messages(conversation_id, message_id, sender_id, body, created_at)` with a partition by conversation and a clustering order by time.
- `conversations` and `memberships`, plus a per-user read marker.
- A presence record per user with a short expiry, refreshed by heartbeats.

### High-level components
- **Gateway / connection servers** hold WebSocket connections and register which server holds which user.
- **Session registry** (a distributed key-value store) maps user IDs to connection servers.
- **Message service** validates messages, assigns IDs, and persists them before acknowledging the sender.
- **Message store**, partitioned by conversation for efficient history reads.
- **Fan-out service** delivers a message to each recipient's connection server, or queues it if the recipient is offline.
- **Queue** between the message service and fan-out, so bursts and retries are absorbed.
- **Push notification service** for offline users.
- **Presence service** that uses heartbeats and expiry.

### Trade-offs
- Fan-out on write (push to each recipient's inbox) makes reads fast but costs more for large groups; fan-out on read is cheaper to write but slower to read.
- Acknowledging only after persistence is safer but adds latency; acknowledging early risks loss.
- Presence with heartbeats is approximate; the design should accept brief inaccuracy.
- Ordering is easiest per conversation through a single partition, which bounds throughput for very large groups.

!!! tip "Interview tip"
    **Q: What happens if the recipient is offline when a message is sent?**
    The message is persisted first, so it is never lost. The fan-out service sees no active connection in the session registry and queues a delivery plus a push notification. When the client reconnects, it fetches history from the last message it has seen. Message IDs that increase per conversation let the client detect gaps.

## Worked outline 3: Hotel booking

I chose this problem because its central difficulty is concurrency control, which many candidates find harder than the read path.

### Requirements
- Functional: search availability by dates and location; reserve a room; pay; cancel; prevent double booking.
- Non-functional: no room is double-booked under concurrent requests; search is fast and tolerant of slightly stale availability; bookings and payments are durable.

### Estimates (assumptions)
Search volume is much higher than booking volume. The write path is small but must be correct. Availability is per room per night, which gives a manageable inventory table for each property.

### API and data model
- `GET /availability?hotel=...&checkIn=...&checkOut=...`
- `POST /reservations` with room type, dates, and a payment token; returns a reservation ID.
- `DELETE /reservations/{id}` for cancellation.
- Table `room_inventory(hotel_id, room_type, night, available_count, version)` with a unique key per hotel, room type, and night.
- Table `reservations(id, hotel_id, room_id, check_in, check_out, status, payment_ref)`.

### High-level components
- **Search service** reads from a replica or a cache of availability, accepting brief staleness.
- **Reservation service** is the write path. It is the only component that changes inventory.
- **Inventory store** on a relational database, where transactions protect the counts.
- **Payment service** integrated with an external payment provider, using idempotency keys so retries do not charge twice.
- **Saga or workflow** that coordinates reserve, pay, and confirm, with compensation (release the room) if payment fails.
- **Expiry job** that releases unpaid holds after a time limit.

### Concurrency control
- **Pessimistic locking** (`SELECT ... FOR UPDATE` on the inventory rows) is simple and correct, but holds locks while the transaction runs.
- **Optimistic locking** uses the `version` column: an update succeeds only if the version is unchanged, and the client retries on conflict. It suits low contention.
- **Conditional decrement** (`UPDATE ... SET available_count = available_count - 1 WHERE available_count > 0`) is atomic and avoids reading first.

Choose by contention level. A popular property on a sale date has high contention, so favour a short, atomic conditional update or a queue per property, not long-held locks.

### Trade-offs
- Holding inventory during checkout improves the user experience but can lock rooms for abandoned carts; a short hold with expiry balances both.
- Strong consistency on the write path with eventually consistent search means users may see a room that is just booked. The reservation step must still reject it.
- Using a saga adds complexity compared with one distributed transaction, which is usually not available across the payment provider.
- Overbooking is a deliberate business choice in some hotels; the design should make the policy explicit rather than accidental.

!!! tip "Interview tip"
    **Q: Two users book the last room at the same moment. What happens?**
    Only one conditional update can succeed, because the database serialises writes to the same row. The other request sees zero rows updated and returns "no longer available". Mention the alternative of optimistic locking with a version column, and explain when each is preferable.

## Worked outline 4: Rate limiter

### Requirements
- Functional: limit each API key to N requests per window; return a clear rejection when the limit is hit; allow different limits per route or plan.
- Non-functional: the check adds little latency; the limit is enforced across all instances; the limiter must not become a single point of failure.

### Estimates (assumptions)
Estimate requests per second across the platform and the number of distinct keys. Each key needs one small counter per window, so storage is modest. The real cost is the number of store operations per request, since every request performs at least one.

### API and data model
- No public endpoint is needed. The limiter sits in front of other endpoints.
- Rule table `rate_rules(client_plan, route, limit, window_seconds)`, cached in each instance and refreshed periodically.
- Counter keys such as `rl:{apiKey}:{route}:{windowStart}` with a TTL slightly longer than the window.
- Responses: `429 Too Many Requests` with `Retry-After`; optionally return remaining quota in headers.

### High-level components
- **Gateway filter or middleware** that identifies the caller and asks the limiter.
- **Shared counter store** (Redis) that holds counts with TTLs.
- **Rule cache** in each instance, so rule lookups do not hit the database on every request.
- **Metrics and alerts** on rejection rates per key, to catch both abuse and misconfigured limits.

### Trade-offs
- Token bucket allows bursts and is smooth in practice; a fixed window is cheaper but lets a client send twice the limit around a window boundary.
- A single Redis round trip per request adds latency. A local, in-memory limit with periodic sync is faster but less accurate across instances.
- If the store is down, failing open protects availability, while failing closed protects the backend. Pick per route, based on what the backend can absorb.
- Counting requests before authentication stops abuse early, but then unauthenticated traffic is limited by IP, which is coarser.

!!! tip "Interview tip"
    **Q: Two gateway instances check the same key at the same moment. How do you avoid letting both through?**
    Make the check-and-update a single atomic operation in the store, such as a Redis script that increments the counter and checks the limit in one step. Reading the count, deciding in the application, and then writing back is a race that lets extra requests through.

## Worked outline 5: News feed

### Requirements
- Functional: users follow other users; a user posts; the home timeline shows posts from followed accounts, newest first or ranked; the timeline pages as the user scrolls.
- Non-functional: reading the timeline is fast; a new post appears within seconds; no post is lost once accepted; very popular accounts must not overload the system.

### Estimates (assumptions)
Estimate posts per day, average follower count, and the read rate for timelines. The key number is fan-out: posts per second multiplied by the average follower count. A few accounts with millions of followers dominate that product, so averages alone mislead.

### API and data model
- `POST /posts` with content; `POST /follows/{userId}`; `GET /timeline?cursor=...`.
- Posts table keyed by post ID, which is time-ordered (see the Unique IDs notes in [High-Level Design](high-level-design.md)).
- Follow graph table `follows(follower_id, followee_id)`, indexed both ways.
- Timeline cache per user: a list or sorted set of post IDs, capped at a fixed length.

### High-level components
- **Post service** validates and stores the post, then publishes a `PostCreated` event.
- **Fan-out workers** consume events from a queue and push the post ID into each follower's timeline cache.
- **Timeline service** reads the cached list for a user, fetches post bodies in batch, and returns a cursor.
- **Follow service** updates the graph and, for a new follow, backfills recent posts.
- **Ranking step** (optional) reorders candidates by signals such as recency and engagement.

### Trade-offs
- Fan-out on write makes reads cheap, but a post by an account with ten million followers creates ten million cache writes.
- Fan-out on read makes writes cheap, but every timeline request merges many followed accounts, which is slow for heavy followers.
- A hybrid works well in practice: push posts from ordinary accounts on write, and for high-follower accounts, merge their recent posts into the timeline at read time.
- Capped timeline caches bound memory, but old posts then need a slower path, such as the post store with a cursor.

!!! tip "Interview tip"
    **Q: What happens when a celebrity with millions of followers posts?**
    Fan-out on write would enqueue millions of cache updates at once. Skip fan-out for accounts above a follower threshold, and merge their recent posts when a follower loads the timeline. Explain that this trades a slightly more expensive read for a bounded write, and that the threshold is a tunable setting.

## Worked outline 6: Payment system

### Requirements
- Functional: accept a payment for an order; report its status; refund fully or partly; reconcile the ledger with the payment provider's records.
- Non-functional: no double charges, even when a client retries; strong consistency for money movement; a full audit trail; availability for checkout, with a clear fallback when the provider is down.

### High-level components
- **Payment API** that takes an idempotency key from the client on every charge request.
- **Payment service and ledger** that records each state change (created, authorised, captured, failed, refunded) as an append-only entry.
- **Provider adapter** that calls the external gateway, with timeouts and retries limited to safe operations.
- **Outbox and event publisher** so the order service learns the outcome without a dual write.
- **Reconciliation job** that compares the ledger with the provider's daily report and flags mismatches.

### Trade-offs
- An idempotency key makes retries safe, but the server must store keys and their results for a time window.
- A database transaction cannot undo a charge at the provider, so the design uses compensating refunds and reconciliation instead of assuming rollback.
- Synchronous confirmation gives the user an answer now, but a slow provider then slows checkout; a pending state with a callback keeps checkout responsive at the cost of more states to handle.

## Worked outline 7: Notification service

### Requirements
- Functional: send notifications by email, SMS, push, and in-app channels; respect each user's preferences and quiet hours; support templates and scheduled sends; report delivery status.
- Non-functional: high throughput during bursts, such as a sale or an outage alert; at-least-once delivery with deduplication for the user; a failing channel must not block the others.

### High-level components
- **Notification API** that accepts an event or request and validates the template and recipient.
- **Preference and rules service** that decides which channels apply and when.
- **Queue per channel** so a slow SMS provider does not delay push or email.
- **Channel workers** that call each provider, with retries, backoff, and a dead-letter queue for permanent failures.
- **Status store** that records each attempt for support and analytics.

### Trade-offs
- Queues absorb bursts and isolate channels, but they add delay, so urgent alerts may need a priority queue.
- At-least-once delivery means a user can receive a duplicate, so each message needs an ID that clients or workers can deduplicate on.
- Fan-out to millions of users should use batched jobs, which trades a short delay for lower load on the providers.

## Worked outline 8: Video platform (YouTube-style)

### Requirements
- Functional: upload a video; transcode it into several resolutions; play it back with adaptive bitrate; search and browse; show views and comments.
- Non-functional: uploads can be large and slow; playback must start quickly anywhere in the world; the read path is far heavier than the write path; processing can be delayed without harming the user.

### High-level components
- **Upload service** that issues resumable upload URLs and stores raw files in object storage.
- **Processing pipeline** driven by a queue, with workers that transcode into several bitrates and generate thumbnails.
- **Metadata service** backed by a database for titles, owners, and status.
- **CDN** that serves segmented video files close to viewers.
- **View and comment counters** updated asynchronously, since exact real-time counts are rarely required.

### Trade-offs
- Transcoding everything up front wastes compute on videos nobody watches; transcoding on demand reduces cost but delays the first play.
- Caching video segments at the edge gives fast playback, but a removed or private video must be purged from the CDN.
- Approximate view counts are cheap to maintain at scale; exact counts cost more and are seldom worth it.

## Worked outline 9: Ride-sharing system (Uber-style)

### Requirements
- Functional: riders request a ride; the system matches a nearby driver; both sides see live location; fares are computed; trips are rated and paid.
- Non-functional: matching must be fast, often within seconds; driver location updates are frequent; the system must stay correct when a driver goes offline mid-trip.

### High-level components
- **Location service** that receives frequent driver position updates and keeps the latest position in memory, keyed by a geographic cell.
- **Matching service** that finds nearby available drivers and offers a trip to one of them, with a timeout before trying the next.
- **Trip service** with a state machine (requested, matched, in progress, completed, cancelled) that owns the trip record.
- **Pricing service** that estimates fares and computes the final charge from the trip data.
- **Event stream** that carries trip and location events to notifications, analytics, and payments.

### Trade-offs
- Geographic partitioning keeps matching local and fast, but a trip near a cell boundary needs a search across neighbouring cells.
- Location updates can be lossy because only the latest value matters; this favours an in-memory store over a durable write per update.
- Surge pricing balances supply and demand, but it must be explained to users and capped by policy.

## Worked outline 10: Jira-style issue tracker

### Requirements
- Functional: organisations create projects; each project has issues with fields, comments, attachments, and a history; each issue type follows a configurable workflow; users see and change issues according to project roles; users search with filters; watchers receive notifications.
- Non-functional: the issue write path must be correct and never lose an update; search may lag a few seconds; the system serves many tenants with different sizes; permission checks must be fast on every request.

### High-level components
- **Project and configuration service** that stores projects, issue types, custom fields, and workflow definitions.
- **Issue service** that writes issues in a relational database partitioned by tenant or project, and allocates per-project keys such as PROJ-123.
- **Workflow engine** that validates each transition on the server against the workflow's states and conditions.
- **Permission service** that answers view, edit, and transition checks from cached project roles.
- **Activity log** that appends every change for audit and the activity feed.
- **Search index** fed by change events, serving filtered queries.
- **Notification service** that consumes events from a queue, resolves watchers and mentions, and sends in batches.

### Trade-offs
- Search is eventually consistent, so a user who just saved an issue may need to read it from the database instead.
- Filtering search results by permission is always correct but costs work per query; precomputed visibility is faster but must be updated when roles change.
- Per-project custom fields need a flexible schema, which is harder to index than fixed columns.
- Batched notifications reduce noise on busy issues, at the cost of delay.

## Quick recap
- Structure every design: requirements, estimates, API and data model, components, deep dive, trade-offs.
- URL shortener: key generation, unique constraints, cache-heavy reads, asynchronous analytics.
- Chat system: persistent connections, a session registry, persist-before-acknowledge, fan-out with offline queues.
- Hotel booking: correctness on the write path through atomic updates or locks, with search tolerant of staleness.
- Across all three, state the trade-off you chose and what would change at higher scale.

**See also:** [Core Concepts](core-concepts.md), [High-Level Design](high-level-design.md), [Low-Level Design](low-level-design.md), [Real-World Projects](../projects/index.md)
