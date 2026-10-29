# Stream API Problems (Part 2 of 2)

Continued from [Part 1](stream-api-problems-part-1.md).

---

## 9. Sort by department, then by salary from highest to lowest

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Build a comparator with `Comparator.comparing` for the first key and `thenComparing` for the second. Reverse the salary key with `Comparator.comparingDouble(...).reversed()`. The sort is O(n log n) time.

### Explanation
**Approach 1: chained comparators.**

```java
import java.util.*;

class SortEmployees {
    record Employee(String name, String dept, int age, double salary) {}

    static List<Employee> sort(List<Employee> employees) {
        return employees.stream()
                .sorted(Comparator.comparing(Employee::dept)
                        .thenComparing(Comparator.comparingDouble(Employee::salary).reversed()))
                .toList();
    }
}
```

**Approach 2: explicit lambda.** Same result, easier to read when the rules are unusual.

```java
import java.util.*;

class SortEmployeesLambda {
    record Employee(String name, String dept, int age, double salary) {}

    static List<Employee> sort(List<Employee> employees) {
        return employees.stream()
                .sorted((a, b) -> {
                    int byDept = a.dept().compareTo(b.dept());
                    return byDept != 0 ? byDept : Double.compare(b.salary(), a.salary());
                })
                .toList();
    }
}
```

### When to use / pitfalls
- `Double.compare` handles `NaN` and `-0.0` consistently; subtracting doubles does not.
- Subtracting ints to compare them can overflow for large values. Use `Integer.compare`.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 10. First ten Fibonacci numbers with `Stream.iterate`

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`Stream.iterate` produces an infinite stream from a seed and a function; `limit` cuts it short. The seed must hold two values, so use a pair, such as a two-element array. The output is 0, 1, 1, 2, 3, 5, 8, 13, 21, 34.

### Explanation
**Approach 1: iterate over pairs.**

```java
import java.util.List;
import java.util.stream.Stream;

class FibonacciStream {
    static List<Long> firstTen() {
        return Stream.iterate(new long[]{0, 1}, f -> new long[]{f[1], f[0] + f[1]})
                .limit(10)
                .map(f -> f[0])
                .toList();
    }
}
```

**Approach 2: loop.**

```java
import java.util.ArrayList;
import java.util.List;

class FibonacciLoop {
    static List<Long> firstTen() {
        List<Long> out = new ArrayList<>();
        long a = 0;
        long b = 1;
        for (int i = 0; i < 10; i++) {
            out.add(a);
            long next = a + b;
            a = b;
            b = next;
        }
        return out;
    }
}
```

### When to use / pitfalls
- Without `limit`, an infinite stream never ends. Always bound it.
- `long` overflows after about 90 terms. Say so if the interviewer asks for more.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 11. Build a map from a list, handling duplicate keys

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`toMap` with two arguments throws `IllegalStateException` when a key appears twice. Add a merge function to choose a value for duplicates, and a map supplier such as `LinkedHashMap::new` to keep insertion order. This is O(n) time.

### Explanation
**Approach 1: `toMap` with merge and supplier.**

```java
import java.util.*;
import java.util.stream.Collectors;

class SalaryByDept {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<String, Double> totalByDept(List<Employee> employees) {
        return employees.stream()
                .collect(Collectors.toMap(
                        Employee::dept,
                        Employee::salary,
                        Double::sum,            // combine duplicates
                        LinkedHashMap::new));   // keep first-seen order
    }
}
```

**Approach 2: `groupingBy` with `summingDouble`.** Same totals, and no duplicate-key problem.

```java
import java.util.*;
import java.util.stream.Collectors;

class SalaryByDeptGroup {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<String, Double> totalByDept(List<Employee> employees) {
        return employees.stream()
                .collect(Collectors.groupingBy(Employee::dept,
                        LinkedHashMap::new,
                        Collectors.summingDouble(Employee::salary)));
    }
}
```

### When to use / pitfalls
- A two-argument `toMap` on duplicate keys is a common runtime failure. Use the four-argument form.
- `Collectors.toMap` returns a `HashMap` in practice, so pass a supplier if order matters.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 12. Reduce a stream to one value, and handle the empty case

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`reduce(identity, accumulator)` combines all elements into one value and returns that value directly, because the identity is the result for an empty stream. `reduce(accumulator)` with no identity returns an `Optional`, because an empty stream has no result. Both are O(n) time.

