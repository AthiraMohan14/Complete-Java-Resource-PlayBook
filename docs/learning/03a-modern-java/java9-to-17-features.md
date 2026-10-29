# Java 9 to 17 Features

Between Java 9 and Java 17, Java moved from a slow release cycle to a six-month one. Many features arrived first as preview features, then became final after feedback. Interviewers ask about these to check that you know which features are final, which were preview, and what each one removes from the boilerplate you would otherwise write.

---

## Core concepts

### Release cadence and preview features

Since Java 10, a new feature release ships every six months. A feature can be marked **preview** in one release. Preview features are off by default and need `--enable-preview` to compile and run. They can change or be removed. A feature becomes **final** only after one or more rounds of feedback. The table below lists the status that matters in interviews.

| Feature | Preview | Final |
|---|---|---|
| Modules (JPMS) | - | Java 9 |
| `var` (local variable type inference) | - | Java 10 |
| `HttpClient` | incubator in 9 | Java 11 |
| `switch` expressions | Java 12 and 13 | Java 14 |
| Text blocks | Java 13 and 14 | Java 15 |
| Records | Java 14 and 15 | Java 16 |
| `instanceof` pattern matching | Java 14 and 15 | Java 16 |
| Sealed classes | Java 15 and 16 | Java 17 |
| Pattern matching for `switch` | Java 17 to 20 (several rounds) | Java 21 |

### Java 9: modules and private interface methods

The Java Platform Module System (JPMS) lets a library declare what it exports and what it requires. A `module-info.java` file sits at the root of the module.

```java
// module-info.java
module com.example.orders {
    requires java.sql;          // this module depends on java.sql
    exports com.example.orders.api; // other modules may use this package
}
```

Only exported packages are visible outside the module. Everything else is encapsulated, even if it is `public`. Modules are covered in more depth in [Java tools and utilities](../03c-tooling-utilities/java-tools-utilities.md).

Java 9 also allowed `private` methods in interfaces. They let default methods share code without exposing a helper to implementers.

```java
public interface Logger {
    default void info(String message) {
        log("INFO", message);
    }

    default void warn(String message) {
        log("WARN", message);
    }

    private void log(String level, String message) {
        System.out.println("[" + level + "] " + message);
    }
}
```

Java 9 also added `Optional.ifPresentOrElse`, `Optional.or`, `Optional.stream`, and the `List.of`, `Set.of`, and `Map.of` factory methods for immutable collections.

### Java 10: local variable type inference (`var`)

`var` lets the compiler infer the type of a local variable from its initializer. It is not dynamic typing. The type is fixed at compile time.

```java
import java.util.ArrayList;
import java.util.List;

public class VarDemo {
    public static void main(String[] args) {
        var names = new ArrayList<String>();   // inferred as ArrayList<String>
        names.add("ada");
        for (var name : names) {               // works in enhanced for loops
            System.out.println(name.length());
        }
        var count = 3;                         // int
        // count = "three";                    // compile error: incompatible types
        List<String> copy = List.copyOf(names);
        System.out.println(copy.size() + count);
    }
}
```

`var` is only for local variables, for-loop variables, and lambda parameters (Java 11). It cannot be used for fields, method parameters, or return types. It also needs an initializer, unless the variable is a `for` loop index.

### Java 11: HttpClient and new String methods

`java.net.http.HttpClient` is the standard HTTP client. It supports HTTP/1.1 and HTTP/2, synchronous and asynchronous calls, and WebSocket. `HttpURLConnection` is legacy.

```java
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class HttpDemo {
    public static void main(String[] args) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://example.com/"))
                .GET()
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println(response.statusCode());
    }
}
```

Java 11 also added these `String` methods:

| Method | Behaviour |
|---|---|
| `strip()` | Removes leading and trailing whitespace. Unlike `trim()`, it understands Unicode whitespace. |
| `isBlank()` | `true` when the string is empty or contains only whitespace. |
| `lines()` | Returns a `Stream<String>` split on line terminators. |
| `repeat(n)` | Repeats the string `n` times. |

```java
public class StringAdditions {
    public static void main(String[] args) {
        String text = "  alpha\n  beta  \n";
        text.lines().map(String::strip).forEach(System.out::println);
        System.out.println("ab".repeat(3));       // ababab
        System.out.println("   ".isBlank());      // true
    }
}
```

### Java 12 and 13: the first previews

Java 12 added two items that are relevant here. `Collectors.teeing` sends a stream to two collectors and merges the results with a function. `NumberFormat.getCompactNumberInstance` formats numbers such as `1.2K` or `3M`. Java 12 also introduced the first preview of `switch` expressions.

Java 13 previewed text blocks.

Check the official release notes for the exact details of these previews before relying on them in an answer.

### Java 14: switch expressions and the CMS removal

`switch` became an expression in Java 14. It returns a value, uses `->` arms, and must be exhaustive when used as an expression. A `yield` statement returns a value from a block arm.

```java
public class SwitchExpr {
    enum Day { MON, TUE, SAT, SUN }

    static String kind(Day day) {
        return switch (day) {
            case SAT, SUN -> "weekend";
            case MON, TUE -> {
                String label = "weekday";
                yield label;
            }
        };
    }

    public static void main(String[] args) {
        System.out.println(kind(Day.SAT)); // weekend
        System.out.println(kind(Day.MON)); // weekday
    }
}
```

