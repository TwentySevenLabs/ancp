# Adapter Authoring Guide

This guide explains how to implement an ANCP adapter for a language or toolchain.

## Adapter Job

An adapter is responsible for turning native toolchain behavior into ANCP documents.

It should:

- discover the workspace,
- identify relevant languages and tools,
- run native checks,
- normalize diagnostics,
- preserve native identity,
- generate repair hints,
- generate repair plans when possible,
- verify repairs with native commands.

It should not:

- invent fake native codes,
- hide tool failures,
- parse prose when a structured API exists,
- mutate files in plan mode,
- label risky fixes as automatic,
- claim verification that did not run.

## Implementation Order

The clean production order:

1. Implement `manifest`.
2. Implement `capabilities`.
3. Implement `check`.
4. Add schema validation for emitted documents.
5. Add native-code-to-canonical-code mapping.
6. Add repair hints.
7. Add `explain`.
8. Add `repair --plan`.
9. Add `verify`.
10. Add `repair --apply` only after preconditions and transactional editing are solid.
11. Add optional `graph`, `effects`, `skills`, and `export`.

## Diagnostic Normalization

For each native diagnostic, map:

| Native concept | ANCP field |
| --- | --- |
| Native tool name | `toolchain[].name`, `diagnostic.source` |
| Native tool version | `toolchain[].version` |
| Native error code/rule ID | `diagnostic.nativeCode` |
| Normalized class | `diagnostic.canonicalCode` |
| Severity | `diagnostic.severity` |
| Diagnostic family | `diagnostic.kind` |
| Message | `diagnostic.message` |
| Primary span | `diagnostic.primaryLocation` |
| Notes/secondary spans | `diagnostic.relatedLocations` |
| Suggested edits | `diagnostic.repairHints` or `plan.repair.actions[].edits` |

## Canonical Code Mapping

Canonical codes should be stable and broad enough to work across languages.

Examples:

| Native diagnostic | Canonical code |
| --- | --- |
| TypeScript `TS2304` | `ancp.diag.symbol.unresolved` |
| Rust `E0425` | `ancp.diag.symbol.unresolved` |
| Python Pyright `reportMissingImports` | `ancp.diag.import.missing` |
| ESLint `no-unused-vars` | `ancp.diag.symbol.unused` or custom code |
| GCC missing header | `ancp.diag.import.missing` |
| Java cannot find symbol | `ancp.diag.symbol.unresolved` |
| C# `CS0246` | `ancp.diag.symbol.unresolved` or `ancp.diag.import.missing` depending context |
| Test assertion failure | `ancp.diag.test.assertion_failed` |

Adapters MAY define custom canonical codes, but they must namespace them outside `ancp.`.

## Location Strategy

Always preserve the native location.

Prefer this order:

1. URI.
2. Range.
3. Encoding unit.
4. Artifact digest.
5. Expected text.
6. Symbol selector.
7. AST-path selector.
8. Context selector.

Line/column alone is acceptable for core diagnostics, but repair plans should include stronger preconditions.

## Repair Hints Vs Repair Plans

Repair hints are small.

```json
{
  "repairId": "ancp.repair.symbol.import_missing",
  "title": "Import missing symbol",
  "confidence": 0.82,
  "safetyLevel": "review_required"
}
```

Repair plans are actionable.

```json
{
  "actionId": "action-001",
  "repairId": "ancp.repair.symbol.import_missing",
  "edits": [],
  "commands": [],
  "preconditions": [],
  "safetyLevel": "review_required"
}
```

Do not put edits inside diagnostic hints. Generate plans separately.

## Safety Defaults

Use `automatic` only when the change is narrowly local and behavior-preserving.

Use `review_required` for:

- imports,
- type annotations,
- dependency changes,
- call signature changes,
- generated-code updates,
- project config changes,
- batch formatters,
- linter fixes that may change behavior.

Use `dangerous` for:

- deletion,
- database writes,
- secret changes,
- dependency installation from network,
- migrations,
- VCS writes,
- external service calls,
- commands outside the workspace.

## Failed Native Tools

If the native tool crashes or cannot run, emit `result.check` with:

- `status: "tool_failed"`,
- `run.exitCode`,
- toolchain metadata if known,
- diagnostic if the failure can be represented,
- raw stderr summary under `data.stderrSummary`.

Do not emit invalid JSON just because the native tool failed.

## Testing An Adapter

Minimum adapter tests:

- manifest validates,
- capabilities validates,
- check result with zero diagnostics validates,
- check result with one diagnostic validates,
- tool failure validates,
- repair unavailable plan validates,
- repair available plan validates,
- verification pass validates,
- verification fail validates,
- every example is stable across runs.

