# Phases 1 to 3: Foundations, DSA and Data

This part covers the first eight weeks of the time-boxed plan, the DSA track that runs alongside them, and the build and data layer in weeks 9 to 14. Finish each phase with its deliverable before moving on.

---

## Phase 1: Foundations and Core Java (weeks 1-8)

Phase 1 has three topics. The first two take about four to seven weeks together. The third is short and can overlap with the start of Phase 2.

### Topic 1: Programming Basics (1-2 weeks)

| Area | Time | What to learn | Practice |
|------|------|---------------|----------|
| Syntax and types | 2-3 days | Variables, primitive and reference types, operators, casting | Official Java tutorials |
| Control flow | 2-3 days | `if`, `switch`, `for`, `while`, `do-while` | Small exercises on loops |
| Methods | 2-3 days | Parameters, return values, scope, recursion | Short utility methods |
| Git basics | 2-3 days | Clone, commit, push, pull, branches, merges | A hands-on Git tutorial with a practice repository |
| IDE and debugging | 1-2 days | Set up IntelliJ IDEA, Eclipse, or VS Code; use breakpoints | Step through a small program |
| Command line | 1-2 days | Navigate directories, compile with `javac`, run with `java` | Compile and run without an IDE |

**Deliverable:** five to ten console programs, such as a calculator, a number game, and a few basic algorithms.

### Topic 2: Core Java (3-5 weeks)

| Area | Duration | Key skills |
|------|----------|------------|
| Object-oriented design | 1 week | Classes, inheritance, polymorphism, encapsulation, SOLID principles |
| Collections | 1 week | ArrayList and LinkedList for lists, HashSet and TreeSet for sets, HashMap for maps; iteration; equality and hashing |
| Exceptions | 3-4 days | `try`, `catch`, `finally`, try-with-resources, checked and unchecked types, custom exceptions |
| Concurrency | 1 week | Thread lifecycle, `synchronized`, `volatile`, atomic classes, `ExecutorService` |
| JVM fundamentals | 3-4 days | Heap and stack, the garbage collector, class loading, the memory model at a high level |
| I/O and serialization | 3-4 days | Byte and character streams, `java.nio.file`, `Serializable` and its risks |

Some points that interviewers test in this topic:

- **Equality and hashing.** An object used as a `HashMap` key needs a consistent `equals` and `hashCode`. If `equals` is overridden without `hashCode`, lookups fail silently.
- **Checked and unchecked exceptions.** Checked exceptions must be declared or caught. Runtime exceptions do not have to be. Try-with-resources closes the resource even when an exception is thrown.
- **Concurrency basics.** `volatile` gives visibility, not atomicity. `synchronized` gives both. Atomic classes are the lighter option for a single counter.
- **Serialization.** Deserializing untrusted data is a security risk. Prefer explicit formats such as JSON for data that crosses a trust boundary.

**Projects:** a multi-threaded counter that is correct under contention, a file processor with error handling, and a small library system designed with classes and interfaces.

### Topic 3: Modern Java, 8 to 21 (1-2 weeks)

| Version | Features | Typical use |
|---------|----------|-------------|
| Java 8 | Lambdas, the Stream API, `Optional`, the `java.time` API | Functional style and data transformation |
| Java 9 and 10 | The module system (9); `var` for local variables (10) | Larger codebases, less repeated type text |
| Java 11 | The standard `HttpClient` | HTTP calls without a third-party library |
| Java 14 | Switch expressions (final) | Returning values from a `switch` |
| Java 16 | Records and `instanceof` pattern matching (both final) | Immutable data carriers and safer casts |
| Java 17 | Sealed classes (final) | Closed type hierarchies |
| Java 21 | Virtual threads and record patterns (both final) | High-concurrency I/O and nested deconstruction |

Points to be careful about:

- String templates were a preview feature in Java 21 and were withdrawn in Java 23. Do not present them as a finished feature.
- The LTS releases are the versions most teams run in production. Know which LTS your target team uses.
- A record is a good fit for a value with no behaviour beyond its fields. It is not a replacement for every class.

**Hands-on:** write Stream pipelines that filter, map, and reduce; convert a small class to a record and explain what changes; run a virtual-thread demo that starts many blocking tasks.

---

## Topic 4: Data Structures and Algorithms (phase 2, parallel track)

The DSA track runs in parallel with Phases 1 and 2. The source plan targets 250 to 350 problems across six areas. Work through them in order of difficulty, not by platform.

