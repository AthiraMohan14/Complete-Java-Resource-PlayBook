# Operators and Control Flow

Operators combine values, and control flow decides which code runs and how often. Interviewers test this through small puzzles: integer division, short-circuit evaluation, operator precedence, and whether a `switch` falls through. This page covers each operator family, the precedence rules, the decision and loop statements, and labelled `break` and `continue`.

## Core concepts

### Arithmetic operators
`+`, `-`, `*`, `/`, `%` (remainder). Integer division truncates toward zero, and the remainder has the sign of the dividend. Division by zero with integers throws `ArithmeticException`; with floating-point it gives `Infinity` or `NaN`.

```java
System.out.println(7 / 2);     // 3
System.out.println(-7 / 2);    // -3
System.out.println(-7 % 3);    // -1
System.out.println(7.0 / 0);   // Infinity
```

`Math.floorDiv` and `Math.floorMod` round toward negative infinity when you need that behaviour.

### Increment, decrement, and assignment
`++` and `--` come in prefix and postfix form. Prefix changes the value before the expression is evaluated; postfix uses the old value. Compound assignment operators (`+=`, `-=`, `*=`, and so on) include an implicit narrowing cast.

```java
int i = 5;
int a = i++;   // a = 5, i = 6
int b = ++i;   // b = 7, i = 7

byte small = 10;
small += 300;  // compiles: implicit (byte) cast; 310 wraps to 54
```

### Relational and equality operators
`<`, `<=`, `>`, `>=`, `==`, `!=`. Each produces a `boolean`. For object references, `==` checks identity, not content.

### Logical operators and short-circuiting
`&&` (AND), `||` (OR), and `!` (NOT) work on `boolean` values. `&&` and `||` short-circuit: the right operand is evaluated only when the left one does not decide the result. The non-short-circuit forms `&` and `|` always evaluate both sides.

```java
String text = null;
if (text != null && text.length() > 0) {   // safe: length() is skipped when text is null
    System.out.println(text);
}
int x = 0;
boolean ok = (x != 0) & (10 / x > 1);       // ArithmeticException: both sides run
```

### Bitwise and shift operators
`&`, `|`, `^` (XOR), `~` (complement), `<<` (left shift), `>>` (signed right shift), and `>>>` (unsigned right shift). On `boolean` values, `&`, `|`, and `^` are logical operators that do not short-circuit.

```java
int flags = 0b0101;
System.out.println(flags & 0b0100);  // 4: bit 2 is set
System.out.println(flags << 1);      // 10
System.out.println(-8 >> 1);         // -4: sign preserved
System.out.println(-8 >>> 28);       // 15: zeros shifted in
```

### The ternary operator
`condition ? valueIfTrue : valueIfFalse`. It is an expression, so it can appear inside another expression. Keep it short; nested ternaries are hard to read.

```java
int age = 20;
String label = age >= 18 ? "adult" : "minor";
```

### instanceof
`instanceof` tests the runtime type of an object. Since Java 16 it also supports pattern matching, which declares a variable when the test succeeds.

```java
Object value = "text";
if (value instanceof String s && !s.isEmpty()) {
    System.out.println(s.toUpperCase());
}
```

### Operator precedence and associativity
Higher rows bind more tightly. Most binary operators are left-associative; assignment and the ternary are right-associative.

| Precedence (high to low) | Operators |
|---|---|
| Postfix | `expr++`, `expr--` |
| Unary | `++expr`, `--expr`, `+`, `-`, `~`, `!` |
| Multiplicative | `*`, `/`, `%` |
| Additive | `+`, `-` |
| Shift | `<<`, `>>`, `>>>` |
| Relational | `<`, `<=`, `>`, `>=`, `instanceof` |
| Equality | `==`, `!=` |
| Bitwise AND | `&` |
| Bitwise XOR | `^` |
| Bitwise OR | `\|` |
| Logical AND | `&&` |
| Logical OR | `\|\|` |
| Ternary | `? :` |
| Assignment | `=`, `+=`, and the other compound forms |

```java
int r = 2 + 3 * 4;            // 14, not 20
boolean b = 5 > 3 == true;    // relational binds tighter than equality: true
System.out.println(r + " " + b);
```

Use parentheses whenever the precedence is not obvious to a reader. Clarity beats cleverness.

### if and if-else
```java
int score = 72;
if (score >= 90) {
    System.out.println("A");
} else if (score >= 70) {
    System.out.println("C or B");
} else {
    System.out.println("below C");
}
```

### switch statement
The classic `switch` jumps to a matching `case` and falls through to the next one until it meets a `break`. Fall-through is useful rarely and bug-prone usually.

```java
int day = 3;
switch (day) {
    case 1:
    case 7:
        System.out.println("weekend");
        break;
    case 3:
        System.out.println("midweek");
        // no break: falls through
    case 4:
        System.out.println("printed for 3 and 4");
        break;
    default:
        System.out.println("other");
}
```

The switch works on `int`-compatible types, `char`, `String`, and enums.

### switch expressions
Since Java 14 the arrow form `case ... ->` does not fall through and can produce a value. Use `yield` inside a block to return a value from a block body. Switch expressions must be exhaustive, so a `default` is usually needed for `int` and `String` selectors.

```java
int day = 3;
String kind = switch (day) {
    case 1, 7 -> "weekend";
    case 2, 3, 4, 5, 6 -> {
        String label = "weekday";
        yield label;
    }
    default -> throw new IllegalArgumentException("bad day: " + day);
};
System.out.println(kind);
```

