from __future__ import annotations

from pathlib import Path

from ancp.native import TSC_RE, parse_pyright_json, parse_rust_json_lines, parse_text_lines


def test_typescript_text_diagnostic_parse(tmp_path: Path) -> None:
    source = tmp_path / "src" / "app.ts"
    source.parent.mkdir()
    source.write_text("renderUser(user)\n", encoding="utf-8")
    text = f"{source}(1,1): error TS2304: Cannot find name 'renderUser'."
    diagnostics = parse_text_lines(text, TSC_RE, tmp_path, "typescript", "typescript", "diag-ts")
    assert len(diagnostics) == 1
    assert diagnostics[0]["canonicalCode"] == "ancp.diag.symbol.unresolved"
    assert diagnostics[0]["nativeCode"] == "TS2304"
    assert diagnostics[0]["fingerprint"].startswith("sha256:")


def test_pyright_json_parse(tmp_path: Path) -> None:
    source = tmp_path / "main.py"
    source.write_text("import rich\n", encoding="utf-8")
    payload = """
    {
      "generalDiagnostics": [
        {
          "file": "main.py",
          "severity": "error",
          "message": "Import \\"rich\\" could not be resolved.",
          "rule": "reportMissingImports",
          "range": {
            "start": {"line": 0, "character": 7},
            "end": {"line": 0, "character": 11}
          }
        }
      ]
    }
    """
    diagnostics = parse_pyright_json(payload, tmp_path)
    assert len(diagnostics) == 1
    assert diagnostics[0]["canonicalCode"] == "ancp.diag.import.missing"
    assert diagnostics[0]["kind"] == "import"


def test_rust_json_parse(tmp_path: Path) -> None:
    source = tmp_path / "src" / "main.rs"
    source.parent.mkdir()
    source.write_text("fn main(){ println!(\"{}\", count); }\n", encoding="utf-8")
    line = """
    {"reason":"compiler-message","message":{"$message_type":"diagnostic","message":"cannot find value `count` in this scope","code":{"code":"E0425","explanation":null},"level":"error","spans":[{"file_name":"src/main.rs","byte_start":0,"byte_end":1,"line_start":1,"line_end":1,"column_start":25,"column_end":30,"is_primary":true}],"children":[]}}
    """
    diagnostics = parse_rust_json_lines(line, tmp_path)
    assert len(diagnostics) == 1
    assert diagnostics[0]["nativeCode"] == "E0425"
    assert diagnostics[0]["canonicalCode"] == "ancp.diag.symbol.unresolved"

