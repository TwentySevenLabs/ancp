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
- raw output fallback path,
- token/byte savings telemetry.

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
compact raw text emitted to the agent when the command fails
```

Successful commands pass through by default in `auto-compact` mode. Failed
commands emit compact ANCP text and keep full native output on disk.

## Output Modes

| Mode | Behavior |
|---|---|
| `passthrough` | Print native stdout/stderr exactly as emitted. |
| `auto-compact` | Print native output for successful commands; print compact ANCP text for failed commands. |
| `compact` | Always print compact ANCP raw text. |
| `json` | Print the full `result.check` JSON document. |
| `both` | Print native output and append compact ANCP text. |

Project-local shims default to `passthrough` unless configured otherwise.
`ancp enable` defaults to `auto-compact`.

## Minimal Text Format

The compact text intentionally avoids Markdown syntax. It is designed for agent
context, not documentation.

```text
ANCP result.check failed diagnostics=1
exit=1 durationMs=92
raw=C:\repo\.ancp\runs\sha256-abc\native.log
tokens native~2400 compact~180 saved~92%
summary severity=error:1 kind=syntax:1
root_causes=1
1. code=ancp.diag.syntax.invalid native=SyntaxError kind=syntax count=1
   at=C:/repo/app.py:15:1
   msg=SyntaxError: expected ':'
   fix=Fix Python syntax [review_required] c=0.40
agent_next=fix root_causes first; rerun native command before claiming verified
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
ancp render --from .ancp\last-check.json --format text --budget 800
```

Render Markdown for human inspection:

```powershell
ancp render --from .ancp\last-check.json --format markdown
```

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
  "estimatedCompactTokens": 105,
  "estimatedSavingsPercent": 79,
  "renderer": "raw-text"
}
```

This lets agents prefer compact signal while still being able to inspect the
full native log when needed.
