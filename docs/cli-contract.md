# ANCP CLI Contract

This document defines the recommended command-line interface for ANCP adapters.

An adapter may expose a different binary name, but `ancp` is the normative command shape used by this specification.

## General Rules

When `--json` is passed:

- stdout MUST contain exactly one ANCP JSON document unless the command explicitly documents newline-delimited output.
- human logs MUST go to stderr.
- process failures MUST still produce a valid ANCP JSON document when possible.
- command arguments SHOULD be deterministic.
- commands SHOULD support `--workspace <path>` where project root detection is ambiguous.

Adapters SHOULD support:

```bash
ancp --version
ancp manifest --json
ancp capabilities --json
ancp check --json
ancp explain <code-or-repair-id> --json
ancp repair --plan --json
ancp repair --apply <plan-file> --json
ancp verify --json
ancp graph --json
ancp skills --json
ancp render --from check-result.json --format text
ancp enable
ancp disable
ancp status
ancp export sarif --out ancp.sarif
```

Only these are required for core conformance:

```bash
ancp manifest --json
ancp capabilities --json
ancp check --json
```

## Exit Codes

Recommended adapter exit codes:

| Exit code | Meaning |
| --- | --- |
| `0` | Command completed and ANCP status is successful or non-failing. |
| `1` | Command completed and ANCP status is failed because diagnostics or verification failures exist. |
| `2` | Native tool failed before a reliable check result could be produced. |
| `3` | Adapter protocol error, invalid config, invalid arguments, or schema failure. |
| `4` | Unsafe operation refused. |
| `5` | Required capability/profile unavailable. |

The JSON document `status` remains authoritative. Exit codes are convenience signals for shells and CI.

When exit code `3` or `5` is used, the adapter MUST still emit a valid ANCP JSON document to stdout with `status: "protocol_error"`. The document MUST include `data.reason` with a human-readable explanation. For exit code `5`, the document SHOULD also include `data.missingProfile` naming the unsupported profile.

## `manifest`

Reports adapter identity, profiles, operations, and language support.

```bash
ancp manifest --json
```

Emits: `manifest.adapter`

Required profile: `core`

The command MUST NOT require a project workspace.

## `capabilities`

Reports capabilities for the current workspace.

```bash
ancp capabilities --json --workspace .
```

Emits: `manifest.capabilities`

Required profile: `core`

The adapter SHOULD detect:

- languages,
- manifests,
- lockfiles,
- build tools,
- test runners,
- formatters,
- linters,
- language servers,
- package managers,
- optional profiles available in this workspace.

## `check`

Runs native analysis and emits normalized diagnostics.

```bash
ancp check --json --workspace .
ancp check --json --language typescript --workspace .
ancp check --json --changed-only --base main
```

Emits: `result.check`

Required profile: `core`

The adapter SHOULD include:

- native command,
- native tool versions,
- workspace identity,
- diagnostics,
- native codes,
- canonical codes,
- primary locations,
- repair hints.

The adapter MUST NOT claim a diagnostic is fixed or verified during `check`.

## `explain`

Explains a diagnostic code, native code, or repair ID.

```bash
ancp explain ancp.diag.symbol.unresolved --json
ancp explain TS2304 --json
ancp explain ancp.repair.symbol.import_missing --json
```

Emits: `result.explain`

Required profile: `explain`

Explanations SHOULD be version-aware when the native tool behavior changes between versions.

## `repair --plan`

Produces repair plans without mutating files.

```bash
ancp repair --plan --json
ancp repair --plan --json --diagnostic diag-ts-001
ancp repair --plan --json --from check-result.json
```

Emits: `plan.repair`

Required profile: `repair-plan`

The adapter MUST NOT edit files in plan mode.

Plans MUST include:

- target diagnostics,
- actions,
- safety levels,
- preconditions when edits are proposed,
- verification steps.

If no repair is known, the adapter SHOULD emit `status: "unavailable"` with an empty `actions` array and explanation data.

## `repair --apply`

Applies a repair plan transactionally.

```bash
ancp repair --apply plan.json --json
```

Emits: `result.apply`

Required profile: `repair-apply`

The adapter MUST check required preconditions before applying.

The adapter SHOULD write backups or apply through VCS-aware transactional editing when possible.

The adapter MUST refuse `dangerous` actions unless the caller passes an explicit approval flag such as:

```bash
ancp repair --apply plan.json --allow-dangerous --json
```

## `verify`

