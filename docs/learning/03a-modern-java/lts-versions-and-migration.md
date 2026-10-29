# Java LTS Versions and Migration

Oracle ships a feature release every six months, and a few of those releases are designated long-term support (LTS). Interviewers ask which version a team should run, which features made each LTS important, and how to move a codebase from one LTS to the next without breaking production.

## Core concepts

### Release cadence and LTS
Since Java 9 a new feature release arrives every six months. Only some releases are LTS, roughly one every two to three years. The LTS lines that matter most for interviews are 8, 11, 17, and 21. Later LTS releases such as 25 follow the same model; check the release notes for the version you target.

Feature releases that are not LTS receive updates only for a short overlap period, so production systems should sit on an LTS line.

### Support windows
The table below uses Oracle's published end-of-support dates for Oracle JDK builds. Vendors such as Eclipse Temurin, Amazon Corretto, and Microsoft build OpenJDK with their own, often longer, schedules. Verify dates on the vendor's site before making a decision.

| LTS | Released | Oracle extended support ends |
|---|---|---|
| Java 8 | March 2014 | December 2030 |
| Java 11 | September 2018 | September 2026 |
| Java 17 | September 2021 | September 2029 |
| Java 21 | September 2023 | September 2031 |

As of this page's date, Java 11 is past the Oracle end date in the table, so new production work should use a newer LTS.

### Release timeline
The timeline lists the features an interviewer is most likely to ask about. Preview features are noted because they are not part of the language until finalized.

| Version | Year | Headline features |
|---|---|---|
| 1.0 | 1996 | Classes, objects, interfaces, and the JVM |
| 1.2 | 1998 | Collections Framework, Swing |
| 1.4 | 2002 | `assert`, regular expressions, NIO |
| 5 | 2004 | Generics, enums, autoboxing, enhanced `for`, annotations |
| 7 | 2011 | try-with-resources, diamond operator, multi-catch |
| 8 | 2014 | Lambdas, Stream API, `java.time`, default methods (LTS) |
| 9 | 2017 | Module system (JPMS), JShell, private interface methods |
| 10 | 2018 | `var` for local variable type inference |
| 11 | 2018 | Standard HTTP client, single-file source launch, Java EE modules removed (LTS) |
| 14 | 2020 | Switch expressions standard, records and `instanceof` patterns as previews |
| 15 | 2020 | Text blocks standard, Nashorn removed, sealed classes as preview |
| 16 | 2021 | Records standard, `instanceof` pattern matching standard |
| 17 | 2021 | Sealed classes standard, strong encapsulation of JDK internals (LTS) |
| 18 | 2022 | UTF-8 as the default charset |
| 19 | 2022 | Record patterns and `switch` patterns as previews |
| 21 | 2023 | Virtual threads, record patterns, `switch` pattern matching, sequenced collections (LTS) |
| 22 | 2024 | Foreign Function and Memory API and unnamed variables finalized |
| 23 | 2024 | String templates withdrawn; primitive types in patterns as a preview |

Two removals are worth remembering. CMS, the old concurrent collector, was removed in Java 14. Nashorn, the JavaScript engine, was deprecated in 11 and removed in 15.

## Migration path: 8, 11, 17, 21

Migrate one LTS at a time: 8 to 11, then 11 to 17, then 17 to 21. Each step is smaller than jumping several versions at once, and it gives you a clear point to test and roll back.

### Java 8 to Java 11 (lowest effort)
**What breaks**

- The Java EE and CORBA modules were removed (JEP 320). This includes JAXB, JAX-WS, and the JavaBeans Activation Framework. Add them back as separate libraries if your code uses them.
- The `rmic` tool was removed. RMI itself remains in the JDK.
- Nashorn is deprecated, and it is removed in 15. Plan a replacement if you embed JavaScript.

**What works without change**

- Lambdas and streams are the same API.
- `var` is available but optional.
- The threading model is unchanged.

Replacing an old URL-reading idiom with the standard HTTP client is a common first change:

```java
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class FetchPage {
    public static void main(String[] args) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://example.com/")).build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println(response.statusCode());
    }
}
```

### Java 11 to Java 17 (moderate effort)
**What breaks**

- Strong encapsulation: code that reflects into JDK internals, such as `sun.misc.Unsafe` or private fields in `java.base`, fails. The `--illegal-access` flag that allowed it was removed in 17.
- Code that depends on removed APIs needs a replacement.

**What is new and worth adopting**

