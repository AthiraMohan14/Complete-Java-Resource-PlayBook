# Syntax Basics

Every Java program follows the same skeleton: a class, a `main` method, and a compile-then-run cycle. This page covers that structure, the naming rules and keywords the compiler enforces, console input with `Scanner`, methods and scope, and type casting. Interviewers use these topics to check that you can read and write basic Java without hesitation.

## Core concepts

### Program structure and the main method
A Java program needs at least one class. The entry point is a `public static void main(String[] args)` method. The JVM calls it with an array of command-line arguments, which are always `String` values.

```java
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, " + (args.length > 0 ? args[0] : "world"));
    }
}
```

The file name must match the public class name: this code lives in `Hello.java`.

### Compile, then run
`javac` compiles source into bytecode. `java` runs the class by name, without the `.class` extension.

```text
javac Hello.java      # produces Hello.class
java Hello Ada        # prints: Hello, Ada
```

Since Java 11 you can also run a single source file directly, which compiles it in memory first:

```text
java Hello.java Ada
```

### Naming conventions and case sensitivity
Java is case sensitive: `count`, `Count`, and `COUNT` are three different names. The conventions below are not enforced by the compiler, but every Java codebase follows them:

| Element | Convention | Example |
|---|---|---|
| Class, interface, enum, record | PascalCase | `OrderService` |
| Method, variable, parameter | camelCase | `calculateTotal` |
| Constant (`static final`) | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Package | all lowercase, reverse domain | `com.example.orders` |

Identifiers may contain letters, digits, `_`, and `$`, and they must not start with a digit or be a keyword. Unicode letters are allowed in identifiers.

### Keywords
Java reserves these words, which cannot be used as identifiers:

```text
abstract   assert    boolean    break      byte       case
catch      char      class      const      continue   default
do         double    else       enum       extends    final
finally    float     for        goto       if         implements
import     instanceof int       interface  long       native
new        package   private    protected  public     return
short      static    strictfp   super      switch     synchronized
this       throw     throws     transient  try        void
volatile   while
```

`true`, `false`, and `null` are literals, not keywords, but they are also reserved. The underscore `_` is a reserved keyword since Java 9. `var`, `record`, `sealed`, `permits`, and `yield` are restricted or contextual identifiers: they have special meaning in some positions, and you can still use them as names in others.

### Comments
```java
// single-line comment
/* multi-line
   comment */
/**
 * Javadoc comment: documents the class or method for the javadoc tool.
 */
```

Java processes Unicode escapes (`\uXXXX`) before it reads the rest of the source. This has a trap: a comment containing `\u000a` ends the comment early, and `"` inside a string literal acts as a quotation mark.

### Unicode
Java source and `char` values use Unicode. A `char` is a 16-bit UTF-16 code unit, so characters outside the Basic Multilingual Plane (such as many emoji) take two `char` values. Use `String.codePointAt` or `codePoints()` when you need full code points.

```java
String greeting = "été"; // "été"
System.out.println(greeting.length());        // 3
System.out.println(greeting.codePointCount(0, greeting.length())); // 3
```

### Console input with Scanner
`Scanner` reads tokens and lines from a source such as `System.in`.

```java
import java.util.Scanner;

public class Greeter {
    public static void main(String[] args) {
        try (Scanner in = new Scanner(System.in)) {
            System.out.print("Your name: ");
            String name = in.nextLine();
            System.out.print("Your age: ");
            int age = in.nextInt();
            System.out.println(name + " is " + age + " years old");
        }
    }
}
```

`nextInt()` reads the number but leaves the line break in the buffer. A following `nextLine()` then returns an empty string. Call `in.nextLine()` once after `nextInt()` to consume it.

For high-volume input, `BufferedReader` is faster. Use `Integer.parseInt` to convert text, which throws `NumberFormatException` for bad input.

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;

public class EchoLines {
    public static void main(String[] args) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
             PrintWriter writer = new PrintWriter(System.out)) {
            String line;
            while ((line = reader.readLine()) != null) {
                writer.println(line.toUpperCase());
            }
            writer.flush();
        }
    }
}
```

Reader and writer classes are covered in more depth in the file-handling material of the core Java section.

### Methods and scope
A method has a return type, a name, and parameters. Parameters are passed by value: a method receives a copy of the primitive value or of the object reference, never the variable itself.

```java
public class Scopes {
    static int total = 0;               // static field: class-level scope

