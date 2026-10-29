# Graphs, Dynamic Programming, and Backtracking Coding Questions (Part 3 of 3)

Continued from [Part 2](graphs-dp-part-2.md).

---

## 12. Generate all permutations (backtracking)

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Backtracking builds a permutation one position at a time and undoes each choice before trying the next. There are n! permutations, each of length n, so the time is O(n * n!) and the space is O(n) for the recursion, excluding output. Swap-based and used-flag approaches have the same complexity.

### Explanation
**Approach 1: swap in place.** O(n * n!) time, O(n) stack.

```java
import java.util.ArrayList;
import java.util.List;

class PermutationsSwap {
    static List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> out = new ArrayList<>();
        backtrack(nums, 0, out);
        return out;
    }

    private static void backtrack(int[] a, int start, List<List<Integer>> out) {
        if (start == a.length) {
            List<Integer> perm = new ArrayList<>();
            for (int x : a) {
                perm.add(x);
            }
            out.add(perm);
            return;
        }
        for (int i = start; i < a.length; i++) {
            swap(a, start, i);
            backtrack(a, start + 1, out);
            swap(a, start, i);               // undo the swap
        }
    }

    private static void swap(int[] a, int i, int j) {
        int tmp = a[i];
        a[i] = a[j];
        a[j] = tmp;
    }
}
```

**Approach 2: used flags and a path list.** O(n * n!) time, O(n) extra space.

```java
import java.util.ArrayList;
import java.util.List;

class PermutationsUsed {
    static List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> out = new ArrayList<>();
        backtrack(nums, new boolean[nums.length], new ArrayList<>(), out);
        return out;
    }

    private static void backtrack(int[] nums, boolean[] used,
                                  List<Integer> path, List<List<Integer>> out) {
        if (path.size() == nums.length) {
            out.add(new ArrayList<>(path));  // copy: path keeps changing
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) {
                continue;
            }
            used[i] = true;
            path.add(nums[i]);
            backtrack(nums, used, path, out);
            path.remove(path.size() - 1);
            used[i] = false;
        }
    }
}
```

### When to use / pitfalls
- Add a copy of the current path to the results, not the path object itself.
- Duplicates in the input need sorting and a "skip if same as previous" rule; say so if the problem allows duplicates.
- N-Queens and Sudoku use the same choose, recurse, undo pattern with pruning.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md), [Coding: Java problems](java-coding-problems-part-1.md)

</details>

---

## Quick recap

- BFS gives shortest paths on unweighted graphs; Dijkstra adds non-negative weights.
- Kahn's algorithm and three-state DFS both handle dependency cycles.
- Union-find answers connectivity questions quickly.
- For DP, name the state, the recurrence, the base cases, and the order of filling.
- Reduce space by keeping only the previous row or the last two values.
- For backtracking, undo each choice and copy results before storing them.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Linked lists and trees](linked-lists-trees-part-1.md), [Stream API problems](stream-api-problems-part-1.md)
