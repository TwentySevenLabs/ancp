# GitHub And Release Plan

This document is the operational checklist for publishing ANCP.

## Repository Setup

Recommended GitHub repository:

```text
agent-native-compiler-protocol/ancp
```

Initial branch:

```text
main
```

Recommended repository description:

```text
Agent Native Compiler Protocol: structured diagnostics, repair plans, and compiler-facing shims for agent-native development.
```

Recommended topics:

```text
agentic-coding
compiler
diagnostics
language-server-protocol
sarif
static-analysis
ai-agents
developer-tools
```

## What To Commit

Commit:

- `src/ancp/`
- `schemas/`
- `taxonomies/`
- `spec/`
- `docs/`
- `examples/`
- `research/README.md`
- `research/tooling-matrix.md`
- `research/languages/`
- `research/standards/`
- `research/source-docs/sources.json`
- `.github/workflows/ci.yml`
- `pyproject.toml`
- `MANIFEST.in`
- `README.md`
- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `LICENSE`
- `requirements-dev.txt`
- `tools/`
- `tests/`

Do not commit generated/downloaded source snapshots unless you have reviewed upstream licensing:

- `research/source-docs/snapshots/`
- `research/source-docs/fetch-report.json`
- `research/source-docs/index.md`
- `verification-report.json`

They can be regenerated locally with:

```bash
python tools/fetch_sources.py
```

## Local Verification Before Push

```bash
python -m pip install -e ".[dev]"
python tools/fetch_sources.py
python tools/audit_contracts.py
python tools/verify_repo.py
pytest
python -m build
python -m twine check dist/*
```

## First Git Commands

```bash
git add .
git commit -m "Release ANCP reference implementation"
git branch -M main
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

## Release Checklist

1. CI passes on GitHub.
2. README quickstart works from a fresh clone.
3. `ancp manifest` emits valid JSON.
4. `ancp install-shims --dir .ancp/bin` creates compiler-name wrappers.
5. A simple Python syntax error creates `.ancp/last-check.json` through the shim path.
6. Examples validate with `ancp validate examples`.
7. `dist/*` passes `twine check`.

## Initial Release Notes

Title:

```text
ANCP 1.0.0 - Agent-native compiler protocol and reference shims
```

Body:

```text
ANCP 1.0.0 ships the first public protocol contract and Python reference implementation for agent-native compiler diagnostics.

Highlights:
- ANCP 1.0 JSON Schema
- diagnostic, repair, and effect taxonomies
- reference CLI
- compiler-name shim installation
- native-tool adapters for Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, Kotlin, .NET, Swift, Zig, Ruby, PHP, Dart, Scala, and Julia
- validation and conformance tooling
- GitHub Actions CI
- research-backed language/tooling matrix
```

## LinkedIn Positioning

Short version:

```text
I built ANCP: an Agent Native Compiler Protocol that lets normal compiler workflows emit structured diagnostics and repair plans for coding agents.

Instead of asking agents to scrape compiler prose, ANCP adds a protocol layer: stable JSON diagnostics, repair hints, safety metadata, verification steps, and compiler-facing shims.
```

Avoid overclaiming:

- say "reference implementation" for the Python package,
- say "native-tool adapters" for wrappers around existing compilers,
- reserve "compiler-native plugin" for future direct compiler integrations.
