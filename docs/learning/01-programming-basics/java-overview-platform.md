# Java Overview and Platform

Java is an object-oriented language that compiles to bytecode and runs on a virtual machine, so the same compiled `.class` files run on any platform that has a matching JVM. Interviewers ask about this layer early because it explains most later answers about memory, performance, and deployment: what the JVM does, how the JDK differs from the JRE, and where garbage collection and class loading fit in.

## Core concepts

### Source, bytecode, and the JVM
Java source code (`.java`) is compiled by `javac` into bytecode (`.class`), an instruction set for a virtual machine rather than for a physical CPU. The JVM loads that bytecode, verifies it, interprets it, and compiles frequently used methods to native code with the just-in-time (JIT) compiler. The bytecode is portable; the JVM is platform-specific. That split is the basis of "write once, run anywhere."

```java
public class PlatformInfo {
    public static void main(String[] args) {
        System.out.println("java.version = " + System.getProperty("java.version"));
        System.out.println("os.name      = " + System.getProperty("os.name"));
    }
}
```

### The platform layers: JVM, JRE, JDK

| Layer | What it contains | Used for |
|---|---|---|
| JVM | The virtual machine: bytecode execution, memory management, threads, garbage collection | Running any Java program |
| JRE | The JVM plus the standard class libraries needed to run programs | Running applications |
| JDK | The JRE plus development tools such as `javac`, `jar`, `javadoc`, and `jshell` | Writing and building programs |

Since Java 9 the JDK includes a modular runtime, and the `jlink` tool can build a slimmed-down runtime image for an application. Separate JRE downloads are much less common today, so in practice you install a JDK.

### Editions
- **Java SE (Standard Edition):** the core language, core libraries, and the JVM. Most of this playbook covers Java SE.
- **Jakarta EE (formerly Java EE):** enterprise APIs for servers, such as servlets and persistence. The project moved to the Eclipse Foundation and was renamed. Its packages moved from `javax.*` to `jakarta.*`.
- **Java ME (Micro Edition):** a platform for embedded and mobile devices. It is now rare.

### Release cadence and LTS
Oracle ships a new feature release every six months, and some releases are designated long-term support (LTS). The roadmap recommends a current LTS release, such as 21 or 25. Feature releases between LTS versions receive only short-term support.

### JVM memory areas
- **Heap:** holds objects and arrays. It is shared by all threads and is managed by the garbage collector.
- **Stack:** each thread has its own stack of method frames. A frame holds local variables and operand data. Very deep recursion ends in a `StackOverflowError`.
- **Metaspace:** holds class metadata. It lives in native memory, not in the Java heap, and replaced PermGen in Java 8.

```java
public class StackDepth {
    static int depth = 0;

    static void recurse() {
        depth++;
        recurse();
    }

    public static void main(String[] args) {
        try {
            recurse();
        } catch (StackOverflowError e) {
            System.out.println("Overflowed after about " + depth + " calls");
        }
    }
}
```

The printed number varies from run to run, because it depends on the stack size and the JVM.

### Garbage collectors
The garbage collector reclaims objects that can no longer be reached from GC roots (such as live stack references and static fields). The main collectors are:

| Collector | Character |
|---|---|
| Serial | Single-threaded; suited to small heaps and simple programs |
| Parallel | Multi-threaded; optimized for throughput |
| CMS | Concurrent mark-sweep; removed in Java 14 |
| G1 | Region-based; the default collector since Java 9; aims for pause-time goals |
| ZGC | Low-latency collector; production-ready since Java 15 |

Common tuning flags:

```text
java -Xms512m -Xmx2g -XX:+UseG1GC -Xlog:gc* MyApp
java -XX:+UseZGC MyApp
```

`-Xms` sets the initial heap size and `-Xmx` sets the maximum. `-Xlog:gc*` writes unified GC logs (JDK 9 and later). When reading a GC log, look at pause durations, how much heap each collection frees, and how often full collections happen. Frequent full collections usually mean the heap is too small or the application keeps too many objects alive.

### Class loading
Classes are loaded on demand by class loaders, which form a hierarchy:

| Loader | Loads | Notes |
|---|---|---|
| Bootstrap | Core JDK classes | Implemented inside the JVM; `getClassLoader()` returns `null` for these classes |
| Platform | Remaining JDK platform modules | Called the Extension loader before Java 9 |
| Application | Your classes from the classpath or module path | The loader that runs `main` |

Loaders use **parent delegation**: a loader asks its parent to load a class first, and only loads it itself if the parent cannot. This is why application code cannot replace `java.lang.String` with its own version.

```java
public class LoaderDemo {
    public static void main(String[] args) {
        System.out.println(LoaderDemo.class.getClassLoader()); // application loader
        System.out.println(String.class.getClassLoader());     // null: bootstrap loader
    }
}
```

### Modules (brief)
Java 9 introduced the Java Platform Module System (JPMS). A module declares what it needs and what it exposes in a `module-info.java` file, which gives strong encapsulation beyond the access modifiers.

```java
module com.example.orders {
    requires java.net.http;
    exports com.example.orders.api;
}
```

Packages that are not exported are not visible to other modules, even if their classes are `public`.

## How it works / Step by step

1. `javac` compiles each `.java` file into one or more `.class` files containing bytecode.
2. `java` starts the JVM, which creates the heap and the main thread's stack.
3. The bootstrap loader loads core classes. The application loader loads your classes, using parent delegation.
4. The JVM verifies the bytecode and starts interpreting it.
5. Frequently executed methods are compiled to native code by the JIT compiler.
6. Objects are allocated on the heap. The garbage collector reclaims those that are no longer reachable.

## Common pitfalls
- Assuming a JRE is enough to compile code. Compiling needs the JDK.
- Thinking Metaspace is part of the heap. It lives outside the Java heap, in native memory.
- Believing garbage collection prevents all memory leaks. An object kept alive by a static field, a cache, or a listener is never collected.
- Choosing a collector flag from old articles. CMS was removed in Java 14, and G1 is the default.
- Importing `javax.*` packages in Jakarta EE 9 and later code, which expects `jakarta.*`.

!!! tip "Interview tip"
    **Q: Why is Java both compiled and interpreted?** Compilation to bytecode happens once, ahead of time with `javac`. The JVM then interprets bytecode and JIT-compiles hot methods at run time, using profiling data that a static compiler does not have. You get portability and runtime optimization, at the cost of some startup time.

## Quick recap
- The JDK contains the compiler and tools, the JRE runs programs, and the JVM executes bytecode.
- The heap holds objects, each thread has its own stack, and Metaspace holds class metadata.
- G1 is the default collector; CMS was removed in Java 14.
- Class loaders delegate to their parent first, which protects core classes.
- Java SE is the core edition; Jakarta EE is the enterprise edition.

**See also:** [Environment Setup](environment-setup.md), [Syntax Basics](syntax-basics.md), [Git, IDEs and Command-Line Tools](git-ide-tools.md)
