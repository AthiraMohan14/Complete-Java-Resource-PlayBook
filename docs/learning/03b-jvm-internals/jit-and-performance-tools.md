# JIT Compilation and Performance Tools

The just-in-time (JIT) compiler turns frequently executed bytecode into native machine code while the program runs. Class Data Sharing (CDS) cuts startup time by sharing pre-parsed class metadata, and JMH is the standard harness for measuring code correctly. Interviewers ask about these topics to see whether you can explain why Java gets faster after warm-up and how you would diagnose a slow service without guessing.

---

## Core concepts

### Interpreter first, then compiled code

The JVM does not compile everything up front. It starts by interpreting bytecode, which is quick to start but slow to run. It counts how often each method and loop runs. When a method becomes "hot", the JIT compiles it to machine code and replaces the interpreted version with the compiled one.

This is why the first requests to a Java service are slower than later ones. The period before compiled code is ready is called **warm-up**.

### Tiered compilation: C1 and C2

Since Java 8, HotSpot uses **tiered compilation** by default, with two compilers:

| Compiler | Name | Goal | Behaviour |
|---|---|---|---|
| C1 | Client compiler | Fast compilation | Quick, light optimisations, adds profiling counters |
| C2 | Server compiler | Peak performance | Slower to compile, aggressive optimisations based on profiling data |

Execution moves through tiers. Code starts in the interpreter, moves to C1 with profiling, and the hottest code is later recompiled by C2. If an assumption made by C2 becomes false (for example, a class is loaded that breaks an inlining decision), the JVM **deoptimises** the code and falls back to a lower tier.

### What the optimiser does

The JIT makes decisions using runtime profiles. Common optimisations include:

- **Inlining:** replacing a method call with the method body, so the call overhead and the boundary disappear.
- **Loop optimisations:** unrolling and hoisting invariant computations out of loops.
- **Escape analysis:** proving that an object never leaves a method, so it can be allocated on the stack or eliminated. This is decided by the JVM and you cannot force it.
- **Dead code elimination:** removing computations whose results are never used.
- **Devirtualisation:** turning a virtual call into a direct call when only one implementation has been seen.

```java
public class HotLoop {
    static long sumOfSquares(int n) {
        long total = 0;
        for (int i = 0; i < n; i++) {
            total += (long) i * i;
        }
        return total;
    }

    public static void main(String[] args) {
        long result = 0;
        for (int round = 0; round < 1_000; round++) {   // sumOfSquares becomes hot and is compiled
            result += sumOfSquares(10_000);
        }
        System.out.println("result = " + result);
    }
}
```

To watch compilation happen, add `-XX:+PrintCompilation`. Each line shows a method being compiled at a given tier. The output format is version-specific, so use it to see that compilation occurs rather than to parse exact text.

### The code cache

Compiled machine code is stored in the **code cache**, a separate native memory area. If it fills up, the JVM stops compiling and prints a warning, and the application can become much slower. Its size can be set with `-XX:ReservedCodeCacheSize`. You rarely need to change it, but a `CodeCache is full` message is worth investigating.

### Class Data Sharing (CDS)

Loading and verifying classes costs startup time. CDS stores the parsed form of classes in an archive file that the JVM maps into memory at start-up.

- The JDK ships a **default CDS archive** for its own classes. It is used automatically.
- **Application CDS (AppCDS)** extends this to your application's classes.

Create and use an AppCDS archive:

```bash
java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar com.example.Main   # run once to record the archive
java -XX:SharedArchiveFile=app.jsa -cp app.jar com.example.Main      # later runs use it
```

The benefit is faster startup and lower memory for many small classes, which matters for short-lived processes such as command-line tools and serverless functions. The archive must match the JDK and the class path it was created with.

### Ahead-of-time options

Class Data Sharing and the JIT are not the only tools for startup. GraalVM native image compiles an application ahead of time to a standalone executable, trading some peak throughput and build time for very fast startup. It is a separate product with its own constraints (for example, reflection needs configuration), so mention it as an option rather than a default.

### JMH: measuring correctly

Writing your own timing loop with `System.nanoTime()` usually gives wrong numbers. Reasons include warm-up, dead code elimination, and constant folding. The **Java Microbenchmark Harness (JMH)** handles warm-up, forks a fresh JVM, and prevents the JIT from removing the work.

```java
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;

// Compiles with the jmh-core dependency and its annotation processor on the build path.
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Thread)
public class ConcatBenchmark {
    private final String a = "hello";
    private final String b = "world";

    @Benchmark
    public String concatWithPlus() {
        return a + " " + b;             // returning the result stops the JIT from discarding the work
    }

    @Benchmark
    public String concatWithBuilder() {
        return new StringBuilder(a).append(' ').append(b).toString();
    }
}
```

JMH generates a main class from these annotations. Run it through the JMH uber-jar produced by your build tool, and read the reported average time and error margin. Results depend on hardware, JDK version, and load, so compare variants run on the same machine.

### Diagnostic and profiling tools

