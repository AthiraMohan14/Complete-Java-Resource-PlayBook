# I/O, Files, and Serialisation

Java has two generations of file APIs. `java.io` (streams and readers, from Java 1.0) is still everywhere, and `java.nio.file` (`Path` and `Files`, from Java 7) is the modern choice. Interviewers ask about streams, buffering, the `Path` API, and serialisation, and the last one is a frequent security topic.

## Core concepts

### Byte streams vs character streams

- **Byte streams** read and write raw bytes: `InputStream` and `OutputStream`, with subclasses such as `FileInputStream` and `FileOutputStream`.
- **Character streams** read and write text using a charset: `Reader` and `Writer`, such as `FileReader` and `FileWriter`.

Always specify the charset explicitly. The default charset varies with the platform and environment, and `FileReader` uses it implicitly.

```java
import java.io.*;
import java.nio.charset.StandardCharsets;

public class CopyBytes {
    public static void main(String[] args) throws IOException {
        try (InputStream in = new FileInputStream("in.bin");
             OutputStream out = new FileOutputStream("out.bin")) {
            in.transferTo(out);   // Java 9+: copies all bytes
        }

        try (Writer w = new OutputStreamWriter(
                new FileOutputStream("notes.txt"), StandardCharsets.UTF_8)) {
            w.write("hello\n");
        }
    }
}
```

### Buffered streams and readers

Each read or write on a raw `FileInputStream` can be a system call. Wrapping it in a buffered stream reads and writes in chunks.

```java
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class ReadLines {
    public static void main(String[] args) throws IOException {
        try (BufferedReader reader = new BufferedReader(
                new FileReader("data.txt", StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
        }
    }
}
```

`BufferedReader.lines()` returns a `Stream<String>`, which is useful for large files, but the stream must be closed (use try-with-resources).

`PrintWriter` offers convenient `print` and `println` methods. Its methods do not throw `IOException`; check `checkError()` if you need to detect failure.

### RandomAccessFile

`RandomAccessFile` lets you read and write at any byte position with `seek(long)`. It is useful for fixed-size records or editing part of a file in place, but it is lower level than NIO channels. Its `"rw"` mode creates the file if it is missing.

```java
import java.io.IOException;
import java.io.RandomAccessFile;

public class RecordFile {
    public static void main(String[] args) throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile("records.dat", "rw")) {
            raf.seek(16);                 // move to byte 16
            raf.writeInt(42);
            raf.seek(16);
            System.out.println(raf.readInt()); // 42
        }
    }
}
```

### The File class (legacy)

`java.io.File` represents a path name and offers `exists()`, `length()`, `delete()`, and `listFiles()`. Its methods often return `false` instead of throwing, which hides the reason for failure. Prefer `Path` and `Files` in new code.

### java.nio.file: Path and Files

`Path` is an immutable path object. `Paths.get` and `Path.of` (Java 11+) create one, and `Files` contains static helpers that throw informative exceptions such as `NoSuchFileException`.

```java
import java.io.IOException;
import java.nio.file.*;
import java.util.List;

public class NioBasics {
    public static void main(String[] args) throws IOException {
        Path file = Path.of("notes.txt");

        Files.writeString(file, "first line\nsecond line\n");   // Java 11+
        String all = Files.readString(file);
        List<String> lines = Files.readAllLines(file);

        System.out.println(lines.size());                       // 2
        System.out.println(Files.exists(file));                 // true
        System.out.println(file.toAbsolutePath().getFileName());
    }
}
```

Common operations:

| Task | Call |
|---|---|
| Read a small file as text | `Files.readString(path)` or `Files.readAllLines(path)` |
| Stream large text lazily | `Files.lines(path)` (close it) |
| Write text | `Files.writeString(path, text)` |
| Copy or move | `Files.copy(src, dst, StandardCopyOption.REPLACE_EXISTING)` |
| Create directories | `Files.createDirectories(path)` |
| Walk a tree | `Files.walk(path)` (close it) |
| Compare two files | `Files.mismatch(path1, path2)` (Java 12+) |

`Files.mismatch` returns the index of the first differing byte, or `-1` if the files are identical. It is the standard way to compare file contents without loading both files into memory.

### NIO channels and ByteBuffer

`java.nio` adds channels and buffers. A `FileChannel` reads and writes into a `ByteBuffer`, and the buffer has position, limit, and capacity. You flip a buffer after writing to switch it to reading.

