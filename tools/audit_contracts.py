#!/usr/bin/env python3
"""Semantic coverage audit for ANCP spec artifacts."""

from __future__ import annotations

import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "ancp-1.0.schema.json").read_text(encoding="utf-8"))
SPEC_TEXT = (ROOT / "spec" / "ancp-1.0.md").read_text(encoding="utf-8")
README_TEXT = (ROOT / "README.md").read_text(encoding="utf-8")
SOURCES = json.loads((ROOT / "research" / "source-docs" / "sources.json").read_text(encoding="utf-8"))


REQUIRED_DOC_KINDS = [
    "manifest.adapter",
    "manifest.capabilities",
    "result.check",
    "result.explain",
    "plan.repair",
    "result.apply",
    "result.verify",
    "graph.code",
    "result.skills",
]

REQUIRED_PROFILES = [
    "core",
    "explain",
    "repair-plan",
    "repair-apply",
    "verify",
    "graph",
    "effects",
    "skills",
    "export",
]

REQUIRED_LANGUAGES = [
    "python",
    "typescript",
    "javascript",
    "go",
    "rust",
    "c-cpp",
    "java",
    "kotlin",
    "csharp",
    "swift",
    "zig",
    "ruby",
    "php",
    "dart",
    "scala",
]

REQUIRED_DOCS = [
    "docs/overview.md",
    "docs/cli-contract.md",
    "docs/adapter-authoring.md",
    "docs/conformance.md",
    "docs/security.md",
    "docs/language-mapping.md",
    "docs/implementation-roadmap.md",
    "research/tooling-matrix.md",
]


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


def pass_check(message: str) -> None:
    print(f"PASS {message}")


def example_doc_kinds() -> set[str]:
    kinds: set[str] = set()
    for path in (ROOT / "examples").rglob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        kinds.add(doc["documentKind"])
    return kinds


def main() -> int:
    schema_doc_kinds = set(SCHEMA["properties"]["documentKind"]["enum"])
    missing_schema_kinds = sorted(set(REQUIRED_DOC_KINDS) - schema_doc_kinds)
    if missing_schema_kinds:
        fail(f"schema missing document kinds: {missing_schema_kinds}")
    pass_check("schema contains all required document kinds")

    missing_spec_kinds = [kind for kind in REQUIRED_DOC_KINDS if kind not in SPEC_TEXT]
    if missing_spec_kinds:
        fail(f"spec missing document kind mentions: {missing_spec_kinds}")
    pass_check("spec mentions all document kinds")

    schema_profiles = set(SCHEMA["$defs"]["profile"]["enum"])
    missing_schema_profiles = sorted(set(REQUIRED_PROFILES) - schema_profiles)
    if missing_schema_profiles:
        fail(f"schema missing profiles: {missing_schema_profiles}")
    pass_check("schema contains all required profiles")

    missing_spec_profiles = [profile for profile in REQUIRED_PROFILES if profile not in SPEC_TEXT]
    if missing_spec_profiles:
        fail(f"spec missing profile mentions: {missing_spec_profiles}")
    pass_check("spec mentions all profiles")

    kinds = example_doc_kinds()
    missing_examples = sorted(set(REQUIRED_DOC_KINDS) - kinds)
    if missing_examples:
        fail(f"examples missing document kinds: {missing_examples}")
    pass_check("examples cover every document kind")

    source_languages = {source["language"] for source in SOURCES}
    missing_languages = sorted(set(REQUIRED_LANGUAGES) - source_languages)
    if missing_languages:
        fail(f"source corpus missing languages: {missing_languages}")
    pass_check("source corpus covers required language ecosystems")

    for doc in REQUIRED_DOCS:
        path = ROOT / doc
        if not path.exists():
            fail(f"missing required doc {doc}")
        text = path.read_text(encoding="utf-8")
        if len(re.sub(r"\\s+", "", text)) < 500:
            fail(f"required doc too thin: {doc}")
    pass_check("required docs exist and are substantive")

    for taxonomy in ["diagnostic-kinds", "repair-kinds", "effect-kinds"]:
        path = ROOT / "taxonomies" / f"{taxonomy}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        if len(doc.get("entries", [])) < 10:
            fail(f"taxonomy too small: {taxonomy}")
    pass_check("taxonomies have meaningful coverage")

    if "Agent Native Compiler Protocol" not in README_TEXT:
        fail("README does not introduce project name")
    if "Production" not in README_TEXT and "production" not in README_TEXT:
        fail("README does not discuss production quality")
    pass_check("README has project framing and quality framing")

    print("PASS contract audit complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