| Tool | What it does | Example |
|---|---|---|
| `jcmd` | Swiss-army knife for a running JVM: thread dumps, heap dumps, flags, JFR control | `jcmd <pid> VM.flags`, `jcmd <pid> Thread.print` |
| `jstat` | Periodic counters for GC and class loading | `jstat -gc <pid> 1000` (every second) |
| `jmap` | Heap histograms and heap dumps | `jmap -histo:live <pid>` |
| `jstack` | Thread dump: what each thread is doing and which locks it holds | `jstack <pid>` |
| `jconsole` | Basic JMX graphical monitor shipped with the JDK | Launch and attach to a process |
| VisualVM | Graphical profiler and monitor; a separate download from the JDK | Heap, CPU, and thread views |
| Java Flight Recorder (JFR) | Low-overhead event recording, analysed in JDK Mission Control | `jcmd <pid> JFR.start duration=60s filename=rec.jfr` |

Start a recording at launch:

```bash
java -XX:StartFlightRecording=duration=60s,filename=rec.jfr -jar app.jar
```

Open `rec.jfr` in JDK Mission Control. It shows allocation hot spots, GC pauses, lock contention, and method profiles with little overhead, which makes it suitable for production.

### Heap dumps and OutOfMemoryError

Ask the JVM to write a heap dump when it runs out of memory:

```bash
java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=dumps -jar app.jar
```

Open the dump in a tool such as Eclipse MAT or VisualVM to find which objects are retained and what keeps them alive. The "dominator tree" or "path to GC root" view is usually where a leak becomes obvious. You can also take one on demand with `jcmd <pid> GC.heap_dump <file>`.

### A diagnostic workflow

When a service is slow, a reliable order of checks is:

1. Confirm the symptom with metrics: latency percentiles, CPU, heap, and GC pause time.
2. Take a few thread dumps (`jstack` or `jcmd Thread.print`) a few seconds apart. Threads that stay in the same state point to a bottleneck such as a lock or a blocking call.
3. Check GC behaviour (`jstat -gc` or GC logs; see [Garbage Collection](garbage-collection.md)).
4. Record with JFR for allocation and CPU hot spots.
5. Change one thing, measure again, and keep only changes that improve the metric you care about.

---

## How it works / Step by step

1. The class loader loads a class, and the interpreter starts running its bytecode.
2. The JVM profiles invocation counts and branch behaviour.
3. A method crossing a threshold is queued for C1 compilation with profiling.
4. Very hot code is recompiled by C2 using the profile, with inlining and other optimisations.
5. If an assumption breaks, the JVM deoptimises the method and returns to the interpreter or a lower tier.
6. Compiled code lives in the code cache; the interpreter handles anything not yet compiled.

| Phase | Typical cost | Notes |
|---|---|---|
| Interpreted | Slowest | Used at first and for cold code |
| C1 | Medium | Fast to produce, profiles for C2 |
| C2 | Fastest | Built from profiles; may take time to compile |

---

## Common pitfalls

- Benchmarking with a hand-written loop and `System.nanoTime()` and trusting the numbers. Use JMH, and return or consume the results.
- Measuring only the first few seconds of a service. Include warm-up before you compare.
- Running with `-Xint` (interpreter only) to "see the real cost". The result describes an unrealistic configuration.
- Assuming escape analysis will remove an allocation you want removed. The JVM decides, and it may change between versions.
- Ignoring the `CodeCache is full` warning.
- Taking a single thread dump and drawing conclusions. Take several to see what is stuck.
- Creating an AppCDS archive with one JDK and running with another. The archive is rejected or ignored.
- Using `System.gc()` before a measurement. It adds a collection that the real workload would not have had.

!!! tip "Interview tip"
    **Q: Why does a Java service get faster after it has been running for a while?**
    The JVM starts by interpreting bytecode, then profiles it. Hot methods are compiled by C1 and, if they stay hot, by C2 using the runtime profile. Inlining, loop optimisation, and devirtualisation then apply. This is why benchmarks need warm-up and why the first requests after a deploy are slower.

    **Follow-up: How would you find out why a service is slow in production?**
    Start with metrics to confirm where the time goes. Then take a few thread dumps with `jstack` or `jcmd`, check GC pauses with `jstat -gc` or GC logs, and record a JFR file for hot spots. Change one thing at a time and measure again.

## Quick recap

- The JVM interprets first, then compiles hot code with C1 and C2 using runtime profiles (tiered compilation is the default).
- CDS, including AppCDS, stores pre-parsed classes to reduce startup time.
- JMH handles warm-up and dead code elimination, which makes it the right tool for microbenchmarks.
- `jcmd`, `jstat`, `jmap`, `jstack`, `jconsole`, VisualVM, and JFR cover most production diagnosis.
- Diagnose with evidence: metrics first, then thread dumps, GC data, and recordings, and change one thing at a time.

**See also:** [JVM Architecture and Memory](jvm-architecture-memory.md), [Garbage Collection](garbage-collection.md), [Class Loading](class-loading.md), [JVM Internals index](index.md)
