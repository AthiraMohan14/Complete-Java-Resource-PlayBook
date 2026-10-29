# Annotations and Reflection

Annotations attach metadata to code, and reflection lets a program inspect and use that code at runtime. Together they explain how Spring finds your beans, how JUnit finds your tests, and how JPA maps your entities. Interviewers ask about them to check that you understand the framework magic, not only the syntax.

## Core concepts

### What an annotation is

An annotation is metadata. By itself it does nothing. It becomes useful when a tool reads it: the compiler, an annotation processor, or code that uses reflection. The annotation has no effect on behaviour unless something acts on it.

There are three forms:

- **Marker**: no elements, such as `@Override` or `@FunctionalInterface`.
- **Single-element**: one element, which may be named `value`, such as `@SuppressWarnings("unchecked")`.
- **Full**: several named elements with optional defaults, such as `@Retention(RetentionPolicy.RUNTIME)`.

### Built-in annotations

| Annotation | Purpose |
|------------|---------|
| `@Override` | The compiler checks that the method really overrides a supertype method |
| `@Deprecated` | Marks an element as discouraged; `forRemoval = true` warns that it will go away |
| `@FunctionalInterface` | The compiler checks that the interface has exactly one abstract method |
| `@SafeVarargs` | Promises that a varargs method does not misuse its generic array |
| `@SuppressWarnings` | Suppresses named compiler warnings in the annotated element |

### Meta-annotations: annotations on annotations

Four meta-annotations control how your own annotation behaves.

- `@Retention` sets how long the annotation is kept: `SOURCE` (dropped by the compiler), `CLASS` (kept in the class file but not visible at runtime, the default), or `RUNTIME` (visible through reflection).
- `@Target` limits where the annotation may appear, such as `METHOD`, `FIELD`, or `TYPE`.
- `@Documented` includes the annotation in generated Javadoc.
- `@Inherited` lets a subclass inherit a class-level annotation from its superclass. It applies only to classes, not to interfaces or methods.

`@Repeatable` lets the same annotation appear more than once on one element when it is paired with a containing annotation.

### Writing a custom annotation

Declare an annotation with `@interface`. Elements look like methods with optional `default` values.

```java
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface Timed {
    String label() default "";
}

class ReportService {

    @Timed(label = "monthly")
    public void run() {
        System.out.println("Running report");
    }

    public void helper() {
        System.out.println("Not timed");
    }
}
```

Without `RUNTIME` retention, the annotation would be invisible to the reader below.

### Reading annotations with reflection

Reflection reads annotations through the `AnnotatedElement` interface, which `Class`, `Method`, `Field`, and `Constructor` implement.

```java
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.Method;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface Timed {
    String label() default "";
}

class ReportService {

    @Timed(label = "monthly")
    public void run() {
        System.out.println("Running report");
    }

    public void helper() {
        System.out.println("Not timed");
    }
}

public class TimedRunner {

    public static void main(String[] args) throws Exception {
        ReportService service = new ReportService();

        for (Method method : ReportService.class.getDeclaredMethods()) {
            Timed timed = method.getAnnotation(Timed.class);
            if (timed != null) {
                System.out.println("Label: " + timed.label());
                method.invoke(service);
            }
        }
    }
}
```

`getDeclaredMethods()` does not guarantee an order. If the order matters, sort the methods or use an explicit list.

### Annotation processing at compile time

Annotation processors run during compilation. They read annotations on source elements and can generate new source files or report errors. This is how Lombok generates getters and builders, and how MapStruct generates mapper implementations. Compile-time processing needs `SOURCE` or `CLASS` retention, and it does not cost anything at runtime.

Processors are written against `javax.annotation.processing`, which is part of the `java.compiler` module and keeps the `javax` package name even in newer JDKs.

### What reflection is

Reflection lets code inspect a type (its name, constructors, fields, methods, and annotations) and act on it (create instances, read and write fields, call methods) without knowing those members at compile time. The entry point is `Class`, which you get from `obj.getClass()`, a class literal such as `Foo.class`, or `Class.forName("...")`.

