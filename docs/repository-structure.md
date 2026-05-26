# Repository Structure

```text
.
|-- README.md
|-- LICENSE
|-- CHANGELOG.md
|-- RELEASE_NOTES.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- CODE_OF_CONDUCT.md
|-- pyproject.toml
|-- MANIFEST.in
|-- requirements-dev.txt
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- src/
|   `-- ancp/
|       |-- cli.py
|       |-- proxy.py
|       |-- shim.py
|       |-- render.py
|       |-- native.py
|       |-- schema.py
|       |-- documents.py
|       |-- adapters/
|       |   |-- base.py
|       |   `-- registry.py
|       `-- resources/
|           |-- schemas/
|           `-- taxonomies/
|-- spec/
|   `-- ancp-1.0.md
|-- schemas/
|   `-- ancp-1.0.schema.json
|-- taxonomies/
|   |-- diagnostic-kinds.json
|   |-- effect-kinds.json
|   `-- repair-kinds.json
|-- docs/
|   |-- adapter-authoring.md
|   |-- cli-contract.md
|   |-- conformance.md
|   |-- execution-breakdown.md
|   |-- github-release-plan.md
|   |-- implementation-roadmap.md
|   |-- invisible-compiler-layer.md
|   |-- language-mapping.md
|   |-- overview.md
|   |-- repository-structure.md
|   |-- security.md
|   |-- sources.md
|   |-- verification.md
|   |-- vision-doctrine.md
|   `-- adr/
|-- research/
|   |-- README.md
|   |-- tooling-matrix.md
|   |-- languages/
|   |-- standards/
|   `-- source-docs/
|       `-- sources.json
|-- examples/
|   |-- generic/
|   |-- python/
|   |-- rust/
|   |-- typescript/
|   |-- buggy/
|   |-- manifest.adapter.json
|   `-- manifest.capabilities.json
|-- tests/
|   |-- test_cli_documents.py
|   |-- test_parsers.py
|   |-- test_proxy_and_shims.py
|   |-- test_render.py
|   `-- test_schema_examples.py
`-- tools/
    |-- audit_contracts.py
    |-- fetch_sources.py
    |-- run_bug_corpus.py
    `-- verify_repo.py
```

## Source Package

`src/ancp` is the installable Python package. It provides:

- `ancp`: the reference CLI for manifest, capability, check, explain, repair-plan, verify, graph, skills, validate, render, schema, and shim installation.
- `ancp.proxy`: prefixed compiler proxies such as `ancp-cargo`, `ancp-tsc`, `ancp-python`, `ancp-kotlinc`, and `ancp-julia`.
- `ancp.shim`: native-name wrappers installed by `ancp install-shims`, so normal commands such as `cargo check` and `python -m py_compile app.py` can emit ANCP sidecars.
- `ancp.adapters`: native-tool adapters for Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, Kotlin, C#/.NET, Swift, Zig, Ruby, PHP, Dart, Scala, Julia, Shell, PowerShell, Lua, Perl, R, Haskell, OCaml, Erlang, Elixir, Clojure, Nix, Terraform, Dockerfile, SQL, JSON, TOML, and YAML.
- `ancp.resources`: packaged copies of the ANCP schema and taxonomies for installed environments.

## Contract Artifacts

The normative protocol lives in `spec/`, `schemas/`, and `taxonomies/`.

The documentation in `docs/` explains the protocol, security model, conformance requirements, adapter authoring model, invisible compiler layer, and OSS release process.

The research notes in `research/` record the compiler/tooling surface used to design ANCP. Generated source snapshots under `research/source-docs/snapshots/` are intentionally not committed by default; regenerate them with `python tools/fetch_sources.py`.

## Examples And Tests

`examples/` contains schema-valid protocol documents and a multilingual broken-code corpus. The corpus is used by `tools/run_bug_corpus.py` to verify that installed native toolchains produce ANCP JSON and compact Markdown.

`tests/` contains unit coverage for schema validation, parser normalization, CLI documents, Markdown rendering, proxy mode, and shim behavior.
