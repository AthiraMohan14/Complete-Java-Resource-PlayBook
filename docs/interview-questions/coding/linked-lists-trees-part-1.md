# Linked Lists, Stacks, and Trees Coding Questions (Part 1 of 2)

Coding questions on singly linked lists, stacks and monotonic stacks, binary trees, and binary search trees. The examples assume the node classes defined in the first two questions, and each question gives two approaches with complexity.

---


This page is split into 2 parts. Continue to [Part 2](linked-lists-trees-part-2.md).

## 1. Reverse a singly linked list

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Walk the list once and point each node's `next` at the previous node. The iterative version runs in O(n) time and O(1) space. The recursive version is also O(n) time but uses O(n) stack space.

### Explanation
The examples use this node class:

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}
```

**Approach 1: iterative.** O(n) time, O(1) space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class ReverseList {
    static ListNode reverseIterative(ListNode head) {
        ListNode prev = null;
        ListNode cur = head;
        while (cur != null) {
            ListNode next = cur.next;   // save the rest of the list
            cur.next = prev;            // flip the pointer
            prev = cur;
            cur = next;
        }
        return prev;                    // prev is the new head
    }
}
```

**Approach 2: recursive.** O(n) time, O(n) stack space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class ReverseListRecursive {
    static ListNode reverseRecursive(ListNode head) {
        if (head == null || head.next == null) {
            return head;
        }
        ListNode newHead = reverseRecursive(head.next);
        head.next.next = head;          // the next node now points back to this one
        head.next = null;
        return newHead;
    }
}
```

### When to use / pitfalls
- Save `cur.next` before changing it, or you lose the rest of the list.
- The recursive version can overflow the stack on very long lists. Prefer the iterative version in production code.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 2. Detect a cycle in a linked list and find where it starts

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Floyd's tortoise-and-hare algorithm moves a slow pointer one step and a fast pointer two steps. If they meet, there is a cycle. To find the start, reset one pointer to the head and advance both one step at a time; they meet at the cycle start. This is O(n) time and O(1) space.

### Explanation
**Approach 1: a set of visited nodes.** O(n) time, O(n) space.

```java
import java.util.HashSet;
import java.util.Set;

class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class CycleSet {
    static boolean hasCycle(ListNode head) {
        Set<ListNode> seen = new HashSet<>();
        for (ListNode n = head; n != null; n = n.next) {
            if (!seen.add(n)) {         // add() returns false when the node was already seen
                return true;
            }
        }
        return false;
    }
}
```

**Approach 2: Floyd's algorithm.** O(n) time, O(1) space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class CycleFloyd {
    static ListNode cycleStart(ListNode head) {
        ListNode slow = head;
        ListNode fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {                       // they met inside the cycle
                ListNode p = head;
                while (p != slow) {                   // walk both one step at a time
                    p = p.next;
                    slow = slow.next;
                }
                return p;                             // the cycle's entry point
            }
        }
        return null;                                  // no cycle
    }
}
```

### When to use / pitfalls
- Compare nodes with `==`, not with `equals`, because the question is about identity.
- Check `fast != null && fast.next != null` before moving `fast.next.next`.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 3. Find the middle node of a linked list

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use slow and fast pointers: when the fast pointer reaches the end, the slow pointer is at the middle. This is O(n) time and O(1) space. Counting the length first and walking half the list is also O(n) time, with two passes.

### Explanation
**Approach 1: slow and fast pointers.** O(n) time, O(1) space. For an even-length list this returns the second middle node.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class MiddleFast {
    static ListNode middle(ListNode head) {
        ListNode slow = head;
        ListNode fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        return slow;
    }
}
```

**Approach 2: count, then walk.** O(n) time, O(1) space, two passes.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class MiddleTwoPass {
    static ListNode middle(ListNode head) {
        int length = 0;
        for (ListNode c = head; c != null; c = c.next) {
            length++;
        }
        ListNode cur = head;
        for (int i = 0; i < length / 2; i++) {
            cur = cur.next;
        }
        return cur;
    }
}
```

### When to use / pitfalls
- Clarify which middle the problem wants for even lengths.
- The fast-pointer version is preferred when you can only traverse once, such as with a stream of nodes.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 4. Merge two sorted linked lists

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a dummy head node and repeatedly attach the smaller front node of the two lists. This is O(n + m) time and O(1) extra space. The recursive version has the same time and O(n + m) stack depth.

### Explanation
**Approach 1: iterative with a dummy node.** O(n + m) time, O(1) extra space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class MergeLists {
    static ListNode merge(ListNode a, ListNode b) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
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
        tail.next = (a != null) ? a : b;   // attach whatever is left
        return dummy.next;
    }
}
```

**Approach 2: recursive.** O(n + m) time, O(n + m) stack space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class MergeListsRecursive {
    static ListNode merge(ListNode a, ListNode b) {
        if (a == null) {
            return b;
        }
        if (b == null) {
            return a;
        }
        if (a.val <= b.val) {
            a.next = merge(a.next, b);
            return a;
        }
        b.next = merge(a, b.next);
        return b;
    }
}
```

