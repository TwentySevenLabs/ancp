# ANCP Conformance

ANCP conformance is profile-based.

An adapter must never claim more than it implements.

## Core Conformance

An adapter is ANCP 1.0 core conformant when:

1. `ancp manifest --json` emits a valid `manifest.adapter`.
2. `ancp capabilities --json` emits a valid `manifest.capabilities`.
3. `ancp check --json` emits a valid `result.check`.
4. Every emitted JSON document validates against `schemas/ancp-1.0.schema.json`.
5. Native tool identity is reported when available.
6. Native diagnostic codes are preserved when available.
7. Diagnostics include primary locations when source locations exist.
8. Tool failures still emit valid ANCP JSON when possible.
9. Unknown fields are placed under `extensions` or `data`.

## Explain Profile

Requires:

- `ancp explain <code> --json`
- valid `result.explain`
- support for canonical codes used by the adapter
- support for native codes where the adapter maps native codes

## Repair Plan Profile

Requires:

- `ancp repair --plan --json`
- valid `plan.repair`
- no mutation in plan mode
- safety levels on every action
- verification steps on every available plan
- required preconditions for source edits

## Repair Apply Profile

Requires:

- `ancp repair --apply <plan> --json`
- valid `result.apply`
- precondition checks before mutation
- refusal of failed preconditions with `status: "precondition_failed"` and no mutation
- refusal of dangerous actions without explicit approval
- accurate `status` reporting: `applied`, `partial`, `rolled_back`, `precondition_failed`, or `not_applied`
- `failedActionIds` populated when actions fail during mutation
- `rollback` object populated when partial failure occurs
- rollback strategy documented in `manifest.adapter`

## Verify Profile

Requires:

- `ancp verify --json`
- valid `result.verify`
- actual command execution or clearly documented manual verification
- diagnostic delta where before/after diagnostics are available
- diagnostic fingerprints SHOULD be included when the adapter emits `result.check` diagnostics used by verification, so that `diagnosticDelta` can reliably correlate diagnostics across runs

## Graph Profile

Requires:

- `ancp graph --json`
- valid `graph.code`
- stable node IDs within the graph document
- explicit partial-data marking when the graph is incomplete

## Effects Profile

Requires:

- operation effects in `manifest.capabilities` or equivalent effect output
- evidence labels: `static`, `dynamic`, `manifest`, `inferred`, `user-declared`, or `unknown`
- safety levels on effectful commands

## Skills Profile

Requires:

- `ancp skills --json`
- valid `result.skills`
- guidance tied to adapter/toolchain versions
- concise sections that agents can load selectively

## Export Profile

Requires:

- at least one export target
- valid output for the target format
- documented lossy fields when exporting to formats that cannot represent all ANCP data

## Repository-Level Conformance

This spec repository is considered internally consistent when:

1. all JSON files parse,
2. all examples validate against the main schema,
3. all taxonomy files have unique IDs,
4. all local Markdown links resolve,
5. the source corpus fetch report exists,
6. schema validation runs without warnings,
7. the final verification report records three independent passes.

