# Queues and Deques

A queue holds elements waiting to be processed, and a deque (double-ended queue) can be used from both ends. Java's `Queue` interface has two main behaviours: first-in-first-out for `ArrayDeque` and `LinkedList`, and priority order for `PriorityQueue`. Interviewers use these to test whether you know which structure gives O(1) access at the ends and how to replace the legacy `Stack` class.

## Core concepts

### The Queue and Deque interfaces
`Queue` offers two forms of each operation: one that throws on failure and one that returns a special value.

| Operation | Throws on failure | Returns special value |
|---|---|---|
| Insert | `add(e)` | `offer(e)` |
| Remove head | `remove()` | `poll()` |
| Examine head | `element()` | `peek()` |

`Deque` adds the same pairs for both ends: `addFirst` / `offerFirst`, `addLast` / `offerLast`, `removeFirst` / `pollFirst`, `removeLast` / `pollLast`, `peekFirst`, and `peekLast`. Prefer `offer`, `poll`, and `peek`: they do not throw when the collection is empty or full.

### ArrayDeque
`ArrayDeque` is a resizable circular array. It is the default choice for both queues and stacks. Operations at either end are amortized O(1). It does not allow `null` elements, and it is not thread-safe.

```java
import java.util.ArrayDeque;
import java.util.Deque;

public class DequeDemo {
    public static void main(String[] args) {
        Deque<String> stack = new ArrayDeque<>();
        stack.push("a");                 // push = addFirst
        stack.push("b");
        System.out.println(stack.pop()); // b: last in, first out

        Deque<String> queue = new ArrayDeque<>();
        queue.offer("first");            // offer = addLast
        queue.offer("second");
        System.out.println(queue.poll()); // first: first in, first out
    }
}
```

`push` and `pop` operate on the head of the deque, which makes an `ArrayDeque` act as a stack. `offer` and `poll` make it a queue.

### Stack versus ArrayDeque
`Stack` extends `Vector` and inherits its synchronized, index-based methods, so it allows operations that break the stack discipline. Its methods also lock on every call. Use `Deque` with `push` and `pop` instead.

### LinkedList as a queue
`LinkedList` implements `Deque` too, so it can serve as a queue. It allows `null` elements and has extra per-node overhead. For plain queues, `ArrayDeque` is usually faster. Use `LinkedList` when you already need its `List` behaviour, such as removing through a `ListIterator`.

### PriorityQueue
`PriorityQueue` is a binary heap. `poll` always removes the least element according to the natural ordering or a comparator. It is not a sorted collection: iterating it does not produce sorted order, and only the head is guaranteed to be the minimum.

```java
import java.util.Comparator;
import java.util.PriorityQueue;

public class TaskQueue {
    record Task(String name, int priority) { }

    public static void main(String[] args) {
        PriorityQueue<Task> tasks = new PriorityQueue<>(
            Comparator.comparingInt(Task::priority));   // lowest number first

        tasks.offer(new Task("backup", 3));
        tasks.offer(new Task("alert", 1));
        tasks.offer(new Task("report", 2));

        while (!tasks.isEmpty()) {
            System.out.println(tasks.poll().name());    // alert, report, backup
        }
    }
}
```

The record `Task` is defined inside the class, so the example runs as written.

Use `PriorityQueue` for top-k problems, scheduling by priority, and merging sorted streams. Each `offer` and `poll` is O(log n), and `peek` is O(1).

### Blocking queues (brief)
For producer-consumer code between threads, the `java.util.concurrent` package provides `BlockingQueue` implementations such as `ArrayBlockingQueue` and `LinkedBlockingQueue`. Their `put` and `take` methods wait when the queue is full or empty. Concurrency is covered outside this page.

### Typical uses
- Stack: undo history, expression evaluation, depth-first traversal with an explicit stack.
- Queue: breadth-first search, request buffering, task processing in arrival order.
- Priority queue: Dijkstra's algorithm, scheduling, and finding the k largest items with a min-heap of size k.

### Choosing a queue or stack

| Need | Use | Why |
|---|---|---|
| FIFO queue | `ArrayDeque` | Constant-time at both ends, no per-node overhead |
| LIFO stack | `ArrayDeque` with `push` and `pop` | Replaces the synchronized `Stack` |
| Smallest or largest first | `PriorityQueue` | Heap gives O(log n) insert and removal of the head |
| Thread hand-off between producers and consumers | `BlockingQueue` | Blocks when full or empty |
| Queue that must hold `null` | `LinkedList` | `ArrayDeque` rejects `null` |

### Breadth-first search with a queue
Breadth-first search visits nodes level by level, and a FIFO queue gives that order. The `visited` set stops the search from looping on cycles.

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class BreadthFirst {
    public static void main(String[] args) {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("D"),
            "C", List.of("D"),
            "D", List.of());

        Set<String> visited = new HashSet<>();
        Deque<String> queue = new ArrayDeque<>();
        queue.offer("A");
        visited.add("A");

        while (!queue.isEmpty()) {
            String node = queue.poll();
            System.out.println(node);          // A, B, C, D
            for (String next : graph.get(node)) {
                if (visited.add(next)) {       // true only the first time
                    queue.offer(next);
                }
            }
        }
    }
}
```

Swapping the queue for a stack (`push` and `pop`) changes the traversal to a depth-first style, so the two structures differ by which end you remove from.

## How it works / Step by step

1. `ArrayDeque.offerLast writes at the tail index and advances it; when full, it doubles the array and copies.
2. `ArrayDeque.push` and `offerFirst` move the head index backward in the circular array.
3. `PriorityQueue.offer` appends to the array and sifts the new element up until the heap property holds.
4. `PriorityQueue.poll` removes the root, moves the last element to the root, and sifts it down.
5. Both `offer` and `poll` on `PriorityQueue` are O(log n); `peek` reads the root in O(1).

## Common pitfalls
- Using `Stack` in new code instead of `Deque`.
- Inserting `null` into an `ArrayDeque`, which throws `NullPointerException`.
- Expecting iteration over a `PriorityQueue` to return elements in sorted order.
- Using `poll` on an empty queue and forgetting that it returns `null`, which later causes a `NullPointerException` when unboxed.
- Choosing `LinkedList` for a queue out of habit.
- Mutating a priority field of an element while it is inside a `PriorityQueue`, which breaks the heap.
- Assuming `remove(Object)` on a `PriorityQueue` is O(log n); it is O(n) because it searches.

!!! tip "Interview tip"
    **Q: How do you find the k largest elements in a stream of n numbers?** Keep a min-heap (a `PriorityQueue` with natural order) of size k. For each number, add it, and if the heap grows past k, poll the smallest. The heap ends up holding the k largest values in O(n log k) time and O(k) space.

## Quick recap
- Use `offer`, `poll`, and `peek` for queues; they signal failure with `null` or `false` rather than throwing.
- `ArrayDeque` is the default for queues and stacks; `push` and `pop` operate on its head.
- `Stack` is legacy; `LinkedList` works as a deque but is heavier.
- `PriorityQueue` is a heap: the head is the minimum by its comparator, and iteration order is not sorted.
- Heap operations are O(log n); peeking at the head is O(1).

**See also:** [Lists](lists.md), [Ordering: Comparable and Comparator](ordering-comparable-comparator.md), [Collections Overview](collections-overview.md)
