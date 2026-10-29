# Gradle

Gradle is a build tool that describes a build as a graph of tasks, configured in a Groovy or Kotlin script. Interviewers ask about Gradle to compare it with Maven and to check that you understand tasks, incremental builds, the wrapper, and multi-project setup.

## Core concepts

### Build scripts: Groovy and Kotlin DSL

Gradle has two script languages. `build.gradle` uses Groovy; `build.gradle.kts` uses Kotlin. Both configure the same model. The Kotlin DSL gives type-safe completion in an IDE, and most new projects use it.

```kotlin
// build.gradle.kts
plugins {
    java
    id("org.springframework.boot") version "3.3.4"   // example version; check the current release
    id("io.spring.dependency-management") version "1.1.6"
}

group = "com.example"
version = "1.0.0-SNAPSHOT"

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

The plugin versions above are placeholders for illustration. Check the current release before copying them.

### Tasks and task dependencies

A Gradle build is a graph of **tasks**. Each task has inputs, outputs, and actions. Tasks run in dependency order, and a task is skipped when its inputs and outputs have not changed (up-to-date checking).

```kotlin
tasks.register("hello") {
    doLast {
        println("Hello from a custom task")
    }
}

tasks.named("build") {
    dependsOn("hello")   // hello runs before build
}
```

Common lifecycle tasks: `assemble` (build artefacts), `check` (run verification such as tests), `build` (assemble plus check), `clean`.

Use `./gradlew tasks` to list tasks and `./gradlew build --dry-run` to see what would run.

### The Gradle wrapper

The wrapper (`gradlew` on Unix, `gradlew.bat` on Windows) downloads and runs a fixed Gradle version. Commit the wrapper files to version control so every developer and CI server uses the same Gradle. Run `./gradlew` rather than a locally installed `gradle`.

### Configurations and dependencies

Gradle dependency configurations replace Maven scopes:

| Configuration | Purpose | Maven equivalent |
|---|---|---|
| `implementation` | Used by this module; hidden from consumers' compile classpath | `compile` (roughly) |
| `api` | Part of this module's public API (java-library plugin) | `compile` (exposed) |
| `compileOnly` | Compile time only | `provided` |
| `runtimeOnly` | Runtime only | `runtime` |
| `testImplementation` | Test compile and run | `test` |

Prefer `implementation` over `api`. It reduces recompilation when dependencies change and keeps the public API small.

### Multi-project builds

A `settings.gradle.kts` file lists subprojects. Shared configuration goes in the root build script or in convention plugins under `buildSrc` or an included build.

```kotlin
// settings.gradle.kts
rootProject.name = "shop"
include("order-service", "payment-client")
```

Subprojects depend on each other with `implementation(project(":payment-client"))`.

### Version catalogs

Version catalogs centralise versions and library coordinates in `gradle/libs.versions.toml`. Each module refers to them as `libs.<alias>`.

```toml
[versions]
junit = "5.10.2"

[libraries]
junit-jupiter = { module = "org.junit.jupiter:junit-jupiter", version.ref = "junit" }
```

```kotlin
dependencies {
    testImplementation(libs.junit.jupiter)
}
```

### Custom tasks

Custom task types extend `DefaultTask` or use built-in types such as `Copy` and `Exec`. Declare inputs and outputs with annotations or properties so Gradle can skip the task when nothing changed.

### Gradle vs Maven

| Area | Maven | Gradle |
|---|---|---|
| Model | Fixed lifecycle, XML | Task graph, Groovy or Kotlin scripts |
| Customisation | Plugins and goals | Plugins, custom tasks, programmatic logic |
| Incremental build | Limited | Up-to-date checks, build cache, configuration cache |
| Readability | Verbose XML, very predictable | Shorter scripts, more flexible, easier to get wrong |
| Ecosystem | Default for many enterprises | Default for Android; common in Spring projects |

Gradle often builds faster on large projects because of incremental builds, the build cache, and parallel execution. Those gains depend on well-written tasks; a slow build is usually a configuration problem, not a tool problem. Maven is simpler to reason about, and its declarative model suits teams that value consistency over flexibility.

## How it works / Step by step

A Gradle build has three phases:

1. **Initialisation:** reads `settings.gradle(.kts)` and decides which projects take part.
2. **Configuration:** runs each project's build script to create the task graph. The configuration cache can reuse this step.
3. **Execution:** runs the requested tasks and their dependencies, skipping up-to-date ones.

Run `./gradlew build --scan` or `--profile` to find slow tasks.

## Common pitfalls

- Putting logic that reads files or the network at configuration time. It runs on every build, even when you only run `clean`.
- Using `api` everywhere, which spreads dependencies to every consumer.
- Not committing the wrapper, so builds use different Gradle versions.
- Mixing Groovy and Kotlin DSL syntax in one script.
- Declaring tasks without inputs and outputs, so they never skip.
- Hard-coding versions in several build files instead of a version catalog.

!!! tip "Interview tip"
    **Q: Why would you choose Gradle over Maven, or the reverse?**
    Gradle suits large or multi-language builds that need incremental builds, caching, and custom logic, and it is the default for Android. Maven suits teams that want a fixed convention and simple XML. Either tool can build a Spring Boot service. Name the trade-off you care about (speed, flexibility, or predictability) and the cost you accept for it.

## Quick recap

- Scripts are `build.gradle` (Groovy) or `build.gradle.kts` (Kotlin); a build is a graph of tasks.
- Up-to-date checks skip tasks whose inputs and outputs have not changed.
- Commit the Gradle wrapper and run `./gradlew`.
- Use `implementation` by default; reserve `api` for types exposed to consumers.
- Version catalogs keep versions in one place.

**See also:** [Maven](maven.md), [Dependency Management](dependency-management.md)
