# Design Patterns Interview Questions (Part 2 of 2)

Decorator, Strategy versus State, Proxy, Template Method, patterns in the JDK, and how Observer compares with publish/subscribe. Start with [Part 1](design-patterns-part-1.md) if you have not read it.

---

## 7. Explain the Decorator pattern with an example.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A decorator wraps an object that implements an interface, adds behaviour before or after delegating, and implements the same interface. Decorators can be stacked at runtime in any order.

### Explanation
A tea stall sells a base tea and optional extras. Each extra is a decorator that adds to the price and the description. The price is computed by asking the outer object, which asks the one inside it, and so on.

```java
interface Tea {
    double cost();
    String description();
}

class PlainTea implements Tea {
    @Override
    public double cost() {
        return 1.20;
    }

    @Override
    public String description() {
        return "Tea";
    }
}

abstract class TeaDecorator implements Tea {

    protected final Tea inner;

    TeaDecorator(Tea inner) {
        this.inner = inner;
    }
}

class LemonDecorator extends TeaDecorator {

    LemonDecorator(Tea inner) {
        super(inner);
    }

    @Override
    public double cost() {
        return inner.cost() + 0.30;
    }

    @Override
    public String description() {
        return inner.description() + ", lemon";
    }
}

// Usage
class TeaDemo {
    public static void main(String[] args) {
        Tea tea = new LemonDecorator(new PlainTea());
        System.out.println(tea.description() + " costs " + tea.cost()); // Tea, lemon costs 1.5
    }
}
```

Java's I/O classes use this design. `new BufferedInputStream(new FileInputStream(path))` adds buffering to a file stream, and both classes are `InputStream`s.

### When to use / pitfalls
- Use it to add optional behaviour that can combine in many ways, without a subclass for each combination.
- Decorators produce many small objects, and long chains are hard to debug.
- The order of decorators can change the result, for example when one wraps and the other filters.

**See also:** [Structural Patterns](../../learning/design-patterns/structural-patterns.md)

</details>

---

## 8. What is the difference between Strategy and State?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Both use an interface and delegation, but they differ in who changes the behaviour. In Strategy, the client chooses an algorithm and usually keeps it. In State, the object moves between states by itself, and each state decides the next one.

### Explanation
A sort routine that takes a `Comparator` is a strategy: the caller picks the ordering, and the sort does not change it. An order that moves from `PLACED` to `SHIPPED` to `DELIVERED` is a state machine: each state handles the events it cares about and sets the next state.

```java
enum OrderState {

    PLACED {
        @Override
        OrderState next() {
            return SHIPPED;
        }
    },
    SHIPPED {
        @Override
        OrderState next() {
            return DELIVERED;
        }
    },
    DELIVERED {
        @Override
        OrderState next() {
            return this; // Terminal state
        }
    };

    abstract OrderState next();
}
```

### When to use / pitfalls
- Strategy: choose behaviour from outside, for example a discount rule or a sort order.
- State: the object's behaviour depends on its current mode, and the mode changes over time.
- Both can have identical class diagrams. Ask who triggers the change to tell them apart.

**See also:** [Behavioural Patterns](../../learning/design-patterns/behavioural-patterns.md)

</details>

---

## 9. What is the difference between a Proxy and a Decorator?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Both wrap an object behind the same interface. A decorator adds behaviour the caller chooses, and often stacks several wrappers. A proxy controls access to a real object, for example by delaying its creation, checking permissions, or forwarding to a remote system.

### Explanation
A decorator is usually built by the code that wants the extra behaviour, and the client knows about the wrapping. A proxy is often created by a framework or by the object's owner, and the client may not know a proxy is in front of the real object. Spring's `@Transactional` and JDK dynamic proxies are proxies. Java's I/O wrappers are decorators.

```java
import java.lang.reflect.Proxy;

interface Repository {
    String find(long id);
}

class RealRepository implements Repository {
    @Override
    public String find(long id) {
        return "row-" + id;
    }
}

public class ProxyDemo {

    public static void main(String[] args) {
        Repository real = new RealRepository();

        // A protection proxy that rejects negative ids before reaching the real object
        Repository guarded = (Repository) Proxy.newProxyInstance(
                Repository.class.getClassLoader(),
                new Class<?>[] {Repository.class},
                (proxy, method, methodArgs) -> {
                    long id = (Long) methodArgs[0];
                    if (id < 0) {
                        throw new IllegalArgumentException("Negative id");
                    }
                    return method.invoke(real, methodArgs);
                });

        System.out.println(guarded.find(3L)); // row-3
    }
}
```

