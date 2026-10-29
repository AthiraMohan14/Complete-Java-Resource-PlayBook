# Practice Problems

Practice problems train the habit of structuring an open-ended design. The eight common problems below cover different parts of the topics in this section: key generation, real-time messaging, global-scale feeds, concurrency control, and more. This page gives a general approach and then worked outlines for three of them: a URL shortener, a chat system, and a hotel booking system.

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

## Quick recap
- Structure every design: requirements, estimates, API and data model, components, deep dive, trade-offs.
- URL shortener: key generation, unique constraints, cache-heavy reads, asynchronous analytics.
- Chat system: persistent connections, a session registry, persist-before-acknowledge, fan-out with offline queues.
- Hotel booking: correctness on the write path through atomic updates or locks, with search tolerant of staleness.
- Across all three, state the trade-off you chose and what would change at higher scale.

**See also:** [Core Concepts](core-concepts.md), [High-Level Design](high-level-design.md), [Low-Level Design](low-level-design.md), [Real-World Projects](../projects/index.md)
