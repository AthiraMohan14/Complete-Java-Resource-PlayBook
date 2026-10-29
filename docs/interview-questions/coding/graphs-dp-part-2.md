# Graphs, Dynamic Programming, and Backtracking Coding Questions (Part 2 of 3)

Continued from [Part 1](graphs-dp-part-1.md).

---

## 6. Climbing stairs: count the ways

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The number of ways to reach step n is the number of ways to reach step n - 1 plus step n - 2, so it is a Fibonacci recurrence. Plain recursion is O(2^n) time. Memoisation or bottom-up tabulation makes it O(n) time. Keeping only the last two values gives O(n) time and O(1) space.

### Explanation
**Approach 1: plain recursion.** O(2^n) time, O(n) stack.

```java
class StairsRecursive {
    static long ways(int n) {
        if (n <= 1) {
            return 1;
        }
        return ways(n - 1) + ways(n - 2);
    }
}
```

**Approach 2: top-down memoisation.** O(n) time, O(n) space.

```java
import java.util.HashMap;
import java.util.Map;

class StairsMemo {
    static long ways(int n, Map<Integer, Long> memo) {
        if (n <= 1) {
            return 1;
        }
        Long cached = memo.get(n);
        if (cached != null) {
            return cached;
        }
        long result = ways(n - 1, memo) + ways(n - 2, memo);
        memo.put(n, result);
        return result;
    }
}
```

**Approach 3: two variables.** O(n) time, O(1) space.

```java
class StairsConstantSpace {
    static long ways(int n) {
        if (n <= 1) {
            return 1;
        }
        long prev = 1;
        long cur = 1;
        for (int i = 2; i <= n; i++) {
            long next = prev + cur;
            prev = cur;
            cur = next;
        }
        return cur;
    }
}
```

### When to use / pitfalls
- Values grow quickly; for large n, the result overflows `long` after about 90 steps. Say so, or use `BigInteger`.
- Name the three steps out loud: the state, the recurrence, and the base cases.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 7. Coin change: fewest coins to make an amount

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Let `dp[a]` be the fewest coins that make amount `a`. Then `dp[a] = 1 + min(dp[a - c])` over all coins `c` no larger than `a`. The bottom-up table is O(amount * coins) time and O(amount) space. The plain recursion explores the same choices repeatedly and is exponential.

### Explanation
**Approach 1: recursion without memoisation.** Exponential time.

```java
class CoinChangeRecursive {
    static int minCoins(int[] coins, int amount) {
        if (amount == 0) {
            return 0;
        }
        if (amount < 0) {
            return -1;                       // dead end
        }
        int best = -1;
        for (int c : coins) {
            int sub = minCoins(coins, amount - c);
            if (sub >= 0 && (best == -1 || sub + 1 < best)) {
                best = sub + 1;
            }
        }
        return best;
    }
}
```

**Approach 2: bottom-up table.** O(amount * coins) time, O(amount) space.

```java
import java.util.Arrays;

class CoinChangeTable {
    static int minCoins(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);         // larger than any real answer
        dp[0] = 0;
        for (int a = 1; a <= amount; a++) {
            for (int c : coins) {
                if (c <= a && dp[a - c] + 1 < dp[a]) {
                    dp[a] = dp[a - c] + 1;
                }
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }
}
```

### When to use / pitfalls
- This is the unbounded version: each coin can be reused. Looping amounts in the outer loop and coins in the inner loop handles that.
- Return -1 when the amount cannot be made, and say so in the answer.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 8. Length of the longest increasing subsequence

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The quadratic dynamic programming solution checks every earlier element: O(n^2) time, O(n) space. A faster solution keeps the smallest tail value for each subsequence length and places each new number with binary search: O(n log n) time, O(n) space.

### Explanation
**Approach 1: dynamic programming.** O(n^2) time, O(n) space.

```java
import java.util.Arrays;

class LisQuadratic {
    static int length(int[] nums) {
        if (nums.length == 0) {
            return 0;
        }
        int[] dp = new int[nums.length];     // dp[i] = best length ending at i
        Arrays.fill(dp, 1);
        int best = 1;
        for (int i = 1; i < nums.length; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) {
                    dp[i] = Math.max(dp[i], dp[j] + 1);
                }
            }
            best = Math.max(best, dp[i]);
        }
        return best;
    }
}
```

**Approach 2: patience sorting with binary search.** O(n log n) time, O(n) space.

```java
class LisBinarySearch {
    static int length(int[] nums) {
        int[] tails = new int[nums.length];  // tails[k] = smallest tail of an increasing run of length k + 1
        int size = 0;
        for (int x : nums) {
            int lo = 0;
            int hi = size;
            while (lo < hi) {
                int mid = (lo + hi) >>> 1;
                if (tails[mid] < x) {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            tails[lo] = x;                   // replace the first tail that is >= x
            if (lo == size) {
                size++;
            }
        }
        return size;
    }
}
```

