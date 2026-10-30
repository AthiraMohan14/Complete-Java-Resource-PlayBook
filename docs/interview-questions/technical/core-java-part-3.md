# Core Java Questions (Part 3 of 3)

Continued from [Part 2](core-java-part-2.md). Questions 19 to 27 cover collections, numeric edge cases, ordering, streams, memory, and enums.

---

## 19. What is the difference between HashMap and ConcurrentHashMap?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`HashMap` is not thread-safe and is the right choice for single-threaded code or code where you control all access with your own locking. `ConcurrentHashMap` is designed for many threads reading and writing at once. It rejects `null` keys and values, and it iterates with weakly consistent iterators instead of failing fast.

### Explanation
```java
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

class MapDemo {
    public static void main(String[] args) {
        Map<String, Integer> plain = new HashMap<>();
        plain.put(null, 1);                    // one null key is allowed

        Map<String, Integer> shared = new ConcurrentHashMap<>();
        shared.put("a", 1);
        // shared.put(null, 1);                // NullPointerException
    }
}
```

- `ConcurrentHashMap` does not lock the whole map for each operation. It uses compare-and-swap for empty bins and locks only the bin it changes, so threads writing to different bins proceed in parallel.
- `Collections.synchronizedMap` wraps a map with one lock. Every thread queues on it, which scales poorly.
- `HashMap` iterators are fail-fast on a best-effort basis: a structural change during iteration throws `ConcurrentModificationException`. `ConcurrentHashMap` iterators never throw it, and they may or may not reflect updates made after they were created.

### When to use / pitfalls
- Use `HashMap` in single-threaded code. Use `ConcurrentHashMap` for shared state that many threads update.
- A compound action, such as "check then put", is not atomic even on `ConcurrentHashMap`. Use `computeIfAbsent` or `merge` for atomic updates.

**See also:** [Collections](../../learning/02b-collections/collections-overview.md)

</details>

---

## 20. What happens when an int overflows Integer.MAX_VALUE?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Integer arithmetic wraps silently. `Integer.MAX_VALUE + 1` becomes `Integer.MIN_VALUE`, and no exception is thrown. Java integers use two's-complement representation, so the value simply moves around the ring from the largest positive number to the most negative one.

### Explanation
```java
int max = Integer.MAX_VALUE;
System.out.println(max);            // 2147483647
System.out.println(max + 1);        // -2147483648
System.out.println(max + 2);        // -2147483647

long widened = (long) max + 1;      // widen before the arithmetic
System.out.println(widened);        // 2147483648

System.out.println(Math.addExact(max, 1));  // throws ArithmeticException: integer overflow
```

The same rule applies to `long`, which wraps at `Long.MAX_VALUE`. `double` does not wrap in this way. Overflow in a `double` gives `Infinity`, which you can see with `Double.MAX_VALUE * 2`. Adding 1 to `Double.MAX_VALUE` leaves it unchanged, because 1 is far below the precision of that value.

### When to use / pitfalls
- To detect overflow, use `Math.addExact`, `Math.multiplyExact`, or check the bounds before the operation.
- To store results that may exceed `int`, widen to `long`, or use `BigInteger` for arbitrary precision.

**See also:** [Wrappers, Strings and Arrays](../../learning/02a-core-language/wrappers-strings-arrays.md)

</details>

---

## 21. What is the value of `a++ + ++a` when `a` is 5?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The result is 12, and `a` ends as 7. Java evaluates operands from left to right, so `a++` yields 5 and leaves `a` at 6, and then `++a` raises `a` to 7 and yields 7. The sum is 12.

### Explanation
```java
int a = 5;
int result = a++ + ++a;             // 5 + 7
System.out.println(result + " " + a);   // 12 7
```

Evaluation order is defined by the language specification, so this is not undefined behaviour. The expression is still hard to read, so avoid it. Split it into steps when you need the same value:

```java
int a = 5;
int first = a++;     // first is 5, a is 6
int second = ++a;    // a is 7, second is 7
int result = first + second;   // 12
```

### When to use / pitfalls
- Do not mix increment operators with other uses of the same variable in one expression.
- Pre- and post-increment differ only in the value the expression yields. The variable changes in both cases.

**See also:** [Operators and Control Flow](../../learning/01-programming-basics/operators-control-flow.md)

