# Low-Level Design

Low-level design (LLD) turns a component from the high-level diagram into classes, interfaces, and method signatures. Interviewers use it to test object-oriented thinking: whether you separate responsibilities, choose the right abstraction, apply patterns only where they pay off, and handle errors without leaking chaos into the rest of the system.

## Core concepts

### Object-oriented design
Start from the nouns and verbs in the requirements. Nouns become classes, and their behaviour becomes methods. Good designs have:

- **Clear responsibilities**: each class has one reason to change.
- **Encapsulated state**: fields are private, and changes go through methods that protect invariants.
- **Interfaces at the seams**: code depends on abstractions where behaviour may vary.
- **Composition over inheritance**: combine objects instead of building deep hierarchies, which tie classes together.

```java
import java.math.BigDecimal;

public class Order {
    private final String id;
    private final BigDecimal total;

    public Order(String id, BigDecimal total) {
        if (total.signum() < 0) {
            throw new IllegalArgumentException("total must not be negative");
        }
        this.id = id;
        this.total = total;
    }

    public String id() { return id; }
    public BigDecimal total() { return total; }
}
```

The constructor protects the invariant, so no `Order` can exist with a negative total. Immutable fields make the object safe to share between threads.

### Class hierarchies and API design
Use inheritance for a real "is-a" relationship with shared behaviour and a stable contract. Sealed types (Java 17) or records (Java 16) can model a closed set of variants:

```java
public sealed interface PaymentResult permits Approved, Declined {}

record Approved(String authCode) implements PaymentResult {}
record Declined(String reason) implements PaymentResult {}
```

For API design, make methods narrow and named after intent (`reserve(seat)` rather than `update(state)`), return values rather than mutating arguments, and document preconditions. Public APIs deserve the same care as HTTP APIs: stable names, clear error types, and no leaking of internal types.

### Design patterns
Patterns are shared solutions to recurring problems. Use them when they remove real duplication or a real variation point, not to decorate code.

**Singleton** ensures one instance. In Java, an enum is the simplest safe form, and it also protects against reflection and serialisation tricks:

```java
public enum AppClock {
    INSTANCE;

    public long nowMillis() {
        return System.currentTimeMillis();
    }
}
```

Be cautious: a singleton is a global, which makes testing harder. Inject dependencies where you can.

**Factory** centralises object creation so callers do not depend on concrete classes:

```java
interface Notifier {
    void send(String message);
}

class EmailNotifier implements Notifier {
    public void send(String message) {
        System.out.println("email: " + message);
    }
}

class SmsNotifier implements Notifier {
    public void send(String message) {
        System.out.println("sms: " + message);
    }
}

class NotifierFactory {
    static Notifier create(String channel) {
        return switch (channel) {
            case "email" -> new EmailNotifier();
            case "sms" -> new SmsNotifier();
            default -> throw new IllegalArgumentException("unknown channel: " + channel);
        };
    }
}
```

**Strategy** makes an algorithm replaceable at runtime. A shipping cost calculator can take a strategy per carrier:

```java
import java.math.BigDecimal;

interface ShippingStrategy {
    BigDecimal cost(BigDecimal weightKg);
}

class FlatRate implements ShippingStrategy {
    public BigDecimal cost(BigDecimal weightKg) {
        return new BigDecimal("5.00");
    }
}

class PerKilogram implements ShippingStrategy {
    public BigDecimal cost(BigDecimal weightKg) {
        return weightKg.multiply(new BigDecimal("1.50"));
    }
}

class Checkout {
    private final ShippingStrategy shipping;

    Checkout(ShippingStrategy shipping) {
        this.shipping = shipping;
    }

    BigDecimal shippingFor(BigDecimal weightKg) {
        return shipping.cost(weightKg);
    }
}
```

**Observer** notifies interested parties when state changes. In Java, the `java.util.concurrent.Flow` API and listener interfaces follow this idea. Keep listeners fast or hand work to an executor, so one slow observer does not block the publisher.

### SOLID principles
- **Single responsibility**: one reason to change per class.
- **Open/closed**: extend behaviour by adding code, such as a new strategy, rather than editing tested code.
- **Liskov substitution**: a subtype must honour the contract of its supertype, so callers do not need type checks.
- **Interface segregation**: prefer small interfaces that clients actually use.
- **Dependency inversion**: depend on abstractions, and pass implementations in.

The `Checkout` class above follows dependency inversion: it depends on `ShippingStrategy`, not on a particular carrier.

### Error handling and graceful degradation
- Use exceptions for exceptional conditions and validation failures that callers cannot continue from. Use checked exceptions for recoverable conditions the caller must handle, and unchecked ones for programming errors.
- Use `Optional` for "no result" from queries, not for absent required values.
- Translate low-level errors at the boundary. A repository should not leak a driver-specific exception to the domain.
- **Graceful degradation** keeps the core function working when a dependency fails: return cached or default data, skip a non-essential feature, or fail fast with a clear message.

```java
public class RecommendationService {

    interface RecommendationClient {
        String fetchFor(String userId) throws Exception;
    }

    private final RecommendationClient client;

    RecommendationService(RecommendationClient client) {
        this.client = client;
    }

    public String recommendationsFor(String userId) {
        try {
            return client.fetchFor(userId);
        } catch (Exception e) {
            // Degrade: the page still renders without personalised items
            return "popular-items";
        }
    }
}
```

The fallback here is trivial for illustration. In a real service, log the failure with context, return a precomputed default, and consider a circuit breaker so repeated failures stop adding latency.

## How it works / Step by step
A method for an LLD interview:
1. Clarify requirements and the main use cases.
2. Identify the core entities and their relationships.
3. Define the public interfaces and the main method signatures.
4. Apply patterns where variation or creation logic is real.
5. Walk through a main use case end to end, and check the SOLID principles.
6. Describe error cases and what the user sees in each.

## Common pitfalls
- Designing every class as an interface, with one implementation each.
- Using a singleton for state that tests need to replace.
- Deep inheritance trees for code reuse, which makes changes ripple unpredictably.
- Mutable domain objects shared across threads without synchronisation.
- Swallowing exceptions, so failures disappear silently.
- Choosing a pattern before understanding the variation it is supposed to handle.

!!! tip "Interview tip"
    **Q: Why use a Strategy instead of an if-else chain?**
    A Strategy puts each algorithm behind an interface, so adding a new one means adding a class rather than editing a conditional that every change touches. It follows the open/closed principle and makes each algorithm testable on its own. Mention that a plain enum with a switch is often enough when the set of variants is small and stable.

## Quick recap
- Model with clear responsibilities, encapsulated state, and narrow, intent-named APIs.
- Use records and sealed types to model data and closed variant sets.
- Apply Singleton (as an enum), Factory, Strategy, and Observer where they remove real variation.
- SOLID guides the seams; dependency inversion is the key one for testability.
- Translate errors at boundaries and degrade gracefully when dependencies fail.

**See also:** [Core Concepts](core-concepts.md), [High-Level Design](high-level-design.md), [Practice Problems](practice-problems.md), [Java Core](../02a-core-language/index.md)
