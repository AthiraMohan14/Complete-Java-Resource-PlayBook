# Executors, Callable, Future, and CompletableFuture

Creating a new thread for every task is expensive and hard to control. The `java.util.concurrent` executor framework separates *what* to run from *how* threads are managed. Interviewers ask about thread pools because they are the default way to run concurrent work in production services.

## Core concepts

### ExecutorService

An `ExecutorService` accepts tasks and runs them on threads it manages. You submit work and let the pool decide when and where it runs.

```java
import java.util.concurrent.*;

public class ExecutorBasics {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 1; i <= 8; i++) {
            int id = i;
            pool.execute(() -> System.out.println("Task " + id + " on "
                    + Thread.currentThread().getName()));
        }
        pool.shutdown();                            // stop accepting new tasks
        pool.awaitTermination(5, TimeUnit.SECONDS); // wait for queued work
    }
}
```

Common factory methods on `Executors`:

| Factory | Behaviour |
|---|---|
| `newFixedThreadPool(n)` | Fixed number of threads, unbounded queue |
| `newCachedThreadPool()` | Creates threads as needed and reuses idle ones |
| `newSingleThreadExecutor()` | One thread, tasks run in order |
| `newVirtualThreadPerTaskExecutor()` | One virtual thread per task (Java 21) |

The factory methods are convenient, but they hide the queue and the thread limits. For production code, many teams build a `ThreadPoolExecutor` directly so the limits are explicit.

### ThreadPoolExecutor

`ThreadPoolExecutor` is the implementation behind most pools. Its main constructor parameters are:

- `corePoolSize`: threads kept alive even when idle.
- `maximumPoolSize`: the upper limit on threads.
- `keepAliveTime`: how long extra threads stay idle before being removed.
- `workQueue`: where waiting tasks sit.
- `RejectedExecutionHandler`: what happens when the pool and queue are both full.

```java
import java.util.concurrent.*;

public class CustomPool {
    public static void main(String[] args) {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
                2,                                  // core threads
                4,                                  // max threads
                30, TimeUnit.SECONDS,               // idle time for extra threads
                new ArrayBlockingQueue<>(10),       // bounded queue
                new ThreadPoolExecutor.CallerRunsPolicy()); // back-pressure

        for (int i = 0; i < 20; i++) {
            int id = i;
            pool.execute(() -> System.out.println("job " + id));
        }
        pool.shutdown();
    }
}
```

How a submitted task is handled:

1. If fewer than `corePoolSize` threads are running, a new thread is created for the task.
2. Otherwise, the task goes into the queue if there is room.
3. If the queue is full and fewer than `maximumPoolSize` threads are running, a new thread is created.
4. If none of the above is possible, the rejection handler runs.

Note that an unbounded queue (such as the one used by `newFixedThreadPool`) means the pool never grows past `corePoolSize` and the queue can grow without limit. Bounded queues plus a rejection policy protect the service from overload.

Built-in rejection policies: `AbortPolicy` (default, throws `RejectedExecutionException`), `CallerRunsPolicy` (the submitting thread runs the task), `DiscardPolicy`, and `DiscardOldestPolicy`.

### Runnable vs Callable

`Runnable.run()` returns nothing and cannot throw checked exceptions. `Callable<V>.call()` returns a value and may throw an exception. Use `Callable` when the task produces a result.

```java
import java.util.concurrent.*;

public class CallableDemo {
    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newSingleThreadExecutor();
        Callable<Integer> square = () -> 7 * 7;
        Future<Integer> f = pool.submit(square);
        System.out.println(f.get()); // 49, blocks until ready
        pool.shutdown();
    }
}
```

### Future

`submit(Callable)` returns a `Future<V>`, a handle to a result that may not exist yet. Its main methods:

- `get()`: blocks until the result is ready. It throws `ExecutionException` if the task failed, and `CancellationException` if it was cancelled.
- `get(timeout, unit)`: same, but throws `TimeoutException` after the wait.
- `isDone()`: true when the task finished, failed, or was cancelled.
- `cancel(mayInterrupt)`: attempts to cancel. With `true`, the running thread is interrupted.

`Future` alone cannot be chained or combined with other futures. That limitation led to `CompletableFuture`.

### CompletableFuture

`CompletableFuture<T>` is a `Future` that you can complete manually, chain, and combine without blocking. Work runs on the common pool by default, or on an executor you pass in.