</details>

---

## 22. What is the difference between `0.0 / 0.0` and `1 / 0` in Java?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Floating-point division by zero does not throw. `0.0 / 0.0` gives `NaN` (not a number), and `1.0 / 0.0` gives `Infinity`. Integer division by zero throws `ArithmeticException`, because integers have no infinity or NaN.

### Explanation
```java
System.out.println(1.0 / 0.0);              // Infinity
System.out.println(-1.0 / 0.0);             // -Infinity
System.out.println(0.0 / 0.0);              // NaN
// System.out.println(1 / 0);               // ArithmeticException: / by zero

double x = 0.0 / 0.0;
System.out.println(x == Double.NaN);        // false: NaN is never equal to anything
System.out.println(Double.isNaN(x));        // true: the correct check
```

Both `NaN` and `Infinity` follow the IEEE 754 rules for floating-point arithmetic. Compare against `NaN` only with `Double.isNaN`, and use `Double.isInfinite` for infinities.

### When to use / pitfalls
- A `NaN` in a calculation spreads to every result that depends on it. Check for it where data comes from outside.
- Dividing by a zero `int` in a loop fails at run time. Guard the divisor first.

**See also:** [Wrappers, Strings and Arrays](../../learning/02a-core-language/wrappers-strings-arrays.md)

</details>

---

## 23. What is the difference between Comparable and Comparator?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`Comparable` gives a class its single natural ordering. The class implements `compareTo(T other)` itself. `Comparator` is a separate object that defines an ordering from outside the class, through `compare(T a, T b)`. Use `Comparable` for the obvious order, such as ID or creation time, and `Comparator` when you need several orders or cannot change the class.

### Explanation
```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

class Student implements Comparable<Student> {
    final String name;
    final int age;

    Student(String name, int age) {
        this.name = name;
        this.age = age;
    }

    @Override
    public int compareTo(Student other) {
        return Integer.compare(age, other.age);   // natural order: age
    }

    @Override
    public String toString() {
        return name + "(" + age + ")";
    }
}

class SortDemo {
    public static void main(String[] args) {
        List<Student> students = new ArrayList<>(List.of(new Student("Ravi", 22), new Student("Ana", 20)));
        Collections.sort(students);                                  // natural order: by age
        students.sort(Comparator.comparing((Student s) -> s.name));  // external order: by name
        System.out.println(students);                                // [Ana(20), Ravi(22)]
    }
}
```

Use `Integer.compare` rather than subtraction. Subtracting two ints can overflow and give the wrong sign. Build multi-field orders with `thenComparing`, such as `Comparator.comparing(...).thenComparingInt(...)`.

### When to use / pitfalls
- `compareTo` should be consistent with `equals`. A `TreeSet` or `TreeMap` treats two elements as duplicates when `compareTo` returns zero, even if `equals` says they differ.
- A `TreeSet` does not accept `null` elements.

**See also:** [Collections](../../learning/02b-collections/collections-overview.md)

</details>

---

## 24. Which collection stores unique employee objects, and what must the class implement?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use a `HashSet` for fast uniqueness checks, or a `TreeSet` when you need elements in sorted order. Both rely on the class's `equals` and `hashCode`, or on `compareTo` for `TreeSet`. Equality should be based on a stable key, such as an employee ID, and the fields used must not change while the object is in the set.

### Explanation
```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

final class Employee {
    private final long id;
    private final String name;

    Employee(long id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Employee other)) return false;   // Java 16+ pattern matching
        return id == other.id;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);                             // same field as equals
    }
}

class EmployeeSetDemo {
    public static void main(String[] args) {
        Set<Employee> set = new HashSet<>();
        set.add(new Employee(1L, "John"));
        set.add(new Employee(1L, "Jane"));   // same id: treated as a duplicate
        System.out.println(set.size());      // 1
    }
}
```

The table below shows the main differences:

| Feature | `HashSet` | `TreeSet` |
|---|---|---|
| Order | Not guaranteed | Sorted by `compareTo` or a `Comparator` |
| Add, remove, lookup | Average constant time | Logarithmic time |
| Duplicate test | `equals` and `hashCode` | `compareTo` (or the comparator) |
| `null` elements | One allowed | Not allowed |

