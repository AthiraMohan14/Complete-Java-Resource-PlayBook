# Optional and Functional Interfaces

`Optional<T>` is a container that holds either a value or nothing, which makes "this might be missing" visible in the type. The `java.util.function` package provides the standard functional interfaces that lambdas and method references target. Interviewers ask about both to see whether you can design null-safe APIs and read stream code fluently.

---

## Core concepts

### Why Optional exists

Returning `null` forces every caller to remember a null check. `Optional` makes the caller handle the empty case in the type signature. It is meant as a return type, not as a field type, a parameter type, or a replacement for every reference.

```java
import java.util.Map;
import java.util.Optional;

public class FindUser {
    static final Map<Integer, String> USERS = Map.of(1, "ada", 2, "linus");

    static Optional<String> findName(int id) {
        return Optional.ofNullable(USERS.get(id));
    }

    public static void main(String[] args) {
        System.out.println(findName(1).orElse("unknown")); // ada
        System.out.println(findName(9).orElse("unknown")); // unknown
    }
}
```

### Creating an Optional

| Factory | Use it when |
|---|---|
| `Optional.of(value)` | The value is known not to be null. Throws `NullPointerException` otherwise. |
| `Optional.ofNullable(value)` | The value may be null. |
| `Optional.empty()` | You need an explicitly empty result. |

### Reading an Optional

Prefer methods that express the intent over `isPresent()` followed by `get()`.

| Method | Behaviour |
|---|---|
| `orElse(x)` | Returns the value or `x`. `x` is always evaluated. |
| `orElseGet(supplier)` | Returns the value or the result of the supplier. Evaluated only when empty. |
| `orElseThrow()` | Returns the value or throws `NoSuchElementException`. Java 10 added the no-argument form. |
| `orElseThrow(supplier)` | Returns the value or throws the exception the supplier builds. |
| `ifPresent(consumer)` | Runs the consumer when a value exists. |
| `ifPresentOrElse(consumer, runnable)` | Java 9. Runs one of two actions. |
| `map(function)` | Transforms the value if present. Returns an empty `Optional` if the result is null. |
| `flatMap(function)` | Use when the function itself returns an `Optional`. |
| `filter(predicate)` | Keeps the value only if it matches. |
| `or(supplier)` | Java 9. Supplies an alternative `Optional`. |
| `stream()` | Java 9. Turns a present value into a one-element stream, or an empty stream. |

```java
import java.util.Optional;

public class OptionalChain {
    record Address(String city) {}
    record User(Address address) {}

    static Optional<String> cityOf(User user) {
        return Optional.ofNullable(user)
                .map(User::address)       // may return null, which becomes empty
                .map(Address::city);
    }

    public static void main(String[] args) {
        System.out.println(cityOf(new User(new Address("Pune")))); // Optional[Pune]
        System.out.println(cityOf(null).orElse("no city"));        // no city
    }
}
```

### Lazy versus eager fallbacks

`orElse` evaluates its argument even when the value is present. If building the fallback is expensive or has side effects, use `orElseGet`.

```java
import java.util.Optional;

public class EagerVsLazy {
    static String expensiveDefault() {
        System.out.println("building default");
        return "default";
    }

    public static void main(String[] args) {
        Optional<String> value = Optional.of("present");
        value.orElse(expensiveDefault());    // prints "building default"
        value.orElseGet(EagerVsLazy::expensiveDefault); // prints nothing
    }
}
```

### Standard functional interfaces

The `java.util.function` package defines a small set of interfaces. Most stream and `Optional` methods take one of these.

| Interface | Shape | Typical use |
|---|---|---|
| `Function<T, R>` | `R apply(T t)` | Transform a value (`map`) |
| `BiFunction<T, U, R>` | `R apply(T t, U u)` | Combine two inputs |
| `Predicate<T>` | `boolean test(T t)` | Filter (`filter`, `anyMatch`) |
| `Consumer<T>` | `void accept(T t)` | Side effects (`forEach`, `ifPresent`) |
| `Supplier<T>` | `T get()` | Lazy creation (`orElseGet`, `generate`) |
| `UnaryOperator<T>` | `T apply(T t)` | A `Function` where input and output types match |
| `BinaryOperator<T>` | `T apply(T t, T u)` | A reduction, such as `reduce` |

Primitive versions avoid boxing: `IntPredicate`, `IntFunction`, `ToIntFunction`, `IntSupplier`, and similar names for `long` and `double`.

Predicates and functions can be composed:

```java
import java.util.function.Function;
import java.util.function.Predicate;

public class Composition {
    public static void main(String[] args) {
        Predicate<String> nonEmpty = s -> !s.isEmpty();
        Predicate<String> shortName = s -> s.length() < 5;
        System.out.println(nonEmpty.and(shortName).test("ada"));  // true

        Function<String, String> trim = String::trim;
        Function<String, Integer> length = String::length;
        System.out.println(trim.andThen(length).apply("  ada ")); // 3
    }
}
```

### Generic methods with lambdas

A lambda's parameter types are inferred from the target functional interface. A generic method can accept any function and keep the types checked at compile time:

```java
import java.util.function.Function;

public class SafeMap {
    static <T, R> R mapOrDefault(T input, Function<T, R> f, R fallback) {
        try {
            return f.apply(input);
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    public static void main(String[] args) {
        System.out.println(mapOrDefault("12", Integer::parseInt, -1)); // 12
        System.out.println(mapOrDefault("x2", Integer::parseInt, -1)); // -1
    }
}
```

---

## How it works / Step by step

1. A method returns `Optional<T>` to say the result may be missing.
2. The caller transforms it with `map` or `flatMap`, which do nothing when empty.
3. The caller finishes with `orElse`, `orElseGet`, or `orElseThrow`, choosing a default, a lazy default, or an exception.
4. Functional interfaces supply the lambdas used in each step.

---

## Common pitfalls

- Calling `get()` without checking. Use `orElseThrow()` so the failure is explicit.
- Using `Optional` as a field, a method parameter, or a collection element. It is not serializable and adds allocation for no benefit.
- Using `orElse` with an expensive or side-effecting argument. Use `orElseGet`.
- Writing `opt.isPresent() ? opt.get() : x` when `orElse` says the same thing.
- Returning `Optional` from a method that returns a collection. Return an empty list instead.
- Confusing `map` and `flatMap`. If the mapping function returns `Optional`, `map` gives `Optional<Optional<T>>`.

!!! tip "Interview tip"
    **Q: Why not return null instead of Optional?**
    `Optional` puts the empty case in the signature, so the compiler and reader see it. A null return depends on documentation and discipline. Keep `Optional` for return values, and do not use it to hide every null in the codebase.

---

## Quick recap

- `Optional` is a return-type tool for "a value might be missing".
- Use `orElseGet` for expensive fallbacks, and `orElseThrow` for failures.
- `map` transforms a value; `flatMap` is for functions that already return an `Optional`.
- `Function`, `Predicate`, `Consumer`, `Supplier`, and the operator interfaces cover most lambda targets.
- Primitive functional interfaces avoid boxing in numeric pipelines.

**See also:** [Java 8 lambdas and streams](java8-lambdas-streams.md) - [Java 9 to 17 features](java9-to-17-features.md) - [Index](index.md)
