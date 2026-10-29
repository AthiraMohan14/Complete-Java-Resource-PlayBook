# Dependency Management

Dependency management decides which library versions end up on your classpath, how they are fetched, and whether they work together. Interviewers ask about it because most production bugs in Java services come from conflicting or unexpected library versions, not from your own code.

## Core concepts

### Semantic versioning

Semantic versioning (SemVer) uses `MAJOR.MINOR.PATCH`:

- **MAJOR:** incompatible API changes.
- **MINOR:** new features, backward compatible.
- **PATCH:** backward-compatible bug fixes.

SemVer is a convention; libraries do not always follow it. Read the release notes before a major upgrade, and treat a minor or patch upgrade as low risk, not zero risk. Pre-release suffixes (`-SNAPSHOT`, `-RC1`) mark versions that are not final.

### Version ranges and dynamic versions

Maven and Gradle can request a range (`[1.2,2.0)`) or a dynamic version (`1.+`, `latest.release`). Dynamic versions make builds non-reproducible: the same commit can build differently next week. Pin exact versions for applications and reserve ranges for libraries that deliberately follow a compatibility policy.

### Transitive dependencies

A transitive dependency is one your dependency needs. Maven and Gradle download them automatically. Inspect the full tree:

```bash
mvn dependency:tree          # Maven
./gradlew dependencies       # Gradle
```

Declare critical libraries directly. Relying on a transitive dependency works until the library you depend on drops it.

### Resolution strategies

- **Maven:** nearest wins; first declaration wins on ties. Override with `<dependencyManagement>`.
- **Gradle:** highest version wins by default when two requests conflict. Control this with `resolutionStrategy`, or with platforms and constraints.

```kotlin
// Gradle: force a version for every configuration
configurations.all {
    resolutionStrategy {
        force("com.fasterxml.jackson.core:jackson-databind:2.17.2")   // example version
    }
}
```

Forcing versions is a last resort. It hides the conflict instead of fixing it. Prefer a BOM or a platform, which keeps related libraries aligned.

### Bills of materials (BOM)

A BOM is a POM that lists compatible versions of many artefacts. Importing one in `<dependencyManagement>` lets you omit versions for the libraries it covers. The Spring Boot BOM (`spring-boot-dependencies`) is the most common example.

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>${spring-boot.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

### Classpath conflicts ("JAR hell")

JAR hell happens when two JARs contain the same class name, or when a library expects a different version of a class than the one loaded. Symptoms: `NoSuchMethodError`, `NoClassDefFoundError`, `ClassCastException` between identical names, or behaviour that changes between IDE and command line.

How to diagnose:

1. Find the failing class in the stack trace.
2. Find which JARs contain it (search the dependency tree or the JAR contents).
3. Check which version wins in the resolved tree.
4. Align versions with a BOM, exclude the duplicate, or upgrade the older library.

Java 9 and later modules (JPMS) detect some conflicts at startup, but most applications still run on the classpath.

### Private repositories and authentication

Private repositories (Nexus, Artifactory, GitHub Packages, or a cloud registry) need credentials. Keep them out of source control:

- Maven: store credentials in `~/.m2/settings.xml` under `<servers>`, and reference them by `<id>` from the POM.
- Gradle: read credentials from `gradle.properties` in the user's home directory, or from environment variables, and reference them in the build script.

```kotlin
// build.gradle.kts: credentials come from the environment, never from the script
repositories {
    maven {
        url = uri("https://repo.example.com/maven")
        credentials {
            username = providers.gradleProperty("repoUser").orNull
            password = providers.gradleProperty("repoToken").orNull
        }
    }
}
```

Use a short-lived token where the registry supports it. Rotate tokens that were ever committed by mistake.

### Lock files and reproducible builds

Gradle supports dependency locking (`gradle dependencies --write-locks`), which records resolved versions in lock files. Maven does not have a built-in lock file; a BOM and pinned versions serve the same purpose. Commit lock files for applications so CI and production resolve the same versions.

### Checking for vulnerable dependencies

Scan your dependencies for known vulnerabilities in CI with a tool such as OWASP Dependency-Check or your platform's dependency scanner. The OWASP Top 10 (2021) lists "Vulnerable and Outdated Components" as a category; the OWASP list is updated periodically, so check the current version.

## How it works / Step by step

When a build resolves dependencies:

1. The tool reads the declared dependencies and any BOMs or platforms.
2. It downloads each artefact's POM or metadata and walks transitive dependencies.
3. It applies the conflict rule (nearest wins in Maven, highest version in Gradle unless constrained).
4. It downloads the chosen artefacts into the local cache and builds the classpath.

To audit a change, compare the dependency tree before and after the upgrade.

## Common pitfalls

- Upgrading a library without reading its release notes or migration guide.
- Using dynamic versions in an application, so builds change without a code change.
- Forcing a version without checking that the library still works with its neighbours.
- Trusting that a library follows SemVer.
- Putting repository passwords or tokens in a file that is committed.
- Ignoring duplicate classes reported at startup.

!!! tip "Interview tip"
    **Q: How do you prevent version conflicts across a multi-module project?**
    Declare every shared version once, using a parent POM with `<dependencyManagement>`, an imported BOM, or a Gradle platform or version catalog. Modules then request the library without a version, so all modules resolve the same one. Check the tree after changes and fail the build on duplicate classes if you need a hard guarantee.

## Quick recap

- SemVer tells you the likely impact of an upgrade; check release notes anyway.
- Pin versions in applications; avoid dynamic version ranges.
- Use BOMs or platforms to align related libraries.
- Diagnose JAR hell from the stack trace, then check the resolved tree.
- Keep repository credentials out of version control.

**See also:** [Maven](maven.md), [Gradle](gradle.md), [Index](index.md)
