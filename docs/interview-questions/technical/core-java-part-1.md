# Core Java Questions (Part 1 of 3)

Frequently asked questions on the Java language, object-oriented design, strings, exceptions, and collections. Answer each one aloud before you open it.

---


This page is split into 3 parts. Continue to [Part 2](core-java-part-2.md).

## 1. What is the difference between the JDK, the JRE, and the JVM?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The JVM runs compiled bytecode. The JRE is the JVM plus the standard libraries needed to run a program. The JDK is the JRE plus development tools such as `javac`.

### Explanation
- **JVM (Java Virtual Machine):** loads `.class` files, verifies them, interprets or JIT-compiles the bytecode, and manages memory and threads.
- **JRE (Java Runtime Environment):** what you need to run an application. Recent JDK distributions no longer ship a separate JRE, so you will mostly see the JDK.
- **JDK (Java Development Kit):** includes `javac`, `jar`, `javadoc`, and `jshell`, plus the JRE.

Java is compiled to bytecode, which is why one `.class` file runs on any platform that has a matching JVM.

### When to use / pitfalls
- Install a JDK to build code. A JRE alone cannot compile.
- Check the version with `java -version` and `javac -version`. A mismatch between them is a common setup error.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 2. Explain the four pillars of object-oriented programming.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Encapsulation hides state behind methods. Inheritance lets a class reuse and extend another. Polymorphism lets one reference type behave differently depending on the object. Abstraction exposes what an object does and hides how it does it.

### Explanation
```java
class Account {
    private double balance;                 // encapsulation: state is hidden

    public void deposit(double amount) {    // abstraction: callers see what, not how
        if (amount <= 0) throw new IllegalArgumentException("amount must be positive");
        balance += amount;
    }

    public double getBalance() { return balance; }
}

class SavingsAccount extends Account {      // inheritance
    @Override
    public void deposit(double amount) {    // polymorphism: overriding
        super.deposit(amount);
        System.out.println("Deposited into savings");
    }
}
```

### When to use / pitfalls
- Encapsulation without invariants is just getters and setters. Keep fields private and enforce rules inside the class.
- Prefer composition over inheritance when the relationship is "has a" rather than "is a".

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 3. What is the difference between compile-time and runtime polymorphism?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Compile-time polymorphism is method overloading, resolved by the compiler from the static types of the arguments. Runtime polymorphism is method overriding, resolved by the JVM from the actual object type.

### Explanation
```java
class Printer {
    void print(Object o) { System.out.println("object"); }
    void print(String s) { System.out.println("string"); }   // overload
}

class Base {
    void show() { System.out.println("base"); }
}

class Derived extends Base {
    @Override
    void show() { System.out.println("derived"); }             // override
}

class Demo {
    public static void main(String[] args) {
        Printer p = new Printer();
        Object text = "hello";
        p.print(text);        // prints "object": chosen by the static type Object

        Base b = new Derived();
        b.show();             // prints "derived": chosen by the runtime type
    }
}
```

Static methods and private methods are bound at compile time, even if they look like overrides. Fields are also resolved by the static type.

### When to use / pitfalls
- Overloading with `null` arguments can be ambiguous. Avoid overloads that accept different reference types in the same position.
- Hiding a static method in a subclass is not overriding. It is resolved by the reference type.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 4. What is the difference between an abstract class and an interface?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
An abstract class can hold state, constructors, and concrete methods, and a class can extend only one. An interface defines a contract; a class can implement many interfaces. Since Java 8, interfaces can also have default and static methods, and since Java 9, private methods.

### Explanation
```java
interface Notifier {
    void send(String message);

    default void sendAll(String... messages) {   // default method (Java 8+)
        for (String m : messages) send(m);
    }
}

abstract class BaseNotifier implements Notifier {
    protected final String sender;                // state: only possible in a class

    protected BaseNotifier(String sender) { this.sender = sender; }
}

class EmailNotifier extends BaseNotifier {
    EmailNotifier() { super("noreply"); }

    @Override
    public void send(String message) {
        System.out.println(sender + ": " + message);
    }
}
```

Choose an interface for a capability that unrelated classes can share. Choose an abstract class when subclasses share state or a common skeleton.

### When to use / pitfalls
- Interfaces have only `public` members (fields are implicitly `public static final`). Do not expect instance fields.
- Adding a default method to a widely used interface can change the behaviour of existing implementations.

**See also:** [Spring and security](spring-and-security-part-1.md)

</details>

---

## 5. Why can a Java class extend only one class, and how do default methods change this?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Java allows single class inheritance to avoid the diamond problem, where two superclasses define the same method and the compiler cannot pick one. Default methods reintroduce the same ambiguity for interfaces, so Java forces the implementing class to resolve the conflict itself.

### Explanation
```java
interface A { default String hello() { return "A"; } }
interface B { default String hello() { return "B"; } }

class C implements A, B {
    @Override
    public String hello() {
        return A.super.hello() + B.super.hello();   // the class must resolve the conflict
    }
}
```

If `C` did not override `hello()`, the code would not compile. A class can still inherit one implementation from a superclass, and the class wins over interface defaults.

### When to use / pitfalls
- Do not use default methods to mimic multiple inheritance of state. Interfaces cannot hold instance fields.
- The superclass method wins over an interface default with the same signature. Keep this rule in mind when reading legacy code.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 6. Why are Java strings immutable, and what is the string pool?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A `String` object cannot change after creation. This allows it to be shared safely between threads, cached for its hash code, and used as a key in hash-based collections. The string pool is a special area of the heap where the JVM stores one copy of each literal string and reuses it.

