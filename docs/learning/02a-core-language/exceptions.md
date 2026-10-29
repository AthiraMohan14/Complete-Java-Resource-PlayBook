# Exceptions

An exception is an object that signals an abnormal condition and transfers control to a handler. Java splits throwables into errors (serious JVM problems you normally should not catch) and exceptions (conditions a program can recover from), and further splits exceptions into checked and unchecked. Interviewers ask about this hierarchy, when to catch versus let errors propagate, how try-with-resources closes resources, and how to read a stack trace.

## Core concepts

### The hierarchy
Everything that can be thrown extends `Throwable`.

```text
Throwable
├── Error                 (serious JVM problems, e.g. OutOfMemoryError, StackOverflowError)
└── Exception
    ├── RuntimeException  (unchecked: programming errors, e.g. NullPointerException)
    └── other Exceptions  (checked: e.g. IOException, SQLException)
```

Catching `Throwable` or `Error` is almost never right. Catch the narrowest type that you can actually handle.

### Checked versus unchecked
- **Checked exceptions** (extend `Exception` but not `RuntimeException`) must be caught or declared with `throws`. The compiler enforces this. They signal recoverable conditions such as a missing file.
- **Unchecked exceptions** (extend `RuntimeException`) need no declaration. They usually signal bugs, such as an invalid argument or a null dereference.
- **Errors** are unchecked too, and you rarely handle them.

```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class ReadConfig {
    static String load(Path path) throws IOException {   // checked: declared
        return Files.readString(path);
    }

    static int parsePort(String text) {                   // unchecked: may throw
        return Integer.parseInt(text);                    // NumberFormatException
    }
}
```

### try, catch, and finally
`try` guards code, each `catch` handles one type (or several with `|`), and `finally` runs whether or not an exception was thrown.

```java
public static int parseOrDefault(String text, int fallback) {
    try {
        return Integer.parseInt(text);
    } catch (NumberFormatException e) {
        System.out.println("bad number: " + text);
        return fallback;
    } finally {
        System.out.println("parse attempted");
    }
}
```

Multi-catch handles two or more unrelated types in one block:

```java
public class MultiCatch {
    static void riskyOperation() {
        throw new IllegalStateException("boom");
    }

    static void log(Exception e) {
        System.out.println("failed: " + e.getMessage());
    }

    public static void main(String[] args) {
        try {
            riskyOperation();
        } catch (IllegalArgumentException | IllegalStateException e) {
            log(e);
        }
    }
}
```

A `finally` block can override the return value or swallow an exception if it returns or throws. Keep `finally` for cleanup only.

### try-with-resources
Any object that implements `AutoCloseable` can be declared in the `try` header. The resource is closed automatically, in reverse declaration order, even when an exception occurs.

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;

public class FirstLine {
    static String firstLine(String text) throws IOException {
        try (BufferedReader reader = new BufferedReader(new StringReader(text))) {
            return reader.readLine();
        }   // reader.close() runs here, on success or failure
    }

    public static void main(String[] args) throws IOException {
        System.out.println(firstLine("alpha\nbeta")); // alpha
    }
}
```

If the body throws and `close()` also throws, the close exception is attached to the first as a suppressed exception, which you can read with `getSuppressed()`. This is the main reason to prefer try-with-resources over a manual `finally` with `close()`.

### Multi-catch and catch order
A multi-catch block handles several unrelated exception types with one handler. The alternatives must not be subclasses of each other. Catch clauses are checked from top to bottom, so put the most specific type first. Catching a superclass before its subclass is a compile error.

```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;

class CountReader {

