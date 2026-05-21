# Implementation Roadmap

This roadmap is for turning the spec into working OSS code.

## Phase 1: Reference Validator

Build:

- schema validator CLI,
- taxonomy validator,
- example validator,
- ANCP document pretty-printer.

Commands:

```bash
ancp-validate examples/typescript/result.check.json
ancp-validate --schema schemas/ancp-1.0.schema.json examples/**/*.json
```

This phase proves the protocol artifacts are usable before any language adapter exists.

## Phase 2: TypeScript Adapter

Why first:

- strong Compiler API,
- common agent workload,
- stable native diagnostic codes,
- clear repair path through language service and ESLint.

Implement:

- `manifest`,
- `capabilities`,
- `check` using TypeScript Compiler API,
- ESLint JSON ingestion,
- `explain`,
- repair plans for missing imports, unused imports, missing args, simple type annotation changes,
- verification through `tsc --noEmit`.

Do not start with auto-apply. Plans first.

## Phase 3: Python Adapter

Implement:

- CPython syntax check,
- Pyright JSON ingestion,
- mypy JSON ingestion,
- Ruff JSON ingestion,
- repair plans for missing dependency, unused import, formatter, simple lint fixes,
- verification through compileall/Pyright/mypy/Ruff.

## Phase 4: Rust Adapter

Implement:

- Cargo JSON ingestion,
- rustc diagnostics mapping,
- suggestion mapping,
- `cargo fix` as batch repair action,
- verification through `cargo check` and `cargo test`.

## Phase 5: Go Adapter

Implement:

- `go list -json`,
- `go test -json`,
- gopls diagnostic ingestion,
- repair plans for gofmt, missing imports, unused imports,
- verification through `go test ./...`.

## Phase 6: C/C++ Adapter

Implement:

- compile database discovery,
- GCC JSON/SARIF ingestion,
- clang/clang-tidy parsing,
- fix-it mapping,
- verification through compile commands.

## Phase 7: JVM And .NET Adapters

Implement Java first through Java Compiler API.

Implement .NET through Roslyn/MSBuild APIs.

Add Kotlin/Scala through build-system integrations after Java/C# foundations exist.

## Phase 8: Swift, Zig, Ruby, PHP, Dart

Implement adapters where the protocol has already proven itself.

Focus on:

- SourceKit-LSP for Swift,
- build/test command safety for Zig,
- syntax/linter composition for Ruby/PHP,
- Dart analyze/fix plan mapping.

## Release Criteria

The first OSS release should include:

- protocol docs,
- schema,
- taxonomies,
- examples,
- validator,
- one serious adapter,
- conformance tests,
- CI that validates every protocol artifact.

