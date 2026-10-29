# Behavioural Design Patterns

Behavioural patterns deal with how objects communicate and share responsibility. They are the patterns most likely to show up in day-to-day code: event listeners, undo buttons, pluggable algorithms, and request pipelines all use them.

## Core concepts

### Chain of Responsibility

A request passes along a chain of handlers. Each handler either deals with the request or passes it to the next one. The sender does not need to know which handler will process it. Servlet filters and Spring Security's filter chain follow this shape.

```java
abstract class SupportHandler {

    private SupportHandler next;

    SupportHandler setNext(SupportHandler next) {
        this.next = next;
        return next;
    }

    void handle(int severity) {
        if (canHandle(severity)) {
            System.out.println(name() + " handled severity " + severity);
        } else if (next != null) {
            next.handle(severity);
        } else {
            System.out.println("No handler for severity " + severity);
        }
    }

    abstract boolean canHandle(int severity);

    abstract String name();
}

class FirstLine extends SupportHandler {
    @Override boolean canHandle(int severity) { return severity <= 2; }
    @Override String name() { return "First line"; }
}

class Engineer extends SupportHandler {
    @Override boolean canHandle(int severity) { return severity <= 4; }
    @Override String name() { return "Engineer"; }
}
```

Build the chain with `first.setNext(new Engineer())`, then call `first.handle(3)`. The request ends at the engineer.

### Command

A command turns a request into an object. That object can be stored, queued, logged, or undone later. Runnable and Callable are simple forms of this. Undo support adds an `undo()` method.

```java
interface Command {
    void execute();
    void undo();
}

class Light {
    void on() { System.out.println("Light on"); }
    void off() { System.out.println("Light off"); }
}

class TurnOnLight implements Command {

    private final Light light;

    TurnOnLight(Light light) {
        this.light = light;
    }

    @Override
    public void execute() {
        light.on();
    }

    @Override
    public void undo() {
        light.off();
    }
}
```

An invoker (a button, a menu, a job queue) stores commands in a list. Undo is then "pop the last command and call `undo()`".

### Interpreter

An interpreter defines a grammar as a set of classes, where each class knows how to evaluate one kind of expression. It suits small languages, such as rule expressions or arithmetic formulas. For large grammars, a parser generator is a better tool.

```java
interface Expr {
    int eval();
}

record Num(int value) implements Expr {
    @Override
    public int eval() {
        return value;
    }
}

record Add(Expr left, Expr right) implements Expr {
    @Override
    public int eval() {
        return left.eval() + right.eval();
    }
}

// new Add(new Num(2), new Add(new Num(3), new Num(4))).eval() returns 9
```

### Iterator

An iterator gives sequential access to a collection without exposing its internal structure. In Java, `Iterator` and `Iterable` are the standard form, and the enhanced `for` loop uses them. Iterators are not thread-safe, and `ConcurrentModificationException` is thrown when a fail-fast iterator sees a change.

```java
import java.util.Iterator;

class Countdown implements Iterable<Integer> {

    private final int start;

    Countdown(int start) {
        this.start = start;
    }

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int current = start;

            @Override
            public boolean hasNext() {
                return current > 0;
            }

            @Override
            public Integer next() {
                return current--;
            }
        };
    }
}
// for (int n : new Countdown(3)) prints 3, 2, 1
```

### Mediator

A mediator is the object that coordinates communication between peers. The peers talk to the mediator, not to each other, so adding a peer does not require changes to every other peer. An air traffic control tower and a chat room server both play this role.

```java
import java.util.ArrayList;
import java.util.List;

class ChatRoom {

    private final List<User> users = new ArrayList<>();

    void join(User user) {
        users.add(user);
    }

    void send(String from, String message, User sender) {
        for (User user : users) {
            if (user != sender) {
                user.receive(from, message);
            }
        }
    }
}

class User {

    private final String name;
    private final ChatRoom room;

    User(String name, ChatRoom room) {
        this.name = name;
        this.room = room;
        room.join(this);
    }

    void send(String message) {
        room.send(name, message, this);
    }

    void receive(String from, String message) {
        System.out.println(name + " received from " + from + ": " + message);
    }
}
```

### Memento

A memento captures an object's state so it can be restored later, without exposing the object's fields to the caller. The originator creates the memento, and a caretaker stores it.

```java
class Editor {

    private String text = "";

    void type(String more) {
        text = text + more;
    }

    String text() {
        return text;
    }

    Memento save() {
        return new Memento(text);
    }

    void restore(Memento memento) {
        this.text = memento.text();
    }

    // Records are implicitly static, so the memento does not hold a reference to the editor
    record Memento(String text) {
    }
}
```

The caretaker keeps a `Deque<Editor.Memento>` for undo history. Snapshots of large state can use a lot of memory, so store only what you need to restore.

### Observer

An observer lets one subject notify a set of listeners when its state changes. The subject knows only the listener interface, so listeners can be added or removed without changing the subject. Event listeners in Swing, JavaBeans, and most UI frameworks use this shape. Messaging systems apply the same idea across processes.

```java
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

interface PriceListener {
    void onPriceChanged(String symbol, double price);
}

class PriceFeed {

    // CopyOnWriteArrayList lets listeners subscribe while a publish is running
    private final List<PriceListener> listeners = new CopyOnWriteArrayList<>();

    void subscribe(PriceListener listener) {
        listeners.add(listener);
    }

    void publish(String symbol, double price) {
        for (PriceListener listener : listeners) {
            listener.onPriceChanged(symbol, price);
        }
    }

    public static void main(String[] args) {
        PriceFeed feed = new PriceFeed();
        feed.subscribe((symbol, price) -> System.out.println(symbol + " is now " + price));
        feed.publish("ACME", 42.5);
    }
}
```