### The five forms of switch
`switch` has grown over several releases. Knowing which form is available in which version is a common interview check.

| Form | Since | Produces a value | Falls through | Typical use |
|---|---|---|---|---|
| Classic statement (`case X:`) | Java 1.0 | No | Yes, unless `break` | Legacy code, deliberate fall-through |
| Arrow statement (`case X ->`) | Java 14 | No | No | Running one action per case |
| Switch expression | Java 14 | Yes | No | Computing a value, with `yield` in blocks |
| Pattern matching | Java 21 | Either | No | Type tests with `when` guards and `case null` |
| Record patterns | Java 21 | Either | No | Destructuring record components in a case |

The classic form accepts `int`-compatible primitives, their wrappers, `char`, `String`, and enums. It does not accept `long`, `float`, `double`, or `boolean`.

Pattern matching lets a `switch` select on any reference type. A sealed hierarchy lets the compiler check that every subtype is handled, so no `default` is needed:

```java
sealed interface Shape permits Circle, Square {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}

public class Areas {
    static double area(Shape shape) {
        return switch (shape) {
            case Circle c -> Math.PI * c.radius() * c.radius();
            case Square s -> s.side() * s.side();
        };
    }

    static String classify(Object obj) {
        return switch (obj) {
            case null -> "null";
            case Integer i when i > 0 -> "positive int " + i;   // guard
            case Integer i -> "other int " + i;
            case String s -> "string of length " + s.length();
            default -> "something else";
        };
    }

    public static void main(String[] args) {
        System.out.println(area(new Square(2)));   // 4.0
        System.out.println(classify(-3));          // other int -3
    }
}
```

Record patterns destructure a record in the `case` label, and they can be nested:

```java
class PointLocator {

    record Point(int x, int y) { }

    static String locate(Object obj) {
        return switch (obj) {
            case Point(int x, int y) when x == 0 && y == 0 -> "origin";
            case Point(int x, int y) -> "point at " + x + ", " + y;
            default -> "not a point";
        };
    }
}
```

Pattern matching `switch` is final in Java 21. Before 21 these forms do not compile, so check the `--release` setting when a snippet fails.

### Loops
```java
for (int i = 0; i < 3; i++) {          // classic for: init, condition, update
    System.out.print(i + " ");
}
int[] nums = {4, 8, 15};
for (int n : nums) {                    // enhanced for-each: read-only traversal
    System.out.print(n + " ");
}
int count = 0;
while (count < 2) {                     // condition checked first
    count++;
}
do {                                    // body runs at least once
    count--;
} while (count > 0);
```

Use the enhanced `for` when you only need each element. Use an index loop when you need the index or want to modify the array.

### break and continue
`break` exits the nearest loop or `switch`. `continue` skips to the next iteration. Labels let you target an outer loop.

```java
outer:
for (int row = 0; row < 3; row++) {
    for (int col = 0; col < 3; col++) {
        if (col == 2) {
            continue;              // next column
        }
        if (row == 1) {
            continue outer;        // next row
        }
        if (row == 2 && col == 1) {
            break outer;          // stop everything
        }
        System.out.print("(" + row + "," + col + ")");
    }
}
```

### Problem solving with control flow
For loop logic, write the loop invariant in a comment: a statement that holds before each iteration. If you cannot state it, the loop is probably wrong. Trace the first two iterations and the last one by hand.

## How it works / Step by step

1. The expression is evaluated using precedence and associativity rules; parentheses override them.
2. `&&` and `||` evaluate the left side, then the right side only if needed.
3. An `if` tests its condition and runs the first matching branch.
4. A `switch` statement jumps to the matching `case` and runs until a `break` or the end; a switch expression evaluates one arm and yields its value.
5. A loop checks its condition (before or after the body, depending on the loop type) and repeats.
6. `break label` and `continue label` transfer control to the labelled loop.

## Common pitfalls
- Using `/` on two `int` values and expecting a fractional result. Cast one operand to `double` first.
- Using `&` where `&&` is meant. The right side then runs even when the left side is false.
- Forgetting `break` in a classic `switch`, which causes unintended fall-through.
- Writing `if (x = 5)` instead of `if (x == 5)`. Java rejects `int` in an `if` condition, but a `boolean` assignment still compiles and is confusing.
- Comparing `String` values with `==` inside a condition.
- Modifying a collection inside an enhanced `for` loop, which throws `ConcurrentModificationException`.
- Writing `a == b == c` and assuming it means `a == b && b == c`. It is parsed as `(a == b) == c`.

!!! tip "Interview tip"
    **Q: What is the difference between `&` and `&&`?** `&&` is short-circuit: the right side is evaluated only if the left side is `true`. `&` always evaluates both sides. Use `&&` for conditions that guard against errors, such as a null check before a method call.

## Quick recap
- Integer division truncates; `%` takes the sign of the dividend.
- `&&` and `||` short-circuit; `&` and `|` do not.
- Precedence puts `*` above `+`, relational above equality, and ternary and assignment at the bottom; use parentheses to be clear.
- Classic `switch` falls through without `break`; arrow-form switch expressions do not and can yield values.
- Labelled `break` and `continue` target an outer loop.

**See also:** [Data Types and Variables](data-types-variables.md), [Syntax Basics](syntax-basics.md), [Wrappers, Strings and Arrays](../02a-core-language/wrappers-strings-arrays.md)
