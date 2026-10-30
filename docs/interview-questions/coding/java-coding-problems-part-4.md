# Java-Specific Coding Problems (Part 4 of 4)

Continued from [Part 3](java-coding-problems-part-3.md).

---

## 19. Find the index where the left sum equals the right sum

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
For each index `i`, the left sum is the total of the elements before `i`, and the right sum is the total of the elements after `i`. Return the first `i` where the two are equal, or `-1` if none exists. Brute force recomputes both sums for every index, which is O(n²). A prefix sum computes the total once and keeps a running left sum, which gives O(n) time and O(1) extra space.

### Explanation
Example: for `[1, 7, 3, 6, 5, 6]` the answer is `3`, because the left sum `1 + 7 + 3 = 11` equals the right sum `5 + 6 = 11`.

The prefix approach uses one identity: `right = total - left - nums[i]`. The element at `i` is excluded from both sides, so the check is `left == total - left - nums[i]`.

**Approach 1: brute force.** O(n²) time, O(1) space.

```java
public class PivotIndexBruteForce {
    static int pivotIndex(int[] nums) {
        for (int i = 0; i < nums.length; i++) {
            long left = 0;
            for (int j = 0; j < i; j++) {
                left += nums[j];
            }
            long right = 0;
            for (int j = i + 1; j < nums.length; j++) {
                right += nums[j];
            }
            if (left == right) {
                return i;
            }
        }
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(pivotIndex(new int[] {1, 7, 3, 6, 5, 6}));  // 3
        System.out.println(pivotIndex(new int[] {1, 2, 3}));           // -1
    }
}
```

**Approach 2: prefix sum.** O(n) time, O(1) extra space.

```java
public class PivotIndexPrefixSum {
    static int pivotIndex(int[] nums) {
        long total = 0;
        for (int value : nums) {
            total += value;
        }
        long left = 0;
        for (int i = 0; i < nums.length; i++) {
            long right = total - left - nums[i];
            if (left == right) {
                return i;
            }
            left += nums[i];
        }
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(pivotIndex(new int[] {1, 7, 3, 6, 5, 6}));  // 3
        System.out.println(pivotIndex(new int[] {2, 1, -1}));          // 0
        System.out.println(pivotIndex(new int[] {}));                  // -1
    }
}
```

A `long` accumulator prevents overflow when the sum of many `int` values exceeds `Integer.MAX_VALUE`.

### When to use / pitfalls
- Clarify whether the answer should be the first or any valid index. The code above returns the first.
- Remember that the element at `i` is excluded from both sides.
- An empty array has no valid index under the usual definition, so return `-1`.

**See also:** [Arrays and Strings Part 1](arrays-strings-part-1.md), [How to approach coding questions](how-to-approach-coding-questions.md)

</details>

---

## 20. Generate all well-formed combinations of n pairs of parentheses

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use backtracking. Build the string one character at a time and track how many `(` and `)` you have placed. You may add `(` while the count of opening brackets is less than `n`. You may add `)` only while it is less than the count of opening brackets. When the string reaches length `2n`, record it. The number of results is the nth Catalan number.

### Explanation
Example: for `n = 3` the output is `((()))`, `(()())`, `(())()`, `()(())`, `()()()`.

The two rules guarantee well-formedness. Opening brackets never exceed `n`, and a closing bracket is only added when it has a matching opener, so the prefix never goes negative.

```java
import java.util.ArrayList;
import java.util.List;

public class GenerateParentheses {
    static List<String> generate(int n) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be zero or more");
        }
        List<String> result = new ArrayList<>();
        backtrack(new StringBuilder(), 0, 0, n, result);
        return result;
    }

    private static void backtrack(StringBuilder current, int open, int close,
                                  int n, List<String> result) {
        if (current.length() == 2 * n) {
            result.add(current.toString());
            return;
        }
        if (open < n) {
            current.append('(');
            backtrack(current, open + 1, close, n, result);
            current.deleteCharAt(current.length() - 1);   // undo the choice
        }
        if (close < open) {
            current.append(')');
            backtrack(current, open, close + 1, n, result);
            current.deleteCharAt(current.length() - 1);
        }
    }

    public static void main(String[] args) {
        System.out.println(generate(3));   // [((())), (()()), (())(), ()(()), ()()()]
        System.out.println(generate(0));   // [""]: one empty combination
    }
}
```

**Complexity.** Time is O(4ⁿ / √n), which is the output-sensitive bound: there are Catalan(n) results and each has length 2n. Extra space is O(n) for the recursion depth and the shared `StringBuilder`, not counting the output list.

### When to use / pitfalls
- Using `StringBuilder` with undo (`deleteCharAt`) avoids creating a new string at every step.
- Checking `close < open` before adding `)` is the step most often missed. Without it the output contains invalid strings such as `)(`.
- The number of results grows fast, so this method is not suitable for very large `n`.

**See also:** [Java Coding Problems Part 3](java-coding-problems-part-3.md), [Graphs and DP Part 1](graphs-dp-part-1.md)

