# Stacks & Queues

Stacks and queues are restricted lists: a stack removes the most recently added item, and a queue removes the oldest. Interviewers ask about them because they model real work such as parsing, undo history, and scheduling. Many harder problems use a **monotonic** stack or deque, which keeps items in sorted order to answer "next greater" or "window maximum" questions in linear time.

## Core concepts

### Stack: last in, first out
The operations are `push`, `pop`, and `peek`. Each is O(1). In Java, use `Deque<Integer> stack = new ArrayDeque<>();` and call `push`, `pop`, and `peek`, which work at the head of the deque.

Avoid `java.util.Stack`. It is a legacy class that extends `Vector`, so every method is synchronized, and it adds an index-based API that a stack does not need. `ArrayDeque` is the usual replacement.

```java
import java.util.ArrayDeque;
import java.util.Deque;

public class StackDemo {
    public static void main(String[] args) throws Exception {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(1);
        stack.push(2);
        int top = stack.peek();   // 2, not removed
        int popped = stack.pop(); // 2
    }
}
```

### Queue: first in, first out
The operations are `offer` (add at the back), `poll` (remove from the front), and `peek`. In Java, `ArrayDeque` also works as a queue. Prefer `offer` and `poll`. When the queue is empty, `poll` and `peek` return `null`, while `remove` and `element` throw `NoSuchElementException`.

```java
import java.util.ArrayDeque;
import java.util.Queue;

public class QueueDemo {
    public static void main(String[] args) throws Exception {
        Queue<String> queue = new ArrayDeque<>();
        queue.offer("first");
        queue.offer("second");
        String next = queue.poll();   // "first"
    }
}
```

### Array-based and linked-list-based implementations
An array-backed stack stores items in an array with a `top` index. It is simple and cache-friendly, but it has a fixed capacity unless you resize it. A linked-list stack pushes and pops at the head, so both operations are O(1) and capacity grows without copying.

A fixed-size queue needs a circular array. Without wrap-around, the array fills up even when slots at the front are free.

```java
import java.util.NoSuchElementException;

public class ArrayQueueDemo {
    static final class ArrayQueue {
        private final int[] data;
        private int head;   // index of the front element
        private int size;

        ArrayQueue(int capacity) {
            data = new int[capacity];
        }

        boolean offer(int x) {
            if (size == data.length) {
                return false;                       // full
            }
            data[(head + size) % data.length] = x;  // wrap around
            size++;
            return true;
        }

        int poll() {
            if (size == 0) {
                throw new NoSuchElementException();
            }
            int x = data[head];
            head = (head + 1) % data.length;
            size--;
            return x;
        }
    }
}
```

Each operation is O(1) time and O(1) extra space.

### Applications: matching brackets
A stack matches the most recent unmatched opener with each closer. This is the standard "valid parentheses" check.

```java
import java.util.*;

public class Brackets {
    static boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') {
                stack.push(c);
            } else {
                if (stack.isEmpty()) {
                    return false;
                }
                char open = stack.pop();
                if ((c == ')' && open != '(')
                        || (c == ']' && open != '[')
                        || (c == '}' && open != '{')) {
                    return false;
                }
            }
        }
        return stack.isEmpty();   // leftover openers mean unmatched
    }
}
```

Time is O(n) and space is O(n) in the worst case.

### Monotonic stack
A monotonic stack keeps its elements in increasing or decreasing order. When a new value breaks the order, the values it dominates are popped, and each pop records an answer. Every index is pushed and popped at most once, so the total time is O(n).

The classic problem is **next greater element**: for each position, find the first later value that is larger. The stack holds indices whose values are still waiting for a larger value.

```java
import java.util.*;

public class NextGreater {
    static int[] nextGreater(int[] a) {
        int[] res = new int[a.length];
        Arrays.fill(res, -1);                         // -1 when no greater value exists
        Deque<Integer> stack = new ArrayDeque<>();    // indices, values kept decreasing
        for (int i = 0; i < a.length; i++) {
            while (!stack.isEmpty() && a[stack.peek()] < a[i]) {
                res[stack.pop()] = a[i];              // a[i] is the next greater for the popped index
            }
            stack.push(i);
        }
        return res;
    }
}
```

This needs `import java.util.Arrays;` and `import java.util.Deque;` with `ArrayDeque`. Time is O(n) and space is O(n).

### Monotonic deque: sliding window maximum
A monotonic deque applies the same idea to a window. Keep indices whose values decrease from front to back. The front is always the maximum of the current window. Drop the front when it leaves the window, and drop the back whenever a new value is at least as large.

