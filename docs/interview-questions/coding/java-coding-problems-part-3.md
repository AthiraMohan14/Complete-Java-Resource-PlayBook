# Java-Specific Coding Problems (Part 3 of 3)

Continued from [Part 2](java-coding-problems-part-2.md).

---

## 11. Transfer money between two accounts without deadlock

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A deadlock happens when one transfer locks A then B while another locks B then A. Lock the two accounts in a fixed global order, such as by account ID, so every thread takes them in the same sequence. An alternative is `tryLock` with a timeout, which backs off and retries instead of waiting forever.

### Explanation
**Approach 1: lock ordering.**

```java
import java.util.concurrent.locks.ReentrantLock;

class Account {
    final long id;
    long balance;
    final ReentrantLock lock = new ReentrantLock();

    Account(long id, long balance) {
        this.id = id;
        this.balance = balance;
    }
}

class Bank {
    static void transfer(Account from, Account to, long amount) {
        Account first = from.id < to.id ? from : to;      // always the lower id first
        Account second = first == from ? to : from;
        first.lock.lock();
        try {
            second.lock.lock();
            try {
                if (from.balance < amount) {
                    throw new IllegalStateException("insufficient funds");
                }
                from.balance -= amount;
                to.balance += amount;
            } finally {
                second.lock.unlock();
            }
        } finally {
            first.lock.unlock();
        }
    }
}
```

**Approach 2: `tryLock` with a timeout and back-off.**

```java
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

class Account {
    final ReentrantLock lock = new ReentrantLock();
    long balance;
}

class BankTryLock {
    static boolean transfer(Account from, Account to, long amount) throws InterruptedException {
        while (true) {
            if (from.lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                try {
                    if (to.lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                        try {
                            if (from.balance < amount) {
                                return false;
                            }
                            from.balance -= amount;
                            to.balance += amount;
                            return true;
                        } finally {
                            to.lock.unlock();
                        }
                    }
                } finally {
                    from.lock.unlock();
                }
            }
            Thread.sleep(5);                        // back off, then try again
        }
    }
}
```

### When to use / pitfalls
- Approach 2 can livelock if two threads keep backing off in step. Add random jitter to the sleep, and cap the retries.
- A transfer to the same account needs care: with approach 1 the same lock is taken twice, which `ReentrantLock` allows. Decide whether to reject it.
- In a real system, prefer a database transaction with a consistent update order over in-memory locks.

**See also:** [Advanced Java and concurrency](../technical/advanced-java-concurrency-part-1.md), [Data and persistence](../technical/data-and-persistence-part-1.md)

</details>

---

## 12. Parse ISO dates and count the days between them

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `java.time`, not `java.util.Date`. `LocalDate.parse` reads ISO-8601 dates (`yyyy-MM-dd`), and `ChronoUnit.DAYS.between` returns the number of days between two dates. Do not use `Period.getDays()` for this: it returns only the day part of a period, not the total number of days.

### Explanation
**Approach 1: `ChronoUnit.DAYS.between`.** O(1) time.

```java
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

class DaysBetween {
    static long days(String start, String end) {
        LocalDate a = LocalDate.parse(start);      // ISO-8601: 2026-01-31
        LocalDate b = LocalDate.parse(end);
        return ChronoUnit.DAYS.between(a, b);
    }
}
```

**Approach 2: epoch days.** O(1) time. Useful when you already work with epoch-day numbers.

```java
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

class DaysBetweenCustomFormat {
    static long days(String start, String end) {
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd/MM/yyyy");
        LocalDate a = LocalDate.parse(start, fmt);
        LocalDate b = LocalDate.parse(end, fmt);
        return b.toEpochDay() - a.toEpochDay();
    }
}
```

### When to use / pitfalls
- `Period.between(a, b).getDays()` returns the days component after months and years are removed. Use `ChronoUnit.DAYS` for a total.
- Time zones matter for instants and date-times. `LocalDate` has none, which is what you want for calendar dates.
- Patterns such as `dd/MM/yyyy` are not the same as `MM/dd/yyyy`. Use an explicit formatter, never a guess.
- `java.util.Date` and `Calendar` are legacy; mention them only to say you would avoid them.

**See also:** [Core Java](../technical/core-java-part-1.md)

</details>

---

## 13. Print the numbers 1 to N without a loop

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use recursion. For ascending output, recurse on `n - 1` first and print `n` after the call returns. For descending output, print `n` before the recursive call. Both versions take O(n) time and O(n) call-stack space. A stream over a range prints the same numbers with no explicit recursion.

### Explanation
**Approach 1: recursion, ascending (print after the call).**

