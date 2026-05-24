from __future__ import annotations

from ancp.render import render_markdown


def test_render_groups_and_compresses_diagnostics() -> None:
    document = {
        "documentKind": "result.check",
        "status": "failed",
        "producer": {"name": "test", "version": "1"},
        "workspace": {"rootUri": "file:///repo"},
        "toolchain": [{"name": "tsc", "role": "typechecker"}],
        "diagnostics": [
            {
                "id": "d1",
                "canonicalCode": "ancp.diag.symbol.unresolved",
                "nativeCode": "TS2304",
                "severity": "error",
                "kind": "symbol",
                "message": "Cannot find name 'x'.",
                "primaryLocation": {
                    "artifact": {"uri": "file:///repo/app.ts"},
                    "range": {"start": {"line": 0, "character": 1}},
                },
                "repairHints": [
                    {
                        "repairId": "ancp.repair.symbol.import_missing",
                        "title": "Import missing symbol",
                        "confidence": 0.8,
                        "safetyLevel": "review_required",
                    }
                ],
            },
            {
                "id": "d2",
                "canonicalCode": "ancp.diag.symbol.unresolved",
                "nativeCode": "TS2304",
                "severity": "error",
                "kind": "symbol",
                "message": "Cannot find name 'y'.",
                "primaryLocation": {
                    "artifact": {"uri": "file:///repo/other.ts"},
                    "range": {"start": {"line": 2, "character": 3}},
                },
                "repairHints": [],
            },
        ],
    }
    markdown = render_markdown(document)
    assert "Root-Cause Groups" in markdown
    assert "2 occurrence" in markdown
    assert "Import missing symbol" in markdown
    assert "Agent Guidance" in markdown

