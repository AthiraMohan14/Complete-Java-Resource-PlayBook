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

## Quick recap

- Use `filter`, `map`, `flatMap`, `sorted`, and `toList()` for most pipelines.
- `groupingBy` and `partitioningBy` cover most grouping questions; know the map each one returns.
- `toMap` needs a merge function for duplicate keys.
- Primitive streams avoid boxing; `average()` and `reduce` return `Optional` for empty input.
- Streams are lazy; always bound infinite streams.
- Never mutate shared state from a parallel stream.

**See also:** [Java coding problems](java-coding-problems-part-1.md), [Arrays and strings](arrays-strings-part-1.md), [Linked lists and trees](linked-lists-trees-part-1.md)
