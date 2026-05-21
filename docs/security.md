# ANCP Security Model

ANCP is designed for coding agents. That means safety must be part of the protocol, not a UI afterthought.

## Threat Model

ANCP assumes:

- project repositories may contain untrusted build scripts,
- tests may execute arbitrary code,
- package managers may access the network,
- compiler plugins and analyzers may execute code,
- generated repair plans may be stale,
- line numbers may move,
- agents may over-trust structured output if safety metadata is weak.

## Required Safety Fields

Every repair action must include:

- `safetyLevel`
- `confidence`

Every command in a repair action must include:

- `argv`
- `workingDirectory`
- `effects`

Every effect must include:

- `kind`
- `safetyLevel`
- preferably `scope`, `reason`, and `evidence`

## Safety Levels

| Level | Meaning | Example |
| --- | --- | --- |
| `automatic` | Narrow, local, behavior-preserving, precondition-checked. | Insert missing semicolon, run formatter in check mode. |
| `review_required` | Plausibly correct but may affect behavior or project state. | Add import, change type annotation, run `ruff --fix`. |
| `dangerous` | Can affect external state, secrets, data, VCS, dependencies, or broad behavior. | Install dependency, run migration, delete file, push branch. |
| `unsupported` | Adapter cannot safely perform or plan the repair. | Ambiguous architecture decision. |

## Commands Are Not Automatically Safe

The following commands must be treated as effectful:

- `npm install`, `pnpm install`, `yarn install`
- `pip install`, `uv sync`, `poetry install`
- `cargo build`, `cargo test`, `cargo fix`
- `go test`
- `dotnet build`, `dotnet test`, `dotnet format`
- `gradle build`, `mvn test`, `sbt test`
- `swift build`, `swift test`
- `zig build`
- arbitrary package scripts

Many of these are normal verification commands. They still need explicit effects because they can execute project code.

## Preconditions

Repair plans should include preconditions. Examples:

- file digest still matches,
- expected text still exists,
- symbol still unresolved,
- dependency still missing,
- profile still supported,
- command still succeeds in dry-run mode.

Consumers must refuse automatic apply if required preconditions fail.

## Workspace Boundaries

Adapters and consumers should distinguish:

- workspace reads,
- workspace writes,
- writes outside workspace,
- VCS writes,
- network access,
- credential access.

Any write outside the workspace is `dangerous`.

## Secrets

ANCP documents must not include secret values.

If a diagnostic references a secret:

- include the location,
- include a redacted fingerprint if useful,
- do not include the raw secret,
- mark repair as `dangerous` if it modifies credential stores or rotates secrets.

## Generated Code

Generated code should be marked through `artifact.role: "generated"` when known.

Adapters should prefer changing the generator source rather than generated output. If only generated output is changed, the plan should explain why.

## Dependency Installation

Dependency installation is always at least `review_required` and usually `dangerous` if it accesses the network.

Dependency manifest edits without installation are `review_required`.

## Verification Claims

Consumers and adapters must not say a repair is verified unless verification steps actually ran and passed.

Valid labels:

- implemented,
- planned,
- applied,
- syntax-checked,
- smoke-tested,
- verified.

Only the last one implies successful verification execution.

