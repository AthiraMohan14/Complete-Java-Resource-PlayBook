# How to Approach Coding Questions

A repeatable method for live coding rounds: what the common question categories look like, the steps to follow, a complexity cheat sheet, and the techniques that solve most problems.

---

## Question Categories

Most coding rounds draw from a small set of topics. Know which technique belongs to which category.

### Arrays and strings
- Two pointers, sliding window, and prefix sums.
- Substring and pattern work, such as finding the longest run without repeats.
- Typical questions: two sum, maximum subarray, merging intervals.
- Covered in [Arrays and strings](arrays-strings-part-1.md).

### Linked lists
- Pointer manipulation: reversal, merging, and finding the middle node.
- Cycle detection with a slow and a fast pointer.
- Keep a dummy head node when the first node may change.
- Covered in [Linked lists, stacks, and trees](linked-lists-trees-part-1.md).

### Trees and graphs
- Breadth-first search (BFS) for shortest paths in unweighted graphs and level-order traversal.
- Depth-first search (DFS) for connectivity, cycles, and tree paths.
- Binary search trees: insert, delete, validate, and find the lowest common ancestor.
- Shortest path with non-negative weights (Dijkstra), and topological sort for ordering tasks with dependencies.
- Covered in [Graphs, dynamic programming, and backtracking](graphs-dp-part-1.md).

### Dynamic programming
- Use it when a problem has overlapping subproblems and optimal substructure.
- Top-down (memoization) is often easier to write first; bottom-up (tabulation) avoids recursion depth limits and is often faster.
- Start by defining the state in words, then the transition, then the base cases.

### Stacks and queues
- Stacks match nested structures: valid brackets, expression evaluation, undo.
- The monotonic stack finds the next greater or smaller element in O(n).
- Queues drive BFS and task scheduling. Java's `ArrayDeque` is the usual choice; prefer it over `LinkedList` for queues.

### Sorting and searching
- Know the cost of merge sort, quick sort, and heap sort, and when each is stable or in-place.
- Binary search works on any monotonic condition, not only on a sorted array. Pick the bounds carefully to avoid off-by-one errors.
- Counting sort and radix sort beat comparison sorts when keys are small integers.

### Math and logic
- Number theory: primes, greatest common divisor, modular arithmetic.
- Combinatorics: counting permutations and combinations, and when they explode.
- Bit manipulation: `&`, `|`, `^`, shifts, and checking or clearing a single bit.
- Probability and simulation questions usually reduce to a counting argument.

### Hash tables and sets
- Frequency counting, grouping, and "have I seen this before" checks.
- Finding duplicates, unique elements, and pairs that sum to a target.
- Remember that hash-based lookups are O(1) on average, not in the worst case.

---

## Approach in Six Steps

Interviewers grade the process as much as the answer. Work through these steps in order, and say what you are doing as you go.

### Step 1: Understand the problem
- Read the statement twice. Write down the inputs, the outputs, and the constraints (size of `n`, value ranges, whether the input can be empty).
- Ask clarifying questions. Are duplicates allowed? Can values be negative? Is the input sorted? Should the answer be a value or the indexes?
- Work one small example by hand. Then work one edge case, such as an empty input or a single element.

### Step 2: Start with brute force
- State the simplest correct solution, even if it is slow.
- Give its time and space complexity. This shows you understand the problem and gives you a baseline to improve on.
- A correct slow answer scores better than an unfinished fast one.

### Step 3: Optimise
- Ask what work is repeated. Repeated searches suggest a hash map. Repeated range queries suggest prefix sums. Repeated minimum or maximum queries suggest a heap.
- Ask whether the input order helps. Sorted input often allows two pointers or binary search.
- Ask whether a trade-off is acceptable: more memory for less time, or a second pass for less memory.

### Step 4: Code it
- Name variables for what they hold: `left` and `right`, not `i` and `j`, when they are pointers.
- Keep helper methods small. Add a comment only where the logic is not obvious.
- Handle the empty input before the main loop.
- Follow the language conventions. In Java, use the collections interfaces (`List`, `Map`) in declarations.

### Step 5: Test
- Trace your code on the example from Step 1, one line at a time.
- Run the edge cases: empty input, one element, all negative values, all equal values, the largest input size.
- Check off-by-one errors at both ends of every loop and every index.

### Step 6: Review
- Can the solution be simpler? Could a standard library method do the work?
- What is the final complexity? Did it match what you claimed?
- Mention any alternatives you would consider with more time, such as a streaming version for input that does not fit in memory.

---

## Complexity Cheat Sheet

### Time, from best to worst
- O(1): constant time, such as an array index or a hash lookup on average.
- O(log n): binary search, balanced tree operations.
- O(n): one pass over the input.
- O(n log n): comparison sorts, and many divide-and-conquer solutions.
- O(n²): nested loops over the same input, bubble sort.
- O(n³): three nested loops, some dynamic programming tables.
- O(2ⁿ): all subsets, many naive recursive solutions.
- O(n!): all permutations.

