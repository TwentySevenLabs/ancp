# Agent Native Compiler Protocol 1.0

Status: Stable implementation contract

This document is the normative specification for Agent Native Compiler Protocol 1.0, abbreviated ANCP 1.0.

The key words `MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, `RECOMMENDED`, `MAY`, and `OPTIONAL` are to be interpreted as described in RFC 2119 style requirements.

## 1. Scope

ANCP defines a language-neutral protocol for exposing compiler, linter, formatter, static-analysis, test, build, package, language-server, and project-indexing facts to coding agents.

ANCP standardizes:

- JSON document kinds,
- diagnostic identity,
- diagnostic location and anchoring,
- repair hints,
- repair plans,
- edit preconditions,
- verification results,
- adapter capability discovery,
- project effect and capability metadata,
- code graph facts,
- agent guidance documents,
- conformance profiles.

ANCP does not define:

- a new programming language,
- a replacement for existing compilers,
- a replacement for LSP,
- a replacement for SARIF,
- a package registry,
- a universal AST,
- a universal type system,
- an agent runtime.

ANCP adapters MAY consume native compiler APIs, CLI output, LSP responses, AST libraries, static analyzers, test runners, package managers, or build systems. The adapter is responsible for converting native facts into ANCP documents.

## 2. Compatibility Target

ANCP 1.0 is designed for these language families:

- statically typed compiled languages such as Rust, Go, C, C++, Zig, Swift, Kotlin, Java, C#,
- gradually typed languages such as TypeScript and Python with type checkers,
- dynamic/compiler-JIT ecosystems such as JavaScript, Ruby, PHP, Julia, Lua, and Python without type checking,
- configuration and data languages such as JSON, YAML, TOML, Nix, Terraform, Dockerfile, SQL, and GraphQL,
- mixed repositories containing multiple languages and toolchains.

The protocol MUST NOT require features that only one language family can provide. Features that depend on language-specific depth MUST be declared through optional profiles.

## 3. Wire Format

ANCP documents MUST be JSON objects encoded as UTF-8.

ANCP schemas are written in JSON Schema Draft 2020-12.

ANCP producers MUST emit valid JSON without comments or trailing commas.

ANCP consumers MUST ignore unknown fields under `extensions`.

ANCP producers MUST NOT add arbitrary top-level fields outside the schema unless the schema explicitly allows them. Extension fields belong under `extensions` and SHOULD use reverse-DNS or URL-like namespacing.

Example:

```json
{
  "extensions": {
    "com.example.my-adapter": {
      "nativeTraceId": "abc123"
    }
  }
}
```

## 4. Document Model

Every ANCP document MUST include:

- `ancpVersion`: semantic protocol version string.
- `documentKind`: one of the registered ANCP document kinds.
- `producer`: object identifying the adapter or tool that produced the document.
- `createdAt`: RFC 3339 timestamp.

Registered ANCP 1.0 document kinds:

| Kind | Required profile | Meaning |
| --- | --- | --- |
| `manifest.adapter` | `core` | Adapter identity and supported features. |
| `manifest.capabilities` | `core` | Project and adapter capability discovery. |
| `result.check` | `core` | Compiler/linter/test/build diagnostics. |
| `result.explain` | `explain` | Structured explanation for a diagnostic, repair, or native code. |
| `plan.repair` | `repair-plan` | Proposed repair actions with preconditions and verification. |
| `result.apply` | `repair-apply` | Result of applying a repair plan. |
| `result.verify` | `verify` | Post-repair validation result. |
| `graph.code` | `graph` | Code graph facts. |
| `result.skills` | `skills` | Version-matched agent guidance. |
| `event.progress` | (streaming only) | Progress heartbeat during long-running operations. |

`event.progress` is a lightweight document used only in streaming mode (see [docs/cli-contract.md](../docs/cli-contract.md)). It does not require `producer` or `createdAt` and is NOT validated against the full ANCP schema. It MUST include `documentKind` and `message`.

## 5. Versioning

ANCP uses semantic versioning.

For ANCP 1.0:

- Producers MUST set `ancpVersion` to a `1.0.x` compatible value.
- Consumers that support `1.0.0` MUST accept any `1.0.x` document that validates against the declared schema.
- Patch releases MUST NOT remove required fields, change field meaning, or narrow allowed values in a breaking way.
- Minor releases MAY add document kinds, optional fields, optional profiles, and taxonomy entries.
- Major releases MAY introduce breaking changes.

Adapters MUST report their own implementation version separately in `producer.version`.

## 6. Profiles

ANCP uses conformance profiles.

The `core` profile is REQUIRED for every ANCP adapter.

| Profile | Requirement | Operations |
| --- | --- | --- |
| `core` | Required | `manifest`, `capabilities`, `check` |
| `explain` | Recommended | `explain` |
| `repair-plan` | Recommended | `repair --plan` |
| `repair-apply` | Optional | `repair --apply` |
| `verify` | Recommended | `verify` |
| `graph` | Optional | `graph` |
| `effects` | Optional | `effects` or `capabilities` with effect data |
| `skills` | Optional | `skills` |
| `export` | Optional | `export` |

An adapter MUST NOT claim a profile unless it implements every required operation and field for that profile.

An adapter MAY expose partial support as named capabilities inside `manifest.capabilities`, but partial support does not grant conformance to the profile.

## 7. Producer Identity

`producer` identifies the adapter, not necessarily the underlying native compiler.

`producer` MUST include:

- `name`
- `version`

`producer` SHOULD include:

- `homepage`
- `sourceUri`
- `license`

The native compiler, linter, formatter, test runner, build tool, or language server MUST be reported under `toolchain`.

## 8. Workspace Identity

ANCP workspace objects identify the project under analysis.

A workspace MUST include:

- `rootUri`

A workspace SHOULD include:

- `workspaceId`
- `vcs`
- `revision`
- `packageManager`

`workspaceId` SHOULD be stable for the repository and SHOULD NOT include secrets, local usernames, or machine-specific paths.

## 9. Toolchain Identity

Each native tool used by the adapter SHOULD be represented as a `toolchain` entry.

A toolchain entry SHOULD include:

- `name`
- `version`
- `role`
- `command`

Allowed roles include:

- `compiler`
- `typechecker`
- `linter`
- `formatter`
- `test`
- `build`
- `package-manager`
- `language-server`
- `indexer`
- `security-scanner`
- `custom`

Adapters MUST preserve native tool versions when they are available. Agents need this to decide whether diagnostic and repair behavior is reproducible.

## 10. Diagnostic Identity

Each diagnostic MUST include:

- `id`: stable identifier for this diagnostic instance within the ANCP document.
- `canonicalCode`: ANCP-normalized diagnostic code.
- `severity`: normalized severity.
- `kind`: broad diagnostic kind.
- `message`: human-readable message.
- `primaryLocation`: main location.
- `repairHints`: array, possibly empty.

Each diagnostic SHOULD include:

- `nativeCode`: native tool code, such as `TS2304`, `E0425`, `F821`, or `CS0103`.
- `nativeMessage`: original native message if different from `message`.
- `source`: native tool source.
- `relatedLocations`.
- `symbols`.
- `fingerprint`.
- `data`.

### 10a. Diagnostic Fingerprinting

The `id` field is scoped to a single ANCP document. It is NOT stable across invocations. When a repair changes line numbers, the next `check` run emits new IDs.

The `fingerprint` field provides a stable identity for correlating the same diagnostic across runs.

`fingerprint` MUST be a string computed from position-independent properties. Adapters SHOULD compute it from:

- `canonicalCode`
- `primaryLocation.artifact.uri`
- `nativeCode` when available
- a content anchor: one of `expectedText`, a `text` selector, or a `symbol` selector from `primaryLocation.selectors`

`fingerprint` MUST NOT include line numbers, column numbers, or byte offsets, because these change after edits.

`fingerprint` SHOULD be deterministic: the same diagnostic in the same source location with the same content SHOULD produce the same fingerprint across adapter invocations.

Adapters MAY use any hash algorithm. The fingerprint is opaque to consumers. Two fingerprints from different adapters are not comparable.

Adapters that support the `verify` profile SHOULD include fingerprints in `result.check` diagnostics.

`canonicalCode` MUST use a stable namespaced string. Core ANCP codes use the prefix `ancp.diag.`.

Examples:

- `ancp.diag.syntax.invalid`
- `ancp.diag.symbol.unresolved`
- `ancp.diag.type.mismatch`
- `ancp.diag.import.missing`
- `ancp.diag.effect.undeclared`
- `ancp.diag.test.assertion_failed`

Adapters MAY emit custom canonical codes, but custom codes MUST be namespaced and MUST NOT use the `ancp.` prefix.

Example:

- `org.rust-lang.rustc.borrow.moved_value`
- `com.typescript.TS2304`

## 11. Severity

Normalized severity MUST be one of:

- `fatal`
- `error`
- `warning`
- `info`
- `hint`

Adapters MUST NOT invent top-level severity values. Native severities MAY be preserved in `data.nativeSeverity`.

## 12. Diagnostic Kinds

`kind` MUST be one of the core diagnostic kinds or a namespaced extension.

Core diagnostic kinds:

- `syntax`
- `symbol`
- `type`
- `module`
- `import`
- `dependency`
- `effect`
- `permission`
- `memory`
- `concurrency`
- `lifetime`
- `ownership`
- `trait`
- `interface`
- `contract`
- `lint`
- `format`
- `test`
- `build`
- `runtime`
- `security`
- `performance`
- `configuration`
- `documentation`
- `unknown`

The diagnostic taxonomy file gives canonical meanings and examples.

## 13. Location Model

ANCP locations MUST support both human readability and machine relocation.

A location MUST include:

- `artifact`
- `range`

An artifact MUST include:

- `uri`

An artifact SHOULD include:

- `languageId`
- `digest`
- `role`

A range MUST include:

- `unit`
- `start`
- `end`

`unit` MUST be one of:

- `utf8`
- `utf16`
- `unicode-codepoint`
- `byte`

Adapters SHOULD use the native unit when preserving native tool output. If the adapter also provides LSP-compatible positions, it SHOULD use `utf16`.

Locations SHOULD include `selectors` when possible. Selectors are relocation anchors beyond line and column:

- `symbol`
- `ast-path`
- `context`
- `text`
- `digest`
- `json-pointer`
- `xpath`
- `css-selector`
- `sql-object`

Agents SHOULD use selectors and preconditions before applying edits. Agents SHOULD NOT rely only on line and column when a plan includes stronger anchors.

## 14. Repair Hints

A repair hint is a compact intent attached to a diagnostic. It is not a patch.

A repair hint MUST include:

- `repairId`
- `title`
- `confidence`
- `safetyLevel`

`repairId` MUST be stable and namespaced. Core repair IDs use the prefix `ancp.repair.`.

Examples:

- `ancp.repair.symbol.import_missing`
- `ancp.repair.symbol.declare_missing`
- `ancp.repair.type.adjust_annotation`
- `ancp.repair.call.add_argument`
- `ancp.repair.config.install_dependency`
- `ancp.repair.test.update_expectation`

`confidence` MUST be a number from `0` to `1`.

`safetyLevel` MUST be one of:

- `automatic`
- `review_required`
- `dangerous`
- `unsupported`

Adapters MUST use `review_required` or stricter when the repair may change runtime behavior.

Adapters MUST use `dangerous` for repairs that may delete data, modify external services, alter credentials, run migrations, or perform network side effects.

## 15. Repair Plans

A repair plan is a structured proposal for resolving diagnostics.

A repair plan MUST include:

- `planId`
- `status`
- `targetDiagnostics`
- `actions`
- `verification`

Plan status MUST be one of:

- `available`
- `partial`
- `unavailable`
- `ambiguous`
- `unsafe`

Each repair action MUST include:

- `actionId`
- `repairId`
- `title`
- `intent`
- `confidence`
- `safetyLevel`

Each repair action MAY include:

- `edits`
- `commands`
- `preconditions`
- `requiresCapabilities`
- `explanation`

Repair plans SHOULD be minimal. A plan SHOULD NOT include unrelated refactors.

Repair plans MUST declare verification steps. A plan with no verification step MUST set `status` to `partial` unless the adapter can prove verification is impossible for the project.

## 16. Edit Model

ANCP supports these edit kinds:

- `text.insert`
- `text.replace`
- `text.delete`
- `file.create`
- `file.delete`
- `file.move`
- `json.patch`

Text edits MUST include:

- `target`
- `newText` for insert or replace

Text edits SHOULD include:

- `expectedText`
- `preconditions`

File edits MUST include:

- target file artifact
- operation-specific fields

JSON patch edits MUST follow RFC 6902 where applicable.

Adapters SHOULD prefer the smallest correct edit. Agents SHOULD apply edits transactionally.

### 16a. Apply Transactionality

When an adapter applies a repair plan through `repair --apply`, the following rules govern transactionality and failure handling.

**Pre-mutation precondition check:**

Before any file is modified, the adapter MUST evaluate all `required: true` preconditions for all actions in the plan. If any required precondition fails, the adapter MUST refuse the entire plan without performing any mutation. The `result.apply` document MUST set `status` to `precondition_failed`.

**Mutation phase:**

If all required preconditions pass, the adapter enters the mutation phase. Edits and commands are applied in action order. Within an action, edits are applied before commands.

If the mutation phase completes successfully, `status` MUST be `applied`.

**Partial failure during mutation:**

If a later action fails after earlier actions have already mutated files, the workspace is in a partially modified state. The adapter SHOULD attempt rollback.

- If rollback succeeds, `status` MUST be `rolled_back`.
- If rollback fails or was not attempted, `status` MUST be `partial`.
- `status` MUST NOT be `applied` when any action failed.

**Rollback strategies:**

Adapters MAY use any of these strategies:

| Strategy | Description |
| --- | --- |
| `vcs` | Reset to the VCS state before mutation (e.g., `git checkout`). Requires a clean VCS state before apply. |
| `backup` | Copy original files to a temporary location before mutation and restore on failure. |
| `in-memory` | Hold original file contents in memory and write them back on failure. |
| `none` | No rollback attempted. |

Adapters that support the `repair-apply` profile MUST document their rollback strategy in `manifest.adapter`.

**Result.apply document:**

The `result.apply` document MUST include:

- `status`: one of `applied`, `partial`, `rolled_back`, `precondition_failed`, `not_applied`.
- `apply.appliedActionIds`: actions that were successfully applied.
- `apply.changedArtifacts`: files that were modified.

The `result.apply` document SHOULD include:

- `apply.rejectedActionIds`: actions that were not applied.
- `apply.failedActionIds`: actions whose application was attempted and failed.
- `apply.rollback`: rollback result object.
- `apply.summary`: human-readable summary.

The `rollback` object SHOULD include:

- `attempted`: boolean indicating whether rollback was attempted.
- `succeeded`: boolean indicating whether rollback restored the workspace.
- `strategy`: rollback strategy used.
- `notes`: additional detail.

## 17. Preconditions

Preconditions protect repair plans from stale context.

Supported precondition kinds:

- `artifact.digest`
- `text.equals`
- `text.contains`
- `symbol.exists`
- `symbol.missing`
- `command.succeeds`
- `dependency.present`
- `dependency.missing`
- `profile.supported`

Consumers MUST check preconditions before applying a plan. If any required precondition fails, the plan MUST NOT be applied automatically.

## 18. Commands

Repair actions MAY include commands.

A command MUST include:

- `argv`
- `workingDirectory`
- `effect`

Commands MUST NOT be represented as shell strings unless the native tool strictly requires shell evaluation. Prefer argument arrays.

Commands that perform filesystem writes, network access, process spawning beyond the direct command, dependency installation, migrations, or credential access MUST declare those effects.

Consumers SHOULD require human review for commands with `dangerous` safety level.

## 19. Verification

Verification steps close the repair loop.

A verification step SHOULD include:

- `name`
- `argv`
- `expectedStatus`
- `produces`

Verification result documents MUST report:

- `status`
- `diagnosticDelta`
- `steps`

`diagnosticDelta` SHOULD include:

- `beforeCount`
- `afterCount`
- `resolvedDiagnosticIds`
- `newDiagnosticIds`
- `unchangedDiagnosticIds`
- `resolvedFingerprints`
- `newFingerprints`
- `unchangedFingerprints`

When diagnostic IDs are not stable across runs (the common case), consumers SHOULD use fingerprints to correlate diagnostics between the before and after check results. The `*Ids` fields refer to document-scoped IDs within the same adapter session. The `*Fingerprints` fields allow correlation across independent invocations.

Consumers MUST prefer fingerprint-based matching over ID-based matching when both are available and the before and after results come from separate invocations.

An agent MUST NOT claim a repair is verified unless verification ran and passed.

## 20. Effect and Capability Model

ANCP effects describe what tools and proposed actions can touch.

Core effect kinds:

- `filesystem.read`
- `filesystem.write`
- `process.spawn`
- `network.access`
- `environment.read`
- `environment.write`
- `dependency.install`
- `database.read`
- `database.write`
- `service.call`
- `credential.read`
- `secret.write`
- `container.run`
- `vcs.read`
- `vcs.write`

Effects SHOULD include:

- `scope`
- `reason`
- `safetyLevel`

The `effects` profile does not require every language to statically prove effects. It requires the adapter to report known effects honestly and distinguish static proof from inference.

`evidence` MUST be one of:

- `static`
- `dynamic`
- `manifest`
- `inferred`
- `user-declared`
- `unknown`

## 21. Code Graph

The `graph` profile exposes structured facts about code.

Graph documents MAY include:

- files,
- modules,
- packages,
- symbols,
- imports,
- exports,
- calls,
- references,
- type relationships,
- ownership relationships,
- dependency relationships,
- test relationships.

ANCP does not require a universal AST. A graph node MUST identify its kind and MAY carry language-specific data under `data` or `extensions`.

## 22. Agent Skills

The `skills` profile provides version-matched guidance for agents.

A skills result SHOULD include:

- adapter workflows,
- language-specific edit rules,
- diagnostic handling guidance,
- validation commands,
- project conventions,
- unsafe operation rules.

Skills MUST identify the adapter and toolchain version they match.

Skills SHOULD be short enough for an agent to load selectively. Long manuals SHOULD be split into named sections.

## 23. CLI Contract

ANCP adapters SHOULD expose a CLI. The normative CLI is described in [docs/cli-contract.md](../docs/cli-contract.md).

Required core commands:

- `ancp manifest --json`
- `ancp capabilities --json`
- `ancp check --json`

Recommended commands:

- `ancp explain <code> --json`
- `ancp repair --plan --json`
- `ancp verify --json`

CLI commands MUST write ANCP JSON documents to stdout when `--json` is provided.

Human-readable logs MUST go to stderr.

## 24. SARIF, LSP, SPDX, CycloneDX, and JSON Patch Interop

ANCP adapters MAY import diagnostics from LSP and MAY export diagnostics to SARIF.

Adapters that consume LSP diagnostics or code actions MUST follow the rules in [docs/lsp-interop.md](../docs/lsp-interop.md), including deduplication, code-action-to-repair-plan mapping, and statefulness reporting.

ANCP MUST preserve enough location, severity, rule, and result metadata to support SARIF export for static-analysis-like diagnostics.

ANCP MAY reference SPDX license identifiers and CycloneDX component identifiers for dependencies and artifacts.

ANCP MAY use RFC 6902 JSON Patch for JSON document repair actions. Source-code text edits SHOULD use the ANCP text edit model instead of JSON Patch unless the target file is JSON.

ANCP MAY use RFC 8785 JSON Canonicalization Scheme for deterministic hashing and signing of protocol documents.

## 25. Security Requirements

Adapters MUST NOT hide side effects in repair plans.

Adapters MUST NOT label a plan `automatic` if it:

- deletes files,
- changes secrets,
- writes outside the workspace,
- installs dependencies,
- calls external services,
- modifies a database,
- performs VCS writes,
- runs migrations,
- disables tests,
- suppresses diagnostics without explanation.

Consumers SHOULD execute repair commands in a workspace jail or sandbox when possible.

Consumers SHOULD show plan summaries before applying any `review_required` or `dangerous` action.

## 26. Error Handling

If a native tool fails before producing diagnostics, the adapter MUST emit a valid ANCP document with status `tool_failed` or `protocol_error`.

Adapters SHOULD include:

- exit code,
- stderr summary,
- command,
- tool version if known,
- failure classification.

Adapters MUST NOT emit invalid JSON as the only result of a failed command when `--json` is requested.

### 26a. Protocol Error Documents

When a command fails due to adapter-level errors (not native tool errors), the adapter MUST emit a valid ANCP document with `status: "protocol_error"` and `data.reason` explaining the error.

Protocol errors include:

- a command that requires a profile the adapter does not support,
- invalid command arguments,
- invalid configuration,
- schema validation failures in input documents,
- missing workspace when one is required.

**Unsupported profile requests:**

When a consumer calls a command for a profile the adapter does not support (e.g., calling `ancp repair --plan` when the adapter only supports `core`), the adapter MUST:

1. Emit a valid ANCP document. The `documentKind` SHOULD be the document kind the command would have produced (e.g., `plan.repair`). If the adapter cannot construct a valid document of that kind, it MAY emit `result.check` with `status: "protocol_error"`.
2. Set `status` to `"protocol_error"`.
3. Include `data.reason` with a human-readable explanation.
4. Include `data.missingProfile` with the name of the unsupported profile.
5. Exit with code `5`.

Example structure:

```json
{
  "ancpVersion": "1.0.0",
  "documentKind": "result.check",
  "status": "protocol_error",
  "data": {
    "reason": "The repair-plan profile is not supported by this adapter.",
    "missingProfile": "repair-plan"
  }
}
```

## 27. Conformance

An implementation is ANCP 1.0 conformant if:

1. It emits valid ANCP 1.0 JSON documents.
2. It implements every required operation for the claimed profiles.
3. It validates against the ANCP 1.0 schema for its emitted document kinds.
4. It reports native tool identity and versions where available.
5. It preserves native diagnostic codes where available.
6. It uses stable canonical codes and repair IDs.
7. It declares repair safety levels and effects honestly.
8. It does not claim verification without executing verification steps.

Detailed conformance tests are in [docs/conformance.md](../docs/conformance.md).

## 28. Non-Goals

ANCP intentionally avoids:

- mandating one parser or AST library,
- forcing all languages into one type model,
- pretending all diagnostics are auto-fixable,
- treating generated code the same as user-authored code,
- requiring network services,
- requiring a specific agent framework,
- requiring a specific package manager,
- requiring a central registry.

## 29. Stability Policy

ANCP 1.0 document meanings are stable. New optional fields may be added in patch releases only if old consumers can ignore them safely.

Breaking changes require ANCP 2.0.
