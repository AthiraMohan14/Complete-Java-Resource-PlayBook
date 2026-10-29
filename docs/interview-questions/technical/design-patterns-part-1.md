# Design Patterns Interview Questions (Part 1 of 2)

Factory, Abstract Factory, Builder, Singleton, Strategy, and Observer from the Gang of Four catalogue, with the Java examples interviewers usually expect. Answer each one aloud before you open it, and name a real project situation where you would use the pattern.

This page is split into 2 parts. Continue to [Part 2](design-patterns-part-2.md).

---

## 1. What is the Factory pattern and when should you use it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A factory creates objects without the caller naming the concrete class. The caller asks for a product, usually through an interface, and the factory decides which implementation to return.

### Explanation
A static factory method takes a parameter such as a vehicle kind and returns a `Vehicle`. The caller only uses `describe()`, so new vehicle types can be added without changing the calling code. The common reasons to use it are:

- The concrete type depends on runtime input, such as a configuration value or a user choice.
- You want to hide construction details, for example when the object needs several steps or a connection.
- You expect new product types to appear and do not want every caller to change.

```java
interface Vehicle {
    String describe();
}

class Car implements Vehicle {
    @Override
    public String describe() {
        return "Four-wheel car";
    }
}

class Motorbike implements Vehicle {
    @Override
    public String describe() {
        return "Two-wheel motorbike";
    }
}

class VehicleFactory {

    static Vehicle create(String kind) {
        if (kind == null) {
            throw new IllegalArgumentException("Kind is required");
        }
        return switch (kind.toLowerCase()) {
            case "car" -> new Car();
            case "motorbike" -> new Motorbike();
            default -> throw new IllegalArgumentException("Unknown kind: " + kind);
        };
    }
}
```

### When to use / pitfalls
- A factory centralises creation, but the switch grows with each new type. Consider a map from name to supplier, or a factory method in each subclass, as the count grows.
- A simple factory is not a GoF pattern. Mention this if the interviewer is strict about terms.
- Do not add a factory when there is only one implementation and no sign of a second.

**See also:** [Creational Patterns](../../learning/design-patterns/creational-patterns.md)

</details>

---

## 2. What is the difference between Factory and Abstract Factory?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A factory method creates one kind of product. An abstract factory creates a family of related products that must be used together, and it returns each product through its own interface.

### Explanation
Imagine a UI theme with labels and text fields. A dark theme must use dark labels and dark text fields. An abstract factory with `createLabel()` and `createTextField()` keeps the two families consistent, because the client picks one factory and gets matching products from it.

```java
interface Label {
    String render();
}

interface TextField {
    String render();
}

interface ThemeFactory {
    Label createLabel();
    TextField createTextField();
}

class DarkLabel implements Label {
    @Override
    public String render() {
        return "[dark label]";
    }
}

class DarkTextField implements TextField {
    @Override
    public String render() {
        return "[dark field]";
    }
}

class DarkThemeFactory implements ThemeFactory {
    @Override
    public Label createLabel() {
        return new DarkLabel();
    }

    @Override
    public TextField createTextField() {
        return new DarkTextField();
    }
}
```

### When to use / pitfalls
- Factory: one product type, one interface, low complexity.
- Abstract factory: several product types that must match, such as a theme or a platform.
- The cost of an abstract factory is that adding a new product type (for example, a menu) changes every factory.

**See also:** [Creational Patterns](../../learning/design-patterns/creational-patterns.md)

</details>

---

## 3. Explain the Builder pattern with a real example.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The Builder pattern constructs an object step by step through a separate builder object, and the final `build()` call returns the finished object. It is used when a class has many optional parameters or needs validation before it exists.

### Explanation
Without a builder, an email class needs a constructor for every combination of optional values, or the caller passes many nulls. A builder gives named, chainable setters. The target class has a private constructor, and the builder is the only way to create it. Fields can then be `final`, which makes the object immutable.

```java
public final class EmailMessage {

    private final String to;
    private final String subject;
    private final boolean highPriority;

    private EmailMessage(Builder builder) {
        this.to = builder.to;
        this.subject = builder.subject;
        this.highPriority = builder.highPriority;
    }

    public static final class Builder {

        private final String to;
        private String subject = "(no subject)";
        private boolean highPriority = false;

        public Builder(String to) {
            this.to = to;
        }

        public Builder subject(String subject) {
            this.subject = subject;
            return this;
        }

        public Builder highPriority(boolean highPriority) {
            this.highPriority = highPriority;
            return this;
        }

        public EmailMessage build() {
            if (to == null || to.isBlank()) {
                throw new IllegalStateException("Recipient is required");
            }
            return new EmailMessage(this);
        }
    }
}

// Usage
class EmailDemo {
    public static void main(String[] args) {
        EmailMessage message = new EmailMessage.Builder("ops@example.com")
                .subject("Nightly job finished")
                .highPriority(true)
                .build();
    }
}
```

### When to use / pitfalls
- Use it for objects with several optional fields, immutable objects, and objects that need cross-field validation.
- Validate in `build()`, once, when all values are known.
- Records are a simpler choice when there are few fields and no validation rules.

**See also:** [Creational Patterns](../../learning/design-patterns/creational-patterns.md)

</details>

---

## 4. What is the Singleton pattern and when is it problematic?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A singleton restricts a class to one instance and gives code a global way to reach it. It is problematic because it hides dependencies, is hard to replace in tests, and is not shared across separate JVM instances.

### Explanation
A thread-safe lazy singleton can use the holder idiom. The JVM initializes the nested class only when `getInstance()` first runs, and class initialization is thread-safe. An enum singleton is an even shorter option and also resists serialization and reflection tricks.

