# Invisible Compiler Layer

ANCP is not only a command that agents call.

The intended production shape is:

```text
developer runs normal command
        |
        v
compiler-name ANCP shim or compiler plugin
        |
        v
real native compiler/checker/test tool
        |
        v
normal stdout/stderr/exit code + ANCP JSON sidecar
```

The developer still runs:

```bash
cargo check
tsc --noEmit
python -m py_compile app.py
julia app.jl
kotlinc Main.kt
gcc -fsyntax-only main.c
clang++ -fsyntax-only main.cpp
```

The invisible ANCP layer preserves native behavior and writes:

```text
.ancp/last-check.json
```

That JSON is the agent-native diagnostic stream.

## Installation Flow

Install the package:

```bash
python -m pip install ancp
```

Install local compiler-name shims:

```bash
ancp install-shims --dir .ancp/bin
```

Prepend the shim directory to PATH.

PowerShell:

```powershell
$env:PATH = "$PWD\.ancp\bin;$env:PATH"
```

POSIX shells:

```bash
export PATH="$PWD/.ancp/bin:$PATH"
```

Now normal compiler commands pass through ANCP.

## Supported Native Names

The reference implementation can create shims for:

- `tsc`
- `eslint`
- `pyright`
- `ruff`
- `python`
- `python3`
- `cargo`
- `rustc`
- `go`
- `gcc`
- `g++`
- `clang`
- `clang++`
- `javac`
- `kotlinc`
- `dotnet`
- `swift`
- `zig`
- `ruby`
- `php`
- `dart`
- `scala-cli`
- `scalac`
- `julia`

These shims do not replace compilers. They find the real compiler later in PATH, execute it, preserve its output and exit code, then emit ANCP JSON.

## Compiler Plugins Vs Shims

The long-term best integration is compiler-native:

- rustc/cargo message-format adapters,
- TypeScript Compiler API / language service adapter,
- Kotlin compiler plugin or build-tool integration,
- Julia LanguageServer/StaticLint integration,
- GCC/Clang diagnostic/fix-it adapter,
- Roslyn analyzer/code-fix adapter,
- Go/gopls adapter.

Shims are the bootstrap layer. They let users get the invisible workflow now, while deeper compiler plugins can later emit ANCP directly.

## Why Shims Are Still Valid

A shim is production-acceptable when it obeys these rules:

- it preserves native stdout,
- it preserves native stderr,
- it preserves native exit code,
- it does not mutate compiler arguments unless explicitly configured,
- it writes ANCP JSON as a sidecar,
- it reports missing native tools honestly,
- it validates emitted ANCP documents.

That gives agents a stable protocol without forcing every language compiler project to accept upstream patches first.

