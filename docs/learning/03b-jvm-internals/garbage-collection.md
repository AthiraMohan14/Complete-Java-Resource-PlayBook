# Garbage Collection

Garbage collection (GC) is the JVM's automatic reclamation of heap memory that the program can no longer reach. Interviewers ask about GC to test whether you know how objects become garbage, which collector to pick for a workload, and how to tell from logs whether the collector is the cause of a slowdown.

---

## Core concepts

### Reachability: what counts as garbage

An object is garbage when no live reference chain connects it to a **GC root**. GC roots include:

- local variables and parameters on each thread's stack
- static fields of loaded classes
- JNI global references and active monitors (locks held by threads)

The collector starts from the roots and marks everything it can reach. Unmarked objects are garbage.

```java
public class Reachability {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder("temporary");
        System.out.println(sb.length());
        sb = null;      // the object is now unreachable; the GC may reclaim it later
        System.out.println("done");
    }
}
```

Setting a reference to `null` does not free memory immediately. It only makes the object eligible for collection.

### Generational hypothesis

Most objects die young. Many short-lived objects are created by request handling, iterators, and temporary strings. The generational design takes advantage of this:

- New objects go into the **young generation** (Eden and survivor spaces).
- A **minor GC** collects the young generation. It is frequent and fast.
- Objects that survive enough minor GCs are promoted to the **old generation**.
- A **major GC** (or full GC) collects the old generation. It is slower and causes longer pauses in most collectors.

### Stop-the-world pauses and concurrent work

Many collector phases must pause application threads so that the object graph does not change while it is traversed. These are **stop-the-world (STW)** pauses. Modern collectors do most of their marking and copying concurrently with the application and only pause briefly. The main trade-off is between:

- **Throughput:** the share of time the application runs versus time spent in GC.
- **Latency:** the length of each pause.
- **Footprint:** the memory the collector needs on top of live data.

You cannot optimise all three at once. The collector you choose sets the balance.

### The collectors in the JDK

| Collector | Flag | Design | Strength | Trade-off |
|---|---|---|---|---|
| Serial | `-XX:+UseSerialGC` | Single-threaded, stop-the-world | Small footprint; good for tiny heaps and single-CPU containers | Long pauses on large heaps |
| Parallel | `-XX:+UseParallelGC` | Multi-threaded stop-the-world | High throughput for batch jobs | Pauses scale with heap size |
| G1 | `-XX:+UseG1GC` | Region-based, mostly concurrent, pause-time goal | Balanced throughput and latency; default since Java 9 | More CPU and memory overhead than Parallel |
| ZGC | `-XX:+UseZGC` | Region-based, concurrent compaction, very low pauses | Pauses that stay low as heap grows | Uses more memory and CPU overhead |
| Epsilon | `-XX:+UseEpsilonGC` (experimental; needs `-XX:+UnlockExperimentalVMOptions`) | No-op collector; allocates but never frees | Performance tests and measuring allocation cost | Runs out of memory when the heap is full |

Shenandoah is another low-pause collector available in some OpenJDK builds. It is not part of every JDK distribution, so check your vendor before relying on it.

### Default collector by Java version

When you do not pass a collector flag, the JVM picks one based on the machine it runs on. "Server-class" means at least two CPUs and about 2 GB of memory, which covers most servers and containers you will deploy to.

| Java version | Default collector (server-class machine) | Notes |
|---|---|---|
| Java 8 | Parallel GC | On small or single-CPU machines the JVM picks Serial GC instead |
| Java 9 | G1 | G1 became the default with JEP 248 |
| Java 11 | G1 | Unchanged from Java 9 |
| Java 17 | G1 | Unchanged |
| Java 21 | G1 | Unchanged; virtual threads change how many threads an app runs, not which collector is the default |

If you move a service from Java 8 to a newer JDK, measure pauses again. The same heap settings can behave differently under G1, which is tuned for pause time rather than raw throughput.

### CMS was removed

The Concurrent Mark Sweep (CMS) collector was deprecated in Java 9 and removed in Java 14. Its replacement is G1. Launch scripts that still pass `-XX:+UseConcMarkSweepGC` fail on a current JDK, so they need to be updated.

### G1 in more detail

G1 divides the heap into equal-sized regions. Each region can be an Eden, survivor, old, or humongous region (for very large objects). G1 chooses which regions to collect based on how much garbage they hold, which is where the name "garbage first" comes from.

You give G1 a pause-time goal, and it tries to meet it:

```bash
java -XX:+UseG1GC -XX:MaxGCPauseMillis=200 MyApp
```

`MaxGCPauseMillis` is a goal, not a guarantee. If the goal is too aggressive for the live data, G1 may run longer pauses or fall back to a full collection.

### G1 phases

