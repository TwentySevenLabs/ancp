# ANCP Vision Doctrine

This document is the operating doctrine for Agent Native Compiler Protocol.

It consolidates the project intent and should guide implementation decisions when details are ambiguous.

## One-Sentence Mission

ANCP makes normal compiler, build, run, lint, and test workflows emit compact, structured, agent-native diagnostics without forcing developers or agents to scrape noisy human prose.

## The Core Belief

Programming languages do not need to be replaced first.

The root compiler/toolchain layer needs an agent-native protocol.

Developers should keep doing normal work:

```bash
cargo check
rustc main.rs
tsc --noEmit
python app.py
julia app.jl
kotlinc Main.kt
gcc main.c
clang++ main.cpp
go test ./...
dotnet build
```

The invisible ANCP layer should make those same workflows produce:

1. native stdout/stderr and native exit code, unchanged,
2. ANCP JSON sidecar diagnostics,
3. compact Markdown for agents,
4. repair hints and verification commands,
5. security/effect metadata.

The developer should not need to learn a new workflow just to make code agent-readable.

## Non-Negotiables

1. **Invisible by default.**
   ANCP must integrate into the compiler path. The CLI is useful, but the project goal is not "an agent calls another CLI." The goal is: normal compiler use produces agent-native diagnostics.

2. **Native compiler truth first.**
   ANCP must preserve native compiler behavior, native error codes, native exit codes, and native output. It wraps or plugs into toolchains; it does not pretend to be the compiler.

3. **Structured JSON is the protocol.**
   JSON is the durable machine contract. Markdown is a derived agent briefing, not the source of truth.

4. **Markdown must reduce bloat.**
   Compiler output is often 90 percent noise for agents. ANCP Markdown should compress diagnostics into root-cause groups, precise locations, native codes, repair hints, and verification steps.

5. **No fake support.**
   If a compiler/tool is not installed or a language lacks stable structured output, ANCP must report that honestly as valid ANCP JSON. It must not fabricate successful checks.

6. **Multi-language from the start.**
   The important targets include Rust, Kotlin, Python, Julia, TypeScript, C, C++, Go, Java, C#/.NET, Swift, Zig, Ruby, PHP, Dart, Scala, JavaScript, Shell, PowerShell, Lua, Perl, R, Haskell, OCaml, Erlang, Elixir, Clojure, Nix, Terraform, Dockerfile, SQL, JSON, TOML, and YAML.

7. **Security is part of the protocol.**
   Build/test/repair commands can execute arbitrary code. ANCP must label effects, safety levels, and risky operations instead of hiding them.

8. **Production-grade developer experience.**
   Install should be simple. A developer should run a few commands, add shims or compiler hooks, keep coding normally, and see ANCP output appear.

9. **Verification over claims.**
   Do not say something is fully working unless it has been run. Use labels like implemented, schema-validated, syntax-checked, smoke-tested, or full-run verified.

10. **Spec evolves through implementation.**
    The spec is mature enough to build against. If implementation exposes a gap, make the right computer-science decision, update schema/docs/tests, and keep moving.

## Product Shape

ANCP has four layers.

### Layer 1: Protocol Contract

This is the stable standard:

- JSON Schema,
- document kinds,
- diagnostic taxonomy,
- repair taxonomy,
- effect taxonomy,
- adapter profiles,
- conformance rules,
- security model.

### Layer 2: Compiler-Facing Integration

This is the invisible layer:

- compiler-name shims,
- compiler proxy mode,
- future direct compiler plugins,
- future build-system integrations.

The shims are the bootstrap route. Deeper compiler plugins are the long-term native route.

### Layer 3: Agent-Facing Compression

This turns JSON into useful agent context:

- root-cause grouping,
- repeated-error compression,
- high-signal locations,
- native code preservation,
- repair hint summary,
- verification command summary,
- context-budget discipline.

### Layer 4: Reference Tooling

This makes the standard usable immediately:

- installable Python package,
- `ancp` CLI,
- `ancp install-shims`,
- `ancp check`,
- `ancp compile`,
- `ancp render`,
- `ancp validate`,
- adapter framework,
- tests and CI,
- buggy multilingual corpus,
- release docs.

## Intended Developer Experience