### Explanation
```java
class Demo {
    public static void main(String[] args) {
        String s = "hello";
        s.toUpperCase();                    // returns a new String; s is unchanged
        System.out.println(s);              // hello

        String a = "hello";                 // from the pool
        String b = new String("hello");     // a new object outside the pool
        System.out.println(a == b);         // false
        System.out.println(a == b.intern()); // true: intern() returns the pooled instance
    }
}
```

Immutability is enforced by a `final` class with no methods that change the internal `char` array.

### When to use / pitfalls
- Concatenating in a loop creates many temporary strings. Use `StringBuilder` in that case.
- Strings are sensitive data in memory. Prefer `char[]` or a dedicated secret type for passwords, when your library supports it.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 7. What is the difference between `==` and `equals()`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`==` compares primitive values by value, but compares object references by identity (whether both refer to the same object). `equals()` compares the logical content, if the class overrides it.

### Explanation
```java
class Demo {
    public static void main(String[] args) {
        int x = 5, y = 5;
        System.out.println(x == y);                 // true: primitive values

        String s1 = new String("java");
        String s2 = new String("java");
        System.out.println(s1 == s2);               // false: two different objects
        System.out.println(s1.equals(s2));          // true: same characters

        Integer i1 = 1000, i2 = 1000;
        System.out.println(i1 == i2);               // false: outside the Integer cache (-128 to 127)
    }
}
```

The `Integer` cache covers at least -128 to 127. Do not rely on `==` for boxed values.

### When to use / pitfalls
- If you override `equals()`, override `hashCode()` too. Equal objects must have equal hash codes.
- Use `Objects.equals(a, b)` when either side might be `null`.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 8. What are `final`, `finally`, and `finalize()`?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`final` is a modifier: it stops a variable from being reassigned, a method from being overridden, or a class from being extended. `finally` is a block in `try` statements that runs whether or not an exception occurs. `finalize()` is a method on `Object` that the garbage collector could call before reclaiming an object; it is deprecated for removal and should not be used.

### Explanation
```java
class Demo {
    static int read() {
        try {
            return Integer.parseInt("12x");     // throws NumberFormatException
        } catch (NumberFormatException e) {
            System.out.println("bad input");
            return -1;
        } finally {
            System.out.println("cleanup runs");  // runs even after the return
        }
    }

    public static void main(String[] args) {
        final int limit = 10;                    // cannot be reassigned
        System.out.println(read() + limit);
    }
}
```

Use try-with-resources, not `finalize()`, to release files, sockets, and connections.

### When to use / pitfalls
- `finally` can override a `return` value if it contains its own `return`. Avoid that.
- `finalize()` runs at an unpredictable time, or not at all, and it slows garbage collection.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 9. What is the difference between widening and narrowing casting?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Widening converts a smaller type to a larger one (for example `int` to `long`). The compiler does it automatically and it does not lose information. Narrowing converts a larger type to a smaller one (for example `long` to `int`); you must write an explicit cast, and the value may be truncated or change sign.

### Explanation
```java
class Demo {
    public static void main(String[] args) {
        int small = 42;
        long big = small;            // widening: implicit

        double d = 3.9;
        int truncated = (int) d;     // narrowing: 3, the fraction is dropped

        int n = 130;
        byte b = (byte) n;           // narrowing: -126, because byte holds -128 to 127

        System.out.println(big + " " + truncated + " " + b);
    }
}
```

### When to use / pitfalls
- Narrowing with a cast does not throw an exception for numeric overflow. Use `Math.toIntExact(long)` when you want an exception instead.
- Mixed arithmetic is promoted to the wider type, so `int / int` is integer division.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 10. What is the difference between checked and unchecked exceptions?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Checked exceptions extend `Exception` (but not `RuntimeException`). The compiler forces you to catch them or declare them with `throws`. Unchecked exceptions extend `RuntimeException` or `Error`, and the compiler does not force handling.

### Explanation
```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

class Demo {
    static String load(Path p) throws IOException {   // checked: must be declared
        return Files.readString(p);
    }

    public static void main(String[] args) {
        int[] values = new int[2];
        try {
            System.out.println(values[5]);             // unchecked: ArrayIndexOutOfBoundsException
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("index problem: " + e.getMessage());
        }
    }
}
```

`Error` (such as `OutOfMemoryError`) signals a serious JVM problem and is not normally caught.

### When to use / pitfalls
- Do not catch `Exception` or `Throwable` broadly and ignore it. Log it or rethrow it.
- Use checked exceptions for conditions the caller can reasonably recover from. Use unchecked exceptions for programming errors.

**See also:** [Core Java](core-java-part-1.md)

</details>

---

## 11. How does try-with-resources work, and what do `throw` and `throws` mean?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Try-with-resources closes any object that implements `AutoCloseable` automatically at the end of the block, in reverse order of declaration. `throw` raises one exception instance. `throws` declares in a method signature which checked exceptions the method might raise.

### Explanation
```java
import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;

class Demo {
    static String firstLine(String text) throws IOException {   // throws: declares the exception
        try (BufferedReader reader = new BufferedReader(new StringReader(text))) {
            String line = reader.readLine();
            if (line == null) {
                throw new IllegalArgumentException("empty input"); // throw: raises one instance
            }
            return line;
        }   // reader is closed here, even if an exception was thrown
    }

    public static void main(String[] args) throws IOException {
        System.out.println(firstLine("hello\nworld"));
    }
}
```

If the body and `close()` both throw, the body's exception is the primary one and the `close()` exception is added as suppressed (`getSuppressed()`).

### When to use / pitfalls
- Declare resources in the `try` header, not in a separate `finally` that you must write by hand.
- Use chained exceptions (`new ServiceException("...", cause)`) to keep the original cause in the stack trace.

**See also:** [Core Java](core-java-part-1.md)

</details>

---


**Next:** [Part 2](core-java-part-2.md)
