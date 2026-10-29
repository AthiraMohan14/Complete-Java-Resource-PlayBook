# Stream API Problems (Part 1 of 2)

Exercises on the Java Stream API, with solutions. Each question gives a stream solution and, where it helps, a plain loop for comparison. Streams are lazy: nothing runs until a terminal operation such as `collect`, `toList`, `sum`, or `forEach`. Java 16 and later provide `Stream.toList()`.

---


This page is split into 2 parts. Continue to [Part 2](stream-api-problems-part-2.md).

## 1. Filter, map, and sort: names of employees older than 30

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Filter the stream by age, map each employee to a name, sort the names, and collect them with `toList()`. The stream and loop versions both run in O(n log n) time because of the sort, and O(n) space for the result.

### Explanation
**Approach 1: stream pipeline.**

```java
import java.util.*;

class AdultNames {
    record Employee(String name, String dept, int age, double salary) {}

    static List<String> olderThan30(List<Employee> employees) {
        return employees.stream()
                .filter(e -> e.age() > 30)
                .map(Employee::name)
                .sorted()
                .toList();                 // unmodifiable list (Java 16+)
    }
}
```

**Approach 2: loop.**

```java
import java.util.*;

class AdultNamesLoop {
    record Employee(String name, String dept, int age, double salary) {}

    static List<String> olderThan30(List<Employee> employees) {
        List<String> names = new ArrayList<>();
        for (Employee e : employees) {
            if (e.age() > 30) {
                names.add(e.name());
            }
        }
        Collections.sort(names);
        return names;
    }
}
```

### When to use / pitfalls
- `toList()` returns an unmodifiable list; `Collectors.toList()` returns a mutable `ArrayList` in practice, but the specification does not promise it.
- Streams are lazy: a `peek` or `map` with side effects may not run if no terminal operation consumes the stream.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 2. Count employees in each department

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Group the employees by department and count each group with `Collectors.counting()`. The result is a `Map<String, Long>`. This is O(n) time on average, with a hash map for the groups.

### Explanation
**Approach 1: `groupingBy` with `counting`.**

```java
import java.util.*;
import java.util.stream.Collectors;

class CountByDept {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<String, Long> countByDept(List<Employee> employees) {
        return employees.stream()
                .collect(Collectors.groupingBy(Employee::dept, Collectors.counting()));
    }
}
```

**Approach 2: loop with `merge`.**

```java
import java.util.*;

class CountByDeptLoop {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<String, Long> countByDept(List<Employee> employees) {
        Map<String, Long> counts = new HashMap<>();
        for (Employee e : employees) {
            counts.merge(e.dept(), 1L, Long::sum);
        }
        return counts;
    }
}
```

### When to use / pitfalls
- `counting()` returns `Long`, not `int`. Comparisons with `int` literals need `1L` or `.intValue()`.
- Use `TreeMap::new` as the map factory if the output must be sorted by department.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 3. Highest-paid employee in each department

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Group by department and take the maximum salary with `Collectors.maxBy`, which produces an `Optional` per group. Alternatively, merge into a map with `toMap` and `BinaryOperator.maxBy`, which avoids `Optional` values. Both are O(n) time.

### Explanation
**Approach 1: `groupingBy` with `maxBy`.**

```java
import java.util.*;
import java.util.stream.Collectors;

class TopPaidStream {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<String, Optional<Employee>> topPaid(List<Employee> employees) {
        return employees.stream()
                .collect(Collectors.groupingBy(Employee::dept,
                        Collectors.maxBy(Comparator.comparingDouble(Employee::salary))));
    }
}
```

**Approach 2: `toMap` with a merge function.** Each value is an `Employee`, not an `Optional`.

```java
import java.util.*;
import java.util.function.BinaryOperator;
import java.util.function.Function;
import java.util.stream.Collectors;

class TopPaidMerge {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<String, Employee> topPaid(List<Employee> employees) {
        return employees.stream()
                .collect(Collectors.toMap(
                        Employee::dept,
                        Function.identity(),
                        BinaryOperator.maxBy(Comparator.comparingDouble(Employee::salary))));
    }
}
```

### When to use / pitfalls
- `toMap` with no merge function throws `IllegalStateException` on duplicate keys. Always supply a merge function when keys can repeat.
- An empty group never appears in `groupingBy` output, so you will not get an `Optional.empty()` for it.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 4. Flatten lists of lists and sum the values

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `flatMap` to turn each inner list into a stream and join them into one stream, then convert to `int` with `mapToInt` and call `sum`. This is O(total elements) time.

### Explanation
**Approach 1: `flatMap` with `mapToInt`.**

```java
import java.util.List;

class FlattenSum {
    static int total(List<List<Integer>> orders) {
        return orders.stream()
                .flatMap(List::stream)        // Stream<List<Integer>> -> Stream<Integer>
                .mapToInt(Integer::intValue)  // avoids boxing in sum()
                .sum();
    }
}
```

**Approach 2: nested loops.**

```java
import java.util.List;

class FlattenSumLoop {
    static int total(List<List<Integer>> orders) {
        int sum = 0;
        for (List<Integer> inner : orders) {
            for (int value : inner) {
                sum += value;
            }
        }
        return sum;
    }
}
```

### When to use / pitfalls
- `map` gives a `Stream<List<Integer>>`, which is the wrong shape. `flatMap` is the operation that flattens.
- A sum of `int` values can overflow. Use `mapToLong` if the total might be large.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 5. Top three most frequent words in a text

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Split the text into lower-case words, count them with `groupingBy` and `counting`, sort the entries by count descending and then by word, and keep three. Sorting the whole map is O(k log k) for k distinct words, and counting is O(n).

