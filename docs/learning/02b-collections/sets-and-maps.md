# Sets and Maps

A `Set` holds unique elements, and a `Map` holds key-value pairs with unique keys. Both are used constantly, and both come in hash-based, insertion-ordered, sorted, and thread-safe variants. Interviewers ask which implementation to choose, how `HashMap` locates a key, and why a mutable key can break a map.

## Core concepts

### Sets
A `Set` rejects duplicates. `add` returns `false` if the element is already present. Membership tests are the main reason to use one.

| Implementation | Ordering | Null elements | Typical use |
|---|---|---|---|
| `HashSet` | None | One `null` allowed | Fast membership checks |
| `LinkedHashSet` | Insertion order | One `null` allowed | Unique items that must keep their order |
| `TreeSet` | Sorted (natural or comparator) | Not allowed | Sorted unique items, range queries |

```java
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

public class SetBasics {
    public static void main(String[] args) {
        String[] input = {"pear", "apple", "pear", "fig"};

        Set<String> hash = new HashSet<>(List.of(input));
        Set<String> ordered = new LinkedHashSet<>(List.of(input));
        Set<String> sorted = new TreeSet<>(List.of(input));

        System.out.println(ordered); // [pear, apple, fig]
        System.out.println(sorted);  // [apple, fig, pear]
        System.out.println(hash.size()); // 3
    }
}
```

`List.of(input)` requires `java.util.List`, and passing an array to `List.of` works because `input` is an array of `String`. The duplicate `pear` is removed by every set.

### HashSet internals
A `HashSet` is a `HashMap` whose keys are the elements. Its operations inherit the hashing rules from the map: an element must have consistent `equals` and `hashCode`.

### Maps
A `Map<K, V>` associates each key with one value. Keys are unique; values need not be. `put` replaces the value for an existing key and returns the old value. `get` returns `null` when the key is absent.

| Implementation | Ordering | Null keys and values | Notes |
|---|---|---|---|
| `HashMap` | None | One null key, many null values | General purpose |
| `LinkedHashMap` | Insertion order (or access order) | Same as `HashMap` | Can implement an LRU cache |
| `TreeMap` | Sorted by key | Null key not allowed | Range and navigation methods |
| `Hashtable` | None | Neither nulls allowed | Legacy, synchronized |
| `ConcurrentHashMap` | None | Neither nulls allowed | Thread-safe, scalable |
| `WeakHashMap` | None | Null key allowed | Entries removed when keys are no longer referenced elsewhere |
| `IdentityHashMap` | None | Null allowed | Compares keys by `==`, not `equals` |

```java
import java.util.HashMap;
import java.util.Map;

public class MapBasics {
    public static void main(String[] args) {
        Map<String, Integer> stock = new HashMap<>();
        stock.put("pen", 10);
        stock.put("pad", 4);
        stock.merge("pen", 5, Integer::sum);       // pen becomes 15
        stock.computeIfAbsent("ink", k -> 0);       // adds ink -> 0
        stock.putIfAbsent("pad", 99);               // no change: pad exists

        System.out.println(stock.getOrDefault("cup", 0)); // 0
        for (Map.Entry<String, Integer> e : stock.entrySet()) {
            System.out.println(e.getKey() + " = " + e.getValue());
        }
    }
}
```

Prefer `merge`, `computeIfAbsent`, and `getOrDefault` over the older check-then-put pattern. They are shorter and, on `ConcurrentHashMap`, atomic.

### How HashMap finds a key
1. The key's `hashCode()` is computed and spread (mixed) to reduce collisions.
2. The hash selects a bucket in an internal array.
3. Within the bucket, `equals()` finds the matching key.
4. If many keys share a bucket, the bucket becomes a tree (Java 8 and later), keeping lookups efficient.

This is why `hashCode` and `equals` must agree, and why a key's fields must not change after insertion. A mutated key stays in its old bucket, so `get` with an equal-looking key returns `null`.

### LinkedHashMap and LRU caches
`LinkedHashMap` can keep entries in access order. Overriding `removeEldestEntry` produces a simple least-recently-used cache.

