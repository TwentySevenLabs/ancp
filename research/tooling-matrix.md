# Cross-Language Tooling Matrix

This matrix is the evidence backbone for ANCP 1.0. It summarizes what the major language ecosystems expose today and what ANCP must abstract.

The key conclusion:

> There is no single universal compiler surface, but there is a stable cross-language shape: discover tools, run checks, normalize diagnostics, preserve native codes, locate source spans, carry fix hints when available, emit repair plans, and verify through native commands.

## Language And Toolchain Summary

| Ecosystem | Primary check surface | Machine-readable output | Native repair/fix surface | Adapter implication |
| --- | --- | --- | --- | --- |
| Python | `py_compile`, `compileall`, Pyright, mypy, Ruff | Pyright `--outputjson`, mypy `--output json`, Ruff `output-format=json`; CPython syntax errors are text/exception based | Ruff `--fix`; Pyright/LSP code actions; mypy mostly reports | ANCP must support language ecosystems where the "compiler" is a set of analyzers rather than one canonical compiler. |
| TypeScript | `tsc`, TypeScript Compiler API | Compiler API returns structured diagnostics; CLI is mostly text | Language service code fixes; ESLint fixes/suggestions | Adapter should prefer Compiler API over parsing `tsc` text. |
| JavaScript | ESLint, TypeScript for typed JS, bundlers, Node test runners | ESLint `json` and `json-with-metadata` | ESLint `--fix`, suggestions with fix ranges | ANCP must separate syntax/type/lint/build/test sources. |
| Go | `go build`, `go test`, `go list`, `go tool compile`, `gopls` | `go test -json`, `go list -json`; gopls LSP diagnostics | `gofmt`, `go fix`, gopls code actions | ANCP needs streaming test events and package metadata, not only compiler errors. |
| Rust | `rustc`, `cargo check`, `cargo test`, `cargo fix` | `rustc --error-format=json`; Cargo `--message-format=json` | rustc suggestions; `cargo fix` | ANCP can map Rust spans, children, suggestions, and applicability almost directly. |
| C/C++ | GCC, Clang, clang-tidy, clangd | GCC JSON/SARIF diagnostics; Clang text/fix-its; clang-tidy diagnostics; compilation database JSON | GCC/Clang fix-it hints; clang-tidy `-fix` | ANCP must model compile commands, translation units, include paths, macro context, and fix-it ranges. |
| Java | `javac`, Java Compiler API, build tools | Java Compiler API exposes `Diagnostic` objects; CLI text | Annotation processors, IDE code actions, Error Prone/Checker Framework fixes | Adapter should prefer Java Compiler API when available and preserve `Diagnostic.Kind`, position, source, code. |
| Kotlin | `kotlinc`, Gradle/Maven, IntelliJ/K2 APIs | CLI diagnostics mostly text; Gradle/IDE APIs richer | IDE quick fixes; compiler plugins unstable | ANCP should support text-backed diagnostics with native warning names and build-tool context. |
| C#/.NET | `dotnet build`, Roslyn, analyzers, `dotnet format` | Roslyn APIs structured; MSBuild logs; `dotnet format --report` JSON | Roslyn code fixes; `dotnet format` fix filters | Adapter should integrate Roslyn/MSBuild rather than raw `csc` where possible. |
| Swift | `swiftc`, SwiftPM, SourceKit-LSP | SourceKit-LSP/LSP diagnostics; compiler diagnostics descriptions exist | SourceKit code actions/quick fixes | ANCP should use LSP and build output as complementary sources. |
| Zig | `zig build`, `zig test`, direct `zig build-exe` | Build summary is structured in CLI text; no stable broad JSON diagnostic contract found in docs | Build system can mutate/generated files; fixes mostly manual | ANCP must not require native JSON output; text adapters remain valid if they normalize honestly. |
| Ruby | `ruby -c`, warnings, RuboCop, Solargraph | `ruby -c` text; RuboCop JSON if used | RuboCop autocorrect; LSP code actions | Adapter should treat Ruby core syntax check plus linter/LSP as separate tools. |
| PHP | `php -l`, PHPStan/Psalm, PHPCS | `php -l` text; static analyzers have machine formats | PHPCS fixer, Rector, IDE actions | Adapter must handle dynamic language syntax check plus optional analyzers. |
| Dart | `dart analyze`, `dart fix` | Analyzer output is CLI-oriented; analysis server/LSP structured | `dart fix --dry-run` and `--apply` | ANCP repair plan split matches Dart's dry-run/apply model. |
| Scala | `scalac`, Scala CLI, sbt, Metals/BSP | Compiler/build output often text; BSP/Metals structured | Scala CLI actionable diagnostics; Scalafix | ANCP should represent build server protocol/source generator/dependency context. |
| Julia | `julia`, `Meta.parse`, LanguageServer.jl, StaticLint.jl, Pkg/test workflows | Parser errors are text/exception based; LanguageServer.jl/StaticLint.jl provide richer structured diagnostic paths | Mostly IDE/LSP actions and package-specific tooling; core syntax repair is manual | ANCP should treat Julia as a dynamic compiler/JIT ecosystem: parse first, then layer LSP/static lint and test execution when installed. |
| Shell/PowerShell | `bash -n`, ShellCheck, PowerShell Parser API | ShellCheck JSON; PowerShell parser errors can be converted from objects | ShellCheck suggestions, PSScriptAnalyzer fixes | ANCP must support automation languages because agents frequently edit scripts and CI glue. |
| Lua/Perl/R | `luac -p`, `perl -c`, R `parse()` | Mostly text diagnostics; R parser exposes conditions | Mostly manual or linter-driven | Dynamic language adapters can start with parser gates and layer linters later. |
| Haskell/OCaml/Erlang/Elixir/Clojure | GHC, ocamlc, erlc, elixirc, clj-kondo | Compiler text; clj-kondo JSON | Ecosystem-specific formatters/lint fixers | Functional ecosystems fit ANCP if adapters preserve native compiler output and module/build context. |
| Config/data/IaC | JSON, TOML, YAML, Nix, Terraform, Dockerfile, SQL | JSON/TOML/YAML parsers; Terraform JSON; hadolint/sqlfluff JSON | Formatters and linters, usually review-required | Agents edit config constantly; ANCP should normalize syntax/config failures as first-class diagnostics. |