### Explanation
**Approach 1: stream pipeline.**

```java
import java.util.*;
import java.util.stream.Collectors;

class TopWords {
    static List<Map.Entry<String, Long>> top3(String text) {
        return Arrays.stream(text.toLowerCase().split("\\W+"))
                .filter(w -> !w.isBlank())
                .collect(Collectors.groupingBy(w -> w, Collectors.counting()))
                .entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed()
                        .thenComparing(Map.Entry.<String, Long>comparingByKey()))
                .limit(3)
                .toList();
    }
}
```

**Approach 2: count with a map, then use a priority queue of size 3.** O(n + k log 3) time. Useful when k is very large, because you never sort all the entries.

```java
import java.util.*;

class TopWordsHeap {
    static List<String> top3(String text) {
        Map<String, Integer> counts = new HashMap<>();
        for (String w : text.toLowerCase().split("\\W+")) {
            if (!w.isBlank()) {
                counts.merge(w, 1, Integer::sum);
            }
        }
        PriorityQueue<Map.Entry<String, Integer>> heap = new PriorityQueue<>(
                Map.Entry.<String, Integer>comparingByValue()); // smallest on top
        for (Map.Entry<String, Integer> entry : counts.entrySet()) {
            heap.add(entry);
            if (heap.size() > 3) {
                heap.poll();
            }
        }
        List<String> result = new ArrayList<>();
        while (!heap.isEmpty()) {
            result.add(0, heap.poll().getKey());
        }
        return result;
    }
}
```

### When to use / pitfalls
- Break ties deterministically, for example by word, or the output order changes between runs.
- The regex `\\W+` splits on non-word characters; apostrophes and accented letters behave differently. Say what you assume.

**See also:** [Stream API problems](stream-api-problems-part-1.md), [Java coding problems](java-coding-problems-part-1.md)

</details>

---

## 6. Split employees into two groups with a predicate

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `Collectors.partitioningBy`, which returns a `Map<Boolean, List<T>>` with both keys always present, even when one group is empty. It runs in O(n) time.

### Explanation
**Approach 1: `partitioningBy`.**

```java
import java.util.*;
import java.util.stream.Collectors;

class SplitBySalary {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<Boolean, List<Employee>> split(List<Employee> employees) {
        return employees.stream()
                .collect(Collectors.partitioningBy(e -> e.salary() >= 50_000));
    }
}
```

**Approach 2: two filters.** Two passes over the list, O(2n) time.

```java
import java.util.*;

class SplitByFilter {
    record Employee(String name, String dept, int age, double salary) {}

    static Map<Boolean, List<Employee>> split(List<Employee> employees) {
        Map<Boolean, List<Employee>> result = new HashMap<>();
        result.put(true, employees.stream().filter(e -> e.salary() >= 50_000).toList());
        result.put(false, employees.stream().filter(e -> e.salary() < 50_000).toList());
        return result;
    }
}
```

### When to use / pitfalls
- `partitioningBy` gives both keys even when a group is empty. A `groupingBy` result would not contain the missing key.
- Do not repeat the predicate in two places (as in the second approach). A named variable or method keeps them in sync.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 7. Sum of squares of the even numbers from 1 to 10

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `IntStream.rangeClosed`, filter the evens, square each one, and sum. The result is 4 + 16 + 36 + 64 + 100 = 220. The stream is O(n) time.

### Explanation
**Approach 1: `IntStream`.**

```java
import java.util.stream.IntStream;

class SumEvenSquares {
    static int solve() {
        return IntStream.rangeClosed(1, 10)
                .filter(i -> i % 2 == 0)
                .map(i -> i * i)
                .sum();                 // 220
    }
}
```

**Approach 2: loop.**

```java
class SumEvenSquaresLoop {
    static int solve() {
        int sum = 0;
        for (int i = 1; i <= 10; i++) {
            if (i % 2 == 0) {
                sum += i * i;
            }
        }
        return sum;                     // 220
    }
}
```

### When to use / pitfalls
- `IntStream.range(1, 10)` excludes 10; `rangeClosed(1, 10)` includes it. This is the most common off-by-one in stream exercises.
- Primitive streams (`IntStream`, `LongStream`, `DoubleStream`) avoid boxing; use them for numeric work.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---

## 8. Average age, handling the empty case

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`average()` on an `IntStream` returns an `OptionalDouble`, because an empty stream has no average. Use `orElse` to supply a default, or `orElseThrow` if an empty list is an error. This is O(n) time.

### Explanation
**Approach 1: `mapToInt` and `average`.**

```java
import java.util.List;

class AverageAge {
    record Employee(String name, String dept, int age, double salary) {}

    static double averageAge(List<Employee> employees) {
        return employees.stream()
                .mapToInt(Employee::age)
                .average()
                .orElse(0.0);           // choose the empty-list behaviour explicitly
    }
}
```

**Approach 2: `summaryStatistics`.** Computes count, sum, min, max, and average in one pass.

```java
import java.util.List;
import java.util.IntSummaryStatistics;

class AverageAgeStats {
    record Employee(String name, String dept, int age, double salary) {}

    static double averageAge(List<Employee> employees) {
        IntSummaryStatistics stats = employees.stream()
                .mapToInt(Employee::age)
                .summaryStatistics();
        return stats.getCount() == 0 ? 0.0 : stats.getAverage();
    }
}
```

### When to use / pitfalls
- `getAverage()` on empty statistics returns 0.0, which can hide an empty input. Check `getCount()` if that matters.
- Do not divide the sum by the size yourself with `int` arithmetic; you lose the fraction.

**See also:** [Stream API problems](stream-api-problems-part-1.md)

</details>

---


**Next:** [Part 2](stream-api-problems-part-2.md)
