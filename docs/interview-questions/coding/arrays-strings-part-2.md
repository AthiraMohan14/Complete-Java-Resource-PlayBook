# Arrays and Strings Coding Questions (Part 2 of 2)

Continued from [Part 1](arrays-strings-part-1.md).

---

## 8. Group anagrams together

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Two words are anagrams when they have the same letter counts. Use that as a key: either the sorted characters, or a count of each letter. Group the words in a map by that key. Sorting each word costs O(k log k) for word length k, so the total is O(n * k log k). The count key is O(n * k).

### Explanation
**Approach 1: sorted characters as the key.** O(n * k log k) time.

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class GroupAnagramsSorted {
    static List<List<String>> solve(String[] words) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String word : words) {
            char[] chars = word.toCharArray();
            Arrays.sort(chars);
            groups.computeIfAbsent(new String(chars), k -> new ArrayList<>()).add(word);
        }
        return new ArrayList<>(groups.values());
    }
}
```

**Approach 2: letter counts as the key.** O(n * k) time. Assumes lowercase `a` to `z`.

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class GroupAnagramsCount {
    static List<List<String>> solve(String[] words) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String word : words) {
            int[] counts = new int[26];
            for (char c : word.toCharArray()) {
                counts[c - 'a']++;
            }
            groups.computeIfAbsent(Arrays.toString(counts), k -> new ArrayList<>()).add(word);
        }
        return new ArrayList<>(groups.values());
    }
}
```

### When to use / pitfalls
- A `String` key built from `Arrays.toString` is readable and correct. A `List<Integer>` key also works.
- Ask whether the input can contain uppercase letters or Unicode. The count array only covers 26 letters.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Coding: Java problems](java-coding-problems-part-1.md)

</details>

---

## 9. Longest palindromic substring

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Expand around each center: a palindrome is a mirror around a character (odd length) or between two characters (even length). This takes O(n^2) time and O(1) space. A dynamic programming table gives the same time with O(n^2) space.

### Explanation
**Approach 1: expand around centers.** O(n^2) time, O(1) space.

```java
class LongestPalindrome {
    static String expandAroundCenters(String s) {
        int start = 0;
        int bestLen = 0;
        for (int center = 0; center < s.length(); center++) {
            for (int odd = 0; odd < 2; odd++) {          // odd = 0: even length, odd = 1: odd length
                int lo = center;
                int hi = center + odd;
                while (lo >= 0 && hi < s.length() && s.charAt(lo) == s.charAt(hi)) {
                    lo--;
                    hi++;
                }
                int len = hi - lo - 1;
                if (len > bestLen) {
                    bestLen = len;
                    start = lo + 1;
                }
            }
        }
        return s.substring(start, start + bestLen);
    }
}
```

**Approach 2: dynamic programming table.** O(n^2) time, O(n^2) space.

```java
class LongestPalindromeDp {
    static String solve(String s) {
        int n = s.length();
        boolean[][] isPal = new boolean[n][n];
        int start = 0;
        int bestLen = n == 0 ? 0 : 1;
        for (int i = 0; i < n; i++) {
            isPal[i][i] = true;
        }
        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                if (s.charAt(i) == s.charAt(j) && (len == 2 || isPal[i + 1][j - 1])) {
                    isPal[i][j] = true;
                    if (len > bestLen) {
                        bestLen = len;
                        start = i;
                    }
                }
            }
        }
        return s.substring(start, start + bestLen);
    }
}
```

### When to use / pitfalls
- Off-by-one errors are common: the palindrome length is `hi - lo - 1` after the loop stops.
- Manacher's algorithm solves this in O(n), but it is rarely expected in an interview; name it and move on.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 10. Find the first and last position of a target in a sorted array

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use two binary searches for the lower bound (first index with value at least the target) and the lower bound of target plus one, minus one. This is O(log n) time and O(1) space. A linear scan is O(n).

### Explanation
**Approach 1: linear scan.** O(n) time, O(1) space.

```java
class RangeLinear {
    static int[] searchRange(int[] a, int target) {
        int first = -1;
        int last = -1;
        for (int i = 0; i < a.length; i++) {
            if (a[i] == target) {
                if (first == -1) {
                    first = i;
                }
                last = i;
            }
        }
        return new int[]{first, last};
    }
}
```

**Approach 2: two binary searches.** O(log n) time, O(1) space.

```java
class RangeBinary {
    // First index whose value is >= target
    static int lowerBound(int[] a, long target) {
        int lo = 0;
        int hi = a.length;
        while (lo < hi) {
            int mid = (lo + hi) >>> 1;
            if (a[mid] < target) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        return lo;
    }

    static int[] searchRange(int[] a, int target) {
        int first = lowerBound(a, target);
        if (first == a.length || a[first] != target) {
            return new int[]{-1, -1};
        }
        int last = lowerBound(a, (long) target + 1) - 1;
        return new int[]{first, last};
    }
}
```

### When to use / pitfalls
- Use `(lo + hi) >>> 1` for the midpoint to avoid overflow on very large indexes.
- Passing `target + 1` as an `int` overflows when the target is `Integer.MAX_VALUE`, which is why the code above widens to `long`.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 11. Search in a rotated sorted array

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
At each step, one half of the current range is sorted. Check whether the target lies within the sorted half; if it does, search there, otherwise search the other half. This is O(log n) time and O(1) space, assuming distinct values. A linear scan is O(n).

