# ANCP Compact Signal Layer

ANCP's compact signal layer is the RTK-style output path for compiler, build,
lint, and test diagnostics. It keeps the developer workflow native while giving
agents minimal, structured diagnostic text instead of raw terminal noise.

## Purpose

Native compiler output is optimized for humans reading a terminal. Agents need a
smaller and more stable signal:

- canonical diagnostic class,
- native compiler code,
- diagnostic kind,
- primary source location,
- root-cause grouping,
- repair direction,
- raw output fallback available by command,
- token/byte savings telemetry in JSON.

The compact signal layer does not replace the ANCP JSON contract. It renders the
JSON into minimal raw text for agent context.

## Runtime Flow

```text
normal command
  python -m py_compile app.py
  cargo check
  go test ./...
  tsc --noEmit
        |
        v
ANCP native-name shim
        |
        v
real compiler/build tool
        |
        v
raw stdout/stderr saved under .ancp/runs/<run-id>/
        |
        v
result.check JSON written to .ancp/last-check.json
        |
        v
ultra-minimal error text emitted to the agent when the command fails
```

Successful commands pass through by default in `auto-ultra` mode. Failed
commands emit surgical one-line ANCP text and keep full native output on disk.

## Output Modes

| Mode | Behavior |
|---|---|
| `passthrough` | Print native stdout/stderr exactly as emitted. |
| `auto-ultra` | Print native output for successful commands; print the shortest useful ANCP text for failed commands. |
| `auto-compact` | Compatibility alias for auto-ultra failure rendering. |
| `ultra` | Always print ultra-minimal ANCP text. |
| `compact` | Always print compact ANCP raw text. |
| `json` | Print the full `result.check` JSON document. |
| `both` | Print native output and append compact ANCP text. |

Project-local shims default to `passthrough` unless configured otherwise.
`ancp enable` defaults to `auto-ultra`.

## Ultra Text Format

The default failure output intentionally avoids Markdown syntax, protocol names,
raw log paths, token stats, and guidance. It is designed to be smaller than the
useful portion of the native error when possible.

```text
SyntaxError src/app.py:15 expected ':' fix:fix syntax
```

For repeated failures, ANCP groups by root cause:

```text
TS2304 src/app.ts:8 Cannot find name 'user' x14 fix:import symbol
```

The richer compact renderer is still available when wanted:

```powershell
ancp render --from .ancp\last-check.json --format text --budget 800
```

## Global Windows Enablement

`ancp enable` installs native-name shims under:

```text
%USERPROFILE%\.ancp\bin
```

Then it prepends that directory to the Windows user PATH. New terminals will
resolve supported compiler/build/lint commands through ANCP first.

```powershell
ancp enable
ancp status
ancp disable
ancp uninstall
```

Profiles:

| Profile | Tools |
|---|---|
| `agent` | Compiler, build, lint, and language tools. This is the default. |
| `full` | Includes shell tools such as `powershell`, `pwsh`, and `bash`. Use only when explicitly needed. |

The default `agent` profile avoids shell interception because shell recursion is
higher risk than compiler interception. `full` exists for controlled testing and
specialized agent environments.

Dry-run the exact install without changing PATH:

```powershell
ancp enable --dry-run
```

Session-only activation:

```powershell
ancp enable --scope session
$env:PATH="$HOME\.ancp\bin;$env:PATH"
```

## Render Existing JSON

Render compact text from any ANCP JSON document:

```powershell
ancp render --from .ancp\last-check.json --format ultra --budget 200
```

Render Markdown for human inspection:

```powershell
ancp render --from .ancp\last-check.json --format markdown
```

## Raw Output And Bypass

Raw logs are saved but not printed in ultra output. Show the latest native log:

```powershell
ancp raw
```

Print only the raw log path:

```powershell
ancp raw --path
```

Show raw stderr from the latest run:

```powershell
ancp raw --stream stderr
```

Run a command without ANCP interception:

```powershell
ancp off -- python -m py_compile app.py
```

This is the intended manual escape hatch when an agent or user wants native
errors exactly as the compiler produced them.

## Raw Output Contract

Every proxied run records raw output metadata in `data.rawOutput`:

```json
{
  "stdoutPath": ".ancp/runs/<run-id>/stdout.txt",
  "stderrPath": ".ancp/runs/<run-id>/stderr.txt",
  "combinedPath": ".ancp/runs/<run-id>/native.log",
  "nativeBytes": 2048,
  "nativeSha256": "sha256:..."
}
```

Every proxied run also records `data.signalMetrics`:

```json
{
  "nativeBytes": 2048,
  "compactBytes": 420,
  "estimatedNativeTokens": 512,
  "estimatedCompactTokens": 20,
  "estimatedSavingsPercent": 96,
  "renderer": "ultra"
}
```

This lets agents prefer compact signal while still being able to inspect the
full native log when needed.
