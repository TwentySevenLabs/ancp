# TypeScript And JavaScript Toolchain Notes

## Sources

- `research/source-docs/snapshots/typescript/tsc-compiler-options.html`
- `research/source-docs/snapshots/typescript/compiler-api.md`
- `research/source-docs/snapshots/javascript/eslint-formatters.html`
- `research/source-docs/snapshots/javascript/eslint-custom-formatters.html`

## ANCP-Relevant Facts

TypeScript has a strong compiler API that exposes structured diagnostics. The `tsc` CLI is useful for verification, but an ANCP adapter should prefer the Compiler API or language service when it needs reliable spans, categories, codes, and fixes.

ESLint provides JSON and JSON-with-metadata formatters. ESLint results include rule IDs, severities, messages, locations, fix metadata, and suggestions.

JavaScript by itself is usually checked by parser/linter/bundler/test tools rather than one official compiler.

## Adapter Requirements

A TypeScript adapter should:

- detect `tsconfig.json`,
- preserve `TSxxxx` native codes,
- map TypeScript diagnostic category to ANCP severity,
- use Compiler API spans as source ranges,
- use Language Service code fixes as repair plans,
- keep `tsc --noEmit` as a verification step.

A JavaScript adapter should:

- detect package manager and project scripts,
- use ESLint JSON when configured,
- preserve parser errors separately from lint rules,
- avoid running package scripts automatically without effect declarations.

## Core Commands

```bash
tsc --noEmit --pretty false
npx eslint --format json .
npx eslint --format json-with-metadata .
npx eslint --fix-dry-run --format json .
```

## ANCP Impact

TypeScript and ESLint prove ANCP must support:

- native codes,
- native rule metadata,
- fix ranges,
- suggestions separate from fixes,
- programmatic APIs as a better source than CLI text.

