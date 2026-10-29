# Synchronisation, Volatile, and Deadlock

When several threads share mutable state, the result depends on timing. Synchronisation makes a block of code run under mutual exclusion and makes its effects visible to other threads. Interviewers use this topic to test whether you understand race conditions, the difference between visibility and atomicity, and how deadlocks form.

## Core concepts

### The race condition

A race condition happens when the correct result depends on the order in which threads run. `count++` looks like one step, but it is three: read, add, write. Two threads can read the same value and both write back the same increment.

```java
public class UnsafeCounter {
    private int count = 0;

    public void increment() {
        count++; // not atomic
    }

    public int get() {
        return count;
    }
}
```

Two threads calling `increment()` one million times each often end below two million.

### `synchronized` methods and blocks

`synchronized` acquires the intrinsic lock (monitor) of an object. Only one thread can hold a given monitor at a time. Exiting the block releases the lock, and the release also makes the writes inside the block visible to the next thread that acquires the same lock.

```java
public class SafeCounter {
    private int count = 0;

    public synchronized void increment() {  // locks 'this'
        count++;
    }

    public synchronized int get() {
        return count;
    }
}
```

A smaller critical section is often better. Lock only the part that touches shared state:

```java
public class Inventory {
    private final Object lock = new Object();
    private int stock = 10;

    public boolean reserve() {
        synchronized (lock) {
            if (stock == 0) {
                return false;
            }
            stock--;
            return true;
        }
    }
}
```

Using a private lock object (instead of `this`) keeps outside code from locking your object by accident.

### Static synchronisation

A `static synchronized` method locks the `Class` object of the class, not an instance. All threads calling any static synchronized method of that class contend for the same lock. A `synchronized (Foo.class) { ... }` block does the same thing.

```java
public class IdGenerator {
    private static long next = 1;

    public static synchronized long nextId() {  // locks IdGenerator.class
        return next++;
    }
}
```

Instance methods and static methods use different locks, so an instance `synchronized` method and a static one can run at the same time.

### `volatile`: visibility, not atomicity

Without synchronisation, one thread may not see another thread's writes at all. The compiler and CPU may cache values or reorder instructions. Declaring a field `volatile` tells the JVM that:

- every read sees the latest written value (visibility), and
- reads and writes are not reordered around each other in a way that breaks the happens-before rule (ordering).

`volatile` does **not** make compound actions atomic. `count++` on a volatile field is still a race.

```java
public class StopFlag implements Runnable {
    private volatile boolean running = true;

    @Override
    public void run() {
        while (running) {
            // work
        }
        System.out.println("Stopped");
    }

    public void stop() {
        running = false; // the worker sees this change
    }
}
```

Use `volatile` for a simple flag or a single value that is written by one thread and read by others. Use `synchronized`, or the atomic classes in [Locks and Atomics](locks-atomics.md), when you need a read-modify-write to be atomic.

### `wait()`, `notify()`, and `notifyAll()`

These methods let threads wait for a condition that another thread will make true. They must be called while holding the monitor of the object, otherwise they throw `IllegalMonitorStateException`. `wait()` releases the monitor while it waits.

```java
public class BoundedBox {
    private int item = -1;
    private boolean full = false;

    public synchronized void put(int value) throws InterruptedException {
        while (full) {          // always loop, never 'if'
            wait();
        }
        item = value;
        full = true;
        notifyAll();
    }

    public synchronized int take() throws InterruptedException {
        while (!full) {
            wait();
        }
        full = false;
        notifyAll();
        return item;
    }
}
```

Two rules matter in interviews:

- Wrap `wait()` in a `while` loop that re-checks the condition. A thread can wake up without a notification (spurious wakeup), and another thread may have changed the state first.
- Prefer `notifyAll()` unless you are certain only one kind of waiter needs to wake. `notify()` wakes an arbitrary waiter, which can leave the right one asleep.

For new code, `java.util.concurrent` queues and locks with `Condition` objects are usually clearer than raw `wait` and `notify`.

### Deadlock

A deadlock happens when two or more threads each hold a lock the others need, and none can continue.

```java
public class DeadlockDemo {
    private static final Object A = new Object();
    private static final Object B = new Object();

    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (A) {
                sleep(50);
                synchronized (B) {
                    System.out.println("T1 got both");
                }
            }
        }).start();

        new Thread(() -> {
            synchronized (B) {
                sleep(50);
                synchronized (A) {          // waits forever for T1
                    System.out.println("T2 got both");
                }
            }
        }).start();
    }

    private static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

The four Coffman conditions must all hold: mutual exclusion, hold and wait, no preemption, and circular wait. Prevention breaks one of them. The most practical fix is **lock ordering**: every thread acquires locks in the same global order (here, always A then B).

Detection: take a thread dump with `jstack <pid>` or `jcmd <pid> Thread.print`. The dump reports "Found one Java-level deadlock" when the JVM detects a cycle. Using `tryLock` with a timeout (see [Locks and Atomics](locks-atomics.md)) is another way to avoid waiting forever.

### Happens-before in one sentence

An unlock happens before a later lock on the same monitor, and a write to a `volatile` field happens before a later read of that field. The JMM uses these edges to decide what a thread is guaranteed to see.

## How it works / Step by step

1. Thread A enters a `synchronized` block and acquires the monitor of the object.
2. Thread B tries to enter the same monitor and moves to `BLOCKED`.
3. A exits the block, releases the monitor, and B acquires it.
4. A `volatile` write by one thread is visible to a later `volatile` read by another.
5. A deadlock forms when each thread holds one monitor and waits for the other.

| Need | Tool |
|---|---|
| Mutual exclusion around several fields | `synchronized` block |
| Stop flag or publish a single value | `volatile` |
| Atomic counter | `AtomicInteger` (see locks and atomics page) |
| Wait for a condition | `wait`/`notifyAll` in a loop, or a `Condition` |

## Common pitfalls

- Assuming `volatile` makes `count++` safe. It does not.
- Using `if` instead of `while` around `wait()`.
- Calling `wait()` or `notify()` without holding the monitor.
- Synchronising on a `String` literal or a boxed `Integer`, which other code may share.
- Locking in different orders in different methods, which creates deadlocks.
- Holding a lock while doing slow I/O or calling unknown code.
- Forgetting that `synchronized` on an instance method does not protect static state.

!!! tip "Interview tip"
    **Q: Why is `volatile` not enough to make a counter thread-safe?**
    `volatile` guarantees visibility and ordering for each single read or write. `count++` is three operations (read, add, write), and `volatile` does not make the three happen as one unit. Use `synchronized`, `AtomicInteger`, or a lock.

## Quick recap

- `synchronized` gives mutual exclusion and visibility on the monitor it locks.
- `static synchronized` locks the `Class` object, not an instance.
- `volatile` gives visibility and ordering, not atomicity.
- Always call `wait()` in a `while` loop, and prefer `notifyAll()`.
- Deadlock needs circular waiting. Lock ordering prevents it. Thread dumps help find it.

**See also:** [Threads Basics](threads-basics.md), [Locks and Atomics](locks-atomics.md), [Executors and Futures](executors-futures.md)
