# Part 1: Foundations, Core Java & DSA

Phases 1 and 2 of the [Full Stack Java Developer Roadmap](index.md). Learn the language and the JVM first, then build problem-solving skill in parallel.

---

## Phase 1: Foundations & Core Java

### 1. Programming Basics & Environment (1–2 weeks)

#### Java Overview and Platform
- What Java is, its history, and its main features
- Java platform layers: JVM (runs bytecode), JRE (runtime), JDK (development kit)
- Editions: Java SE (standard), Jakarta EE (formerly Java EE, for enterprise servers), Java ME (embedded and mobile, now rare)

#### JVM Fundamentals
- JVM architecture, bytecode compilation, and the memory model
- Heap vs stack; Metaspace (replaced PermGen in Java 8)
- Garbage collectors: Serial, Parallel, CMS (removed in Java 14), G1, ZGC
- GC tuning flags and how to read GC logs
- Class loading: Bootstrap, Platform (formerly Extension, renamed in Java 9), and Application loaders; the parent-delegation model

#### Environment Setup
- Install a JDK (use a current LTS release, such as 21 or 25)
- Set `JAVA_HOME`, add the JDK `bin` folder to `PATH`
- Verify with `java -version` and `javac -version`

#### Basic Syntax
- Program structure, the `main` method, and the compile-then-run flow (`javac`, then `java`)
- Class naming conventions, case sensitivity, comments, keywords, and Unicode
- User input with `Scanner`; command-line arguments
- Reader/Writer classes
- Reading Input; Parsing Data
- Type casting: widening (automatic, safe) and narrowing (explicit, may lose data)
- Date and time basics (see `java.time` in Section 3)

#### Core Language Fundamentals
- Logic, syntax, and control flow
- Methods and functions; scope management
- Problem solving: pseudocode, tracing by hand, and systematic debugging

#### Data Types, Variables & Modifiers
- Primitive types: `byte`, `short`, `int`, `long`, `float`, `double`, `char`, `boolean`. Know each size, range, and default value.
- Non-primitive (reference) types
- Variables: local, instance, and static; their scope and lifetime
- Access modifiers: `public`, `protected`, default (package-private), `private`
- Non-access modifiers: `static`, `final`, `abstract`, `synchronized`, `transient`, `volatile`

#### Operators
- Arithmetic, relational, logical, assignment, unary, and bitwise operators
- The ternary operator
- Operator precedence and associativity

#### Control Flow
- Decisions: `if`, `if-else`, `switch` (including switch expressions)
- Loops: `for`, enhanced `for-each`, `while`, `do-while`
- Loop control: `break`, `continue`

#### Tools
- **Git and GitHub:** clone, commit, push, pull, branches, merge conflicts
- **IDEs:** IntelliJ IDEA, Eclipse, VS Code
- **Command line:** navigating folders, compiling, and running from a terminal

---

### 2. Core Java Concepts (2–3 weeks)

#### Wrapper Classes, Numbers & Arrays
- Wrapper classes (`Integer`, `Double`, and others), autoboxing and unboxing
- `Math` and number utility methods
- `Boolean` and `Character` classes; Unicode handling
- `String Class and Methods`, `StringBuilder`, and `StringBuffer`, `String Comparison`; `==` vs `equals()`
- Arrays: one- and multi-dimensional, initialisation, `final` arrays, and the `Arrays` utility class

#### Object-Oriented Programming
- **Classes and objects:** class definition, object creation, Class Attributes & Methods, constructors, `this`, instance members, variable scope, aggregation vs composition
- **Initialisation order:** static and instance initialiser blocks, constructor chaining
- **Inheritance:** `extends`, `super`, method overriding, Rules for Overriding, types of inheritance (Java supports single class inheritance, plus multiple interfaces)
- **Polymorphism:** compile-time (overloading) and runtime (overriding); static vs dynamic binding
- **Abstraction:** abstract classes and abstract methods
- **Encapsulation:** data hiding, getters and setters
- **Interfaces:** default methods, static methods, private interface methods
- **SOLID principles:** learn each letter with a Java example

