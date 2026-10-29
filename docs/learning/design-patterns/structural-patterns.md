# Structural Design Patterns

Structural patterns describe how classes and objects are composed into larger structures. They answer questions like "how do I make two incompatible APIs work together", "how do I treat a group of objects like one object", and "how do I add behaviour without editing the original class".

## Core concepts

### Adapter

An adapter lets a class with one interface be used where a different interface is expected. It wraps the incompatible object and translates calls. Java's `InputStreamReader` is an adapter: it turns a byte stream into a character reader.

```java
interface MediaPlayer {
    void play(String fileName);
}

// An existing class with a different method name and signature
class LegacyMp4Player {
    void playMp4(String name) {
        System.out.println("Legacy MP4 player: " + name);
    }
}

class Mp4Adapter implements MediaPlayer {

    private final LegacyMp4Player legacy;

    Mp4Adapter(LegacyMp4Player legacy) {
        this.legacy = legacy;
    }

    @Override
    public void play(String fileName) {
        legacy.playMp4(fileName);
    }
}
```

### Bridge

A bridge separates an abstraction from its implementation so that both can vary independently. Without it, every combination (remote control times device) needs its own subclass. With it, the abstraction holds a reference to an implementation interface.

```java
interface Device {
    void setPower(boolean on);
}

class Television implements Device {
    @Override
    public void setPower(boolean on) {
        System.out.println("TV " + (on ? "on" : "off"));
    }
}

abstract class RemoteControl {

    protected final Device device;

    RemoteControl(Device device) {
        this.device = device;
    }

    abstract void togglePower();
}

class BasicRemote extends RemoteControl {

    private boolean on;

    BasicRemote(Device device) {
        super(device);
    }

    @Override
    void togglePower() {
        on = !on;
        device.setPower(on);
    }
}
```

A new remote (say, an advanced one with a mute button) does not need a new device class, and a new device does not need new remote classes.

### Composite

A composite treats single objects and groups of objects through the same interface. A file system is the usual example: a file and a folder both report a size, and a folder's size is the sum of its children.

```java
import java.util.ArrayList;
import java.util.List;

interface FileNode {
    long size();
}

class FileItem implements FileNode {

    private final long bytes;

    FileItem(long bytes) {
        this.bytes = bytes;
    }

    @Override
    public long size() {
        return bytes;
    }
}

class Folder implements FileNode {

    private final List<FileNode> children = new ArrayList<>();

    void add(FileNode node) {
        children.add(node);
    }

    @Override
    public long size() {
        return children.stream().mapToLong(FileNode::size).sum();
    }

    public static void main(String[] args) {
        Folder root = new Folder();
        root.add(new FileItem(120));
        Folder docs = new Folder();
        docs.add(new FileItem(300));
        root.add(docs);
        System.out.println(root.size()); // 420
    }
}
```

The composite's `size()` method calls `size()` on each child. It does not care whether a child is a leaf or a folder. This recursion is the whole pattern.

### Decorator

A decorator wraps an object that implements an interface, adds behaviour before or after delegating, and implements the same interface. Decorators can be stacked in any order at runtime. Java's I/O classes are the standard example: `new BufferedInputStream(new FileInputStream(path))` adds buffering on top of a file stream.

```java
interface Writer {
    void write(String text);
}

class ConsoleWriter implements Writer {
    @Override
    public void write(String text) {
        System.out.println(text);
    }
}

abstract class WriterDecorator implements Writer {

    protected final Writer inner;

    WriterDecorator(Writer inner) {
        this.inner = inner;
    }
}

class TimestampDecorator extends WriterDecorator {

    TimestampDecorator(Writer inner) {
        super(inner);
    }

    @Override
    public void write(String text) {
        inner.write("[12:00] " + text);
    }
}

class UpperCaseDecorator extends WriterDecorator {

    UpperCaseDecorator(Writer inner) {
        super(inner);
    }

    @Override
    public void write(String text) {
        inner.write(text.toUpperCase());
    }
}

// Usage: new UpperCaseDecorator(new TimestampDecorator(new ConsoleWriter())).write("ready");
// Prints: [12:00] READY
```

Decorators and inheritance solve the same problem differently. Inheritance fixes the combination at compile time, and each new combination needs a new class. Decorators compose at runtime, but they produce many small objects, and the order of wrapping can matter.

### Facade

A facade gives a simple entry point to a subsystem with many parts. The subsystem classes still exist and can still be used directly; the facade is a convenience for the common path.

```java
class InventoryService {
    boolean reserve(String sku) {
        return true; // Real code would check stock
    }
}

class PaymentService {
    boolean charge(double amount) {
        return amount > 0;
    }
}

class ShippingService {
    void schedule(String sku) {
        System.out.println("Shipping " + sku);
    }
}

class CheckoutFacade {

    private final InventoryService inventory = new InventoryService();
    private final PaymentService payment = new PaymentService();
    private final ShippingService shipping = new ShippingService();

    boolean placeOrder(String sku, double amount) {
        if (!inventory.reserve(sku)) {
            return false;
        }
        if (!payment.charge(amount)) {
            return false;
        }
        shipping.schedule(sku);
        return true;
    }
}
```

