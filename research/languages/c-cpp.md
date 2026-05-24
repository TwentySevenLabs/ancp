# C And C++ Toolchain Notes

## Sources

- `research/source-docs/snapshots/c-cpp/gcc-diagnostic-formatting.html`
- `research/source-docs/snapshots/c-cpp/clang-diagnostics.html`
- `research/source-docs/snapshots/c-cpp/clang-diagnostics-reference.html`
- `research/source-docs/snapshots/c-cpp/clang-tidy.html`
- `research/source-docs/snapshots/c-cpp/json-compilation-database.html`

## ANCP-Relevant Facts

C and C++ are not analyzable correctly without the compile command context:

- include paths,
- macros,
- language standard,
- target,
- compiler flags,
- generated headers,
- translation-unit identity.

Clang defines `compile_commands.json`, a JSON compilation database used by tooling.

GCC supports structured diagnostic formatting including JSON/SARIF-oriented output and fix-it hints.

Clang diagnostics include rich source ranges and fix-it hints. `clang-tidy` provides lint diagnostics and can apply fixes.

## Adapter Requirements

A C/C++ adapter should:

- require, discover, or generate `compile_commands.json`,
- identify translation units,
- preserve compiler command arguments,
- preserve diagnostic flags and warning groups,
- map fix-it hints to source edits,
- model generated files and external headers,
- distinguish compiler diagnostics from clang-tidy/static-analysis diagnostics.

## Core Commands

```bash
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON .
clang++ -fsyntax-only file.cpp
gcc -fdiagnostics-format=json -fsyntax-only file.c
clang-tidy file.cpp --export-fixes fixes.yaml
```

## ANCP Impact

C/C++ proves ANCP needs compile-context fields. File path alone is not enough to reproduce a diagnostic.

