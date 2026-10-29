# Wrappers, Strings and Arrays

Java's primitives are fast but not objects, so the language provides wrapper classes to use them where objects are required. Strings and arrays are the two most common data holders in any program. Interviewers ask about `==` versus `equals()`, why `String` is immutable, how autoboxing can throw a `NullPointerException`, and how to choose between `StringBuilder` and `StringBuffer`.

## Core concepts

### Wrapper classes
Each primitive has a wrapper class in `java.lang`: `Byte`, `Short`, `Integer`, `Long`, `Float`, `Double`, `Character`, and `Boolean`. Wrappers are immutable objects. They are needed for generic collections (which hold objects only), for nullable values, and for utility methods such as parsing.

```java
Integer boxed = Integer.valueOf(42);       // explicit boxing (preferred over new Integer)
int primitive = boxed.intValue();          // explicit unboxing
int parsed = Integer.parseInt("123");      // parsing text to a primitive
System.out.println(boxed + parsed);        // 165: unboxing happens in the arithmetic
```

`new Integer(...)` and the other wrapper constructors are deprecated for removal; use `valueOf` or autoboxing.

### Autoboxing and unboxing
The compiler inserts boxing (primitive to wrapper) and unboxing (wrapper to primitive) automatically when a context needs the other form.

```java
import java.util.ArrayList;
import java.util.List;

public class Autoboxing {
    public static void main(String[] args) {
        List<Integer> numbers = new ArrayList<>();
        numbers.add(7);            // autoboxed: Integer.valueOf(7)
        int first = numbers.get(0); // auto-unboxed
        System.out.println(first); // 7
    }
}
```

Unboxing a `null` wrapper throws `NullPointerException`. The cache for `Integer` values covers -128 to 127, so `Integer.valueOf` returns the same object for those values; outside that range, `==` between two boxed values usually compares different objects.

```java
Integer a = 127, b = 127;
Integer c = 128, d = 128;
System.out.println(a == b);       // true: cached
System.out.println(c == d);       // false: different objects
System.out.println(c.equals(d));  // true: compare values with equals
```

### Math and number utilities
`Math` has static helpers: `abs`, `pow`, `sqrt`, `max`, `min`, `round`, `floor`, `ceil`, and `random`. The `*Exact` methods (such as `Math.addExact` and `Math.multiplyExact`) throw `ArithmeticException` on overflow instead of wrapping. `Math.floorDiv` and `Math.floorMod` round toward negative infinity.

```java
System.out.println(Math.round(2.5));       // 3: rounds half up
System.out.println(Math.floorMod(-7, 3));  // 2
System.out.println(Integer.compare(3, 9)); // -1
Math.addExact(Integer.MAX_VALUE, 1);       // throws ArithmeticException
```

### Boolean and Character utilities
`Boolean.parseBoolean("TRUE")` returns `true`; any string other than "true" (ignoring case) gives `false`, so it never throws. `Character` offers classification methods: `isDigit`, `isLetter`, `isLetterOrDigit`, `isWhitespace`, and `getNumericValue`. `Character.isLetter` understands Unicode, so it accepts letters outside ASCII.

```java
System.out.println(Character.isLetter('é'));   // true
System.out.println(Character.isDigit('7'));    // true
System.out.println(Character.getNumericValue('7')); // 7
```

### Strings are immutable
A `String` cannot change after creation. Every "modification" returns a new string. The JVM keeps one copy of each literal in a pool, so identical literals usually refer to the same object.

```java
String s = "Java";
s.toUpperCase();              // returns a new String; s is unchanged
System.out.println(s);        // Java
s = s.toUpperCase();          // reassign to keep the result
System.out.println(s);        // JAVA
```

Useful methods: `length`, `charAt`, `substring`, `indexOf`, `contains`, `replace`, `split`, `strip`, `isBlank`, `repeat`, `lines`, `String.join`, and `String.format`.

```java
System.out.println("  hi  ".strip());          // "hi"
System.out.println("ab".repeat(3));             // ababab
System.out.println(String.join(", ", "a", "b")); // a, b
System.out.println("a,b,,c".split(",").length); // 4: trailing empties are dropped, empty middle kept
```

### == versus equals()
`==` compares references (identity) for objects and values for primitives. `equals()` compares content when the class overrides it, and `String` does. Always compare strings with `equals()`. To ignore case, use `equalsIgnoreCase`. For null-safe comparison of a value you control, write `"expected".equals(value)`.

