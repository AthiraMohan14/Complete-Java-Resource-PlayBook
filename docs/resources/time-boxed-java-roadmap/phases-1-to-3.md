# Phases 1 to 3: Foundations, DSA and Data

Weeks 1 to 8 of the plan are covered here, along with the DSA track that runs next to them and the build and data layer in weeks 9 to 14. Complete each phase's deliverable before you start the next one.

---

## Phase 1: Foundations and Core Java (weeks 1-8)

Phase 1 contains three topics. Topics one and two together need roughly four to seven weeks. Topic three is brief and may run alongside the opening of Phase 2.

### Topic 1: Programming Basics (1-2 weeks)

| Area | Time | What to learn | Practice |
|------|------|---------------|----------|
| Syntax and types | 2-3 days | Variables, primitive versus reference types, operators, type casting | Work through the official Java tutorials |
| Control flow | 2-3 days | `if`, `switch`, `for`, `while`, `do-while` | Short exercises that use loops |
| Methods | 2-3 days | Parameters, return values, scope, recursion | Small utility methods |
| Git basics | 2-3 days | Clone, commit, push, pull, branches, merges | A hands-on Git lesson with a practice repository |
| IDE and debugging | 1-2 days | Set up IntelliJ IDEA, Eclipse, or VS Code; use breakpoints | Step through a small program |
| Command line | 1-2 days | Move between directories, compile with `javac`, run with `java` | Compile and run a program without an IDE |

**Deliverable:** build five to ten console programs, for example a calculator, a number-guessing game, and a few simple algorithm exercises.

### Topic 2: Core Java (3-5 weeks)

| Area | Time budget | Skills covered |
|------|----------|------------|
| Object-oriented design | 1 week | Class design, inheritance, polymorphism, encapsulation, and the SOLID rules |
| Collections | 1 week | Lists with ArrayList and LinkedList, sets with HashSet and TreeSet, maps with HashMap; looping over elements; equals and hashing |
| Exceptions | 3-4 days | `try`, `catch`, and `finally` blocks, try-with-resources, checked versus unchecked types, custom exception classes |
| Concurrency | 1 week | Thread states, `synchronized`, `volatile`, atomic types, and `ExecutorService` |
| JVM fundamentals | 3-4 days | Heap versus stack, garbage collection, class loading, and a big-picture view of the memory model |
| I/O and serialization | 3-4 days | Byte and character streams, `java.nio.file`, and `Serializable` along with its hazards |

Some points that interviewers test in this topic:

- **Equality and hashing.** Keys used in a `HashMap` need consistent `equals` and `hashCode` implementations. Overriding `equals` but not `hashCode` makes lookups fail without any error.
- **Checked and unchecked exceptions.** Checked exceptions have to be declared or handled. Runtime exceptions are optional to handle. A resource opened in try-with-resources is still closed when an exception escapes.
- **Concurrency basics.** `volatile` guarantees visibility but not atomicity. `synchronized` provides both. For a single counter, atomic classes are a lighter choice.
- **Serialization.** Deserializing data from an untrusted source is a security hazard. For data that crosses a trust boundary, choose an explicit format such as JSON.

**Projects:** build a multi-threaded counter that stays correct under contention, a file processor with error handling, and a small library system modeled with classes and interfaces.

### Topic 3: Modern Java, 8 to 21 (1-2 weeks)

| Version | Features | Typical use |
|---------|----------|-------------|
| Java 8 | Lambdas, the Stream API, `Optional`, the `java.time` API | Functional style and transforming data |
| Java 9 and 10 | The module system (9); `var` for local variables (10) | Larger codebases, less repetition in type declarations |
| Java 11 | The standard `HttpClient` | Making HTTP calls with no external library |
| Java 14 | Switch expressions (final) | Yielding a value from a `switch` |
| Java 16 | Records and `instanceof` pattern matching (both final) | Immutable data holders and safer casts |
| Java 17 | Sealed classes (final) | Closed type hierarchies |
| Java 21 | Virtual threads and record patterns (both final) | Large numbers of concurrent I/O tasks and unpacking nested records |

Points to be careful about:

- String templates shipped only as a preview in Java 21 and were withdrawn in Java 23, so do not describe them as a stable feature.
- Most production teams run an LTS (long-term support) release. Find out which one your target team uses.
- Records suit values whose only job is to hold fields. They do not replace every class.

**Hands-on:** build Stream pipelines that filter, map, and reduce; turn a small class into a record and describe what changes; launch a virtual-thread demo that starts many blocking tasks.

---

## Topic 4: Data Structures and Algorithms (phase 2, parallel track)

The DSA track runs alongside Phases 1 and 2. The plan aims for 250 to 350 problems spread over six areas. Go in order of difficulty rather than by the site the problems come from.