```java
import java.util.concurrent.*;

public class CfDemo {
    public static void main(String[] args) {
        CompletableFuture<String> result = CompletableFuture
                .supplyAsync(() -> 21)              // runs on a pool thread
                .thenApply(n -> n * 2)              // transform the value
                .thenApply(n -> "answer=" + n)
                .exceptionally(ex -> "failed: " + ex.getMessage());

        System.out.println(result.join());          // answer=42
    }
}
```

Useful methods:

- `supplyAsync` / `runAsync`: start work asynchronously.
- `thenApply`, `thenAccept`, `thenRun`: continue after a result (transform, consume, or run).
- `thenCompose`: continue with another `CompletableFuture` (flat-map).
- `thenCombine`: combine two independent futures.
- `allOf` / `anyOf`: wait for many futures.
- `exceptionally`, `handle`, `whenComplete`: deal with errors.
- `join()` (unchecked) and `get()` (checked) to read the result.

Combining two independent calls in parallel:

```java
import java.util.concurrent.CompletableFuture;

public class CombineDemo {
    public static void main(String[] args) {
        CompletableFuture<String> user = CompletableFuture.supplyAsync(() -> "alice");
        CompletableFuture<Integer> score = CompletableFuture.supplyAsync(() -> 90);
        String summary = user.thenCombine(score, (u, s) -> u + " scored " + s).join();
        System.out.println(summary); // alice scored 90
    }
}
```

Pass a dedicated executor for blocking I/O. The common pool has few threads, and blocking calls on it can starve other work:

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class IoPoolDemo {
    static String callRemoteService() {
        return "response";
    }

    public static void main(String[] args) {
        ExecutorService io = Executors.newFixedThreadPool(20);
        CompletableFuture.supplyAsync(() -> callRemoteService(), io);
        io.shutdown();
    }
}
```

### Virtual threads and executors (Java 21)

Java 21 made virtual threads a final feature. A per-task virtual thread executor suits code that spends most of its time waiting on network or disk, because waiting virtual threads do not block operating system threads. Do not expect a speed-up for CPU-bound work, and do not pool virtual threads; create one per task.

```java
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class VirtualThreadsDemo {
    public static void main(String[] args) {
        try (ExecutorService vt = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {
                vt.submit(() -> {
                    Thread.sleep(100);   // blocking is cheap for virtual threads
                    return null;
                });
            }
        } // close() waits for submitted tasks (ExecutorService is AutoCloseable since Java 19)
    }
}
```

### Shutting down

Always shut down an executor, or the JVM may not exit because pool threads are non-daemon. `shutdown()` finishes queued tasks and stops accepting new ones. `shutdownNow()` attempts to interrupt running tasks and returns the tasks that never started.

## How it works / Step by step

1. Create a pool (factory method or `ThreadPoolExecutor`).
2. `submit` a `Callable` (get a `Future`) or `execute` a `Runnable`.
3. The pool queues the task or assigns it to a worker thread.
4. The result is available through `Future.get()` or a `CompletableFuture` chain.
5. Call `shutdown()` and `awaitTermination()`.

## Common pitfalls

- Using `Executors.newFixedThreadPool` or `newCachedThreadPool` in production without knowing their queue and thread limits. A cached pool can create unlimited threads.
- Forgetting `shutdown()`, which keeps the JVM alive.
- Calling `future.get()` inside a loop on the same pool that runs the tasks, causing a deadlock when the pool is saturated.
- Ignoring the exception wrapped in `ExecutionException`.
- Running blocking calls on the `CompletableFuture` common pool.
- Calling `join()` on a future that never completes, with no timeout.

!!! tip "Interview tip"
    **Q: Why use a thread pool instead of `new Thread` for each task?**
    Thread creation costs time and memory, and unbounded threads can exhaust resources. A pool reuses a bounded set of threads, queues the excess work, and gives you a place to set limits and rejection behaviour.

## Quick recap

- `ExecutorService` separates tasks from thread management.
- `ThreadPoolExecutor` parameters (core, max, queue, rejection policy) define behaviour under load.
- `Callable` returns a value and may throw. `Future.get()` blocks and wraps errors in `ExecutionException`.
- `CompletableFuture` chains and combines async work without blocking.
- Use bounded queues and a dedicated executor for blocking I/O.
- Always call `shutdown()`.

**See also:** [Threads Basics](threads-basics.md), [Locks and Atomics](locks-atomics.md), [Synchronisation and Volatile](synchronisation-volatile.md)