</details>

---

## 21. Print all combinations of 1 and 2 that sum to n

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Treat the question as ordered sequences, where `1 + 2` and `2 + 1` are different. Use recursion: the last step is either `1` or `2`, so the number of ways for `n` is the number of ways for `n - 1` plus the number of ways for `n - 2`. This gives Fibonacci numbers. Printing every sequence is backtracking and takes time proportional to the output. Counting the sequences needs only a memo or an iterative loop, which is O(n).

### Explanation
Example: for `n = 4` the sequences are `[1, 1, 1, 1]`, `[1, 1, 2]`, `[1, 2, 1]`, `[2, 1, 1]`, and `[2, 2]`. There are five, which matches Fibonacci.

If the question means unordered combinations, `2 + 1 + 1` and `1 + 1 + 2` are the same. In that case the answer is the number of distinct counts of twos, which is `n / 2 + 1` (integer division). State which meaning you intend before you code.

**Approach 1: recursion that prints every sequence.**

```java
import java.util.ArrayList;
import java.util.List;

public class OneAndTwoSequences {
    static void printAll(int n) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be zero or more");
        }
        build(n, new ArrayList<>());
    }

    private static void build(int remaining, List<Integer> path) {
        if (remaining == 0) {
            System.out.println(path);
            return;
        }
        for (int step = 1; step <= 2 && step <= remaining; step++) {
            path.add(step);
            build(remaining - step, path);
            path.remove(path.size() - 1);   // backtrack
        }
    }

    public static void main(String[] args) {
        printAll(4);
        // [1, 1, 1, 1]
        // [1, 1, 2]
        // [1, 2, 1]
        // [2, 1, 1]
        // [2, 2]
    }
}
```

**Approach 2: count with a memo, or iteratively.** These return the number of sequences, not the sequences themselves.

```java
import java.util.HashMap;
import java.util.Map;

public class CountOneAndTwoSequences {
    // Recursive with memo: O(n) time and O(n) space.
    static long countMemo(int n, Map<Integer, Long> memo) {
        if (n < 0) {
            return 0;
        }
        if (n == 0) {
            return 1;
        }
        Long cached = memo.get(n);
        if (cached != null) {
            return cached;
        }
        long ways = countMemo(n - 1, memo) + countMemo(n - 2, memo);
        memo.put(n, ways);
        return ways;
    }

    // Iterative: O(n) time and O(1) space.
    static long countIterative(int n) {
        if (n < 0) {
            return 0;
        }
        if (n < 2) {
            return 1;
        }
        long a = 1;   // ways(0)
        long b = 1;   // ways(1)
        for (int i = 2; i <= n; i++) {
            long next = a + b;
            a = b;
            b = next;
        }
        return b;
    }

    public static void main(String[] args) {
        System.out.println(countMemo(4, new HashMap<>()));   // 5
        System.out.println(countIterative(4));               // 5
        System.out.println(countIterative(10));              // 89
    }
}
```

**Complexity.** Printing all sequences takes O(F(n+1) × n) time, where F is the Fibonacci sequence, because each of the F(n+1) sequences has length up to `n`. Recursion depth is O(n). Counting takes O(n) time with the memo or the iterative loop. The `long` return type overflows for `n` above about 90, so use `BigInteger` if larger values are needed.

### When to use / pitfalls
- Confirm whether order matters before writing code. This changes the answer.
- The memo is most useful when the recursion also computes sub-results many times. Printing gains nothing from a memo because every sequence must be printed anyway.
- Watch the base case: `n = 0` has exactly one (empty) sequence.

**See also:** [Graphs and DP Part 1](graphs-dp-part-1.md), [Graphs and DP Part 2](graphs-dp-part-2.md)

</details>

---

## 22. Reverse a string without using predefined reverse methods

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Do not call `StringBuilder.reverse()`. Use one of two approaches. The first copies the string into a `char[]` and swaps characters from both ends with two pointers until they meet. The second builds a new `StringBuilder` by appending characters from the last index down to zero. Both take O(n) time and O(n) space, because Java strings are immutable and a new string must be created.

### Explanation
Example: `"interview"` becomes `"weivretni"`.

**Approach 1: char array with two pointers.**

```java
public class ReverseStringTwoPointers {
    static String reverse(String s) {
        char[] chars = s.toCharArray();
        int left = 0;
        int right = chars.length - 1;
        while (left < right) {
            char temp = chars[left];
            chars[left] = chars[right];
            chars[right] = temp;
            left++;
            right--;
        }
        return new String(chars);
    }

    public static void main(String[] args) {
        System.out.println(reverse("interview"));   // weivretni
        System.out.println(reverse(""));            // empty string
    }
}
```

**Approach 2: StringBuilder loop.**

