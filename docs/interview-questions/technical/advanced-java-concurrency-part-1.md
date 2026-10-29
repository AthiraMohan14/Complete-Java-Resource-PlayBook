# Advanced Java: Concurrency, JVM Memory, and GC (Part 1 of 2)

Questions on threads, synchronisation, the `java.util.concurrent` toolkit, virtual threads, and how the JVM manages memory. Interviewers use these to check whether you can reason about shared state, not just name classes.

---


This page is split into 2 parts. Continue to [Part 2](advanced-java-concurrency-part-2.md).

## 1. What is the difference between extending `Thread` and implementing `Runnable`? What are the thread states?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Implementing `Runnable` separates the task from the thread that runs it, so the same task can be submitted to a thread pool. Extending `Thread` ties the task to one thread and uses up Java's single inheritance slot. A thread moves through the states `NEW`, `RUNNABLE`, `BLOCKED`, `WAITING`, `TIMED_WAITING`, and `TERMINATED`.

### Explanation
```java
class Demo {
    public static void main(String[] args) throws InterruptedException {
        Runnable task = () -> System.out.println("running in " + Thread.currentThread().getName());
        Thread t = new Thread(task, "worker-1");
        System.out.println(t.getState());   // NEW
        t.start();
        t.join();                           // wait for it to finish
        System.out.println(t.getState());   // TERMINATED
    }
}
```

- `BLOCKED`: waiting to enter a `synchronized` block.
- `WAITING`: waiting indefinitely (`wait()`, `join()`, `LockSupport.park()`).
- `TIMED_WAITING`: waiting for a fixed time (`sleep(ms)`, `wait(ms)`).

### When to use / pitfalls
- Calling `run()` directly does not start a new thread. Only `start()` does.
- Do not rely on thread priorities for correctness.
- Prefer an executor to creating threads by hand. See question 6.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 2. What does `synchronized` lock, and how does a static synchronized method differ from an instance one?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A `synchronized` instance method locks the object (`this`). A `static synchronized` method locks the `Class` object. Only one thread at a time can hold a given lock, and a thread that enters the lock sees the writes made by the previous holder.

### Explanation
```java
class Counter {
    private int count;

    public synchronized void increment() {      // locks this Counter instance
        count++;
    }

    public synchronized int get() {
        return count;
    }

    private static int total;

    public static synchronized void addToTotal(int n) {   // locks Counter.class
        total += n;
    }
}
```

A `synchronized (lockObject) { ... }` block gives finer control. Choose a private final lock object so outside code cannot lock on it.

### When to use / pitfalls
- Two threads synchronised on different objects do not exclude each other.
- Keep critical sections short. Do not call slow I/O or unknown callbacks while holding a lock.
- Reentrant: a thread that already holds the lock can enter again.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 3. What is the difference between `volatile` and `synchronized`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`volatile` guarantees visibility: a write to a volatile field is seen by later reads from any thread, and it orders those accesses. It does not make a read-modify-write sequence atomic. `synchronized` provides both mutual exclusion and visibility.

### Explanation
```java
class Worker implements Runnable {
    private volatile boolean running = true;   // visibility only

    public void stop() {
        running = false;                       // seen by the worker thread
    }

    @Override
    public void run() {
        while (running) {
            // do work
        }
    }
}
```

`volatile int count; count++;` is still a race, because the increment reads, adds, and writes. Use `AtomicInteger` or a lock for that.

### When to use / pitfalls
- Use `volatile` for a simple flag or a single value published by one writer.
- Do not use `volatile` to protect a compound check-then-act, such as "if null, create".
- Java's memory model defines happens-before edges. A volatile write happens-before every later read of the same field.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 4. How do `wait()` and `notify()` work, and why must the condition be checked in a loop?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`wait()` releases the object's monitor and suspends the thread until another thread calls `notify()` or `notifyAll()` on the same object. It must be called while holding that monitor. The condition is re-checked in a `while` loop because a thread can wake up spuriously or find that the state changed again before it runs.

