# Agent Native Compiler Protocol

Agent Native Compiler Protocol, or ANCP, is a language-neutral protocol for making existing compiler, linter, formatter, test, and build toolchains usable by coding agents without forcing every ecosystem to invent a new programming language.

The core idea is simple:

> Existing tools may keep their native internals. ANCP defines the stable machine contract that adapters expose to agents.

ANCP turns tool output into structured diagnostics, repair hints, repair plans, verification steps, code graph facts, effect/capability metadata, and version-matched agent guidance. It is designed to sit above current languages such as TypeScript, Python, Rust, Go, Java, C, C++, C#, Swift, Kotlin, Julia, Zig, Ruby, PHP, Lua, Perl, R, Haskell, OCaml, Erlang, Elixir, Clojure, Nix, Terraform, Dockerfile, SQL, JSON, TOML, YAML, and others.

## What This Repository Contains

This repository is the public ANCP 1.0 contract and Python reference implementation:

| Area | Status | Location |
| --- | --- | --- |
| Normative protocol spec | Written | [spec/ancp-1.0.md](spec/ancp-1.0.md) |
| JSON Schema contract | Written | [schemas/ancp-1.0.schema.json](schemas/ancp-1.0.schema.json) |
| Core diagnostic taxonomy | Written | [taxonomies/diagnostic-kinds.json](taxonomies/diagnostic-kinds.json) |
| Core repair taxonomy | Written | [taxonomies/repair-kinds.json](taxonomies/repair-kinds.json) |
| Core effect taxonomy | Written | [taxonomies/effect-kinds.json](taxonomies/effect-kinds.json) |
| CLI contract | Written | [docs/cli-contract.md](docs/cli-contract.md) |
| Adapter authoring guide | Written | [docs/adapter-authoring.md](docs/adapter-authoring.md) |
| Conformance rules | Written | [docs/conformance.md](docs/conformance.md) |
| Security model | Written | [docs/security.md](docs/security.md) |
| Language mapping guide | Written | [docs/language-mapping.md](docs/language-mapping.md) |
| Example protocol documents | Written | [examples](examples) |
| Reference CLI/package | Implemented | [src/ancp](src/ancp) |
| Compiler-name shim layer | Implemented | [docs/invisible-compiler-layer.md](docs/invisible-compiler-layer.md) |
| Compact agent signal layer | Implemented | [docs/compact-signal-layer.md](docs/compact-signal-layer.md) |
| Native-tool adapters | Implemented | [src/ancp/adapters](src/ancp/adapters) |
| Bug corpus | Implemented | [examples/buggy](examples/buggy) |
| Repository verifier | Implemented | [tools/verify_repo.py](tools/verify_repo.py) |
| Toolchain availability checker | Implemented | [tools/check_toolchains.py](tools/check_toolchains.py) |

## Why ANCP Exists

Most compiler and test outputs were designed for humans:

- prose error messages,
- unstable text formatting,
- file-line-column references without durable anchors,
- no typed repair intent,
- no machine-readable validation loop,
- no explicit distinction between safe edits and dangerous commands,
- documentation that may not match the installed tool version.

Coding agents can work around this, but every workaround is brittle. ANCP standardizes the missing layer.

ANCP does not replace compilers, language servers, static analyzers, package managers, or test runners. It wraps them with a stable protocol:

```text
compiler / linter / test / LSP / build tool
                 |
                 v
          language adapter
                 |
                 v
      ANCP JSON documents
                 |
                 v
      agents, IDEs, CI, repair bots
```

For agent terminals, ANCP can also render compact raw text from the same JSON:

```text
normal compiler command
        |
        v
ANCP result.check JSON + raw native logs
        |
        v
minimal root-cause text for agents
```

See [Compact Signal Layer](docs/compact-signal-layer.md) for `ancp enable`,
`auto-compact`, token savings telemetry, and raw-output fallback behavior.

## Design Principles

1. **Language neutral, not language vague.**
   ANCP uses broad canonical categories, but every diagnostic still keeps native tool codes and source metadata.

