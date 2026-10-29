# Advanced Java: Concurrency, JVM Memory, and GC (Part 2 of 2)

Continued from [Part 1](advanced-java-concurrency-part-1.md).

---

## 11. What are `Semaphore`, `CountDownLatch`, and `CyclicBarrier`, and how do they differ?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A `Semaphore` limits how many threads can use a resource at once. A `CountDownLatch` lets threads wait until a count reaches zero, and it cannot be reset. A `CyclicBarrier` makes a fixed group of threads wait for each other at a point, and it can be reused for the next round.

### Explanation
```java
import java.util.concurrent.*;

class Demo {
    public static void main(String[] args) throws InterruptedException {
        Semaphore permits = new Semaphore(2);      // at most two concurrent users
        CountDownLatch done = new CountDownLatch(3); // wait for three tasks

        for (int i = 0; i < 3; i++) {
            new Thread(() -> {
                try {
                    permits.acquire();
                    try {
                        System.out.println("working");
                    } finally {
                        permits.release();
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    done.countDown();
                }
            }).start();
        }

        done.await();                               // returns after three countDown() calls
        System.out.println("all finished");
    }
}
```

### When to use / pitfalls
- A latch is one-shot. Use a `CyclicBarrier` or `Phaser` for repeated rounds.
- Release a semaphore permit in a `finally` block, or you will leak permits.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 12. How would you build a producer-consumer pipeline in Java?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a `BlockingQueue`. The producer calls `put()`, which waits when the queue is full; the consumer calls `take()`, which waits when the queue is empty. The bounded capacity gives you back pressure for free. End the stream with a poison pill or by closing the executor.

### Explanation
```java
import java.util.concurrent.*;

class Demo {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> queue = new ArrayBlockingQueue<>(10);

        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 5; i++) {
                    queue.put(i);              // waits if the queue is full
                }
                queue.put(-1);                 // poison pill: tells the consumer to stop
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });

        Thread consumer = new Thread(() -> {
            try {
                while (true) {
                    int value = queue.take();  // waits if the queue is empty
                    if (value == -1) break;
                    System.out.println("processed " + value);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
    }
}
```

### When to use / pitfalls
- An unbounded queue removes back pressure; a fast producer can exhaust memory.
- Restore the interrupt flag (`Thread.currentThread().interrupt()`) instead of swallowing `InterruptedException`.
- With several consumers, send one poison pill per consumer.