```java
import java.util.*;

public class SlidingWindowMax {
    static int[] maxSlidingWindow(int[] a, int k) {
        int n = a.length;
        int[] res = new int[n - k + 1];
        Deque<Integer> dq = new ArrayDeque<>();      // indices, values decreasing
        for (int i = 0; i < n; i++) {
            while (!dq.isEmpty() && dq.peekFirst() <= i - k) {
                dq.pollFirst();                      // front index left the window
            }
            while (!dq.isEmpty() && a[dq.peekLast()] <= a[i]) {
                dq.pollLast();                       // back values can never be the maximum again
            }
            dq.offerLast(i);
            if (i >= k - 1) {
                res[i - k + 1] = a[dq.peekFirst()];
            }
        }
        return res;
    }
}
```

It assumes `1 <= k <= a.length`. Time is O(n), because each index enters and leaves the deque once.

### Trapping rain water
Water above a bar depends on the lower of the tallest bars on its left and right. A monotonic stack fills the basin one layer at a time: when a taller bar arrives, the popped bar is the bottom of a basin bounded by the stack top and the new bar.

```java
import java.util.*;

public class RainWater {
    static int trap(int[] h) {
        Deque<Integer> stack = new ArrayDeque<>();   // indices with non-increasing heights
        int water = 0;
        for (int i = 0; i < h.length; i++) {
            while (!stack.isEmpty() && h[i] > h[stack.peek()]) {
                int bottom = stack.pop();
                if (stack.isEmpty()) {
                    break;                           // no left wall
                }
                int left = stack.peek();
                int width = i - left - 1;
                int boundedHeight = Math.min(h[left], h[i]) - h[bottom];
                water += width * boundedHeight;
            }
            stack.push(i);
        }
        return water;
    }
}
```

Time is O(n) and space is O(n). A two-pointer solution also runs in O(n) with O(1) extra space, and it is worth knowing as a follow-up.

### Priority queue
`PriorityQueue` is a binary heap. `offer` and `poll` are O(log n), `peek` is O(1), and building a queue from a collection is O(n). Iterating over it does not return elements in sorted order, only `poll` does.

For a "k smallest" problem, keep a max-heap of size k. Each time it grows past k, remove the largest.

```java
import java.util.*;

public class KSmallest {
    static int[] kSmallest(int[] a, int k) {
        PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Comparator.reverseOrder());
        for (int x : a) {
            maxHeap.offer(x);
            if (maxHeap.size() > k) {
                maxHeap.poll();                  // drop the largest of the candidates
            }
        }
        int[] res = new int[maxHeap.size()];
        int i = 0;
        for (int x : maxHeap) {
            res[i++] = x;                        // unordered result
        }
        return res;
    }
}
```

This is O(n log k) time and O(k) space, which beats sorting when k is much smaller than n.

## How it works / Step by step

1. Ask whether the problem asks about the most recent item (stack), the oldest item (queue), or a window (deque).
2. For "next greater", "previous smaller", or span questions, write down what the stack holds and what triggers a pop.
3. Store indices instead of values when you need distances or window bounds.
4. For a window, check the front against the window's left edge before you read the answer.
5. Trace a small example, such as `[2, 1, 5, 6, 2, 3]`, through each push and pop.

| Problem type | Structure | Time |
|---|---|---|
| Matching or nesting | Stack | O(n) |
| Next greater or smaller | Monotonic stack | O(n) |
| Sliding window maximum or minimum | Monotonic deque | O(n) |
| Top k of a stream | Heap of size k | O(n log k) |
| Breadth-first ordering | Queue | O(n) over the input |

## Common pitfalls

- Using `java.util.Stack` in new code. Use `ArrayDeque`.
- Using `pop` or `peek` on an empty deque. Check `isEmpty()` first.
- Storing values in a monotonic stack when you need indices. Two different positions can hold equal values.
- Using `<` where the problem needs `<=`, or the reverse, which changes the answer when values repeat.
- Forgetting to remove the expired index from the front of a sliding window deque.
- Assuming a `PriorityQueue` iterates in sorted order.
- Passing an `int` to `PriorityQueue.remove` expecting an index. It removes by value.

!!! tip "Interview tip"
    **Q: Why is a monotonic stack O(n) even though it has a `while` loop inside a `for` loop?**
    A: Every index is pushed once and popped at most once, so the total number of pops across the whole run is at most n. The inner loop does not repeat work for the same index.

## Quick recap

- Use `ArrayDeque` for stacks and queues. Avoid `java.util.Stack`.
- Stack operations are O(1). A queue needs a circular array when fixed-size.
- A monotonic stack answers next-greater and span questions in O(n).
- A monotonic deque gives the window maximum in O(n).
- A heap of size k gives the top k in O(n log k).

**See also:** [Arrays & Strings](arrays-strings.md), [Linked Lists](linked-lists.md), [Trees](trees.md), [DSA Foundations](index.md)