    static int add(int a, int b) {      // a and b: parameter scope
        int sum = a + b;                // sum: local scope, lives until the method returns
        total += sum;
        return sum;
    }

    public static void main(String[] args) {
        int x = 2;
        add(x, 3);
        System.out.println(total + " " + x); // 5 2: x is unchanged
    }
}
```

A local variable is visible only inside the block where it is declared. Reusing the same name in a sibling block is allowed; reusing it inside a nested block that is still in scope is not.

### Problem solving: pseudocode and tracing
Before coding, write the steps in plain language or pseudocode. Then trace the code by hand with small inputs: write each variable's value after every line. Most logic errors show up in the trace, and the same method works for debugging with a debugger's step-through.

### Date and time basics
Modern date and time code uses `java.time`, not `java.util.Date`. A quick example:

```java
import java.time.LocalDate;

public class DateBasics {
    public static void main(String[] args) {
        LocalDate release = LocalDate.of(2024, 1, 15);
        System.out.println(release.plusDays(30)); // 2024-02-14
    }
}
```

The fuller date and time API is outside this section's scope; the roadmap places it in the core Java and modern Java sections.

### Type casting
Casting converts a value from one type to another. Two kinds exist.

- **Widening (implicit, safe):** `byte` to `short` to `int` to `long` to `float` to `double`. No data is lost in the normal case. `long` to `float` can lose precision for very large values.
- **Narrowing (explicit, may lose data):** you write the target type in parentheses. The value is truncated or wrapped.

```java
int big = 300;
byte small = (byte) big;        // 300 wraps to 44
double d = 3.99;
int truncated = (int) d;        // 3: truncates toward zero, does not round
int code = 'A';                 // char widens to int automatically: 65
char letter = (char) 66;        // 'B'
System.out.println(small + " " + truncated + " " + code + " " + letter);
```

Reference casts work differently: a cast to a subtype is checked at run time and throws `ClassCastException` if the object is not an instance of that type.

## How it works / Step by step

1. Write the class with a `public static void main(String[] args)` method. The file name matches the class name.
2. Run `javac` to produce bytecode, then `java` with the class name.
3. The JVM calls `main`, which runs statements top to bottom.
4. Method calls push a frame on the stack; `return` pops it and passes back a value.
5. Narrowing casts truncate; widening casts happen automatically.

## Common pitfalls
- Naming the file differently from the public class. The compiler reports "class X is public, should be declared in a file named X.java".
- Treating `"Hello"` and `'H'` as the same kind of value. Double quotes are `String`, single quotes are `char`.
- Expecting `(int) 3.99` to round to 4. It truncates to 3.
- Forgetting that `(byte) 200` is `-56`, because `byte` ranges from -128 to 127.
- Calling `nextLine()` straight after `nextInt()` and getting an empty string.
- Assuming `args[0]` exists. Always check `args.length` first.
- Using a keyword such as `class` or `default` as a variable name.

!!! tip "Interview tip"
    **Q: Is Java pass-by-value or pass-by-reference?** Java is always pass-by-value. For objects, the value passed is a copy of the reference, so the method can change the object's fields but cannot make the caller's variable point to a different object. Swapping two object references inside a method does not swap them for the caller.

## Quick recap
- A Java program is a class with a `public static void main(String[] args)` method; the file name matches the public class.
- `javac` compiles to bytecode; `java ClassName` runs it, and `java File.java` runs a single file since Java 11.
- Naming conventions are a convention, not a rule, but keywords and identifier rules are enforced.
- `Scanner.nextInt()` leaves the line break behind; consume it with `nextLine()`.
- Widening casts are automatic; narrowing casts truncate or wrap, so check the value range first.

**See also:** [Data Types and Variables](data-types-variables.md), [Operators and Control Flow](operators-control-flow.md), [Environment Setup](environment-setup.md)
