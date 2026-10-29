# SOLID Principles and Anti-Patterns

SOLID is a set of five object-oriented design principles that explain why good pattern use looks the way it does. Anti-patterns are the common shortcuts that look helpful at first and cause trouble later. Interviewers ask about both to test judgement, not memory.

## Core concepts

### Single Responsibility Principle (SRP)

A class should have one reason to change. If a class formats a report, saves it to the database, and sends it by email, a change to the email rules forces you to edit a class that also owns the report format.

```java
// Before: one class with three reasons to change
class InvoiceManager {
    void save(Invoice invoice) { /* database code */ }
    String format(Invoice invoice) { return "Invoice " + invoice.id(); }
    void email(Invoice invoice) { /* mail code */ }
}

// After: each responsibility has its own class
record Invoice(String id) { }

class InvoiceRepository {
    void save(Invoice invoice) { System.out.println("saved " + invoice.id()); }
}

class InvoiceFormatter {
    String format(Invoice invoice) { return "Invoice " + invoice.id(); }
}
```

SRP is about reasons to change, not about making classes tiny. A class with one clear job can still have many methods.

### Open/Closed Principle (OCP)

Software entities should be open for extension and closed for modification. You add behaviour by adding new code, not by editing tested code. The Strategy pattern is the usual way to get this.

```java
interface TaxRule {
    double tax(double amount);
}

class StandardTax implements TaxRule {
    @Override
    public double tax(double amount) {
        return amount * 0.2;
    }
}

// A new rule is a new class. Checkout does not change.
class ReducedTax implements TaxRule {
    @Override
    public double tax(double amount) {
        return amount * 0.05;
    }
}
```

A `switch` on a type code is the classic sign that OCP is being broken. Each new case edits existing code.

### Liskov Substitution Principle (LSP)

A subtype must be usable anywhere its parent type is used, without the caller noticing a broken promise. The classic failure is a `Square` that extends `Rectangle` and enforces equal sides. Code that sets width and height independently now gets surprising results.

```java
class Rectangle {
    protected int width;
    protected int height;

    void setWidth(int width) { this.width = width; }
    void setHeight(int height) { this.height = height; }
    int area() { return width * height; }
}

// Violates LSP: setting one side silently changes the other
class Square extends Rectangle {
    @Override
    void setWidth(int width) { this.width = width; this.height = width; }

    @Override
    void setHeight(int height) { this.width = height; this.height = height; }
}
```

The fix is to avoid the inheritance. Model shapes with a common interface, such as `area()`, and let each shape hold its own fields.

LSP also covers stronger preconditions and weaker postconditions in subclasses. If a subclass throws for inputs the parent accepts, it breaks substitution.

### Interface Segregation Principle (ISP)

Clients should not be forced to depend on methods they do not use. A large interface with many unrelated methods forces every implementation to stub out methods it cannot support.

```java
// Too broad: a read-only client must still see write methods
interface Store {
    String read(String key);
    void write(String key, String value);
    void delete(String key);
}

// Split by what callers need
interface ReadableStore {
    String read(String key);
}

interface WritableStore {
    void write(String key, String value);
    void delete(String key);
}
```

### Dependency Inversion Principle (DIP)

High-level code should depend on abstractions, and low-level details should depend on the same abstractions. In practice, a service asks for a `PaymentGateway` interface in its constructor, and the wiring code decides which implementation to pass in. Dependency injection is the mechanism that does this for you.

```java
interface PaymentGateway {
    boolean charge(double amount);
}

class OrderService {

    private final PaymentGateway gateway;

    // The service does not create the gateway. It receives one.
    OrderService(PaymentGateway gateway) {
        this.gateway = gateway;
    }

    boolean placeOrder(double amount) {
        return gateway.charge(amount);
    }
}

// In a test: new OrderService(amount -> true)
```

Constructor injection makes the dependency visible and easy to replace in tests. Spring's container does the wiring for you; see [Dependency Injection](../08-spring-core/dependency-injection.md).

### Design habits: immutability and equals/hashCode

Two habits support most of the patterns above. Immutable objects can be shared safely between threads, which is why Builder, Flyweight, and value classes benefit from them. Make fields `final`, do not expose mutable collections, and return copies.

`equals` and `hashCode` must agree. If two objects are equal, they must return the same hash code. A class used as a key in a `HashMap` that breaks this rule can appear to lose entries. Records generate both methods from their components, which is the safest default for value types.

## How it works / Step by step

To apply SOLID to a design review, walk through the code in this order:

1. Name each class's responsibility in one sentence. If you need "and", consider SRP.
2. Find places where a type check or switch decides behaviour. Consider OCP and a strategy or polymorphism.
3. Check each subclass against its parent with a sample call. Consider LSP.
4. Look at each interface. If some implementations throw "not supported", consider ISP.
5. Find `new` calls for collaborators inside business classes. Consider DIP and constructor injection.

## Anti-patterns

| Anti-pattern | What it looks like | Better option |
|--------------|-------------------|---------------|
| God object | One class that knows and does almost everything | Split by responsibility (SRP) |
| Singleton overuse | Global static access everywhere | Dependency injection with a singleton-scoped bean |
| Anemic domain model | Entities are plain data holders; all logic is in service classes | Move behaviour that belongs to the entity into it |
| Service locator | A global lookup that code calls to find its own dependencies | Constructor injection |
| Premature abstraction | Interfaces and factories for a single implementation with no planned variation | Write the concrete class; extract an interface when a second case appears |
| Pattern for its own sake | A pattern added because it has a name | Describe the problem first, then choose the pattern |
| Shotgun surgery | One change touches many classes | Group code that changes together |

Each anti-pattern has a legitimate use in some case. The Singleton is useful for a thread pool, and an interface with one implementation is fine at a module boundary. The problem is using them by default.

## Common pitfalls

- **Treating SOLID as rules to memorise.** Each principle is a guide to reasons for change. Applying all five to a 40-line script makes the code harder to read.
- **Creating an interface for every class.** A small interface is a cost. Add it when there is a real second implementation, a test seam, or a module boundary.
- **Using inheritance for code reuse only.** If the subclass is not a true kind of the parent, prefer composition.
- **Confusing DIP with DI.** DIP is the design rule (depend on abstractions). Dependency injection is one way to follow it.
- **Ignoring the anemic model trap.** Services that only call getters and setters on entities are often a sign that logic has leaked out of the domain.

!!! tip "Interview tip"
    "Which SOLID principle is most often broken in practice?" A good answer is SRP, because classes grow by accretion. Then explain how you would notice it: a class that changes for several unrelated reasons, or a diff where one feature touches many unrelated methods.

## Quick recap

- SRP: one reason to change per class.
- OCP: add behaviour with new code, not by editing working code.
- LSP: subtypes must keep the promises of their parent types.
- ISP: keep interfaces small and focused on what clients use.
- DIP: depend on abstractions, and inject the concrete implementation.
- Immutability and consistent `equals`/`hashCode` make objects safer to share and to use as keys.
- Anti-patterns to watch for: god objects, overused singletons, anemic models, service locators, and premature abstraction.

**See also:** [Creational Patterns](creational-patterns.md), [Structural Patterns](structural-patterns.md), [Behavioural Patterns](behavioural-patterns.md), [Dependency Injection](../08-spring-core/dependency-injection.md), [Design Patterns interview questions](../../interview-questions/technical/design-patterns-part-1.md)
