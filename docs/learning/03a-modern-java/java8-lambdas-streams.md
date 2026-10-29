# Java 8: Lambdas and Streams

Java 8 added lambda expressions, method references, and the Stream API. Together they let you describe what to compute over a collection instead of writing the loop by hand. Interviewers ask about them to check that you know the difference between lazy intermediate operations and eager terminal operations, and when a stream is the wrong tool.

---

## Core concepts

### Functional interfaces

A functional interface has exactly one abstract method. A lambda is an instance of one. The `@FunctionalInterface` annotation asks the compiler to check that rule. It is optional, but it documents intent and gives a clear error if someone adds a second abstract method later.

```java
@FunctionalInterface
interface Discount {
    double apply(double price);
}

public class DiscountDemo {
    public static void main(String[] args) {
        Discount tenPercent = price -> price * 0.9;
        System.out.println(tenPercent.apply(200.0)); // 180.0
    }
}
```

### Lambda syntax

A lambda has a parameter list, `->`, and a body. Parentheses are optional for a single parameter with an inferred type. Use braces and `return` when the body has more than one statement.

```java
import java.util.function.BinaryOperator;

public class LambdaSyntax {
    public static void main(String[] args) {
        BinaryOperator<Integer> add = (a, b) -> a + b;   // expression body
        BinaryOperator<Integer> max = (a, b) -> {         // block body
            if (a > b) {
                return a;
            }
            return b;
        };
        System.out.println(add.apply(2, 3)); // 5
        System.out.println(max.apply(2, 3)); // 3
    }
}
```

A lambda can use a local variable only if that variable is effectively final. It cannot reassign it. The rule exists because the lambda can outlive the method call that created it, and Java captures a copy of the value.

### Method references

A method reference is a shorter way to write a lambda that only calls an existing method. There are four forms.

| Form | Example | Equivalent lambda |
|---|---|---|
| Static method | `Integer::parseInt` | `s -> Integer.parseInt(s)` |
| Instance method of a particular object | `printer::print` | `x -> printer.print(x)` |
| Instance method of an arbitrary object of a type | `String::toUpperCase` | `s -> s.toUpperCase()` |
| Constructor | `ArrayList::new` | `() -> new ArrayList<>()` |

```java
import java.util.List;

public class MethodRefs {
    public static void main(String[] args) {
        List<String> names = List.of("ada", "linus", "grace");
        names.stream()
             .map(String::toUpperCase)   // instance method of an arbitrary object
             .forEach(System.out::println); // instance method of a particular object
    }
}
```

### Streams: the basic shape

A stream is a sequence of elements and a pipeline of operations on them. A pipeline has three parts:

1. A **source** (a collection, an array, `Stream.of`, `IntStream.range`, a file's lines).
2. Zero or more **intermediate operations** (`filter`, `map`, `flatMap`, `sorted`, `distinct`, `limit`, `skip`, `peek`). These return a new stream.
3. One **terminal operation** (`forEach`, `collect`, `reduce`, `count`, `findFirst`, `anyMatch`, `toList`). This runs the pipeline and produces a result or side effect.

```java
import java.util.List;

public class PipelineShape {
    public static void main(String[] args) {
        long count = List.of(3, 8, 1, 9, 4).stream()  // source
                .filter(n -> n > 2)                   // intermediate
                .map(n -> n * n)                      // intermediate
                .count();                             // terminal
        System.out.println(count); // 4
    }
}
```

### Laziness and short-circuiting

Intermediate operations do nothing until a terminal operation runs. The elements then flow through the whole pipeline one at a time, so a `filter` followed by `findFirst` may stop after touching only a few elements.

```java
import java.util.List;
import java.util.Optional;

public class LazyDemo {
    public static void main(String[] args) {
        Optional<Integer> first = List.of(1, 2, 3, 4, 5).stream()
                .peek(n -> System.out.println("visit " + n))
                .filter(n -> n % 2 == 0)
                .findFirst();
        System.out.println(first.orElse(-1));
        // Prints "visit 1", "visit 2", then 2. Elements 3 to 5 are never visited.
    }
}
```

A stream can be consumed only once. Reusing a `Stream` object throws `IllegalStateException`. Create a new stream from the source when you need another pass.

### Collectors

`collect` with a `Collector` turns a stream into a collection or a summary. `Collectors` provides the common ones.

```java
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class CollectorsDemo {
    record Order(String customer, double amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("ana", 20.0),
                new Order("ben", 35.5),
                new Order("ana", 12.0));

        Map<String, Double> totalByCustomer = orders.stream()
                .collect(Collectors.groupingBy(
                        Order::customer,
                        Collectors.summingDouble(Order::amount)));

        System.out.println(totalByCustomer.get("ana")); // 32.0
    }
}
```

`Collectors.toList()` returns an `ArrayList` in practice, but the spec does not promise that type. Java 16 added `Stream.toList()`, which returns an unmodifiable list and is the usual choice now.

### Parallel streams

`parallelStream()` or `.parallel()` splits work across the common `ForkJoinPool`. It helps only for large, CPU-bound work on splittable sources. For small inputs, I/O, or work that shares mutable state, it is slower or wrong.

---

## How it works / Step by step

| Step | What happens |
|---|---|
| 1. Build the pipeline | Intermediate calls only record the operation. Nothing runs. |
| 2. Call a terminal operation | The stream pulls elements from the source. |
| 3. Each element passes through the stages | Elements are processed one by one, not stage by stage over the whole collection. |
| 4. Short-circuit if possible | `findFirst`, `anyMatch`, and `limit` can stop early. |

---

## Common pitfalls

- Using `forEach` to build a collection. Use `collect` instead. Mutating an external list from inside a stream is a side effect, and it breaks under parallel execution.
- Reusing a stream after a terminal operation. It throws `IllegalStateException`.
- Relying on `peek` for real work. `peek` is for debugging. Some pipelines skip it entirely when the count is known.
- Using `Collectors.toMap` without a merge function. A duplicate key throws `IllegalStateException`.
- Capturing a variable that is not effectively final.
- Assuming `parallelStream` is always faster. Measure first.

!!! tip "Interview tip"
    **Q: What is the difference between intermediate and terminal operations?**
    Intermediate operations are lazy and return a new stream. Terminal operations trigger the pipeline and either produce a result or close it. Without a terminal operation, nothing runs.

---

## Quick recap

- A lambda is an instance of a functional interface, which has one abstract method.
- Method references are shorter forms of lambdas that call an existing method.
- A stream pipeline is one source, zero or more intermediate operations, and one terminal operation.
- Intermediate operations are lazy; short-circuit terminals can stop early.
- A stream can be consumed only once.
- Prefer `collect` and `Stream.toList()` over side effects in `forEach`.

**See also:** [Optional and functional interfaces](optional-functional-interfaces.md) - [Java 9 to 17 features](java9-to-17-features.md) - [Index](index.md)
