# ANCP Research Corpus

This folder contains the research base for Agent Native Compiler Protocol 1.0.

The goal is not to mirror the entire internet documentation for every language. The goal is to preserve the official and source-level documents that matter for ANCP:

- compiler CLI behavior,
- structured diagnostic output,
- native diagnostic IDs,
- source ranges and location models,
- quick-fix or code-action systems,
- build/test result formats,
- formatter/linter machine output,
- language server diagnostic behavior,
- package/dependency metadata,
- safety/effect surfaces.

## Layout

| Path | Purpose |
| --- | --- |
| `source-docs/sources.json` | Curated list of official/source documents to fetch. |
| `source-docs/snapshots/` | Downloaded local snapshots of the source documents. |
| `source-docs/fetch-report.json` | Fetch status for each source. |
| `languages/` | Per-language research summaries. |
| `standards/` | Existing standard comparison notes. |
| `tooling-matrix.md` | Cross-language matrix used to validate ANCP abstractions. |

## Evidence Rule

When ANCP defines a core abstraction, it should be traceable to at least one of:

- an official compiler/toolchain document,
- an official language server document,
- a mature standard such as LSP, SARIF, JSON Schema, JSON Patch, SPDX, CycloneDX, or JCS,
- a widely adopted ecosystem tool when the language itself does not provide a compiler-like surface.

## Snapshot Rule

Downloaded snapshots are source evidence, not vendored documentation for redistribution as a docs product. Public docs pages remain owned and licensed by their upstream authors. ANCP docs should summarize and link rather than copy large upstream text.

