# Backtracking and Recursion

Recursion solves a problem by reducing it to smaller instances of itself. Backtracking extends recursion to search: it builds a candidate solution step by step, abandons a path as soon as it cannot succeed, and undoes its last choice before trying the next one. Interviewers use these to test whether you can define base cases, manage state, and prune the search.

## Core concepts

### Recursion: base cases and recurrence

Every recursive method needs:

1. A **base case** that returns without recursing.
2. A **recursive case** that moves toward the base case.

```java
public class Factorial {
    static long factorial(int n) {
        if (n <= 1) return 1;               // base case
        return n * factorial(n - 1);        // recursive case
    }

    public static void main(String[] args) {
        System.out.println(factorial(10));  // 3628800
    }
}
```

Each call adds a frame to the call stack. Java's default thread stack holds a limited number of frames, so deep recursion throws `StackOverflowError`. Typical default stacks handle a few thousand to tens of thousands of frames, depending on frame size; do not rely on an exact number.

### Tail recursion

A call is in tail position when nothing happens after it returns. A compiler can reuse the current frame for a tail call. Java does not guarantee tail-call optimisation, so tail-recursive code still grows the stack in practice.

```java
public class TailSum {
    // Tail-recursive in form, but the JVM does not eliminate the frames
    static long sumTo(long n, long acc) {
        return n == 0 ? acc : sumTo(n - 1, acc + n);
    }

    // Same result with a loop, which is the safe choice in Java
    static long sumToLoop(long n) {
        long acc = 0;
        for (long i = n; i > 0; i--) {
            acc += i;
        }
        return acc;
    }
}
```

When recursion depth can be large (for example, a linked list of a million nodes), convert to an explicit loop or an explicit `Deque` used as a stack.

### Backtracking: choose, explore, un-choose

The template for backtracking has three steps inside a loop over choices:

```text
for each choice c:
    if c is allowed:
        apply c            // choose
        recurse            // explore
        undo c             // un-choose (backtrack)
```

**Permutations.** Generate all orderings of distinct numbers.

```java
import java.util.*;

public class Permutations {
    static List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> out = new ArrayList<>();
        build(nums, new boolean[nums.length], new ArrayList<>(), out);
        return out;
    }

    private static void build(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> out) {
        if (path.size() == nums.length) {
            out.add(new ArrayList<>(path));          // copy: path keeps changing
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            used[i] = true;
            path.add(nums[i]);
            build(nums, used, path, out);
            path.remove(path.size() - 1);            // undo
            used[i] = false;
        }
    }

    public static void main(String[] args) {
        System.out.println(permute(new int[]{1, 2, 3}).size());   // 6
    }
}
```

**N-Queens.** Place `n` queens so none attack each other. Track columns and both diagonals with boolean arrays, so each check is O(1).

```java
public class NQueens {
    static int count(int n) {
        return place(0, n, new boolean[n], new boolean[2 * n], new boolean[2 * n]);
    }

    // cols: used columns; d1: row + col diagonals; d2: row - col diagonals (offset by n)
    private static int place(int row, int n, boolean[] cols, boolean[] d1, boolean[] d2) {
        if (row == n) return 1;
        int total = 0;
        for (int c = 0; c < n; c++) {
            if (cols[c] || d1[row + c] || d2[row - c + n]) continue;
            cols[c] = d1[row + c] = d2[row - c + n] = true;
            total += place(row + 1, n, cols, d1, d2);
            cols[c] = d1[row + c] = d2[row - c + n] = false;
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(count(6));   // 4
    }
}
```

**Sudoku.** Fill empty cells one at a time, trying digits 1 to 9 and checking row, column, and box constraints. Backtrack when a cell has no valid digit. Pruning is the key: choosing the empty cell with the fewest candidates is a common speed-up.

**Subsets and combinations.** The same template, but each choice decides whether to include an element and the recursion starts from the next index. This avoids duplicates.

### Pruning

Pruning cuts branches that cannot lead to a valid answer. Examples: sort input and skip repeated values at the same depth; stop when the running sum already exceeds the target; check constraints before recursing, not after.

## How it works / Step by step

1. Define the state: what the partial solution looks like at each level.
2. Define the base case: when is a candidate complete?
3. Write the loop of choices and the validity check for each.
4. Apply the choice, recurse, then undo the choice. Undo must restore exactly what you changed.
5. Copy the partial solution when you store a result. Storing the reference stores a list that will later be emptied.
6. Estimate the cost: backtracking is usually exponential, so prune to make it practical.

## Common pitfalls

- Forgetting to undo the choice, so later branches see stale state.
- Adding `path` to the results without copying it: every stored entry ends up identical.
- Missing base cases, which cause infinite recursion.
- Assuming recursion is free. Each call uses stack memory.
- Using recursion for input sizes that can exceed the stack depth; convert to a loop or an explicit stack.
- Duplicate results from repeated input values. Sort and skip equal neighbours at the same level.

!!! tip "Interview tip"
    **Q: How is backtracking different from brute force?**
    Brute force enumerates every candidate and checks each one at the end. Backtracking builds candidates incrementally and abandons a partial candidate as soon as it violates a constraint. The search tree is the same shape, but the pruned branches are never explored. Worst case is still exponential; say so.

## Quick recap

- Every recursive method needs a base case that makes progress toward it.
- Java does not optimise tail calls; deep recursion can throw `StackOverflowError`.
- Backtracking follows choose, explore, un-choose.
- Copy partial results before storing them.
- Prune early (constraint checks before recursing) to make exponential search practical.

**See also:** [Graphs](graphs.md) (DFS is recursion over a graph), [Dynamic Programming](dynamic-programming.md), [Greedy, Bit Manipulation and Hashing](greedy-bit-manipulation-hashing.md)