### When to use / pitfalls
- The dummy node removes special cases for an empty result.
- The iterative version reuses the existing nodes; no new nodes are created.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 5. Remove the nth node from the end of a list

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Put a dummy node before the head, move a fast pointer `n + 1` steps ahead, then move both pointers until the fast one reaches the end. The slow pointer is then just before the node to remove. This is O(L) time, where L is the list length, and O(1) space.

### Explanation
**Approach 1: one pass with two pointers.** O(L) time, O(1) space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class RemoveNthFromEnd {
    static ListNode remove(ListNode head, int n) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode fast = dummy;
        ListNode slow = dummy;
        for (int i = 0; i <= n; i++) {       // keep a gap of n + 1 nodes
            fast = fast.next;
        }
        while (fast != null) {
            fast = fast.next;
            slow = slow.next;
        }
        slow.next = slow.next.next;          // unlink the target
        return dummy.next;
    }
}
```

**Approach 2: count the length first.** O(L) time, two passes, O(1) space.

```java
class ListNode {
    int val;
    ListNode next;

    ListNode(int val) {
        this.val = val;
    }
}

class RemoveNthTwoPass {
    static ListNode remove(ListNode head, int n) {
        int length = 0;
        for (ListNode c = head; c != null; c = c.next) {
            length++;
        }
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy;
        for (int i = 0; i < length - n; i++) {
            prev = prev.next;
        }
        prev.next = prev.next.next;
        return dummy.next;
    }
}
```

### When to use / pitfalls
- Removing the head is the case the dummy node handles cleanly.
- Ask whether `n` is always valid; if not, check it before walking.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 6. Check whether a string of brackets is valid

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Push the closing bracket for each opening bracket onto a stack. For each closing bracket, pop and compare; any mismatch or an empty stack means invalid. The stack version is O(n) time and O(n) space. Repeatedly removing matched pairs is simpler to write but takes O(n^2) time in the worst case.

### Explanation
**Approach 1: stack.** O(n) time, O(n) space.

```java
import java.util.ArrayDeque;
import java.util.Deque;

class ValidBrackets {
    static boolean isValid(String s) {
        Deque<Character> expected = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            switch (c) {
                case '(' -> expected.push(')');
                case '[' -> expected.push(']');
                case '{' -> expected.push('}');
                default -> {
                    if (expected.isEmpty() || expected.pop() != c) {
                        return false;
                    }
                }
            }
        }
        return expected.isEmpty();
    }
}
```

**Approach 2: repeated removal.** O(n^2) worst case.

```java
class ValidBracketsReplace {
    static boolean isValid(String s) {
        String previous;
        do {
            previous = s;
            s = s.replace("()", "").replace("[]", "").replace("{}", "");
        } while (!s.equals(previous));
        return s.isEmpty();
    }
}
```

### When to use / pitfalls
- Check for an empty stack before every `pop()`, or input such as `)` throws an exception.
- Odd-length input can be rejected at once, as a quick early exit.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 7. Next greater element for each value

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a monotonic stack of indexes whose values are decreasing. When a new value is larger than the value at the top, it is the next greater element for that top index; pop it and record the answer. Each index is pushed and popped once, so the time is O(n) and the space is O(n). A nested loop is O(n^2).

### Explanation
**Approach 1: nested loops.** O(n^2) time, O(1) extra space, excluding output.

```java
class NextGreaterBrute {
    static int[] solve(int[] nums) {
        int[] result = new int[nums.length];
        for (int i = 0; i < nums.length; i++) {
            result[i] = -1;                       // -1 means no greater element
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[j] > nums[i]) {
                    result[i] = nums[j];
                    break;
                }
            }
        }
        return result;
    }
}
```

**Approach 2: monotonic stack.** O(n) time, O(n) space.

```java
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

class NextGreaterStack {
    static int[] solve(int[] nums) {
        int[] result = new int[nums.length];
        Arrays.fill(result, -1);
        Deque<Integer> stack = new ArrayDeque<>();     // indexes still waiting for a greater value
        for (int i = 0; i < nums.length; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
                result[stack.pop()] = nums[i];
            }
            stack.push(i);
        }
        return result;
    }
}
```

### When to use / pitfalls
- Store indexes, not values, on the stack; you need the index to write the result.
- The same pattern solves "daily temperatures" and "trapping rain water" style questions.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---


**Next:** [Part 2](linked-lists-trees-part-2.md)
