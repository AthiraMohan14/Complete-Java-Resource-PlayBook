# Git, IDEs and Command-Line Tools

Day-to-day Java work depends on three tools: Git for version control, an IDE for editing and debugging, and the command line for compiling, running, and scripting. Interviewers often ask about the Git workflow (branches, merges, and conflicts) and about how you would compile and run code without an IDE, so this page covers both.

## Core concepts

### Git basics
Git records snapshots of a project called commits. A repository on your machine can be linked to a remote copy on a host such as GitHub, usually named `origin`.

| Task | Command |
|---|---|
| Get a copy of a remote repository | `git clone <url>` |
| See changed files | `git status` |
| Stage changes | `git add <file>` or `git add .` |
| Record a commit | `git commit -m "Describe the change"` |
| Upload commits | `git push` |
| Download and merge remote changes | `git pull` |
| List, create, and switch branches | `git branch`, `git switch -c <name>`, `git switch <name>` |
| Combine a branch into the current one | `git merge <branch>` |
| Show history | `git log --oneline --graph` |

A typical feature flow: create a branch, make and commit changes, push the branch, open a pull request, then merge it into `main` after review.

```text
git switch -c feature/parse-orders
# edit files
git add src/OrderParser.java
git commit -m "Add order parser"
git push -u origin feature/parse-orders
```

Use a `.gitignore` file to keep build output (such as `*.class` and `out/`) and IDE settings out of the repository.

### Merge conflicts
A conflict happens when two branches change the same lines. Git stops the merge and marks the file:

```text
<<<<<<< HEAD
int limit = 10;
=======
int limit = 20;
>>>>>>> feature/limits
```

To resolve it, edit the file to the correct final code and remove the markers, then run `git add <file>` and `git commit`. Use `git merge --abort` to cancel a merge that is not going well.

### Pull versus fetch
`git fetch` downloads remote commits without changing your working files. `git pull` is a fetch followed by a merge (or rebase, if configured). Fetch first when you want to inspect changes before combining them.

### IDEs
| IDE | Strengths | Typical use |
|---|---|---|
| IntelliJ IDEA | Strong refactoring, code analysis, and built-in build tool integration | Large Java and enterprise projects |
| Eclipse | Long-standing, open source, extensible through plugins | Projects that already use Eclipse |
| VS Code | Lightweight editor; Java support comes from the Java extension pack | Quick edits, mixed-language work |

Whichever IDE you choose, learn these features: running and debugging with breakpoints, stepping into and over code, viewing variables, using the integrated terminal, and running Git from the UI. Configure the project's JDK once in the IDE settings, and check that it matches the JDK in your shell.

### The command line
Compiling and running from a terminal teaches you what the IDE does for you.

```text
javac -d out src/com/example/app/Main.java    # compile into the out folder
java -cp out com.example.app.Main             # run, with out on the classpath
```

Common navigation commands: `cd <folder>` changes the folder, `dir` (Windows) or `ls` (macOS and Linux) lists it, and `cd ..` moves up one level.

### JShell
`jshell` is a read-eval-print loop (REPL) that ships with the JDK. Use it to test expressions without writing a class.

```text
jshell> int square(int n) { return n * n; }
jshell> square(7)
$2 ==> 49
jshell> /exit
```

### Javadoc
Javadoc comments (`/** ... */`) document classes and methods. The `javadoc` tool turns them into HTML.

```java
/**
 * Adds two numbers.
 *
 * @param a the first operand
 * @param b the second operand
 * @return the sum of {@code a} and {@code b}
 */
public static int add(int a, int b) {
    return a + b;
}
```

```text
javadoc -d docs src/com/example/app/MathUtil.java
```

### Packaging: JAR files
A JAR is a ZIP archive of classes and resources, with an optional manifest. The `jar` tool creates one. Multi-release JARs can contain alternate class versions for newer Java releases.

```text
jar --create --file app.jar --main-class com.example.app.Main -C out .
java -jar app.jar
```

### Inspecting bytecode with javap
`javap` disassembles a compiled class. It lists fields and method signatures, and with `-c` it prints the bytecode instructions. Use it to check what the compiler produced, for example how a string concatenation or an enhanced `for` loop is translated. `-p` includes private members.

```text
javap -p out/com/example/app/Main.class       # signatures, including private members
javap -c -p out/com/example/app/Main.class    # plus the bytecode of each method
```

### Debugging from the terminal with jdb
`jdb` is the JDK's command-line debugger. It attaches to a program started with debugging enabled, or launches one itself. The commands are the same ones an IDE debugger uses: set a breakpoint, run, step, and print a variable.

```text
jdb -classpath out com.example.app.Main
> stop at com.example.app.Main:12    # breakpoint on line 12
> run
> print total                         # inspect a local variable
> step                                # run the current line, entering calls
> cont                                # resume until the next breakpoint
```

For remote programs, start the JVM with `-agentlib:jdwp` and attach `jdb` to the port it reports. The IDE debugger uses the same protocol.

## How it works / Step by step

1. Git tracks changes in three areas: the working tree, the staging area (`git add`), and the commit history (`git commit`).
2. `git push` sends local commits to the remote; `git pull` brings remote commits in and merges them.
3. Compiling uses `javac`, which writes `.class` files to the output folder given by `-d`.
4. Running uses `java` with the classpath (`-cp`) that contains the compiled classes.
5. `jshell` evaluates each entry as you type it, and `javadoc` reads doc comments from source files.

## Common pitfalls
- Committing build output or IDE folders because there is no `.gitignore`.
- Running `git add .` without checking `git status`, which can stage files you did not intend to commit.
- Resolving a merge conflict by deleting the conflict markers and leaving both versions of the code.
- Working on `main` directly instead of a branch.
- Using a different JDK in the IDE than the one `java` uses on the command line.
- Forgetting the classpath: `java Main` fails when `Main.class` is not in the current folder or on `-cp`.
- Confusing `git fetch` (no changes to your files) with `git pull` (merges changes).

!!! tip "Interview tip"
    **Q: How do you undo a commit that has already been pushed?** Do not rewrite shared history. Use `git revert <commit>`, which creates a new commit that undoes the change. `git reset` and rebase rewrite history, which is safe only on branches nobody else uses.

## Quick recap
- Git: branch for each change, commit with clear messages, and merge after review.
- Resolve a conflict by editing the file to the correct result, then `git add` and `git commit`.
- Choose an IDE, learn its debugger, and make sure it uses the same JDK as your shell.
- `javac -d` compiles into an output folder; `java -cp` runs classes from it.
- `jshell` is for quick experiments; `javadoc` turns doc comments into HTML.

**See also:** [Environment Setup](environment-setup.md), [Java Overview and Platform](java-overview-platform.md), [Syntax Basics](syntax-basics.md)
