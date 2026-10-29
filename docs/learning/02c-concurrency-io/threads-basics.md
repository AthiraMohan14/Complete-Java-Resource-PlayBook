# Threads Basics

A thread is an independent path of execution inside a Java process. Interviewers ask about threads early because almost every later concurrency topic (locks, executors, memory visibility) builds on how threads are created, scheduled, and move through their states.

## Core concepts

### Thread lifecycle and states

A `Thread` moves through the states defined by the `Thread.State` enum. You can read the current state with `getState()`, which is useful for debugging but is only a snapshot.

| State | Meaning |
|---|---|
| `NEW` | Created but `start()` has not been called yet |
| `RUNNABLE` | Running, or ready to run and waiting for CPU time from the scheduler |
| `BLOCKED` | Waiting to enter a `synchronized` block or method held by another thread |
| `WAITING` | Waiting indefinitely, for example after `Object.wait()`, `Thread.join()`, or `LockSupport.park()` |
| `TIMED_WAITING` | Waiting for a fixed time, for example `Thread.sleep(ms)` or `wait(ms)` |
| `TERMINATED` | `run()` has returned or thrown an exception |

```java
public class StateDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> {
            try {
                Thread.sleep(200);
            } catch (InterruptedException ignored) {
            }
        });
        System.out.println(t.getState()); // NEW
        t.start();
        Thread.sleep(50);
        System.out.println(t.getState()); // TIMED_WAITING
        t.join();
        System.out.println(t.getState()); // TERMINATED
    }
}
```

Calling `start()` twice throws `IllegalThreadStateException`. A terminated thread cannot be restarted.

### Creating threads: extending Thread vs implementing Runnable

There are two common ways to define the work a thread performs.

```java
// 1. Extend Thread
class PrintTask extends Thread {
    @Override
    public void run() {
        System.out.println("Running in " + getName());
    }
}

// 2. Implement Runnable (preferred)
class PrintJob implements Runnable {
    @Override
    public void run() {
        System.out.println("Running in " + Thread.currentThread().getName());
    }
}

public class CreateThreads {
    public static void main(String[] args) {
        new PrintTask().start();
        new Thread(new PrintJob(), "worker-1").start();
        new Thread(() -> System.out.println("Lambda task")).start();
    }
}
```

Prefer `Runnable` for three reasons:

- Java has single inheritance. Extending `Thread` uses up your only superclass slot.
- The task is separated from the mechanism that runs it. The same `Runnable` can be given to a `Thread`, an executor, or a test.
- A `Runnable` can be passed to an `ExecutorService` (see [Executors and Futures](executors-futures.md)), which manages threads for you.

Because `Runnable` is a functional interface with one abstract method, a lambda works as well.

### Starting, joining, and naming threads

- `start()` asks the JVM to create a new thread that calls `run()`. Calling `run()` directly just runs the code on the current thread, which is a common mistake.
- `join()` makes the calling thread wait until the target thread terminates. `join(ms)` waits at most the given time.
- `setName()` and the constructor argument give threads readable names for logs and thread dumps.
- `setDaemon(true)` marks a thread as a daemon. The JVM exits when only daemon threads remain. It must be set before `start()`.

```java
public class JoinDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread a = new Thread(() -> System.out.println("A done"), "A");
        Thread b = new Thread(() -> System.out.println("B done"), "B");
        a.start();
        b.start();
        a.join(); // main waits for A
        b.join(); // main waits for B
        System.out.println("Both finished");
    }
}
```

### Interrupts

Interruption is a cooperative signal. One thread calls `interrupt()` on another, and the target decides what to do. Nothing stops the target automatically.

- If the target is blocked in `sleep`, `wait`, or `join`, that method throws `InterruptedException` and clears the interrupt flag.
- Otherwise the flag stays set. The code should check `Thread.currentThread().isInterrupted()` in its loop.

```java
public class InterruptDemo implements Runnable {
    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            // do a unit of work
        }
        System.out.println("Stopped cleanly");
    }

    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(new InterruptDemo());
        t.start();
        Thread.sleep(100);
        t.interrupt();
        t.join();
    }
}
```

Never swallow an `InterruptedException` silently. Either rethrow it or restore the flag with `Thread.currentThread().interrupt()`.

### Thread priority

`setPriority(1..10)` is a hint to the scheduler. Its effect depends on the operating system and is not guaranteed. Do not use priority for correctness. Use locks, executors, or queues to control ordering.

### Virtual threads (Java 21)

Virtual threads are lightweight threads scheduled by the JVM on a small pool of platform threads. Java 21 made them a final feature. They are useful when code spends most of its time waiting on I/O, because a blocked virtual thread does not hold an operating system thread. Create one with `Thread.ofVirtual().start(runnable)` or `Thread.startVirtualThread(runnable)`. The API is the same `Thread` class, so the code that runs inside is ordinary blocking Java code.

## How it works / Step by step

1. Create a `Thread` with a `Runnable` (or a lambda).
2. Call `start()`. The JVM allocates a call stack and schedules the thread.
3. The thread runs `run()` and may move between `RUNNABLE`, `BLOCKED`, `WAITING`, and `TIMED_WAITING`.
4. When `run()` returns or throws, the thread becomes `TERMINATED`.
5. Other threads can `join()` it to wait for completion.

## Common pitfalls

- Calling `run()` instead of `start()`. The code runs on the caller's thread and no concurrency happens.
- Calling `start()` twice. This throws `IllegalThreadStateException`.
- Extending `Thread` when you only need a task. This couples the task to the thread and blocks other superclasses.
- Relying on thread priority or timing (for example, `sleep` to "wait for the other thread") for correctness.
- Swallowing `InterruptedException`, which makes the thread impossible to cancel.
- Assuming a `Thread` object is safe to reuse after it terminates.

!!! tip "Interview tip"
    **Q: What is the difference between `start()` and `run()`?**
    `start()` creates a new thread of execution and then calls `run()` on it. Calling `run()` directly is an ordinary method call on the current thread. Interviewers often use this to check whether you understand threads at all.

## Quick recap

- A thread goes through `NEW`, `RUNNABLE`, `BLOCKED`, `WAITING`, `TIMED_WAITING`, and `TERMINATED`.
- Prefer implementing `Runnable` over extending `Thread`.
- `start()` creates the thread. `run()` is just a method.
- `join()` waits for a thread to finish. Interruption is cooperative.
- Priority is only a hint. Do not use it for correctness.
- Virtual threads (Java 21) suit I/O-heavy, blocking code.

**See also:** [Synchronisation and Volatile](synchronisation-volatile.md), [Executors and Futures](executors-futures.md), [Locks and Atomics](locks-atomics.md)
