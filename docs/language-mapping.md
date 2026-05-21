# Language Mapping Guide

This guide maps common language/toolchain diagnostics to ANCP fields.

## Canonical Diagnostic Codes

Core ANCP codes should be broad and reusable.

Recommended initial canonical code set:

| Canonical code | Meaning |
| --- | --- |
| `ancp.diag.syntax.invalid` | Source cannot be parsed. |
| `ancp.diag.symbol.unresolved` | Name/symbol/member cannot be found. |
| `ancp.diag.symbol.unused` | Symbol/import/variable is unused. |
| `ancp.diag.type.mismatch` | Actual type does not match expected type. |
| `ancp.diag.type.missing_annotation` | Required annotation is absent. |
| `ancp.diag.call.missing_argument` | Call lacks required argument. |
| `ancp.diag.call.extra_argument` | Call has unsupported argument. |
| `ancp.diag.import.missing` | Import/include/module cannot be resolved. |
| `ancp.diag.dependency.missing` | Dependency is missing from environment or manifest. |
| `ancp.diag.config.invalid` | Configuration is invalid. |
| `ancp.diag.format.not_formatted` | Formatter would change file. |
| `ancp.diag.lint.rule_violation` | Linter rule violation. |
| `ancp.diag.test.assertion_failed` | Test assertion failed. |
| `ancp.diag.build.failed` | Build step failed. |
| `ancp.diag.security.secret_detected` | Secret or credential found in code. |
| `ancp.diag.effect.undeclared` | Effect/capability was used without declaration. |
| `ancp.diag.unknown` | Unknown classification. |

## TypeScript

| Native | ANCP |
| --- | --- |
| `TS2304` Cannot find name | `ancp.diag.symbol.unresolved` |
| `TS2307` Cannot find module | `ancp.diag.import.missing` |
| `TS2322` Type not assignable | `ancp.diag.type.mismatch` |
| `TS2345` Argument type mismatch | `ancp.diag.type.mismatch` |
| `TS2554` Expected N arguments | `ancp.diag.call.missing_argument` or `ancp.diag.call.extra_argument` |

Preferred input: TypeScript Compiler API.

Verification: `tsc --noEmit --pretty false`.

## JavaScript / ESLint

| Native | ANCP |
| --- | --- |
| Parser error | `ancp.diag.syntax.invalid` |
| `no-unused-vars` | `ancp.diag.symbol.unused` |
| `no-undef` | `ancp.diag.symbol.unresolved` |
| rule violation | `ancp.diag.lint.rule_violation` |

Preferred input: ESLint `json-with-metadata` or Node API.

Repair: ESLint fixes and suggestions.

## Python

| Native | ANCP |
| --- | --- |
| `SyntaxError` | `ancp.diag.syntax.invalid` |
| Pyright `reportMissingImports` | `ancp.diag.import.missing` |
| Pyright `reportUndefinedVariable` | `ancp.diag.symbol.unresolved` |
| Ruff `F401` | `ancp.diag.symbol.unused` |
| Ruff formatter diff | `ancp.diag.format.not_formatted` |

Preferred input: Pyright JSON, mypy JSON, Ruff JSON.

Verification: `python -m compileall`, `pyright`, `mypy`, `ruff check`, project tests.

## Go

| Native | ANCP |
| --- | --- |
| undefined name | `ancp.diag.symbol.unresolved` |
| cannot use X as Y | `ancp.diag.type.mismatch` |
| import not used | `ancp.diag.symbol.unused` |
| package not found | `ancp.diag.import.missing` |
| test fail event | `ancp.diag.test.assertion_failed` |

Preferred input: `gopls` diagnostics, `go list -json`, `go test -json`.

## Rust

| Native | ANCP |
| --- | --- |
| `E0425` cannot find value | `ancp.diag.symbol.unresolved` |
| `E0308` mismatched types | `ancp.diag.type.mismatch` |
| borrow checker errors | `ancp.diag.lifetime` or `ancp.diag.ownership` (core diagnostic kinds) |
| unused variable lint | `ancp.diag.symbol.unused` |
| `E0505` cannot move out of borrowed | `ancp.diag.ownership` |
| `E0506` assignment to borrowed path | `ancp.diag.ownership` |
| `E0597` value does not live long enough | `ancp.diag.lifetime` |

