# Final Readiness Report

Date: 2026-05-24

Status: ready for GitHub publication after the maintainer chooses the final repository owner/name.

## What Is Ready

ANCP now contains:

- a normative ANCP 1.0 protocol spec,
- an ANCP 1.0 JSON Schema,
- diagnostic, repair, and effect taxonomies,
- a Python package named `ancp`,
- the `ancp` CLI,
- prefixed compiler proxies such as `ancp-cargo`, `ancp-tsc`, `ancp-python`, `ancp-kotlinc`, `ancp-julia`, `ancp-pwsh`, `ancp-terraform`, and `ancp-sqlfluff`,
- native-name compiler shims installed with `ancp install-shims`,
- adapters for Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, Kotlin, C#/.NET, Swift, Zig, Ruby, PHP, Dart, Scala, Julia, Shell, PowerShell, Lua, Perl, R, Haskell, OCaml, Erlang, Elixir, Clojure, Nix, Terraform, Dockerfile, SQL, JSON, TOML, and YAML,
- compact Markdown rendering for agents,
- a multilingual intentionally broken bug corpus,
- research notes and source document fetch tooling,
- CI, packaging metadata, tests, release notes, contribution policy, security policy, and OSS checklist docs.

## Verification Evidence

The local release was checked with these passes.

| Pass | Command | Result |
| --- | --- | --- |
| Syntax | `python -m compileall -q src tests tools` | passed |
| Unit tests | `pytest` | 14 passed |
| Source corpus | `python tools/fetch_sources.py` | fetched 77/77 source documents |
| Contract audit | `python tools/audit_contracts.py` | passed |
| Repo validator | `python tools/verify_repo.py` | passed, wrote `verification-report.json` |
| CLI JSON | `ancp manifest \| python -m json.tool` | passed |
| CLI JSON | `ancp capabilities \| python -m json.tool` | passed |
| CLI JSON | `ancp schema \| python -m json.tool` | passed |
| Shim install | `ancp install-shims --dir .ancp/bin --force` | passed |
| Shim smoke | normal `python -m py_compile bad.py` through shim | exit 1, ANCP sidecar status `failed`, 1 diagnostic |
| Bug corpus | `python tools/run_bug_corpus.py` | emitted ANCP JSON/Markdown for all 33 cases |
| Bug corpus validation | `ancp validate .ancp/bug-corpus` | passed |
| Package build | `python -m build` | built wheel and sdist |
| Package metadata | `python -m twine check dist/*` | both artifacts passed |

Local tool availability during verification:

- Installed and producing diagnostics: Python, Go, Julia, JSON, TOML, YAML, PowerShell.
- Not installed or not available in this environment: TypeScript compiler, Rust/Cargo, GCC/Clang, Java, Kotlin, .NET, Swift, Zig, Ruby, PHP, Dart, Scala, ShellCheck/Bash, Lua, Perl, R, GHC, OCaml, Erlang, Elixir, clj-kondo, Nix, Terraform, hadolint, SQLFluff.
- Missing native tools correctly report `tool_failed`; they do not pretend to pass.

## Scope Boundary

This release implements the protocol, schema, reference CLI, shims, proxies, native-tool adapters, renderers, tests, and docs.

The current compiler-facing production path is the shim/proxy layer:

```text
normal compiler command -> ANCP shim -> real native tool -> native output + .ancp/last-check.json
```

Direct upstream compiler plugins are the next integration tier. They should emit the same ANCP schema and can reuse the same taxonomies and conformance rules. The project is still useful before upstream plugins because developers can install shims and keep running normal compiler commands today.

## What To Commit

Commit these:

- `.github/`
- `src/`
- `tests/`
- `tools/`
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
- `README.md`
- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `LICENSE`
- `pyproject.toml`
- `MANIFEST.in`
- `requirements-dev.txt`
- `.gitignore`

Do not commit generated outputs by default:

- `.ancp/`
- `dist/`
- `build/`
- `src/*.egg-info/`
- `verification-report.json`
- `research/source-docs/snapshots/`
- `research/source-docs/fetch-report.json`
- `research/source-docs/index.md`

## Fresh Verification Commands

Before pushing:

```bash
python -m pip install -e ".[dev]"
python -m compileall -q src tests tools
pytest
python tools/fetch_sources.py
python tools/audit_contracts.py
python tools/verify_repo.py
ancp manifest | python -m json.tool
ancp capabilities | python -m json.tool
ancp schema | python -m json.tool
ancp install-shims --dir .ancp/bin --force
python tools/run_bug_corpus.py
ancp validate .ancp/bug-corpus
python -m build
python -m twine check dist/*
```

## GitHub Push Commands

Use these after choosing the final repo owner/name:

```bash
git status --short
git add .
git commit -m "Release ANCP 1.0.0 reference implementation"
git branch -M main
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

If the remote already exists:

```bash
git remote set-url origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

With GitHub CLI:

```bash
gh repo create <owner>/<repo> --public --source . --remote origin --push
```

## Release Commands

Create and push the tag:

```bash
git tag -a v1.0.0 -m "ANCP 1.0.0"
git push origin v1.0.0
```

Create the GitHub release:

```bash
gh release create v1.0.0 dist/ancp-1.0.0-py3-none-any.whl dist/ancp-1.0.0.tar.gz --title "ANCP 1.0.0" --notes-file RELEASE_NOTES.md
```

Optional PyPI/TestPyPI publication:

```bash
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```

## Launch Positioning

Use this wording publicly:

```text
ANCP is an Agent Native Compiler Protocol for existing languages. It lets normal compiler workflows emit structured diagnostics, repair hints, verification metadata, and compact agent-facing summaries without asking every ecosystem to adopt a new language.
```

Avoid overclaiming:

- say "reference implementation" for the Python package,
- say "native-tool adapters and compiler-name shims" for the current integration layer,
- reserve "upstream compiler plugin" for future direct compiler integrations.
