# Creational Design Patterns

Creational patterns control how objects get created. Interviewers ask about them to see whether you can separate "who needs the object" from "how the object is built", and whether you know the cost of each choice.

## Core concepts

### Singleton

A singleton guarantees one instance of a class in a JVM and gives code a single way to reach it. Use it for things that really are one-per-application, such as a configuration holder or a registry of metrics.

The simplest lazy version is not safe under concurrency. Two threads can both see `null` and both create an instance. Two thread-safe options are common.

```java
// Option 1: initialization-on-demand holder (lazy and thread-safe)
public final class ConfigHolder {

    private ConfigHolder() {
    }

    private static final class Holder {
        static final ConfigHolder INSTANCE = new ConfigHolder();
    }

    public static ConfigHolder getInstance() {
        return Holder.INSTANCE;
    }
}

// Option 2: enum (serialization-safe and reflection-resistant)
public enum AppMode {
    INSTANCE;

    public String describe() {
        return "running in " + name();
    }
}
```

Double-checked locking also works, but only with a `volatile` field. Without `volatile`, another thread can see a partially constructed object.

```java
public final class Registry {

    private static volatile Registry instance;

    private Registry() {
    }

    public static Registry getInstance() {
        Registry local = instance;
        if (local == null) {
            synchronized (Registry.class) {
                local = instance;
                if (local == null) {
                    instance = local = new Registry();
                }
            }
        }
        return local;
    }
}
```

### Factory Method

A factory method is a method that creates an object, and subclasses decide which concrete type to return. The caller works against an interface and never names the concrete class.

```java
interface LogSink {
    void write(String line);
}

class ConsoleSink implements LogSink {
    @Override
    public void write(String line) {
        System.out.println(line);
    }
}

class JsonConsoleSink implements LogSink {
    @Override
    public void write(String line) {
        System.out.println("{\"msg\": \"" + line + "\"}");
    }
}

abstract class SinkCreator {

    // The factory method. Subclasses choose the product.
    abstract LogSink createSink();

    void log(String line) {
        createSink().write(line);
    }
}

class JsonSinkCreator extends SinkCreator {
    @Override
    LogSink createSink() {
        return new JsonConsoleSink();
    }
}
```

A static method that switches on a string is sometimes called a "simple factory". It is not a GoF pattern, but it is common and often enough. It becomes a problem when every new type means editing the same `switch`, which breaks the open/closed principle.

### Abstract Factory

An abstract factory creates a family of related objects that must be used together. The client picks one factory and gets consistent products from it. A database dialect is a typical case: a PostgreSQL factory must return PostgreSQL-style ID generators and query builders, never a mix of dialects.

```java
interface IdGenerator {
    String nextId();
}

interface QueryBuilder {
    String selectAll(String table);
}

interface DialectFactory {
    IdGenerator createIdGenerator();
    QueryBuilder createQueryBuilder();
}

class PostgresIdGenerator implements IdGenerator {
    @Override
    public String nextId() {
        return "SELECT nextval('ids')";
    }
}

class PostgresQueryBuilder implements QueryBuilder {
    @Override
    public String selectAll(String table) {
        return "SELECT * FROM \"" + table + "\"";  // Postgres quotes identifiers with double quotes
    }
}

class PostgresDialectFactory implements DialectFactory {
    @Override
    public IdGenerator createIdGenerator() {
        return new PostgresIdGenerator();
    }

    @Override
    public QueryBuilder createQueryBuilder() {
        return new PostgresQueryBuilder();
    }
}
```

A MySQL factory would be built the same way, quoting identifiers with backticks instead. Adding a new product type (for example, a menu) forces a change to every factory. That is the trade-off: easy to add a family, harder to add a new kind of member.

### Prototype

A prototype creates new objects by copying an existing one. It helps when building an object from scratch is expensive, or when the caller only has an existing object and wants a similar one.

In Java, `Object.clone()` and `Cloneable` are error-prone. `clone()` makes a shallow copy by default, and the checked `CloneNotSupportedException` is awkward. A copy constructor or a static `copy()` method is usually clearer.

