# Build Tools and Dependency Management

How Java projects are built, packaged, and kept free of library conflicts. This section covers roadmap section 5: Maven, Gradle, and dependency management.

---

## Topics

### [Maven](maven.md)
**POM - lifecycle - scopes - nearest wins - profiles - multi-module**
How a `pom.xml` describes a build, how phases and plugins run, and how dependency conflicts are resolved.

### [Gradle](gradle.md)
**build scripts - tasks - wrapper - configurations - version catalogs**
Groovy and Kotlin build scripts, task graphs, the Gradle wrapper, and a comparison with Maven.

### [Dependency Management](dependency-management.md)
**semantic versioning - BOM - transitive dependencies - JAR hell - repositories**
Versioning rules, controlling which library versions are used, diagnosing classpath conflicts, and private repositories.
