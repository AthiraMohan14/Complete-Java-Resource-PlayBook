# Sets and Maps

A `Set` holds unique elements, and a `Map` holds key-value pairs with unique keys. Both are used constantly, and both come in hash-based, insertion-ordered, sorted, and thread-safe variants. Interviewers ask which implementation to choose, how `HashMap` locates a key, how it grows, and why a mutable key can break a map.

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
        List<String> input = List.of("pear", "apple", "pear", "fig");

        Set<String> hash = new HashSet<>(input);
        Set<String> ordered = new LinkedHashSet<>(input);
        Set<String> sorted = new TreeSet<>(input);

        System.out.println(ordered);     // [pear, apple, fig]
        System.out.println(sorted);      // [apple, fig, pear]
        System.out.println(hash.size()); // 3
    }
}
```

The duplicate `pear` is dropped by every set. The order of `HashSet` output is not something to rely on.

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
        stock.merge("pen", 5, Integer::sum);   // pen becomes 15
        stock.computeIfAbsent("ink", k -> 0);  // adds ink -> 0
        stock.putIfAbsent("pad", 99);          // no change: pad exists

        System.out.println(stock.getOrDefault("cup", 0)); // 0
        for (Map.Entry<String, Integer> e : stock.entrySet()) {
            System.out.println(e.getKey() + " = " + e.getValue());
        }
    }
}
```

Prefer `merge`, `computeIfAbsent`, and `getOrDefault` over the older check-then-put pattern. They are shorter, and on `ConcurrentHashMap` they are atomic.

### How HashMap finds a key
1. The key's `hashCode()` is computed and spread (mixed) so that high bits influence the bucket index.
2. The hash selects a bucket in an internal array.
3. Within the bucket, `equals()` finds the matching key.
4. If a bucket grows long, its entries become a balanced tree (Java 8 and later), which bounds the cost of a lookup inside that bucket.

This is why `hashCode` and `equals` must agree, and why a key's fields must not change after insertion. A mutated key stays in its old bucket, so `get` with an equal-looking key returns `null`.

### Capacity, load factor, and resizing
A `HashMap` keeps an array of buckets. Four numbers describe its growth:

- **Capacity:** the number of buckets. The default is 16, and the array is allocated on the first insertion.
- **Load factor:** the fraction of buckets that may fill before the map grows. The default is 0.75, which balances memory against collisions.
- **Threshold:** capacity multiplied by load factor. With the defaults it is 12, so the 13th entry triggers a resize.
- **Rehashing:** when the threshold is crossed, the map allocates an array of double the capacity and moves every entry into it. The cost is O(n) for that one insert, but the amortized cost of `put` stays O(1).

A lower load factor resizes sooner, which means fewer collisions and more memory. A higher one saves memory and risks longer buckets. If you know the size in advance, pass an initial capacity so that no resize happens while you fill the map.

```java
import java.util.HashMap;
import java.util.Map;

public class PresizedMap {
    public static void main(String[] args) {
        int expected = 1_000;
        // Leave headroom so that 1,000 entries stay below the 0.75 threshold.
        Map<Integer, String> byId = new HashMap<>((int) (expected / 0.75f) + 1);
        for (int i = 0; i < expected; i++) {
            byId.put(i, "item-" + i);
        }
        System.out.println(byId.size()); // 1000
    }
}
```

### Collisions and tree bins
Two different keys can share a bucket. Java handles this with a linked chain. When one chain reaches 8 nodes and the table has at least 64 buckets, the chain is converted to a red-black tree. If the table is smaller, the map resizes instead. Good `hashCode` distribution keeps chains short in the first place, which is more important than the tree fallback.

### LinkedHashMap and LRU caches
`LinkedHashMap` can keep entries in access order. Overriding `removeEldestEntry` produces a simple least-recently-used cache.

```java
import java.util.LinkedHashMap;
import java.util.Map;

public class LruCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    public LruCache(int capacity) {
        super(16, 0.75f, true);   // true: access order
        this.capacity = capacity;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
}
```

### TreeSet and TreeMap
Both are red-black trees, so the core operations take O(log n). They keep elements sorted and offer navigation methods from `NavigableSet` and `NavigableMap`: `first`, `last`, `floor`, `ceiling`, `headMap`, `tailMap`, and `subMap`. They use `compareTo` or a comparator, not `equals` and `hashCode`, to decide whether two keys are the same. Keys must be comparable, and an inconsistent comparator makes entries disappear.

```java
import java.util.TreeMap;

public class FloorDemo {
    public static void main(String[] args) {
        TreeMap<Integer, String> grades = new TreeMap<>();
        grades.put(90, "A");
        grades.put(80, "B");
        grades.put(70, "C");
        System.out.println(grades.floorKey(85)); // 80: greatest key <= 85
        System.out.println(grades.headMap(80));  // {70=C}
    }
}
```

## ConcurrentHashMap