`java.util.Observable` and `Observer` were deprecated in Java 9. Write a small interface like the one above, or use `PropertyChangeSupport` from `java.beans` for bean-style properties.

### State

A state object holds the behaviour for one state of an object, and the context delegates to whichever state is current. Unlike Strategy, the states usually change each other. A traffic light is a good example. An enum with constant-specific bodies is a compact way to write it.

```java
enum TrafficLight {

    RED {
        @Override
        TrafficLight next() {
            return GREEN;
        }
    },
    GREEN {
        @Override
        TrafficLight next() {
            return YELLOW;
        }
    },
    YELLOW {
        @Override
        TrafficLight next() {
            return RED;
        }
    };

    abstract TrafficLight next();
}
```

Calling `TrafficLight.RED.next()` returns `GREEN`. Each state decides the transition, and the enum's constants are the states.

### Strategy

A strategy is an interchangeable algorithm behind an interface. The caller picks the strategy, and the context uses it without knowing the details. In modern Java, a strategy is often a lambda. `Comparator` is a strategy for sorting.

```java
interface DiscountPolicy {
    double apply(double price);
}

class Checkout {

    private final DiscountPolicy discount;

    Checkout(DiscountPolicy discount) {
        this.discount = discount;
    }

    double total(double price) {
        return discount.apply(price);
    }

    public static void main(String[] args) {
        Checkout seasonal = new Checkout(price -> price * 0.9);
        Checkout none = new Checkout(price -> price);
        System.out.println(seasonal.total(100.0)); // 90.0
        System.out.println(none.total(100.0));     // 100.0
    }
}
```

### Template Method

A template method defines the skeleton of an algorithm in a base class, and subclasses fill in some steps. The base method is usually `final` so subclasses cannot reorder the steps. `HttpServlet` and `AbstractList` use this idea.

```java
abstract class ReportGenerator {

    // The template: fixed order, cannot be overridden
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

### Visitor

A visitor adds new operations to a fixed set of classes without changing them. Each element accepts a visitor and calls the visitor method that matches its type. The price is that adding a new element type requires changing every visitor. Use this when the set of types is stable and the operations change often.

```java
interface ShapeVisitor<R> {
    R visit(Circle circle);
    R visit(Square square);
}

interface Shape {
    <R> R accept(ShapeVisitor<R> visitor);
}

record Circle(double radius) implements Shape {
    @Override
    public <R> R accept(ShapeVisitor<R> visitor) {
        return visitor.visit(this);
    }
}

record Square(double side) implements Shape {
    @Override
    public <R> R accept(ShapeVisitor<R> visitor) {
        return visitor.visit(this);
    }
}

class AreaVisitor implements ShapeVisitor<Double> {
    @Override
    public Double visit(Circle circle) {
        return Math.PI * circle.radius() * circle.radius();
    }

    @Override
    public Double visit(Square square) {
        return square.side() * square.side();
    }
}
```

Java 21's pattern matching for `switch` often replaces a visitor when the hierarchy is sealed. The visitor is still the right choice when the operations belong to a separate concern and must be defined from outside the types.

## How it works / Step by step

| Pattern | Who decides what happens | Typical Java example |
|---------|-------------------------|----------------------|
| Chain of Responsibility | Each handler, one at a time | Servlet filters, Spring Security filters |
| Command | The command object, when executed | `Runnable`, job queues, undo stacks |
| Interpreter | Expression classes | Small rule or formula evaluators |
| Iterator | The iterator, step by step | `Iterable` and enhanced `for` |
| Mediator | The mediator, between peers | Chat rooms, message brokers within a process |
| Memento | The originator restores its own snapshot | Undo history in editors |
| Observer | Each listener, on notification | Event listeners, JavaBeans property change events |
| State | The current state object | Order status flows, traffic light cycles |
| Strategy | The chosen algorithm | `Comparator`, payment methods |
| Template Method | The base class order, subclass steps | `AbstractList`, `HttpServlet` |
| Visitor | The visitor, per element type | Compiler AST passes |

## Common pitfalls

- **Chain with no terminal handler.** If no handler accepts the request, it disappears silently. Decide what the end of the chain does.
- **Observers that throw.** One listener's exception can stop the notification loop for the rest. Catch and log per listener if that matters.
- **Mutating a list during iteration.** Use a concurrent list, or copy the listeners before the loop.
- **Strategy and State mixed up.** Strategy is chosen from outside and usually does not change the context's mode. State changes itself over time.
- **Visitor everywhere.** Each new element type touches every visitor. Use it only where the type set is stable.
- **Memento leaking internals.** If the memento exposes the object's fields, callers can change them. Keep it opaque or immutable.

!!! tip "Interview tip"
    "Strategy and State have the same class diagram. What is the difference?" Strategy is picked by the client and stays fixed for a use case. State is changed by the object itself as it moves between modes, and each state knows the next state.

## Quick recap

- Chain of Responsibility: pass a request along until one handler takes it.
- Command: wrap an action in an object so it can be queued or undone.
- Interpreter: evaluate a small grammar with one class per rule.
- Iterator: walk a collection without exposing its structure.
- Mediator: route communication through one coordinator.
- Memento: save and restore state without exposing internals.
- Observer: notify subscribers when a subject changes.
- State: let an object change its behaviour as its state changes.
- Strategy: swap an algorithm behind an interface, often with a lambda.
- Template Method: fix the algorithm's order in a base class.
- Visitor: add operations to a stable set of types.

**See also:** [Creational Patterns](creational-patterns.md), [Structural Patterns](structural-patterns.md), [SOLID and Anti-Patterns](solid-and-anti-patterns.md), [Design Patterns interview questions](../../interview-questions/technical/design-patterns-part-1.md)
