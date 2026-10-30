# Java-Specific Coding Problems (Part 2 of 4)

Continued from [Part 1](java-coding-problems-part-1.md).

---

## 5. Parse key=value configuration lines

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Skip blank lines and comments, split each remaining line at the first `=`, trim both sides, and store the pair in a map. Reject lines without a key. Both approaches are O(total characters) time. The regex version validates the format; the split version is simpler and easier to debug.

### Explanation
**Approach 1: `indexOf` and `substring`.**

```java
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

class ConfigParser {
    static Map<String, String> parse(List<String> lines) {
        Map<String, String> config = new LinkedHashMap<>();
        for (String raw : lines) {
            String line = raw.strip();
            if (line.isEmpty() || line.startsWith("#")) {
                continue;
            }
            int eq = line.indexOf('=');
            if (eq <= 0) {
                throw new IllegalArgumentException("bad line: " + raw);
            }
            config.put(line.substring(0, eq).strip(), line.substring(eq + 1).strip());
        }
        return config;
    }
}
```

**Approach 2: a compiled regular expression.** Validates the key format too.

```java
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

class ConfigParserRegex {
    private static final Pattern LINE =
            Pattern.compile("^\\s*([A-Za-z_][\\w.]*)\\s*=\\s*(.*?)\\s*$");

    static Map<String, String> parse(List<String> lines) {
        Map<String, String> config = new LinkedHashMap<>();
        for (String raw : lines) {
            if (raw.isBlank() || raw.strip().startsWith("#")) {
                continue;
            }
            Matcher m = LINE.matcher(raw);
            if (!m.matches()) {
                throw new IllegalArgumentException("bad line: " + raw);
            }
            config.put(m.group(1), m.group(2));
        }
        return config;
    }
}
```

### When to use / pitfalls
- Decide what a duplicate key means. The code above keeps the last value; a strict parser throws.
- Values can contain `=`, which is why the split happens at the first one only.
- Quoted values with `#` inside them need a real tokenizer, not a comment check at the start of the line.

**See also:** [Java coding problems](java-coding-problems-part-1.md)

</details>

---

## 6. Count word frequencies in a file

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Open the file with try-with-resources so it is always closed, read it line by line, split into words, and count them. Files are read lazily, so the memory use depends on the number of distinct words, not on the file size. Both approaches are O(n) time.

### Explanation
**Approach 1: `Files.lines` with streams.**

```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;
import java.util.stream.Stream;

class FileWordCount {
    static Map<String, Long> count(Path file) throws IOException {
        try (Stream<String> lines = Files.lines(file)) {
            return lines
                    .flatMap(line -> Arrays.stream(line.toLowerCase().split("\\W+")))
                    .filter(word -> !word.isBlank())
                    .collect(Collectors.groupingBy(word -> word, TreeMap::new, Collectors.counting()));
        }
    }
}
```

**Approach 2: `BufferedReader` loop.**

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.TreeMap;

class FileWordCountReader {
    static Map<String, Integer> count(Path file) throws IOException {
        Map<String, Integer> counts = new TreeMap<>();
        try (BufferedReader reader = Files.newBufferedReader(file)) {
            String line;
            while ((line = reader.readLine()) != null) {
                for (String word : line.toLowerCase().split("\\W+")) {
                    if (!word.isBlank()) {
                        counts.merge(word, 1, Integer::sum);
                    }
                }
            }
        }
        return counts;
    }
}
```

### When to use / pitfalls
- Never read a large file with `readAllLines` or `readString` if the file may be big; both load everything into memory.
- `Files.newBufferedReader` uses UTF-8 by default; pass a charset if the file uses another encoding.
- Close the stream from `Files.lines`. Forgetting this leaks a file handle.

**See also:** [Stream API problems](../coding/stream-api-problems-part-1.md), [Core Java](../technical/core-java-part-1.md)

</details>

---

## 7. Create an immutable class with a builder

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Make the class `final`, make every field `private final`, copy mutable inputs on the way in, and return unmodifiable views on the way out. A builder collects optional values and validates them in `build()`. A Java `record` with a compact constructor gives you most of this with less code.

### Explanation
**Approach 1: final class with a nested builder.**

```java
import java.util.ArrayList;
import java.util.List;

final class Order {
    private final String id;
    private final List<String> items;

    private Order(Builder builder) {
        this.id = builder.id;
        this.items = List.copyOf(builder.items);    // defensive, unmodifiable copy
    }

    String id() {
        return id;
    }

    List<String> items() {
        return items;
    }

    static Builder builder() {
        return new Builder();
    }

    static final class Builder {
        private String id;
        private final List<String> items = new ArrayList<>();

        Builder id(String id) {
            this.id = id;
            return this;
        }

        Builder addItem(String item) {
            items.add(item);
            return this;
        }

        Order build() {
            if (id == null) {
                throw new IllegalStateException("id is required");
            }
            return new Order(this);
        }
    }
}
```

**Approach 2: record with a compact constructor.**

```java
import java.util.List;
import java.util.Objects;