### Explanation
**Approach 1: linear scan.** O(n) time, O(1) space.

```java
class RotatedLinear {
    static int search(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {
            if (nums[i] == target) {
                return i;
            }
        }
        return -1;
    }
}
```

**Approach 2: modified binary search.** O(log n) time, O(1) space.

```java
class RotatedBinary {
    static int search(int[] nums, int target) {
        int lo = 0;
        int hi = nums.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            if (nums[mid] == target) {
                return mid;
            }
            if (nums[lo] <= nums[mid]) {                      // left half is sorted
                if (nums[lo] <= target && target < nums[mid]) {
                    hi = mid - 1;
                } else {
                    lo = mid + 1;
                }
            } else {                                          // right half is sorted
                if (nums[mid] < target && target <= nums[hi]) {
                    lo = mid + 1;
                } else {
                    hi = mid - 1;
                }
            }
        }
        return -1;
    }
}
```

### When to use / pitfalls
- With duplicate values, `nums[lo] == nums[mid]` can hide which half is sorted, and the worst case becomes O(n). Say so if the interviewer allows duplicates.
- Test with a one-element array and with the target at each end.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 12. Trapping rain water

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Water above a bar is limited by the lower of the tallest bar to its left and the tallest bar to its right. Precompute those maxima in two arrays for O(n) time and O(n) space, or use two pointers that track both maxima for O(n) time and O(1) space.

### Explanation
**Approach 1: prefix and suffix maxima.** O(n) time, O(n) space.

```java
class TrapPrefix {
    static int trap(int[] h) {
        int n = h.length;
        if (n == 0) {
            return 0;
        }
        int[] left = new int[n];
        int[] right = new int[n];
        left[0] = h[0];
        for (int i = 1; i < n; i++) {
            left[i] = Math.max(left[i - 1], h[i]);
        }
        right[n - 1] = h[n - 1];
        for (int i = n - 2; i >= 0; i--) {
            right[i] = Math.max(right[i + 1], h[i]);
        }
        int water = 0;
        for (int i = 0; i < n; i++) {
            water += Math.min(left[i], right[i]) - h[i];
        }
        return water;
    }
}
```

**Approach 2: two pointers.** O(n) time, O(1) space.

```java
class TrapTwoPointers {
    static int trap(int[] h) {
        int l = 0;
        int r = h.length - 1;
        int leftMax = 0;
        int rightMax = 0;
        int water = 0;
        while (l < r) {
            if (h[l] < h[r]) {
                leftMax = Math.max(leftMax, h[l]);     // the right side is at least h[l]
                water += leftMax - h[l];
                l++;
            } else {
                rightMax = Math.max(rightMax, h[r]);   // the left side is at least h[r]
                water += rightMax - h[r];
                r--;
            }
        }
        return water;
    }
}
```

### When to use / pitfalls
- The two-pointer version works because the smaller side's maximum is already the limiting factor.
- Explain the water formula in words first: water at each bar is `min(leftMax, rightMax) - height`, never negative.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Stacks and queues](linked-lists-trees-part-1.md)

</details>

---

## 13. String compression (run-length encoding)

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Scan the string, count each run of equal characters, and write the character followed by the count when the count is greater than one. A `StringBuilder` gives O(n) time and O(n) space. The in-place version on a `char[]` uses two pointers and O(1) extra space.

### Explanation
**Approach 1: StringBuilder.** O(n) time, O(n) space.

```java
class CompressBuilder {
    static String compress(String s) {
        StringBuilder sb = new StringBuilder();
        int i = 0;
        while (i < s.length()) {
            int j = i;
            while (j < s.length() && s.charAt(j) == s.charAt(i)) {
                j++;
            }
            sb.append(s.charAt(i));
            if (j - i > 1) {
                sb.append(j - i);
            }
            i = j;
        }
        return sb.toString();
    }
}
```

**Approach 2: in-place two pointers on a char array.** O(n) time, O(1) extra space.

```java
class CompressInPlace {
    static int compress(char[] chars) {
        int write = 0;
        int read = 0;
        while (read < chars.length) {
            char c = chars[read];
            int run = 0;
            while (read < chars.length && chars[read] == c) {
                read++;
                run++;
            }
            chars[write++] = c;
            if (run > 1) {
                for (char digit : Integer.toString(run).toCharArray()) {
                    chars[write++] = digit;
                }
            }
        }
        return write;               // the compressed length; the rest of the array is unused
    }
}
```

### When to use / pitfalls
- Counts of 10 or more produce several digits; the in-place version handles this, which is easy to miss.
- The output is never longer than the input, but it is not always shorter: `ab` stays `ab`, while `aabb` becomes `a2b2` with the same length. Ask whether the caller needs the shorter form or the original.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Coding: Java problems](java-coding-problems-part-1.md)

</details>

---

## Quick recap

- Start with the brute force, state its complexity, then improve it.
- Hash maps trade space for time (two sum, anagrams).
- Sliding windows and two pointers give O(n) on many contiguous-range problems.
- Binary search needs a monotonic condition; rotated arrays still have one half sorted at each step.
- Ask about duplicates, empty input, negative numbers, and character sets before you code.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md), [Stream API problems](stream-api-problems-part-1.md)
