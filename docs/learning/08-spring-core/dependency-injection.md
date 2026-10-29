# Dependency Injection

Dependency injection (DI) is the mechanism by which the container supplies a bean's collaborators. Spring supports constructor, setter, field, and method injection. Interviewers ask about DI to see whether you prefer constructor injection and why, how you resolve ambiguity between several candidate beans, and how you handle circular dependencies.

## Core concepts

### Constructor injection (preferred)

Constructor injection passes dependencies through the constructor. The fields can be `final`, the object is never half-built, and tests can create the class with plain `new` and fake collaborators.

```java
import org.springframework.stereotype.Service;

@Service
public class OrderService {

    private final PaymentClient payments;
    private final OrderRepository orders;

    public OrderService(PaymentClient payments, OrderRepository orders) {
        this.payments = payments;
        this.orders = orders;
    }

    public void place(long orderId) {
        // use payments and orders
    }
}
```

When a class has one constructor, Spring uses it without `@Autowired`. With several constructors, mark the one to use with `@Autowired`.

### Setter injection

Setter injection suits optional dependencies that can be changed after construction. It leaves the object partly built until the setter runs, so use it sparingly.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ReceiptPrinter {

    private Formatter formatter;

    @Autowired(required = false)           // optional: skipped if no Formatter bean exists
    public void setFormatter(Formatter formatter) {
        this.formatter = formatter;
    }
}
```

```java
interface Formatter {                      // application interface, not java.util.Formatter
    String format(String text);
}
```

### Field injection

Field injection puts `@Autowired` on a field. It is short but has real costs: the fields cannot be `final`, the dependencies are hidden from the constructor signature, and tests need reflection or a Spring context to set them. Avoid it in new code, and prefer constructor injection.

### Method injection

A method marked `@Autowired` is called after construction, with its parameters injected. It behaves like a setter with several arguments. Use it rarely.

### Autowiring modes

In XML configuration, `autowire` controls how collaborators are matched:

| Mode | Matches by |
|---|---|
| `no` | Nothing; dependencies must be wired explicitly (default) |
| `byName` | Property name equals bean name |
| `byType` | Property type matches exactly one bean |
| `constructor` | Constructor parameter type matches a bean |

Annotation-based injection uses type first, then name as a tie-break, and does not use these XML modes. Know the modes for legacy code and interviews; in modern Spring, annotations do the work.

### Annotations: @Autowired, @Resource, @Inject

| Annotation | From | Notes |
|---|---|---|
| `@Autowired` | Spring | Matches by type; supports `required` and `Optional` |
| `@Resource` | JSR-250 (`jakarta.annotation`) | Matches by name first, then type |
| `@Inject` | JSR-330 (`jakarta.inject`) | Matches by type; no `required` attribute |

`@Autowired` is the Spring default and the one most codebases use. Use one style consistently.

### Resolving ambiguity: @Qualifier and @Primary

When two beans match the type, Spring fails with `NoUniqueBeanDefinitionException` unless you disambiguate.

```java
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

public interface PaymentGateway {
    void charge(long cents);
}

@Component("cardGateway")
@Primary                              // used when no qualifier is given
class CardGateway implements PaymentGateway {
    public void charge(long cents) { }
}

@Component("bankGateway")
class BankTransferGateway implements PaymentGateway {
    public void charge(long cents) { }
}

@org.springframework.stereotype.Service
class Checkout {
    private final PaymentGateway gateway;

    Checkout(@Qualifier("bankGateway") PaymentGateway gateway) {   // overrides @Primary
        this.gateway = gateway;
    }
}
```

`@Primary` sets a default. `@Qualifier` picks a specific bean at the injection point. Use `@Qualifier` for explicit choices and `@Primary` for the common default.

### Custom qualifiers with a meta-annotation

Repeating `@Qualifier("bankGateway")` with string literals across many classes is easy to get wrong. A custom qualifier gives the choice a name, and the injection point reads as a domain term. You create an annotation and mark it with `@Qualifier`, which makes it a qualifier in its own right. Spring compares its attributes with the annotation on each candidate bean.

```java
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import org.springframework.beans.factory.annotation.Qualifier;

