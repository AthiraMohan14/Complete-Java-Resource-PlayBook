# Iterators and Utilities

!!! note "In simple words"
    An iterator is a bookmark that walks through a collection one item at a time. If the collection changes under the bookmark in the wrong way, Java stops the walk with an error. The `Collections` class offers helper methods such as sort, shuffle, and max.

## Why it matters

Almost every program loops over collections. Doing it safely matters: changing a list while a loop reads it is one of the most common Java bugs, and interviewers use it to test whether you understand how iterators work behind the for-each loop. The `Collections` utility class is also worth knowing, because it saves you from writing sorting, searching, and wrapping code by hand.

## How it works

### The Iterator interface

`Iterator<E>` has three methods: `hasNext()`, `next()`, and an optional `remove()`. The enhanced `for` loop is shorthand for an iterator. Every `Iterable`, including all collections, provides `iterator()`.

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
                it.remove();              // the safe way to remove during iteration
            }
        }
        System.out.println(items);        // [a, b]
    }
}
```

`remove()` throws `IllegalStateException` if you call it before `next()` or twice in a row. It throws `UnsupportedOperationException` for immutable collections.

### ListIterator

`ListIterator` works only on lists. It moves in both directions, and it can replace or insert elements while you walk. Use it when you need to change elements in place.

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

Most iterators of `ArrayList`, `HashMap`, `HashSet`, and `TreeMap` are fail-fast. The collection keeps a modification counter. The iterator records that counter when it is created and checks it on each `next()`. If the collection changed in any way other than through the iterator's own `remove`, the iterator throws `ConcurrentModificationException`.

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

Fail-fast behaviour is a best-effort check that helps you find bugs. It is not a guarantee, and it is not a thread-safety feature.

### Fail-safe and weakly consistent iterators

Concurrent collections iterate in a different way:

- `CopyOnWriteArrayList` iterators walk a snapshot. They never throw `ConcurrentModificationException`, but they do not see later changes, and they do not support `remove`.
- `ConcurrentHashMap` and `ConcurrentSkipListMap` iterators are weakly consistent. They never throw `ConcurrentModificationException`. They may or may not reflect concurrent changes, and each element is returned at most once.

Choose these types when other threads change the collection while you iterate.

### Modifying during iteration: the safe options

1. Use `Iterator.remove()`.
2. Use `removeIf(predicate)`, which every `Collection` has since Java 8.
3. Collect the items to change into a second collection, then apply the change after the loop.
4. Use a concurrent collection when other threads write.

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

A class that implements `Iterable<T>` works in a for-each loop. `spliterator()` supports parallel and stream processing. The modern Java pages cover streams.

### The Collections utility class

`java.util.Collections` provides static methods that work on collections:

| Method | Purpose |
|---|---|
| `sort(list)`, `sort(list, comparator)` | Sort a list in place |
| `reverse(list)`, `shuffle(list)` | Reverse or randomize a list |
| `max(coll)`, `min(coll)` | Largest or smallest element |
| `frequency(coll, x)` | Count of occurrences of `x` |
| `unmodifiableList`, `unmodifiableSet`, `unmodifiableMap` | Read-only views |
| `synchronizedList`, `synchronizedMap` | Wrappers with a single lock |
| `emptyList()`, `singletonList(x)`, `nCopies(n, x)` | Small immutable collections |
| `swap(list, i, j)` | Swap two elements |
| `binarySearch(list, key)` | Search a sorted list |
| `addAll(coll, elements...)` | Add several elements in one call |
| `rotate(list, distance)` | Shift elements circularly |
| `fill(list, x)` | Set every position to the same value |
| `copy(dest, src)` | Copy into a destination at least as long as the source |
| `disjoint(c1, c2)` | True when the two collections share no element |
| `replaceAll(list, oldVal, newVal)` | Replace every occurrence of a value |

`Collections.sort` is stable, so equal elements keep their order. It uses TimSort for objects, and its worst case is O(n log n).

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class SortDemo {
    public static void main(String[] args) {
        List<Integer> values = new ArrayList<>(List.of(4, 1, 3));
        Collections.sort(values);                             // [1, 3, 4]
        Collections.reverse(values);                          // [4, 3, 1]
        System.out.println(Collections.max(values));          // 4
        System.out.println(Collections.frequency(values, 3)); // 1
    }
}
```

### Views versus copies

