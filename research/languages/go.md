# Go Toolchain Notes

## Sources

- `research/source-docs/snapshots/go/go-command.html`
- `research/source-docs/snapshots/go/go-compile.html`
- `research/source-docs/snapshots/go/test2json.html`
- `research/source-docs/snapshots/go/gopls-diagnostics.html`

## ANCP-Relevant Facts

Go has an unusually cohesive toolchain:

- `go build` compiles packages,
- `go test` runs tests,
- `go test -json` emits machine-readable test events,
- `go list -json` emits package metadata,
- `go tool compile` exposes lower-level compile behavior,
- `gopls` provides LSP diagnostics and code actions.

`gopls` diagnostics come from compilation-like analysis and optional analyzers. It uses LSP diagnostics and can provide code actions.

## Adapter Requirements

A Go adapter should:

- use `go list -json` for package discovery,
- use `go test -json` for test results,
- use `gopls` when code actions and editor-grade diagnostics are needed,
- preserve package import path and module information,
- model generated files and build tags,
- declare test execution as effectful.

## Core Commands

```bash
go list -json ./...
go test -json ./...
go test ./...
go vet ./...
gofmt -w .
go fix ./...
```

## ANCP Impact

Go proves ANCP must handle:

- JSON event streams,
- package graphs,
- build tags,
- separate compile/test/package metadata documents,
- LSP as a diagnostic source.