#### Packages, Enums & Inner Classes
- **Packages:** built-in and user-defined; access control between packages
- **Enums:** declaration, constructors, methods, strings, `name()` and `ordinal()`
- **Inner classes:** member, static, nested, local, and anonymous classes. Diamond Operator
- **Design examples:** Singleton (private constructor plus a static instance). Java has no top-level static class; a static nested class is the closest equivalent.

#### Exceptions
- Exception hierarchy: `Throwable`, `Error`, `Exception`, `RuntimeException`
- Checked vs unchecked exceptions
- `try`, `catch`, `finally`; try-with-resources
- `throw` vs `throws`
- Custom exceptions; exception propagation; reading stack traces; chained exceptions

#### Generics
- Generic classes, generic methods, and bounded types
- Wildcards (`? extends`, `? super`) and PECS (producer extends, consumer super)
- Type erasure and its effect on runtime checks

#### Collections Framework
- **Hierarchy:** `Iterable` → `Collection` → `List`, `Set`, `Queue`; `Map` is separate
- **Lists:** `ArrayList`, `LinkedList`, `Vector` (legacy), `CopyOnWriteArrayList`
- **Sets:** `HashSet`, `LinkedHashSet`, `TreeSet`, `ConcurrentHashSet`; thread-safe sets via `ConcurrentHashMap.newKeySet()`
- **Maps:** `HashMap`, `LinkedHashMap`, `TreeMap`, `Hashtable` (legacy), `ConcurrentHashMap`, `WeakHashMap`, `IdentityHashMap`
- **Queues and deques:** `PriorityQueue`, `ArrayDeque`
- **Ordering:** `Comparable`, `Comparator`, `SortedSet`, `SortedMap`
- **Utilities:** the `Collections` class; `Iterator` vs fail-fast and fail-safe iteration

#### Multithreading &Concurrency
- Thread lifecycle and states
- Creating threads: extending `Thread` vs implementing `Runnable` (prefer `Runnable`)
- Thread Pool
- Synchronisation: `synchronized` blocks and methods, static synchronisation and block synchronization
- `volatile`: visibility, not atomicity
- `wait` and `notify` for inter-thread communication
- Deadlock: how to detect and prevent it
- Interrupts; thread priority (do not rely on it for correctness)
- Atomic classes (`AtomicInteger`, `AtomicReference`); `ThreadLocal`
- `ReentrantLock`, `Semaphore`, `CountDownLatch`, `CyclicBarrier`
- `ExecutorService`, `ThreadPoolExecutor`; `Callable` and `Future`; `CompletableFuture`

#### I/O, Files & Serialization
- **Files:** `java.io` (File, byte and character streams, buffered streams, `RandomAccessFile`) and `java.nio.file` (`Path`, `Files`)
- File handling
- RandomAccessFile
- **NIO:** channels and `ByteBuffer`
- **Readers and writers:** `BufferedReader`, `PrintWriter`
- **Serialisation:** `Serializable`, `transient`, `serialVersionUID`; why deserialising untrusted data is dangerous
- Object Serialization
- Deserialization
- File Mismatch Method

#### Networking
- Networking Basics
- `InetAddress`; `URL` and `URLConnection`
- `java.net.http.HttpClient` (Java 11+). `HttpURLConnection` is legacy.
- Socket programming; client-server communication
- Sending email with Jakarta Mail (JavaMail)

#### Date & Time
- Use `java.time`: `LocalDate`, `LocalDateTime`, `Instant`, `Duration`, `Period`, `DateTimeFormatter`
- `java.util.Date` and `Calendar` are legacy; know them, but do not use them in new code

#### Tools & Runtime Features
- Command-line arguments; **JShell** (REPL) for quick experiments
- **Javadoc** comments and the `javadoc` tool
- **Packaging:** JAR files, multi-release JARs
- **Modules:** Java Platform Module System (JPMS)
- **Performance:** JIT compiler, ZGC, Class Data Sharing(CDS) archives, JMH (microbenchmarks)
- The Nashorn JavaScript engine was removed in Java 15. Know it only as history.

