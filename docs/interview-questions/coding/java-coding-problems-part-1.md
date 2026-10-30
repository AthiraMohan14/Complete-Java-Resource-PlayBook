# Java-Specific Coding Problems (Part 1 of 4)

Practical Java tasks that interviewers use to check language and library knowledge: caches, singletons, bounded buffers, parsing, file handling, immutability, equality, iteration, parallelism, locking, and dates. Each question gives two approaches with their trade-offs.

---


This page is split into 3 parts. Continue to [Part 2](java-coding-problems-part-2.md).

## 1. Implement an LRU cache

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An LRU (least recently used) cache evicts the entry that was used longest ago when it is full. Both `get` and `put` should run in O(1) time. The shortest correct Java version extends `LinkedHashMap` in access order. The explicit version pairs a `HashMap` with a doubly linked list, which shows you understand the data structure.

### Explanation
**Approach 1: `LinkedHashMap` in access order.** O(1) average for `get` and `put`.

```java
import java.util.LinkedHashMap;
import java.util.Map;

class LruCacheLinked<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    LruCacheLinked(int capacity) {
        super(capacity, 0.75f, true);        // accessOrder = true: get() moves the entry to the end
        this.capacity = capacity;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;            // evict the least recently used entry
    }
}
```

**Approach 2: `HashMap` plus a doubly linked list with sentinels.** O(1) for each operation.

```java
import java.util.HashMap;
import java.util.Map;

class LruCacheManual<K, V> {
    private static class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;

        Node(K key, V value) {
            this.key = key;
            this.value = value;
        }
    }

    private final int capacity;
    private final Map<K, Node<K, V>> index = new HashMap<>();
    private final Node<K, V> head = new Node<>(null, null);   // sentinel: most recent side
    private final Node<K, V> tail = new Node<>(null, null);   // sentinel: least recent side

    LruCacheManual(int capacity) {
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    V get(K key) {
        Node<K, V> node = index.get(key);
        if (node == null) {
            return null;
        }
        unlink(node);
        addToFront(node);
        return node.value;
    }

    void put(K key, V value) {
        Node<K, V> existing = index.get(key);
        if (existing != null) {
            existing.value = value;
            unlink(existing);
            addToFront(existing);
            return;
        }
        if (index.size() == capacity) {
            Node<K, V> lru = tail.prev;
            unlink(lru);
            index.remove(lru.key);
        }
        Node<K, V> node = new Node<>(key, value);
        index.put(key, node);
        addToFront(node);
    }

    private void unlink(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void addToFront(Node<K, V> node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }
}
```

### When to use / pitfalls
- Neither version is thread-safe. Wrap them with a lock, or use a library cache in production.
- Use the sentinel nodes so that inserting and removing never need null checks.
- Clarify whether `get` counts as a use. The rule above assumes it does.

**See also:** [Java coding problems](java-coding-problems-part-1.md), [Architecture and distributed systems](../technical/architecture-and-distributed.md)

</details>

---

## 2. Write a thread-safe singleton

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Three approaches are standard. The holder idiom uses lazy loading through a nested class and is thread-safe without explicit locks. An enum with one constant is the simplest, and it also resists reflection and serialisation attacks. Double-checked locking works, but only with a `volatile` field.

### Explanation
**Approach 1: holder idiom.**

```java
class SettingsSingleton {
    private SettingsSingleton() {
    }

    private static class Holder {
        static final SettingsSingleton INSTANCE = new SettingsSingleton();   // loaded on first use
    }

    static SettingsSingleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

**Approach 2: enum.**

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

enum Registry {
    INSTANCE;

    private final Map<String, String> entries = new ConcurrentHashMap<>();

    void put(String key, String value) {
        entries.put(key, value);
    }

    String get(String key) {
        return entries.get(key);
    }
}
```

**Approach 3: double-checked locking.** Works only because the field is `volatile`.

```java
class LazyConfig {
    private static volatile LazyConfig instance;

    private LazyConfig() {
    }

    static LazyConfig getInstance() {
        LazyConfig local = instance;               // read once
        if (local == null) {
            synchronized (LazyConfig.class) {
                local = instance;
                if (local == null) {
                    local = new LazyConfig();
                    instance = local;
                }
            }
        }
        return local;
    }
}
```

### When to use / pitfalls
- Without `volatile`, another thread can see a partly constructed object. This is the classic bug with double-checked locking.
- A singleton that holds mutable global state is hard to test. Consider passing it in through dependency injection instead.
- Serialising a regular singleton creates a second instance unless you add `readResolve`. Enums avoid that.

**See also:** [Core Java](../technical/core-java-part-1.md), [Advanced Java and concurrency](../technical/advanced-java-concurrency-part-1.md)

</details>

---

