# Tooling & Utilities

Notes on the everyday JDK tools and standard utilities that sit around the language: jshell for experiments, javadoc for documentation, JARs and modules for packaging, and `java.time` for dates and times. Interviewers often ask about these to check whether a candidate has actually shipped Java code, not just written it.

---

## Topics

### [Java Tools & Utilities](java-tools-utilities.md)
**jshell - javadoc - JAR - multi-release JAR - modules - command-line arguments**
Command-line arguments, the REPL, documentation comments, packaging, and the Java Platform Module System (JPMS), plus the removed Nashorn engine as history.

### [Date & Time (java.time)](date-time.md)
**LocalDate - Instant - Duration - Period - DateTimeFormatter - legacy Date and Calendar**
The `java.time` API that replaced `java.util.Date` and `Calendar`, how to pick the right type, and why the legacy classes cause bugs.

### More in this section

### [Annotations and Reflection](annotations-and-reflection.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Annotations attach metadata to code, and reflection lets a program inspect and use that code at runtime. Together they explain how Spring finds your beans, how JUnit finds your...

