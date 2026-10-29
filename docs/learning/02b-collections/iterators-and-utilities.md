# Iterators and Utilities

An `Iterator` is the standard way to walk a collection one element at a time and, where allowed, remove elements as you go. Interviewers ask why modifying a collection inside a for-each loop throws `ConcurrentModificationException`, what fail-fast and fail-safe mean, and which utility methods on `Collections` are worth knowing.

## Core concepts

### The Iterator interface
`Iterator<E>` has three methods: `hasNext()`, `next()`, and an optional `remove()`. The enhanced `for` loop is syntactic sugar over an iterator. Every `Iterable`, including all collections, provides `iterator()`.

```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class IteratorDemo {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>(List.of("a", "", "b"));
        Iterator<String> it = items.iterator();
        while (it.hasNext()) {
            if (it.next().isEmpty()) {
                it.remove();              // the only safe removal during iteration
            }
        }
        System.out.println(items);        // [a, b]
    }
}
```

`remove()` throws `IllegalStateException` if called before `next()` or twice in a row, and `UnsupportedOperationException` for immutable collections.

### ListIterator
`ListIterator` works only on lists. It walks in both directions, and it can set or add elements during iteration. It is the right tool for replacing elements in place.

```java
import java.util.ArrayList;
import java.util.List;
import java.util.ListIterator;

public class UpperCaseAll {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>(List.of("ana", "ben"));
        ListIterator<String> li = items.listIterator();
        while (li.hasNext()) {
            li.set(li.next().toUpperCase());   // replace each element
        }
        System.out.println(items); // [ANA, BEN]
    }
}
```

### Fail-fast iterators
Most iterators of `ArrayList`, `HashMap`, `HashSet`, and `TreeMap` are fail-fast. Each collection keeps a modification counter. The iterator records the count when created and checks it on each `next()`. If the collection changed by any means other than the iterator's own `remove`, the iterator throws `ConcurrentModificationException`.

```java
import java.util.ArrayList;
import java.util.List;

public class RemoveDuringLoop {
    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3, 4));
        for (Integer n : nums) {
            if (n == 2) {
                nums.remove(n);     // removes the value 2; the next call to next() throws
            }
        }
    }
}
```

Fail-fast is a best-effort detector for bugs, not a guarantee. It does not promise to catch every concurrent change, so do not rely on it for thread safety.

### Fail-safe and weakly consistent iterators
Concurrent collections iterate differently:

- `CopyOnWriteArrayList` iterators work on a snapshot. They never throw `ConcurrentModificationException`, but they do not see later changes and do not support `remove`.
- `ConcurrentHashMap` and `ConcurrentSkipListMap` iterators are weakly consistent. They never throw `ConcurrentModificationException`; they may or may not reflect concurrent changes, and each element is returned at most once.

Choose these when other threads modify the collection while you iterate.

### Modifying during iteration: the safe options
1. Use `Iterator.remove()`.
2. Use `removeIf(predicate)`, available on every `Collection` since Java 8.
3. Collect the items to change into a second collection, then apply the change after the loop.
4. Use a concurrent collection if other threads are writing.

```java
import java.util.ArrayList;
import java.util.List;

public class RemoveIfDemo {
    public static void main(String[] args) {
        List<String> words = new ArrayList<>(List.of("keep", "drop", "keep"));
        words.removeIf(w -> w.equals("drop"));
        System.out.println(words); // [keep, keep]
    }
}
```

For maps, `map.entrySet().removeIf(...)`, `map.values().removeIf(...)`, and `map.keySet().removeIf(...)` remove entries safely.

### Iterable and spliterators (brief)
A class that implements `Iterable<T>` can be used in a for-each loop. `spliterator()` supports parallel and stream processing. Streams are covered in the modern Java section.

### The Collections utility class
`java.util.Collections` provides static methods that operate on collections.