```java
public class ReverseStringBuilder {
    static String reverse(String s) {
        StringBuilder sb = new StringBuilder(s.length());
        for (int i = s.length() - 1; i >= 0; i--) {
            sb.append(s.charAt(i));
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println(reverse("interview"));   // weivretni
        System.out.println(reverse("a"));           // a
    }
}
```

**Complexity.** Both approaches run in O(n) time and use O(n) extra space. The two-pointer version does about n/2 swaps on the array, and the loop version does n appends.

### When to use / pitfalls
- Pass `null` to either method and it throws `NullPointerException`. Add a null check if callers may pass one.
- Both methods work on UTF-16 code units. A character outside the Basic Multilingual Plane is stored as two `char` values, and reversing them separately breaks the character. Mention this if the interviewer asks about emoji or other supplementary characters.
- In a real project, `new StringBuilder(s).reverse()` is the clearest choice. The exercise is about the algorithm.

**See also:** [Arrays and Strings Part 1](arrays-strings-part-1.md), [Arrays and Strings Part 2](arrays-strings-part-2.md)

</details>

---

## 23. Sort students by marks and assign ranks, including ties

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Sort the students with a `Comparator` that orders by marks descending and then by name ascending, so the order is fixed. Then make one pass over the sorted list. Students with equal marks get the same rank. Standard ranking (also called competition ranking) skips numbers after a tie, so the ranks are `1, 2, 2, 4`. Dense ranking does not skip, so the ranks are `1, 2, 2, 3`. Sorting is O(n log n) and the rank pass is O(n).

### Explanation
Example marks `90, 85, 85, 70`:

| Student | Marks | Standard rank | Dense rank |
|---|---|---|---|
| Ben | 90 | 1 | 1 |
| Asha | 85 | 2 | 2 |
| Chris | 85 | 2 | 2 |
| Dev | 70 | 4 | 3 |

The rank pass uses the position in the sorted list for standard rank, and a counter of distinct marks for dense rank.

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class StudentRanking {
    record Student(String name, int marks) {}

    record Ranked(String name, int marks, int standardRank, int denseRank) {}

    // Marks descending, then name ascending for a stable, predictable order.
    static final Comparator<Student> BY_MARKS_DESC_THEN_NAME =
            Comparator.comparingInt(Student::marks)
                      .reversed()
                      .thenComparing(Student::name);

    static List<Ranked> assignRanks(List<Student> students) {
        List<Student> sorted = new ArrayList<>(students);   // do not modify the input
        sorted.sort(BY_MARKS_DESC_THEN_NAME);

        List<Ranked> result = new ArrayList<>(sorted.size());
        int standardRank = 0;
        int denseRank = 0;
        boolean first = true;
        int previousMarks = 0;

        for (int i = 0; i < sorted.size(); i++) {
            Student s = sorted.get(i);
            if (first || s.marks() != previousMarks) {
                standardRank = i + 1;     // position of the first student with this mark
                denseRank++;              // next distinct mark value
                previousMarks = s.marks();
                first = false;
            }
            result.add(new Ranked(s.name(), s.marks(), standardRank, denseRank));
        }
        return result;
    }

    public static void main(String[] args) {
        List<Student> students = List.of(
                new Student("Asha", 85),
                new Student("Ben", 90),
                new Student("Chris", 85),
                new Student("Dev", 70));

        for (Ranked r : assignRanks(students)) {
            System.out.println(r);
        }
    }
}
```

Output:

```
Ranked[name=Ben, marks=90, standardRank=1, denseRank=1]
Ranked[name=Asha, marks=85, standardRank=2, denseRank=2]
Ranked[name=Chris, marks=85, standardRank=2, denseRank=2]
Ranked[name=Dev, marks=70, standardRank=4, denseRank=3]
```

**Complexity.** Time is O(n log n) for the sort and O(n) for the rank pass. Extra space is O(n) for the sorted copy and the result list.

### When to use / pitfalls
- Compare with `Integer.compare` or `Comparator.comparingInt`. Subtracting marks can overflow for extreme values.
- Clarify which ranking the interviewer wants. Competition ranking is common in sports and exams, and dense ranking is common in reports that show distinct levels.
- Do not sort the caller's list in place unless that is part of the contract. The code above copies it first.
- A tie-breaker like name is needed only for a stable display order. It does not change the rank values.

**See also:** [Stream API Problems Part 1](stream-api-problems-part-1.md), [Java Coding Problems Part 2](java-coding-problems-part-2.md)

</details>

---

## Quick recap

- Prefix sums turn the pivot-index check from O(n²) into O(n).
- Generate parentheses with backtracking. Add `)` only when it has a matching `(`.
- Sequences of 1s and 2s that sum to `n` follow Fibonacci counts. Clarify whether order matters.
- Reverse a string with a two-pointer swap on a `char[]`, or with a `StringBuilder` loop.
- Sort with a full comparator, then assign standard or dense ranks in one pass over the sorted list.

**See also:** [Java Coding Problems Part 3](java-coding-problems-part-3.md), [How to approach coding questions](how-to-approach-coding-questions.md)
