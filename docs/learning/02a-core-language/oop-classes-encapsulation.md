# Classes, Objects and Encapsulation

A class is a blueprint that defines state (fields) and behaviour (methods), and an object is one instance of that blueprint. Encapsulation hides state behind a deliberate interface. Interviewers ask how constructors chain, what order initializers run in, and whether a relationship is composition or aggregation, so this page covers those mechanics with small examples.

## Core concepts

### Classes and objects
A class declares fields, constructors, and methods. `new` creates an object on the heap and runs a constructor. Each object gets its own copy of instance fields; `static` members belong to the class and are shared.

```java
public class BankAccount {
    private static int openedCount = 0;   // class-level
    private final String id;              // per object, set once
    private long balanceCents;            // per object

    public BankAccount(String id) {
        this.id = id;
        openedCount++;
    }

    public long balance() {
        return balanceCents;
    }

    public static int openedCount() {
        return openedCount;
    }

    public static void main(String[] args) {
        BankAccount a = new BankAccount("A-1");
        System.out.println(a.balance() + " " + BankAccount.openedCount()); // 0 1
    }
}
```

### Constructors and this
A constructor has the class name and no return type. If you write none, the compiler supplies a no-argument default constructor. Writing any constructor removes that default. Use `this` to refer to the current object, and `this(...)` as the first statement to call another constructor in the same class.

```java
public class Point {
    private final int x;
    private final int y;

    public Point() {
        this(0, 0);            // constructor chaining within the class
    }

    public Point(int x, int y) {
        this.x = x;            // this.x is the field; x is the parameter
        this.y = y;
    }

    @Override
    public String toString() {
        return "(" + x + ", " + y + ")";
    }

    public static void main(String[] args) {
        System.out.println(new Point());      // (0, 0)
        System.out.println(new Point(3, 4));  // (3, 4)
    }
}
```

### Constructor chaining with super
A subclass constructor calls its superclass constructor first. If the first statement is not `this(...)` or `super(...)`, the compiler inserts `super()`. This is why a superclass with only a parameterized constructor forces every subclass to pass arguments up.

### Copy constructors and the builder pattern
A copy constructor takes an object of the same class and copies its state. It gives you an independent object without `clone()`, which is awkward to implement correctly. A builder collects optional settings step by step and then creates an immutable object in one place.

```java
public class Settings {
    private final String host;
    private final int port;

    private Settings(Builder builder) {
        this.host = builder.host;
        this.port = builder.port;
    }

    public Settings(Settings other) {        // copy constructor
        this.host = other.host;
        this.port = other.port;
    }

    public static class Builder {
        private String host = "localhost";
        private int port = 8080;

        public Builder host(String host) {
            this.host = host;
            return this;
        }

        public Builder port(int port) {
            this.port = port;
            return this;
        }

        public Settings build() {
            return new Settings(this);
        }
    }

    public static void main(String[] args) {
        Settings s = new Settings.Builder().port(9000).build();
        Settings copy = new Settings(s);
        System.out.println(copy.host + ":" + copy.port);   // localhost:9000
    }
}
```

### Initialization order
When a class is first used, its static fields and static initializer blocks run once, in textual order. For each new object, the order is:

1. The superclass constructor chain runs (its own initialization happens inside it).
2. Instance field initializers and instance initializer blocks run, in textual order.
3. The rest of the constructor body runs.

```java
public class Init {
    static { System.out.println("1. static block"); }
    { System.out.println("3. instance block"); }
    private int value = compute("4. field initializer");

    Init() {
        System.out.println("5. constructor body");
    }

    static int compute(String label) {
        System.out.println(label);
        return 1;
    }

    public static void main(String[] args) {
        System.out.println("0. main starts");
        new Init();
    }
}
```