### When to use / pitfalls
- Decorator: add optional features, such as buffering, logging, or formatting, that the caller composes.
- Proxy: control access or lifecycle, such as lazy loading, security, caching, or remote calls.
- Proxies created by Spring skip self-invoked methods. Keep that in mind when a call seems to ignore an annotation.

**See also:** [Structural Patterns](../../learning/design-patterns/structural-patterns.md), [AOP](../../learning/08-spring-core/aop.md)

</details>

---

## 10. What is the Template Method pattern, and how does it differ from Strategy?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Template Method fixes the order of an algorithm in a base class and lets subclasses supply some steps. Strategy puts the whole varying part behind an object that is passed in. Template Method uses inheritance; Strategy uses composition.

### Explanation
A report generator always writes a header, a body, and a footer. The base class makes `generate()` final, so the order cannot change, and subclasses implement `body()`. With Strategy, the body would be an injected object instead of an overridden method.

```java
abstract class ReportGenerator {

    public final String generate() {
        return header() + body() + footer();
    }

    protected String header() {
        return "== Report ==\n";
    }

    protected abstract String body();

    protected String footer() {
        return "== End ==\n";
    }
}

class SalesReport extends ReportGenerator {
    @Override
    protected String body() {
        return "Sales: 120 units\n";
    }
}
```

### When to use / pitfalls
- Template Method: the steps are fixed and only a few vary, and the variants belong to one family of classes.
- Strategy: the algorithm varies independently of the class that uses it, and you may want to combine it with other strategies.
- Template Method can lead to deep inheritance. Prefer composition when the number of variants grows.

**See also:** [Behavioural Patterns](../../learning/design-patterns/behavioural-patterns.md)

</details>

---

## 11. Which design patterns does the JDK itself use?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Several patterns appear in the standard library. Common examples are Iterator (collections), Decorator (I/O readers), Adapter (`InputStreamReader`), Factory (`List.of`, `Calendar.getInstance`), and Proxy (dynamic proxies). Naming real examples shows that you have read the library, not only memorised the patterns.

### Explanation
- **Iterator:** `Iterable.iterator()` and the enhanced `for` loop.
- **Decorator:** `BufferedReader` wraps any `Reader`, adding buffering and `readLine()`.
- **Adapter:** `InputStreamReader` turns an `InputStream` of bytes into a `Reader` of characters.
- **Factory:** `List.of(...)` returns an implementation the caller does not name, and `Calendar.getInstance()` picks a calendar for the current locale.
- **Proxy:** `java.lang.reflect.Proxy` creates proxies from interfaces at runtime.

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class JdkPatterns {

    public static void main(String[] args) throws IOException {
        // Adapter (InputStreamReader) inside a Decorator (BufferedReader)
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
            System.out.println("Read: " + reader.readLine());
        }
    }
}
```

### When to use / pitfalls
- Knowing the JDK examples helps you explain a pattern with a familiar case.
- Do not claim that a JDK class is a pure textbook pattern. Describe what it does and which pattern shape it resembles.

**See also:** [Structural Patterns](../../learning/design-patterns/structural-patterns.md), [Behavioural Patterns](../../learning/design-patterns/behavioural-patterns.md)

</details>

---

## 12. How does Observer differ from publish/subscribe?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Observer is usually direct: the subject keeps references to its listeners and calls them. Publish/subscribe adds a broker between publishers and subscribers, so the two sides do not know each other and do not even run in the same process.

### Explanation
Publish/subscribe is usually described as an architectural style, while Observer is a class-level design pattern. The broker adds durability, retries, and fan-out across services, and it adds latency and operational cost. For a small in-process event bus, Observer is the simpler tool.

### When to use / pitfalls
- Observer: in-process events, UI updates, and domain events that must finish in the same request.
- Pub/sub: integration between services, workloads that can be retried, and consumers that scale separately.
- With pub/sub, a message can be delivered more than once or out of order, so consumers should be idempotent.

**See also:** [Behavioural Patterns](../../learning/design-patterns/behavioural-patterns.md), [Messaging](../../learning/13-messaging/index.md)

</details>

---

## Quick recap

- Decorator wraps an object to add behaviour, and the wrappers can be stacked.
- Strategy is chosen by the client; State changes itself as the object moves between modes.
- Proxy controls access to a real object; Decorator adds optional features the caller composes.
- Template Method fixes the algorithm's order in a base class; Strategy swaps an injected object.
- The JDK is full of examples: iterators, wrapping readers, dynamic proxies, and factory methods.
- Observer notifies in-process listeners; pub/sub routes messages through a broker across services.

**See also:** [SOLID and Anti-Patterns](../../learning/design-patterns/solid-and-anti-patterns.md), [Creational Patterns](../../learning/design-patterns/creational-patterns.md), [Design Patterns Part 1](design-patterns-part-1.md)