## Common Fields Found Across Ecosystems

Nearly every mature toolchain can supply or infer:

- language ID,
- tool name and version,
- command arguments,
- exit status,
- source artifact URI,
- source range or position,
- severity,
- human message,
- native diagnostic code or rule ID,
- diagnostic category,
- related locations or notes,
- suggested edits or fix IDs if supported,
- verification command.

ANCP core therefore requires these fields or explicit absence where unavailable.

## What Cannot Be Universal

ANCP must not require these as core:

- full AST,
- full type model,
- structured effect inference,
- safe auto-fixes,
- package graph,
- test graph,
- language server availability,
- generated-code classification,
- compiler plugin APIs,
- binary artifact metadata.

These belong in optional profiles.

## Diagnostic Shape Comparison

| Feature | Python | TypeScript | Go | Rust | C/C++ | JVM | .NET | Swift | Dynamic langs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Native code/rule ID | Analyzer-dependent | `TSxxxx` | Mixed | `Exxxx`/lint names | warning flags/rule names | diagnostic codes/API | `CSxxxx`, analyzer IDs | diagnostic descriptions | linter-dependent |
| Severity | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Primary span | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Often |
| Related spans | Analyzer-dependent | Yes via API | gopls/LSP | Yes children/spans | Yes notes/path | Yes | Yes | Yes | Tool-dependent |
| Suggested edits | Ruff/Pyright | Language service/ESLint | gopls/go fix | rustc/cargo fix | fix-its | IDE/tools | Roslyn | SourceKit | Linter-dependent |
| JSON output | Tool-dependent | API, not core CLI | Yes for tests/list | Yes | GCC/SARIF, tools | API | API/report | LSP | Tool-dependent |

## Repair Model Lessons

Real tools split into four repair classes:

1. **Textual fix-it**: replace this range with this text.
   - Rust suggestions, GCC fix-its, Clang fix-its, ESLint fixes.

2. **Semantic code action**: perform an IDE/compiler-service action.
   - TypeScript language service, Roslyn, SourceKit-LSP, gopls.

3. **Batch fixer**: run a native command that edits many files.
   - `cargo fix`, `ruff --fix`, `eslint --fix`, `dart fix --apply`, `dotnet format`.

4. **Manual repair hint**: the tool knows the class of issue but cannot safely fix it.
   - Type mismatches, ambiguous imports, ownership/lifetime issues, test failures.

ANCP repair plans must support all four.

## Verification Model Lessons

Every adapter needs a native validation path:

- Python: `python -m py_compile`, `pyright`, `mypy`, `ruff check`, `pytest`.
- TypeScript: `tsc --noEmit`, ESLint, tests.
- Go: `go test ./...`, `go test -json`, `go vet`.
- Rust: `cargo check`, `cargo test`.
- C/C++: build command, CTest, clang-tidy, GCC/Clang compile.
- Java/Kotlin/Scala: Gradle/Maven/sbt/Scala CLI test/build tasks.
- C#: `dotnet build`, `dotnet test`, `dotnet format --verify-no-changes`.
- Swift: `swift build`, `swift test`.
- Zig: `zig build`, `zig build test`, `zig test`.
- Ruby/PHP: syntax check plus test runner and linter/static analyzer.
- Dart: `dart analyze`, `dart test`.
- Julia: `julia --startup-file=no --history-file=no`, parser checks through `Meta.parse`/`Meta.parseall`, LanguageServer.jl/StaticLint.jl when available, and `Pkg.test` for package verification.
- Shell/PowerShell: `bash -n`, ShellCheck, PowerShell Parser API, PSScriptAnalyzer.
- Lua/Perl/R: `luac -p`, `perl -c`, `Rscript -e parse(...)`.
- Haskell/OCaml/Erlang/Elixir/Clojure: compiler syntax/type checks and clj-kondo JSON.
- Config/data/IaC: parser validation for JSON/TOML/YAML, `nix-instantiate --parse`, `terraform validate -json`, hadolint, sqlfluff.

ANCP must model verification as commands and diagnostic delta, not as a boolean.

## Safety Model Lessons

Fix commands can do more than edit code:

- `dotnet format` may restore, compile, and run analyzers.
- `cargo fix` and build scripts can execute project build logic.
- `go test` can execute arbitrary tests.
- `npm`/package scripts can execute arbitrary commands.
- C/C++ builds can run generators.
- Gradle/Maven/sbt builds can execute plugins.
- Zig build scripts are code.

Therefore ANCP repair actions and verification steps must declare effects and trust requirements. The protocol cannot treat "compiler command" as automatically safe.

## Required ANCP Abstractions Confirmed By Research

The research confirms these core abstractions are necessary:

- document envelope,
- adapter manifest,
- capability discovery,
- run metadata,
- toolchain metadata,
- workspace identity,
- diagnostics with native and canonical codes,
- source artifacts and ranges,
- related locations,
- symbols,
- repair hints,
- repair plans,
- edit operations,
- commands with effects,
- preconditions,
- verification steps,
- diagnostic delta,
- optional graph facts,
- optional skills/guidance,
- optional export mappings.

## Adapter Strategy By Ecosystem

| Ecosystem | Preferred adapter strategy |
| --- | --- |
| Python | Compose CPython syntax compile, Pyright or mypy, Ruff, pytest. Prefer machine output where supported. |
| TypeScript | Use TypeScript Compiler API for diagnostics; use language service for fixes; optionally consume ESLint JSON. |
| JavaScript | Use ESLint JSON and parser errors; optionally TypeScript for JS projects; preserve rule metadata. |
| Go | Use `go list -json` for package graph, `go test -json` for tests, gopls for diagnostics/actions, `go build` for verification. |
| Rust | Use Cargo JSON and rustc JSON; map suggestions/applicability; call `cargo fix` only as review-required batch action. |
| C/C++ | Require or infer `compile_commands.json`; parse GCC JSON/SARIF where available; consume clang-tidy and clangd when available. |
| Java | Use Java Compiler API when implementing in JVM; preserve javac diagnostic source/kind/code/position. |
| Kotlin | Use build-tool integration first; direct `kotlinc` where simple; keep compiler-plugin assumptions optional. |
| C# | Use Roslyn/MSBuild APIs; consume `dotnet format --report` for fix reports. |
| Swift | Use SwiftPM + SourceKit-LSP; map compiler diagnostics and code actions. |
| Zig | Use `zig build` and `zig test`; treat build graph commands as effectful. |
| Ruby | Use `ruby -c` plus RuboCop/Solargraph if present. |
| PHP | Use `php -l` plus PHPStan/Psalm/PHPCS/Rector if present. |
| Dart | Use `dart analyze`; map `dart fix --dry-run` to plans and `--apply` to review-required apply. |
| Scala | Use Scala CLI/sbt/BSP/Metals; expose SemanticDB support under graph profile. |
| Julia | Use a no-startup parser pass for fast syntax diagnostics; integrate LanguageServer.jl/StaticLint.jl for semantic diagnostics; treat package tests and Pkg operations as effectful verification steps. |
| Shell | Prefer ShellCheck JSON; fall back to `bash -n` for syntax-only checks. |
| PowerShell | Use the parser API for syntax diagnostics; PSScriptAnalyzer can be layered as lint/repair metadata. |
| Lua/Perl/R | Use native parser/compile-only commands first; add language-specific linters as optional richer adapters. |
| Haskell/OCaml/Erlang/Elixir/Clojure | Use native compilers or clj-kondo; keep build-system integration optional because project setup differs heavily. |
| JSON/TOML/YAML | Use embedded parsers for deterministic syntax diagnostics with no external tool dependency. |
| Nix/Terraform/Dockerfile/SQL | Prefer native JSON-output tooling where available; report missing tools honestly. |
