# LSP Interoperability Guide

This guide covers how ANCP adapters that wrap Language Server Protocol servers should handle the overlap between LSP diagnostics/code-actions and ANCP diagnostics/repair-plans.

## When To Use LSP Vs CLI

Many toolchains expose both an LSP server and a CLI entry point. They serve different roles in ANCP.

| Concern | Preferred source | Reason |
| --- | --- | --- |
| Diagnostics | LSP (if server is already running) | Lower latency, richer metadata (related locations, symbols, code actions). |
| Code actions / repair hints | LSP | CLI rarely surfaces actionable fixes with edit spans. |
| Verification | CLI | LSP is stateful; verification requires reproducibility from a clean invocation. |
| Batch check (CI) | CLI | No server lifecycle to manage. |

If both sources are available, prefer LSP for diagnostics and CLI for verification. Adapters MUST document which source they use per operation in the adapter manifest or capabilities response.

Example capability note:

```json
{
  "check": { "source": "gopls", "transport": "lsp" },
  "verify": { "source": "go test -json", "transport": "cli" }
}
```

## Deduplication

When an adapter consumes both CLI and LSP output, the same native diagnostic often appears twice. Adapters MUST NOT emit duplicate diagnostics from the same native root cause.

Two diagnostics are considered duplicates when all of the following match:

- `nativeCode`
- artifact URI
- `range.start.line`
- `range.start.character`

When deduplicating, keep the source with richer metadata — the one that provides more of: `relatedLocations`, symbols, repair hints. Record the discarded source for traceability:

```json
{
  "nativeCode": "TS2304",
  "canonicalCode": "ancp.diag.symbol.unresolved",
  "data": {
    "duplicateSource": "tsc-cli"
  }
}
```

If both sources carry identical metadata, prefer LSP.

## Code Action To Repair Plan Mapping

LSP code actions map to ANCP `plan.repair` actions. The mapping is mechanical but requires safety annotation.

| LSP concept | ANCP field | Notes |
| --- | --- | --- |
| `CodeAction.title` | `action.title` | Preserve verbatim. |
| `CodeAction.kind` | `action.repairId` | Adapter SHOULD define a mapping table (see below). |
| `CodeAction.edit` (WorkspaceEdit) | `action.edits[]` | Convert `TextEdit` ranges to ANCP location format. |
| `CodeAction.isPreferred` | `action.confidence` | Preferred actions get higher confidence (adapter decides value). |
| `CodeAction.diagnostics` | Link to parent `diagnostic.id` | Preserve the association. |
| `CodeAction.command` | `action.commands[]` | See command safety below. |

Example `repairId` mapping table for a TypeScript adapter:

| `CodeAction.kind` | `repairId` |
| --- | --- |
| `quickfix` | `ancp.repair.quickfix` |
| `refactor.extract` | `ancp.repair.refactor.extract` |
| `source.organizeImports` | `ancp.repair.imports.organize` |
| `source.fixAll` | `ancp.repair.fixall` |

### Safety Defaults

All LSP-sourced repairs default to `safetyLevel: "review_required"` unless the adapter can prove they are narrowly local and behavior-preserving. The bar for `automatic` is the same as in the security model — the change must be local, deterministic, and precondition-checked.

### Command Evaluation

Commands inside LSP code actions (`CodeAction.command`) MUST be evaluated for effects before inclusion in the plan. If the command triggers network access, file writes outside the workspace, or dependency installation, the action's `safetyLevel` escalates to `dangerous`. If the adapter cannot determine the command's effects, it MUST set `safetyLevel: "review_required"` at minimum and include an `effects` entry with `kind: "unknown"`.

## Statefulness Warning

LSP servers are stateful. They maintain:

- open-file buffers (may differ from disk),
- project-wide symbol tables,
- incremental compilation caches,
- plugin/extension state.

This creates three problems for ANCP consumers:

1. Diagnostics sourced from LSP depend on the server's current view of the project. Stale buffers produce stale diagnostics.
2. Code actions generated from LSP are NOT reproducible from a cold start without restarting the server and reopening the same files.
3. Incremental compilation may mask errors that a clean build would surface.

Adapters using LSP as a source MUST include a server state marker:

```json
{
  "data": {
    "lspServerState": "warm"
  }
}
```

Valid values:

| Value | Meaning |
| --- | --- |
| `cold` | Server was started fresh for this request or state was explicitly reset. |
| `warm` | Server was already running with cached state. |

Consumers SHOULD treat warm-cache results with lower confidence when staleness is a concern. Verification commands SHOULD NOT rely on warm LSP state.

## Multi-Source Adapters

An adapter MAY combine CLI and LSP sources in a single `result.check` document.

Requirements:

- Each diagnostic SHOULD include `source` indicating which tool produced it.
- Diagnostic `id` values MUST be unique across sources within the document.
- The `toolchain` array MUST list all tools used.
- Deduplication rules from the section above apply before emission.

Example toolchain entry for a multi-source adapter:

```json
{
  "toolchain": [
    { "name": "gopls", "version": "0.17.1", "transport": "lsp" },
    { "name": "go", "version": "1.23.0", "transport": "cli" }
  ]
}
```

When sources disagree on severity for the same diagnostic, the adapter SHOULD prefer the stricter severity and note the discrepancy in `data`.
