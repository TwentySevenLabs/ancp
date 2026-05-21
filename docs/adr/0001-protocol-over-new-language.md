# ADR 0001: Protocol Over New Language

Status: Accepted

## Context

Agent-native languages such as Zero show that compilers can expose JSON diagnostics, repair IDs, fix plans, and version-matched agent guidance.

The bigger OSS opportunity is broader: existing codebases will continue to use TypeScript, Python, Rust, Go, Java, Kotlin, C#, C/C++, Swift, Zig, Ruby, PHP, Dart, Scala, and other current ecosystems.

## Decision

ANCP is a protocol and schema layer over existing tools, not a new programming language.

Adapters convert native toolchain outputs into ANCP documents.

## Consequences

Benefits:

- usable with existing repos,
- easier OSS adoption,
- adapter-by-adapter implementation,
- no need to design syntax or runtime,
- compatible with LSP, SARIF, JSON Schema, SPDX, CycloneDX, and native compilers.

Costs:

- adapters must handle inconsistent native tool quality,
- some languages have weak structured output,
- repair quality varies by ecosystem,
- conformance must be profile-based.