```java
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.*;

public class ChannelDemo {
    public static void main(String[] args) throws Exception {
        try (FileChannel ch = FileChannel.open(Path.of("bytes.bin"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            ByteBuffer buf = ByteBuffer.allocate(8);
            buf.putInt(7).putInt(9);
            buf.flip();                 // switch from writing to reading
            ch.write(buf);
        }
    }
}
```

NIO also provides non-blocking channels for networking (see [Networking](networking.md)). For ordinary file work, `Files` covers most cases.

### Serialisation

Serialisation turns an object graph into bytes. A class opts in by implementing `java.io.Serializable`, which is a marker interface with no methods.

```java
import java.io.*;

public class User implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String name;
    private transient String password;  // not written to the stream

    public User(String name, String password) {
        this.name = name;
        this.password = password;
    }

    public static void main(String[] args) throws Exception {
        try (ObjectOutputStream out = new ObjectOutputStream(
                new FileOutputStream("user.ser"))) {
            out.writeObject(new User("ann", "secret"));
        }
        try (ObjectInputStream in = new ObjectInputStream(
                new FileInputStream("user.ser"))) {
            User u = (User) in.readObject();
            System.out.println(u.name + " " + u.password); // ann null
        }
    }
}
```

Key points:

- **`serialVersionUID`** identifies the class version. If you omit it, the JVM computes one from the class structure, and a small change (adding a method, for example) can make old data unreadable. Declare it explicitly.
- **`transient`** excludes a field from serialisation. On deserialisation, object fields are set to `null` and primitives to their defaults.
- **Serialisable superclasses** must have a no-argument constructor if they are not serialisable themselves.
- Static fields are never serialised.
- Prefer JSON or another explicit format for data crossing service boundaries. Java serialisation ties the data to the Java class layout.

### Why deserialising untrusted data is dangerous

`ObjectInputStream.readObject()` can instantiate classes from the stream and run code during deserialisation, using methods the attacker can influence. Gadget chains built from classes on the classpath have led to remote code execution. This is why deserialising data from an untrusted source is a security risk. OWASP lists it under software and data integrity failures (A08:2021 in the OWASP Top 10 2021). The OWASP Top 10 is updated periodically, so check the current version.

Mitigations:

- Do not deserialise data from untrusted sources. Use JSON or another data-only format.
- If you must, use an allowlist with an `ObjectInputFilter` (Java 9+) and reject unknown classes.
- Keep dependencies up to date, since many gadget chains depend on old libraries.

## How it works / Step by step

1. Open a stream on the file or socket, wrapping it in a buffered or character stream as needed.
2. Read or write inside try-with-resources so the stream closes even on error.
3. For a serialised object, the JVM writes the class name, `serialVersionUID`, and non-transient fields.
4. On read, the JVM checks the class name and `serialVersionUID`, creates the object without calling its constructor (for the first non-serialisable superclass), and restores the fields.
5. Use `Files.mismatch` or checksums to compare files; do not read both fully into memory.

| Need | Use |
|---|---|
| Text file, small | `Files.readString` / `writeString` |
| Text file, large | `Files.lines` or `BufferedReader` |
| Binary copy | `InputStream.transferTo` |
| Random access | `RandomAccessFile` or `FileChannel` |
| Save objects | JSON (preferred) or `Serializable` with care |

## Common pitfalls

- Forgetting to close streams, or closing them in the wrong order. Use try-with-resources.
- Relying on the default charset.
- Reading a huge file with `readAllLines` or `readString` and running out of memory.
- Omitting `serialVersionUID` and then breaking deserialisation with a harmless change.
- Storing secrets in a serialised object without `transient`, or expecting `transient` fields to survive.
- Calling `Files.lines` or `Files.walk` without closing the stream, which leaks file handles.
- Deserialising data from a network source with `ObjectInputStream`.

!!! tip "Interview tip"
    **Q: What does `transient` do, and why is deserialising untrusted data dangerous?**
    `transient` skips a field during serialisation, so it is reset to its default after reading. Untrusted deserialisation is dangerous because `readObject` can create arbitrary classes and trigger code paths that an attacker can chain into remote code execution. The fix is to avoid it, or to filter classes strictly.

## Quick recap

- Byte streams handle binary data. Character streams handle text, and need an explicit charset.
- Wrap streams in buffered readers and writers for performance.
- `Path` and `Files` are the modern file API. `Files.mismatch` compares two files.
- NIO channels and `ByteBuffer` give lower-level, buffer-based access.
- `Serializable` needs `serialVersionUID`. `transient` excludes fields.
- Deserialising untrusted data can lead to remote code execution. Avoid it.

**See also:** [Networking](networking.md), [Threads Basics](threads-basics.md), [Date and Time](../03c-tooling-utilities/date-time.md)