Preferred input: `cargo check --message-format=json`.

Repair: rustc suggestions and `cargo fix`.

## C / C++

| Native | ANCP |
| --- | --- |
| missing header | `ancp.diag.import.missing` |
| undeclared identifier | `ancp.diag.symbol.unresolved` |
| incompatible pointer/integer/type | `ancp.diag.type.mismatch` |
| clang-tidy check | `ancp.diag.lint.rule_violation` |
| linker error | `ancp.diag.build.failed` |

Required context: compile command, translation unit, include paths, macros, target.

## Java

| Native | ANCP |
| --- | --- |
| cannot find symbol | `ancp.diag.symbol.unresolved` |
| package does not exist | `ancp.diag.import.missing` |
| incompatible types | `ancp.diag.type.mismatch` |
| annotation processor error | `ancp.diag.build.failed` or custom |

Preferred input: Java Compiler API diagnostics.

## Kotlin

| Native | ANCP |
| --- | --- |
| unresolved reference | `ancp.diag.symbol.unresolved` |
| type mismatch | `ancp.diag.type.mismatch` |
| no value passed | `ancp.diag.call.missing_argument` |
| compiler warning name | preserve under `nativeCode` |

Preferred input: build tool/IDE APIs where available; direct `kotlinc` otherwise.

## C# / .NET

| Native | ANCP |
| --- | --- |
| `CS0103` name does not exist | `ancp.diag.symbol.unresolved` |
| `CS0246` type/namespace not found | `ancp.diag.symbol.unresolved` or `ancp.diag.import.missing` |
| `CS0029` cannot convert type | `ancp.diag.type.mismatch` |
| `IDE0005` unnecessary using | `ancp.diag.symbol.unused` |
| `CAxxxx` analyzer rule | `ancp.diag.lint.rule_violation` or `ancp.diag.security.*` |

Preferred input: Roslyn/MSBuild.

## Swift

| Native | ANCP |
| --- | --- |
| cannot find in scope | `ancp.diag.symbol.unresolved` |
| no such module | `ancp.diag.import.missing` |
| cannot convert value | `ancp.diag.type.mismatch` |
| exhaustive switch issue | `ancp.diag.contract` or `ancp.diag.type.mismatch` depending context |

Preferred input: SourceKit-LSP plus SwiftPM/compiler output.

## Zig

| Native | ANCP |
| --- | --- |
| expected token | `ancp.diag.syntax.invalid` |
| use of undeclared identifier | `ancp.diag.symbol.unresolved` |
| expected type | `ancp.diag.type.mismatch` |
| build step failure | `ancp.diag.build.failed` |

Preferred input: `zig build`, `zig test`, direct compiler output.

## Ruby

| Native | ANCP |
| --- | --- |
| `ruby -c` syntax failure | `ancp.diag.syntax.invalid` |
| RuboCop rule | `ancp.diag.lint.rule_violation` |
| Sorbet/Steep type error | `ancp.diag.type.mismatch` |

## PHP

| Native | ANCP |
| --- | --- |
| `php -l` parse error | `ancp.diag.syntax.invalid` |
| PHPStan/Psalm undefined class/function | `ancp.diag.symbol.unresolved` |
| PHPStan/Psalm type issue | `ancp.diag.type.mismatch` |
| PHPCS rule | `ancp.diag.lint.rule_violation` |

## Dart

| Native | ANCP |
| --- | --- |
| analyzer undefined identifier | `ancp.diag.symbol.unresolved` |
| analyzer type error | `ancp.diag.type.mismatch` |
| lint | `ancp.diag.lint.rule_violation` |
| `dart fix --dry-run` proposed fix | `plan.repair` |

## Scala

| Native | ANCP |
| --- | --- |
| not found | `ancp.diag.symbol.unresolved` |
| type mismatch | `ancp.diag.type.mismatch` |
| implicit/given resolution issue | `ancp.diag.trait` or custom |
| build server diagnostic | preserve source and native code where available |

