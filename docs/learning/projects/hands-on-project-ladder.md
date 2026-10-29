# Hands-On Project Ladder

Build these in order. Each small project reinforces the topics before it, and the capstone brings them together into a backend core. You do not need to finish the ladder before starting the large projects, but skipping levels usually shows up later as gaps in exceptions, concurrency, or design.

## How to use the ladder

- Finish each project with a README in your own words (you may keep it in the repository, not in this playbook), tests for the core rules, and a short list of what you would change.
- Commit in small steps so the history shows the design evolving.
- Time-box each project. If one takes much longer than expected, note what was hard and move on or revisit it.

## Beginner

### CLI banking system
- **Build:** accounts with deposit, withdrawal, and transfer; a menu-driven command-line interface; balances saved to a file and reloaded on start.
- **Milestones:** model the account class with validation; add exceptions for insufficient funds and invalid amounts; add file storage; add tests for transfers.
- **Skills practised:** OOP (encapsulation, class design), exceptions (checked and unchecked, custom types), file storage.

### String utility toolkit
- **Build:** a library with functions for reversing strings, counting characters, checking palindromes, and encoding and decoding text (UTF-8 and Base64).
- **Milestones:** write each function with unit tests for edge cases (empty input, null, surrogate pairs); document each function's contract.
- **Skills practised:** strings and `StringBuilder`, character encodings, test design, handling null.

### Array analytics tool
- **Build:** read a list of numbers from a file or arguments and print the mean, median, mode, minimum, maximum, and standard deviation.
- **Milestones:** implement with arrays and loops first; then compare results with a library call in tests; handle empty input and integer overflow.
- **Skills practised:** arrays, loops, basic statistics, numeric types and their limits.

## Intermediate

### Employee management system
- **Build:** a console or small web app to add, search, update, and remove employees, with reports by department and salary band.
- **Milestones:** choose collections for each query; add search with `Optional` returns; write reports with streams; separate the data layer from the console.
- **Skills practised:** collections (List, Map, Set), streams and lambdas, `Optional`, layering.

### File-based task manager
- **Build:** tasks with due dates, priorities, and status, saved to disk in a format you can read back.
- **Milestones:** start with plain text, then move to serialisation or JSON; handle corrupted files; add a backup on each save.
- **Skills practised:** I/O streams and `Files`, serialisation trade-offs, data versioning.

### Multithreaded file downloader
- **Build:** download several files in parallel, report progress, support cancellation, and resume a partial download.
- **Milestones:** single download first; then an executor with a fixed pool; then progress reporting; then cancellation with interruption; then resume using range requests.
- **Skills practised:** threads, executors, futures, I/O, cancellation and interruption.

## Advanced

### In-memory order processing engine
- **Build:** accept orders from many producers, match or fill them against inventory, and report results, safely under concurrent access.
- **Milestones:** define the order model; add a single-threaded version with tests; add concurrency with locks or concurrent collections; measure throughput before and after.
- **Skills practised:** concurrency (locks, atomic types, concurrent collections), streams for batch processing, avoiding deadlock by lock ordering.

### Generic cache framework
- **Build:** a cache with `get` and `put`, size limits, and pluggable eviction policies (least recently used first, then one more).
- **Milestones:** generic types with bounded wildcards; an LRU based on a linked hash map or a hand-built list; thread safety; expiry on access; benchmarks.
- **Skills practised:** generics, maps, eviction policies, interfaces for pluggable strategies, testing with time control.

### Producer-consumer messaging system
- **Build:** several producers publish messages to an in-process channel, consumers process them, and the system applies back pressure when consumers fall behind.
- **Milestones:** implement with a blocking queue; add graceful shutdown with a poison pill or interrupts; add metrics for queue depth; test with more producers than consumers.
- **Skills practised:** blocking queues, thread coordination, back pressure, graceful shutdown.

## Capstone

### Mini Java backend core
- **Build:** a small backend with a layered architecture: HTTP endpoints, DTOs, services, a data access layer, and consistent exception handling. Include a concurrent job that processes queued work, and a streams-based reporting endpoint.
- **Milestones:** domain model and service layer with tests; DTO mapping and validation at the boundary; a global error handler that returns Problem Details; a background worker with bounded concurrency; a short performance note on JVM settings and hotspots you measured.
- **Skills practised:** layered architecture, DTOs, services, exception handling, streams, concurrency, JVM performance notes (see [API design](../../learning/21-api-design/pagination-errors-idempotency.md) for the error format).

## Level check

Before moving on, you should be able to explain:

| Level | You can explain |
|---|---|
| Beginner | Why a field should be private, when a checked exception is right, how a string is stored |
| Intermediate | Why a stream pipeline is lazy, how `HashMap` resizes, when to use a blocking queue |
| Advanced | How a deadlock forms, why a cache needs thread safety, what back pressure achieves |
| Capstone | Where each layer's responsibility ends, and how you measured one performance change |

**See also:** [Projects overview](index.md), [E-Commerce Platform](ecommerce-platform.md), [Portfolio Requirements](portfolio-requirements.md)
