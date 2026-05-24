# Contributing

ANCP is a protocol and reference implementation for agent-native compiler diagnostics. Contributions should preserve the core contract: normal toolchains stay usable, ANCP adds structured diagnostics and repair metadata, and adapters report support honestly.

## Local Setup

```bash
python -m pip install -e ".[dev]"
```

## Required Checks

Run these before opening a pull request:

```bash
python -m compileall -q src tests tools
pytest
python tools/audit_contracts.py
python tools/verify_repo.py
python tools/run_bug_corpus.py
python -m build
python -m twine check dist/*
```

If research sources changed, also run:

```bash
python tools/fetch_sources.py
```

## Adapter Rules

Adapters must:

- preserve native diagnostic codes when available,
- prefer structured native output over text parsing,
- emit schema-valid ANCP documents on success and failure,
- report missing tools as `tool_failed`,
- avoid mutating user files during check, explain, verify, or repair-plan operations,
- mark effectful commands with effect metadata,
- treat auto-fixes as review-required unless the adapter can prove the action is safe.

## Documentation Rules

When adding a language or toolchain, update:

- `src/ancp/adapters/`,
- `research/source-docs/sources.json`,
- `research/tooling-matrix.md`,
- `research/languages/`,
- `docs/language-mapping.md` if canonical mappings change,
- tests and examples as needed.

## Pull Request Shape

Keep pull requests focused:

- one protocol/schema change per PR,
- one adapter family per PR,
- tests for parser and CLI behavior,
- documentation for new user-visible behavior.

Do not include generated directories such as `dist/`, `build/`, `.ancp/`, `.pytest_cache/`, or downloaded source snapshots unless maintainers explicitly ask for a frozen evidence artifact.
