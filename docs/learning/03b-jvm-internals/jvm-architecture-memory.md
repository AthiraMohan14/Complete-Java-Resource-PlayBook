# JVM Architecture and Memory

The Java Virtual Machine (JVM) is the runtime that executes Java bytecode. It loads classes, manages memory, runs garbage collection, and compiles hot code to native machine instructions. Interviewers ask about the JVM memory model because most real Java problems (OutOfMemoryError, StackOverflowError, memory leaks, slow pauses) come from misunderstanding where data lives and who frees it.

---

## Core concepts

### From source code to bytecode

Java source files (`.java`) are compiled by `javac` into bytecode (`.class` files). Bytecode is a platform-neutral instruction set. Any JVM that supports the class file version can run it, which is the basis of "write once, run anywhere."

```java
// Hello.java
public class Hello {
    public static void main(String[] args) {
        int sum = 2 + 3;
        System.out.println("sum = " + sum);
    }
}
```

```bash
javac Hello.java        # produces Hello.class
javap -c Hello          # disassembles the bytecode so you can read it
java Hello              # starts the JVM, loads Hello.class, runs main
```

`javap -c` shows instructions such as `iconst_2`, `iconst_3`, `iadd`, which are stack-based operations. The JVM interprets these instructions at first and compiles hot ones to machine code later (see [JIT Compilation](jit-and-performance-tools.md)).

### JVM, JRE and JDK

| Term | What it is | Contains |
|---|---|---|
| JVM | The virtual machine that runs bytecode | Class loaders, interpreter, JIT, garbage collector |
| JRE | Runtime environment (older packaging) | JVM plus core libraries |
| JDK | Development kit | JRE plus `javac`, `jshell`, `jar`, `javadoc`, and diagnostic tools |

Current JDK distributions do not ship a separate JRE. You install a JDK, which includes everything needed to run and build programs.

### Runtime data areas

The JVM divides memory into areas. The ones that matter in interviews are:

| Area | Shared or per thread | What it stores | Typical error |
|---|---|---|---|
| Heap | Shared by all threads | All objects and arrays | `OutOfMemoryError: Java heap space` |
| Thread stack | One per thread | Stack frames: local variables, operand stack, method call data | `StackOverflowError` |
| Metaspace | Shared (native memory) | Class metadata: method and field info, constant pool | `OutOfMemoryError: Metaspace` |
| Program counter (PC) register | One per thread | Address of the current bytecode instruction | (none in practice) |
| Native method stack | One per thread | Frames for native (JNI) code | `StackOverflowError` in native code |
| Code cache | Shared | JIT-compiled machine code | `CodeCache is full` warning |

### Heap vs stack

The heap holds objects. The stack holds method frames. Each method call pushes a frame that contains its local variables and parameters. When the method returns, the frame is popped and its locals disappear.

```java
public class HeapVsStack {
    static int counter = 0;                 // static field: lives with the class (Metaspace reference, value in heap)

    public static void main(String[] args) {
        int local = 42;                     // primitive local: stored in main's stack frame
        StringBuilder sb = new StringBuilder("hi"); // reference "sb" is on the stack; the object is on the heap
        helper(sb);
        System.out.println(local + " " + sb);
    }

    static void helper(StringBuilder ref) {
        ref.append("!");                    // changes the object on the heap; the caller sees it
        counter++;
    }
}
```

Key points:

- Local variables of primitive type hold the value directly in the stack frame.
- Local variables of reference type hold a pointer to an object on the heap.
- Passing a reference copies the pointer, not the object. Java is always pass-by-value; for objects, the value copied is the reference.
- Objects on the heap survive until no reference reaches them, then the garbage collector reclaims them.

### Stack frames and StackOverflowError

Each thread has a fixed-size stack. Deep or unbounded recursion fills it and throws `StackOverflowError`.

```java
public class DeepRecursion {
    static int depth = 0;

    static void recurse() {
        depth++;
        recurse();                          // no base case: each call adds a frame
    }

    public static void main(String[] args) {
        try {
            recurse();
        } catch (StackOverflowError e) {
            System.out.println("Caught StackOverflowError: " + (depth > 0));
        }
    }
}
```

The exact depth varies by platform and JVM flags, so the example prints a boolean rather than a number. You can change the per-thread stack size with `-Xss`, for example `-Xss512k`. A larger value allows deeper recursion but uses more memory per thread.

### The heap in more detail

The heap is divided into generations in the default collectors:

- **Young generation:** new objects are allocated here. It is further split into an Eden space and survivor spaces. Most objects die young, so collecting this area is cheap and frequent (a "minor GC").
- **Old generation (tenured):** objects that survive several young collections are promoted here. Collecting it is more expensive (a "major" or "full" GC, depending on the collector).

Some collectors do not use this split in the same way. ZGC and Shenandoah use region-based or non-generational designs (ZGC gained a generational mode in Java 21). Choose the collector first, then read its memory layout.

Heap size is set with:

```bash
java -Xms512m -Xmx2g MyApp   # initial heap 512 MB, maximum heap 2 GB
```

Setting `-Xms` equal to `-Xmx` avoids resizing pauses and is common for server applications.