    static int readCount(String path) {
        try {
            return Integer.parseInt(Files.readString(Path.of(path)).trim());
        } catch (NoSuchFileException e) {                   // most specific first: a missing file means zero
            return 0;
        } catch (IOException | NumberFormatException e) {   // multi-catch: unrelated types
            throw new IllegalStateException("cannot read count from " + path, e);
        }
    }
}
```

### throw versus throws
- `throw` raises an exception object: `throw new IllegalArgumentException("quantity must be positive");`
- `throws` declares what a method may raise: `void save() throws IOException`.

### Custom exceptions
Extend `RuntimeException` for programming errors, or `Exception` when callers should be forced to handle the case. Provide constructors that accept a message and a cause.

```java
public class InsufficientFundsException extends Exception {
    private final long shortfallCents;

    public InsufficientFundsException(String message, long shortfallCents) {
        super(message);
        this.shortfallCents = shortfallCents;
    }

    public long shortfallCents() {
        return shortfallCents;
    }
}
```

### Chained exceptions and propagation
When you translate one exception into another, pass the original as the cause so the stack trace keeps the root problem.

```java
static int parseSetting(String raw) {
    try {
        return Integer.parseInt(raw);
    } catch (NumberFormatException e) {
        throw new IllegalArgumentException("invalid setting: " + raw, e);
    }
}
```

An exception that is not caught propagates up the call stack until a handler is found. If none is found, the thread's uncaught exception handler prints it and the thread ends.

### Handling InterruptedException
`Thread.sleep`, `join`, and many blocking calls throw `InterruptedException` when another thread interrupts them. Do not swallow it with an empty catch block. Either let it propagate, or restore the interrupt status so that code further up can see the request to stop:

```java
static void pause(long millis) {
    try {
        Thread.sleep(millis);
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();   // restore the flag for callers
    }
}
```

### Reading stack traces
A stack trace lists the exception type and message, then the frames from the throw point up to the caller. The top line is the most specific frame in your code; the `Caused by:` section shows the chained root cause. Read from the top to find where the exception was created, and from the bottom to find the entry point. Stack traces are captured when the exception is created, so creating exceptions in tight loops is expensive.

## How it works / Step by step

1. `throw` creates or uses an exception object and unwinds the call stack.
2. The JVM checks each frame for a `try` block with a matching `catch`.
3. If a `catch` matches, control jumps to it; `finally` runs before control leaves the `try` statement.
4. Try-with-resources closes each resource in reverse order before the `catch` or `finally` runs.
5. If nothing catches the exception, the thread ends and its handler reports the trace.

## Common pitfalls
- Catching `Exception` or `Throwable` and ignoring it, which hides bugs.
- Logging and rethrowing the same exception at every layer, which produces duplicate log entries.
- Losing the cause by throwing a new exception without passing the original.
- Using exceptions for normal control flow, such as looping until a parse fails.
- Returning from `finally`, which silently discards the exception.
- Using `e.printStackTrace()` in production code instead of a logger.
- Declaring `throws Exception` on a method, which hides what can actually go wrong.
- Creating and catching `NullPointerException` instead of preventing the null in the first place.
- Writing an empty catch block for `InterruptedException`, which loses the interrupt request.
- Throwing a generic `Exception` or `RuntimeException` with no message. Name the failure and include the values involved.

!!! tip "Interview tip"
    **Q: When should you use a checked exception versus an unchecked one?** Use a checked exception when the caller can reasonably recover, such as a missing file the caller can replace. Use an unchecked exception for programming errors or invalid arguments the caller should not handle. Many modern APIs prefer unchecked exceptions because checked ones spread through every signature.

## Quick recap
- Throwables split into errors (JVM problems), checked exceptions (must be handled or declared), and unchecked `RuntimeException`s.
- `finally` is for cleanup; `return` or `throw` inside it can override the outcome.
- Try-with-resources closes `AutoCloseable` resources automatically and records suppressed exceptions.
- Custom exceptions should carry a message and a cause.
- Always pass the original exception as the cause when translating errors.

**See also:** [Wrappers, Strings and Arrays](wrappers-strings-arrays.md), [Enums, Inner Classes and Packages](enums-inner-classes-packages.md), [Generics](generics.md)
