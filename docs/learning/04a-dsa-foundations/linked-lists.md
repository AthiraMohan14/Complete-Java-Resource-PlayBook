# Linked Lists

A linked list is a chain of nodes, where each node holds a value and a reference to the next node. Interviewers use linked-list questions to test pointer handling: whether you can reverse links safely, find a cycle without extra memory, and keep track of the head when it changes. Most of these problems are short to code but easy to get wrong.

## Core concepts

### Node structure
Each list uses a node type. The examples on this page assume the following class, nested in a `ListDemo` class.

```java
public class ListDemo {

    static final class Node {
        int val;
        Node next;

        Node(int val) {
            this.val = val;
        }
    }
}
```

A list is identified by its `head`. If the head changes during an operation, the function must return the new head.

### Singly, doubly, and circular lists
- **Singly linked:** each node has one `next` reference. You can traverse forward only. Insert and delete at a known node are O(1) once you have the previous node.
- **Doubly linked:** each node also has a `prev` reference. Deleting a known node is O(1) without searching for its predecessor. The cost is extra memory per node.
- **Circular:** the last node points back to the head, either in a singly or a doubly linked list. Traversal needs a stop condition, usually returning to the start node.

Access by index is O(n) in all three, because you must walk from the head.

```java
public class DoublyLinkedNodes {
    // Doubly linked node: prev lets you unlink a known node in O(1).
    static final class DNode {
        int val;
        DNode prev;
        DNode next;

        DNode(int val) {
            this.val = val;
        }
    }
}
```

In the JDK, `java.util.LinkedList` is a doubly linked list that also implements `Deque`. In practice, `ArrayDeque` is faster for stack and queue use, and `ArrayList` is faster for index access. Use `LinkedList` mainly when you need cheap insertion through an iterator.

### Insert, delete, and reverse
Reversal is the most common linked-list task. Keep three references: `prev`, `curr`, and `next`. Save `next` before you change `curr.next`, or you lose the rest of the list.

```java
import java.util.*;

public class ReverseList {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    static Node reverse(Node head) {
        Node prev = null;
        Node curr = head;
        while (curr != null) {
            Node next = curr.next;   // save the rest of the list
            curr.next = prev;        // flip the link
            prev = curr;             // advance prev
            curr = next;             // advance curr
        }
        return prev;                 // prev is the new head
    }
}
```

Time is O(n) and extra space is O(1). The recursive version uses O(n) stack space, so mention that trade-off if you use it.

### Dummy nodes
A dummy (sentinel) node placed before the head removes special cases. When the first real node might be deleted or replaced, return `dummy.next` at the end.

```java
import java.util.*;

public class NthFromEnd {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    static Node removeNthFromEnd(Node head, int n) {
        Node dummy = new Node(0);
        dummy.next = head;
        Node fast = dummy;
        Node slow = dummy;
        for (int i = 0; i <= n; i++) {   // move fast n + 1 steps ahead
            fast = fast.next;
        }
        while (fast != null) {           // keep the gap; slow stops before the target
            fast = fast.next;
            slow = slow.next;
        }
        slow.next = slow.next.next;      // unlink the target
        return dummy.next;
    }
}
```

This needs one pass and O(1) extra space. It assumes `1 <= n <= length`. Without the dummy, removing the head needs a separate branch.

### Fast and slow pointers
Move one pointer by one step and another by two. This pattern finds the middle node, detects cycles, and locates the start of a cycle.

```java
import java.util.*;

public class MiddleNode {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    // Returns the middle node. For an even count, returns the second of the two middles.
    static Node middle(Node head) {
        Node slow = head;
        Node fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        return slow;
    }
}
```

### Cycle detection (Floyd's algorithm)
If a list has a cycle, the fast pointer eventually meets the slow pointer inside it. If there is no cycle, the fast pointer reaches `null`.

```java
import java.util.*;

public class CycleCheck {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    static boolean hasCycle(Node head) {
        Node slow = head;
        Node fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                return true;
            }
        }
        return false;
    }
}
```

