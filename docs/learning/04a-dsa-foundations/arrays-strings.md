# Arrays & Strings

Arrays and strings are the first data structures most interview problems use. Almost every question here comes down to choosing the right pattern: two pointers, a sliding window, binary search, prefix sums, or a string-matching algorithm. An interviewer asks about them to see whether you can cut a nested loop down to a single pass or a logarithmic search.

## Core concepts

### Array operations and their costs
An array is a fixed-size block of contiguous memory. Index access is O(1). Searching an unsorted array is O(n). Inserting or deleting in the middle shifts elements, so it is O(n). Sorting costs O(n log n) in general.

| Operation | Unsorted array | Sorted array |
|---|---|---|
| Access by index | O(1) | O(1) |
| Search by value | O(n) | O(log n) with binary search |
| Insert or delete at the middle | O(n) | O(n) |
| Append at the end (`ArrayList`, amortised) | O(1) | O(1) |

In Java, `Arrays.sort` uses a dual-pivot quicksort for primitive arrays and a stable TimSort for object arrays. Use `Arrays.sort` for primitives and `Collections.sort` or `List.sort` for objects that need stability.

### Two pointers
Use two indices that move toward each other or in the same direction. On a sorted array, a pair with a target sum can be found in one pass.

```java
static int[] twoSumSorted(int[] a, int target) {
    int lo = 0;
    int hi = a.length - 1;
    while (lo < hi) {
        int sum = a[lo] + a[hi];
        if (sum == target) {
            return new int[] {lo, hi};
        }
        if (sum < target) {
            lo++;
        } else {
            hi--;
        }
    }
    return new int[0]; // no pair found
}
```

This runs in O(n) time and O(1) extra space. The same idea solves palindrome checks, reversing in place, and removing duplicates from a sorted array.

### Sliding window
A window is a contiguous range `[left, right]`. Grow it on the right, and shrink it on the left when a condition breaks. For a window of fixed size k, slide it by one element at a time. For a variable size, shrink until the condition holds again.

```java
// Longest subarray whose sum is at most k. Requires non-negative values.
static int longestAtMost(int[] a, int k) {
    int best = 0;
    int sum = 0;
    int left = 0;
    for (int right = 0; right < a.length; right++) {
        sum += a[right];
        while (sum > k) {
            sum -= a[left];
            left++;
        }
        best = Math.max(best, right - left + 1);
    }
    return best;
}
```

Each index enters and leaves the window at most once, so the time is O(n).

### Binary search and its variants
Binary search halves the search range on each step, so it takes O(log n) time and O(1) space. The usual bug is the midpoint overflow. Write `lo + (hi - lo) / 2`, not `(lo + hi) / 2`.

The most useful variant is the **lower bound**: the first index whose value is greater than or equal to the target.

```java
static int lowerBound(int[] a, int target) {
    int lo = 0;
    int hi = a.length;           // half-open range [lo, hi)
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;                   // a.length if every value is smaller
}
```

For the first or last occurrence of a value, use the lower bound, or the upper bound minus one. The same loop also finds the minimum in a rotated sorted array. Compare `a[mid]` with `a[hi]`: if `a[mid] > a[hi]`, the minimum is to the right of `mid`, otherwise it is at `mid` or to the left.

`Arrays.binarySearch` returns `-(insertion point) - 1` when the value is missing and does not promise which duplicate it returns. Write your own loop when duplicates matter.

### Prefix sums
Store running totals once, then answer any range sum in O(1).

```java
int[] a = {2, 4, 6, 8};
int l = 1;
int r = 2;
int[] prefix = new int[a.length + 1];
for (int i = 0; i < a.length; i++) {
    prefix[i + 1] = prefix[i] + a[i];
}
// Sum of a[l..r] inclusive:
int rangeSum = prefix[r + 1] - prefix[l];
```

Building the table costs O(n) time and O(n) space. Queries are O(1). The same idea with a hash map of prefix sums counts subarrays that sum to a target in O(n).

### Strings in Java
A `String` is immutable. Each concatenation in a loop creates a new object, so build text with `StringBuilder`. Compare text with `equals`, never `==`. Use `charAt` for indexed access and `toCharArray` when you need to sort or modify characters.

Common checks:

```java
// Anagram check for lowercase letters: count each letter.
static boolean isAnagram(String s, String t) {
    if (s.length() != t.length()) {
        return false;
    }
    int[] counts = new int[26];
    for (int i = 0; i < s.length(); i++) {
        counts[s.charAt(i) - 'a']++;
        counts[t.charAt(i) - 'a']--;
    }
    for (int c : counts) {
        if (c != 0) {
            return false;
        }
    }
    return true;
}
```

Run time is O(n) and space is O(1) for a fixed alphabet.

### Palindrome checks

A palindrome reads the same forwards and backwards. Compare characters from both ends and move inward. If the question ignores spaces and letter case, normalise the text first. Both versions below run in O(n) time. The recursive one also uses O(n) call-stack space, so it is unsafe for very long input.

