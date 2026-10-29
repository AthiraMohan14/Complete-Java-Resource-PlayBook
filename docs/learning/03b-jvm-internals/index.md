# JVM Internals

How the Java Virtual Machine runs your code: where objects live, how memory is reclaimed, how classes are loaded, and how the JIT compiler and profiling tools help you diagnose performance problems. Interviewers ask these questions to see whether you understand what happens after `javac` and `java` run.

---

## Topics

### [JVM Architecture and Memory](jvm-architecture-memory.md)
**bytecode - heap - stack - Metaspace - memory model**
What the JVM is made of, the difference between heap and stack, where each kind of data lives, and why PermGen was replaced by Metaspace.

### [Garbage Collection](garbage-collection.md)
**Serial - Parallel - G1 - ZGC - GC logs - tuning flags**
The collectors that ship with the JDK, how they differ, which one to pick, and how to read a GC log.

### [Class Loading](class-loading.md)
**Bootstrap - Platform - Application - parent delegation - linking - initialisation**
The three built-in class loaders, the parent-delegation model, and the lifecycle a class goes through before its code runs.

### [JIT Compilation and Performance Tools](jit-and-performance-tools.md)
**JIT - C1 - C2 - tiered compilation - CDS - JMH - jcmd - JFR**
How the JIT compiler speeds up hot code, how Class Data Sharing reduces startup cost, and which tools to use when a service is slow.
