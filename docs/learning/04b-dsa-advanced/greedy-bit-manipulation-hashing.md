# Greedy, Bit Manipulation and Hashing

These three techniques are often the fastest route to an answer once you spot the pattern. Greedy algorithms make the locally best choice at each step, bit manipulation works on the binary form of numbers, and hashing gives constant-time lookup. Interviewers ask about them to see whether you can prove a greedy choice is safe and whether you know the trade-offs of hash-based structures.

## Core concepts

### Greedy algorithms

A greedy algorithm picks the best-looking option at each step and never reconsiders. It is correct only when the problem has the **greedy choice property** (a local best choice can be part of a global optimum) and **optimal substructure**. Proving this is part of the answer.

Classic example: maximum number of non-overlapping intervals. Sort by end time, then take each interval that starts after the last chosen end.

```java
import java.util.Arrays;

public class Intervals {
    static int maxNonOverlapping(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[1], b[1]));   // sort by end
        int count = 0;
        int end = Integer.MIN_VALUE;
        for (int[] iv : intervals) {
            if (iv[0] >= end) {
                count++;
                end = iv[1];
            }
        }
        return count;
    }

    public static void main(String[] args) {
        int[][] iv = {{1, 3}, {2, 4}, {3, 5}, {6, 7}};
        System.out.println(maxNonOverlapping(iv));   // 3
    }
}
```

Other greedy classics: Huffman coding, Kruskal and Prim (see [Graphs](graphs.md)), interval scheduling, and jump game. Greedy fails for coin change with arbitrary denominations; use [dynamic programming](dynamic-programming.md) there.

A quick check for correctness: try a small counterexample. If the greedy choice can be beaten by some other choice on a small input, the greedy approach is wrong.

### Bit manipulation

Java's integer types are two's complement. Useful operators: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT), `<<` (left shift), `>>` (arithmetic right shift), `>>>` (unsigned right shift).

| Expression | Meaning |
|---|---|
| `x & (x - 1)` | Clears the lowest set bit |
| `x & -x` | Isolates the lowest set bit |
| `x ^ x` | `0` |
| `x ^ 0` | `x` |
| `(x >> i) & 1` | Value of bit `i` |
| `x \| (1 << i)` | Sets bit `i` |
| `x & ~(1 << i)` | Clears bit `i` |

XOR cancels pairs, so finding the single number that appears once among pairs takes O(n) time and O(1) space:

```java
public class SingleNumber {
    static int singleNumber(int[] nums) {
        int result = 0;
        for (int n : nums) {
            result ^= n;          // paired values cancel to 0
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(singleNumber(new int[]{4, 1, 2, 1, 2}));   // 4
    }
}
```

Counting set bits and checking powers of two:

```java
public class Bits {
    public static void main(String[] args) {
        int x = 0b1011;                              // 11
        System.out.println(Integer.bitCount(x));     // 3
        System.out.println((x & (x - 1)) == 0);      // false: not a power of two
        System.out.println(Integer.highestOneBit(x)); // 8
        System.out.println(Integer.toBinaryString(x)); // 1011
    }
}
```

Subsets can be enumerated with a bitmask: for `n` elements, the integers `0` to `2ⁿ - 1` each describe one subset. This is the basis of bitmask DP.

Watch the shift distance: for `int`, `1 << 32` equals `1 << 0` in Java because the shift count is taken modulo 32. Use `1L << k` for shifts of 32 or more.

### Hashing

A hash function maps a key to an index in a table. Lookup, insert, and delete take expected O(1) time with a good hash function. `HashMap` and `HashSet` are the Java implementations.

**The `equals` and `hashCode` contract.** If `a.equals(b)`, then `a.hashCode() == b.hashCode()`. Breaking this makes `HashSet` and `HashMap` lookups fail. Records generate both methods correctly:

```java
import java.util.HashSet;
import java.util.Set;

public class HashContract {
    record Point(int x, int y) { }   // equals and hashCode generated from the components

    public static void main(String[] args) {
        Set<Point> seen = new HashSet<>();
        seen.add(new Point(1, 2));
        System.out.println(seen.contains(new Point(1, 2)));   // true
    }
}
```

Do not use mutable objects as keys if their hash-relevant fields can change after insertion. The entry becomes unreachable.

**Collision handling.** Two keys can map to the same bucket. Common strategies:

- **Separate chaining:** each bucket holds a list. Java's `HashMap` uses this. When a bucket grows long, Java converts it to a tree (treeification) to keep worst-case lookup at O(log n). Treeification happens only when a bucket holds 8 or more entries and the table has at least 64 slots; otherwise the table resizes instead. The tree bins order keys by `Comparable` when they provide it.
- **Open addressing:** on collision, probe for another empty slot (linear, quadratic, or double hashing). Needs a lower load factor.

The default load factor of `HashMap` is 0.75; a resize doubles the table when the threshold is exceeded.

**Rolling hashes and Rabin-Karp.** A polynomial rolling hash updates in O(1) when the window slides, so substring search runs in expected O(n + m). Equal hashes do not prove equal strings, so verify a match character by character.

**Suffix arrays.** A suffix array lists the starting indexes of all suffixes in sorted order. Build it in O(n log n) with doubling, or O(n log² n) with simple sorting. Combined with an LCP (longest common prefix) array, it answers substring queries quickly. Explain the idea and its use in text search; full construction is rarely required in interviews.

## How it works / Step by step

Choosing among these techniques:

1. Can you sort the input so that a local choice is always safe? Try greedy, then test with a small counterexample.
2. Does the problem involve pairs cancelling, membership of a small set, or flags? Try bit manipulation.
3. Do you need fast lookup, counting, or grouping? Use a `HashMap` or `HashSet`.
4. Need to find duplicates or track seen values in one pass? A `HashSet` gives O(n) time.

## Common pitfalls

- Applying greedy without checking the greedy choice property.
- Forgetting that `>>` keeps the sign bit; use `>>>` for unsigned shifts.
- Integer overflow when shifting or multiplying. Use `long` for wide values.
- Overriding `equals` without `hashCode` (or the reverse).
- Using a `HashMap` key whose fields change after insertion.
- Assuming a hash match is a string match; always verify.

!!! tip "Interview tip"
    **Q: Why does the XOR trick find the single number in O(1) space?**
    XOR is commutative, associative, and `x ^ x = 0`. Every value that appears twice cancels, leaving the unique value. The answer does not depend on order, so no sorting or extra array is needed.

## Quick recap

- Greedy works only when a local best choice is provably part of a global optimum; check with a counterexample.
- `x & (x - 1)` clears the lowest set bit; XOR cancels equal pairs.
- Use `>>>` for unsigned shifts and `1L <<` for shifts beyond 31.
- Override `equals` and `hashCode` together; records do this for you.
- Hash collisions are handled by chaining (Java `HashMap`) or open addressing.

**See also:** [Graphs](graphs.md), [Dynamic Programming](dynamic-programming.md), [Backtracking and Recursion](backtracking-recursion.md)