---

### 3. Modern Java (8-21) Features (1-2 weeks)

#### Modern Java Features
- **Java 8:** Lambda expressions, Stream API, Method references, Optional, Date/Time API, Teeing Collectors, Default Methods, Base64 Encoding, Switch Expressions, Hidden Classes, Compact Number Formatting

**Java Generics**
- Generic Classes
- Generic Methods
- Bounded Types

**Java Lambda Expressions**
- Functional Interfaces
- Lambda Syntax
- Use Cases

**Java Stream API**
- Stream Creation
- Intermediate Operations
- Terminal Operations

**Java Optional Class**
- Null Safety
- Optional Methods

- **Java 9:** Module system, interfaces with private methods
- **Java 10:** Local variable type inference (var)
- **Java 11:** HttpClient, String methods (strip, lines, repeat, isBlank)
- **Java 14:** Records (immutable data carriers), instanceof pattern matching
- **Java 15:** Sealed classes, text blocks
- **Java 16:** Records finalized, pattern matching preview
- **Java 17:** Sealed classes finalized, pattern matching enhanced
- **Java 21:** Virtual Threads (Project Loom), Record patterns, String templates (preview)
- **Java 22–25:** Incremental Enhancements

---

## Phase 2: Data Structures & Algorithms

### 3. Core DSA: 250–350 LeetCode Problems (Parallel Track)

Work on this track alongside Phases 1, 3, and 4. Aim for 3–5 problems per week, and review every solution. Ask yourself whether you can explain the time and space complexity.

#### Arrays & Strings
- Array operations: insert, delete, search, sort
- Two pointers; sliding window
- Binary search: first or last occurrence, rotated arrays
- Prefix sums and range queries
- String manipulation; pattern matching (KMP, Rabin-Karp, Z-algorithm)
- Substrings, palindromes, anagrams, string compression

#### Linked Lists
- Singly, doubly, and circular linked lists
- Operations - Insert, delete, reverse
- Cycle detection (Floyd's algorithm); finding the middle; merging lists
- Removing duplicates; partitioning; reordering

#### Stacks & Queues
- Array-based and linked-list-based implementations and its applications
- Monotonic stacks and queues; deque operations; priority queues
- Next greater element; sliding window maximum; trapping rain water

#### Trees
- Binary trees and binary search trees (BST)
- Traversals: in-order, pre-order, post-order, level-order
- Balanced trees (AVL, red-black); B-trees; tries; segment trees
- Tree dynamic programming(DP); lowest common ancestor (LCA); path-sum problems
- Morris traversal (constant-space traversal); tree serialisation

#### Graphs
- Representations: adjacency list and adjacency matrix
- Depth-first search (DFS) and breadth-first search (BFS)
- Shortest paths: Dijkstra, Bellman-Ford, Floyd-Warshall
- Minimum spanning trees: Kruskal, Prim
- Topological sort; cycle detection; strongly connected components
- Union-Find (disjoint set union)
- Bipartite graphs; 0/1 BFS; articulation points and bridges

#### Dynamic Programming
- Overlapping subproblems and optimal substructure
- Memoisation (top-down) vs tabulation (bottom-up)
- Classic problems: Fibonacci, knapsack, longest common subsequence (LCS), longest increasing subsequence (LIS), coin change, grid paths
- Interval DP; tree DP; digit DP; bitmask (state compression) DP

#### Advanced Techniques
- Recursion: base cases, tail recursion, and when recursion depth becomes a problem(optimization)
- Backtracking: N-Queens, Sudoku, permutations
- Greedy algorithms
- Bit manipulation: XOR, AND, OR, shifts
- Hashing and collision handling; suffix arrays

---

## Next

Continue to [Part 2: Data, JDBC & Spring](part-2-data-spring.md).
