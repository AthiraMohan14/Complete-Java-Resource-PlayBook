# Dynamic Programming

Dynamic programming (DP) solves a problem by breaking it into overlapping subproblems and storing each answer so it is computed once. Interviewers use DP to test whether you can define a state, write a recurrence, and reduce time and space.

## Core concepts

### Overlapping subproblems and optimal substructure

DP applies when two conditions hold:

- **Optimal substructure:** the best answer to the whole problem is built from best answers to smaller parts.
- **Overlapping subproblems:** the same smaller part is needed many times. Plain recursion recomputes it each time; DP stores it.

Naive `fib(n)` takes exponential time because `fib(n-2)` is computed inside both `fib(n-1)` and `fib(n)`. Caching fixes that.

### Memoisation (top-down) and tabulation (bottom-up)

| Approach | How it works | Pros | Cons |
|---|---|---|---|
| Memoisation | Recursion plus a cache | Only computes states you need; easy to write from the recurrence | Recursion depth; call overhead |
| Tabulation | Fill a table in dependency order | No recursion; easy to reduce space | Must compute states you may not need |

Memoised Fibonacci:

```java
public class FibMemo {
    static long fib(int n, long[] memo) {
        if (n < 2) return n;
        if (memo[n] != 0) return memo[n];      // 0 is a safe "not computed" marker here, since fib(n) >= 1 for n >= 2
        return memo[n] = fib(n - 1, memo) + fib(n - 2, memo);
    }

    public static void main(String[] args) {
        System.out.println(fib(50, new long[51]));   // 12586269025
    }
}
```

Avoid `Map.computeIfAbsent` with a recursive call that writes to the same map. In Java 9 and later it throws `ConcurrentModificationException`.

Tabulated coin change (minimum number of coins):

```java
import java.util.Arrays;

public class CoinChange {
    static int minCoins(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);           // larger than any valid answer, acts as infinity
        dp[0] = 0;
        for (int a = 1; a <= amount; a++) {
            for (int c : coins) {
                if (c <= a) {
                    dp[a] = Math.min(dp[a], dp[a - c] + 1);
                }
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }

    public static void main(String[] args) {
        System.out.println(minCoins(new int[]{1, 2, 5}, 11));   // 3 (5 + 5 + 1)
    }
}
```

### Classic problems

**0/1 knapsack.** Each item is used at most once. Iterating capacity in reverse lets a one-dimensional array work.

```java
public class Knapsack {
    static int knapsack(int[] weight, int[] value, int capacity) {
        int[] best = new int[capacity + 1];
        for (int i = 0; i < weight.length; i++) {
            for (int c = capacity; c >= weight[i]; c--) {   // reverse order: each item counted once
                best[c] = Math.max(best[c], best[c - weight[i]] + value[i]);
            }
        }
        return best[capacity];
    }
}
```

**Longest common subsequence (LCS).** Two-dimensional table; `dp[i][j]` is the LCS length of the first `i` characters of `a` and the first `j` of `b`.

```java
public class Lcs {
    static int lcs(String a, String b) {
        int[][] dp = new int[a.length() + 1][b.length() + 1];
        for (int i = 1; i <= a.length(); i++) {
            for (int j = 1; j <= b.length(); j++) {
                dp[i][j] = a.charAt(i - 1) == b.charAt(j - 1)
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        return dp[a.length()][b.length()];
    }
}
```

**Longest increasing subsequence (LIS).** The O(n²) version is a direct recurrence: `dp[i]` is the best length ending at `i`. The O(n log n) version keeps a "tails" array and uses binary search; mention it when asked for a faster solution.

**Grid paths.** Count paths from the top-left to the bottom-right moving only right or down: `dp[r][c] = dp[r-1][c] + dp[r][c-1]`, with the first row and column set to 1.