```java
import java.util.stream.IntStream;

public class Palindrome {
    // Loop-free check: compare each pair from the outside in
    static boolean isPalindrome(String text) {
        String clean = text.replaceAll("\\s+", "").toLowerCase();
        return IntStream.range(0, clean.length() / 2)
                .allMatch(i -> clean.charAt(i) == clean.charAt(clean.length() - 1 - i));
    }

    // Recursive check: compare the outer pair, then recurse on the inside
    static boolean isPalindromeRecursive(String clean, int lo, int hi) {
        if (lo >= hi) {
            return true;
        }
        return clean.charAt(lo) == clean.charAt(hi)
                && isPalindromeRecursive(clean, lo + 1, hi - 1);
    }

    public static void main(String[] args) {
        System.out.println(isPalindrome("A man a plan a canal Panama"));           // true
        System.out.println(isPalindromeRecursive("racecar", 0, "racecar".length() - 1)); // true
    }
}
```

### String matching: KMP
Finding a pattern of length m in text of length n by trying every start position costs O(n·m). KMP avoids re-checking characters by using a prefix table. The table stores, for each position in the pattern, the length of the longest proper prefix that is also a suffix. Matching then costs O(n + m).

```java
// prefix[i] = length of longest proper prefix of pat[0..i] that is also a suffix.
static int[] prefixFunction(String pat) {
    int[] pi = new int[pat.length()];
    int k = 0;
    for (int i = 1; i < pat.length(); i++) {
        while (k > 0 && pat.charAt(i) != pat.charAt(k)) {
            k = pi[k - 1];
        }
        if (pat.charAt(i) == pat.charAt(k)) {
            k++;
        }
        pi[i] = k;
    }
    return pi;
}

// Returns the first index of pat in text, or -1. Assumes pat is non-empty.
static int kmpSearch(String text, String pat) {
    int[] pi = prefixFunction(pat);
    int k = 0;
    for (int i = 0; i < text.length(); i++) {
        while (k > 0 && text.charAt(i) != pat.charAt(k)) {
            k = pi[k - 1];
        }
        if (text.charAt(i) == pat.charAt(k)) {
            k++;
        }
        if (k == pat.length()) {
            return i - pat.length() + 1;
        }
    }
    return -1;
}
```

**Rabin-Karp** computes a rolling hash of each window of the text and compares hashes with the pattern's hash. It runs in O(n + m) on average and O(n·m) in the worst case, when many hashes collide. Every hash match must be confirmed character by character.

**The Z-algorithm** builds a Z-array, where `z[i]` is the length of the longest substring starting at `i` that matches a prefix of the string. Concatenating the pattern, a separator, and the text gives an O(n + m) search, the same as KMP. Learn KMP first; it is the more common interview answer.

## How it works / Step by step

1. Read the constraints. Sorted input suggests binary search or two pointers. Non-negative values suggest a sliding window.
2. Name the pattern you think fits, then check it against a small example by hand.
3. Write the loop with explicit bounds. Decide whether each range is inclusive or half-open and keep it consistent.
4. Test the edge cases: an empty array, one element, all equal values, and a target that is not present.
5. State the time and space cost before you finish.

| Clue in the problem | Pattern to try |
|---|---|
| Sorted array, find a pair or a triple | Two pointers |
| Longest or shortest contiguous range with a condition | Sliding window |
| Sorted or monotonic search space | Binary search |
| Many range-sum queries | Prefix sums |
| Find a substring in a large text | KMP |
| Count anagrams or character frequencies | Count array of size 26 |

## Common pitfalls

- Using `(lo + hi) / 2` in binary search, which can overflow for large indices.
- Mixing inclusive and exclusive bounds, which causes off-by-one errors.
- Using `==` to compare strings. It compares object references.
- Concatenating strings in a loop with `+`, which is O(n²) over the whole loop.
- Forgetting that the sliding window shrink loop must run before you read the window size.
- Using `Arrays.binarySearch` on duplicates and assuming you get the first match.
- Calling `charAt` past the end of a string. Check `i < s.length()` first.

!!! tip "Interview tip"
    **Q: Why does a sliding window run in O(n) when it has a nested `while` loop?**
    A: Each index is added to the window once on the right and removed at most once on the left. The total number of moves is bounded by 2n, so the work is linear.

## Quick recap

- Index access is O(1). Search is O(n) unsorted and O(log n) sorted.
- Two pointers and sliding windows reduce nested loops to a single pass.
- Binary search needs a monotonic condition. Use `lo + (hi - lo) / 2` and a clear bound convention.
- Prefix sums turn repeated range sums into O(1) queries.
- KMP matches a pattern in O(n + m) using a prefix table.
- Palindrome checks compare pairs from both ends; normalise case and spaces first.

**See also:** [Linked Lists](linked-lists.md), [Stacks & Queues](stacks-queues.md), [Trees](trees.md), [DSA Foundations](index.md)
