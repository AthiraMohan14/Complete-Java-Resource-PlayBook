# Java Tools & Utilities

The JDK ships with a small set of command-line tools that every Java developer uses: `java`, `javac`, `jshell`, `javadoc`, and `jar`. Interviewers ask about these to see whether you can compile, run, document, and package a program without an IDE doing the work for you.

## Core concepts

### Command-line arguments
The JVM passes whatever follows the class name on the `java` command line into the `String[] args` parameter of `main`. Every element is a `String`, so numbers must be parsed explicitly. Arguments are not split on spaces by the JVM; the shell does that.

```java
public class Greet {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: java Greet <name> [times]");
            return;
        }
        int times = args.length > 1 ? Integer.parseInt(args[1]) : 1;
        for (int i = 0; i < times; i++) {
            System.out.println("Hello, " + args[0]);
        }
    }
}
```

Run it with `javac Greet.java`, then `java Greet Asha 2`. Quote arguments that contain spaces: `java Greet "Asha Nair"`.

### jshell (the REPL)
`jshell` is an interactive read-eval-print loop, added in Java 9. It is the fastest way to test a library call or a language rule without creating a class.

```text
$ jshell
jshell> int square(int x) { return x * x; }
|  created method square(int)
jshell> square(7)
$2 ==> 49
jshell> /exit
```

Use `/exit` to leave, `/list` to see the snippets you have entered, and `/save` to write them to a file. Snippets do not need a `public class` wrapper. Treat jshell as a sandbox: state lives only for that session.

### Javadoc
Javadoc comments start with `/**` and are read by the `javadoc` tool to produce HTML API documentation. Block tags describe parameters, return values, and exceptions.

```java
/**
 * Returns the total price after applying a discount.
 *
 * @param price    the list price, must not be negative
 * @param percent  the discount in the range 0 to 100
 * @return the discounted price
 * @throws IllegalArgumentException if {@code percent} is outside 0..100
 */
public static double discounted(double price, double percent) {
    if (percent < 0 || percent > 100) {
        throw new IllegalArgumentException("percent out of range: " + percent);
    }
    return price * (1 - percent / 100);
}
```

Generate the HTML with `javadoc -d docs/api -sourcepath src -subpackages com.example`. Use `{@code ...}` for inline code and `{@link ...}` for cross-references. Write Javadoc for public API; use plain `//` comments for implementation details.

### JAR files
A JAR is a ZIP archive with a `META-INF/MANIFEST.MF` file. The manifest can name the entry-point class (`Main-Class`) so the JAR runs with `java -jar`.

| Command | What it does |
|---|---|
| `jar cf app.jar -C out .` | Create a JAR from compiled classes in `out` |
| `jar cfe app.jar com.example.Main -C out .` | Create a JAR and set `Main-Class` (`e` option) |
| `jar tf app.jar` | List the contents |
| `jar xf app.jar` | Extract the contents |
| `java -jar app.jar` | Run the entry point from the manifest |

Classpath dependencies are not bundled by default. Build tools such as Maven or Gradle produce "fat" or "uber" JARs when you need one self-contained file.

### Multi-release JARs
A multi-release JAR (MRJAR) holds one set of classes for the baseline Java version and extra class versions under `META-INF/versions/<N>/`. The JVM uses the highest version it supports, so a library can use newer APIs on newer runtimes while still running on older ones.

```text
app.jar
  com/example/Hasher.class            <- baseline (runs on any supported release)
  META-INF/versions/9/com/example/Hasher.class  <- used on Java 9 and later
  META-INF/MANIFEST.MF                <- contains "Multi-Release: true"
```

The manifest needs the attribute `Multi-Release: true`. Without it, the JVM ignores the versioned directories.

### Modules (JPMS)
The Java Platform Module System, added in Java 9, groups packages into named modules and states what each module needs and what it shares. A module is declared in `module-info.java` at the root of its source tree.

```java
// src/com.example.shop/module-info.java
module com.example.shop {
    requires java.logging;          // this module reads java.logging
    exports com.example.shop.api;   // other modules may use this package
    // com.example.shop.internal is not exported; it stays hidden
}
```

Key points:
- `requires` declares a dependency on another module. Without it, the code cannot compile against that module's packages.
- `exports` makes a package visible to other modules. Packages you do not export are encapsulated, even if they are `public`.
- `opens` allows deep reflection into a package, which frameworks such as dependency injection containers need for private fields.
- Modules can be compiled and run from the command line, for example `javac -d out --module-source-path src $(find src -name "*.java")` and `java -p out -m com.example.shop/com.example.shop.api.Main`. Keep the exact flags in the official JDK documentation for your release.

### Nashorn (history only)
Nashorn was a JavaScript engine that shipped in the JDK from Java 8. It was deprecated in Java 11 and removed in Java 15. Do not use it in new code. If you need scripting from Java today, call an external engine or run the script in a separate process.

## How it works / Step by step

1. Write source files in a package-based folder tree.
2. Compile with `javac -d out ...`, which writes `.class` files to `out`.
3. Run with `java -cp out com.example.Main`, or package them first with `jar`.
4. Add Javadoc comments to public types and methods, then run `javadoc` to produce HTML.
5. For libraries, add `module-info.java` when you need strong encapsulation, then compile with the module source path.

## Common pitfalls

- Forgetting that every `args` element is a `String`, then calling `args[1] + 1` and getting string concatenation.
- Building a JAR without `Main-Class`, so `java -jar` fails with "no main manifest attribute".
- Leaving `Multi-Release: true` out of the manifest, so versioned classes silently never load.
- Exporting an internal package by accident, which turns an implementation detail into a public contract.
- Using `{@link}` with a name that does not resolve, which fails the Javadoc build only with strict doclint.

!!! tip "Interview tip"
    **Q: What is the difference between a JAR and a module?**
    A JAR is a packaging format: an archive of classes and resources. A module is a language-level unit with a `module-info.java` that declares its dependencies (`requires`) and its public API (`exports`). A modular JAR is a JAR with a module descriptor. Modules add strong encapsulation at compile time and at run time; a plain JAR on the classpath gives you only `public` vs non-public access.

## Quick recap

- `args` holds raw strings from the command line; parse them yourself.
- `jshell` is a REPL for quick experiments and does not persist state.
- Javadoc uses `@param`, `@return`, and `@throws`, and is generated with `javadoc`.
- A JAR is a ZIP with a manifest; `Main-Class` makes it runnable with `java -jar`.
- Multi-release JARs store version-specific classes under `META-INF/versions/`.
- JPMS (Java 9+) uses `module-info.java`, `requires`, and `exports` to encapsulate packages. Nashorn was removed in Java 15.

**See also:** [Date & Time (java.time)](date-time.md), [Learning index](../index.md)