| Method | Purpose |
|---|---|
| `sort(list)`, `sort(list, comparator)` | Sort a list in place |
| `reverse(list)`, `shuffle(list)` | Reverse or randomize a list |
| `max(coll)`, `min(coll)` | Largest or smallest element |
| `frequency(coll, x)` | Count of occurrences of `x` |
| `unmodifiableList`, `unmodifiableSet`, `unmodifiableMap` | Read-only views |
| `synchronizedList`, `synchronizedMap` | Wrappers with a single lock |
| `emptyList()`, `singletonList(x)`, `nCopies(n, x)` | Common small immutable collections |
| `swap(list, i, j)` | Swap two elements |
| `binarySearch(list, key)` | Search a sorted list |
| `addAll(coll, elements...)` | Add several elements in one call |
| `rotate(list, distance)` | Shift elements circularly by a distance |
| `fill(list, x)` | Set every position to the same value |
| `copy(dest, src)` | Copy into a destination list at least as long as the source |
| `disjoint(c1, c2)` | True when the two collections share no element |
| `replaceAll(list, oldVal, newVal)` | Replace every occurrence of a value |

`Collections.sort` is stable: equal elements keep their relative order. It uses a merge-based algorithm (TimSort for objects), so its worst case is O(n log n).

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class SortDemo {
    public static void main(String[] args) {
        List<Integer> values = new ArrayList<>(List.of(4, 1, 3));
        Collections.sort(values);                 // [1, 3, 4]
        Collections.reverse(values);              // [4, 3, 1]
        System.out.println(Collections.max(values));           // 4
        System.out.println(Collections.frequency(values, 3));  // 1
    }
}
```

### Views versus copies
`unmodifiableList` and `subList` return views: changes to the underlying list appear through them. `List.copyOf` and `new ArrayList<>(list)` return copies that stay the same when the original changes. Know which you return from an API, because a caller may expect a snapshot.

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ViewVsCopy {
    public static void main(String[] args) {
        List<String> live = new ArrayList<>(List.of("x"));
        List<String> view = Collections.unmodifiableList(live);
        List<String> snapshot = List.copyOf(live);
        live.add("y");
        System.out.println(view.size());      // 2: the view sees the change
        System.out.println(snapshot.size());  // 1: the copy does not
    }
}
```

### Thread safety of the wrappers
`Collections.synchronizedList` and similar wrappers lock every method call, but iteration and compound operations (such as check-then-add) still need the caller to hold the lock on the wrapper while iterating. For new concurrent code, prefer `ConcurrentHashMap`, `CopyOnWriteArrayList`, or the `java.util.concurrent` queues.

## How it works / Step by step

1. `iterator()` returns an object that holds a cursor and an expected modification count.
2. `hasNext()` checks whether the cursor is before the end; `next()` returns the element and advances.
3. For a fail-fast iterator, `next()` compares the expected count with the collection's count and throws if they differ.
4. `Iterator.remove()` removes the last returned element and updates the expected count, so the iterator stays valid.
5. `Collections` methods wrap or operate on the collection passed in; views delegate every call to the original.

## Common pitfalls
- Calling `list.remove(x)` inside a for-each loop, which throws `ConcurrentModificationException` in most cases. Note that removing the second-to-last element can exit the loop silently instead of throwing.
- Calling `iterator.remove()` twice without a `next()` in between.
- Assuming `CopyOnWriteArrayList` iterators see later additions.
- Returning an `unmodifiableList` view and expecting the caller's list to be immutable when the underlying list is still modified elsewhere.
- Using `Collections.synchronizedList` and iterating without locking the wrapper.
- Calling `Collections.max` on an empty collection, which throws `NoSuchElementException`.

!!! tip "Interview tip"
    **Q: Why does removing the second-to-last element in a for-each loop not throw?** The iterator's `hasNext` checks the cursor against the size, and after the removal the size equals the cursor, so the loop ends before `next()` runs the modification check. It is a quirk of the implementation, not a guarantee. The reliable answer is to use `Iterator.remove()` or `removeIf`.

## Quick recap
- Use `Iterator.remove()` or `removeIf` to delete during iteration.
- Fail-fast iterators throw `ConcurrentModificationException` on detected changes; they are a bug detector, not a thread-safety tool.
- Concurrent collections use snapshot or weakly consistent iterators that never throw that exception.
- `Collections` provides sorting, searching, frequency, and wrapper utilities.
- Know whether a method returns a view or a copy.

**See also:** [Collections Overview](collections-overview.md), [Lists](lists.md), [Sets and Maps](sets-and-maps.md)