```java
public final class MetricsRegistry {

    private MetricsRegistry() {
    }

    private static final class Holder {
        static final MetricsRegistry INSTANCE = new MetricsRegistry();
    }

    public static MetricsRegistry getInstance() {
        return Holder.INSTANCE;
    }

    public void record(String name) {
        System.out.println("metric: " + name);
    }
}
```

The problems appear in larger designs:

- **Hidden dependencies.** A class that calls `getInstance()` does not show what it needs in its constructor.
- **Testing.** A test cannot substitute a fake without changing the singleton.
- **Scaling.** Each service instance has its own singleton. A "one instance" rule holds per JVM, not across a cluster.

A better design uses dependency injection. The container creates one bean and injects it wherever it is needed, so the dependency is visible and replaceable.

```java
import org.springframework.stereotype.Service;

class MetricsRegistry {
}

@Service
public class ReportService {

    private final MetricsRegistry metrics;

    public ReportService(MetricsRegistry metrics) {
        this.metrics = metrics;
    }
}
```

### When to use / pitfalls
- Reasonable: loggers, thread pools, connection pools, and configuration holders that are truly one per process.
- Avoid: service objects that hold business logic. Inject them instead.
- With Spring, a bean is singleton-scoped by default, which gives you one instance per container without a hand-written singleton.

**See also:** [Creational Patterns](../../learning/design-patterns/creational-patterns.md), [Dependency Injection](../../learning/08-spring-core/dependency-injection.md)

</details>

---

## 5. Explain the Strategy pattern and give a use case.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The Strategy pattern puts each algorithm behind a common interface so the algorithm can be chosen and swapped at runtime. The context object calls the interface and does not know which strategy it has.

### Explanation
A parcel needs a shipping price. Each shipping option implements `ShippingStrategy`. The parcel holds a reference to whichever option the customer chose, and changing the option does not change the parcel. In modern Java, a strategy with one method is often a lambda.

```java
interface ShippingStrategy {
    double cost(double weightKg);
}

class StandardShipping implements ShippingStrategy {
    @Override
    public double cost(double weightKg) {
        return 4.0 + 0.5 * weightKg;
    }
}

class ExpressShipping implements ShippingStrategy {
    @Override
    public double cost(double weightKg) {
        return 12.0 + 1.5 * weightKg;
    }
}

class Parcel {

    private final double weightKg;
    private ShippingStrategy strategy;

    Parcel(double weightKg, ShippingStrategy strategy) {
        this.weightKg = weightKg;
        this.strategy = strategy;
    }

    void setStrategy(ShippingStrategy strategy) {
        this.strategy = strategy;
    }

    double shippingCost() {
        return strategy.cost(weightKg);
    }
}

// Usage
class ShippingDemo {
    public static void main(String[] args) {
        Parcel parcel = new Parcel(2.0, new StandardShipping());
        System.out.println(parcel.shippingCost()); // 5.0
        parcel.setStrategy(new ExpressShipping());
        System.out.println(parcel.shippingCost()); // 15.0
    }
}
```

Other examples in the JDK: `Comparator` passed to `List.sort`, and the compression or formatter choice in many libraries.

### When to use / pitfalls
- Use it when the same operation has several variants chosen by configuration or by the user.
- It removes if/else chains that select behaviour, which keeps the open/closed principle.
- Do not use it for a single fixed algorithm. An interface with one implementation adds indirection without benefit.

**See also:** [Behavioural Patterns](../../learning/design-patterns/behavioural-patterns.md)

</details>

---

## 6. What is the Observer pattern and when would you use it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
The Observer pattern lets one subject notify many listeners when its state changes. The subject knows only the listener interface, so listeners can be added or removed without changing the subject.

### Explanation
A stock service that receives new inventory needs to tell other parts of the system. Each interested part registers a listener. The stock service calls each one after the count is saved. The subject does not care what the listeners do.

```java
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

interface StockListener {
    void onRestocked(String sku);
}

class StockService {

    private final List<StockListener> listeners = new CopyOnWriteArrayList<>();

    void subscribe(StockListener listener) {
        listeners.add(listener);
    }

    void restock(String sku) {
        System.out.println("Restocked " + sku);
        for (StockListener listener : listeners) {
            listener.onRestocked(sku);
        }
    }
}

// Usage
class StockDemo {
    public static void main(String[] args) {
        StockService stock = new StockService();
        stock.subscribe(sku -> System.out.println("Notify waiting customers for " + sku));
        stock.subscribe(sku -> System.out.println("Update storefront for " + sku));
        stock.restock("SKU-100");
    }
}
```

The JDK's `java.util.Observable` and `Observer` types were deprecated in Java 9. Do not use them in new code. Write a small listener interface, or use `PropertyChangeSupport` from `java.beans` for bean-style properties.

### Observer vs Pub/Sub

| Aspect | Observer | Pub/Sub |
|--------|----------|---------|
| Coupling | Subject holds listener references | Publishers and subscribers share a broker or topic |
| Delivery | Direct call, in the same process | Through a broker, often across processes |
| Failure handling | An exception from a listener can stop the loop | The broker can retry, persist, and isolate consumers |
| Examples | UI listeners, in-process events | Kafka, RabbitMQ, SNS/SQS |

### When to use / pitfalls
- Use Observer for in-process notifications where the listeners are known and fast.
- Use pub/sub when listeners run in other services, need retries, or must not slow the publisher.
- A slow listener slows every listener after it. Run slow work asynchronously.

**See also:** [Behavioural Patterns](../../learning/design-patterns/behavioural-patterns.md), [Messaging](../../learning/13-messaging/index.md)

</details>
