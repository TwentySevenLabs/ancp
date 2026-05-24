# Swift And Zig Toolchain Notes

## Sources

- `research/source-docs/snapshots/swift/swift-compiler.html`
- `research/source-docs/snapshots/swift/sourcekit-lsp-readme.md`
- `research/source-docs/snapshots/swift/diagnostic-descriptions-index.html`
- `research/source-docs/snapshots/zig/language-reference.html`
- `research/source-docs/snapshots/zig/build-system.html`

## Swift

Swift has compiler and SwiftPM surfaces plus SourceKit-LSP. SourceKit-LSP implements LSP for Swift and C-family languages and supports projects using Swift Package Manager or `compile_commands.json`.

The Swift compiler front-end supports IDE integration and emits warnings/errors through compiler phases.

## Zig

Zig exposes direct commands such as `zig build-exe`, `zig build-lib`, `zig build-obj`, and `zig test`, plus a code-based build system in `build.zig`.

The Zig build system is a graph of steps and can generate files, run project tools, produce assets, mutate source files in place, and orchestrate tests.

## Adapter Requirements

A Swift adapter should:

- detect SwiftPM,
- use SourceKit-LSP for diagnostics/actions where possible,
- use `swift build` and `swift test` for verification,
- preserve module/package/test information.

A Zig adapter should:

- detect `build.zig` and `build.zig.zon`,
- treat build scripts as executable code,
- model generated-file steps,
- verify with `zig build` and `zig build test`,
- avoid assuming structured JSON diagnostics unless the installed Zig version provides it.

## ANCP Impact

Swift validates the LSP adapter path. Zig validates the safety model for build scripts as code.