G1 does not run one big cycle. It alternates short young pauses with a background marking cycle, then uses mixed pauses to reclaim old regions a few at a time.

| Phase | Stops application threads? | What happens |
|---|---|---|
| Young GC | Yes, briefly | Live objects in Eden and survivor regions are copied to survivor or old regions. The collector also starts concurrent marking when old-generation occupancy passes `InitiatingHeapOccupancyPercent` (default 45). |
| Concurrent mark | No, runs alongside the application | Traces the live object graph from the GC roots. The first step, initial mark, is done inside a young pause. |
| Remark | Yes, briefly | Finishes marking using the snapshot taken at the start of the cycle, and identifies regions that are now empty or nearly empty. |
| Cleanup | Mostly a short pause | Records live-data totals for each old region and frees regions that hold no live objects. It does not compact the heap; copying happens in evacuation pauses. |
| Mixed GC | Yes | Evacuates all young regions together with the old regions that hold the most garbage, so old space is reclaimed in small steps. |

In normal operation the sequence is: young pauses, then a marking cycle (concurrent mark, remark, cleanup), then several mixed pauses, then young pauses again. If young collections cannot keep up while marking is running, G1 can fall back to a full stop-the-world collection.

### ZGC in more detail

ZGC aims for pauses that stay below a millisecond or so, independent of heap size. It does most work concurrently, including relocating live objects. It uses colored pointers and load barriers to keep the application consistent while objects move.

```bash
java -XX:+UseZGC -Xmx16g MyApp
```

ZGC is a good fit for latency-sensitive services with large heaps. For small heaps with a throughput goal, Parallel or G1 is often a better choice. Measure before switching.

### Choosing a collector

A rough guide, to be confirmed by measurement:

- Small container, one CPU, small heap: Serial.
- Batch job where total runtime matters more than pause length: Parallel.
- General-purpose service, default choice: G1.
- Latency-sensitive service where pauses must stay short even with a large heap: ZGC.

The JVM picks a default collector based on the machine. Check which one is active with:

```bash
java -XX:+PrintFlagsFinal -version | grep -E "Use(G1|Serial|Parallel|Z)GC"
```

### Memory leaks in a garbage-collected language

GC prevents dangling pointers, but it does not prevent leaks. A leak happens when objects remain reachable even though the program no longer needs them. The collector cannot free them because a live reference still points to them.

```java
import java.util.ArrayList;
import java.util.List;

public class LeakExample {
    private static final List<byte[]> CACHE = new ArrayList<>();

    static void handleRequest() {
        CACHE.add(new byte[1024]);  // never removed: the static list keeps every array reachable
    }

    public static void main(String[] args) {
        for (int i = 0; i < 10; i++) {
            handleRequest();
        }
        System.out.println("cached entries: " + CACHE.size());
    }
}
```

Common sources of leaks are static collections used as caches with no eviction, listeners that are never removed, `ThreadLocal` values in thread pools, and class-loader leaks after redeployment.

### Weak references

Weak references let the GC reclaim an object when only weak references point to it. They are useful for caches where you are happy to lose entries under memory pressure.

```java
import java.lang.ref.WeakReference;

public class WeakDemo {
    public static void main(String[] args) {
        Object strong = new Object();
        WeakReference<Object> weak = new WeakReference<>(strong);

        System.out.println("before: " + (weak.get() != null));   // true
        strong = null;
        System.gc();   // a hint only; the JVM may ignore it
        System.out.println("after: " + (weak.get() != null));    // may print true or false
    }
}
```

`WeakHashMap` is built on the same idea. For cleanup actions after an object is collected, use `java.lang.ref.Cleaner` (Java 9+). `Object.finalize()` is deprecated and should not be used in new code.

### Tuning flags you will see

```bash
-Xms2g -Xmx2g                       # fixed heap size, avoids resize pauses
-XX:MaxGCPauseMillis=200            # pause-time goal for G1
-XX:+HeapDumpOnOutOfMemoryError     # write a heap dump when the heap is exhausted
-XX:HeapDumpPath=/var/dumps/        # where to write the dump
```

Tuning should follow measurement. Start with the default collector and the heap size that fits your machine. Change one flag at a time and compare GC logs and latency numbers.

---

## How it works / Step by step

1. Allocation: `new` takes space from the young generation (or a TLAB, a per-thread allocation buffer).
2. When Eden fills, a minor GC runs. Live objects are copied to a survivor space or promoted to the old generation.
3. When the old generation fills past a threshold, a major GC runs. G1 and ZGC do this concurrently in most cases.
4. If concurrent work cannot keep up, the collector falls back to a longer stop-the-world collection.
5. If live data does not fit even after full collection, the JVM throws `OutOfMemoryError: Java heap space`.

### Reading GC logs

Enable unified GC logging with:

```bash
java -Xlog:gc*:file=gc.log:time,uptime,level,tags -Xmx2g MyApp
```

A typical G1 young-collection line looks like this (the exact text changes between JDK versions, so treat it as an illustration):

```text
[2.345s][info][gc] GC(12) Pause Young (Normal) (G1 Evacuation Pause) 412M->96M(2048M) 9.871ms
```

Read it left to right:

- `GC(12)`: the 13th collection since startup.
- `Pause Young`: a young-generation pause.
- `412M->96M(2048M)`: heap used before and after, and the current committed heap size.
- `9.871ms`: the pause length. This is the number your latency SLO cares about.

Things to look for:

- Frequent pauses with little memory freed suggests a leak or too small a young generation.
- Old-generation usage that climbs after each full collection and never drops is a leak.
- Long pauses that match request timeouts point to a collector or heap-size problem.
- Many back-to-back "Allocation Failure" messages mean allocation outpaces collection.

Tools that read these logs include GCViewer and GCEasy (third-party), and the JDK's `jstat -gc <pid>` for live counters.

### Common GC symptoms and fixes

Most GC problems show up first as a latency or memory symptom. Match the symptom to a likely cause, then confirm it with GC logs or a heap dump before changing flags.

| Symptom | Likely cause | Fix |
|---|---|---|
| Full GC thrashing: frequent full collections, high CPU, little memory freed | Live data close to `-Xmx`, a leak, or an allocation rate the old generation cannot absorb | Find what keeps data alive (heap dump). Reduce the live set or allocation rate. Raise `-Xmx` only if the live data really fits in the larger heap. |
| Long pauses: requests time out during collections | Large live set being copied, very large (humongous) objects, a throughput-tuned collector such as Parallel, or an unrealistic pause goal | Shrink the live set. Use G1 or ZGC for latency-sensitive services. Set `MaxGCPauseMillis` to a value the workload can meet, and check logs for full collections. |
| High GC overhead: a large share of CPU goes to collection | High allocation rate with a small young generation, or a heap that stays nearly full | Reduce short-lived allocations (reuse buffers, avoid temporary collections). Give the young generation or the heap more room. |
| Memory leak: old-generation usage climbs after each full collection | Static collections, caches with no size limit, listeners never removed, or `ThreadLocal` values left in pooled threads | Take a heap dump (`jmap -dump:live,format=b,file=heap.hprof <pid>`, or `-XX:+HeapDumpOnOutOfMemoryError`). Open it in a tool such as Eclipse MAT and follow the retaining paths. Bound caches, remove listeners, and call `ThreadLocal.remove()` when work ends. |

No fixed CPU percentage defines "high GC overhead". The JVM throws `OutOfMemoryError: GC overhead limit exceeded` when almost all of its time goes to GC and very little memory is recovered. Treat that error as a sign to fix allocations or the heap, not as something to switch off.

---

## Common pitfalls

- Calling `System.gc()` in application code. It is only a hint, and it usually causes a full collection, which is costly. Use it only in tests or with a specific reason.
- Setting `-Xmx` very high without a plan for pauses. A larger heap makes some collectors pause longer.
- Changing many GC flags at once. You cannot tell which change helped.
- Assuming that GC removes all memory problems. Leaks come from live references, not from the collector.
- Using CMS flags on Java 14 or later. The JVM will not start.
- Relying on `finalize()` to close files or sockets. Use try-with-resources instead.
- Tuning the heap without looking at allocation rate. Reducing allocations often helps more than tuning.

!!! tip "Interview tip"
    **Q: How do you decide which garbage collector to use?**
    Start with the default (G1 on current JDKs), measure pause times and throughput under realistic load, and only then change the collector. Use Parallel when throughput matters more than pauses, and ZGC when pauses must stay low on a large heap. Always confirm the choice with GC logs and latency metrics.

    **Follow-up: Can a Java program have a memory leak?**
    Yes. The GC frees objects that are unreachable. If a static cache, listener, or ThreadLocal keeps a reference to objects that are no longer needed, they stay reachable and the heap fills up. Heap dumps and object histograms (`jmap -histo`) help find the retaining path.

## Quick recap

- An object is garbage when no GC root can reach it; setting a reference to `null` only makes it eligible.
- The generational design collects young objects often and old objects rarely.
- Serial, Parallel, G1, and ZGC cover small, batch, general, and low-latency workloads. G1 is the default since Java 9.
- CMS was removed in Java 14; use G1 or ZGC instead.
- Read `-Xlog:gc*` output to find pause lengths, heap growth, and leaks.

**See also:** [JVM Architecture and Memory](jvm-architecture-memory.md), [JIT Compilation and Performance Tools](jit-and-performance-tools.md), [JVM Internals index](index.md)