| Area | Problems | Key skills |
|------|----------|------------|
| Arrays and strings | 50-70 | Two-pointer technique, sliding-window problems, binary search, string matching such as KMP |
| Linked lists | 20-30 | Cycle detection, merging, reversal, partitioning |
| Trees and graphs | 60-80 | BFS and DFS, tree dynamic programming, lowest common ancestor, shortest paths, minimum spanning trees, topological sort |
| Stacks and queues | 30-40 | Monotonic stacks and queues, priority queues, expression evaluation |
| Dynamic programming | 50-70 | Memoization, tabulation, state compression, interval DP |
| Advanced | 30-40 | Backtracking, greedy algorithms, bit manipulation, union-find |

**Progression:**

1. **Easy (1-2 weeks):** learn the basic patterns.
2. **Medium (2-3 weeks):** apply the patterns to new problems.
3. **Hard (1-2 weeks):** optimize and compare more than one approach.

**Pace:** two to three problems a day. For each problem, write the complexity of your solution and one alternative, even if you do not implement it.

---

## Phase 3: Build Tools and Data Layer (weeks 9-14)

Phase 3 covers the build tools, relational databases, and persistence. It runs about six weeks.

### Topic 5: Build Tools (3-5 days)

**Maven**

- The POM: dependencies, plugins, and properties.
- The default lifecycle: validate, compile, test, package, install, deploy.
- Profiles for different environments.
- Dependency management, including the parent POM and the dependency management section.

**Gradle**

- Build scripts, tasks, and task dependencies.
- Plugins and the plugin ecosystem.
- Build caching and incremental builds for speed.
- The trade-off between Maven's declarative model and Gradle's programmable one.

**Practice:** build a multi-module Maven project, then recreate it in Gradle and compare the two build files.

### Topic 6: Databases and SQL (2-3 weeks)

**SQL fundamentals (3-4 days)**

- DDL: `CREATE`, `ALTER`, `DROP`.
- DML: `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
- Constraints: primary key, foreign key, unique, and not null.

**Intermediate SQL (4-5 days)**

- Joins: inner, left, right, and full outer.
- Aggregates with `GROUP BY` and `HAVING`, and the difference between `WHERE` and `HAVING`.
- Subqueries and common table expressions (CTEs).

**Advanced SQL (3-4 days)**

- Window functions: `ROW_NUMBER`, `RANK`, `LAG`, `LEAD`.
- Transactions and the ACID properties.
- Reading an execution plan and adding an index that the plan uses.

**Engine-specific notes (3-4 days)**

- **MySQL:** the InnoDB storage engine, replication, and partitioning. MySQL does not shard by itself. Sharding is done by the application or by a proxy layer.
- **PostgreSQL:** `JSONB`, full-text search, and extensions.
- **Redis:** data types, Pub/Sub, and common caching patterns.

**Practice:** 30 to 50 SQL problems across at least two engines.

### Topic 7: JDBC and Java Persistence (1-2 weeks)

**JDBC (3-4 days)**

- Connection pooling. HikariCP is the default pool in Spring Boot.
- `PreparedStatement` for parameterized queries, and `ResultSet` for reading rows.
- Batch updates and calling stored procedures with `CallableStatement`.
- Transaction boundaries: auto-commit, commit, and rollback.

**JPA and Hibernate (4-5 days)**

- Entity mapping: `@Entity`, `@Table`, `@Id`, `@GeneratedValue`.
- Relationships: `@OneToOne`, `@OneToMany`, `@ManyToMany`, and which side owns the foreign key.
- Fetch types: `LAZY` and `EAGER`. Lazy loading outside a transaction throws a `LazyInitializationException`.
- The persistence context, which is the session that tracks entity changes.

**Spring Data JPA (2-3 days)**

- The repository abstraction.
- Derived query methods such as `findBy...`, `countBy...`, and `deleteBy...`.
- Pagination and sorting with `Pageable` and `Sort`.
- Custom queries with `@Query`, and projections for returning only some columns.

**Database migrations (1-2 days)**

- Flyway: versioned SQL migrations.
- Liquibase: changelogs in XML, YAML, or JSON.

**Project:** design a small e-commerce schema, then implement the same reads and writes with JDBC and with JPA. Compare the code and the SQL each one produces.

---

## Phase 1 to 3 Deliverables

- Console programs from Phase 1 in a single repository, with a short README per program.
- A DSA log with the problem, the approach, and the complexity.
- One multi-module build, in Maven and in Gradle.
- An e-commerce schema with migrations and a JPA mapping.

**See also:** [Overview](index.md), [Phases 4 to 6](phases-4-to-6.md), [Core Java interview questions](../../interview-questions/technical/core-java-part-1.md), [Data and persistence interview questions](../../interview-questions/technical/data-and-persistence-part-1.md)