### Explanation
```java
class Mailbox {
    private String message;

    public synchronized void put(String m) throws InterruptedException {
        while (message != null) {      // loop, not if
            wait();
        }
        message = m;
        notifyAll();
    }

    public synchronized String take() throws InterruptedException {
        while (message == null) {
            wait();
        }
        String m = message;
        message = null;
        notifyAll();
        return m;
    }
}
```

In new code, `java.util.concurrent.locks.Condition` (from a `ReentrantLock`) gives separate wait sets for different conditions, which is clearer than `wait`/`notify` on one monitor.

### When to use / pitfalls
- Calling `wait()` without holding the lock throws `IllegalMonitorStateException`.
- `notify()` wakes an arbitrary waiter. Use `notifyAll()` unless you are sure only one kind of waiter exists.
- Prefer a `BlockingQueue` (question 12) over hand-written wait and notify.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 5. What is a deadlock, and how do you prevent it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A deadlock happens when threads wait for each other's locks in a cycle, so none can continue. It needs four conditions at once: mutual exclusion, hold and wait, no preemption, and circular wait. Break any one condition to prevent it; in practice, the common fix is a consistent lock ordering, which removes circular wait.

### Explanation
```java
class Transfer {
    private final Object lockA = new Object();
    private final Object lockB = new Object();

    // Risky: one method takes A then B, another takes B then A.
    // Safe: every method takes lockA first, then lockB.
    public void moveAtoB() {
        synchronized (lockA) {
            synchronized (lockB) {
                // move funds
            }
        }
    }

    public void moveBtoA() {
        synchronized (lockA) {        // same order as above
            synchronized (lockB) {
                // move funds
            }
        }
    }
}
```

Detect deadlocks at runtime with `jstack <pid>` or `jcmd <pid> Thread.print`, which report "Found one Java-level deadlock" when one exists.

### When to use / pitfalls
- Timed `tryLock(timeout)` on `ReentrantLock` lets a thread back off instead of waiting forever.
- Keep the lock scope small and never call external code while holding a lock.
- A deadlock is different from a livelock (threads keep running but make no progress) and from starvation.

**See also:** [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 6. What is an `ExecutorService`, and how do you size a thread pool?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An `ExecutorService` manages a pool of worker threads and a queue of submitted tasks, so you do not create a thread per task. Size CPU-bound pools near the number of cores. Size I/O-bound pools larger, based on how many tasks you expect to wait at once, and measure.

### Explanation
```java
import java.util.concurrent.*;

class Demo {
    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        Future<Integer> result = pool.submit(() -> 6 * 7);
        System.out.println(result.get());   // blocks until the task completes: 42
        pool.shutdown();                     // stop accepting tasks; let queued ones finish
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

A common sizing guide for CPU-bound work is the number of cores; for I/O-bound work, it is cores multiplied by (1 + wait time / compute time). Treat that as a starting point and measure it.

### When to use / pitfalls
- `Executors.newFixedThreadPool` uses an unbounded queue, so a backlog can grow until memory runs out. In production, build a `ThreadPoolExecutor` with a bounded queue and a rejection policy.
- Always call `shutdown()`. Non-daemon pool threads keep the JVM alive.
- Exceptions thrown inside `execute()` go to the thread's uncaught-exception handler; exceptions from `submit()` are held in the `Future`.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 7. How do `Callable` and `Future` differ from `Runnable`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`Runnable.run()` returns nothing and cannot throw checked exceptions. `Callable<V>.call()` returns a value and can throw an exception. `submit()` returns a `Future<V>`, which lets you get the result, check whether it is done, cancel it, or read the exception through `ExecutionException`.

### Explanation
```java
import java.util.concurrent.*;

class Demo {
    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newSingleThreadExecutor();
        Callable<String> task = () -> {
            Thread.sleep(200);
            return "report ready";
        };
        Future<String> future = pool.submit(task);
        try {
            System.out.println(future.get(1, TimeUnit.SECONDS));
        } catch (ExecutionException e) {
            System.out.println("task failed: " + e.getCause());
        } catch (TimeoutException e) {
            future.cancel(true);
        } finally {
            pool.shutdown();
        }
    }
}
```

### When to use / pitfalls
- `Future.get()` blocks. Use a timeout, or use `CompletableFuture` to avoid blocking.
- Always handle `ExecutionException`: the real cause is `getCause()`.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 8. How does `CompletableFuture` compose asynchronous work?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`CompletableFuture` represents a value that will arrive later and lets you chain steps without blocking. `supplyAsync` starts work on a pool, `thenApply` transforms the result, `thenCompose` chains another asynchronous step, `thenCombine` joins two independent results, and `allOf` waits for many. Errors are handled with `exceptionally` or `handle`.

### Explanation
```java
import java.util.concurrent.CompletableFuture;

