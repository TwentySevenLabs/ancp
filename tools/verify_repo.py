#!/usr/bin/env python3
"""Verify the ANCP spec repository."""

from __future__ import annotations

import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ancp-1.0.schema.json"
REPORT_PATH = ROOT / "verification-report.json"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def rel(path: pathlib.Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def should_skip(path: pathlib.Path) -> bool:
    ignored = {".git", ".ancp", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build"}
    return any(part in ignored or part.endswith(".egg-info") for part in path.parts)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_json_parse() -> Check:
    failures: list[str] = []
    count = 0
    for path in ROOT.rglob("*.json"):
        if should_skip(path):
            continue
        count += 1
        try:
            load_json(path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{rel(path)}: {exc}")
    if failures:
        return Check("json-parse", False, "; ".join(failures[:10]))
    return Check("json-parse", True, f"parsed {count} JSON files")


def check_schema_examples() -> Check:
    try:
        import jsonschema
    except Exception as exc:  # noqa: BLE001
        return Check("schema-examples", False, f"jsonschema unavailable: {exc}")

    schema = load_json(SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)
    failures: list[str] = []
    count = 0
    for path in (ROOT / "examples").rglob("*.json"):
        count += 1
        doc = load_json(path)
        errors = sorted(validator.iter_errors(doc), key=lambda err: list(err.path))
        if errors:
            first = errors[0]
            failures.append(f"{rel(path)}: {first.message} at /{'/'.join(map(str, first.path))}")
    if failures:
        return Check("schema-examples", False, "; ".join(failures[:10]))
    return Check("schema-examples", True, f"validated {count} example documents")


def check_taxonomies() -> Check:
    failures: list[str] = []
    for path in (ROOT / "taxonomies").glob("*.json"):
        doc = load_json(path)
        entries = doc.get("entries", [])
        ids = [entry.get("id") for entry in entries]
        if any(not item for item in ids):
            failures.append(f"{rel(path)} has missing entry id")
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            failures.append(f"{rel(path)} duplicate ids: {duplicates}")
    if failures:
        return Check("taxonomies", False, "; ".join(failures))
    return Check("taxonomies", True, "taxonomy IDs are present and unique")


LOCAL_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def normalize_link_target(raw: str) -> str | None:
    target = raw.strip()
    if not target or target.startswith("#"):
        return None
    if "://" in target or target.startswith("mailto:"):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0]
    if not target:
        return None
    return target


def check_markdown_links() -> Check:
    failures: list[str] = []
    count = 0
    for path in ROOT.rglob("*.md"):
        if should_skip(path) or "source-docs/snapshots" in rel(path):
            continue
        text = path.read_text(encoding="utf-8")
        for match in LOCAL_LINK_RE.finditer(text):
            target = normalize_link_target(match.group(1))
            if target is None:
                continue
            count += 1
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                failures.append(f"{rel(path)} links outside repo: {target}")
                continue
            if not candidate.exists():
                failures.append(f"{rel(path)} missing link target: {target}")
    if failures:
        return Check("markdown-links", False, "; ".join(failures[:20]))
    return Check("markdown-links", True, f"checked {count} local markdown links")


def check_source_fetch_report() -> Check:
    report_path = ROOT / "research" / "source-docs" / "fetch-report.json"
    if not report_path.exists():
        return Check("source-fetch-report", False, "missing fetch-report.json")
    report = load_json(report_path)
    failures = [item for item in report if not item.get("ok")]
    if failures:
        ids = ", ".join(item.get("id", "?") for item in failures[:10])
        return Check("source-fetch-report", False, f"{len(failures)} failed fetches: {ids}")
    return Check("source-fetch-report", True, f"{len(report)} source snapshots fetched")


def check_required_files() -> Check:
    required = [
        "README.md",
        "LICENSE",
        "spec/ancp-1.0.md",
        "schemas/ancp-1.0.schema.json",
        "taxonomies/diagnostic-kinds.json",
        "taxonomies/repair-kinds.json",
        "taxonomies/effect-kinds.json",
        "docs/cli-contract.md",
        "docs/adapter-authoring.md",
        "docs/conformance.md",
        "docs/security.md",
        "docs/language-mapping.md",
        "research/tooling-matrix.md",
        "research/source-docs/sources.json",
        "research/source-docs/fetch-report.json",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    if missing:
        return Check("required-files", False, "missing: " + ", ".join(missing))
    return Check("required-files", True, f"{len(required)} required files present")


def main() -> int:
    checks = [
        check_required_files(),
        check_json_parse(),
        check_schema_examples(),
        check_taxonomies(),
        check_markdown_links(),
        check_source_fetch_report(),
    ]

    report = {
        "ok": all(check.ok for check in checks),
        "checks": [check.__dict__ for check in checks],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for check in checks:
        marker = "PASS" if check.ok else "FAIL"
        print(f"{marker} {check.name}: {check.detail}")

    if not report["ok"]:
        print(f"Wrote {rel(REPORT_PATH)}")
        return 1
    print(f"Wrote {rel(REPORT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