`ConcurrentHashMap` is the standard map for several threads that read and write at the same time. It avoids a single lock over the whole map, so threads working on different keys rarely wait for each other.

### Internal structure (Java 8 and later)
The map is an array of bins, the same shape as `HashMap`. The difference is in how writers coordinate:

- An empty bin is filled with a compare-and-set operation, so no lock is taken.
- A bin that already holds entries is locked with `synchronized` on its head node. Writers to different bins do not block each other.
- Reads normally take no lock. They see the most recent values that have been fully published.
- Resizing is shared out among threads that try to write while the table grows.

Older versions (Java 7 and before) split the map into segments, each with its own lock. That design was replaced in Java 8, so an answer that mentions segments is out of date.

```text
HashMap: one structure, any write needs the caller to hold a lock
ConcurrentHashMap: many bins, each write locks only its own bin
  bin 0   bin 1   bin 2   bin 3   bin 4
   (a)     (b)     (c)     (d)     (e)
  Thread 1 writes bin 1, thread 2 writes bin 3, at the same time.
```

### Basic usage
```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ChmBasics {
    public static void main(String[] args) {
        // initial capacity 16, load factor 0.75, expected concurrency 4
        Map<String, Integer> prices = new ConcurrentHashMap<>(16, 0.75f, 4);

        prices.put("tea", 3);
        prices.put("cake", 5);
        prices.replace("tea", 4);
        prices.remove("cake");

        System.out.println(prices.get("tea")); // 4
        // Iterating while other threads write is safe; no external lock is needed.
        prices.forEach((item, cost) -> System.out.println(item + " costs " + cost));
    }
}
```

The three constructor arguments are hints. The concurrency level is no longer used for locking in Java 8 and later; treat it as a sizing hint only.

### Atomic compound operations
Single calls like `putIfAbsent`, `replace(key, old, new)`, `computeIfAbsent`, `computeIfPresent`, `compute`, and `merge` are atomic for one key. The function you pass runs while the bin is held, so keep it short and do not call back into the same map for other keys.

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ChmAtomic {
    public static void main(String[] args) {
        Map<String, Integer> scores = new ConcurrentHashMap<>();

        scores.putIfAbsent("ana", 0);                       // only if missing
        scores.replace("ana", 0, 10);                       // only if still 0
        scores.computeIfPresent("ana", (k, v) -> v + 5);    // ana -> 15
        scores.computeIfAbsent("ben", k -> 7);              // ben -> 7
        int bonus = scores.getOrDefault("cy", -1);          // -1: no entry

        System.out.println(scores + " bonus=" + bonus);
    }
}
```

### Thread-safe counter
A check-then-act sequence is not atomic even on a concurrent map:

```java
import java.util.HashMap;
import java.util.Map;

class UnsafeCounter {

    public static void main(String[] args) {
        Map<String, Integer> map = new HashMap<>();
        map.put("count", 0);

        // Not safe: two threads can read the same value and both write value + 1.
        Integer current = map.get("count");
        map.put("count", current + 1);
    }
}
```

Use one atomic call instead. `merge` adds the value with a function that runs under the bin lock:

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class SafeCounter {
    public static void main(String[] args) throws InterruptedException {
        Map<String, Integer> counts = new ConcurrentHashMap<>();
        Runnable work = () -> {
            for (int i = 0; i < 1_000; i++) {
                counts.merge("count", 1, Integer::sum);
            }
        };
        Thread a = new Thread(work);
        Thread b = new Thread(work);
        a.start();
        b.start();
        a.join();
        b.join();
        System.out.println(counts.get("count")); // 2000, every time
    }
}
```

For a very hot counter, `java.util.concurrent.atomic.LongAdder` spreads updates over several cells and is faster under heavy contention.

### Performance and comparison with a synchronized map
`Collections.synchronizedMap(new HashMap<>())` wraps every call in one lock, so only one thread makes progress at a time. Under contention, `ConcurrentHashMap` lets threads that touch different bins run in parallel. The gap grows with the number of threads and writes. Measure on your own workload rather than quoting a benchmark figure; the result depends on hardware, key distribution, and the JVM.

| Aspect | `Collections.synchronizedMap` | `ConcurrentHashMap` |
|---|---|---|
| Locking | One lock for the whole map | Per-bin locks; reads usually lock-free |
| Concurrency | One thread at a time | Many threads on different bins |
| Iteration | Caller must lock the wrapper | Safe; weakly consistent |
| Compound actions | Caller must lock | `merge`, `compute`, `computeIfAbsent` are atomic per key |
| Null keys or values | Allowed | Rejected with `NullPointerException` |
| Best fit | Low contention, simple code | Frequent concurrent reads and writes |