**See also:** [Data and persistence](data-and-persistence-part-1.md), [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 13. What are virtual threads, and what should you know about them in Java 21?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Virtual threads (final in Java 21, from Project Loom) are lightweight threads scheduled by the JVM onto a small pool of platform threads, called carrier threads. When a virtual thread blocks on I/O, it unmounts and frees its carrier. They suit workloads with many concurrent blocking tasks; they do not make CPU-bound work faster.

### Explanation
```java
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

class Demo {
    public static void main(String[] args) throws Exception {
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {
                executor.submit(() -> {
                    Thread.sleep(100);     // blocking call: the carrier thread is released
                    return null;
                });
            }
        }                                  // close() waits for submitted tasks to finish
    }
}
```

In Java 21, a virtual thread that blocks inside a `synchronized` block stays pinned to its carrier thread. Prefer `ReentrantLock` in code that blocks while holding a lock.

### When to use / pitfalls
- Do not pool virtual threads. Create one per task.
- Do not use thread-local caches sized for pools of platform threads.
- Virtual threads are not a replacement for tuning a database connection pool; the pool still limits concurrency.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 14. What are the main memory areas of the JVM?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The heap holds objects and arrays and is shared by all threads; it is divided into generations in most collectors. Each thread has its own stack holding method frames and local variables. Metaspace holds class metadata in native memory and replaced PermGen in Java 8. The code cache holds JIT-compiled code.

### Explanation
| Area | Shared? | Holds | Typical error |
|---|---|---|---|
| Heap | Yes | Objects and arrays | `OutOfMemoryError: Java heap space` |
| Thread stack | Per thread | Frames, primitives, references | `StackOverflowError` (deep recursion) |
| Metaspace | Yes | Class metadata | `OutOfMemoryError: Metaspace` |
| Code cache | Yes | JIT-compiled code | Warning when full; compilation stops |

```java
class Demo {
    static int depth = 0;

    static void recurse() {
        depth++;
        recurse();                     // unbounded recursion fills the thread stack
    }

    public static void main(String[] args) {
        try {
            recurse();
        } catch (StackOverflowError e) {
            System.out.println("stack overflowed after " + depth + " calls");
        }
    }
}
```

### When to use / pitfalls
- Local variables that hold references keep objects alive only while the frame exists; the object lives on the heap.
- A memory leak in Java is usually a reference that stays reachable from a static field, a cache, or a listener that is never removed.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 15. Which garbage collectors should you know, and what changed recently?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Serial is single-threaded and suits small heaps or single-CPU machines. Parallel uses several threads to maximise throughput. G1 is the default collector since Java 9 and aims at predictable pauses by collecting regions with the most garbage first. ZGC is a low-latency collector designed to keep pauses short even on large heaps. The CMS collector was removed in Java 14.

### Explanation
Most objects die young, so generational collectors focus on the young generation. Choose a collector by the goal:

- Throughput for batch jobs: Parallel.
- Balanced latency and throughput for most services: G1 (the default).
- Very low pause times on large heaps: ZGC.

Check collector choice and behaviour with GC logging, for example `-Xlog:gc*` on Java 9 and later. Confirm flags against the documentation of your JDK version before you change them in production.

```java
class Demo {
    public static void main(String[] args) {
        Runtime rt = Runtime.getRuntime();
        long usedMb = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
        System.out.println("heap in use (MB): " + usedMb);
    }
}
```

### When to use / pitfalls
- Setting `-Xmx` too low causes frequent collections; setting it too high can cause long pauses in older collectors and wastes memory in containers.
- `System.gc()` is only a hint. Do not call it in application code.
- Container-aware JVM settings matter when the process runs in Docker or Kubernetes. See [DevOps, cloud, and AI](devops-cloud-and-ai-part-1.md).

**See also:** [Devops, cloud, and AI](devops-cloud-and-ai-part-1.md)

</details>

---

## 16. How would you diagnose a slow or out-of-memory Java service?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Measure before changing anything. Collect GC logs and metrics for pauses and heap usage, take a thread dump to see what threads are doing, and take a heap dump when memory grows. Then find the code path that owns the hot objects or the blocked threads and fix that cause.

### Explanation
Useful tools that ship with the JDK:

- `jstack <pid>` or `jcmd <pid> Thread.print`: thread dump, shows `BLOCKED` threads and deadlocks.
- `jmap -dump:live,format=b,file=heap.hprof <pid>` or the `-XX:+HeapDumpOnOutOfMemoryError` flag: heap dump for a tool such as Eclipse MAT.
- `jcmd <pid> GC.heap_info` and GC logs: heap occupancy and pause times.
- Java Flight Recorder: low-overhead profiling events.

Use the same questions in each case: which object type holds the most memory, which thread holds the lock, and what changed in the last deployment.

### When to use / pitfalls
- A heap that grows steadily after each full GC often points to a leak, such as an unbounded cache.
- A high CPU with many threads in `RUNNABLE` in one method points to a hot loop. A high count of `BLOCKED` threads points to lock contention.
- Do not take a heap dump on a production box without planning: it pauses the JVM and writes a large file.

**See also:** [Spring and security](spring-and-security-part-1.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 17. Which design patterns do you use most, and how do you pick one?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The Gang of Four patterns fall into three groups. Creational patterns control how objects are made (Singleton, Factory, Builder). Structural patterns control how objects are composed (Decorator, Adapter, Proxy). Behavioural patterns control how objects cooperate (Observer, Strategy, Template Method). Pick a pattern by the problem you are solving, not by the name.

### Explanation
A pattern is useful when the code has a recurring shape. Match the symptom to the pattern:

| Symptom | Pattern | Typical example |
|---|---|---|
| Creation logic is spread across callers | Factory | Choosing a database driver from a config value |
| Object has many optional settings | Builder | An HTTP request with headers, timeouts, and a body |
| Behaviour must change at runtime | Strategy | Swapping a pricing rule or a sort order |
| Several parts react to one event | Observer | UI listeners, domain events |
| Two APIs do not match | Adapter | Wrapping a legacy client behind your interface |
| Add cross-cutting behaviour around an object | Decorator | Logging, compression, or retry around a call |

Strategy is the most common one in modern Java because a lambda can stand in for a small strategy interface:

```java
import java.util.Comparator;
import java.util.List;

class PricingDemo {
    interface DiscountRule {
        double apply(double amount);
    }

    static double checkout(double amount, DiscountRule rule) {
        return rule.apply(amount);
    }

    public static void main(String[] args) {
        DiscountRule halfOff = a -> a * 0.5;
        DiscountRule flatFive = a -> Math.max(0, a - 5);
        System.out.println(checkout(100, halfOff));  // 50.0
        System.out.println(checkout(100, flatFive)); // 95.0

        List<String> names = new java.util.ArrayList<>(List.of("bo", "alice"));
        names.sort(Comparator.comparingInt(String::length)); // Strategy via Comparator
        System.out.println(names);
    }
}
```

### When to use / pitfalls
- Do not add a pattern "for later". Start with the simplest code and refactor when the variation appears.
- Singleton is easy to overuse. It hides dependencies and makes tests harder. Prefer passing the instance in through a constructor, which a DI container can manage.
- A pattern name in an interview is a shorthand. Explain the problem it solves and the trade-off it adds.

**See also:** [Design patterns (learning)](../../learning/design-patterns/creational-patterns.md), [Core Java](core-java-part-1.md)

</details>

---

## 18. Explain the Decorator pattern with a working example.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A decorator implements the same interface as the object it wraps, holds a reference to that object, and adds behaviour before or after delegating. You can stack decorators in any order at runtime. This is more flexible than creating a subclass for every combination of features.

### Explanation
```java
import java.time.Instant;

interface Notifier {
    void send(String message);
}

class EmailNotifier implements Notifier {
    @Override
    public void send(String message) {
        System.out.println("email: " + message);
    }
}

abstract class NotifierDecorator implements Notifier {
    protected final Notifier inner;

    NotifierDecorator(Notifier inner) {
        this.inner = inner;
    }
}

class UpperCaseDecorator extends NotifierDecorator {
    UpperCaseDecorator(Notifier inner) { super(inner); }

    @Override
    public void send(String message) {
        inner.send(message.toUpperCase());
    }
}

class TimestampDecorator extends NotifierDecorator {
    TimestampDecorator(Notifier inner) { super(inner); }

    @Override
    public void send(String message) {
        inner.send("[" + Instant.now() + "] " + message);
    }
}

class DecoratorDemo {
    public static void main(String[] args) {
        Notifier n = new TimestampDecorator(new UpperCaseDecorator(new EmailNotifier()));
        n.send("deploy finished");
    }
}
```

The JDK uses the same idea. `new BufferedReader(new InputStreamReader(System.in))` wraps one reader inside another, and each layer adds buffering or decoding. `GZIPOutputStream` wraps any `OutputStream` to add compression.

### When to use / pitfalls
- Decorator keeps the same interface. If the wrapper needs a different interface, you want an Adapter.
- Stacking many small decorators makes debugging harder, because the call passes through several layers. Keep the chain short.
- Decorator changes behaviour on one object. Inheritance changes it for every instance of the class and is fixed at compile time.
- Spring's proxy-based features (such as `@Transactional`) are implemented with proxies. A proxy often looks like a decorator, but its purpose is interception rather than adding a feature.

**See also:** [Structural patterns](../../learning/design-patterns/structural-patterns.md), [Design patterns](../../learning/design-patterns/creational-patterns.md)

</details>

---

## 19. How do generics and type erasure work, and what are PECS rules?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Generics give compile-time type checking, so you do not need casts when reading from a collection. The compiler then erases the type parameters: at runtime `List<String>` and `List<Integer>` are the same class. Use `? extends T` when you only read from a structure and `? super T` when you only write to it. This is the PECS rule: Producer Extends, Consumer Super.

### Explanation
```java
import java.util.ArrayList;
import java.util.List;

class ErasureDemo {
    static double sum(List<? extends Number> producer) {
        double total = 0;
        for (Number n : producer) {        // reading: producer
            total += n.doubleValue();
        }
        return total;
    }

    static void addInts(List<? super Integer> consumer) {
        consumer.add(1);                   // writing: consumer
        consumer.add(2);
    }

    public static void main(String[] args) {
        List<String> strings = new ArrayList<>();
        List<Integer> ints = new ArrayList<>();
        System.out.println(strings.getClass() == ints.getClass()); // true, both ArrayList

        List<Number> numbers = new ArrayList<>();
        addInts(numbers);
        System.out.println(sum(numbers));  // 3.0
    }
}
```

Erasure has consequences that interviewers like to test:

- `obj instanceof List<String>` does not compile. `obj instanceof List<?>` does.
- You cannot write `new T()` or `new List<String>[10]`.
- The compiler adds casts and bridge methods, so older code still runs on the same JVM.

The main reason for erasure is compatibility. Generics arrived in Java 5, and code compiled before then had to keep running and linking against generic libraries, so the JVM kept one class per raw type. Erasure is not a memory optimisation.

### When to use / pitfalls
- A method that takes `List<Object>` does not accept a `List<String>`. Use a wildcard instead.
- Heap pollution happens when a generic variable holds a value of the wrong type through a raw type. Avoid raw types.
- Libraries that need the real type at runtime (for example, some JSON mappers) use a `Class<T>` or a `TypeReference` token to keep the type information.

**See also:** [Generics (learning)](../../learning/02a-core-language/generics.md), [Core Java](core-java-part-2.md)

</details>

---

## 20. How do you find and fix a performance bottleneck in a Java application?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Measure first, then change one thing at a time. Profile CPU, allocation, locks, and I/O to find the hot path. Fix the largest cost, measure again, and confirm the change helped. Common causes are GC pressure, lock contention, slow database access (including N+1 queries), and memory leaks.

### Explanation
A practical workflow:

1. Reproduce the slowness with a realistic load, and record a baseline (latency percentiles, throughput, heap use).
2. Profile. Java Flight Recorder (JFR) ships with the JDK and is safe enough for production. Sampling profilers such as async-profiler and commercial tools like JProfiler or YourKit show where time goes.
3. Find the hot method or the wait point. A thread dump shows lock waits; a JFR recording shows allocation.
4. Change one thing and re-measure.

Microbenchmarks need JMH, because the JIT and dead-code elimination make naive timing unreliable:

```java
// Requires the JMH dependency and its annotation processor.
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Scope;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@State(Scope.Benchmark)
public class MapBench {
    private final Map<String, Integer> map = new ConcurrentHashMap<>();

    @Benchmark
    public Integer incrementKey() {
        return map.merge("key", 1, Integer::sum);
    }
}
```

Typical fixes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Latency spikes at regular intervals | GC pauses | Check heap sizing, reduce allocation, consider a low-pause collector |
| Many threads `BLOCKED` on one lock | Lock contention | Narrow the critical section, use a concurrent map or a lock-free counter |
| Many small SQL queries per request | N+1 loading | Fetch the association in one query (for example, a `JOIN FETCH`) |
| Heap grows after every full GC | Leak | Find the retaining path with a heap dump, remove the reference |

### When to use / pitfalls
- A "faster" change that you did not measure is a guess. Keep the baseline and compare.
- Do not benchmark in a debugger or with a tiny input. The JIT needs warm-up time.
- Often the slow part is the database or the network rather than the Java code. Check the query plan before rewriting Java.

**See also:** [Concurrency](../../learning/02c-concurrency-io/locks-atomics.md), [Observability (metrics)](../../learning/20-observability/metrics.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## Quick recap

- Use `Runnable` and executors; avoid creating threads by hand.
- `synchronized` gives exclusion and visibility; `volatile` gives visibility only.
- Guard `wait()` with a `while` loop; prefer `BlockingQueue` for hand-off.
- Prevent deadlock with a consistent lock order and timed lock attempts.
- Use `CompletableFuture` for composition and an explicit pool for blocking work.
- Java 21 virtual threads help with many blocking tasks; they do not speed up CPU-bound code.
- Diagnose with thread dumps, heap dumps, and GC logs, and measure first.

**See also:** [Core Java](core-java-part-1.md), [Spring and security](spring-and-security-part-1.md), [Data and persistence](data-and-persistence-part-1.md)