- Records (standard in 16) replace hand-written data classes.
- `instanceof` pattern matching (standard in 16) removes a cast after a type check.
- Sealed classes (standard in 17) restrict which classes may extend a type.
- Text blocks (standard in 15) make multi-line strings readable.

```java
public record User(String name, int age) { }

public class Greeting {
    static String describe(Object obj) {
        if (obj instanceof User user) {          // pattern variable, no cast
            return user.name() + " (" + user.age() + ")";
        }
        return "not a user";
    }
}
```

Record deconstruction patterns such as `obj instanceof User(String name, int age)` are a Java 21 feature. They do not compile on 17.

To find code that touches JDK internals, run the dependency analyzer on the built jar:

```bash
jdeps -jdkinternals myapp.jar
```

### Java 17 to Java 21 (low effort)
**What breaks**

- Very little. Java 21 is largely source-compatible with 17, so most work is evaluation rather than repair.

**What is new**

- Virtual threads (final in 21) are lightweight threads scheduled by the JVM. They suit I/O-bound code where each request blocks while it waits.
- Record patterns and `switch` pattern matching (final in 21) handle nested data cleanly. Sealed types let the compiler check that a `switch` is exhaustive.
- Sequenced collections give a common API for the first and last element of ordered collections.

A thread-per-task executor shows the change in style:

```java
import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.IntStream;

public class VirtualThreadsDemo {
    public static void main(String[] args) {
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            IntStream.range(0, 10_000).forEach(i ->
                executor.submit(() -> {
                    Thread.sleep(Duration.ofMillis(100));   // blocking call, cheap on a virtual thread
                    return i;
                }));
        }   // close() waits for all submitted tasks
    }
}
```

A fixed pool of platform threads limits how many blocking tasks run at once. A virtual thread that blocks costs little, so the pool bound goes away.

Two cautions for Java 21 adoption:

- Virtual threads help blocking I/O. They do not make CPU-bound code faster.
- In Java 21, a virtual thread that blocks inside a `synchronized` block pins its carrier thread. Prefer `ReentrantLock` in hot blocking paths, and check the JDK release notes for later fixes.

## Decision guide

- New project: start on the newest LTS that your frameworks and libraries support, which is 21 at the time of writing or a later LTS.
- Existing Java 8 service: move to 11 first, test, then continue to 17 and 21.
- Latency-sensitive I/O service: 21 with virtual threads is the strongest option.
- Need sealed hierarchies and exhaustive pattern matching: 17 is the minimum.

## Migration practice

1. Compile with the target release, using `--release` for javac or `<maven.compiler.release>` in Maven, so the compiler rejects APIs that are not in the target.
2. Run the full test suite and any integration tests on the new JDK.
3. Scan for internal API use with `jdeps`.
4. Run the new version in staging with production-like load. Compare latency and GC behaviour, not only pass or fail.
5. Roll out gradually and keep the old JDK available until the new one has run cleanly.

### Troubleshooting
- `NoSuchMethodError` at run time, for an API that exists in the source, often means the code was compiled with a newer JDK than the runtime. Compile with `--release` set to the runtime version.
- `InaccessibleObjectException` or an illegal reflective access error means code reflects into JDK internals. Replace the call with a public API, or open the package explicitly as a last resort.
- `NoClassDefFoundError` for `javax.xml.bind` or similar classes means a module was removed. Add the replacement library. Note that Jakarta EE 9 and later use `jakarta.*` package names.

## Interview tip

**Q: Which LTS would you choose for a new service, and why?** Pick the newest LTS that your frameworks support, currently 21 or a later LTS. It gives records, sealed types, pattern matching, and virtual threads. If the team is stuck on Java 8, the upgrade path is 8 to 11 to 17 to 21, testing at each step. Name the support end date in your answer, because it decides how long you can run without an upgrade.

## Quick recap
- LTS releases are 8, 11, 17, and 21 in the interview canon; later LTS releases such as 25 follow the same model.
- Java 11 removed the Java EE and CORBA modules. Nashorn was removed in 15.
- Records, pattern matching for `instanceof`, sealed classes, and text blocks arrive between 15 and 17.
- Record deconstruction patterns and `switch` patterns are Java 21 features; virtual threads are final in 21.
- Migrate one LTS at a time, compile with `--release`, and check for internal API use with `jdeps`.

**See also:** [Java Overview and Platform](../01-programming-basics/java-overview-platform.md), [Java 9 to 17 Features](java9-to-17-features.md), [Java 21 Features](java21-features.md), [Optional and Functional Interfaces](optional-functional-interfaces.md)
