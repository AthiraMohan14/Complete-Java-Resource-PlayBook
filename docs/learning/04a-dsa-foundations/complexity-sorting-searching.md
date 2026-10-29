# Complexity, Sorting and Searching

Big-O notation describes how the work or memory of an algorithm grows with the size of its input. Interviewers expect you to state time and space for every answer you give, and to know the standard costs of sorting, searching, and the common data structures.

## Core concepts

### Growth rates

From slowest-growing to fastest-growing:

| Class | Typical example | Growth when n doubles |
|---|---|---|
| O(1) | Array index, hash lookup (average) | No change |
| O(log n) | Binary search | Adds one step |
| O(n) | One pass over an array | Doubles |
| O(n log n) | Efficient comparison sort | A little more than doubles |
| O(n²) | Nested loops over the same input | Quadruples |
| O(2ⁿ) | Enumerating all subsets | Squares the work |
| O(n!) | Enumerating all permutations | Explodes quickly |

Drop constants and lower-order terms: `3n² + 5n + 2` is O(n²). Give time and space separately. Say whether a bound is worst case, average case, or amortised, because a hash table's O(1) is an average, and a growing `ArrayList` is amortised O(1) per append.

### Operation costs of common structures

| Structure | Access by index | Search | Insert | Delete | Notes |
|---|---|---|---|---|---|
| Array | O(1) | O(n) | O(n) | O(n) | Fixed size; shifting costs on insert and delete |
| `ArrayList` (dynamic array) | O(1) | O(n) | O(1) amortised at the end, O(n) in the middle | O(n) | Resizes now and then |
| Linked list | O(n) | O(n) | O(1) at a known node | O(1) at a known node | Finding the node costs O(n) |
| `ArrayDeque` (stack or queue) | None | O(n) | O(1) at either end | O(1) at either end | No index access in the API |
| `HashMap` / `HashSet` | None | O(1) average | O(1) average | O(1) average | Many collisions degrade it toward O(n) |
| `TreeMap` / `TreeSet` | None | O(log n) | O(log n) | O(log n) | Keeps keys sorted; supports range queries |
| `PriorityQueue` (heap) | None | O(n) | O(log n) | O(log n) to remove the top | Peek at the top is O(1) |

The hash table row assumes a good hash function and a load factor kept in check. Java's `HashMap` treeifies crowded buckets, which limits the damage from many collisions. See [Greedy, Bit Manipulation and Hashing](../04b-dsa-advanced/greedy-bit-manipulation-hashing.md).

### Sorting algorithms

| Algorithm | Average time | Worst time | Extra space | Stable |
|---|---|---|---|---|
| Quicksort | O(n log n) | O(n²) | O(log n) | No |
| Mergesort | O(n log n) | O(n log n) | O(n) | Yes |
| Heapsort | O(n log n) | O(n log n) | O(1) | No |
| Insertion sort | O(n²) | O(n²) | O(1) | Yes |

Quicksort's worst case appears with consistently bad pivots. Random or median-of-three pivot choices make it rare. Insertion sort is slow in general, but it is fast on small or nearly sorted input, which is why hybrid sorts use it for small ranges. Heapsort guarantees O(n log n) with no extra array, but it is not stable and is slower in practice than quicksort on typical data.

**Java.** `Arrays.sort` on primitive arrays uses a dual-pivot quicksort. Stability does not matter for primitives, because equal values are indistinguishable. `Arrays.sort` on object arrays, `Collections.sort`, and `List.sort` use TimSort, a stable merge-based sort with O(n log n) worst-case time.

### Searching

- **Linear search** checks each element. It is O(n) and works on unsorted data.
- **Binary search** halves a sorted range on each step, for O(log n) time. The same idea works on any monotonic condition, not just a sorted array.

Common variants:

- **First or last occurrence.** When the middle matches, record it and keep searching in the half that could hold an earlier or later match.
- **Rotated sorted array.** At each step, decide which half is still sorted and check whether the target lies in it.
- **Search on the answer space.** When a yes-or-no check is monotonic in some quantity, binary search over that quantity. For example, find the smallest capacity that lets a job finish in d days.

A lower-bound search finds the first index whose value is at least the target. Its half-open range makes the boundary rules easy to get right:

```java
public class LowerBound {
    // Returns the first index i with a[i] >= target, or a.length if none
    static int lowerBound(int[] a, int target) {
        int lo = 0;
        int hi = a.length;                     // search the range [lo, hi)
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (a[mid] < target) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        return lo;
    }

    public static void main(String[] args) {
        int[] sorted = {1, 2, 2, 2, 5, 8};
        System.out.println(lowerBound(sorted, 2));   // 1
        System.out.println(lowerBound(sorted, 6));   // 5
    }
}
```

