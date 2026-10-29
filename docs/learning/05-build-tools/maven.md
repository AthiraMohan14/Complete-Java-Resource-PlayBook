# Maven

Maven is a build tool that uses a declarative project file (`pom.xml`) to describe a project's identity, dependencies, and build steps. Interviewers ask about Maven to check that you know how a build moves from source to artefact, how dependencies are resolved, and how to fix a broken build without guessing.

## Core concepts

### The POM

The Project Object Model (POM) is the `pom.xml` at the root of a project. It declares coordinates (`groupId`, `artifactId`, `version`), packaging, properties, dependencies, and plugins.

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>order-service</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>21</maven.compiler.release>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

The `groupId:artifactId:version` triple is the coordinate of an artefact. Everything else in Maven depends on it.

### Build lifecycle

A lifecycle is an ordered sequence of phases. Running a phase runs every phase before it.

| Phase | What it does |
|---|---|
| `validate` | Checks the project is correct and all information is available |
| `compile` | Compiles main source code |
| `test` | Runs unit tests (Surefire plugin) |
| `package` | Builds the artefact (JAR, WAR) |
| `verify` | Runs integration checks on the package |
| `install` | Copies the artefact into the local repository (`~/.m2`) |
| `deploy` | Copies the artefact to a remote repository |

`mvn package` runs validate, compile, test, and package. `mvn clean install` also deletes `target/` first, using the separate `clean` lifecycle.

### Plugins and goals

Each phase is bound to plugin goals. For example, `maven-compiler-plugin:compile` is bound to `compile`. You can also run a goal directly, such as `mvn dependency:tree`. Plugin configuration goes in `<build><plugins>`.

Common plugins:

- **Surefire:** runs unit tests (`*Test.java` by default).
- **Failsafe:** runs integration tests in the `verify` phase.
- **Shade:** builds a fat (uber) JAR that bundles dependencies so the application runs with `java -jar`.
- **Spring Boot Maven plugin:** builds an executable JAR with `spring-boot:repackage`.

### Dependencies and scopes

Scopes control when a dependency is on the classpath:

| Scope | Compile | Test | Runtime | Typical example |
|---|---|---|---|---|
| `compile` (default) | Yes | Yes | Yes | Libraries the code calls |
| `provided` | Yes | Yes | No | Servlet API supplied by the server |
| `runtime` | No | Yes | Yes | JDBC driver |
| `test` | No | Yes | No | JUnit |

Transitive dependencies are the dependencies of your dependencies. Maven pulls them in automatically.

### Dependency mediation and management

When two paths bring different versions of the same library, Maven uses **nearest wins**: the version closest to the root of the dependency tree is used. If the distance is equal, the first declaration wins. This is why `dependency:tree` matters.

Two tools control versions:

- **`<dependencyManagement>`** sets the version of a dependency for the whole project (and child modules) without adding it to the classpath. Importing the Spring Boot BOM with `<scope>import</scope>` is the standard example.
- **`<exclusions>`** remove a transitive dependency from one declared dependency.

```xml
<dependency>
    <groupId>com.example</groupId>
    <artifactId>payment-client</artifactId>
    <version>2.3.0</version>
    <exclusions>
        <exclusion>
            <groupId>commons-logging</groupId>
            <artifactId>commons-logging</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

### Profiles

Profiles change the build for an environment or condition. Activate one with `-P dev` or an activation rule (for example, a property or the JDK version).

```xml
<profiles>
    <profile>
        <id>prod</id>
        <properties>
            <skipTests>true</skipTests>
        </properties>
    </profile>
</profiles>
```

Keep secrets out of profiles in the POM. Pass them at runtime or from a settings file.

### Repositories

Maven resolves artefacts from **Maven Central** by default. A project or company can add repositories in `pom.xml` or, better, in `settings.xml` (under `~/.m2`). Private repositories need credentials in `settings.xml` under `<servers>`, keyed by a repository `id`. Do not commit credentials to the POM.

### Multi-module projects

A parent POM with `<packaging>pom</packaging>` lists child modules with `<modules>`. Children inherit configuration and dependency versions from the parent. Running `mvn install` at the root builds modules in dependency order.

## How it works / Step by step

When you run `mvn clean package`:

1. Maven reads `settings.xml` and the POM hierarchy, merging parents and profiles.
2. It resolves dependencies, downloading missing artefacts to `~/.m2/repository`.
3. `clean` deletes `target/`.
4. Phases run in order; `compile` writes `target/classes`, `test` runs Surefire, and `package` writes the JAR to `target/`.

For a broken build, run `mvn -e` for the stack trace, `mvn dependency:tree` to see which version won, and `mvn help:effective-pom` to see the merged POM.

## Common pitfalls

- Declaring a version in several places, so the versions drift apart. Put shared versions in `<properties>` or a BOM.
- Relying on transitive dependencies without declaring them. A dependency upgrade can remove them silently.
- Using `SNAPSHOT` versions in production. Snapshots change; releases should be fixed.
- Committing credentials or tokens in `pom.xml`.
- Forgetting that `mvn install` writes to the local repository, so a stale artefact can hide a real problem.
- Using `<scope>compile</scope>` for test-only libraries, which bloats the production JAR.

!!! tip "Interview tip"
    **Q: How does Maven resolve a version conflict?**
    Maven uses nearest wins. The version reached by the shortest path in the dependency tree is chosen; ties go to the first declaration. To control it explicitly, pin the version in `<dependencyManagement>` (or import a BOM). Use `mvn dependency:tree` to confirm the result.

## Quick recap

- The POM declares coordinates, dependencies, and plugins; lifecycles run phases in order.
- `mvn package` runs `validate` through `package`; `clean` is a separate lifecycle.
- Scopes control the classpath; `test` and `provided` stay out of the production JAR.
- Nearest wins resolves conflicts; `dependencyManagement` pins versions.
- Use Surefire for unit tests, Failsafe for integration tests, and Shade or the Spring Boot plugin for runnable JARs.

**See also:** [Gradle](gradle.md), [Dependency Management](dependency-management.md)