**Maximum subarray (Kadane's algorithm).** Let `endingHere` be the best sum of a subarray that ends at the current element. Each step either extends the previous subarray or starts fresh at the current element. The answer is the best `endingHere` seen. This runs in O(n) time and O(1) space. It needs at least one element.

```java
public class MaxSubarray {
    static int maxSubarraySum(int[] nums) {
        int best = nums[0];
        int endingHere = 0;
        for (int n : nums) {
            endingHere = Math.max(n, endingHere + n);   // extend, or start fresh at n
            best = Math.max(best, endingHere);
        }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(maxSubarraySum(new int[]{-2, 1, -3, 4, -1, 2, 1, -5, 4})); // 6, from [4, -1, 2, 1]
    }
}
```

Starting `best` from `nums[0]` rather than `Integer.MIN_VALUE` keeps the answer correct when every element is negative.

#### Kadane's algorithm as a one-state DP
Kadane's algorithm fits the DP recipe with a single state: `endingHere[i]` is the best subarray sum that ends at index `i`. The recurrence is `endingHere[i] = max(nums[i], endingHere[i-1] + nums[i])`. Only the previous value is needed, so one variable replaces the array. Interview problems that ask for the maximum subarray, maximum circular subarray, or maximum product of a subarray (which needs a second running minimum) follow the same pattern. The array-focused version of the problem is in [Arrays and Strings](../../interview-questions/coding/arrays-strings-part-1.md).

Trace of the example input, showing the state after each element:

| Index | `nums[i]` | `endingHere` (extend or restart) | `best` so far |
|---|---|---|---|
| 0 | -2 | max(-2, 0 - 2) = -2 | -2 |
| 1 | 1 | max(1, -2 + 1) = 1 | 1 |
| 2 | -3 | max(-3, 1 - 3) = -2 | 1 |
| 3 | 4 | max(4, -2 + 4) = 4 | 4 |
| 4 | -1 | max(-1, 4 - 1) = 3 | 4 |
| 5 | 2 | max(2, 3 + 2) = 5 | 5 |
| 6 | 1 | max(1, 5 + 1) = 6 | 6 |
| 7 | -5 | max(-5, 6 - 5) = 1 | 6 |
| 8 | 4 | max(4, 1 + 4) = 5 | 6 |

The answer is 6, from the subarray `[4, -1, 2, 1]`. In the code above, the initial `endingHere` is 0, which gives the same result because the first step takes `max(n, 0 + n)`.

### Less common DP families

- **Interval DP:** `dp[i][j]` covers the subarray or substring from `i` to `j`. Typical for matrix-chain multiplication and "burst balloons". Loop by interval length.
- **Tree DP:** compute values for children, then combine at the parent (depth-first post-order). Typical for "maximum path sum" and "diameter".
- **Digit DP:** count numbers in a range with a digit property. State includes position, a tight flag, and the property so far.
- **Bitmask DP:** the state is a subset encoded in an integer. Travelling salesman over `n` cities takes O(2ⁿ × n²), so it works only for small `n`.

## How it works / Step by step

A reliable method for any DP problem:

1. Define the state in words: "`dp[i]` is the best answer for the first `i` items."
2. Write the recurrence: how `dp[i]` depends on smaller states.
3. Set the base cases (empty input, zero amount).
4. Choose the order of computation (or write the memoised recursion first).
5. Check the answer's location in the table, then reduce space if each row depends only on the previous row.

## Common pitfalls

- Defining a state that does not contain enough information to make the next decision.
- Off-by-one errors between the 1-based table and the 0-based input.
- Using `0` as "unreachable" when `0` is also a valid answer. Use a sentinel like `Integer.MAX_VALUE` or `amount + 1`.
- Overflow when adding two `Integer.MAX_VALUE` sentinels. Check before adding, or use `long`.
- Iterating the knapsack capacity forwards, which lets an item be counted several times.
- Forgetting that memoised recursion can overflow the call stack for large inputs.

!!! tip "Interview tip"
    **Q: How do you decide between memoisation and tabulation?**
    Start with memoisation because it follows the recurrence directly and computes only the states you need. Switch to tabulation when recursion depth is a risk or when you want to reduce space row by row. Both have the same time complexity; the state count times the cost per state.

## Quick recap

- DP needs optimal substructure and overlapping subproblems.
- Memoisation is top-down recursion with a cache; tabulation fills a table bottom-up.
- Define the state first, then the recurrence, then the base cases.
- 0/1 knapsack iterates capacity in reverse; LCS and grid paths use 2-D tables.
- Kadane's algorithm is a one-variable DP for the maximum subarray sum.
- Use sentinels carefully: a value that means "unreachable" must not be a valid answer.

**See also:** [Graphs](graphs.md), [Backtracking and Recursion](backtracking-recursion.md), [Greedy, Bit Manipulation and Hashing](greedy-bit-manipulation-hashing.md)
