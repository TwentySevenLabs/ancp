# JVM Toolchain Notes

## Sources

- `research/source-docs/snapshots/java/javac.html`
- `research/source-docs/snapshots/java/java-compiler-api.html`
- `research/source-docs/snapshots/java/jdk-compiler-module.html`
- `research/source-docs/snapshots/java/openjdk-javac-diagnostics.html`
- `research/source-docs/snapshots/kotlin/command-line.html`
- `research/source-docs/snapshots/kotlin/compiler-reference.html`
- `research/source-docs/snapshots/kotlin/compiler-plugins.html`
- `research/source-docs/snapshots/scala/compiler-options.html`
- `research/source-docs/snapshots/scala/scala-cli-commands.html`

## Java

Java has a strong compiler API through `javax.tools.JavaCompiler`. Programmatic compilation can receive `Diagnostic` objects with kind, code, source, position, line, column, and message.

Javac also has internal diagnostic formatting infrastructure and compiler tree APIs in the `jdk.compiler` module.

## Kotlin

Kotlin has direct command-line compilers for JVM, JS, and Native, and common usage through Gradle/Maven/IDE integration.

The docs expose compiler options and diagnostic warning-level controls. Compiler plugin APIs exist but are explicitly unstable and should not be a required ANCP path.

## Scala

Scala has `scalac`, Scala CLI, sbt, BSP, Metals, and SemanticDB. Scala CLI supports compile/test flows and mentions actionable diagnostics.

## Adapter Requirements

A JVM-family adapter should:

- detect Gradle, Maven, sbt, Scala CLI, and direct compiler modes,
- preserve target platform and source language version,
- prefer Java Compiler API for Java when implementing on the JVM,
- use build tool tasks as verification steps,
- classify annotation processors/compiler plugins as effectful build extensions,
- keep Kotlin compiler plugin assumptions optional,
- expose SemanticDB under graph profile when available.

## Core Commands

```bash
javac ...
gradle build
mvn test
kotlinc ...
scala-cli compile .
scala-cli test .
sbt test
```

## ANCP Impact

The JVM family proves ANCP must separate source language from build system and must support compiler APIs as first-class adapter inputs.