2. **Stable IDs over prose parsing.**
   Agents match `canonicalCode`, `nativeCode`, `repairId`, and `documentKind`, not English error strings.

3. **Repair plans before mutation.**
   ANCP repair is a plan with preconditions, edits, commands, safety level, and verification steps. Blind auto-editing is not the protocol default.

4. **Positions must be relocatable.**
   Line and column are not enough. ANCP locations carry ranges, file digests, expected text, and optional anchors such as symbols, AST paths, and context hashes.

5. **Security is part of the contract.**
   Plans declare capabilities, filesystem/network/process effects, risk, and whether review is required.

6. **Adapters are honest about support.**
   ANCP uses profiles and capability negotiation. A Python adapter can be useful without supporting Rust borrow diagnostics. A linter-only adapter can be conformant without build support.

7. **Compatibility with existing standards matters.**
   ANCP is designed to interoperate with JSON Schema, LSP, SARIF, SPDX, CycloneDX, JSON Patch, and JSON canonicalization rather than replacing them.

## Protocol Documents

Every ANCP payload is a JSON document with:

- `ancpVersion`
- `documentKind`
- `producer`
- `createdAt`
- document-specific fields

The main document kinds are:

| Kind | Purpose |
| --- | --- |
| `manifest.adapter` | Describes an adapter implementation and its supported profiles. |
| `manifest.capabilities` | Describes discovered project capabilities, operations, tools, languages, and effects. |
| `result.check` | Reports diagnostics from compile/lint/type/test/build checks. |
| `result.explain` | Explains a diagnostic or repair in structured form. |
| `plan.repair` | Describes repair actions, edits, commands, preconditions, and verification. |
| `result.apply` | Reports the result of applying a repair plan. |
| `result.verify` | Reports post-repair validation. |
| `graph.code` | Reports symbols, dependencies, call edges, ownership edges, or module relationships. |
| `result.skills` | Returns version-matched agent guidance from the adapter. |

## Profiles

ANCP is split into profiles so most languages can implement it without lying about capabilities.

| Profile | Required | Purpose |
| --- | --- | --- |
| `core` | Yes | Discovery, check results, diagnostics, locations, taxonomy, versioning. |
| `explain` | Recommended | Structured diagnostic explanations. |
| `repair-plan` | Recommended | Machine-readable repair plans. |
| `repair-apply` | Optional | Transactional repair application. |
| `verify` | Recommended | Post-repair validation and diagnostic delta reporting. |
| `graph` | Optional | Code graph, symbol graph, dependency graph. |
| `effects` | Optional | Capability and effect metadata. |
| `skills` | Optional | Version-matched agent instructions. |
| `export` | Optional | Export to SARIF, CycloneDX, SPDX, or project-native formats. |

## Minimal Adapter Loop

A conformant core adapter can expose this loop:

```bash
ancp manifest
ancp capabilities
ancp check
ancp explain ancp.diag.symbol.unresolved
ancp repair --plan
ancp verify
```

The adapter may internally call `tsc`, `pyright`, `ruff`, `pytest`, `rustc`, `cargo check`, `go test`, `mypy`, `clang`, `javac`, an LSP server, or any other native tool.

## Invisible Compiler Layer

The reference implementation includes both an agent-facing CLI and a compiler-facing shim layer.

Install:

```bash
python -m pip install -e .
```

Create local compiler-name shims:

```bash
ancp install-shims --dir .ancp/bin
```

Prepend `.ancp/bin` to PATH, then keep using normal commands:

```bash
cargo check
rustc main.rs
tsc --noEmit
python -m py_compile app.py
julia app.jl
kotlinc Main.kt
gcc -fsyntax-only main.c
clang++ -fsyntax-only main.cpp
bash -n script.sh
pwsh -NoProfile -File script.ps1
terraform validate
```

The native compiler output and exit code are preserved. ANCP writes a structured sidecar:

```text
.ancp/last-check.json
```

See [docs/invisible-compiler-layer.md](docs/invisible-compiler-layer.md).

## Example