@Target({ElementType.TYPE, ElementType.FIELD, ElementType.PARAMETER, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Qualifier
public @interface Channel {
    String value();
}
```

The candidates carry the same annotation, and the injection point asks for it:

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

public interface Notifier {
    void send(String recipient, String message);
}

@Service
@Channel("email")
class EmailNotifier implements Notifier {
    public void send(String recipient, String message) { }
}

@Service
@Channel("sms")
class SmsNotifier implements Notifier {
    public void send(String recipient, String message) { }
}

@Service
class ReminderService {

    private final Notifier notifier;

    ReminderService(@Channel("sms") Notifier notifier) {   // picks SmsNotifier
        this.notifier = notifier;
    }
}
```

A misspelt value such as `@Channel("smss")` fails at startup with a "no qualifying bean" error, which is better than a silent wrong choice. To avoid repeating literals, keep the values in a constants class and write `@Channel(Channels.SMS)`. For a marker with no value, such as "the cached implementation", declare the annotation without a `value` element and match on the annotation alone.

### Collections and optional dependencies

Spring injects all beans of a type as a `List`, `Set`, or `Map` (keyed by bean name). This is useful for strategy patterns.

```java
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class PaymentRouter {
    private final List<PaymentGateway> gateways;

    public PaymentRouter(List<PaymentGateway> gateways) {   // all PaymentGateway beans
        this.gateways = gateways;
    }
}
```

For optional beans, use `Optional<T>` as the parameter type, or `ObjectProvider<T>` when you also need lazy or repeated lookup.

```java
import java.util.Optional;

public class AuditHook {
    private final Optional<Auditor> auditor;

    public AuditHook(Optional<Auditor> auditor) {   // empty, not an error, if no Auditor bean exists
        this.auditor = auditor;
    }
}

interface Auditor { }
```

### Circular dependencies

A circular dependency is when bean A needs B and B needs A. Constructor injection cannot resolve it, because neither can be built first. Spring Boot 2.6 and later prohibits circular references by default (`spring.main.allow-circular-references` is `false`).

Fix the design rather than enabling the flag:

- Extract the shared logic into a third bean that both depend on.
- Move one of the calls to an event: publish a Spring application event and let the other bean listen.
- Pass a function or callback instead of the whole bean.
- Use `@Lazy` on one injection point as a last resort. It defers creation with a proxy and hides the design problem.

The event approach is the cleanest of these. The publisher does not know who listens, so the dependency points one way only:

```java
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;

record OrderPlaced(String orderId) { }

@Service
class OrderPlacement {

    private final ApplicationEventPublisher events;

    OrderPlacement(ApplicationEventPublisher events) {
        this.events = events;
    }

    void place(String orderId) {
        events.publishEvent(new OrderPlaced(orderId));   // no reference to the listener
    }
}

@Service
class LoyaltyPoints {

    @EventListener
    void onOrderPlaced(OrderPlaced event) {
        // award points; OrderPlacement never depends on this class
    }
}
```

Circular dependencies are usually a sign that two classes have too much responsibility in common.

## How it works / Step by step

Injecting a constructor-based bean:

1. The container finds the constructor of `OrderService`.
2. For each parameter, it looks up a matching bean by type (then qualifier, primary, or name).
3. If a matching bean does not exist yet, it creates that bean first, recursively.
4. It calls the constructor with the resolved beans, then runs the rest of the lifecycle.

If step 3 loops back to a bean already being created, the container detects a cycle.

## Common pitfalls

- Using field injection in new code, which hides dependencies and blocks `final` fields.
- Adding `@Autowired(required = false)` to a dependency that is actually required, which hides a missing bean until it is used.
- Injecting several beans of one type without `@Primary` or `@Qualifier`, then getting a startup error.
- Enabling `allow-circular-references` to get the application to start.
- Injecting a request-scoped bean into a singleton without a scoped proxy.
- Forgetting that injected `List` order depends on bean ordering; use `@Order` when order matters.

!!! tip "Interview tip"
    **Q: Why is constructor injection preferred over field injection?**
    The dependencies are explicit and required, the fields can be `final` (immutable after construction), the class is easy to test with plain `new`, and missing dependencies fail at startup. Field injection hides dependencies, needs reflection in tests, and cannot enforce immutability.

## Quick recap

- Constructor injection is the default choice; setter injection suits optional dependencies.
- `@Autowired` matches by type; `@Resource` matches by name first.
- Resolve ambiguity with `@Primary` (default) and `@Qualifier` (explicit).
- Inject `List<T>` for all beans of a type; use `Optional<T>` for optional ones.
- Spring Boot 2.6+ forbids circular dependencies by default; redesign rather than enable them.

**See also:** [IoC and Beans](ioc-and-beans.md), [Stereotypes and Configuration](stereotypes-and-configuration.md), [Transactions](transactions.md)
