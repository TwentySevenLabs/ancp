# ANCP 1.0.0

ANCP 1.0.0 ships the Agent Native Compiler Protocol contract and Python reference implementation.

## Highlights

- ANCP 1.0 JSON Schema.
- Normative spec, conformance model, security model, and adapter authoring guide.
- Diagnostic, repair, and effect taxonomies.
- Reference CLI: `ancp`.
- Compiler-name shims for invisible compiler-layer usage.
- Native-tool adapters for Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, Kotlin, C#/.NET, Swift, Zig, Ruby, PHP, Dart, Scala, Julia, Shell, PowerShell, Lua, Perl, R, Haskell, OCaml, Erlang, Elixir, Clojure, Nix, Terraform, Dockerfile, and SQL.
- Built-in parser adapters for JSON, TOML, and YAML.
- Compact Markdown rendering for agent context.
- Multilingual broken-code corpus for adapter smoke testing.
- CI, packaging, verification scripts, and OSS release checklist.

## Install

```bash
python -m pip install ancp
```

For local development before publishing to PyPI:

```bash
python -m pip install -e ".[dev]"
```

## Invisible Compiler Layer

```bash
ancp install-shims --dir .ancp/bin
```

Put `.ancp/bin` first in `PATH`, then keep using normal compiler commands. ANCP preserves native stdout/stderr/exit code and writes `.ancp/last-check.json`.

## Verification

The local release was verified with:

```bash
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

## Important Scope Note

This release provides the protocol, schema, reference CLI, shims, and native-tool adapters. Direct upstream compiler plugins can emit the same ANCP schema later; the current implementation gives users the invisible compiler workflow today through local compiler-name shims and native compiler/checker integration.
