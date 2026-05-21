# ADR 0005: Diagnostic Fingerprinting

Status: Accepted

## Context

ANCP diagnostic IDs such as `diag-ts-001` are document-scoped. They are not stable across invocations. When a repair changes line numbers, the next `check` run emits new IDs. The `result.verify` document uses `diagnosticDelta` with fields like `resolvedDiagnosticIds`, but there is no specification for how to correlate diagnostics across runs.

Without a stable identity model, verification cannot reliably determine which diagnostics were resolved and which are new.

## Decision

ANCP adds an optional `fingerprint` field to each diagnostic. The fingerprint is a stable string computed from position-independent properties: `canonicalCode`, `artifact.uri`, `nativeCode` (if available), and a content anchor such as `expectedText` or a `text` selector.

Line numbers MUST NOT be included in the fingerprint because they change after edits.

Adapters that support the `verify` profile SHOULD include fingerprints. Consumers correlating diagnostics across runs SHOULD match by fingerprint when IDs differ.

## Consequences

Benefits:

- `diagnosticDelta` in `result.verify` can reliably track resolved vs new diagnostics across runs,
- agents can track diagnostic persistence across repair iterations,
- fingerprints are optional so existing adapters are not broken.

Costs:

- adapters must compute a stable hash,
- fingerprint collisions are possible when multiple diagnostics share the same canonical code and artifact without distinguishing content anchors,
- the algorithm is not fully prescribed, so two adapters may fingerprint differently (by design — fingerprints are adapter-scoped).
