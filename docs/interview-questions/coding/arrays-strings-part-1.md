# Arrays and Strings Coding Questions (Part 1 of 2)

Common array and string problems asked in Java interviews. Each question gives two or three approaches, with time and space complexity, and a short Java solution. Say the brute-force idea first, then improve it.

---


This page is split into 2 parts. Continue to [Part 2](arrays-strings-part-2.md).

## 1. Two Sum: find two indexes whose values add up to a target

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a hash map from value to index. For each number, check whether `target - number` is already in the map. This runs in O(n) time and O(n) space. The brute-force nested loop is O(n^2) time and O(1) space.

### Explanation
**Approach 1: brute force.** O(n^2) time, O(1) space.

```java
class TwoSum {
    static int[] bruteForce(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] + nums[j] == target) {
                    return new int[]{i, j};
                }
            }
        }
        return new int[0];
    }
}
```

**Approach 2: hash map.** O(n) time, O(n) space.

```java
import java.util.HashMap;
import java.util.Map;

class TwoSumMap {
    static int[] solve(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            Integer j = seen.get(target - nums[i]);
            if (j != null) {
                return new int[]{j, i};
            }
            seen.put(nums[i], i);
        }
        return new int[0];
    }
}
```

### When to use / pitfalls
- Store the value's index only after checking, so the same element is not paired with itself.
- If the array is sorted, two pointers from both ends give O(n) time and O(1) space.
- Interviewers often ask for the case with duplicate values; the hash map handles it because it checks before inserting.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 2. Maximum subarray sum

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Kadane's algorithm keeps the best sum of a subarray ending at the current index and the best overall sum. It runs in O(n) time and O(1) space. A brute-force check of every subarray is O(n^2) time.

### Explanation
**Approach 1: brute force.** O(n^2) time, O(1) space.

```java
class MaxSubarray {
    static int bruteForce(int[] nums) {          // assumes nums.length >= 1
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
}
```

**Approach 2: Kadane's algorithm.** O(n) time, O(1) space.

```java
class Kadane {
    static int maxSubarray(int[] nums) {         // assumes nums.length >= 1
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

### When to use / pitfalls
- Initialise from `nums[0]`, not 0, so an all-negative array returns the largest single element.
- To return the subarray itself, track start and end indexes when `current` restarts.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 3. Best time to buy and sell a stock once

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Scan the prices once, keep the lowest price seen so far, and at each day compute the profit from selling today. This is O(n) time and O(1) space.

### Explanation
**Approach 1: check every pair.** O(n^2) time, O(1) space.

```java
class StockBruteForce {
    static int maxProfit(int[] prices) {
        int best = 0;
        for (int buy = 0; buy < prices.length; buy++) {
            for (int sell = buy + 1; sell < prices.length; sell++) {
                best = Math.max(best, prices[sell] - prices[buy]);
            }
        }
        return best;
    }
}
```

**Approach 2: track the minimum.** O(n) time, O(1) space.

```java
class StockOnePass {
    static int maxProfit(int[] prices) {
        int minSoFar = Integer.MAX_VALUE;
        int best = 0;
        for (int price : prices) {
            minSoFar = Math.min(minSoFar, price);
            best = Math.max(best, price - minSoFar);
        }
        return best;
    }
}
```

### When to use / pitfalls
- Returning 0 means "do not trade"; some problem versions return -1 instead. Read the statement.
- A variant that allows many transactions becomes a sum of all positive day-to-day gains.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 4. Merge overlapping intervals

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Sort the intervals by start, then walk through them, extending the last merged interval when the next one overlaps it. The sort dominates: O(n log n) time, O(n) space for the output.

### Explanation
**Approach 1: sort and sweep.** O(n log n) time.

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

class MergeIntervals {
    static int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> merged = new ArrayList<>();
        for (int[] current : intervals) {
            if (merged.isEmpty() || merged.get(merged.size() - 1)[1] < current[0]) {
                merged.add(current.clone());                // no overlap: start a new interval
            } else {
                int[] last = merged.get(merged.size() - 1);
                last[1] = Math.max(last[1], current[1]);    // overlap: extend the end
            }
        }
        return merged.toArray(new int[0][]);
    }
}
```

**Approach 2: note.** If coordinates are small integers, a difference array counts how many intervals cover each point in O(n + range) time. It fails when the range is large, so the sort-based approach is the general answer.