To find where the cycle starts, reset one pointer to the head after they meet, then move both one step at a time. They meet at the cycle entry.

```java
import java.util.*;

public class CycleStart {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    static Node cycleStart(Node head) {
        Node slow = head;
        Node fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                Node p = head;
                while (p != slow) {
                    p = p.next;
                    slow = slow.next;
                }
                return p;
            }
        }
        return null;   // no cycle
    }
}
```

Both versions are O(n) time and O(1) space. Compare this with a `HashSet` of visited nodes, which is also O(n) time but uses O(n) space.

### Merging sorted lists
Use a dummy node as the tail anchor, then attach whichever node is smaller.

```java
import java.util.*;

public class MergeLists {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    static Node merge(Node a, Node b) {
        Node dummy = new Node(0);
        Node tail = dummy;
        while (a != null && b != null) {
            if (a.val <= b.val) {
                tail.next = a;
                a = a.next;
            } else {
                tail.next = b;
                b = b.next;
            }
            tail = tail.next;
        }
        tail.next = (a != null) ? a : b;   // attach the leftover part
        return dummy.next;
    }
}
```

This is O(n + m) time and O(1) extra space, because it reuses the existing nodes.

### Removing duplicates and partitioning
In a sorted list, duplicates are adjacent. Skip the next node whenever its value matches the current node.

```java
import java.util.*;

public class DedupeSorted {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }


    static Node dedupeSorted(Node head) {
        Node cur = head;
        while (cur != null && cur.next != null) {
            if (cur.val == cur.next.val) {
                cur.next = cur.next.next;   // drop the duplicate
            } else {
                cur = cur.next;
            }
        }
        return head;
    }
}
```

For partitioning around a value, build two lists, one for values less than `x` and one for the rest, then join them. Reordering problems follow the same pattern: split, transform, and reconnect.

## How it works / Step by step

1. Draw the list on paper with arrows and label `head`, `prev`, `curr`, and `next`.
2. Decide whether the head can change. If it can, use a dummy node.
3. Before every reassignment of a `next` link, make sure the node it used to point to is still reachable.
4. Test with an empty list, a one-node list, and a two-node list. Most pointer bugs show up in these.
5. For cycle problems, state which pointer moves faster and why they must meet.

| Task | Technique | Time | Extra space |
|---|---|---|---|
| Reverse | Three pointers | O(n) | O(1) |
| Middle | Fast and slow | O(n) | O(1) |
| Cycle detection | Floyd | O(n) | O(1) |
| Cycle start | Floyd, then reset one pointer | O(n) | O(1) |
| Merge sorted | Dummy tail | O(n + m) | O(1) |
| Remove nth from end | Gap of n between pointers | O(n) | O(1) |

## Common pitfalls

- Setting `curr.next = prev` before saving `curr.next`, which loses the rest of the list.
- Forgetting to return the new head after reversal or deletion of the head.
- Dereferencing `null` in `fast.next.next`. Always check `fast != null && fast.next != null` first.
- Comparing values with `==` when the values are `Integer` objects. Use `.equals` for boxed types. The examples above use `int`, where `==` is correct.
- Using `java.util.LinkedList.get(i)` inside a loop, which makes the loop O(n²).
- Forgetting to break the link when you remove a node from a circular list, which leaves the loop intact.

!!! tip "Interview tip"
    **Q: How do you find the middle of a singly linked list in one pass?**
    A: Use two pointers. The slow pointer moves one step and the fast pointer moves two. When the fast pointer reaches the end, the slow pointer is at the middle. You do not need the length.

## Quick recap

- A linked list gives O(1) insert and delete at a known node, and O(n) access by index.
- Reversal uses three pointers and must save `next` before changing it.
- A dummy node removes special cases when the head might change.
- Floyd's fast and slow pointers detect cycles in O(n) time and O(1) space.
- Use `ArrayDeque` in Java for stack and queue work, not `LinkedList`, unless you need the list operations.

**See also:** [Arrays & Strings](arrays-strings.md), [Stacks & Queues](stacks-queues.md), [Trees](trees.md), [DSA Foundations](index.md)