Fresh install:

```bash
python -m pip install ancp
ancp install-shims --dir .ancp/bin
```

Add `.ancp/bin` to the front of `PATH`.

Then normal commands work:

```bash
cargo check
tsc --noEmit
python app.py
julia app.jl
kotlinc Main.kt
gcc -fsyntax-only main.c
```

ANCP writes:

```text
.ancp/last-check.json
```

Agents can read:

```bash
ancp render --from .ancp/last-check.json
```

This should feel like infrastructure, not a separate manual ritual.

## What ANCP Must Optimize For

1. **Agent context efficiency**
   Show what matters, group repetitions, keep root causes visible, and avoid dumping huge compiler logs into model context.

2. **Compiler fidelity**
   Preserve native code, severity, location, message, tool version, command, exit code, and source tool.

3. **Repairability**
   Every diagnostic should try to expose repair intent, even when safe auto-edit is unavailable.

4. **Verification**
   Every proposed repair path should tell the agent how to verify.

5. **Safety**
   Commands that can install dependencies, run tests, write files, call network, or mutate outside workspace must be labeled.

6. **Language honesty**
   Strong compilers get richer diagnostics. Dynamic languages may rely on syntax checkers, linters, language servers, and static analyzers. Both are valid if represented honestly.

## Language Strategy

### Rust

Use `cargo check --message-format=json` and `rustc --error-format=json` when possible. Rust is one of the strongest ANCP targets because native structured diagnostics and suggestions already exist.

### TypeScript / JavaScript

Use TypeScript Compiler API/`tsc` and ESLint JSON. TypeScript should become one of the first polished adapters because it has stable diagnostic codes and strong language-service repair actions.

### Python

Compose CPython syntax checks, Pyright, Ruff, mypy, and test runners. Python proves ANCP must support multi-tool language adapters.

### Julia

Use Julia parser/package/test surfaces and later LanguageServer.jl or StaticLint.jl. The first implementation should at least parse/check files and emit honest ANCP failures.

### Kotlin

Use `kotlinc` and later Gradle/Kotlin compiler integrations. Kotlin needs build-context awareness and should not be faked through shallow text-only assumptions.

### C / C++

Use GCC/Clang diagnostics, fix-its, and `compile_commands.json`. C/C++ proves compile context is mandatory.

### Other Important Languages

Go, Java, C#/.NET, Swift, Zig, Ruby, PHP, Dart, Scala, and JavaScript should have native-tool-backed adapters that preserve output and emit valid ANCP.

## Quality Bar

The project is not ready just because files exist.

It is ready when:

- package installs locally,
- CLI commands work,
- compiler shims install,
- normal compiler commands pass through shims,
- ANCP JSON validates,
- Markdown render is compact and useful,
- tests pass,
- CI is configured,
- buggy corpus runs for installed compilers,
- release docs explain how to publish,
- limitations are explicit,
- repeated verification passes.

## What Not To Do

- Do not make ANCP only a separate agent command.
- Do not hide native compiler output.
- Do not replace native exit codes.
- Do not hallucinate diagnostics when tools are missing.
- Do not dump massive raw logs into Markdown.
- Do not make repair apply automatic by default.
- Do not mark dangerous commands safe.
- Do not over-design future compiler plugins before the shim/proxy path works.

## Current Execution Plan

1. Package the repo as an installable Python project.
2. Implement protocol validation and schema loading.
3. Implement native adapter framework.
4. Implement compiler proxy mode.
5. Implement compiler-name shims for normal workflows.
6. Implement adapters for the major language set.
7. Implement compact Markdown rendering.
8. Add multilingual buggy corpus and smoke runner.
9. Add tests, CI, release docs, and GitHub plan.
10. Run verification repeatedly and fix every concrete failure.

## Success Definition

The first public release succeeds if someone can:

1. clone the repo,
2. install it,
3. run `ancp install-shims`,
4. compile broken code normally,
5. see native compiler output,
6. find `.ancp/last-check.json`,
7. run `ancp render --from .ancp/last-check.json`,
8. hand the Markdown to an agent,
9. get a compact, useful diagnosis instead of a noisy compiler dump.

That is the revolution: compilers become agent-readable without developers changing how they code.
