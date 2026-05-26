# Expanded Ecosystem Notes

ANCP now includes adapters beyond the first mainstream compiler set. These adapters cover automation languages, functional languages, infrastructure-as-code, and config/data formats that coding agents edit constantly.

## Shell And PowerShell

Shell scripts and PowerShell scripts are high-impact because they sit in CI, release, deployment, and local automation paths.

Adapter strategy:

- Shell: prefer ShellCheck JSON when available; fall back to `bash -n` for syntax checks.
- PowerShell: use the built-in Parser API to emit syntax diagnostics without executing the script.

ANCP impact:

- script diagnostics must be treated as compiler-facing because broken automation can block builds even when application code is correct,
- analyzers may expose suggestions, but applying them should remain review-required.

## Lua, Perl, And R

These dynamic ecosystems have useful parser/compile-only entry points:

- Lua: `luac -p`
- Perl: `perl -c`
- R: `parse(file=...)` through `Rscript`

ANCP impact:

- a parser-only adapter is still valuable when it emits valid diagnostics and labels its scope honestly,
- richer semantic diagnostics should be optional and toolchain-specific.

## Haskell, OCaml, Erlang, Elixir, And Clojure

These ecosystems are important for compiler/tooling breadth and for projects with functional-language services.

Adapter strategy:

- Haskell: `ghc -fno-code`
- OCaml: `ocamlc -c`
- Erlang: `erlc`
- Elixir: `elixirc`
- Clojure: clj-kondo JSON where installed

ANCP impact:

- adapters must preserve module/build context where available,
- build-system integration should be optional because Stack, Cabal, Dune, Rebar, Mix, deps.edn, and Leiningen have different assumptions.

## Config, Data, And Infrastructure Languages

Agents edit JSON, TOML, YAML, Nix, Terraform, Dockerfiles, and SQL constantly. Broken config often blocks the whole project.

Adapter strategy:

- JSON/TOML/YAML: use embedded parsers for no-external-tool syntax diagnostics.
- Nix: `nix-instantiate --parse`
- Terraform: `terraform validate -json`
- Dockerfile: hadolint JSON
- SQL: sqlfluff JSON

ANCP impact:

- config diagnostics should be first-class `result.check` documents,
- missing external tools should report `tool_failed`,
- embedded parser adapters should be preferred when they are deterministic and safe.
