from __future__ import annotations

from pathlib import Path

from ancp.cli import aggregate_status, capabilities_document, graph_document, resolve_workspace, skills_document, verify_document
from ancp.adapters import get_adapter
from ancp.schema import validate_document


def test_capabilities_document_validates(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    document = capabilities_document(tmp_path)
    assert document["documentKind"] == "manifest.capabilities"
    assert validate_document(document) == []


def test_graph_document_validates(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    document = graph_document(tmp_path)
    assert document["documentKind"] == "graph.code"
    assert validate_document(document) == []


def test_skills_document_validates() -> None:
    document = skills_document()
    assert document["documentKind"] == "result.skills"
    assert validate_document(document) == []


def test_explicit_workspace_does_not_climb_to_parent(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = parent / "child"
    (parent / ".git").mkdir(parents=True)
    child.mkdir()
    assert resolve_workspace(str(child)) == child.resolve()


def test_aggregate_status_tracks_partial_tool_failures() -> None:
    documents = [{"status": "passed"}, {"status": "tool_failed"}]
    assert aggregate_status(documents) == "partial"


def test_verify_document_does_not_pass_missing_tool(tmp_path: Path) -> None:
    (tmp_path / "main.scala").write_text("object Main { def main(args: Array[String]) = println(\"x\") }\n", encoding="utf-8")
    document = verify_document(tmp_path, "scala", timeout=1)
    if document["data"]["checkDocuments"][0]["status"] == "tool_failed":
        assert document["status"] == "tool_failed"


def test_internal_json_toml_yaml_adapters_validate(tmp_path: Path) -> None:
    cases = [
        ("json", "broken.json", '{"items": [1, 2,]}'),
        ("toml", "broken.toml", "[project\nname = 'broken'\n"),
        ("yaml", "broken.yaml", "items:\n  - one\n    nested: bad\n"),
    ]
    for language, filename, content in cases:
        root = tmp_path / language
        root.mkdir()
        (root / filename).write_text(content, encoding="utf-8")
        adapter = get_adapter(language)
        assert adapter is not None
        document = adapter.check(root)
        assert document["status"] == "failed"
        assert document["diagnostics"]
        assert validate_document(document) == []