### When to use / pitfalls
- Override `equals` and `hashCode` together, and keep them based on the same fields.
- Do not base equality on a mutable field. If the field changes while the object is in a hash set, the set can no longer find it.

**See also:** [Collections](../../learning/02b-collections/collections-overview.md)

</details>

---

## 25. How do you filter, sort, and transform a collection with the Stream API?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Build a pipeline: a source, then intermediate operations such as `filter`, `sorted`, and `map`, then one terminal operation such as `toList` or `collect`. Streams are lazy, so nothing runs until the terminal operation starts, and each stream can be consumed only once.

### Explanation
```java
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

record Employee(long id, String name, double salary, String dept) { }

class StreamDemo {
    public static void main(String[] args) {
        List<Employee> staff = List.of(
            new Employee(1L, "John", 50_000, "IT"),
            new Employee(2L, "Jane", 60_000, "HR"),
            new Employee(3L, "Bob", 45_000, "IT"));

        List<Employee> topEarners = staff.stream()
            .filter(e -> e.salary() > 46_000)
            .sorted(Comparator.comparingDouble(Employee::salary).reversed())
            .limit(2)
            .toList();                                   // Java 16+

        List<String> names = staff.stream()
            .map(Employee::name)
            .collect(Collectors.toList());

        Map<String, List<Employee>> byDept = staff.stream()
            .collect(Collectors.groupingBy(Employee::dept));

        double total = staff.stream()
            .mapToDouble(Employee::salary)
            .sum();

        System.out.println(topEarners.size() + " " + names + " " + byDept.keySet() + " " + total);
    }
}
```

`sorted` plus `limit` is a common top-N query. `distinct` uses `equals` and `hashCode`, not a field name, so it works only when those methods are overridden as in the previous question.

### When to use / pitfalls
- For very large inputs, `parallelStream` can help, but it adds coordination cost. Measure before using it, and avoid it when the operations have side effects.
- A stream cannot be reused. Create a new stream from the source for each pipeline.
- Do not change the source collection while the stream is running.

**See also:** [Java 8: Lambdas and Streams](../../learning/03a-modern-java/java8-lambdas-streams.md)

</details>

---

## 26. What causes a memory leak in Java?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A Java memory leak happens when objects stay reachable after the program no longer needs them, so the garbage collector cannot free them. The usual causes are static collections or caches that only grow, listeners that are never removed, `ThreadLocal` values left in pooled threads, and objects kept alive by long-lived references. Garbage collection frees unreachable objects, not unused ones.

### Explanation
```java
import java.util.ArrayList;
import java.util.List;

class Registry {
    private static final List<byte[]> CACHE = new ArrayList<>();   // grows for the life of the JVM

    static void remember(byte[] payload) {
        CACHE.add(payload);                                         // leak: nothing ever removes entries
    }
}
```

Fixes depend on the cause. Bound the cache, evict entries by size or age, or use a `WeakHashMap` when the keys should disappear once nothing else references them. Remove listeners when their owner is done. Call `ThreadLocal.remove()` in pooled threads. Close resources with try-with-resources.

### When to use / pitfalls
- Take a heap dump, such as with `jmap` or the JVM's automatic dump option, and inspect what holds the objects.
- An `OutOfMemoryError` is not always a leak. A heap that is simply too small for the workload also produces it.

**See also:** [Java Overview and Platform](../../learning/01-programming-basics/java-overview-platform.md)

</details>

---

## 27. When should you use an enum?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use an `enum` for a fixed set of named constants that the compiler should know about, such as days of the week, order states, or currency codes. An enum is type-safe, works in `switch`, and can carry fields and methods. Each constant is a single object, so enums are also a safe way to write a singleton.

### Explanation
```java
enum OrderStatus {
    PENDING, SHIPPED, DELIVERED;

    boolean isFinal() {
        return this == DELIVERED;
    }
}

class EnumDemo {
    public static void main(String[] args) {
        OrderStatus status = OrderStatus.valueOf("SHIPPED");
        System.out.println(status.isFinal());   // false
        for (OrderStatus s : OrderStatus.values()) {
            System.out.println(s + " " + s.ordinal());
        }
    }
}
```

Store the enum's `name()` when you persist it. Its `ordinal()` depends on declaration order, so reordering constants or inserting one in the middle changes stored values.