```java
import java.util.LinkedHashMap;
import java.util.Map;

public class LruCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    public LruCache(int capacity) {
        super(16, 0.75f, true);     // true: access order
        this.capacity = capacity;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
}
```

### TreeSet and TreeMap
Both are red-black trees, so operations take O(log n). They keep elements sorted and offer navigation methods from `NavigableSet` and `NavigableMap`: `first`, `last`, `floor`, `ceiling`, `headMap`, `tailMap`, and `subMap`. They use `compareTo` or a comparator, not `equals` and `hashCode`, to decide whether two keys are the same. Keys must be comparable, and inconsistent comparators cause missing entries.

```java
import java.util.TreeMap;

public class FloorDemo {
    public static void main(String[] args) {
        TreeMap<Integer, String> grades = new TreeMap<>();
        grades.put(90, "A");
        grades.put(80, "B");
        grades.put(70, "C");
        System.out.println(grades.floorKey(85));   // 80: greatest key <= 85
        System.out.println(grades.headMap(80));    // {70=C}
    }
}
```

### Thread-safe sets and maps
- `ConcurrentHashMap` is the standard thread-safe map. It locks only the affected bins on writes, and reads usually do not lock. Atomic compound methods such as `merge` and `computeIfAbsent` are safe to use concurrently.
- `ConcurrentHashMap.newKeySet()` gives a thread-safe `Set`.
- `Collections.synchronizedMap(new HashMap<>())` wraps a map with one lock; iteration still needs manual locking.
- `ConcurrentSkipListSet` and `ConcurrentSkipListMap` are sorted concurrent alternatives.

### Iterating maps
Iterate `entrySet()` to get keys and values together. Iterating `keySet()` and calling `get` for each key does an extra lookup. `Map.forEach((k, v) -> ...)` is shorter when you do not need to remove entries.

## How it works / Step by step

1. `HashSet.add(x)` calls `HashMap.put(x, PRESENT)` internally; the set reports whether the key was new.
2. `HashMap.put` computes the hash, finds the bucket, and walks it comparing keys with `equals`.
3. If the key exists, the value is replaced and the old value is returned; if not, a node is added.
4. When the number of entries exceeds the load factor times the capacity, the table doubles and entries are redistributed.
5. `TreeMap.put` walks a balanced tree using `compareTo` or the comparator, then rebalances.

## Common pitfalls
- Using a mutable object as a key and changing it after insertion.
- Relying on `HashMap` or `HashSet` iteration order. It is unspecified and can change.
- Calling `get(key)` and unboxing the result when the key is missing, which throws `NullPointerException`.
- Using `TreeMap` with keys whose `compareTo` is inconsistent with `equals`.
- Using `Hashtable` in new code. Use `HashMap` or `ConcurrentHashMap`.
- Modifying a map while iterating it, which throws `ConcurrentModificationException`.
- Assuming `ConcurrentHashMap` makes a sequence of separate `get` and `put` calls atomic. Use `merge` or `compute` instead.

!!! tip "Interview tip"
    **Q: How would you implement a thread-safe counter per key?** Use `ConcurrentHashMap<String, LongAdder>` or `ConcurrentHashMap<String, Long>` with `merge(key, 1L, Long::sum)`. The `merge` call is atomic for that key, which avoids the race between a separate `get` and `put`. For high-contention counters, `LongAdder` spreads updates across cells.

## Quick recap
- `HashSet` and `HashMap` are the default choices, with O(1) average operations.
- `LinkedHashSet` and `LinkedHashMap` keep insertion order; `TreeSet` and `TreeMap` keep sorted order with O(log n) operations.
- Keys must have consistent `equals` and `hashCode` (or `compareTo` for trees), and must not change after insertion.
- `ConcurrentHashMap` is the thread-safe map; use its atomic `merge` and `compute` methods.
- `LinkedHashMap` with access order plus `removeEldestEntry` makes an LRU cache.

**See also:** [Collections Overview](collections-overview.md), [Ordering: Comparable and Comparator](ordering-comparable-comparator.md), [Iterators and Utilities](iterators-and-utilities.md)
