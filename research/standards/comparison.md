# Standards Comparison

ANCP is deliberately built beside existing standards, not against them.

## JSON Schema

ANCP uses JSON Schema Draft 2020-12 for validating protocol documents.

ANCP does not use JSON Schema to define semantics that cannot be expressed structurally. The normative Markdown spec remains authoritative when schema validation is insufficient.

## LSP

LSP standardizes editor-to-language-server communication.

ANCP borrows:

- diagnostics,
- severity normalization,
- ranges,
- code actions,
- commands,
- language IDs.

ANCP adds:

- CLI-first documents,
- repair plans,
- adapter profiles,
- preconditions,
- verification results,
- effect metadata,
- reusable agent guidance.

Adapters may consume LSP responses and emit ANCP documents.

## SARIF

SARIF standardizes static-analysis result interchange.

ANCP borrows:

- result/rule separation,
- artifact locations,
- related locations,
- logical locations,
- code flows,
- tool metadata.

ANCP adds:

- compiler/test/build diagnostics,
- repair hints and plans,
- apply/verify lifecycle,
- command effects,
- agent-facing skills.

ANCP diagnostics should be exportable to SARIF where they behave like static-analysis results.

## JSON Patch

JSON Patch is useful for editing JSON documents.

ANCP uses JSON Patch only for JSON-like targets. Source-code edits require richer source ranges, expected text, and relocation anchors, so ANCP defines a source edit model.

## JSON Canonicalization

ANCP recommends JCS for deterministic hashes and signatures.

Protocol documents should be canonicalized before signing if a trust chain is required.

## SPDX And CycloneDX

SPDX and CycloneDX are better standards for software identity and dependency/bill-of-materials metadata than anything ANCP should invent.

ANCP should reference SPDX license IDs and CycloneDX component IDs rather than copying their full models.

