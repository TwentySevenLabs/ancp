# .NET Toolchain Notes

## Sources

- `research/source-docs/snapshots/csharp/compiler-options.html`
- `research/source-docs/snapshots/csharp/compiler-options-advanced.html`
- `research/source-docs/snapshots/csharp/dotnet-format.html`
- `research/source-docs/snapshots/csharp/code-analysis-overview.html`

## ANCP-Relevant Facts

C# and .NET projects are normally built through `dotnet build` and MSBuild rather than direct `csc` invocation.

The Roslyn compiler platform exposes structured diagnostics and analyzers. Diagnostic IDs such as `CSxxxx`, `IDExxxx`, and `CAxxxx` are important stable native codes.

`dotnet format` can fix formatting, code style, and analyzer issues, supports filtering by diagnostic IDs, and can produce a JSON report. Its documentation notes that it may restore, compile, and run analyzers, so it must be treated as effectful.

## Adapter Requirements

A .NET adapter should:

- detect solution/project files,
- use Roslyn/MSBuild APIs when possible,
- preserve diagnostic IDs and analyzer rule IDs,
- report nullable/unsafe/langversion configuration,
- model `dotnet format` as review-required because it may restore/build/run analyzers,
- verify with `dotnet build` and `dotnet test`.

## Core Commands

```bash
dotnet build
dotnet test
dotnet format --verify-no-changes
dotnet format --report ancp-dotnet-format-report
```

## ANCP Impact

.NET proves ANCP must model build systems that execute analyzers and restore dependencies during apparently simple formatting operations.

