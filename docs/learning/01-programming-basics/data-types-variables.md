# Data Types and Variables

Java splits types into primitives, which hold a single value directly, and reference types, which hold a pointer to an object. Every variable also has a kind (local, instance, or static), a scope, and modifiers that control access and behaviour. Interviewers ask about sizes, default values, and the difference between `==` on primitives and on objects, so it is worth knowing this page well.

## Core concepts

### Primitive types
Java has eight primitive types. Their sizes and ranges are fixed by the language, not by the platform.

| Type | Size | Range or content | Default | Literal example |
|---|---|---|---|---|
| `byte` | 8 bits | -128 to 127 | `0` | `(byte) 100` |
| `short` | 16 bits | -32,768 to 32,767 | `0` | `(short) 1000` |
| `int` | 32 bits | -2,147,483,648 to 2,147,483,647 | `0` | `1_000_000` |
| `long` | 64 bits | about -9.2 × 10^18 to 9.2 × 10^18 | `0L` | `10_000_000_000L` |
| `float` | 32 bits | IEEE 754 single precision | `0.0f` | `3.14f` |
| `double` | 64 bits | IEEE 754 double precision | `0.0` | `3.14159` |
| `char` | 16 bits | Unsigned UTF-16 code unit, `'\u0000'` to `'￿'` | `'\u0000'` | `'A'` |
| `boolean` | Not fixed by the language spec | `true` or `false` | `false` | `true` |

Underscores in numeric literals are allowed (Java 7 and later), and hexadecimal (`0xFF`), octal, and binary (`0b1010`) literals are available. The `boolean` size is intentionally left to the JVM implementation, so do not quote a size for it.

```java
public class PrimitiveDemo {
    public static void main(String[] args) {
        int max = Integer.MAX_VALUE;
        System.out.println(max + 1);              // wraps around to -2147483648
        System.out.println(Byte.MIN_VALUE + " " + Byte.MAX_VALUE); // -128 127
        System.out.println(0.1 + 0.2 == 0.3);     // false: floating point is approximate
        System.out.println(10 / 4);               // 2: integer division
        System.out.println(10 / 4.0);             // 2.5
    }
}
```

### Default values
Fields (instance and static) get default values automatically, as shown in the table. Local variables get no default. The compiler rejects a read of a local variable that has not been definitely assigned.

```java
public class Defaults {
    static int count;          // 0
    String name;               // null

    public static void main(String[] args) {
        int local;
        // System.out.println(local);  // compile error: variable might not have been initialized
        local = 5;
        System.out.println(count + " " + new Defaults().name + " " + local); // 0 null 5
    }
}
```

### Reference types
Anything that is not a primitive is a reference type: classes, interfaces, arrays, enums, and records. A variable of a reference type holds the address of an object (in practice, a reference the JVM manages), or `null` if it points to nothing. The default for reference fields is `null`.

```java
String a = "hello";
String b = "hello";
String c = new String("hello");
System.out.println(a == b);       // true: both refer to the same interned literal
System.out.println(a == c);       // false: different objects
System.out.println(a.equals(c));  // true: same content
```

For primitives, `==` compares values. For references, `==` compares identity, and `equals()` compares content when the class defines it.

### Variable kinds: local, instance, static
| Kind | Declared | Lives as long as | Default value |
|---|---|---|---|
| Local | Inside a method, constructor, or block | The block runs | None; must be assigned before use |
| Instance | In a class, without `static` | The object exists | Type default |
| Static | In a class, with `static` | The class is loaded | Type default |

```java
public class Counter {
    static int created = 0;   // static: shared by all Counter objects
    int value;                // instance: one per object

    Counter() {
        created++;
    }

    void increment() {
        int step = 1;         // local: exists only during this call
        value += step;
    }

    public static void main(String[] args) {
        Counter a = new Counter();
        Counter b = new Counter();
        a.increment();
        System.out.println(created + " " + a.value + " " + b.value); // 2 1 0
    }
}
```

Note that `step` is a local variable, so it has no default. Note also that a `static` field is accessed through the class name, while an instance field needs an object.

### Scope and lifetime
Scope is where a name is visible; lifetime is how long the storage exists. A block (anything between `{` and `}`) limits the scope of the variables declared in it. Loop variables such as `i` in `for (int i = 0; ...)` exist only for the loop. A local variable captured by a lambda or an inner class must be effectively final, which means it is never reassigned after initialization.

### Final variables
`final` on a variable means it can be assigned once. `final` on a reference variable fixes the reference, not the object it points to.

```java
final int limit = 10;          // cannot be reassigned
final int[] values = {1, 2, 3};
values[0] = 99;                // allowed: the array's contents change
// values = new int[3];        // compile error: the reference is final
```

### Access modifiers
Access modifiers control which code can see a member.

| Modifier | Same class | Same package | Subclass in another package | Anywhere |
|---|---|---|---|---|
| `private` | Yes | No | No | No |
| (default, no keyword) | Yes | Yes | No | No |
| `protected` | Yes | Yes | Yes (through inheritance) | No |
| `public` | Yes | Yes | Yes | Yes |

