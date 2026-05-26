# Toolchain Coverage

ANCP adapters are split into two layers:

1. built-in protocol and parser support that ships with the Python package,
2. native compiler/checker integrations that require the relevant ecosystem tool to be installed.

The reference package is useful even when some compilers are missing. Missing tools are reported as ANCP `tool_failed` results instead of invalid JSON or fake success.

## Check Local Availability

Run:

```bash
python tools/check_toolchains.py
```

For machine-readable output:

```bash
python tools/check_toolchains.py --json
```

By default the checker returns exit code `0` so it can be used as a report in local verification. Add `--strict` when a CI job expects every tool in that job to be installed:

```bash
python tools/check_toolchains.py --language rust --language go --strict
```

## Built In

These adapters do not require an external compiler for syntax validation:

- JSON
- TOML
- YAML

Python and PowerShell usually exist on Windows machines already, but they are still external runtime/toolchain integrations.

## Recommended Native Tools

| Language family | Tool |
| --- | --- |
| Python | `python` |
| TypeScript | `tsc` |
| JavaScript | `eslint` |
| Rust | `cargo`, `rustc` |
| Go | `go` |
| C | `gcc` or `clang` |
| C++ | `g++` or `clang++` |
| Java | `javac` |
| Kotlin | `kotlinc` |
| C#/.NET | `dotnet` |
| Swift | `swift` |
| Zig | `zig` |
| Ruby | `ruby` |
| PHP | `php` |
| Dart | `dart` |
| Scala | `scala-cli` or `scalac` |
| Julia | `julia` |
| Shell | `shellcheck` preferred, `bash` fallback |
| PowerShell | `pwsh` or Windows PowerShell |
| Lua | `luac` preferred, `lua` fallback |
| Perl | `perl` |
| R | `Rscript` |
| Haskell | `ghc` |
| OCaml | `ocamlc` |
| Erlang | `erlc` |
| Elixir | `elixirc` |
| Clojure | `clj-kondo` |
| Nix | `nix-instantiate` |
| Terraform | `terraform` |
| Dockerfile | `hadolint` |
| SQL | `sqlfluff` |

## Windows User-Level Install Examples

Use these only for tools you want to exercise locally. CI should install toolchains in dedicated jobs rather than relying on one giant image.

```powershell
scoop install shellcheck lua perl terraform hadolint
npm install -g typescript eslint
python -m pip install sqlfluff
```

Heavier ecosystems are better installed with their official installers or CI setup:

- Rust: `rustup`
- Java/Kotlin/Scala: JDK plus Kotlin/Scala tooling
- Haskell: GHCup
- OCaml: opam
- Erlang/Elixir: official installers or package manager images
- R: CRAN R installer
- Swift, Zig, Dart, Ruby, PHP, Nix: ecosystem-specific installers

## CI Strategy

Do not require every compiler in one job. Use a matrix:

- core job: schema validation, unit tests, package build, JSON/TOML/YAML/Python checks,
- systems job: Rust, Go, C/C++, Zig,
- JVM/.NET job: Java, Kotlin, Scala, C#,
- dynamic job: JavaScript, TypeScript, Ruby, PHP, Dart, Julia, Lua, Perl, R,
- functional job: Haskell, OCaml, Erlang, Elixir, Clojure,
- infrastructure job: Shell, PowerShell, Nix, Terraform, Dockerfile, SQL.

Each job should run:

```bash
python tools/check_toolchains.py --json --strict --language rust --language go
python tools/run_bug_corpus.py
ancp validate .ancp/bug-corpus
```

The matrix should fail when an expected installed compiler returns `tool_failed`, but the local all-language corpus may still pass schema validation when a developer has partial tooling.