### Explanation
**Approach 1: `reduce` with an identity.**

```java
import java.util.List;

class ProductOf {
    static int product(List<Integer> values) {
        return values.stream().reduce(1, (a, b) -> a * b);   // empty list gives 1
    }
}
```

**Approach 2: `reduce` without identity, returning `Optional`.**

```java
import java.util.List;
import java.util.Optional;

class LargestOf {
    static Optional<Integer> largest(List<Integer> values) {
        return values.stream().reduce(Integer::max);         // empty list gives Optional.empty()
    }
}
```

### When to use / pitfalls
- The accumulator must be associative, and the identity must be a true identity for it, or parallel streams give wrong answers.
- Use `max`, `min`, or `sum` directly when they fit; they read more clearly than `reduce`.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 13. Parallel streams and shared mutable state

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A parallel stream runs the pipeline on several threads. Writing into a shared, non-thread-safe list from `forEach` is a data race, and the result is lost or corrupted elements. Use a `collect` or `toList` that merges per-thread results, or a thread-safe collector. Parallel streams help only for large, CPU-heavy pipelines with cheap merging.

### Explanation
**Approach 1: broken (shown to explain the problem).**

```java
import java.util.ArrayList;
import java.util.List;
import java.util.stream.IntStream;

class ParallelRace {
    static List<Integer> unsafe() {
        List<Integer> bad = new ArrayList<>();
        IntStream.range(0, 1_000).parallel().boxed().forEach(bad::add);   // data race
        return bad;                                                        // size may be less than 1000
    }
}
```

**Approach 2: collect the results.** The framework builds per-thread containers and merges them.

```java
import java.util.List;
import java.util.stream.IntStream;

class ParallelSafe {
    static List<Integer> safe() {
        return IntStream.range(0, 1_000).parallel().boxed().toList();   // always 1000 elements
    }
}
```

### When to use / pitfalls
- Parallel streams use the common `ForkJoinPool` by default. Blocking I/O inside the pipeline can starve other work in the JVM.
- For small inputs or cheap operations, the parallel version is slower than the sequential one.
- Measure with a benchmark (JMH) before you choose parallel streams for performance.

**See also:** [Advanced Java and concurrency](../technical/advanced-java-concurrency-part-1.md), [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 14. Upper-case a list of words and sort the result

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Map each word to upper case, then sort. Natural `String` order compares the characters as stored, so sort after the case change, or sort with `String.CASE_INSENSITIVE_ORDER` on the original words. Both give the same order. The sort is O(n log n) time and the result is O(n) space.

### Explanation
**Approach 1: map, then sort.**

```java
import java.util.List;

class UpperSortedWords {
    static List<String> upperSorted(List<String> words) {
        return words.stream()
                .map(String::toUpperCase)
                .sorted()
                .toList();
    }
}
```

**Approach 2: sort the original words case-insensitively, then upper-case them.** The order is the same as approach 1, because the comparator ignores case.

```java
import java.util.List;

class SortThenUpper {
    static List<String> sortThenUpper(List<String> words) {
        return words.stream()
                .sorted(String.CASE_INSENSITIVE_ORDER)
                .map(String::toUpperCase)
                .toList();
    }
}
```

With the input `["banana", "apple", "Cherry", "date"]`, all three methods return `[APPLE, BANANA, CHERRY, DATE]`.

### When to use / pitfalls
- Sorting the raw mixed-case words with plain `sorted()` puts `"Cherry"` before `"apple"`, because upper-case letters have lower code points. That is why the case change or the comparator matters.
- `toList()` returns an unmodifiable list. Use `Collectors.toCollection(ArrayList::new)` if the caller will change it.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Collections framework](../../learning/02b-collections/collections-overview.md)

</details>

---

## 15. Pick the even numbers above 10 from a list of integers

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Filter with `n > 10` and `n % 2 == 0`, either as two filters or one combined predicate. Collecting into a `Set` drops duplicates, and sorting descending with `limit(2)` gives the top two matches. Filtering is O(n) time, and the top-k version adds an O(m log m) sort over the m matches.