| Area | Problems | Key skills |
|------|----------|------------|
| Arrays and strings | 50-70 | Two pointers, sliding windows, binary search, pattern matching such as KMP |
| Linked lists | 20-30 | Detecting cycles, merging, reversing, partitioning |
| Trees and graphs | 60-80 | BFS and DFS, tree DP, lowest common ancestor, shortest paths, minimum spanning trees, topological ordering |
| Stacks and queues | 30-40 | Monotonic stacks and queues, priority queues, evaluating expressions |
| Dynamic programming | 50-70 | Caching subproblem results (memoization), bottom-up tables, state compression, interval DP |
| Advanced | 30-40 | Backtracking, greedy methods, bit tricks, union-find |

**Progression:**

1. **Easy (1-2 weeks):** learn the core patterns.
2. **Medium (2-3 weeks):** use those patterns on unfamiliar problems.
3. **Hard (1-2 weeks):** tune your solutions and weigh more than one approach.

**Pace:** aim for two or three problems per day. For each one, note the complexity of your solution plus one alternative, even if you never code the alternative.

---

## Phase 3: Build Tools and Data Layer (weeks 9-14)

Phase 3 handles build tooling, relational databases, and persistence over roughly six weeks.

### Topic 5: Build Tools (3-5 days)

**Maven (POM-based)**

- The project object model (POM): dependencies, plugins, and properties.
- The standard build phases in order: validate, compile, test, package, install, and deploy.
- Profiles that switch settings per environment.
- Dependency management, including inheritance from a parent POM and its `dependencyManagement` block.

**Gradle**

- Build scripts, the tasks they define, and how tasks depend on each other.
- Plugins and the wider plugin catalog.
- Build caching and incremental builds to save time.
- Maven's declarative style compared with Gradle's scriptable style.

**Practice:** create a multi-module Maven project, rebuild the same layout in Gradle, and compare the two build files.

### Topic 6: Databases and SQL (2-3 weeks)

**Core statements (3-4 days)**

- Schema commands (DDL): `CREATE`, `ALTER`, `DROP`.
- Data commands (DML): `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
- Constraints: primary keys, foreign keys, uniqueness, and NOT NULL rules.

**Joins and grouping (4-5 days)**

- Join types: inner, left, right, and full outer.
- Aggregation via `GROUP BY` and `HAVING`, plus how `WHERE` differs from `HAVING`.
- Subqueries and CTEs (common table expressions).

**Analytics and tuning (3-4 days)**

- Window functions such as `ROW_NUMBER`, `RANK`, `LAG`, and `LEAD`.
- Transactions and what ACID guarantees.
- Reading a query plan, then adding an index the planner actually picks up.

**Engine-specific notes (3-4 days)**

- **MySQL:** InnoDB as the storage engine, replication, and partitioning. Sharding is not built into MySQL; the application or a proxy layer has to handle it.
- **PostgreSQL:** `JSONB` columns, full-text search, and extension support.
- **Redis:** its data types, Pub/Sub messaging, and typical caching approaches.

**Practice:** solve 30 to 50 SQL problems on at least two database engines.

### Topic 7: JDBC and Java Persistence (1-2 weeks)

**Raw JDBC (3-4 days)**

- Connection pooling; Spring Boot uses HikariCP by default.
- `PreparedStatement` for queries with bound parameters, and `ResultSet` for reading returned rows.
- Batched writes, and invoking stored procedures through `CallableStatement`.
- Where transactions begin and end: auto-commit mode, commit, and rollback.

**JPA and Hibernate (4-5 days)**

- Mapping entities with `@Entity`, `@Table`, `@Id`, and `@GeneratedValue`.
- Associations using `@OneToOne`, `@OneToMany`, and `@ManyToMany`, and deciding which side holds the foreign key.
- Fetch strategies `LAZY` and `EAGER`. Touching a lazy association after the transaction has closed raises `LazyInitializationException`.
- The persistence context: the unit-of-work session that watches entity state.

**Spring Data JPA (2-3 days)**

- The repository abstraction layer.
- Query methods derived from names, like `findBy...`, `countBy...`, and `deleteBy...`.
- Paging and ordering through `Pageable` and `Sort`.
- Hand-written queries via `@Query`, and projections that return only selected columns.

**Database migrations (1-2 days)**

- Flyway: SQL migrations under version numbers.
- Liquibase: changelog files written as XML, YAML, or JSON.

**Project:** model a small e-commerce schema, then build the same reads and writes twice, once with JDBC and once with JPA. Compare the code you wrote and the SQL each approach generates.

---

## Phase 1 to 3 Deliverables

- Phase 1 console programs in one repository, each with a brief README.
- A DSA log recording each problem, your approach, and its complexity.
- One multi-module project built with both Maven and Gradle.
- An e-commerce schema with migration scripts and a JPA mapping.

**See also:** [Overview](index.md), [Phases 4 to 6](phases-4-to-6.md), [Core Java interview questions](../../interview-questions/technical/core-java-part-1.md), [Data and persistence interview questions](../../interview-questions/technical/data-and-persistence-part-1.md)
