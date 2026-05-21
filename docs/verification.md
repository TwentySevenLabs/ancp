# Verification

This repository is verified with three independent passes.

## Pass 1: Source Corpus Fetch

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

- all configured source documents fetch successfully,
- failed downloads are reported explicitly.

## Pass 2: Contract Coverage Audit

Command:

```bash
python tools/audit_contracts.py
```

Purpose:

- checks schema document kinds,
- checks spec document-kind coverage,
- checks profile coverage,
- checks examples cover all document kinds,
- checks source corpus covers required language ecosystems,
- checks required docs are substantive,
- checks taxonomies have meaningful coverage,
- checks README production-quality framing.

Expected result:

- every semantic coverage check passes.

## Pass 3: Repository Validator

Command:

```bash
python tools/verify_repo.py
```

Purpose:

- parses every JSON file,
- validates examples against `schemas/ancp-1.0.schema.json`,
- checks taxonomy ID uniqueness,
- checks local Markdown links,
- checks source fetch report,
- writes `verification-report.json`.

Expected result:

- all repository-level validation checks pass.

## Current Verification Status

Last verified on 2026-05-21.

The final local verification state is recorded in `verification-report.json`.