```java
String x = new String("ok");
String y = "ok";
System.out.println(x == y);            // false
System.out.println(x.equals(y));       // true
System.out.println("ok".equals(null)); // false, no exception
```

### StringBuilder and StringBuffer
Concatenating in a loop creates many temporary strings. `StringBuilder` is mutable and not synchronized, so it is the default choice inside one method or one thread. `StringBuffer` has the same API, with synchronized methods, for the rare case where a single builder is shared between threads.

```java
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 3; i++) {
    sb.append(i).append(',');
}
sb.setLength(sb.length() - 1);   // drop the trailing comma
System.out.println(sb);          // 0,1,2
```

### Arrays
Arrays have a fixed length set at creation and store one type. They are objects, and they live on the heap.

```java
int[] scores = {90, 75, 88};             // initializer
int[] buckets = new int[5];              // all zeros
String[] names = new String[2];          // all nulls

int[][] grid = new int[3][4];            // 3 rows of 4 ints
int[][] jagged = {{1}, {2, 3}, {4, 5, 6}}; // rows may differ in length

System.out.println(scores.length);       // 3: length is a field, not a method
System.out.println(grid[0].length);      // 4
```

### The Arrays utility class
`java.util.Arrays` provides `toString`, `deepToString` (for nested arrays), `sort`, `binarySearch`, `fill`, `copyOf`, `equals`, `deepEquals`, `asList`, and `stream`.

```java
import java.util.Arrays;

public class ArraysDemo {
    public static void main(String[] args) {
        int[] data = {5, 2, 9, 1};
        int[][] grid = {{1, 2}, {3, 4}};
        Arrays.sort(data);
        System.out.println(Arrays.toString(data));           // [1, 2, 5, 9]
        System.out.println(Arrays.binarySearch(data, 5));    // 2
        System.out.println(Arrays.deepToString(grid).length() > 0); // true
    }
}
```

`Arrays.asList` returns a fixed-size list backed by the array: you can set elements but not add or remove them. Changes to the list write through to the array.

### final arrays
Declaring an array `final` fixes the reference, not the elements. The contents can still change.

```java
final int[] counts = new int[2];
counts[0] = 10;        // allowed
// counts = new int[3]; // compile error
```

## How it works / Step by step

1. Assigning a primitive to a wrapper-typed variable runs `Integer.valueOf`, which may return a cached object.
2. Using a wrapper where a primitive is needed calls its `xxxValue()` method; a `null` reference throws `NullPointerException`.
3. A string literal is taken from the string pool; `new String(...)` creates a new object.
4. A `StringBuilder` appends into one growing buffer and produces a `String` only when `toString` is called.
5. Arrays are allocated with a fixed size; index access is bounds-checked and throws `ArrayIndexOutOfBoundsException` when out of range.

## Common pitfalls
- Using `==` to compare wrapper objects with values above 127. Use `equals()` or unbox first.
- Unboxing a `null` value from a map lookup, such as `int n = map.get(key);`, which throws `NullPointerException`.
- Concatenating strings in a loop with `+`. Use `StringBuilder` for loops.
- Ignoring the return value of a string method, as in `s.trim();` with no assignment.
- Expecting `"a,b,,c".split(",")` to keep trailing empty strings. It drops them.
- Using `Arrays.asList(...).add(...)`, which throws `UnsupportedOperationException`.
- Assuming a `final` array is read-only.
- Confusing `length` (a field on arrays) with `length()` (a method on strings).

!!! tip "Interview tip"
    **Q: Why is `String` immutable?** Immutability makes strings safe to share, usable as hash keys because their hash code never changes, and safe for the string pool. The cost is that every change creates a new object, which is why `StringBuilder` exists for building text in a loop.

## Quick recap
- Wrappers box primitives for objects and collections; autoboxing is automatic, and unboxing `null` fails.
- `Integer` values from -128 to 127 are cached, so `==` on them can mislead.
- Strings are immutable; use `equals()` for content and `StringBuilder` for repeated concatenation.
- Arrays have fixed length; `length` is a field, and `Arrays` provides sort, search, and print helpers.
- A `final` array or reference does not make its contents immutable.

**See also:** [Data Types and Variables](../01-programming-basics/data-types-variables.md), [Collections Overview](../02b-collections/collections-overview.md), [Exceptions](exceptions.md)