Top-level classes can be `public` or package-private (default). Use `private` for fields by default, and widen access only when needed.

### Non-access modifiers
| Modifier | Applies to | Effect |
|---|---|---|
| `static` | Fields, methods, nested classes | Belongs to the class, not to an instance |
| `final` | Variables, methods, classes | Cannot be reassigned, overridden, or extended |
| `abstract` | Classes, methods | Cannot be instantiated, or must be implemented by a subclass |
| `synchronized` | Methods, blocks | Only one thread at a time enters the guarded code |
| `transient` | Fields | Excluded from default serialization |
| `volatile` | Fields | Reads and writes go to main memory; visibility between threads, not atomicity |
| `native` | Methods | The body is written in platform code outside Java (usually C or C++) and reached through JNI. The declaration has no body and ends with a semicolon |

`transient` and `volatile` are used with serialization and concurrency, which are covered in later material. The example below shows the shape of each.

```java
import java.io.Serializable;

public class Session implements Serializable {
    private static final long serialVersionUID = 1L;

    private String userId;
    private transient String cachedToken;  // not written when serialized
    private volatile boolean active;       // visible to other threads when changed

    public synchronized void deactivate() {
        active = false;
    }
}
```

`native` is the one modifier in the table that does not add behaviour in Java code. The compiler only checks the declaration; the implementation lives in a shared library that the program loads, usually with `System.loadLibrary`. Java code calls the method like any other, and the JVM hands the call to the native code.

```java
public class Clock {
    static {
        System.loadLibrary("clock");   // loads libclock.so, or clock.dll on Windows
    }

    // No body here: the implementation is in the native library
    public native long currentMillis();
}
```

A few keywords are easy to get wrong:

- `const` is a reserved keyword with no meaning. You cannot use it as a name or a modifier. Use `static final` for constants.
- `strictfp` was needed for strict floating-point arithmetic before Java 17. Since 17 every floating-point operation is strict, so the modifier has no effect.

### Local variable type inference with var (Java 10)
`var` lets the compiler infer the type of a local variable from its initializer. The variable is still statically typed; only the spelling changes.

```java
import java.util.ArrayList;
import java.util.List;

public class VarDemo {
    public static void main(String[] args) {
        var total = 0L;                             // long
        var names = new ArrayList<String>();        // ArrayList<String>
        List<String> copy = names;                  // the declared type can still be spelled out
        names.add("Ada");
        System.out.println(total + " " + copy);     // 0 [Ada]
    }
}
```

`var` is a reserved type name, not a keyword. Its use is limited to local variables, `for` loop variables, and try-with-resources variables. It cannot declare fields, method parameters, or return types. It also needs an initializer that gives a type: `var x = null;` and `var a = {1, 2};` do not compile.

Use `var` when the right-hand side makes the type obvious, such as a constructor call. Spell the type out when the reader would have to guess it.

## How it works / Step by step

1. The compiler checks that each local variable is assigned before it is read.
2. Primitive variables hold the value itself; reference variables hold a reference to an object.
3. Assignment copies the value for primitives and copies the reference for objects.
4. When a block ends, its local variables go out of scope; objects they referred to may become unreachable and eligible for garbage collection.
5. Field access follows the modifiers: `private` is checked at compile time, so the rule is enforced before the code runs.

## Common pitfalls
- Using `==` to compare `String` contents. Use `equals()`.
- Overflowing `int` silently. `Integer.MAX_VALUE + 1` wraps to a negative number; use `Math.addExact` to detect it.
- Expecting `10 / 4` to equal `2.5`. Both operands are `int`, so the result is `int`.
- Assuming a `final` array can't change. The reference is fixed; its elements can still change.
- Leaving a `volatile` field unsynchronized and expecting atomic updates such as `count++`. It is not atomic.
- Writing `long big = 10000000000;` without the `L` suffix. The literal is too large for `int` and fails to compile.
- Declaring a local variable and reading it before assignment in one branch of an `if`.
- Writing `var items = new ArrayList<>();`, which infers `ArrayList<Object>`. Give the type argument, as in `new ArrayList<String>()`.

!!! tip "Interview tip"
    **Q: What is the default value of a local variable versus an instance variable?** Instance and static fields get defaults (`0`, `false`, `'\u0000'`, or `null`). Local variables have no default, and the compiler refuses to compile code that reads one before it is definitely assigned. The rule exists to prevent reading leftover or uninitialized values.

## Quick recap
- Eight primitive types have fixed sizes; `boolean` size is not defined by the language spec.
- Fields get default values; local variables must be assigned before use.
- Primitives compare by value with `==`; objects compare by identity, and `equals()` compares content.
- `final` on a reference fixes the reference, not the object.
- `private` by default for fields; `transient` and `volatile` have specific, narrow purposes.

**See also:** [Syntax Basics](syntax-basics.md), [Operators and Control Flow](operators-control-flow.md), [Java Overview and Platform](java-overview-platform.md)