`Arrays.binarySearch` returns the index of a matching element, but when the array holds duplicates, the index it finds is not guaranteed to be the first one. When the key is missing, it returns a negative value that encodes the insertion point.

### Core patterns and where they live

| Pattern | Use it for | Covered in |
|---|---|---|
| Two pointers | Pairs in sorted arrays, palindromes, removing duplicates | [Arrays & Strings](arrays-strings.md) |
| Sliding window | Longest valid substring, best sum over a fixed size | [Arrays & Strings](arrays-strings.md) |
| Recursion and backtracking | Subsets, permutations, combinations, N-queens | [Backtracking and Recursion](../04b-dsa-advanced/backtracking-recursion.md) |
| BFS and DFS | Trees and graphs; BFS for shortest unweighted paths; topological sort for DAGs | [Trees](trees.md), [Graphs](../04b-dsa-advanced/graphs.md) |
| Dynamic programming | Overlapping subproblems with optimal substructure | [Dynamic Programming](../04b-dsa-advanced/dynamic-programming.md) |
| Greedy | Locally best choices that provably lead to a global best (interval scheduling, Huffman coding) | [Greedy, Bit Manipulation and Hashing](../04b-dsa-advanced/greedy-bit-manipulation-hashing.md) |

Some algorithms are must-know examples and appear in several patterns. Kadane's algorithm for the maximum subarray sum is in [Dynamic Programming](../04b-dsa-advanced/dynamic-programming.md). Dijkstra's shortest-path algorithm (non-negative weights), Union-Find for connectivity, and Floyd's cycle detection are covered in [Graphs](../04b-dsa-advanced/graphs.md) and [Linked Lists](linked-lists.md).

### Choosing a data structure

| Need | Pick | Why |
|---|---|---|
| Lookup by key | `HashMap` / `HashSet` | O(1) average |
| Sorted keys, range queries | `TreeMap` / `TreeSet` | O(log n) operations, ordered iteration |
| First in, first out | `ArrayDeque` (`offer` and `poll`) | O(1) at both ends |
| Last in, first out | `ArrayDeque` (`push` and `pop`) | Avoid the legacy `Stack` class, which extends the synchronised `Vector` |
| Repeated min or max, top-k | `PriorityQueue` | O(log n) per update |
| Prefix queries on strings | Trie | Cost depends on word length |
| Fixed size with index access | Array | O(1) by index |

## How it works / Step by step

A reliable answer process for a coding question:

1. Clarify the input, its size limits, and the expected output, including edge cases.
2. Walk through a small example by hand.
3. State a brute-force solution and its time and space cost.
4. Find the repeated work or the wasted search, and optimise.
5. Write clean code with clear variable names.
6. Test the edges: empty input, one element, duplicates, negative values, and the largest input size.
7. State the final time and space complexity, and say why.

## Common pitfalls

- Quoting only the average case for a hash table, without mentioning collisions.
- Forgetting space cost, including the call stack of a recursive solution.
- Assuming quicksort is always O(n log n), without considering pivot choice on adversarial input.
- Off-by-one errors in binary search. Choose a bound convention (closed or half-open) and keep it.
- Assuming `Arrays.binarySearch` returns the first of several equal values.
- Using `java.util.Stack` in new code instead of `ArrayDeque`.

!!! tip "Interview tip"
    **Q: Which sort would you use for a list of objects in Java, and why?**
    Use `List.sort` or `Collections.sort`, which run TimSort. It is stable, which matters when you sort by one field after another, and it runs in O(n log n) worst case. For primitive arrays, `Arrays.sort` is usually faster, and stability does not matter there. Mention that quicksort's worst case is O(n²).

## Quick interview prep checklist

- **Arrays:** binary search, sliding window, two pointers, prefix sums.
- **Trees:** BFS and DFS, the three depth-first orders, BST operations, balanced trees.
- **Graphs:** BFS and DFS, shortest paths (Dijkstra for non-negative weights, Bellman-Ford when weights can be negative), topological sort.
- **Dynamic programming:** identify the subproblems, then pick memoisation or tabulation.
- **Complexity:** be able to rank O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ), and O(n!), and justify each answer.

## Quick recap

- Rank growth rates and state time and space for every answer.
- Hash tables give O(1) average lookups; tree maps give O(log n) with order.
- Mergesort and heapsort guarantee O(n log n); quicksort is fastest on average but has an O(n²) worst case.
- Binary search works on any monotonic condition, and the boundary rules need a clear convention.
- Choose the data structure from the operation you need most often.

**See also:** [Arrays & Strings](arrays-strings.md), [Heaps and Tries](heaps-and-tries.md), [Trees](trees.md), [Dynamic Programming](../04b-dsa-advanced/dynamic-programming.md), [DSA Foundations](index.md)
