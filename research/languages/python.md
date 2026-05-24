# Python Toolchain Notes

## Sources

- `research/source-docs/snapshots/python/py_compile.html`
- `research/source-docs/snapshots/python/compileall.html`
- `research/source-docs/snapshots/python/pyright-command-line.md`
- `research/source-docs/snapshots/python/mypy-command-line.html`
- `research/source-docs/snapshots/python/ruff-settings.html`
- `research/source-docs/snapshots/python/ruff-formatter.html`

## ANCP-Relevant Facts

Python does not have one canonical project compiler. A useful Python adapter is a composition of:

- CPython syntax compilation via `py_compile` or `compileall`,
- type analysis via Pyright or mypy,
- lint and style analysis via Ruff,
- tests via pytest/unittest or project-native commands.

CPython syntax compilation provides syntax errors but not a rich cross-project diagnostic model.

Pyright supports structured JSON output through `--outputjson`.

Mypy has command-line diagnostics and supports JSON output in modern releases through `--output json`.

Ruff supports machine-readable output formats including JSON and can also format or fix code.

## Adapter Requirements

A Python ANCP adapter should:

- detect `pyproject.toml`, `setup.cfg`, `tox.ini`, `mypy.ini`, `ruff.toml`, and lockfiles,
- report each analyzer separately in `toolchain`,
- preserve native rule names such as Ruff rule IDs and Pyright diagnostic rule names,
- classify CPython parser failures as `syntax`,
- classify Pyright/mypy failures as `type`, `symbol`, `import`, `configuration`, or `unknown`,
- treat Ruff autofixes as repair plans with `review_required` unless the rule is known behavior-preserving,
- mark test execution as effectful because tests can run arbitrary code.

## Core Commands

```bash
python -m py_compile path/to/file.py
python -m compileall -q .
pyright --outputjson
mypy --output json .
ruff check --output-format json .
ruff format --check .
```

## ANCP Impact

Python proves ANCP must support multi-tool language adapters. The adapter is not always "the compiler."