Java 14 also removed the Concurrent Mark Sweep (CMS) garbage collector. See [Garbage collection](../03b-jvm-internals/garbage-collection.md).

### Java 14 and 15: records and pattern matching previews

A record is a transparent, immutable data carrier. The compiler generates the constructor, accessors, `equals`, `hashCode`, and `toString`. Records were preview in 14 and 15, and final in Java 16.

```java
public record Point(int x, int y) {
    public Point {                       // compact constructor for validation
        if (x < 0 || y < 0) {
            throw new IllegalArgumentException("negative coordinate");
        }
    }

    public double distanceFromOrigin() {
        return Math.sqrt(x * x + y * y);
    }
}
```

`instanceof` pattern matching removes the explicit cast after a type check. It was preview in 14 and 15, and final in Java 16.

```java
public class PatternInstanceof {
    static String describe(Object obj) {
        if (obj instanceof String s && !s.isBlank()) {
            return "non-blank string of length " + s.length();
        }
        return "something else";
    }

    public static void main(String[] args) {
        System.out.println(describe("hello")); // non-blank string of length 5
        System.out.println(describe(42));      // something else
    }
}
```

Java 15 also finalised text blocks. A text block is a multi-line string literal, delimited by `"""`. Indentation is stripped based on the closing delimiter's position.

```java
public class TextBlockDemo {
    public static void main(String[] args) {
        String json = """
                {
                  "name": "ada",
                  "role": "engineer"
                }
                """;
        System.out.print(json);
    }
}
```

Java 15 also removed the Nashorn JavaScript engine, and previewed sealed classes.

### Java 16: records and instanceof final

Java 16 made records and `instanceof` pattern matching final. It also added `Stream.toList()`, which returns an unmodifiable list. The Java 16 finalisation of records is the feature to name when someone asks what changed after the previews.

### Java 17: sealed classes

A sealed class or interface limits which classes may extend or implement it. The `permits` clause lists them. Each permitted subclass must be `final`, `sealed`, or `non-sealed`. The compiler then knows every subtype, so an exhaustive `switch` needs no default branch.

```java
sealed interface Shape permits Circle, Square {}

record Circle(double radius) implements Shape {}

record Square(double side) implements Shape {}

public class ShapeArea {
    static double area(Shape shape) {
        if (shape instanceof Circle c) {
            return Math.PI * c.radius() * c.radius();
        }
        if (shape instanceof Square s) {
            return s.side() * s.side();
        }
        throw new IllegalStateException("unknown shape"); // unreachable for these two types
    }

    public static void main(String[] args) {
        System.out.printf("%.2f%n", area(new Square(2.0))); // 4.00
    }
}
```

Records are implicitly `final`, so they satisfy the sealed subtype rule. The compiler knows the full list of subtypes, which is what lets a `switch` over a sealed type be exhaustive without a `default` branch. Pattern matching for `switch` was preview from Java 17 through Java 20 and became final in Java 21, covered in [Java 21 features](java21-features.md).

---

## How it works / Step by step

| Release | Headline items |
|---|---|
| 9 | JPMS modules, private interface methods, `List.of` / `Set.of` / `Map.of` |
| 10 | `var` |
| 11 | `HttpClient`, `String.strip`, `isBlank`, `lines`, `repeat` |
| 12 to 13 | Switch expression and text block previews, `Collectors.teeing`, compact number formatting |
| 14 | Switch expressions final, records and `instanceof` patterns in preview, CMS removed |
| 15 | Text blocks final, sealed classes preview, Nashorn removed, hidden classes |
| 16 | Records final, `instanceof` pattern matching final, `Stream.toList()` |
| 17 | Sealed classes final (LTS release) |

---

## Common pitfalls

- Using `var` where the inferred type is hard to read. It reduces noise, but it should not hide meaning.
- Treating `var` as dynamic typing. The type is still checked at compile time.
- Using `trim()` when you want Unicode-aware whitespace removal. Use `strip()`.
- Forgetting that a record's fields are `final` and that the class is `final`. Records are not for mutable state.
- Expecting `permits` to work without matching subclass modifiers. Each permitted class needs `final`, `sealed`, or `non-sealed`.
- Assuming a preview feature works in production. Preview needs `--enable-preview` and may change.
- Using `HttpURLConnection` in new code. Use `HttpClient`.

!!! tip "Interview tip"
    **Q: Which Java version made records and sealed classes final?**
    Records were final in Java 16, and sealed classes in Java 17. Java 17 is an LTS release, so most production code that uses sealed types targets it or a later LTS.

---

## Quick recap

- Java 9 added modules, private interface methods, and immutable collection factories.
- `var` (Java 10) infers local variable types at compile time.
- `HttpClient` (Java 11) is the standard HTTP client; `String` gained `strip`, `isBlank`, `lines`, and `repeat`.
- Switch expressions (final in 14), text blocks (final in 15), records (final in 16), and sealed classes (final in 17) are the main final additions.
- Pattern matching removes casts after type checks, and sealed types make `switch` exhaustive.

**See also:** [Java 8 lambdas and streams](java8-lambdas-streams.md) - [Java 21 features](java21-features.md) - [Index](index.md)