```java
import java.util.ArrayList;
import java.util.List;

class Template {

    private final String title;
    private final List<String> sections;

    Template(String title, List<String> sections) {
        this.title = title;
        // Copy the list so the new object does not share state with the original
        this.sections = new ArrayList<>(sections);
    }

    Template copy() {
        return new Template(title, sections);
    }

    void addSection(String section) {
        sections.add(section);
    }

    @Override
    public String toString() {
        return title + " " + sections;
    }

    public static void main(String[] args) {
        Template original = new Template("Weekly", List.of("Goals"));
        Template copy = original.copy();
        copy.addSection("Risks");
        System.out.println(original); // Weekly [Goals]
        System.out.println(copy);     // Weekly [Goals, Risks]
    }
}
```

### Builder

A builder collects the parts of an object step by step and creates the final object in one call, usually `build()`. It fixes the "telescoping constructor" problem, where a class has five constructors with overlapping parameter lists and callers cannot tell which `int` is which.

Builders are a good fit for classes with several optional settings, for immutable objects, and for objects that need validation before they exist.

```java
public final class ServerConfig {

    private final String host;
    private final int port;
    private final boolean tls;

    private ServerConfig(Builder builder) {
        this.host = builder.host;
        this.port = builder.port;
        this.tls = builder.tls;
    }

    public static Builder builder(String host) {
        return new Builder(host);
    }

    public static final class Builder {

        private final String host;
        private int port = 8080;
        private boolean tls = false;

        private Builder(String host) {
            this.host = host;
        }

        public Builder port(int port) {
            this.port = port;
            return this;
        }

        public Builder tls(boolean tls) {
            this.tls = tls;
            return this;
        }

        public ServerConfig build() {
            if (port <= 0 || port > 65535) {
                throw new IllegalStateException("Port out of range: " + port);
            }
            return new ServerConfig(this);
        }
    }

    @Override
    public String toString() {
        return (tls ? "https" : "http") + "://" + host + ":" + port;
    }

    public static void main(String[] args) {
        ServerConfig config = ServerConfig.builder("localhost").port(8443).tls(true).build();
        System.out.println(config); // https://localhost:8443
    }
}
```

Java records cover many data-only cases with less code. A builder is still useful when there are optional fields, validation rules, or a need for defaults.

Lombok's `@Builder` generates this boilerplate. Its generated code follows the same pattern, so knowing the hand-written version helps when you debug generated code.

## How it works / Step by step

| Step | Singleton | Factory Method | Abstract Factory | Prototype | Builder |
|------|-----------|----------------|------------------|-----------|---------|
| 1 | Make the constructor private | Declare a creator with a factory method | Declare an interface for each product | Declare a copy operation | Declare the product and its optional fields |
| 2 | Expose one static access point | Subclasses override the method | Implement a factory per family | Implement the copy | Add setter-like methods that return the builder |
| 3 | Create the instance once | Client calls the creator | Client picks one factory | Client copies instead of constructing | Client calls `build()` |

## Common pitfalls

- **Singleton as a global variable.** A singleton hides dependencies, so tests cannot swap it out. In Spring, prefer a bean that the container manages, since beans are singleton-scoped by default and can be injected.
- **Serialization breaks a naive singleton.** Deserialization can create a second instance unless you implement `readResolve()`. An enum avoids this.
- **Shallow copies in prototypes.** A copy that shares a mutable list with the original causes bugs that appear only after one object is changed.
- **Builders that accept invalid state.** Validate in `build()`, not in each setter, so the object is checked once with all values known.
- **Abstract factories for one product.** If you only ever create one kind of object, a plain factory method is enough.

!!! tip "Interview tip"
    Interviewers often ask, "How would you make a singleton thread-safe?" Name the holder idiom or the enum, explain why a `volatile` field is needed for double-checked locking, and then say that dependency injection is usually a better answer in an application.

## Quick recap

- Singleton: one instance, made safe with a holder class or an enum.
- Factory Method: subclasses decide the concrete product; the caller depends on the interface.
- Abstract Factory: creates families of products that must match.
- Prototype: copy an existing object; prefer copy constructors to `Cloneable`.
- Builder: readable construction of objects with optional fields and validation.

**See also:** [Structural Patterns](structural-patterns.md), [Behavioural Patterns](behavioural-patterns.md), [SOLID and Anti-Patterns](solid-and-anti-patterns.md), [Dependency Injection](../08-spring-core/dependency-injection.md), [Design Patterns interview questions](../../interview-questions/technical/design-patterns-part-1.md)