Running this prints the static block first (when the class is initialized, before `main`'s first line when `main` lives in that class), then the instance steps in order.

### Static members
A `static` member belongs to the class. Static fields have one copy shared by all instances. Static methods are called on the class and cannot use `this` or instance fields. Static initializer blocks run once, when the class is initialized. A static nested class has no link to an instance of the outer class.

Static methods are hidden, not overridden. The method that runs is chosen by the declared type of the reference, not by the object's actual class:

```java
class Parent {
    static String name() { return "parent"; }
}

class Child extends Parent {
    static String name() { return "child"; }   // hides Parent.name(); does not override it
}

public class HidingDemo {
    public static void main(String[] args) {
        Parent p = new Child();
        System.out.println(p.name());          // parent: chosen by the declared type
        System.out.println(Child.name());      // child
    }
}
```

### Instance members and variable scope
Instance methods can read and write instance fields and call other instance methods. Static methods cannot refer to `this` or instance fields directly. A parameter or local variable can hide a field of the same name; use `this.name` to reach the field.

### Association, aggregation, composition, and dependency
Objects relate to each other in four common ways. The first three are about how long the linked objects live. Dependency is about how long one class relies on another.

| Relation | Meaning | Ownership and lifetime | Example |
|---|---|---|---|
| Association | One object knows about another through a link | Neither owns the other; both can exist alone | A `Student` is linked to a `Course` through an enrollment |
| Aggregation | A "has-a" link where the part can exist without the whole | The whole refers to parts it does not own | A `Team` refers to `Player` objects that can exist without it |
| Composition | A "part-of" link where the part cannot outlive the whole | The whole creates and owns the part | An `Order` creates its `OrderLine` objects |
| Dependency | A class uses another briefly, typically in a method | No field; the relation lasts for one call | A report service uses a printer inside one method |

```java
import java.util.ArrayList;
import java.util.List;

class Order {                         // composition: creates its lines
    private final List<String> lines = new ArrayList<>();
    public void addLine(String item) { lines.add(item); }
}

class Player { }

class Team {                          // aggregation: receives existing players
    private final List<Player> players;
    public Team(List<Player> players) { this.players = players; }
}
```

These examples assume `java.util.ArrayList` and `java.util.List` are imported, and `Player` is a separate class. Composition is usually preferred for code you control, because it keeps lifetimes simple.

A dependency keeps no field. The class uses the other one inside a method and forgets it afterwards:

```java
class Printer {
    void print(String text) {
        System.out.println(text);
    }
}

class ReportService {
    void publish(String text) {
        new Printer().print(text);   // dependency: no field, used only inside this method
    }
}
```

### Encapsulation
Encapsulation keeps fields `private` and exposes behaviour through methods. Getters return values, setters validate and then assign. Avoid a setter for every field; often a method that performs an operation (such as `deposit`) expresses intent better.

```java
public class Temperature {
    private double celsius;

    public double getCelsius() {
        return celsius;
    }

    public void setCelsius(double value) {
        if (value < -273.15) {
            throw new IllegalArgumentException("below absolute zero: " + value);
        }
        this.celsius = value;
    }
}
```

Return immutable views or copies of mutable state. Returning a live internal list lets callers change your object without going through its rules.

```java
import java.util.ArrayList;
import java.util.List;

public class Order {
    private final List<String> lines = new ArrayList<>();

    public List<String> lines() {
        return List.copyOf(lines);   // a copy: callers cannot change our list
    }
}
```

### JavaBeans, POJOs, and EJB
These three terms describe how a class is written and what it is for.

- **POJO (plain old Java object):** an ordinary class that does not extend or implement a framework type. Frameworks can use it without special rules. Most domain and DTO classes are POJOs.
- **JavaBean:** a POJO that follows conventions so tools can read and edit its properties. It has a public no-argument constructor, private fields exposed through getters and setters, and, as a common convention, implements `Serializable`. The JavaBeans specification itself does not require `Serializable`.
- **EJB (Enterprise JavaBean):** a server-side component model from the enterprise platform. EJBs add transactions, security, and remote access managed by the container. They are heavier than beans and POJOs. In current code the package names are `jakarta.ejb.*`; older code uses `javax.ejb.*`.

```java
import java.io.Serializable;

public class StudentBean implements Serializable {
    private static final long serialVersionUID = 1L;

    private String name;
    private int age;

    public StudentBean() { }                 // public no-argument constructor

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
}
```

Records (Java 16) are a compact way to write a POJO for data that should not change. They do not follow the bean setter convention.

### Serialization
Serialization turns an object's state into a byte stream, so it can be written to a file or sent over a network. Deserialization rebuilds the object from those bytes. A class opts in by implementing `java.io.Serializable`, a marker interface with no methods. Subclasses of a serializable class are serializable too.

Two details come up in interviews. A `transient` field is skipped, so it comes back as its default value. A `serialVersionUID` identifies the class version. Declare it explicitly, because otherwise the JVM computes one from the class shape, and a small edit can make old data unreadable.

```java
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;

class Profile implements Serializable {
    private static final long serialVersionUID = 1L;

    String user;
    transient String password;     // not written to the stream
}

public class SerializationDemo {
    public static void main(String[] args) throws IOException, ClassNotFoundException {
        Profile original = new Profile();
        original.user = "ada";
        original.password = "secret";

        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(original);
        }

        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray()))) {
            Profile copy = (Profile) in.readObject();
            System.out.println(copy.user + " " + copy.password);   // ada null
        }
    }
}
```

Avoid deserializing data from untrusted sources. Java deserialization has a long history of security bugs, so prefer a plain data format such as JSON for data that crosses a trust boundary.

### Object identity, equals and hashCode
`==` compares identity. Override `equals` and `hashCode` together when objects should compare by value, and keep them consistent: equal objects must have equal hash codes. Records (Java 16) generate both for you.

## How it works / Step by step

1. `new` allocates memory for the object's fields, with default values.
2. The constructor is selected by argument types at compile time.
3. The constructor chain runs top-down: superclass first, then field initializers and instance blocks, then the constructor body.
4. Method calls use the object's reference; static methods are called on the class.
5. Private members are accessible only inside the same class, which is how encapsulation is enforced.

## Common pitfalls
- Assuming the default constructor still exists after you add a parameterized one. It does not.
- Forgetting `this.` when a parameter has the same name as a field, so the assignment does nothing useful.
- Calling an overridable method from a constructor, where the subclass field is still uninitialized.
- Exposing a mutable list or array through a getter.
- Writing a setter for every field, which defeats encapsulation.
- Overriding `equals` without `hashCode`, so hash-based collections fail to find objects.
- Assuming a static method can access an instance field.

!!! tip "Interview tip"
    **Q: Composition or inheritance?** Prefer composition when the relationship is "has a" or when you want to reuse behaviour without locking in a type hierarchy. Use inheritance for a true "is a" relationship with shared behaviour. Composition lets you change the parts at run time and avoids fragile base-class problems.

## Quick recap
- A class defines fields and methods; `new` creates an object and runs a constructor.
- `this(...)` chains constructors in one class; `super(...)` calls the parent constructor first.
- Initialization order: static blocks once, then per object: superclass, field initializers and instance blocks, constructor body.
- Composition means ownership of the part; aggregation means a reference to an existing object.
- Keep fields private, validate in setters, and return copies of mutable state.

**See also:** [Inheritance, Polymorphism and Interfaces](inheritance-polymorphism-interfaces.md), [Enums, Inner Classes and Packages](enums-inner-classes-packages.md), [Wrappers, Strings and Arrays](wrappers-strings-arrays.md)