### When to use / pitfalls
- The `tails` array does not hold the actual subsequence. Reconstructing it needs extra bookkeeping.
- For a non-decreasing subsequence, use `tails[mid] <= x` in the binary search.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 9. Longest common subsequence of two strings

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Let `dp[i][j]` be the LCS length of the first `i` characters of one string and the first `j` of the other. If the characters match, add one to the diagonal value; otherwise take the larger of the two neighbours. This is O(n * m) time and space. Keeping only two rows gives O(min(n, m)) space if you rearrange the loops.

### Explanation
**Approach 1: full 2D table.** O(n * m) time, O(n * m) space.

```java
class LcsTable {
    static int length(String a, String b) {
        int n = a.length();
        int m = b.length();
        int[][] dp = new int[n + 1][m + 1];
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= m; j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[n][m];
    }
}
```

**Approach 2: two rolling rows.** O(n * m) time, O(m) space.

```java
class LcsRolling {
    static int length(String a, String b) {
        int m = b.length();
        int[] prev = new int[m + 1];
        for (int i = 1; i <= a.length(); i++) {
            int[] cur = new int[m + 1];
            for (int j = 1; j <= m; j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    cur[j] = prev[j - 1] + 1;
                } else {
                    cur[j] = Math.max(prev[j], cur[j - 1]);
                }
            }
            prev = cur;
        }
        return prev[m];
    }
}
```

### When to use / pitfalls
- LCS returns a length. To return the subsequence, walk back through the table.
- Edit distance uses almost the same table, with insert, delete, and replace costs.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 10. 0/1 knapsack: maximise value within a capacity

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Each item is either taken or left. A two-dimensional table over items and capacities is O(n * W) time and space. A one-dimensional array works if you loop capacities from high to low, so each item is counted at most once: O(n * W) time and O(W) space.

### Explanation
**Approach 1: 2D table.** O(n * W) time and space.

```java
class KnapsackTable {
    static int best(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];
        for (int i = 1; i <= n; i++) {
            for (int w = 0; w <= capacity; w++) {
                dp[i][w] = dp[i - 1][w];                       // skip item i
                if (weights[i - 1] <= w) {
                    dp[i][w] = Math.max(dp[i][w],
                            dp[i - 1][w - weights[i - 1]] + values[i - 1]);   // take item i
                }
            }
        }
        return dp[n][capacity];
    }
}
```

**Approach 2: one row, capacities in reverse.** O(n * W) time, O(W) space.

```java
class KnapsackRow {
    static int best(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1];
        for (int i = 0; i < weights.length; i++) {
            for (int w = capacity; w >= weights[i]; w--) {   // reverse order: each item used once
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
        return dp[capacity];
    }
}
```

### When to use / pitfalls
- Looping capacities upward would let the same item be used repeatedly, which is the unbounded knapsack. Know the difference.
- Use `long` for values if totals may be large.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 11. Minimum path sum in a grid

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Only moves right and down are allowed, so the minimum sum to reach a cell is its value plus the smaller of the cell above and the cell to the left. This is O(R * C) time. The table can be filled in place to use O(1) extra space.

### Explanation
**Approach 1: separate table.** O(R * C) time and space.

```java
class MinPathSumTable {
    static int solve(int[][] grid) {
        int rows = grid.length;
        int cols = grid[0].length;
        int[][] dp = new int[rows][cols];
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (r == 0 && c == 0) {
                    dp[r][c] = grid[r][c];
                } else if (r == 0) {
                    dp[r][c] = dp[r][c - 1] + grid[r][c];
                } else if (c == 0) {
                    dp[r][c] = dp[r - 1][c] + grid[r][c];
                } else {
                    dp[r][c] = Math.min(dp[r - 1][c], dp[r][c - 1]) + grid[r][c];
                }
            }
        }
        return dp[rows - 1][cols - 1];
    }
}
```

**Approach 2: in place.** O(R * C) time, O(1) extra space. Overwrites the input.

```java
class MinPathSumInPlace {
    static int solve(int[][] grid) {
        int rows = grid.length;
        int cols = grid[0].length;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (r == 0 && c == 0) {
                    continue;
                } else if (r == 0) {
                    grid[r][c] += grid[r][c - 1];
                } else if (c == 0) {
                    grid[r][c] += grid[r - 1][c];
                } else {
                    grid[r][c] += Math.min(grid[r - 1][c], grid[r][c - 1]);
                }
            }
        }
        return grid[rows - 1][cols - 1];
    }
}
```

### When to use / pitfalls
- State whether you may modify the input before choosing the in-place version.
- A problem that allows moves in all four directions is a shortest-path problem, not this DP.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---


**Next:** [Part 3](graphs-dp-part-3.md)
