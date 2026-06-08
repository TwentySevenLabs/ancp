from __future__ import annotations

import json
import sys
from pathlib import Path

from ancp.cli import aggregate_status, capabilities_document, graph_document, main, resolve_workspace, skills_document, verify_document
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


def test_javascript_adapter_accepts_node_check_fallback(tmp_path: Path) -> None:
    (tmp_path / "broken.js").write_text("function broken( {\n", encoding="utf-8")
    adapter = get_adapter("javascript")
    assert adapter is not None
    document = adapter.check(tmp_path)
    if document["status"] == "failed":
        assert document["diagnostics"]
        assert document["diagnostics"][0]["canonicalCode"] == "ancp.diag.syntax.invalid"
    else:
        assert document["status"] == "tool_failed"
    assert validate_document(document) == []


def test_raw_command_reads_recorded_native_log(tmp_path: Path, capsys) -> None:
    raw_log = tmp_path / "native.log"
    raw_log.write_text("native error text\n", encoding="utf-8")
    check = tmp_path / "last-check.json"
    check.write_text(
        json.dumps({"documentKind": "result.check", "data": {"rawOutput": {"combinedPath": str(raw_log)}}}),
        encoding="utf-8",
    )
    assert main(["raw", "--from", str(check)]) == 0
    assert capsys.readouterr().out == "native error text\n"


def test_render_ultra_command_does_not_add_extra_blank_line(tmp_path: Path, capsys) -> None:
    check = tmp_path / "last-check.json"
    check.write_text(
        json.dumps(
            {
                "documentKind": "result.check",
                "status": "failed",
                "diagnostics": [
                    {
                        "id": "d1",
                        "canonicalCode": "ancp.diag.syntax.invalid",
                        "nativeCode": "SyntaxError",
                        "severity": "error",
                        "kind": "syntax",
                        "message": "SyntaxError: expected ':'",
                        "primaryLocation": {
                            "artifact": {"uri": "file:///repo/src/app.py"},
                            "range": {"start": {"line": 14, "character": 0}},
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert main(["render", "--from", str(check), "--format", "ultra"]) == 0
    assert capsys.readouterr().out == "SyntaxError src/app.py:15 expected ':'\n"


def test_off_command_runs_native_command_without_ancp(capsys) -> None:
    assert main(["off", "--", sys.executable, "-c", "print('native')"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "native\n"
    assert captured.err == ""
