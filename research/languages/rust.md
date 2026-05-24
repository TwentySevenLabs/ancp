# Rust Toolchain Notes

## Sources

- `research/source-docs/snapshots/rust/rustc-json.html`
- `research/source-docs/snapshots/rust/cargo-check.html`
- `research/source-docs/snapshots/rust/cargo-fix.html`
- `research/source-docs/snapshots/rust/rustc-diagnostics-guide.html`

## ANCP-Relevant Facts

Rust is one of the best fits for ANCP because `rustc` and Cargo already expose structured diagnostic data.

`rustc --error-format=json` emits newline-delimited JSON diagnostic messages. Diagnostics include code, level, message, spans, children, suggestions, and rendered text.

Cargo supports JSON message output and can wrap compiler diagnostics.

`cargo fix` applies compiler suggestions where appropriate.

## Adapter Requirements

A Rust adapter should:

- use `cargo check --message-format=json`,
- preserve `rustc` codes and lint names,
- map `spans` to ANCP primary and related locations,
- map children of level `help` to repair hints when they include suggestions,
- preserve suggestion applicability,
- model `cargo fix` as a batch repair command with review requirements,
- keep `cargo check` and `cargo test` as verification steps.

## Core Commands

```bash
cargo check --message-format=json
cargo test --message-format=json
cargo fix --allow-dirty --allow-staged
rustc --error-format=json file.rs
```

## ANCP Impact

Rust validates ANCP's diagnostic child, suggestion, applicability, and fix-plan model.

