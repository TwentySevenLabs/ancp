# ANCP Execution Breakdown

This plan follows `docs/vision-doctrine.md`.

## Task 1: Package Foundation

- Add `pyproject.toml`.
- Add package source under `src/ancp`.
- Include schema and taxonomies as package data.
- Add console scripts.
- Add `MANIFEST.in`.
- Ensure editable install works.

## Task 2: Protocol Validation Core

- Load ANCP schema.
- Validate JSON documents.
- Validate examples.
- Expose `ancp validate`.
- Keep `tools/verify_repo.py` as repo-level validation.

## Task 3: Adapter Framework

- Define adapter base class.
- Define native tool specs.
- Discover matching adapters from workspace markers and file extensions.
- Normalize tool missing states into valid ANCP JSON.
- Preserve native tool metadata.

## Task 4: Compiler-Facing Layer

- Add `ancp compile <adapter> -- <native command>`.
- Add `ancp-*` direct proxy entrypoints.
- Add `ancp install-shims`.
- Generate native-name wrappers into `.ancp/bin`.
- Preserve stdout, stderr, and exit code.
- Write `.ancp/last-check.json`.

## Task 5: Language Adapters

- Python: pyright, ruff, CPython compileall.
- TypeScript: tsc.
- JavaScript: ESLint JSON.
- Rust: cargo/rustc JSON.
- Go: go test JSON.
- C/C++: GCC/Clang diagnostics.
- Java: javac.
- Kotlin: kotlinc.
- Julia: Julia parser execution.
- C#/.NET: dotnet build.
- Swift: swift build.
- Zig: zig build.
- Ruby: ruby -c.
- PHP: php -l.
- Dart: dart analyze.
- Scala: scala-cli/scalac.

## Task 6: Agent Markdown Compression

- Render ANCP JSON to compact Markdown.
- Group diagnostics by canonical/native code.
- Show high-signal location/message/repair hint.
- Limit diagnostic count.
- Preserve verification guidance.
- Avoid raw log bloat.

## Task 7: Buggy Corpus

- Add intentionally broken programs for major languages.
- Include common root causes: missing imports, unresolved symbols, type mismatches, wrong arity, syntax errors.
- Add runner that executes installed-tool smoke checks.
- Emit JSON and Markdown artifacts under `.ancp/bug-corpus`.

## Task 8: Tests

- Validate all examples.
- Validate generated manifest/capabilities/skills/graph docs.
- Test parsers for TypeScript, Pyright, Rust.
- Test compiler proxy.
- Test shim installation.
- Test Markdown rendering.

## Task 9: OSS Release Surface

- Add CI workflow.
- Add GitHub release plan.
- Add invisible compiler layer docs.
- Update README quickstart.
- Make ignored/generated artifacts clear.
- Keep research manifest and summaries commit-ready.

## Task 10: Verification Loop

- Run `python -m compileall`.
- Run `pytest`.
- Run `python tools/verify_repo.py`.
- Run `python tools/audit_contracts.py`.
- Run package build.
- Run local install smoke commands.
- Run bug corpus where native tools exist.
- Fix failures until clean.

