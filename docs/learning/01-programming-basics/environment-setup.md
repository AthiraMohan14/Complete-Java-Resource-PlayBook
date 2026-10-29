# Environment Setup

Setting up a JDK correctly is the first practical step in any Java course or interview task. Interviewers rarely ask about installers, but they often ask why `javac` is "not recognized" or why a build tool picks the wrong Java version, and the answer almost always comes down to `JAVA_HOME` and `PATH`.

## Core concepts

### Choosing and installing a JDK
Install a JDK, not just a runtime. Several vendors publish OpenJDK builds (Eclipse Temurin, Oracle JDK, Amazon Corretto, and others), and they are interchangeable for learning. Pick a current LTS release, such as 21 or 25, as the roadmap suggests. Install it once, then keep the install path in mind, because the next two steps need it.

After installing, open a new terminal. Environment changes only apply to processes started after the change.

### JAVA_HOME
`JAVA_HOME` is an environment variable that points to the root folder of the JDK, the folder that contains `bin`, `lib`, and `conf`. It should point to the JDK root, not to `bin`. Build tools such as Maven and Gradle, and many IDEs, read `JAVA_HOME` to find the compiler.

Example values (your path will differ):

```text
Windows:  C:\Program Files\Java\jdk-21
macOS:    /Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home
Linux:    /usr/lib/jvm/java-21-openjdk-amd64
```

### PATH
`PATH` is the list of folders the shell searches when you type a command name. Add the JDK's `bin` folder so that `java` and `javac` can be found from any folder. Using `%JAVA_HOME%\bin` (Windows) or `$JAVA_HOME/bin` (macOS and Linux) keeps the entry tied to the variable.

### Setting the variables

**Windows (Command Prompt, for the current user):**

```text
setx JAVA_HOME "C:\Program Files\Java\jdk-21"
setx PATH "%PATH%;%JAVA_HOME%\bin"
```

`setx` writes the values for future sessions only. Also note that `setx` truncates values longer than 1024 characters. For a long `PATH`, edit it through **System Properties, then Environment Variables** instead. Open a new terminal afterwards.

**macOS (zsh, in `~/.zshrc`):**

```text
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
export PATH="$JAVA_HOME/bin:$PATH"
```

**Linux (bash, in `~/.bashrc`):**

```text
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
```

Reload the file with `source ~/.zshrc` or `source ~/.bashrc`, or open a new terminal.

### Verifying the installation
Run these commands in a new terminal:

```text
java -version
javac -version
```

Both should report the same major version. Note that `java -version` writes to standard error, not standard output, so it may look like it printed nothing special when you pipe it. To check where the commands come from, use `where java` on Windows or `which java` on macOS and Linux. The path should be inside your JDK folder.

To confirm that `JAVA_HOME` is set, run `echo %JAVA_HOME%` (Command Prompt), `echo $env:JAVA_HOME` (PowerShell), or `echo $JAVA_HOME` (macOS and Linux).

Finally, compile and run a small program to confirm the whole chain works:

```java
public class Hello {
    public static void main(String[] args) {
        System.out.println("JDK is working: " + Runtime.version().feature());
    }
}
```

```text
javac Hello.java
java Hello
```

`Runtime.version().feature()` returns the major version number of the running JDK.

## How it works / Step by step

1. Install a JDK and note its install folder.
2. Set `JAVA_HOME` to that folder (the root, not `bin`).
3. Add `%JAVA_HOME%\bin` or `$JAVA_HOME/bin` to `PATH`.
4. Open a new terminal, so the changes take effect.
5. Run `java -version` and `javac -version`, then compile and run a test class.

## Common pitfalls
- Setting `JAVA_HOME` to the `bin` folder instead of the JDK root.
- Leaving an older JDK earlier in `PATH`, so `java -version` reports the wrong version. Put the JDK `bin` folder first, or fix the older entry.
- Having a JRE on `PATH` without a JDK. The `javac` command then fails with "not recognized".
- Forgetting to open a new terminal after changing environment variables.
- Using `setx` on a `PATH` value that is longer than 1024 characters, which truncates it.
- Mixing up the IDE's project SDK with the system `JAVA_HOME`. The IDE can use a different JDK from the one your shell uses.

!!! tip "Interview tip"
    **Q: Your build fails with "invalid source release" or "unsupported class file version". What happened?** The compiler or runtime is older than the code expects. Check `java -version` and `JAVA_HOME`, then either install a newer JDK or set the compiler release (for example, `javac --release 17`) to match the target. The fix is to align the JDK, `JAVA_HOME`, and the project's configured Java version.

## Quick recap
- Install a JDK (not just a JRE), preferably a current LTS release.
- `JAVA_HOME` points to the JDK root; `PATH` includes its `bin` folder.
- Open a new terminal after changing variables.
- Verify with `java -version` and `javac -version`, then compile and run a test class.
- Most "command not found" or wrong-version errors come from `PATH` order or a wrong `JAVA_HOME`.

**See also:** [Java Overview and Platform](java-overview-platform.md), [Syntax Basics](syntax-basics.md), [Git, IDEs and Command-Line Tools](git-ide-tools.md)