### Explanation
**Approach 1: two filters.** Easiest to read.

```java
import java.util.List;

class EvenOver10 {
    static List<Integer> evensOver10(List<Integer> numbers) {
        return numbers.stream()
                .filter(n -> n > 10)
                .filter(n -> n % 2 == 0)
                .toList();
    }
}
```

**Approach 2: one combined predicate.** Write `n > 10 && n % 2 == 0` in a single `filter` call. It is the same result in one stage.

**Approach 3: collect to a set, and keep the top two.**

```java
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

class EvenOver10Sets {
    static Set<Integer> distinctEvens(List<Integer> numbers) {
        return numbers.stream()
                .filter(n -> n > 10 && n % 2 == 0)
                .collect(Collectors.toSet());
    }

    static List<Integer> topTwo(List<Integer> numbers) {
        return numbers.stream()
                .filter(n -> n > 10 && n % 2 == 0)
                .sorted(Comparator.reverseOrder())
                .limit(2)
                .toList();
    }
}
```

With the input `[5, 12, 8, 15, 20, 3, 18, 7, 25]`, the filtered list is `[12, 20, 18]` and the top two are `[20, 18]`.

### When to use / pitfalls
- `toSet()` loses order and duplicates. Use it only when uniqueness is the point.
- Put `limit` after `sorted`, not before. `limit` first would keep the first two matches in encounter order, not the largest two.
- For a very large stream with a small k, a bounded heap is cheaper than sorting everything. Mention it if the interviewer pushes on performance.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Java coding problems](java-coding-problems-part-1.md)

</details>

---

## 16. Count how often each word appears

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Group the words by their own value with `groupingBy` and `counting`. This gives a `Map<String, Long>` in O(n) time and O(k) space for k distinct words. Lower-case the words first if case should not matter, and sort the entries by count if the output must be ranked.

### Explanation
**Approach 1: `groupingBy` with `counting`.**

```java
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

class WordFrequency {
    static Map<String, Long> counts(List<String> words) {
        return words.stream()
                .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
    }
}
```

**Approach 2: normalise case, then count.** `"Apple"` and `"apple"` now share one key.

```java
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

class WordFrequencyIgnoreCase {
    static Map<String, Long> countsIgnoringCase(List<String> words) {
        return words.stream()
                .map(w -> w.toLowerCase(Locale.ROOT))
                .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
    }
}
```

**Approach 3: sort the entries by count, highest first.** Ties are broken by the word, so the output is stable.

```java
import java.util.List;
import java.util.Map;

class WordFrequencyRanked {
    static List<Map.Entry<String, Long>> byCountDescending(Map<String, Long> counts) {
        return counts.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed()
                        .thenComparing(Map.Entry.<String, Long>comparingByKey()))
                .toList();
    }
}
```

For `["apple", "banana", "apple", "cherry", "banana", "apple"]`, the counts are apple=3, banana=2, cherry=1. Ranked by count, that is the same order.

### When to use / pitfalls
- `counting()` returns `Long`. Do not compare it with an `int` literal without `L` or a conversion.
- `groupingBy` returns a `HashMap`, so its iteration order is not defined. Sort the entries or use a `TreeMap` factory if the order is part of the answer.
- Use `Locale.ROOT` for case changes. The default locale can change results, for example in Turkish.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Collections framework](../../learning/02b-collections/collections-overview.md)

</details>

---

## 17. Sum, multiply, and join values with `reduce`

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`reduce(identity, accumulator)` folds the stream into one value. The identity is the result for an empty stream, so `0` for a sum, `1` for a product, and `""` for a string. For strings, `Collectors.joining` is the better tool than `reduce`. Each reduction is O(n) time.

### Explanation
**Approach 1: sum and product with an identity.**

```java
import java.util.List;

class ReduceMath {
    static int sum(List<Integer> values) {
        return values.stream().reduce(0, Integer::sum);
    }

    static int product(List<Integer> values) {
        return values.stream().reduce(1, (a, b) -> a * b);
    }
}
```

**Approach 2: concatenation with `String::concat`.** The identity is `""`.