```java
class PrintNumbers {
    static void ascending(int n) {
        if (n <= 0) {
            return;                  // base case: nothing to print
        }
        ascending(n - 1);            // the smaller problem prints 1..n-1 first
        System.out.print(n + " ");
    }

    public static void main(String[] args) {
        ascending(5);                // prints: 1 2 3 4 5
    }
}
```

**Approach 2: recursion, descending (print before the call).**

```java
static void descending(int n) {
    if (n <= 0) {
        return;
    }
    System.out.print(n + " ");   // print the current value first
    descending(n - 1);           // then handle the rest
}
// descending(5) prints: 5 4 3 2 1
```

**Approach 3: `IntStream`.**

```java
import java.util.stream.IntStream;

class SolutionStreams {

    static void viaStream(int n) {
        IntStream.range(1, n + 1).forEach(number -> System.out.print(number + " "));
    }
}
```

### When to use / pitfalls
- Every call adds a frame, so a very large `n` can throw `StackOverflowError`. The stream version does not have this limit.
- Java does not eliminate tail calls, so `descending` still uses one stack frame per number.
- Decide what `n <= 0` should do before you code. The versions above print nothing.

**See also:** [How to approach coding questions](how-to-approach-coding-questions.md)

</details>

---

## 14. Check whether a string is a palindrome

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Normalise the input first (remove whitespace, lower-case it), then compare characters from the two ends moving inward. The two-pointer loop is the best choice: O(n) time and O(1) extra space beyond the normalised copy. Recursion and streams give the same answer; recursion costs O(n) stack space.

### Explanation
**Approach 1: two pointers.**

```java
class Palindrome {
    static boolean isPalindrome(String text) {
        String t = text.replaceAll("\\s+", "").toLowerCase();
        int left = 0;
        int right = t.length() - 1;
        while (left < right) {
            if (t.charAt(left) != t.charAt(right)) {
                return false;        // a mismatched pair ends the search
            }
            left++;
            right--;
        }
        return true;
    }
}
```

**Approach 2: recursion on the same two pointers.**

```java
static boolean isPalindromeRecursive(String text) {
    String t = text.replaceAll("\\s+", "").toLowerCase();
    return matches(t, 0, t.length() - 1);
}

private static boolean matches(String s, int left, int right) {
    if (left >= right) {
        return true;                 // checked every pair
    }
    if (s.charAt(left) != s.charAt(right)) {
        return false;
    }
    return matches(s, left + 1, right - 1);
}
```

**Approach 3: stream.**

```java
import java.util.stream.IntStream;

class PalindromeStream {

    static boolean isPalindromeStream(String text) {
        String t = text.replaceAll("\\s+", "").toLowerCase();
        return IntStream.range(0, t.length() / 2)
                .allMatch(i -> t.charAt(i) == t.charAt(t.length() - 1 - i));
    }
}
```

### When to use / pitfalls
- The normalisation above removes only whitespace. If the question says to ignore punctuation too, filter with `Character.isLetterOrDigit` instead.
- A `null` input throws `NullPointerException`. Say so, and add a null check if the interviewer wants one.
- The empty string and a single character are palindromes. The loops above handle both.

