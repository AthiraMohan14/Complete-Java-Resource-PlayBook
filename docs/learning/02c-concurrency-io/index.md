# Concurrency, I/O, and Networking

Threads, synchronisation, executors, file and stream APIs, serialisation, and networking. These topics make up roadmap section 2 (concurrency, I/O, and networking), and interviewers use them to test how you reason about shared state, blocking calls, and external systems.

---

## Topics

### [Threads Basics](threads-basics.md)
**thread lifecycle - Thread.State - Runnable - start vs run - join - interrupts - virtual threads**
Thread states, creating threads with `Runnable`, joining and interrupting, and why `start()` is not `run()`.

### [Synchronisation and Volatile](synchronisation-volatile.md)
**synchronized - volatile - wait/notify - race condition - deadlock - lock ordering**
Mutual exclusion with `synchronized`, what `volatile` does and does not guarantee, safe `wait` loops, and how deadlocks form and are avoided.

### [Executors and Futures](executors-futures.md)
**ExecutorService - ThreadPoolExecutor - Callable - Future - CompletableFuture - bounded queues**
Thread pools, how `ThreadPoolExecutor` handles load, and how to get and chain results with `Future` and `CompletableFuture`.

### [Locks and Atomics](locks-atomics.md)
**ReentrantLock - Semaphore - CountDownLatch - CyclicBarrier - AtomicInteger - CAS - ThreadLocal**
Explicit locks, coordination helpers for groups of threads, lock-free atomic variables, and per-thread values.

### [I/O, Files, and Serialisation](io-files-serialisation.md)
**java.io - streams - Path and Files - NIO channels - Serializable - transient - serialVersionUID**
Byte and character streams, the modern `Path` and `Files` API, NIO buffers, and the risks of Java serialisation.

### [Networking](networking.md)
**InetAddress - URI - HttpClient - Socket - ServerSocket - Jakarta Mail**
Name resolution, the Java 11 `HttpClient`, raw TCP sockets, and sending email with Jakarta Mail.

**See also:** [Learning home](../index.md)