```java
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

class Person {

    private String name;

    public Person() {
        this.name = "unknown";
    }

    public String greet() {
        return "Hello, " + name;
    }
}

public class ReflectionDemo {

    public static void main(String[] args) throws Exception {
        Class<?> type = Person.class;

        Constructor<?> ctor = type.getConstructor();
        Object person = ctor.newInstance();

        Field name = type.getDeclaredField("name");
        name.setAccessible(true);   // Allow access to a private field
        name.set(person, "Asha");

        Method greet = type.getMethod("greet");
        System.out.println(greet.invoke(person)); // Hello, Asha
    }
}
```

The `setAccessible(true)` call breaks encapsulation on purpose. Frameworks use it to inject values into private fields.

### Java modules and strong encapsulation

In Java 16 and later, `setAccessible` on a member of a JDK package that is not opened to your code throws `InaccessibleObjectException`. A library that needs deep reflection into a JDK package must be opened with `--add-opens` on the command line. Application code in the unnamed module is less affected, but this is a common surprise when upgrading an older framework to a newer JDK.

### Reflection on records

Records expose their components through `Class.getRecordComponents()` (Java 16 and later). This is how serializers such as Jackson read record fields without a setter.

```java
record Point(int x, int y) { }

// Point.class.getRecordComponents() returns two components: x and y
```

### Cost and trade-offs

Reflection is slower than a direct call, and it skips compile-time checks. A wrong method name is a runtime `NoSuchMethodException`, not a compile error. Reflection also makes code harder to read and refactor, because IDEs cannot rename a string-based lookup reliably.

Modern JDKs have reduced much of the cost. `MethodHandle` lookups are a faster alternative for hot paths, but for most application code the difference does not matter, and clarity should win.

## How it works / Step by step

How Spring uses these ideas at startup, in simplified form:

1. Classpath scanning finds classes annotated with `@Component`, `@Service`, or similar.
2. For each class, the container reads constructors and fields with reflection, and checks annotations such as `@Autowired`.
3. The container creates instances and injects collaborators through the reflected members.
4. Annotations such as `@Transactional` or `@Cacheable` are applied by a proxy wrapped around the bean (see [AOP](../08-spring-core/aop.md)).

Frameworks do most of this work once, at startup. Runtime cost is usually paid during bean creation, not on each request.

## Common pitfalls

- **Forgetting `RUNTIME` retention.** An annotation with the default `CLASS` retention is not visible to `getAnnotation`, and the lookup returns `null` with no error.
- **Using `getMethods()` when you need private members.** `getMethods()` returns public methods only, including inherited ones. Use `getDeclaredMethods()` for members declared in the class itself.
- **Forgetting `@Inherited` expectations.** Subclasses inherit a class annotation only when `@Inherited` is present, and only for classes.
- **Breaking on private members in new JDKs.** Deep reflection into JDK internals can fail on newer versions. Check for `InaccessibleObjectException`.
- **String-based lookups in refactored code.** Renaming a method does not update `getMethod("oldName")`. Prefer type-safe approaches where you can.

!!! tip "Interview tip"
    "How does Spring know which class is a bean?" Annotations plus classpath scanning. The container reads the annotations with reflection, creates the objects, and injects dependencies. Mention that `@Retention(RUNTIME)` is what makes the annotation visible to that reading.

## Quick recap

- Annotations are metadata; they do nothing until a tool reads them.
- `@Retention` controls visibility: `SOURCE`, `CLASS`, or `RUNTIME`.
- `@Target`, `@Documented`, and `@Inherited` shape how an annotation is used.
- Reflection reads and changes types at runtime through `Class`, `Method`, `Field`, and `Constructor`.
- `setAccessible` breaks encapsulation; Java modules restrict it.
- Reflection is flexible but slower and less safe at compile time.

**See also:** [Java Tools and Utilities](java-tools-utilities.md), [AOP](../08-spring-core/aop.md), [Generics](../02a-core-language/generics.md), [Structural Patterns](../design-patterns/structural-patterns.md)