```json
{
  "ancpVersion": "1.0.0",
  "documentKind": "result.check",
  "producer": {
    "name": "ancp-typescript-adapter",
    "version": "1.0.0"
  },
  "createdAt": "2026-05-21T00:00:00Z",
  "status": "failed",
  "workspace": {
    "rootUri": "file:///repo",
    "workspaceId": "sha256:8f9f0b7a"
  },
  "run": {
    "runId": "run-ts-001",
    "command": ["tsc", "--noEmit", "--pretty", "false"],
    "startedAt": "2026-05-21T00:00:00Z",
    "durationMs": 421
  },
  "toolchain": [
    {
      "name": "typescript",
      "version": "5.8.3",
      "role": "typechecker"
    }
  ],
  "diagnostics": [
    {
      "id": "diag-001",
      "canonicalCode": "ancp.diag.symbol.unresolved",
      "nativeCode": "TS2304",
      "severity": "error",
      "kind": "symbol",
      "message": "Cannot find name 'renderUser'.",
      "primaryLocation": {
        "artifact": {
          "uri": "file:///repo/src/app.ts",
          "languageId": "typescript"
        },
        "range": {
          "unit": "utf16",
          "start": { "line": 12, "character": 9 },
          "end": { "line": 12, "character": 19 }
        }
      },
      "repairHints": [
        {
          "repairId": "ancp.repair.symbol.import_missing",
          "title": "Import the missing symbol from an existing module",
          "confidence": 0.82,
          "safetyLevel": "review_required"
        }
      ]
    }
  ]
}
```

## Repository Verification

Run:

```bash
python -m pip install -e ".[dev]"
python tools/fetch_sources.py
python tools/audit_contracts.py
python tools/verify_repo.py
pytest
python tools/run_bug_corpus.py
python tools/check_toolchains.py
python -m build
python -m twine check dist/*
```

The verification stack checks:

- every JSON file parses,
- the main ANCP schema parses,
- examples validate against the schema when `jsonschema` is installed,
- taxonomy entries have stable IDs,
- documentation links point to existing local files,
- the contract audit covers document kinds, profiles, docs, examples, and source research,
- package import, parser, renderer, proxy, shim, and CLI behavior pass unit tests,
- the multilingual bug corpus emits ANCP JSON/Markdown where native tools are installed,
- the wheel and sdist pass packaging metadata checks.

## Production Quality Bar

This repository treats the protocol contract and reference implementation as production-facing infrastructure.

For ANCP itself, production quality means:

- the normative spec, schema, taxonomies, examples, adapter docs, and reference package agree with each other,
- example protocol documents validate against the schema,
- every claimed document kind and profile is documented,
- repair plans include preconditions, effects, safety levels, and verification steps,
- local source snapshots exist for the standards and language/toolchain docs used to design the contract,
- verification can be rerun locally with deterministic scripts,
- normal compiler commands can be routed through local compiler-name shims without changing project build scripts.

For an ANCP adapter, production quality means:

- it emits valid ANCP JSON on success and failure,
- it preserves native diagnostic codes and tool versions,
- it uses structured native APIs when available instead of parsing prose,
- it never mutates files in plan mode,
- it labels risky actions honestly,
- it does not claim verification unless verification actually ran.

## Relationship To Existing Standards

ANCP intentionally borrows from existing standards:

- JSON Schema Draft 2020-12 for validation.
- LSP for locations, diagnostics, code actions, and language tooling shape.
- SARIF for static-analysis interchange and code-scanning export.
- RFC 6902 JSON Patch for metadata patch operations where JSON patching is appropriate.
- RFC 8785 JSON Canonicalization Scheme for deterministic signing and hashing.
- SPDX and CycloneDX for software identity, dependency, licensing, and bill-of-materials export.

ANCP adds the missing agent-facing contract: typed repair intent, repair plans, validation loops, adapter profiles, stable agent guidance, and cross-language diagnostic normalization.

## License

This repository is licensed under Apache-2.0. The intent is permissive OSS use by language adapter authors, IDE authors, agent runtimes, CI systems, and research projects.
