# Ordering: Comparable and Comparator

Sorting and sorted collections need a rule for comparing two objects. `Comparable` gives a class its one natural order. `Comparator` gives you any number of external orders. Interviewers ask about the contract these interfaces must follow, how to build multi-field comparators, and why `TreeSet` can silently drop elements that `equals` would keep.

## Core concepts

### Comparable: natural ordering
A class implements `Comparable<T>` and defines `compareTo`. It returns a negative number when `this` is less than the argument, zero when equal, and a positive number when greater.

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class Version implements Comparable<Version> {
    private final int major;
    private final int minor;

    public Version(int major, int minor) {
        this.major = major;
        this.minor = minor;
    }

    @Override
    public int compareTo(Version other) {
        int byMajor = Integer.compare(major, other.major);
        return byMajor != 0 ? byMajor : Integer.compare(minor, other.minor);
    }

    @Override
    public String toString() {
        return major + "." + minor;
    }

    public static void main(String[] args) {
        List<Version> list = new ArrayList<>(List.of(new Version(2, 1), new Version(1, 9)));
        Collections.sort(list);
        System.out.println(list); // [1.9, 2.1]
    }
}
```

Use `Integer.compare` (or `Long.compare`) rather than subtraction, which can overflow. `String` and the wrapper classes already implement `Comparable`.

### Comparator: external ordering
A `Comparator<T>` is a separate object (often a lambda) that compares two values. Use one when you need a different order, when the class is not yours, or when there are several orders.

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class ByLengthDemo {
    public static void main(String[] args) {
        Comparator<String> byLength = (a, b) -> Integer.compare(a.length(), b.length());
        List<String> names = new ArrayList<>(List.of("Grace", "Ada", "Linus"));
        names.sort(byLength);
        System.out.println(names); // [Ada, Grace, Linus]
    }
}
```

### Building comparators with the factory methods
The `Comparator` interface provides static factories and default methods that compose cleanly.

| Method | Purpose |
|---|---|
| `Comparator.comparing(keyExtractor)` | Order by a key that is `Comparable` |
| `comparingInt`, `comparingLong`, `comparingDouble` | Primitive keys, without boxing |
| `thenComparing(...)` | Break ties with a second comparison |
| `reversed()` | Reverse the order |
| `Comparator.naturalOrder()` / `reverseOrder()` | Natural order or its reverse |
| `nullsFirst` / `nullsLast` | Place `null` values at one end |

```java
import java.util.Comparator;
import java.util.List;

public class EmployeeDemo {
    record Employee(String name, String dept, int salary) { }

    public static void main(String[] args) {
        List<Employee> staff = List.of(
            new Employee("Ana", "Sales", 900),
            new Employee("Ben", "Dev", 1200),
            new Employee("Cy", "Dev", 1100));

        List<Employee> sorted = staff.stream()
            .sorted(Comparator.comparing(Employee::dept)
                .thenComparing(Employee::salary, Comparator.reverseOrder()))
            .toList();

        sorted.forEach(e -> System.out.println(e.name())); // Ben, Cy, Ana
    }
}
```

`Stream.toList()` needs Java 16 or later. The example also uses `Comparator.comparing(Employee::dept)` first, then breaks ties by salary in descending order.

Be careful with arithmetic comparators such as `(a, b) -> a.salary() - b.salary()`. Subtraction can overflow for large values; use `Integer.compare` or `comparingInt`.

### The comparator contract
A comparator must be:

- **Antisymmetric:** if `compare(a, b)` is negative, then `compare(b, a)` is positive.
- **Transitive:** if `a < b` and `b < c`, then `a < c`.
- **Consistent:** repeated calls with the same arguments give the same result.

Violating the contract can make `sort` throw `IllegalArgumentException` ("Comparison method violates its general contract") or leave a `TreeMap` in an inconsistent state.

### Consistency with equals
A sorted collection (`TreeSet`, `TreeMap`) decides "same element" by comparison, not by `equals`. If `compareTo` returns zero for two objects that `equals` says are different, the set keeps only the first one. Document it when they differ, and keep them aligned where possible.

```java
import java.util.Set;
import java.util.TreeSet;

public class VersionSetDemo {
    record Version(int major, int minor) implements Comparable<Version> {
        @Override
        public int compareTo(Version other) {
            int byMajor = Integer.compare(major, other.major());
            return byMajor != 0 ? byMajor : Integer.compare(minor, other.minor());
        }
    }

    public static void main(String[] args) {
        Set<Version> versions = new TreeSet<>();
        versions.add(new Version(1, 0));
        versions.add(new Version(1, 0)); // compareTo is 0, so it is treated as a duplicate
        System.out.println(versions.size()); // 1
    }
}
```

### SortedSet, SortedMap, and their navigable forms
`SortedSet` and `SortedMap` are interfaces for collections kept in order. Their navigable successors, `NavigableSet` and `NavigableMap`, add methods such as `floor`, `ceiling`, `higher`, `lower`, `first`, `last`, `pollFirst`, and `descendingSet`. `TreeSet` and `TreeMap` implement the navigable interfaces, and `ConcurrentSkipListSet` and `ConcurrentSkipListMap` provide thread-safe equivalents.

### Sorting arrays and lists
- `Arrays.sort(int[])` uses a dual-pivot quicksort for primitives. It is not stable, but stability cannot be observed for equal primitive values, so it does not matter there.
- `Arrays.sort(Object[])` and `List.sort` use a stable merge-based algorithm (TimSort), so equal elements keep their relative order.
- Pass a comparator to sort objects by something other than their natural order.

## How it works / Step by step

1. `Collections.sort` or `List.sort` calls `compareTo` or the comparator for pairs of elements.
2. `TimSort` finds runs of already sorted data and merges them, so nearly sorted input is fast.
3. `TreeSet.add(x)` walks the tree comparing `x` with stored elements; if a comparison returns zero, the element is treated as present and is not added.
4. `thenComparing` runs the second comparator only when the first returns zero.
5. `reversed()` wraps the comparator so that `compare(a, b)` returns `compare(b, a)`.

## Common pitfalls
- Using subtraction in a comparator, which can overflow.
- Implementing `Comparable` inconsistently with `equals`, so a `TreeSet` drops "distinct" objects.
- Writing a comparator that is not transitive, such as one that compares only some fields in some cases.
- Forgetting that `Comparator.comparing` throws `NullPointerException` when a key is `null`, unless wrapped with `nullsFirst` or `nullsLast`.
- Mixing up `Collections.sort` (sorts a list) with `Collections.reverseOrder()` (returns a comparator).
- Expecting `Arrays.sort` on primitives to be stable. For primitives, stability is unobservable, so it does not matter.
- Sorting a list returned by `List.of`, which throws `UnsupportedOperationException`.

!!! tip "Interview tip"
    **Q: Comparable or Comparator?** Use `Comparable` when the class has one obvious natural order and you control the class. Use a `Comparator` when you need multiple orders, when the class is from a library, or when the order depends on the context. A class can have many comparators but only one `compareTo`.

## Quick recap
- `Comparable` defines a natural order through `compareTo`; `Comparator` defines an external order.
- Build comparators with `comparing`, `thenComparing`, and `reversed`; use `comparingInt` for primitives.
- Use `Integer.compare`, not subtraction, to avoid overflow.
- Sorted collections use comparison, not `equals`, to detect duplicates.
- Object sorting in Java is stable; the sort contract requires transitive, consistent comparators.

**See also:** [Sets and Maps](sets-and-maps.md), [Lists](lists.md), [Iterators and Utilities](iterators-and-utilities.md)