### Space
- O(1): only a fixed number of variables.
- O(log n): recursion depth of a balanced divide-and-conquer.
- O(n): an extra array, a hash map, or a recursion stack that grows with the input.
- O(n²): a two-dimensional table, such as a grid DP.

### Things that surprise candidates
- A recursive function uses stack space even when it allocates nothing else.
- Building a string by repeated concatenation in a loop is O(n²) in Java; use `StringBuilder`.
- `ArrayList.contains` is O(n). Using it inside a loop turns an O(n) pass into O(n²).

---

## Common Techniques

| Technique | Use case | Example problem |
|-----------|----------|-----------------|
| **Two pointers** | Sorted array, palindrome, pair with a sum | Check a palindrome, pair with target sum |
| **Sliding window** | Contiguous subarray or substring with a condition | Longest substring without repeating characters |
| **Binary search** | Sorted data, or a monotonic yes/no condition | Find the first index where a condition holds |
| **Hash map** | Counting, grouping, storing earlier results | Group anagrams, pair with a sum |
| **Heap** | K largest or smallest, running median | Top K frequent elements |
| **Stack** | Last in, first out; matching; next greater element | Valid parentheses, next greater element |
| **BFS and DFS** | Graphs, trees, connected regions | Count islands, shortest path in a grid |
| **Dynamic programming** | Overlapping subproblems, optimisation | Coin change, longest increasing subsequence |
| **Backtracking** | Build candidates and undo choices | Subsets, permutations, N-Queens |
| **Greedy** | A locally best choice is provably globally best | Interval scheduling, activity selection |

Two notes on Java:
- `PriorityQueue` is a min-heap by default. For a max-heap, pass `Comparator.reverseOrder()`.
- A sliding window keeps two indexes and a count or set of what is inside the window. Move the right index on every step and the left index only when the window breaks the rule.

---

## Worked Example: Two Sum

**Problem:** Given an array of integers and a target, return the indexes of two different elements whose values add up to the target. Assume exactly one answer exists.

**Brute force:** check every pair. O(n²) time, O(1) space.

**Optimal:** walk the array once and store each value's index in a hash map. For each value, look up `target - value` in the map. If it is there, you have the answer. O(n) time, O(n) space.

```java
import java.util.HashMap;
import java.util.Map;

class TwoSum {
    static int[] bruteForce(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] + nums[j] == target) {
                    return new int[] {i, j};
                }
            }
        }
        return new int[0];
    }

    static int[] withHashMap(int[] nums, int target) {
        Map<Integer, Integer> indexByValue = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            Integer other = indexByValue.get(target - nums[i]);
            if (other != null) {
                return new int[] {other, i};
            }
            indexByValue.put(nums[i], i);
        }
        return new int[0];
    }
}
```

The hash map version checks for a match before it stores the current value. That order matters: it stops `[3, 3]` with target `6` from pairing an element with itself.

---

## Interview Tips

**Do**
- Think aloud. Say what you are considering and why you reject an option.
- Clarify requirements before writing code.
- Start with brute force, then optimise, and state the complexity of each.
- Test on the examples and on edge cases before you say you are done.
- Use clear names and consistent indentation. Readable code is easier to review.

**Do not**
- Start coding before you understand the input and output.
- Over-engineer the first version.
- Ignore edge cases such as empty input or duplicates.
- Leave a known bug in place and hope it goes unnoticed.
- Forget to state the complexity at the end.

If you are stuck, go back to a small example and write out the steps by hand. Most breakthroughs come from noticing a repeated calculation, not from a new idea.

---

## Practice Resources

- Practice platforms: LeetCode, HackerRank, and CodeSignal. Medium-difficulty problems are the usual interview level.
- Practice by category, in the order from [Arrays and strings](arrays-strings-part-1.md) through [Linked lists](linked-lists-trees-part-1.md) and [Graphs and dynamic programming](graphs-dp-part-1.md).
- Time yourself. A typical budget is 30 to 45 minutes per problem, including explanation.
- Re-solve problems you got wrong after a few days, without looking at your earlier answer.
- For Java-specific tasks, see [Java-specific coding problems](java-coding-problems-part-1.md).

---

## Quick Recap

- Identify the category first, because it suggests the technique.
- Follow the six steps: understand, brute force, optimise, code, test, review.
- Use the complexity cheat sheet to justify each choice you make.
- Typical wins: a hash map for lookups, two pointers for sorted data, a heap for top-K, BFS for shortest paths.
- Explain your trade-offs out loud, and test before you stop.

**See also:** [Interview questions overview](../index.md), [Stream API problems](stream-api-problems-part-1.md), [Java-specific coding problems](java-coding-problems-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md)