### Iteration is weakly consistent
Iterators of a `ConcurrentHashMap` never throw `ConcurrentModificationException`. An iterator reflects some state of the map at or after the moment it was created, so it may or may not see an entry that another thread adds while it runs. Each entry is returned at most once. Use this when you can accept a slightly stale view; do not use it to compute an exact total while writers are active.

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class WeaklyConsistent {
    public static void main(String[] args) throws InterruptedException {
        Map<String, Integer> map = new ConcurrentHashMap<>();
        Thread writer = new Thread(() -> {
            for (int i = 1; i <= 3; i++) {
                map.put("slot-" + i, i);
            }
        });
        writer.start();
        for (String slot : map.keySet()) {  // may print 0 to 3 keys, never throws
            System.out.println("seen " + slot);
        }
        writer.join();
    }
}
```

### Example: a small TTL cache
A cache that expires entries after a fixed time needs the value and its timestamp to be read together. Storing both in one immutable record keeps that read consistent.

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class TtlCache<K, V> {
    private record Entry<T>(T value, long storedAtMillis) { }

    private final Map<K, Entry<V>> entries = new ConcurrentHashMap<>();
    private final long maxAgeMillis;

    public TtlCache(long maxAgeMillis) {
        this.maxAgeMillis = maxAgeMillis;
    }

    public void put(K key, V value) {
        entries.put(key, new Entry<>(value, System.currentTimeMillis()));
    }

    public V get(K key) {
        Entry<V> entry = entries.get(key);
        if (entry == null) {
            return null;
        }
        if (System.currentTimeMillis() - entry.storedAtMillis() > maxAgeMillis) {
            entries.remove(key, entry);     // remove only if unchanged since we read it
            return null;
        }
        return entry.value();
    }

    public int size() {
        return entries.size();
    }

    public static void main(String[] args) {
        TtlCache<String, String> cache = new TtlCache<>(60_000); // one minute
        cache.put("user:1", "Ana");
        System.out.println(cache.get("user:1")); // Ana
    }
}
```

The expired entries are removed lazily, when someone asks for them. A production cache would also sweep old entries and bound its size.

### Other thread-safe options
- `ConcurrentHashMap.newKeySet()` gives a thread-safe `Set` backed by a `ConcurrentHashMap`. The JDK has no `ConcurrentHashSet` class.
- `ConcurrentSkipListSet` and `ConcurrentSkipListMap` are sorted concurrent alternatives.
- `Collections.synchronizedMap` is fine for simple cases; iteration still needs manual locking.

### Iterating maps
Iterate `entrySet()` to get keys and values together. Iterating `keySet()` and calling `get` for each key does an extra lookup. `Map.forEach((k, v) -> ...)` is shorter when you do not need to remove entries.

## How it works / Step by step

1. `HashSet.add(x)` calls `HashMap.put(x, PRESENT)` internally; the set reports whether the key was new.
2. `HashMap.put` computes the hash, finds the bucket, and walks it comparing keys with `equals`.
3. If the key exists, the value is replaced and the old value is returned; if not, a node is added.
4. When the number of entries passes the threshold (capacity times load factor), the table doubles and entries are redistributed.
5. `TreeMap.put` walks a balanced tree using `compareTo` or the comparator, then rebalances.
6. `ConcurrentHashMap.put` locks only the bin it writes to, after using a compare-and-set when the bin is empty.

## Common pitfalls
- Using a mutable object as a key and changing it after insertion.
- Relying on `HashMap` or `HashSet` iteration order. It is unspecified and can change.
- Calling `get(key)` and unboxing the result when the key is missing, which throws `NullPointerException`.
- Using `TreeMap` with keys whose `compareTo` is inconsistent with `equals`.
- Using `Hashtable` in new code. Use `HashMap` or `ConcurrentHashMap`.
- Modifying a `HashMap` while iterating it, which throws `ConcurrentModificationException`.
- Assuming `ConcurrentHashMap` makes a separate `get` followed by `put` atomic. Use `merge` or `compute`.
- Calling `put` with a `null` key or value on a `ConcurrentHashMap`.

!!! tip "Interview tip"
    **Q: How would you implement a thread-safe counter per key?** Use `ConcurrentHashMap<String, Long>` with `merge(key, 1L, Long::sum)`. The `merge` call is atomic for that key, which avoids the race between a separate `get` and `put`. For a single very hot counter, `LongAdder` spreads the updates across cells.

## Quick recap
- `HashSet` and `HashMap` are the default choices, with O(1) average operations.
- `LinkedHashSet` and `LinkedHashMap` keep insertion order; `TreeSet` and `TreeMap` keep sorted order with O(log n) operations.
- `HashMap` grows at capacity times load factor (12 for the default 16 buckets) and doubles.
- Keys must have consistent `equals` and `hashCode` (or `compareTo` for trees), and must not change after insertion.
- `ConcurrentHashMap` locks per bin, rejects nulls, and is weakly consistent when iterated; use `merge` and `compute` for atomic updates.

**See also:** [Collections Overview](collections-overview.md), [Ordering: Comparable and Comparator](ordering-comparable-comparator.md), [Iterators and Utilities](iterators-and-utilities.md)
