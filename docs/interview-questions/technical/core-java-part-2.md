# Core Java Questions (Part 2 of 2)

Continued from [Part 1](core-java-part-1.md).

---

## 12. How do you write a custom exception?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Extend `Exception` for a checked exception, or `RuntimeException` for an unchecked one. Provide constructors that accept a message and a cause, so the original failure is kept.

### Explanation
```java
class InsufficientFundsException extends Exception {
    private final double shortfall;

    InsufficientFundsException(String message, double shortfall) {
        super(message);
        this.shortfall = shortfall;
    }

    double getShortfall() { return shortfall; }
}

class Demo {
    static void withdraw(double balance, double amount) throws InsufficientFundsException {
        if (amount > balance) {
            throw new InsufficientFundsException("not enough funds", amount - balance);
        }
    }

    public static void main(String[] args) {
        try {
            withdraw(10, 25);
        } catch (InsufficientFundsException e) {
            System.out.println(e.getMessage() + ", short by " + e.getShortfall());
        }
    }
}
```

### When to use / pitfalls
- Do not put sensitive data into exception messages that may reach logs or clients.
- In Spring Boot, map custom exceptions to HTTP responses with a `@RestControllerAdvice` class. See [Spring and security](spring-and-security-part-1.md).

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 13. What are the differences between `ArrayList` and `LinkedList`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`ArrayList` stores elements in a resizable array, so reads by index are O(1) and adding at the end is amortised O(1). `LinkedList` stores nodes that point to each other, so removing or inserting at a known position is O(1) once you have the node, but finding by index is O(n).

### Explanation
| Operation | `ArrayList` | `LinkedList` |
|---|---|---|
| `get(i)` | O(1) | O(n) |
| Add at end | amortised O(1) | O(1) |
| Insert or remove at the front | O(n) | O(1) |
| Memory per element | lower (array slot) | higher (node and two references) |

In practice `ArrayList` is faster for most workloads because of CPU cache locality. Use `ArrayDeque` when you need a queue or stack.

### When to use / pitfalls
- Do not choose `LinkedList` just because insertion sounds cheap. Measure first.
- Removing inside a for-each loop throws `ConcurrentModificationException`. Use `Iterator.remove()` or `removeIf`.

**See also:** [Core Java](core-java-part-1.md), [Data and persistence](data-and-persistence-part-1.md)

</details>

---

## 14. What is the difference between `List`, `Set`, and `Map`, and between `Comparable` and `Comparator`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A `List` is an ordered collection that allows duplicates. A `Set` holds no duplicates. A `Map` stores key-value pairs and is not a `Collection`. `Comparable` gives a class one natural ordering through `compareTo`. `Comparator` is an external ordering you pass in.

### Explanation
```java
import java.util.*;

record Person(String name, int age) implements Comparable<Person> {
    @Override
    public int compareTo(Person other) {
        return Integer.compare(age, other.age);       // natural order: by age
    }
}

class Demo {
    public static void main(String[] args) {
        List<Person> people = new ArrayList<>(List.of(
                new Person("Asha", 31), new Person("Ben", 25)));
        Collections.sort(people);                                   // uses compareTo
        people.sort(Comparator.comparing(Person::name).reversed()); // external order
        System.out.println(people);
    }
}
```

### When to use / pitfalls
- Keep `compareTo` consistent with `equals` if the type goes into a `TreeSet` or `TreeMap`. Otherwise two "different" elements may be treated as duplicates.
- `Map` is not a subtype of `Collection`, so `for (x : map)` does not compile. Iterate `map.entrySet()`.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 15. How does `HashMap` work internally?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`HashMap` uses an array of buckets. It computes the key's `hashCode()`, spreads the high bits into the low bits, and uses the result to pick a bucket. Keys that land in the same bucket are chained; when a bucket becomes long, Java 8 and later convert it to a tree. The default capacity is 16 and the load factor is 0.75, so the table doubles when more than 12 entries are stored.

### Explanation
Steps for `put(key, value)`:

1. Compute `h = key.hashCode()`, then `h ^ (h >>> 16)` to spread the bits.
2. Compute the index with `(n - 1) & hash`, where `n` is the table length (a power of two).
3. If the bucket is empty, store the entry.
4. If the bucket has an entry with an equal key (`hash` match and `equals()`), replace its value.
5. Otherwise append the new node. When a bucket reaches 8 nodes and the table has at least 64 buckets, the bucket becomes a red-black tree. If the table is smaller, the map resizes instead.
6. After inserting, if the size exceeds the threshold (capacity times 0.75), the table doubles and entries are redistributed.

