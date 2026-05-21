# ADR 0004: Effects And Safety In Core Documents

Status: Accepted

## Context

Build, test, format, and repair commands can execute arbitrary project code or touch external state.

Examples:

- `go test` executes tests.
- `dotnet format` may restore, compile, and run analyzers.
- `cargo fix` can run build scripts.
- `zig build` executes `build.zig`.
- package managers can download and execute install scripts.

## Decision

ANCP requires safety levels on repair actions and effect declarations on commands.

The effects profile adds richer capability reporting, but repair command effects are part of the repair contract.

## Consequences

Consumers can make policy decisions without parsing shell commands.

Adapters must be honest when safety cannot be proven.