Runs verification steps.

```bash
ancp verify --json
ancp verify --json --from plan.json
```

Emits: `result.verify`

Required profile: `verify`

Verification MUST report actual commands run. A successful status means the verification steps ran and passed.

## `graph`

Emits code graph facts.

```bash
ancp graph --json
ancp graph --json --kind imports
ancp graph --json --kind symbols
```

Emits: `graph.code`

Required profile: `graph`

Graph output MAY be partial. Partial graph output MUST say so in `data` or `extensions`.

## `skills`

Emits version-matched agent guidance.

```bash
ancp skills --json
ancp skills --json --section repair-loop
```

Emits: `result.skills`

Required profile: `skills`

Skills should be concise operational instructions, not full language manuals.

## `render`

Renders ANCP JSON into a user- or agent-facing text format.

```bash
ancp render --from check-result.json --format markdown
ancp render --from check-result.json --format text --budget 800
```

Markdown output is intended for human inspection. Text output is the compact
agent signal format: no Markdown fences, no tables, root-cause groups first,
raw-output fallback path included when available.

## `enable`, `disable`, `uninstall`, and `status`

Manages native-name shims for invisible compiler integration.

```bash
ancp enable
ancp enable --dry-run
ancp enable --scope session
ancp enable --profile full
ancp disable
ancp uninstall
ancp status
```

`enable` installs compiler/tool shims and configures `auto-compact` output by
default. On Windows, `--scope user` prepends the ANCP shim directory to the user
PATH. `--scope session` prints activation commands without mutating persistent
PATH.

Profiles:

- `agent`: default compiler/build/lint/test tool interception.
- `full`: includes shell tools such as `powershell`, `pwsh`, and `bash`.

`disable` removes ANCP from the user PATH without deleting shims. `uninstall`
disables ANCP and removes the shim directory. `status` reports installation,
PATH, and state metadata.

## `export`

Exports ANCP results to other formats.

```bash
ancp export sarif --from check-result.json --out ancp.sarif
ancp export cyclonedx --out bom.json
```

Required profile: `export`

Supported export formats SHOULD include SARIF when the adapter produces static-analysis-like diagnostics.

## Streaming Output

Some native tools stream events over time (e.g., `go test -json`, Cargo test runners). ANCP adapters MAY support streaming output.

### `--stream` Flag

Adapters that support streaming SHOULD accept a `--stream` flag on commands that may produce long-running output:

```bash
ancp check --json --stream
ancp verify --json --stream
```

When `--stream` is passed:

- stdout MUST use NDJSON (newline-delimited JSON) format: one valid JSON object per line, separated by `\n`.
- each line MUST be a valid ANCP JSON document or an `event.progress` object.
- the final line MUST be the complete result document (e.g., `result.check`, `result.verify`).
- human logs MUST still go to stderr.

When `--stream` is NOT passed, the adapter MUST buffer all output and emit a single JSON document as usual.

### `event.progress`

Progress events are lightweight heartbeats emitted during long-running operations.

Progress events are NOT full ANCP documents. They do not require `producer`, `createdAt`, or document-specific required fields.

A progress event MUST include:

- `documentKind`: `"event.progress"`
- `message`: human-readable status message

A progress event SHOULD include:

- `ancpVersion`: protocol version
- `elapsedMs`: milliseconds since the operation started
- `phase`: current operation phase (e.g., `"compiling"`, `"testing"`, `"analyzing"`)
- `progress`: optional object with `current` and `total` for countable work

Example NDJSON stream:

```
{"documentKind":"event.progress","ancpVersion":"1.0.0","message":"Compiling 142 modules...","elapsedMs":0,"phase":"compiling"}
{"documentKind":"event.progress","ancpVersion":"1.0.0","message":"Running tests...","elapsedMs":2340,"phase":"testing","progress":{"current":0,"total":47}}
{"documentKind":"event.progress","ancpVersion":"1.0.0","message":"Running tests...","elapsedMs":4100,"phase":"testing","progress":{"current":23,"total":47}}
{"ancpVersion":"1.0.0","documentKind":"result.check","producer":{"name":"ancp-go-adapter","version":"1.0.0"},"createdAt":"2026-05-21T00:00:00Z","status":"failed",...}
```

### Adapters Without Streaming Support

Adapters that do not support streaming MUST ignore the `--stream` flag silently and emit a single JSON document. Adapters MUST NOT emit malformed NDJSON when `--stream` is passed but not supported.