### When to use / pitfalls
- Use an enum when the set of values is fixed at compile time. Use a class or a database table when the values are data that changes at run time.
- An enum can implement an interface, which lets each constant supply its own behaviour.

**See also:** [Enums, Inner Classes and Packages](../../learning/02a-core-language/enums-inner-classes-packages.md)

</details>

---

## 28. What is JavaFX, and where is it used?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
JavaFX is Java's toolkit for building desktop and rich-client user interfaces. It provides a scene graph, layout containers, CSS styling, FXML markup for layouts, and media and graphics support. It is used for desktop applications, internal tools, and interactive dashboards. Since Java 11 it is no longer part of the JDK. It is a separate set of modules, published by the OpenJFX project, and a build must add it as a dependency.

### Explanation
JavaFX and Swing both build desktop interfaces in Java, but they differ in design:

- **Swing** is an older toolkit that is still part of the JDK. It draws its own components on top of AWT and is widely found in existing applications.
- **JavaFX** is newer. It uses a scene graph, supports CSS and FXML, and renders through a hardware-accelerated pipeline. Its APIs are designed for richer visual effects, animation, and media.

Teams starting a new desktop application often choose JavaFX for its styling and layout model. Teams with a large Swing codebase usually keep Swing and migrate only parts of the interface when there is a clear benefit.

### When to use / pitfalls
- Do not assume JavaFX ships with `java`. A project on Java 11 or later must declare the JavaFX modules in its build file.
- JavaFX is a client-side toolkit. For web or server work, use a framework such as Spring Boot.
- Mention the version and build setup if you describe a JavaFX project, because the module setup differs from the older bundled JDK.

**See also:** [Java overview and platform](../../learning/01-programming-basics/java-overview-platform.md), [Core Java Part 2](core-java-part-2.md)

</details>

---

## 29. How do you balance performance improvements with code clarity?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Measure first with a profiler, or with a benchmark for a small piece of code. Keep the simplest correct version by default. Optimise only the hot paths that the measurements show matter. When a faster version is harder to read, document the trade-off next to the code and record the measured gain, so the next reader knows why it is there.

### Explanation
A typical sequence:

1. Write the clear version and make it correct with tests.
2. Measure the real workload, using a profiler such as the one in the IDE, or JMH for a microbenchmark. JMH handles JIT warm-up and dead-code elimination, which hand-written timing loops often get wrong.
3. Find the hot path. If it takes a small share of total time, leave the code alone.
4. If the hot path matters, make the smallest change that gives the gain, such as a better collection type, avoiding repeated allocation, or caching one expensive lookup.
5. Add a short comment that states the reason and the measured effect, and keep the test that protects the behaviour.

```java
// Hot path: called for every row in an import. Profiling showed that a linear scan
// dominated the run time, so a HashMap index replaces it. The linear version stays
// in the tests as a reference for correctness.
```

### When to use / pitfalls
- Premature optimisation makes code harder to change and often gains nothing. Start with the simple version.
- Do not trust a single timing run. Repeat measurements and use realistic input sizes.
- A change that speeds up a rarely used method adds complexity with no benefit.
- Document the trade-off when you choose the less readable version, so a later change does not undo it without knowing the cost.

**See also:** [Java overview and platform](../../learning/01-programming-basics/java-overview-platform.md), [Advanced Java Concurrency Part 1](advanced-java-concurrency-part-1.md)

</details>

---

## Quick recap

- `HashMap` suits single-threaded code; `ConcurrentHashMap` rejects nulls and supports concurrent updates.
- `int` overflow wraps silently; use `Math.addExact` or widen to `long` before the arithmetic.
- `a++ + ++a` is well defined but hard to read; split it into steps.
- Floating-point division by zero gives `NaN` or `Infinity`; integer division by zero throws.
- `Comparable` gives one natural order; `Comparator` gives external orders. Use `Integer.compare`, not subtraction.
- `HashSet` and `TreeSet` depend on `equals` and `hashCode`, or `compareTo`. Use stable keys.
- Streams are lazy pipelines that can be consumed once.
- Memory leaks come from objects that stay reachable; enums suit a fixed set of constants.

**See also:** [Core Java Part 2](core-java-part-2.md), [Collections](../../learning/02b-collections/collections-overview.md), [Java 8 Lambdas and Streams](../../learning/03a-modern-java/java8-lambdas-streams.md)