class Demo {
    public static void main(String[] args) {
        CompletableFuture<String> customer = CompletableFuture.supplyAsync(() -> "cust-42");
        CompletableFuture<Integer> points = CompletableFuture.supplyAsync(() -> 120);

        String summary = customer
                .thenCombine(points, (c, p) -> c + " has " + p + " points")
                .exceptionally(ex -> "lookup failed: " + ex.getMessage())
                .join();                 // join() blocks only at the end

        System.out.println(summary);
    }
}
```

`thenApply` is like `map`; `thenCompose` is like `flatMap`. Use the `Async` variants (such as `thenApplyAsync`) when the next step is slow and should not run on the thread that completed the previous one.

### When to use / pitfalls
- Without an explicit executor, `supplyAsync` uses the common `ForkJoinPool`. Pass your own pool for blocking I/O so you do not starve it.
- `join()` throws `CompletionException`; `get()` throws `ExecutionException`.

**See also:** [Architecture and distributed systems](architecture-and-distributed.md)

</details>

---

## 9. What are atomic classes and `ThreadLocal`, and when do you use them?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Atomic classes such as `AtomicInteger` and `AtomicReference` perform single-variable updates (for example, compare-and-set) without a lock. `ThreadLocal` gives each thread its own copy of a value, so there is no sharing to synchronise.

### Explanation
```java
import java.util.concurrent.atomic.AtomicInteger;

class RequestCounter {
    private final AtomicInteger handled = new AtomicInteger();

    void onRequest() {
        handled.incrementAndGet();     // atomic, no lock needed
    }

    int total() {
        return handled.get();
    }
}

class RequestContext {
    private static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();

    static void set(String id) { REQUEST_ID.set(id); }
    static String get() { return REQUEST_ID.get(); }
    static void clear() { REQUEST_ID.remove(); }   // always remove, especially in pools
}
```

### When to use / pitfalls
- Atomics work for one variable. If two fields must change together, use a lock or an immutable object swapped through `AtomicReference`.
- `ThreadLocal` values leak in thread pools unless you call `remove()`. This is a real bug source in web servers.
- With virtual threads, `ThreadLocal` is still valid, but creating very many of them costs memory.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 10. What is the difference between `ReentrantLock` and `synchronized`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Both are reentrant mutual-exclusion locks. `ReentrantLock` adds features that `synchronized` lacks: timed and interruptible lock attempts (`tryLock`, `lockInterruptibly`), an optional fairness policy, and multiple `Condition` objects. `synchronized` is simpler and releases the lock automatically, even on exceptions.

### Explanation
```java
import java.util.concurrent.locks.ReentrantLock;

class Account {
    private final ReentrantLock lock = new ReentrantLock();
    private long balance;

    void deposit(long amount) {
        lock.lock();
        try {
            balance += amount;
        } finally {
            lock.unlock();              // must be in finally
        }
    }

    boolean tryDeposit(long amount) {
        if (!lock.tryLock()) {          // give up instead of waiting
            return false;
        }
        try {
            balance += amount;
            return true;
        } finally {
            lock.unlock();
        }
    }
}
```

### When to use / pitfalls
- Forgetting `unlock()` in a `finally` block leaves the lock held forever.
- Use `synchronized` by default. Reach for `ReentrantLock` when you need timeouts, interruption, or several conditions.

**See also:** [Core Java](core-java-part-1.md)

</details>

---


**Next:** [Part 2](advanced-java-concurrency-part-2.md)