```java
import java.util.HashMap;
import java.util.Map;

class Demo {
    public static void main(String[] args) {
        Map<String, Integer> stock = new HashMap<>();
        stock.put("apple", 3);
        stock.put(null, 0);                 // one null key is allowed; it goes to bucket 0
        System.out.println(stock.get("apple"));
    }
}
```

### When to use / pitfalls
- Use immutable keys. If a key's `hashCode()` changes after insertion, the entry becomes hard or impossible to find.
- Override `hashCode()` whenever you override `equals()`.
- `HashMap` is not thread-safe. Use `ConcurrentHashMap` for shared access. See [Concurrency](advanced-java-concurrency-part-1.md).
- Pre-size the map when you know the expected size to avoid repeated resizing.

**See also:** [Core Java](core-java-part-1.md), [Concurrency](advanced-java-concurrency-part-1.md)

</details>

---

## 16. What is the difference between fail-fast and fail-safe iterators?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A fail-fast iterator, such as the one from `ArrayList` or `HashMap`, throws `ConcurrentModificationException` if the collection changes structurally after the iterator is created (other than through the iterator itself). A fail-safe iterator, such as the one from `CopyOnWriteArrayList` or `ConcurrentHashMap`, works on a snapshot or tolerates concurrent changes and does not throw this exception.

### Explanation
```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

class Demo {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("a", "b", "c"));
        Iterator<String> it = names.iterator();
        while (it.hasNext()) {
            if (it.next().equals("b")) {
                it.remove();            // safe: the iterator knows about the change
            }
        }
        System.out.println(names);      // [a, c]
    }
}
```

The fail-fast check is best effort. Do not rely on it to detect concurrent access in code that runs on several threads.

### When to use / pitfalls
- Remove elements with `Iterator.remove()` or `removeIf`, never with `list.remove()` inside a for-each loop.
- Fail-safe collections give weakly consistent views. Do not expect them to show every concurrent update.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 17. Is Java pass-by-value or pass-by-reference?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Java is always pass-by-value. For objects, the value that is copied is the reference, so the method can change the object's state through it, but it cannot make the caller's variable point to a different object.

### Explanation
```java
import java.util.ArrayList;
import java.util.List;

class Demo {
    static void addItem(List<String> list) {
        list.add("new");                 // changes the shared object: visible to the caller
    }

    static void replace(List<String> list) {
        list = new ArrayList<>();        // changes only the local copy of the reference
        list.add("lost");
    }

    public static void main(String[] args) {
        List<String> items = new ArrayList<>();
        addItem(items);
        replace(items);
        System.out.println(items);       // [new]
    }
}
```

### When to use / pitfalls
- Returning a mutable internal collection exposes it to callers. Return a copy or an unmodifiable view.
- `final` on a parameter stops reassignment, but it does not make the object immutable.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 18. What changed in recent Java versions that interviewers ask about?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Records (final in Java 16) are concise immutable data carriers. Sealed classes (final in Java 17) restrict which classes may extend a type. Switch expressions (final in Java 14) return values. `instanceof` pattern matching (final in Java 16) removes a separate cast. Record patterns (final in Java 21) allow deconstruction in `switch` and `instanceof`.

### Explanation
```java
sealed interface Shape permits Circle, Square {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}

class Demo {
    static double area(Shape shape) {
        return switch (shape) {
            case Circle c -> Math.PI * c.radius() * c.radius();
            case Square s -> s.side() * s.side();
        };
    }

    public static void main(String[] args) {
        System.out.println(area(new Square(2)));   // 4.0
    }
}
```

The `switch` above compiles without a `default` because the sealed hierarchy is closed. Pattern matching for `switch` requires Java 21 or later.

### When to use / pitfalls
- Records are shallow-immutable: a `List` component can still be modified unless you copy it in the compact constructor.
- Java 21 pattern matching for `switch` is final; check the release notes of your target version before using newer preview features.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## Quick recap

- JVM runs bytecode; JRE adds libraries; JDK adds tools.
- Overloading is compile-time; overriding is runtime.
- Strings are immutable and pooled; use `equals()` for content.
- `finally` always runs; `finalize()` should not be used.
- Checked exceptions must be handled or declared; try-with-resources closes resources for you.
- `HashMap` uses hashing, buckets, and resizing at 0.75 load factor.

**See also:** [Advanced Java and concurrency](advanced-java-concurrency-part-1.md), [Spring and security](spring-and-security-part-1.md), [Data and persistence](data-and-persistence-part-1.md)
