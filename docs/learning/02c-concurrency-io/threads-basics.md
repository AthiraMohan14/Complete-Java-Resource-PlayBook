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

### Why programs use threads

- **Responsiveness:** a UI or request handler can stay available while a slow job runs on another thread.
- **Hardware use:** on a multi-core machine, independent pieces of work can run at the same time.
- **Simpler structure:** a server can give each connection its own thread of control, which is easier to read than hand-written state machines.

### User threads and daemon threads

Every thread is either a user thread or a daemon thread. The JVM uses this flag only to decide when it may exit.

| | User thread | Daemon thread |
|---|---|---|
| JVM exit | Waits for every user thread to finish | Does not wait; it is abandoned when only daemon threads remain |
| Typical use | Application work | Background housekeeping, such as a heartbeat or cache cleaner |
| Default | Created by the application | A new thread inherits the daemon flag of the thread that created it |

```java
public class DaemonDemo {
    public static void main(String[] args) {
        Thread heartbeat = new Thread(() -> {
            while (true) {
                System.out.println("alive");
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    return;
                }
            }
        });
        heartbeat.setDaemon(true);   // must be called before start()
        heartbeat.start();
        // main returns here, so the JVM exits without waiting for heartbeat
    }
}
```

A daemon thread can be stopped at any point when the JVM exits, so never leave a file write or a transaction half done on one. Daemon status does not change scheduling priority; the two settings are independent.

### Processes, threads, and IPC

A process is a running program with its own address space. A thread lives inside a process and shares that process's memory with its sibling threads.

| Aspect | Process | Thread |
|---|---|---|
| Memory | Separate, mostly isolated address space | Shares the heap and static fields of its process |
| Cost to create and switch | Higher | Lower |
| Sharing data | Needs IPC mechanisms | Shares objects directly, so it needs synchronisation |
| Isolation | A failing process usually does not corrupt others | A bug that corrupts shared state affects every thread |

Processes fall into two groups by how they relate to each other:

- **Independent process:** it neither shares data nor resources with other processes, so other processes cannot change its results and it needs no IPC.
- **Co-operating process:** it exchanges data or shares resources with other processes, so what those processes do can affect it. It needs IPC to pass data and to coordinate.

Processes that cooperate must use inter-process communication (IPC). There are two basic models:

1. **Shared memory:** the processes map a common region of memory and coordinate access to it, usually with a lock or semaphore.
2. **Message passing:** the processes exchange discrete messages through a channel such as a pipe, socket, or queue.

Files and network sockets are common everyday forms of message passing. Inside one JVM you do not need IPC, because threads already share memory. Use it when your Java program talks to a separate program, such as a database or a sidecar process on the same host. The `java.net` and `java.nio` packages cover the socket side (see [Networking](networking.md)).

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