The client calls `placeOrder` and does not need to know the order of the three steps. A facade should not hide everything, or it becomes a bottleneck that every change must pass through.

### Flyweight

A flyweight shares state that many objects have in common, so that thousands of objects do not each store their own copy. The shared part is called intrinsic state, and the part that differs per use is extrinsic state, which the caller passes in.

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

final class CharacterStyle {

    private static final Map<String, CharacterStyle> CACHE = new ConcurrentHashMap<>();

    private final String font;
    private final int size;

    private CharacterStyle(String font, int size) {
        this.font = font;
        this.size = size;
    }

    static CharacterStyle of(String font, int size) {
        return CACHE.computeIfAbsent(font + ":" + size, key -> new CharacterStyle(font, size));
    }

    @Override
    public String toString() {
        return font + " " + size;
    }

    public static void main(String[] args) {
        CharacterStyle a = CharacterStyle.of("Serif", 12);
        CharacterStyle b = CharacterStyle.of("Serif", 12);
        System.out.println(a == b); // true, one shared object
    }
}
```

Java already uses this idea. `Integer.valueOf` caches values from -128 to 127, and `String` literals are pooled. The flyweight only pays off when there are very many objects with few distinct states.

### Proxy

A proxy stands in for another object and controls access to it. The proxy has the same interface as the real object. It can add lazy loading, access checks, logging, caching, or remote calls. Java's dynamic proxies create a proxy at runtime from an interface.

```java
import java.lang.reflect.Proxy;

interface UserRepository {
    String findName(long id);
}

class DatabaseUserRepository implements UserRepository {
    @Override
    public String findName(long id) {
        return "user-" + id;
    }

    public static void main(String[] args) {
        UserRepository real = new DatabaseUserRepository();
        UserRepository loggingProxy = (UserRepository) Proxy.newProxyInstance(
                UserRepository.class.getClassLoader(),
                new Class<?>[] {UserRepository.class},
                (proxy, method, methodArgs) -> {
                    System.out.println("Calling " + method.getName());
                    return method.invoke(real, methodArgs);
                });
        System.out.println(loggingProxy.findName(7L));
    }
}
```

Spring AOP creates proxies in the same way, so a `@Transactional` method call goes through a proxy before it reaches your code. This is why self-invocation (calling an annotated method from within the same class) skips the advice. See [AOP](../08-spring-core/aop.md).

## How it works / Step by step

| Pattern | Problem it solves | Key mechanism |
|---------|------------------|---------------|
| Adapter | Incompatible interfaces | Wrap and translate calls |
| Bridge | Two dimensions of variation | Hold a reference to the implementation interface |
| Composite | Part-whole trees | Same interface for leaves and branches |
| Decorator | Add behaviour at runtime | Wrap and delegate, same interface |
| Facade | Complex subsystem | One simple entry point |
| Flyweight | Too many similar objects | Share intrinsic state through a cache |
| Proxy | Control access | Same interface, extra logic before or after delegation |

## Common pitfalls

- **Confusing adapter and facade.** An adapter changes an interface to match another one. A facade defines a new, simpler interface over several existing ones.
- **Confusing decorator and proxy.** A decorator adds behaviour the caller chose. A proxy controls access, often with the proxy creating or locating the real object itself.
- **Deep decorator stacks.** Long chains are hard to debug. Keep the number of wrappers small and name them clearly.
- **Flyweight with mutable shared state.** Shared objects must not change after creation, or one caller will affect all others.
- **Dynamic proxies only work with interfaces.** For a class without an interface, use a class-based proxy mechanism instead (for example, the CGLIB-based proxies that Spring falls back to in some configurations).

!!! tip "Interview tip"
    "How is a proxy different from a decorator?" Both wrap an object with the same interface. A decorator is built by the code that wants extra behaviour, and it usually stacks several wrappers. A proxy is about access control or lifecycle, such as lazy creation or security checks, and the client often does not know a proxy exists.

## Quick recap

- Adapter translates one interface into another.
- Bridge separates abstraction from implementation so each can grow on its own.
- Composite lets a group and a single item share one interface.
- Decorator adds behaviour by wrapping; Java I/O uses it heavily.
- Facade offers one simple entry point to a complex subsystem.
- Flyweight shares common state to save memory.
- Proxy controls access; Spring AOP and dynamic proxies rely on it.

**See also:** [Creational Patterns](creational-patterns.md), [Behavioural Patterns](behavioural-patterns.md), [AOP](../08-spring-core/aop.md), [Design Patterns interview questions](../../interview-questions/technical/design-patterns-part-1.md)
