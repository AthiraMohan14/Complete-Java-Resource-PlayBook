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
- Use sentinels carefully: a value that means "unreachable" must not be a valid answer.

**See also:** [Graphs](graphs.md), [Backtracking and Recursion](backtracking-recursion.md), [Greedy, Bit Manipulation and Hashing](greedy-bit-manipulation-hashing.md)
