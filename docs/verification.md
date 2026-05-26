# Verification

ANCP is verified with five independent local passes. The goal is not only "the tests pass"; it is that the contract, package, compiler-facing shims, examples, research corpus, and release artifacts agree with each other.

## Pass 1: Research Source Fetch

Command:

```bash
python tools/fetch_sources.py
```

Purpose:

- downloads official/source documents listed in `research/source-docs/sources.json`,
- writes snapshots under `research/source-docs/snapshots`,
- writes `research/source-docs/fetch-report.json`,
- writes `research/source-docs/index.md`.

Expected result:

- every configured source document fetches successfully,
- failures are listed explicitly with the failing source id and URL.

## Pass 2: Contract Coverage Audit

Command:

```bash
python tools/audit_contracts.py
```

Purpose:

- checks schema document kinds,
- checks spec document-kind coverage,
- checks profile coverage,
- checks example coverage,
- checks source corpus language coverage,
- checks required docs are substantive,
- checks taxonomy coverage,
- checks README quality framing.

Expected result:

- every semantic coverage check passes.

## Pass 3: Repository Validator

Command:

```bash
python tools/verify_repo.py
```

Purpose:

- parses every committed JSON file,
- validates examples against `schemas/ancp-1.0.schema.json`,
- checks taxonomy ID uniqueness,
- checks local Markdown links,
- checks source fetch report,
- writes `verification-report.json`.

Expected result:

- all repository-level validation checks pass.

## Pass 4: Package And Runtime Tests

Commands:

```bash
python -m compileall -q src tests tools
pytest
ancp manifest | python -m json.tool
ancp capabilities | python -m json.tool
ancp schema | python -m json.tool
python -m build
python -m twine check dist/*
python tools/check_toolchains.py
```

Purpose:

- verifies Python syntax,
- exercises parser, renderer, schema, proxy, shim, and CLI unit tests,
- confirms top-level CLI commands emit parseable JSON,
- confirms wheel and source distributions can be built,
- confirms package metadata is acceptable to Python packaging tools.
- reports which native language toolchains are available for real compiler-backed smoke coverage.

Expected result:

- syntax compilation exits 0,
- unit tests pass,
- CLI JSON commands parse,
- build succeeds,
- `twine check` reports `PASSED` for every built artifact.
- installed native toolchains appear in the availability report; missing optional toolchains are expected on partial developer machines.

## Pass 5: Invisible Compiler Layer And Bug Corpus

Commands:

```bash
ancp install-shims --dir .ancp/bin --force
python tools/run_bug_corpus.py
```

For a direct shim smoke test:

```bash
mkdir -p .ancp/shim-smoke
printf 'def broken(:\n    pass\n' > .ancp/shim-smoke/bad.py
cd .ancp/shim-smoke
PATH="$PWD/../bin:$PATH" python -m py_compile bad.py
ancp render --from .ancp/last-check.json
```

On PowerShell, prepend the shim directory with:

```powershell
$env:PATH="$PWD\.ancp\bin;$env:PATH"
```

Purpose:

- confirms native-name compiler shims can be installed,
- confirms normal compiler commands preserve native output and exit code,
- confirms ANCP sidecars are written to `.ancp/last-check.json`,
- confirms the broken-code corpus produces ANCP JSON and Markdown where native compilers are installed,
- confirms missing local compilers are reported as `tool_failed` instead of pretending to pass.

Expected result:

- shim installation emits valid JSON,
- a broken Python file produces a failed ANCP sidecar through normal `python -m py_compile`,
- bug corpus entries with installed native tools report diagnostics,
- languages without installed tools report `tool_failed` honestly.

## Current Verification Status

The most recent local status is recorded in `docs/final-readiness-report.md` when a release is prepared.

`verification-report.json`, `.ancp/bug-corpus/`, `dist/`, `build/`, and downloaded source snapshots are generated outputs. They are useful verification evidence locally, but they are not required to be committed unless the maintainer deliberately wants to publish a frozen evidence snapshot.
