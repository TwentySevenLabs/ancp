# ADR 0003: Repair Plans Before Apply

Status: Accepted

## Context

Compiler and linter fixes vary widely:

- Rust suggestions may be precise but can have different applicability levels.
- ESLint fixes can be safe or semantic.
- `dotnet format` may restore, compile, and run analyzers.
- `cargo fix` runs project build logic.
- package-manager fixes can access the network.

Agents need a stable repair contract before mutation.

## Decision

ANCP separates repair hints, repair plans, apply results, and verification results.

`repair --plan` MUST NOT mutate files.

`repair --apply` is optional and must check preconditions.

## Consequences

Agents can inspect and reason about plans before executing them.

Adapters can ship useful repair support without building a safe mutation engine on day one.

