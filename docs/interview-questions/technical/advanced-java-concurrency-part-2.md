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

## Quick recap

- Use `Runnable` and executors; avoid creating threads by hand.
- `synchronized` gives exclusion and visibility; `volatile` gives visibility only.
- Guard `wait()` with a `while` loop; prefer `BlockingQueue` for hand-off.
- Prevent deadlock with a consistent lock order and timed lock attempts.
- Use `CompletableFuture` for composition and an explicit pool for blocking work.
- Java 21 virtual threads help with many blocking tasks; they do not speed up CPU-bound code.
- Diagnose with thread dumps, heap dumps, and GC logs, and measure first.

**See also:** [Core Java](core-java-part-1.md), [Spring and security](spring-and-security-part-1.md), [Data and persistence](data-and-persistence-part-1.md)
