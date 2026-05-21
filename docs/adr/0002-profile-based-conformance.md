# ADR 0002: Profile-Based Conformance

Status: Accepted

## Context

Different languages expose different tooling depth. Rust has structured compiler JSON and suggestions. Go has JSON test streams and package metadata. Java has Compiler API diagnostics. Python and JavaScript rely on analyzer/linter composition. Ruby and PHP core syntax checkers are much thinner.

One required feature set for all languages would either be too weak or dishonest.

## Decision

ANCP uses profiles:

- `core`
- `explain`
- `repair-plan`
- `repair-apply`
- `verify`
- `graph`
- `effects`
- `skills`
- `export`

Only `core` is required.

## Consequences

Adapters can be useful early without pretending to support graph/effects/auto-apply.

Consumers can negotiate capabilities instead of guessing.

