# Julia Toolchain Notes

## Sources

- `research/source-docs/snapshots/julia/command-line-interface.html`
- `research/source-docs/snapshots/julia/meta-parse.html`
- `research/source-docs/snapshots/julia/asts.html`
- `research/source-docs/snapshots/julia/languageserver-syntax.html`
- `research/source-docs/snapshots/julia/staticlint.html`

## ANCP-Relevant Facts

Julia does not behave like a classic ahead-of-time compiler ecosystem for day-to-day development. Useful diagnostics come from several layers:

- parser checks through Julia itself,
- AST/lowering/compiler frontend behavior,
- LanguageServer.jl for editor/LSP diagnostics,
- StaticLint.jl for project-aware static analysis,
- package tests through `Pkg.test` or project-specific test commands.

The lowest-friction reference adapter should run Julia with startup and history disabled, parse source files, and convert syntax failures into ANCP diagnostics. That is fast, has minimal side effects, and works without requiring an IDE server.

Richer semantic diagnostics should be an optional adapter extension that uses LanguageServer.jl/StaticLint.jl when installed in the user environment. That path is better for unresolved symbols and project-aware diagnostics, but it has more dependency and environment sensitivity than the parser gate.

## Adapter Requirements

A Julia ANCP adapter should:

- detect `.jl` files, `Project.toml`, and `Manifest.toml`,
- run syntax parsing with `--startup-file=no` and `--history-file=no`,
- preserve filename-aware parser locations where available,
- classify parse failures as `syntax`,
- represent LanguageServer.jl/StaticLint.jl diagnostics as optional richer sources,
- treat package resolution, precompilation, and tests as effectful verification steps,
- avoid claiming type-level certainty from parser-only checks.

## Core Commands

```bash
julia --startup-file=no --history-file=no path/to/file.jl
julia --startup-file=no --history-file=no -e 'Meta.parseall(read(ARGS[1], String); filename=ARGS[1])' path/to/file.jl
julia --project=. --startup-file=no --history-file=no -e 'using Pkg; Pkg.test()'
```

## ANCP Impact

Julia proves ANCP must handle dynamic compiler ecosystems cleanly. A conformant adapter may start with parser diagnostics and add LSP/static-lint signals without pretending that every language has the same compile pipeline as Rust, Go, or C++.
