from __future__ import annotations

import json
from pathlib import Path

from ancp.schema import validate_document


ROOT = Path(__file__).resolve().parents[1]


def test_all_examples_validate() -> None:
    paths = sorted((ROOT / "examples").rglob("*.json"))
    assert paths
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert validate_document(document) == [], path


def test_manifest_document_validates() -> None:
    from ancp.cli import manifest_document

    document = manifest_document()
    assert document["documentKind"] == "manifest.adapter"
    assert validate_document(document) == []

