# Changelog

All notable changes to ANCP are documented here.

## 1.0.0 - 2026-05-24

Initial public release.

### Added

- ANCP 1.0 normative specification.
- JSON Schema Draft 2020-12 protocol schema.
- Diagnostic, repair, and effect taxonomies.
- Python reference package with `ancp` CLI.
- Compiler-facing proxy entry points such as `ancp-cargo`, `ancp-tsc`, `ancp-python`, `ancp-kotlinc`, and `ancp-julia`.
- Native-name shim installer via `ancp install-shims`.
- Native-tool adapters for Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, Kotlin, C#/.NET, Swift, Zig, Ruby, PHP, Dart, Scala, Julia, Shell, PowerShell, Lua, Perl, R, Haskell, OCaml, Erlang, Elixir, Clojure, Nix, Terraform, Dockerfile, SQL, JSON, TOML, and YAML.
- Markdown renderer for compact agent-facing diagnostic summaries.
- Multilingual intentionally broken bug corpus.
- Repository validation, contract audit, source fetch, and bug corpus scripts.
- GitHub Actions CI.
- Research corpus covering language/toolchain docs and adjacent standards.

### Verification

- Syntax compilation passes.
- Unit tests pass.
- Schema examples validate.
- Contract audit passes.
- Source corpus fetch passes.
- Wheel and sdist build successfully.
- `twine check` passes for release artifacts.
- Shim smoke test writes a valid ANCP sidecar from a normal compiler command.
- Bug corpus emits ANCP-valid JSON reports.