```java
import java.util.List;

class ReduceConcat {
    static String concatenate(List<String> parts) {
        return parts.stream().reduce("", String::concat);
    }
}
```

With the parts `"1"` to `"5"`, the result is `"12345"`.

**Approach 3: join with a separator.** Without an identity, the result is an `Optional`, so give the empty case a default.

```java
import java.util.List;

class ReduceJoin {
    static String dashJoined(List<String> parts) {
        return parts.stream()
                .reduce((a, b) -> a + "-" + b)
                .orElse("");
    }
}
```

With `["Hello", " ", "World"]`, the result is `"Hello- -World"`, because the middle part is a space.

**Approach 4: maximum with `Optional`.** `reduce(Integer::max)` returns `Optional.empty()` for an empty list.

### When to use / pitfalls
- `reduce("", (a, b) -> a + b)` creates a new string at every step, so it is quadratic in the total length. `Collectors.joining()` appends into one `StringBuilder` instead.
- The accumulator must be associative, and the identity must really be an identity. Otherwise a parallel stream gives wrong answers.
- Prefer `Integer::sum`, `max`, or `IntStream.sum()` when they fit. They say what they do.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Stream API problems part 1](stream-api-problems-part-1.md#8-average-age-handling-the-empty-case)

</details>

---

## 18. Names and splits for employees earning above 50,000

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Filter on the salary, then map to names and collect them into one comma-separated string. Sorting by salary, adding a name filter, and `partitioningBy` are all variations on the same pipeline. Each is O(n) time, and sorting adds O(m log m) for the m matches.

### Explanation
**Approach 1: filter, map, and join.**

```java
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

class HighEarners {
    record Employee(String name, double salary) {}

    static final double THRESHOLD = 50_000;

    static String namesCsv(List<Employee> staff) {
        return staff.stream()
                .filter(e -> e.salary() > THRESHOLD)
                .map(Employee::name)
                .collect(Collectors.joining(", "));
    }

    static List<String> namesBySalaryDesc(List<Employee> staff) {
        return staff.stream()
                .filter(e -> e.salary() > THRESHOLD)
                .sorted(Comparator.comparingDouble(Employee::salary).reversed())
                .map(Employee::name)
                .toList();
    }

    static List<String> namesLongerThan3(List<Employee> staff) {
        return staff.stream()
                .filter(e -> e.salary() > THRESHOLD)
                .filter(e -> e.name().length() > 3)
                .map(Employee::name)
                .toList();
    }

    static Map<Boolean, List<Employee>> split(List<Employee> staff) {
        return staff.stream()
                .collect(Collectors.partitioningBy(e -> e.salary() > THRESHOLD));
    }
}
```

With the staff Alice 75000, Bob 45000, Charlie 95000, Diana 55000, and Eve 40000, the joined names are `"Alice, Charlie, Diana"`. Sorted by salary, the order is Charlie, Alice, Diana. The partition has three `true` entries and two `false` entries.

### When to use / pitfalls
- `filter` and `map` are lazy and process one element at a time. `sorted` and `distinct` must buffer the stream before they emit, so put filters before them to shrink the buffer.
- `partitioningBy` always has both keys, even when one side is empty. `groupingBy` would leave the missing key out.
- Do not repeat the threshold in several places. A named constant, as above, keeps the rule in one place.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Java 8 lambdas and streams](../../learning/03a-modern-java/java8-lambdas-streams.md)

</details>

---

## Quick recap

- Use `filter`, `map`, `flatMap`, `sorted`, and `toList()` for most pipelines.
- `groupingBy` and `partitioningBy` cover most grouping questions; know the map each one returns.
- `toMap` needs a merge function for duplicate keys.
- Primitive streams avoid boxing; `average()` and `reduce` return `Optional` for empty input.
- Streams are lazy; always bound infinite streams.
- Never mutate shared state from a parallel stream.
- Use `Collectors.joining` to build strings; `reduce` with `+` is quadratic.

**See also:** [Java coding problems](java-coding-problems-part-1.md), [Arrays and strings](arrays-strings-part-1.md), [Linked lists and trees](linked-lists-trees-part-1.md)