**See also:** [How to approach coding questions](how-to-approach-coding-questions.md), [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 15. Find the maximum sum of a contiguous subarray

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use Kadane's algorithm. Walk the array once and keep the best sum of a subarray that ends at the current index. If that running sum drops below the current element, start a new subarray there. This is O(n) time and O(1) space. Brute force (O(n²)) and divide and conquer (O(n log n)) also work and are useful to mention.

### Explanation
Example: for `[-1, 3, -2, 5, -4, 2]` the answer is `6`, from the subarray `[3, -2, 5]`.

**Approach 1: Kadane's algorithm.**

```java
class MaxSubarray {
    static int kadane(int[] nums) {
        if (nums.length == 0) {
            throw new IllegalArgumentException("array is empty");
        }
        int best = nums[0];
        int current = nums[0];
        for (int i = 1; i < nums.length; i++) {
            current = Math.max(nums[i], current + nums[i]);   // extend or restart
            best = Math.max(best, current);
        }
        return best;
    }
}
```

Starting from `nums[0]` rather than `0` keeps the method correct when every number is negative.

**Approach 2: brute force over all subarrays.** O(n²) time, O(1) space.

```java
static int bruteForce(int[] nums) {
    int best = Integer.MIN_VALUE;
    for (int i = 0; i < nums.length; i++) {
        int sum = 0;
        for (int j = i; j < nums.length; j++) {
            sum += nums[j];
            best = Math.max(best, sum);
        }
    }
    return best;
}
```

**Approach 3: divide and conquer.** O(n log n) time, O(log n) stack space. The best subarray is in the left half, the right half, or crosses the midpoint.

```java
static int divideAndConquer(int[] nums, int lo, int hi) {
    if (lo == hi) {
        return nums[lo];
    }
    int mid = lo + (hi - lo) / 2;
    int leftBest = divideAndConquer(nums, lo, mid);
    int rightBest = divideAndConquer(nums, mid + 1, hi);
    return Math.max(Math.max(leftBest, rightBest), crossing(nums, lo, mid, hi));
}

private static int crossing(int[] nums, int lo, int mid, int hi) {
    int leftSum = Integer.MIN_VALUE;
    int sum = 0;
    for (int i = mid; i >= lo; i--) {          // best sum ending at mid
        sum += nums[i];
        leftSum = Math.max(leftSum, sum);
    }
    int rightSum = Integer.MIN_VALUE;
    sum = 0;
    for (int i = mid + 1; i <= hi; i++) {      // best sum starting at mid + 1
        sum += nums[i];
        rightSum = Math.max(rightSum, sum);
    }
    return leftSum + rightSum;
}
```

Call it as `divideAndConquer(nums, 0, nums.length - 1)`.

### When to use / pitfalls
- Kadane's algorithm returns only the sum. To return the indexes too, record the start index whenever `current` restarts, and the end index whenever `best` changes.
- Kadane's algorithm is a dynamic programming idea: each step depends only on the previous step's value.
- Sums of large `int` values can overflow. Use `long` if the input range is large.
- Mention the brute force first in an interview, then move to Kadane's.

**See also:** [Maximum subarray sum in Arrays and strings](arrays-strings-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 16. Remove duplicates from a list while keeping the order

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a `LinkedHashSet`. It drops repeated elements and keeps the first occurrence of each in insertion order. For the same result in a stream, filter with `HashSet::add`, which returns `false` for an element already seen. Both run in O(n) time and O(n) extra space.

### Explanation
**Approach 1: `LinkedHashSet`.**

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;

class Dedup {
    static List<Integer> viaLinkedHashSet(List<Integer> input) {
        return new ArrayList<>(new LinkedHashSet<>(input));
    }

    public static void main(String[] args) {
        System.out.println(viaLinkedHashSet(Arrays.asList(1, 2, 2, 3, 3, 3)));  // [1, 2, 3]
    }
}
```

**Approach 2: stream with a filter.**

```java
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

class DedupStream {

    static List<Integer> viaStream(List<Integer> input) {
        Set<Integer> seen = new HashSet<>();
        return input.stream()
                .filter(seen::add)                    // add returns false on a repeat
                .collect(Collectors.toList());
    }
}
```

**Approach 3: explicit loop.** This is the easiest version to step through with a debugger.

```java
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

class DedupLoop {

    static List<Integer> viaLoop(List<Integer> input) {
        Set<Integer> seen = new HashSet<>();
        List<Integer> result = new ArrayList<>();
        for (Integer value : input) {
            if (seen.add(value)) {
                result.add(value);
            }
        }
        return result;
    }
}
```

### When to use / pitfalls
- `Collectors.toSet()` removes duplicates but does not keep the order. Use it only when order does not matter.
- Duplicate detection depends on `equals` and `hashCode`. For your own classes, override both, or the set will keep "duplicates" that look equal.
- `Arrays.asList` returns a fixed-size list. Copy the result into an `ArrayList` if the caller will change it.
- `Stream.toList()` (Java 16 and later) returns an unmodifiable list, which is handy here. `Collectors.toList()` makes no promise about the list type.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [How to approach coding questions](how-to-approach-coding-questions.md)

</details>

---

## 17. Find a duplicate value in a linked list

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Check each value against the values already seen. A `HashSet` does this in O(n) time and O(n) space. If you cannot use extra memory, compare every pair of nodes in O(n²) time and O(1) space. Floyd's tortoise and hare solves a different problem: a cycle in the pointers. Name that difference out loud in the interview.

### Explanation
**Approach 1: `HashSet`.** Returns the value that repeats first when you walk the list.

```java
import java.util.HashSet;
import java.util.Set;

class ListNode {
    final int val;
    ListNode next;

    ListNode(int val, ListNode next) {
        this.val = val;
        this.next = next;
    }
}

class DuplicateFinder {
    // Returns a value that appears more than once, or null when every value is unique.
    static Integer firstRepeatedValue(ListNode head) {
        Set<Integer> seen = new HashSet<>();
        for (ListNode node = head; node != null; node = node.next) {
            if (!seen.add(node.val)) {
                return node.val;
            }
        }
        return null;
    }
}
```

**Approach 2: nested walk, no extra memory.** O(n²) time, O(1) space.

```java
class DuplicateFinder {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val, ListNode next) { this.val = val; this.next = next; }
    }

    static Integer duplicateNoExtraSpace(ListNode head) {
        for (ListNode outer = head; outer != null; outer = outer.next) {
            for (ListNode inner = outer.next; inner != null; inner = inner.next) {
                if (inner.val == outer.val) {
                    return outer.val;
                }
            }
        }
        return null;
    }
}
```

**Related: detecting a cycle in the pointers (Floyd).** This does not look at values. It answers "does the list loop back on itself?"

```java
class CycleDetector {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val, ListNode next) { this.val = val; this.next = next; }
    }

    static boolean hasCycle(ListNode head) {
        ListNode tortoise = head;   // moves one step at a time
        ListNode hare = head;       // moves two steps at a time
        while (hare != null && hare.next != null) {
            tortoise = tortoise.next;
            hare = hare.next.next;
            if (tortoise == hare) {
                return true;        // the two pointers met inside a loop
            }
        }
        return false;
    }
}
```

### When to use / pitfalls
- The two approaches can return different duplicated values. The `HashSet` returns the value whose second copy appears first. The nested walk returns the earliest node that has a later match. Say which one you want.
- Floyd's algorithm finds a duplicate in the classic array puzzle where each value is an index into the array. It does not find repeated values in a plain linked list.
- `inner.val == outer.val` compares `int` fields, so `==` is correct here. For `Integer` objects, use `equals`.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md), [Java-specific problems part 2](java-coding-problems-part-2.md)

</details>

---

## 18. Predict the output of a Java snippet

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Trace the code one expression at a time, left to right, and track every variable after each step. Pay close attention to `++` and `--` (pre- and post-increment), operator precedence, and implicit `String` conversion. For the snippet `int x = 5; int y = ++x + x++ + x;`, the output is `7 19`.

### Explanation
**Approach 1: hand trace.**

```java
int x = 5;
int y = ++x + x++ + x;
System.out.println(x + " " + y);
```

| Step | Expression | Effect | Value produced |
|------|------------|--------|----------------|
| 1 | `++x` | `x` becomes 6 before use | 6 |
| 2 | `x++` | value is read as 6, then `x` becomes 7 | 6 |
| 3 | `x` | `x` is 7 | 7 |
| 4 | `y = 6 + 6 + 7` | | 19 |

The line prints `7 19`.

**Approach 2: run it.** Put the code in a class with a `main` method and compile it, or paste it into `jshell`. This confirms the answer and is a fair step to take in an interview if the interviewer allows it.

```java
public class TraceDemo {
    public static void main(String[] args) {
        int x = 5;
        int y = ++x + x++ + x;
        System.out.println(x + " " + y);   // 7 19
    }
}
```

### When to use / pitfalls
- Write down each intermediate value. `1 + 2 + "3"` prints `33`, because the first two operands are added before the string concatenation.
- `==` on boxed `Integer` values compares references, so `128 == 128` boxed is `false`. Use `equals`.
- A `finally` block that returns overrides a return in the `try` block.
- Say your trace out loud, then confirm it by running the code if you can.

**See also:** [Core Java part 1](../technical/core-java-part-1.md), [How to approach coding questions](how-to-approach-coding-questions.md)

</details>

---

## Quick recap

- LRU: a `LinkedHashMap` in access order is the short answer; a `HashMap` with a doubly linked list shows the mechanics.
- Singletons: holder idiom or enum; double-checked locking needs `volatile`.
- Blocking hand-off: prefer `BlockingQueue`; know the lock-and-condition version.
- Parsing: recursive descent for expressions; split at the first delimiter for simple formats.
- Immutability: final fields, defensive copies, and records.
- Equality: override both `equals` and `hashCode`, using the same fields.
- Concurrency: fixed lock order prevents deadlock; parallel streams need stateless pipelines.
- Dates: `java.time` with `ChronoUnit` for totals.
- Recursion: recurse before printing for ascending output, after for descending; watch the stack depth.
- Palindromes: normalise first, then compare from both ends; two pointers use O(1) extra space.
- Subarrays: Kadane's algorithm in one pass; brute force and divide and conquer as fallbacks.
- Deduplication: `LinkedHashSet` keeps order; `Collectors.toSet()` does not.
- Linked-list duplicates: `HashSet` for values; Floyd's algorithm is for pointer cycles only.
- Output prediction: trace left to right, then run the code to confirm.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Stream API problems](stream-api-problems-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md)
