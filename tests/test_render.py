from __future__ import annotations

from ancp.render import render_markdown, render_text, render_ultra


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


def test_render_text_is_minimal_and_budgeted() -> None:
    document = {
        "documentKind": "result.check",
        "status": "failed",
        "run": {"exitCode": 1, "durationMs": 9},
        "data": {
            "rawOutput": {"combinedPath": ".ancp/runs/abc/native.log"},
            "signalMetrics": {
                "estimatedNativeTokens": 1000,
                "estimatedCompactTokens": 80,
                "estimatedSavingsPercent": 92,
            },
        },
        "diagnostics": [
            {
                "id": "d1",
                "canonicalCode": "ancp.diag.syntax.invalid",
                "nativeCode": "SyntaxError",
                "severity": "error",
                "kind": "syntax",
                "message": "expected ':'",
                "primaryLocation": {
                    "artifact": {"uri": "file:///repo/app.py"},
                    "range": {"start": {"line": 4, "character": 8}},
                },
                "repairHints": [
                    {
                        "repairId": "ancp.repair.syntax.insert_token",
                        "title": "Fix Python syntax",
                        "confidence": 0.4,
                        "safetyLevel": "review_required",
                    }
                ],
            }
        ],
    }
    text = render_text(document, token_budget=120)
    assert "# " not in text
    assert "```" not in text
    assert "ANCP result.check failed diagnostics=1" in text
    assert "tokens native~1000 compact~80 saved~92%" in text
    assert "code=ancp.diag.syntax.invalid native=SyntaxError" in text
    assert "fix=Fix Python syntax [review_required] c=0.40" in text


def test_render_ultra_hides_protocol_metadata() -> None:
    document = {
        "documentKind": "result.check",
        "status": "failed",
        "data": {
            "rawOutput": {"combinedPath": ".ancp/runs/abc/native.log"},
            "signalMetrics": {"estimatedNativeTokens": 1000, "estimatedCompactTokens": 80, "estimatedSavingsPercent": 92},
        },
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
                "repairHints": [
                    {
                        "repairId": "ancp.repair.syntax.insert_token",
                        "title": "Fix Python syntax",
                        "confidence": 0.4,
                        "safetyLevel": "review_required",
                    }
                ],
            }
        ],
    }
    ultra = render_ultra(document)
    assert ultra == "SyntaxError src/app.py:15 expected ':' fix:fix syntax\n"
    assert "ANCP" not in ultra
    assert "result.check" not in ultra
    assert "raw=" not in ultra
    assert "tokens" not in ultra


def test_render_ultra_shortens_missing_import_noise() -> None:
    document = {
        "documentKind": "result.check",
        "status": "failed",
        "diagnostics": [
            {
                "id": "d1",
                "canonicalCode": "ancp.diag.import.missing",
                "severity": "error",
                "kind": "import",
                "message": "package not/a/real/package is not in std (C:\\Program Files\\Go\\src\\not\\a\\real\\package)",
                "primaryLocation": {
                    "artifact": {"uri": "file:///repo/go/main.go"},
                    "range": {"start": {"line": 3, "character": 7}},
                },
                "repairHints": [
                    {
                        "repairId": "ancp.repair.module.add_dependency",
                        "title": "Add or fix the missing dependency/import path",
                        "confidence": 0.5,
                        "safetyLevel": "review_required",
                    }
                ],
            }
        ],
    }
    ultra = render_ultra(document)
    assert ultra == "import.missing go/main.go:4 not/a/real/package not found fix:fix import\n"
    assert "Program Files" not in ultra
