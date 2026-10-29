# Lists

A `List` is an ordered collection that allows duplicates and access by index. The two common implementations, `ArrayList` and `LinkedList`, have very different performance profiles, and interviewers often ask you to pick one and justify it. This page covers each implementation, the legacy `Vector`, and the copy-on-write list used for concurrent reads.

## Core concepts

### The List interface
`List<E>` adds index-based methods to `Collection`: `get(int)`, `set(int, E)`, `add(int, E)`, `remove(int)`, `indexOf`, `subList`, and `listIterator`. Program against the interface and choose the implementation at construction.

```java
import java.util.ArrayList;
import java.util.List;

public class ListBasics {
    public static void main(String[] args) {
        List<String> tasks = new ArrayList<>();
        tasks.add("write");
        tasks.add("test");
        tasks.add(1, "review");          // insert at index 1
        System.out.println(tasks);       // [write, review, test]
        System.out.println(tasks.get(2)); // test
        tasks.remove("write");           // remove by value
        System.out.println(tasks);       // [review, test]
    }
}
```

Note the overload trap: `remove(int)` removes by index and `remove(Object)` removes by value. For a `List<Integer>`, `list.remove(1)` removes index 1, and `list.remove(Integer.valueOf(1))` removes the value 1.

### ArrayList
`ArrayList` is backed by a resizable array. Reads by index are O(1). Appending is amortized O(1): when the array is full, it grows (typically by about half) and copies the elements. Inserting or removing in the middle shifts elements, which is O(n).

```java
import java.util.ArrayList;
import java.util.List;

public class ListCapacity {
    public static void main(String[] args) {
        List<Integer> numbers = new ArrayList<>(100);   // initial capacity hint
        for (int i = 0; i < 5; i++) {
            numbers.add(i * i);
        }
        System.out.println(numbers.get(3));   // 9
    }
}
```

Use `ArrayList` as the default list. It has good cache locality, and most workloads are dominated by iteration and indexed reads.

### LinkedList
`LinkedList` is a doubly linked list of nodes, and it also implements `Deque`. Adding or removing at the ends is O(1). Getting by index walks the list, so it is O(n). Each node carries extra memory for two references, and the nodes are scattered in memory, so iteration is usually slower than `ArrayList` in practice.

Choose `LinkedList` mainly when you need a `Deque` interface with both-end operations; otherwise prefer `ArrayDeque` for a queue or stack.

### Iterating while removing
Removing inside a for-each loop throws `ConcurrentModificationException`. Use `Iterator.remove()` or `removeIf`.

```java
import java.util.ArrayList;
import java.util.List;

public class RemoveEmpty {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("ana", "", "ben", ""));
        names.removeIf(String::isEmpty);         // safe, and concise
        System.out.println(names);               // [ana, ben]
    }
}
```

### Vector
`Vector` is an older, synchronized version of `ArrayList`. Each method takes a lock, which is slower in single-threaded code and does not make compound operations atomic. New code should use `ArrayList`. Use `Collections.synchronizedList` or a concurrent collection when you need thread safety.

### CopyOnWriteArrayList
`CopyOnWriteArrayList` is thread-safe. Every write copies the whole underlying array, so writes are expensive. Reads and iteration never lock and see a stable snapshot, so it suits lists that are read far more often than they change, such as a list of listeners.

```java
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public class Listeners {
    public static void main(String[] args) {
        List<String> listeners = new CopyOnWriteArrayList<>();
        listeners.add("audit");
        for (String l : listeners) {       // iterates over a snapshot; no exception on concurrent add
            System.out.println(l);
        }
    }
}
```

Iterators of a `CopyOnWriteArrayList` do not support `remove`, and they do not reflect changes made after they were created.

### Unmodifiable and fixed-size lists
- `List.of(...)` and `List.copyOf(...)` return unmodifiable lists that reject `null`.
- `Arrays.asList(...)` returns a fixed-size list backed by the array. `set` works, `add` and `remove` throw `UnsupportedOperationException`.
- `Collections.unmodifiableList(list)` returns a read-only view. Changes to the underlying list still show through the view.

### Sorting lists
`list.sort(comparator)` sorts in place. Pass `null` to sort by natural order (the elements must implement `Comparable`). `Collections.sort` does the same thing for a list.

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class SortByLength {
    public static void main(String[] args) {
        List<String> words = new ArrayList<>(List.of("pear", "fig", "apple"));
        words.sort(Comparator.comparing(String::length).thenComparing(Comparator.naturalOrder()));
        System.out.println(words); // [fig, pear, apple]
    }
}
```

This example needs `java.util.Comparator`. Ordering is covered in detail on the ordering page.

## How it works / Step by step

1. `ArrayList.add` appends to the backing array. If the array is full, it allocates a larger one and copies.
2. `ArrayList.add(i, x)` shifts elements from index `i` to the end by one, then stores `x`.
3. `LinkedList.get(i)` starts at the nearer end and follows `next` or `prev` references until it reaches index `i`.
4. `CopyOnWriteArrayList.add` copies the array, adds the element to the copy, and publishes the copy.
5. `ArrayList` iterators check a modification counter and throw `ConcurrentModificationException` if the list changed outside the iterator.

## Common pitfalls
- Using `LinkedList` for indexed access. The cost is O(n) per call, so a loop becomes O(n²).
- Calling `remove(int)` when you meant to remove a value, with `List<Integer>`.
- Removing elements inside a for-each loop.
- Assuming `Arrays.asList` returns a normal, resizable list.
- Using `CopyOnWriteArrayList` for a write-heavy list, where each write copies the array.
- Expecting `Vector` to be thread-safe for compound operations such as check-then-add.
- Forgetting the initial capacity hint when you know the size, which causes repeated copies.

!!! tip "Interview tip"
    **Q: When would you choose `LinkedList` over `ArrayList`?** Rarely. `ArrayList` wins for most index-based and iteration workloads. Only consider `LinkedList` when you need frequent insertion or removal at a position you already hold through a `ListIterator`, and even then measure first. For queues and stacks, use `ArrayDeque`.

## Quick recap
- `List` is ordered, allows duplicates, and supports indexed access.
- `ArrayList` is the default: O(1) reads by index, amortized O(1) appends, O(n) middle inserts.
- `LinkedList` is O(1) at the ends but O(n) by index; it is rarely the right choice for lists.
- `CopyOnWriteArrayList` gives lock-free iteration for read-heavy, rarely changed lists.
- Use `removeIf` or `Iterator.remove()` to delete while iterating.

**See also:** [Collections Overview](collections-overview.md), [Queues and Deques](queues-and-deques.md), [Iterators and Utilities](iterators-and-utilities.md)
