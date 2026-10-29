# Collections Overview

The Collections Framework is a set of interfaces and classes for storing and manipulating groups of objects. Its design separates what a collection promises (an interface such as `List` or `Map`) from how it stores data (an implementation such as `ArrayList` or `HashMap`). Interviewers start here because the answers depend on the hierarchy, the `equals` and `hashCode` contract, and the complexity of each operation.

## Core concepts

### The hierarchy
`Iterable` is the root for anything usable in an enhanced `for` loop. `Collection` extends it and is the root for lists, sets, and queues. `Map` is separate: it holds key-value pairs, not single elements, so it does not extend `Collection`.

```text
Iterable
└── Collection
    ├── List      (ordered, index-based, duplicates allowed)
    ├── Set       (no duplicates)
    │   └── SortedSet -> NavigableSet
    └── Queue     (ordered for processing)
        └── Deque (double-ended)

Map               (key -> value, unique keys)
└── SortedMap -> NavigableMap
```

### The main interfaces at a glance

| Interface | Stores | Duplicates | Typical implementations |
|---|---|---|---|
| `List` | Ordered elements, accessed by index | Yes | `ArrayList`, `LinkedList`, `Vector`, `CopyOnWriteArrayList` |
| `Set` | Unique elements | No | `HashSet`, `LinkedHashSet`, `TreeSet` |
| `Queue` | Elements in processing order | Yes | `PriorityQueue`, `ArrayDeque`, `LinkedList` |
| `Deque` | Elements at both ends | Yes | `ArrayDeque`, `LinkedList` |
| `Map` | Unique keys mapped to values | Values yes, keys no | `HashMap`, `LinkedHashMap`, `TreeMap`, `ConcurrentHashMap` |

The roadmap lists `ConcurrentHashSet` as a set type. The JDK has no class with that name. For a thread-safe set, use `ConcurrentHashMap.newKeySet()`, which returns a `Set<K>` backed by a `ConcurrentHashMap`.

```java
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class SeenOrders {
    public static void main(String[] args) throws Exception {
        Set<String> seen = ConcurrentHashMap.newKeySet();
        seen.add("order-1");
        System.out.println(seen.add("order-1")); // false: already present
    }
}
```

### Legacy and specialist types
- `Vector` and `Hashtable` predate the framework. They are synchronized, which is slow for single-threaded use, and new code should prefer `ArrayList` or `HashMap` with explicit synchronization when needed.
- `Stack` extends `Vector`. Use `ArrayDeque` instead.
- `WeakHashMap` keeps entries only while their keys are reachable elsewhere.
- `IdentityHashMap` compares keys with `==` rather than `equals`.
- `EnumMap` and `EnumSet` are fast collections for enum keys and values.

### The equals and hashCode contract
Hash-based collections (`HashSet`, `HashMap`) rely on two methods:

1. If `a.equals(b)` is true, then `a.hashCode() == b.hashCode()` must be true.
2. `hashCode` must stay the same while the object is stored in a hash collection.

Break either rule and lookups fail: the object is stored in one bucket but searched in another. Use fields that do not change while the object is in a collection.

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public final class Sku {
    private final String code;

    public Sku(String code) {
        this.code = code;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Sku other)) return false;
        return code.equals(other.code);
    }

    @Override
    public int hashCode() {
        return Objects.hash(code);
    }

    public static void main(String[] args) {
        Set<Sku> skus = new HashSet<>();
        skus.add(new Sku("A-100"));
        System.out.println(skus.contains(new Sku("A-100"))); // true
    }
}
```

Without the `hashCode` override, `contains` would almost certainly return `false`, even though `equals` says the objects match.

### Complexity at a glance
Big-O figures describe typical implementations and are the usual interview answer. Actual performance depends on sizing, hash quality, and the JVM.

| Structure | Access by index or key | Search | Insert or remove |
|---|---|---|---|
| `ArrayList` | O(1) by index | O(n) | O(1) amortized at the end; O(n) in the middle |
| `LinkedList` | O(n) by index | O(n) | O(1) at known node; O(n) to find the node |
| `HashSet` / `HashMap` | Average O(1) | Average O(1) | Average O(1) |
| `TreeSet` / `TreeMap` | O(log n) | O(log n) | O(log n) |
| `ArrayDeque` | n/a | O(n) | O(1) at either end |
| `PriorityQueue` | n/a | O(n) | `offer` and `poll` O(log n); `peek` O(1) |

### Choosing an implementation
- Need an index-based list with mostly reads? `ArrayList`.
- Need unique items? `HashSet`, or `LinkedHashSet` to keep insertion order, or `TreeSet` for sorted order.
- Need key-value lookups? `HashMap`, `LinkedHashMap` for insertion order, `TreeMap` for sorted keys.
- Need a stack or queue? `ArrayDeque`.
- Need to process by priority? `PriorityQueue`.
- Need thread-safe access? `ConcurrentHashMap` for maps, `CopyOnWriteArrayList` for lists read far more often than written.

### Immutable factory methods
Java 9 added `List.of`, `Set.of`, and `Map.of`. These return unmodifiable collections that reject `null` elements and throw `UnsupportedOperationException` on change. `Set.of` and `Map.of` also throw `IllegalArgumentException` on duplicates. `List.copyOf`, `Set.copyOf`, and `Map.copyOf` make unmodifiable copies.

```java
import java.util.List;

public class ImmutableRoles {
    public static void main(String[] args) throws Exception {
        List<String> roles = List.of("reader", "writer");
        // roles.add("admin");  // UnsupportedOperationException
    }
}
```

## How it works / Step by step

1. A `HashSet` or `HashMap` calls `hashCode()` to choose a bucket.
2. Within a bucket, it calls `equals()` to find the matching element or key.
3. A `TreeSet` or `TreeMap` uses the comparator or `compareTo` to walk a balanced tree.
4. An `ArrayList` keeps a backing array and grows it when full, copying the contents.
5. A `LinkedList` links nodes, so inserting at a known position is cheap but indexing requires walking.

## Common pitfalls
- Overriding `equals` but not `hashCode` (or the reverse), which breaks hash-based collections.
- Storing mutable objects as hash keys and then changing the fields that feed `hashCode`.
- Choosing `LinkedList` for random access. `ArrayList` is almost always faster for lists.
- Using `Vector` or `Hashtable` in new single-threaded code out of habit.
- Assuming `List.of` results can be modified, or that `Arrays.asList` supports `add`.
- Expecting `HashMap` to keep insertion order. Use `LinkedHashMap`.
- Using `Stack` instead of `ArrayDeque`.

!!! tip "Interview tip"
    **Q: How does `HashMap` work internally?** It hashes the key, selects a bucket, and compares keys with `equals` inside the bucket. Since Java 8, a bucket that grows past a threshold becomes a balanced tree, which bounds worst-case lookups within a bucket at O(log n) rather than O(n). Good `hashCode` distribution keeps buckets small, so average operations stay O(1).

## Quick recap
- `Collection` covers lists, sets, and queues; `Map` is separate.
- Hash-based collections need consistent `equals` and `hashCode` for keys and elements.
- Choose the implementation by the operation you run most often, not by habit.
- `ConcurrentHashMap.newKeySet()` is the standard thread-safe set.
- `List.of`, `Set.of`, and `Map.of` create immutable collections; they reject nulls.

**See also:** [Lists](lists.md), [Sets and Maps](sets-and-maps.md), [Queues and Deques](queues-and-deques.md)