### Metaspace replaced PermGen

Before Java 8, class metadata lived in an area called PermGen, inside the heap, with a fixed maximum size. Applications that loaded many classes (application servers, code generators, frequent redeploys) hit `OutOfMemoryError: PermGen space`.

Java 8 removed PermGen and introduced Metaspace. Metaspace lives in native (off-heap) memory and grows as needed, so it is limited by the operating system rather than a fixed heap region.

```bash
java -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=256m MyApp
```

- `MetaspaceSize` is the initial size that triggers a GC when reached. It is not a hard cap.
- `MaxMetaspaceSize` is the hard upper limit. Without it, Metaspace can consume native memory until the machine runs out.

If you see a steady increase in Metaspace, suspect a class-loader leak: classes loaded by a redeployed web application that stay referenced from a long-lived object.

### Memory model (Java Memory Model)

The Java Memory Model (JMM) defines how threads see each other's writes. Without synchronization, a thread may see stale values or writes may appear out of order. The JMM provides rules through `synchronized`, `volatile`, and `final` fields. The concurrency pages cover these in detail (see [Synchronisation and volatile](../02c-concurrency-io/synchronisation-volatile.md)).

The JMM is about visibility and ordering between threads. It is separate from the heap and stack layout, though both are sometimes called "memory model" in casual conversation.

### Inspecting memory at runtime

```java
public class MemoryStats {
    public static void main(String[] args) {
        Runtime rt = Runtime.getRuntime();
        long mb = 1024L * 1024L;
        System.out.printf("max=%d MB, total=%d MB, free=%d MB, cpus=%d%n",
                rt.maxMemory() / mb,
                rt.totalMemory() / mb,
                rt.freeMemory() / mb,
                rt.availableProcessors());
    }
}
```

`maxMemory()` reflects `-Xmx`. `totalMemory()` is the heap currently reserved by the JVM, and `freeMemory()` is the part of it that is unused. These numbers are a quick sanity check; for real diagnosis use the tools in [JIT Compilation and Performance Tools](jit-and-performance-tools.md).

---

## How it works / Step by step

1. `javac` compiles `.java` files into `.class` files containing bytecode.
2. `java` starts the JVM and creates the main thread with its own stack.
3. The class loader loads `Main.class` and its dependencies, creating Metaspace entries for each class (see [Class Loading](class-loading.md)).
4. `main` runs. Each method call pushes a frame on the current thread's stack.
5. Each `new` allocates an object in the young generation of the heap.
6. When memory runs low, the garbage collector finds objects no longer reachable from any live reference (GC roots: thread stacks, static fields, JNI references) and reclaims them (see [Garbage Collection](garbage-collection.md)).
7. Hot methods are compiled to machine code by the JIT compiler and stored in the code cache.

| Symptom | Likely area | First thing to check |
|---|---|---|
| `OutOfMemoryError: Java heap space` | Heap | Heap dump (object histogram) and `-Xmx` |
| `StackOverflowError` | Thread stack | Recursion depth and `-Xss` |
| `OutOfMemoryError: Metaspace` | Metaspace | Class count and class-loader leaks |
| `OutOfMemoryError: unable to create native thread` | Native memory and thread count | Number of threads and `-Xss` |

---

## Common pitfalls

- Assuming that a local object lives on the stack. The reference lives on the stack; the object is on the heap. (Escape analysis can sometimes allocate objects on the stack, but that is an optimisation the JVM decides, not something you control.)
- Increasing `-Xmx` to fix a leak. A bigger heap only delays the failure if objects are still referenced.
- Creating unbounded recursion without a base case, then blaming the stack size.
- Leaving `MaxMetaspaceSize` unset in containers and then being killed by the container memory limit.
- Treating the Java Memory Model and the memory layout as the same topic.
- Using `Runtime.freeMemory()` as a measure of how much memory the application really needs. The JVM only reports what it has reserved right now.

!!! tip "Interview tip"
    **Q: What is the difference between heap and stack?**
    The heap is shared by all threads and holds objects and arrays; the garbage collector reclaims it. Each thread has its own stack that holds method frames, local variables, and references. Stack memory is released automatically when a method returns, so it does not need garbage collection.

    **Follow-up: Why did Java 8 replace PermGen with Metaspace?**
    PermGen was a fixed-size area inside the heap, so applications that loaded many classes ran out of space. Metaspace uses native memory that grows as needed, which removes most of those failures. It can still be capped with `-XX:MaxMetaspaceSize`.

## Quick recap

- Bytecode is produced by `javac` and run by the JVM; the JVM can interpret it or JIT-compile it.
- The heap holds objects and is shared; each thread has its own stack of frames.
- A reference is stored on the stack or in an object, while the object itself is on the heap.
- Metaspace (native memory) holds class metadata and replaced PermGen in Java 8.
- `-Xms`, `-Xmx`, `-Xss`, `-XX:MetaspaceSize`, and `-XX:MaxMetaspaceSize` control the main memory areas.

**See also:** [Garbage Collection](garbage-collection.md), [Class Loading](class-loading.md), [JIT Compilation and Performance Tools](jit-and-performance-tools.md), [JVM Internals index](index.md)