record OrderRecord(String id, List<String> items) {
    OrderRecord {
        Objects.requireNonNull(id, "id");
        items = List.copyOf(items);     // copy and make unmodifiable
    }
}
```

### When to use / pitfalls
- Returning the internal `List` directly lets callers change the object. Copy or wrap it.
- `List.copyOf` rejects `null` elements. Decide whether that is what you want.
- A record is shallowly immutable: an element that is itself mutable can still change.

**See also:** [Core Java](../technical/core-java-part-1.md)

</details>

---

## 8. Implement `equals` and `hashCode` correctly

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Equal objects must have equal hash codes, and `equals` must be reflexive, symmetric, transitive, and consistent. Compare every field that defines identity, use `Objects.hash` for the hash code, and do not use mutable fields that change after the object goes into a hash-based collection. A record generates both methods for you.

### Explanation
**Approach 1: manual implementation.**

```java
import java.util.Objects;

final class Money {
    private final long cents;
    private final String currency;

    Money(long cents, String currency) {
        this.cents = cents;
        this.currency = Objects.requireNonNull(currency);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof Money other)) {        // pattern matching (Java 16+)
            return false;
        }
        return cents == other.cents && currency.equals(other.currency);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cents, currency);
    }
}
```

**Approach 2: record.**

```java
record MoneyRecord(long cents, String currency) {
}
```

### When to use / pitfalls
- Overriding `equals` without `hashCode` breaks `HashSet` and `HashMap`.
- Using `getClass() != o.getClass()` instead of `instanceof` is a valid choice, but it means subclasses are never equal to the base class.
- If a key's hash code changes after insertion, lookups fail. Keep fields used in `hashCode` immutable.

**See also:** [Core Java](../technical/core-java-part-1.md)

</details>

---

## 9. Write a custom `Iterable` over a range of integers

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Implement `Iterable<Integer>` and return an `Iterator` whose `hasNext` and `next` track the current position. The class then works in an enhanced `for` loop. Throw `NoSuchElementException` from `next()` when there is nothing left. Iterating is O(1) per element.

### Explanation
**Approach 1: anonymous iterator.**

```java
import java.util.Iterator;
import java.util.NoSuchElementException;

final class IntRange implements Iterable<Integer> {
    private final int start;
    private final int endExclusive;

    IntRange(int start, int endExclusive) {
        this.start = start;
        this.endExclusive = endExclusive;
    }

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int next = start;

            @Override
            public boolean hasNext() {
                return next < endExclusive;
            }

            @Override
            public Integer next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                return next++;
            }
        };
    }
}
```

**Approach 2: `IntStream` as the source.** The stream's iterator is not exposed directly, so use this when you do not need a custom `Iterable` type.

```java
import java.util.stream.IntStream;

class RangeStream {
    static void printRange(int start, int endExclusive) {
        IntStream.range(start, endExclusive).forEach(System.out::println);
    }
}
```

### When to use / pitfalls
- Do not implement `remove()` unless you mean it. The default throws `UnsupportedOperationException`, which is the right behaviour for a read-only range.
- Creating a new iterator per call keeps the iterable reusable; sharing one iterator object does not.

**See also:** [Core Java](../technical/core-java-part-1.md), [Stream API problems](../coding/stream-api-problems-part-1.md)

</details>

---

## 10. Sum a large array in parallel

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Split the array in half recursively until each piece is small, sum the pieces in parallel with a `RecursiveTask`, and combine the results. This is O(n) total work divided across cores, so the speed-up depends on the core count. A parallel `LongStream` does the same thing with less code.

### Explanation
**Approach 1: fork/join with `RecursiveTask`.**

```java
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveTask;

class SumTask extends RecursiveTask<Long> {
    private static final int THRESHOLD = 10_000;
    private final long[] data;
    private final int from;
    private final int to;

    SumTask(long[] data, int from, int to) {
        this.data = data;
        this.from = from;
        this.to = to;
    }

    @Override
    protected Long compute() {
        if (to - from <= THRESHOLD) {
            long sum = 0;
            for (int i = from; i < to; i++) {
                sum += data[i];
            }
            return sum;
        }
        int mid = (from + to) >>> 1;
        SumTask left = new SumTask(data, from, mid);
        SumTask right = new SumTask(data, mid, to);
        left.fork();                              // run the left half asynchronously
        return right.compute() + left.join();     // compute the right half here
    }

    static long sum(long[] data) {
        return ForkJoinPool.commonPool().invoke(new SumTask(data, 0, data.length));
    }
}
```

**Approach 2: parallel stream.**

```java
import java.util.stream.LongStream;

class ParallelSumStream {
    static long sum(long[] data) {
        return LongStream.of(data).parallel().sum();
    }
}
```

### When to use / pitfalls
- A threshold that is too small creates more tasks than the work justifies. Measure with JMH.
- The common pool is shared by parallel streams and other code. Do not block inside these tasks.
- For small arrays, a plain loop is faster than either approach.

**See also:** [Advanced Java and concurrency](../technical/advanced-java-concurrency-part-1.md)

</details>

---


**Next:** [Part 3](java-coding-problems-part-3.md)