`unmodifiableList` and `subList` return views. Changes to the underlying list appear through them. `List.copyOf` and `new ArrayList<>(list)` return copies that stay the same when the original changes. Know which one an API returns, because a caller may expect a snapshot.

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

`Collections.synchronizedList` and similar wrappers lock every method call. Iteration and compound operations, such as check-then-add, still need the caller to hold the wrapper's lock. For new concurrent code, prefer `ConcurrentHashMap`, `CopyOnWriteArrayList`, or the queues in `java.util.concurrent`.

### Step by step: what happens inside

1. `iterator()` returns an object that holds a cursor and an expected modification count.
2. `hasNext()` checks whether the cursor is before the end. `next()` returns the element and moves the cursor forward.
3. For a fail-fast iterator, `next()` compares the expected count with the collection's current count and throws if they differ.
4. `Iterator.remove()` removes the last element returned and updates the expected count, so the iterator stays valid.
5. `Collections` methods work on the collection you pass in. Views forward every call to the original.

```mermaid
sequenceDiagram
    participant Loop
    participant It as Iterator
    participant List
    Loop->>It: hasNext
    It-->>Loop: true
    Loop->>It: next
    It->>List: check modCount
    List-->>It: unchanged
    It-->>Loop: element
    Loop->>It: remove
    It->>List: remove and update expected count
```

## Where it is used

- Looping over a result set and removing rejected rows with `removeIf`.
- Replacing values in place with a `ListIterator`, such as normalizing names.
- Returning `unmodifiableList` views from a domain object so callers cannot change its state.
- Using `Collections.sort`, `max`, and `frequency` for reports and small statistics.
- Choosing a weakly consistent concurrent map when a background thread updates a shared cache.

## Benefits

- The iterator protocol is the same for every collection, so loops work everywhere.
- `Iterator.remove` and `removeIf` make deletion during a walk safe and short.
- Fail-fast checks catch many accidental edits early in development.
- `Collections` offers well-tested helpers that you would otherwise write yourself.

## Cons and limits

- Fail-fast checks are not reliable. They can miss some changes, so they are no substitute for correct code.
- Fail-safe and weakly consistent iterators can show stale data, so they do not give exact counts while writers are active.
- Views share state with their source, which surprises callers who expected a snapshot.
- `Collections.synchronizedList` offers little help for iteration.

### Common pitfalls

- Calling `list.remove(x)` inside a for-each loop. It usually throws `ConcurrentModificationException`. Removing the second-to-last element can end the loop quietly instead, so the bug can hide.
- Calling `iterator.remove()` twice without a `next()` in between.
- Assuming a `CopyOnWriteArrayList` iterator sees additions made after it was created.
- Returning an `unmodifiableList` view and expecting the list to be immutable, when the underlying list is still changed elsewhere.
- Iterating a `Collections.synchronizedList` without holding its lock.
- Calling `Collections.max` on an empty collection, which throws `NoSuchElementException`.

## Best practices

1. Delete with `Iterator.remove()` or `removeIf`, never with a plain for-each loop.
2. Return `List.copyOf(...)` when callers should get a snapshot, and an unmodifiable view when they should see updates.
3. Use concurrent collections when threads share the data, and avoid manual locking around iteration.
4. Use `Collections` helpers for common work, and check for an empty collection before calling `max` or `min`.

!!! tip "Interview tip"
    **Q: Why does removing the second-to-last element in a for-each loop not throw?** The iterator's `hasNext` compares the cursor with the size. After the removal, the size equals the cursor, so the loop ends before `next()` runs the modification check. This is an implementation detail, not a guarantee. The reliable answer is to use `Iterator.remove()` or `removeIf`.

## Quick recap

- Use `Iterator.remove()` or `removeIf` to delete items while iterating.
- Fail-fast iterators throw `ConcurrentModificationException` when they detect a change. They are a bug detector, not a thread-safety tool.
- Concurrent collections use snapshot or weakly consistent iterators, and they never throw that exception.
- `Collections` provides sorting, searching, frequency, and wrapper utilities.
- Know whether a method returns a view or a copy.

## Official documentation

- [java.util.concurrent package (Java 21 API)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html)
- [Java 21 API index](https://docs.oracle.com/en/java/javase/21/docs/api/index.html)

**See also:** [Collections Overview](collections-overview.md), [Lists](lists.md), [Sets and Maps](sets-and-maps.md)
