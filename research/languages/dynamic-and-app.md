# Ruby, PHP, Dart, And Similar Dynamic/App Toolchains

## Sources

- `research/source-docs/snapshots/ruby/options.html`
- `research/source-docs/snapshots/ruby/documentation.html`
- `research/source-docs/snapshots/php/commandline-options.html`
- `research/source-docs/snapshots/dart/dart-analyze.html`
- `research/source-docs/snapshots/dart/dart-fix.html`

## Ruby

Ruby supports `ruby -c` for syntax checking without execution. Richer diagnostics and fixes usually come from RuboCop, Sorbet, Steep, or language servers.

## PHP

PHP supports `php -l` for syntax checking. Richer static diagnostics come from PHPStan, Psalm, PHPCS, Rector, and IDE/language-server tools.

## Dart

Dart provides `dart analyze` for static analysis and `dart fix` for automated fixes. `dart fix` has a dry-run/apply split, which maps cleanly to ANCP repair plan and apply phases.

## Adapter Requirements

Adapters for these ecosystems should:

- distinguish syntax checking from static analysis,
- preserve linter/static analyzer rule IDs,
- mark dynamic test execution as effectful,
- use dry-run fix modes as repair plans when available,
- avoid claiming type guarantees when only syntax checking ran.

## ANCP Impact

These languages prove ANCP cannot assume every language has a static compiler, but the protocol still works when adapters compose syntax checkers, analyzers, linters, formatters, and test runners.