### When to use / pitfalls
- Clone the first interval before mutating it, so the caller's array is not changed.
- Touching intervals such as `[1,2]` and `[2,3]` count as overlapping in most statements. Check whether `<` or `<=` is correct for the problem.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 5. Product of array except self

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Compute prefix products from the left and multiply by suffix products from the right, all in the output array. This gives O(n) time and O(1) extra space, not counting the output. Avoid division, because a zero breaks it.

### Explanation
**Approach 1: nested loops.** O(n^2) time, O(1) extra space.

```java
class ProductExceptSelfBrute {
    static int[] solve(int[] nums) {
        int n = nums.length;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            int product = 1;
            for (int j = 0; j < n; j++) {
                if (i != j) {
                    product *= nums[j];
                }
            }
            out[i] = product;
        }
        return out;
    }
}
```

**Approach 2: prefix and suffix passes.** O(n) time, O(1) extra space.

```java
class ProductExceptSelf {
    static int[] solve(int[] nums) {
        int n = nums.length;
        int[] out = new int[n];
        int prefix = 1;
        for (int i = 0; i < n; i++) {
            out[i] = prefix;          // product of everything to the left
            prefix *= nums[i];
        }
        int suffix = 1;
        for (int i = n - 1; i >= 0; i--) {
            out[i] *= suffix;         // multiply by everything to the right
            suffix *= nums[i];
        }
        return out;
    }
}
```

### When to use / pitfalls
- Division-based solutions are O(n) too, but they fail on zeros and need special cases. Mention them, then explain why you avoid them.
- Integer products overflow quickly. Ask whether the result type should be `long`.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 6. Rotate an array right by k positions

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Reverse the whole array, then reverse the first `k` elements and the rest separately. This is O(n) time and O(1) extra space. Copying into a new array is also O(n) time, but it uses O(n) extra space.

### Explanation
**Approach 1: copy into a new array.** O(n) time, O(n) space.

```java
class RotateCopy {
    static int[] rotate(int[] nums, int k) {
        int n = nums.length;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            out[(i + k) % n] = nums[i];
        }
        return out;
    }
}
```

**Approach 2: three reversals.** O(n) time, O(1) space.

```java
class RotateReverse {
    static void rotate(int[] nums, int k) {
        int n = nums.length;
        k %= n;                       // handles k larger than the length
        reverse(nums, 0, n - 1);
        reverse(nums, 0, k - 1);
        reverse(nums, k, n - 1);
    }

    private static void reverse(int[] a, int i, int j) {
        while (i < j) {
            int tmp = a[i];
            a[i++] = a[j];
            a[j--] = tmp;
        }
    }
}
```

### When to use / pitfalls
- Take `k %= n` first. If `n` is zero, that is a division by zero, so guard for empty arrays.
- The in-place version changes the caller's array; say so in your answer.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 7. Length of the longest substring without repeating characters

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a sliding window with two indexes. Move the right end forward; when a repeated character appears inside the window, move the left end past its previous occurrence. The window approach is O(n) time, and the space is bounded by the character set size.

### Explanation
**Approach 1: check every substring.** O(n^3) time with a naive uniqueness check, O(min(n, alphabet)) space.

```java
import java.util.HashSet;
import java.util.Set;

class LongestUniqueBrute {
    static int solve(String s) {
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            for (int j = i + 1; j <= s.length(); j++) {
                Set<Character> seen = new HashSet<>();
                boolean unique = true;
                for (int k = i; k < j; k++) {
                    if (!seen.add(s.charAt(k))) {
                        unique = false;
                        break;
                    }
                }
                if (unique) {
                    best = Math.max(best, j - i);
                }
            }
        }
        return best;
    }
}
```

**Approach 2: sliding window with last-seen index.** O(n) time.

```java
import java.util.HashMap;
import java.util.Map;

class LongestUnique {
    static int solve(String s) {
        Map<Character, Integer> lastIndex = new HashMap<>();
        int best = 0;
        int left = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            Integer prev = lastIndex.get(c);
            if (prev != null && prev >= left) {
                left = prev + 1;          // jump past the earlier copy
            }
            lastIndex.put(c, right);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
```

### When to use / pitfalls
- Check `prev >= left`. An old occurrence before the window should not move the left end backwards.
- For ASCII input, an `int[128]` array of last indexes is faster than a `HashMap`.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---


**Next:** [Part 2](arrays-strings-part-2.md)