## 3. Implement a bounded buffer for producers and consumers

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A bounded buffer blocks producers when it is full and consumers when it is empty. You can build it with a `ReentrantLock` and two `Condition` objects (not-full and not-empty), or use `ArrayBlockingQueue`, which already does this. Use `while` loops around `await()` to handle spurious wakeups.

### Explanation
**Approach 1: lock and conditions.** Each operation is O(1) apart from waiting time.

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

class BoundedBuffer<T> {
    private final Deque<T> items = new ArrayDeque<>();
    private final int capacity;
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();

    BoundedBuffer(int capacity) {
        this.capacity = capacity;
    }

    void put(T item) throws InterruptedException {
        lock.lock();
        try {
            while (items.size() == capacity) {
                notFull.await();
            }
            items.addLast(item);
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }

    T take() throws InterruptedException {
        lock.lock();
        try {
            while (items.isEmpty()) {
                notEmpty.await();
            }
            T item = items.removeFirst();
            notFull.signal();
            return item;
        } finally {
            lock.unlock();
        }
    }
}
```

**Approach 2: `ArrayBlockingQueue` with an executor.**

```java
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

class BlockingBufferDemo {
    public static void main(String[] args) throws Exception {
        BlockingQueue<String> queue = new ArrayBlockingQueue<>(5);
        ExecutorService pool = Executors.newFixedThreadPool(2);
        pool.submit(() -> {
            for (int i = 0; i < 3; i++) {
                queue.put("job-" + i);          // blocks when the queue is full
            }
            return null;
        });
        pool.submit(() -> {
            for (int i = 0; i < 3; i++) {
                System.out.println("took " + queue.take());   // blocks when the queue is empty
            }
            return null;
        });
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

### When to use / pitfalls
- Use `signal` when one waiter can proceed; use `signalAll` when waiters have different conditions or several can proceed.
- Always release the lock in `finally`.
- In an interview, prefer approach 2 for production code and show approach 1 to prove you understand the mechanics.

**See also:** [Advanced Java and concurrency](../technical/advanced-java-concurrency-part-1.md)

</details>

---

## 4. Evaluate an arithmetic expression with precedence and parentheses

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use recursive descent: one method per precedence level. `expr` handles `+` and `-`, `term` handles `*` and `/`, and `factor` handles numbers, parentheses, and unary minus. The parser runs in O(n) time for an input of length n. Shunting-yard, which uses two stacks, is the other standard approach.

### Explanation
**Approach 1: recursive descent.**

```java
class ExpressionParser {
    private final String src;
    private int pos;

    private ExpressionParser(String src) {
        this.src = src.replaceAll("\\s+", "");
    }

    static long eval(String text) {
        ExpressionParser parser = new ExpressionParser(text);
        long value = parser.expr();
        if (parser.pos != parser.src.length()) {
            throw new IllegalArgumentException("unexpected input at " + parser.pos);
        }
        return value;
    }

    private long expr() {
        long value = term();
        while (peek() == '+' || peek() == '-') {
            char op = src.charAt(pos++);
            long right = term();
            value = op == '+' ? value + right : value - right;
        }
        return value;
    }

    private long term() {
        long value = factor();
        while (peek() == '*' || peek() == '/') {
            char op = src.charAt(pos++);
            long right = factor();
            if (op == '*') {
                value *= right;
            } else {
                if (right == 0) {
                    throw new ArithmeticException("divide by zero");
                }
                value /= right;
            }
        }
        return value;
    }

    private long factor() {
        if (peek() == '(') {
            pos++;
            long value = expr();
            expect(')');
            return value;
        }
        if (peek() == '-') {
            pos++;
            return -factor();
        }
        int start = pos;
        while (pos < src.length() && Character.isDigit(src.charAt(pos))) {
            pos++;
        }
        if (start == pos) {
            throw new IllegalArgumentException("number expected at " + pos);
        }
        return Long.parseLong(src.substring(start, pos));
    }

    private char peek() {
        return pos < src.length() ? src.charAt(pos) : '\0';
    }

    private void expect(char c) {
        if (peek() != c) {
            throw new IllegalArgumentException("expected " + c + " at " + pos);
        }
        pos++;
    }
}
```

**Approach 2: shunting-yard, then evaluate.** Convert the infix tokens to postfix with an operator stack, using precedence to decide when to pop. Evaluate the postfix form with a value stack. O(n) time and O(n) space. Describe it in words; implement it if asked.

### When to use / pitfalls
- Integer division truncates toward zero in Java, so `-7 / 2` is `-3`. State that choice.
- Unary minus and the subtraction sign are easy to confuse. The `factor` method above handles unary minus at the start of a factor.
- Report errors with the position; interviewers look for that.

**See also:** [Java coding problems](java-coding-problems-part-1.md), [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---


**Next:** [Part 2](java-coding-problems-part-2.md)
