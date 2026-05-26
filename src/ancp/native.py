"""Native diagnostic parsers shared by adapters."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from . import documents as doc


TSC_RE = re.compile(r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s+(?P<severity>error|warning)\s+(?P<code>TS\d+):\s+(?P<message>.+)$")
GCC_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s+(?P<severity>fatal error|error|warning|note):\s+(?P<message>.+)$")
DOTNET_RE = re.compile(r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s+(?P<severity>error|warning)\s+(?P<code>[A-Z]{1,4}\d{3,5}|[A-Z]{2}\d{4}):\s+(?P<message>.+?)(?:\s+\[.+\])?$")
JAVAC_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+):\s+(?P<severity>error|warning):\s+(?P<message>.+)$")
GO_FILE_RE = re.compile(r"(?P<file>[^:\s]+\.go):(?P<line>\d+):(?P<col>\d+):\s+(?P<message>.+)")
RUBY_RE = re.compile(r"(?P<file>.+?):(?P<line>\d+):\s+(?P<message>.+)")
PHP_RE = re.compile(r"(?:Parse error|Fatal error):\s+(?P<message>.+?)\s+in\s+(?P<file>.+?)\s+on line\s+(?P<line>\d+)", re.IGNORECASE)


def canonical_for_native(native_code: str | None, message: str, default: str = "ancp.diag.unknown") -> tuple[str, str, list[dict[str, Any]]]:
    text = f"{native_code or ''} {message}".lower()
    if any(token in text for token in ["not found in current path", "is not in std", "package does not exist", "cannot find module", "could not be resolved", "no such module", "no such file or directory"]):
        return "ancp.diag.import.missing", "import", [doc.repair_hint("ancp.repair.module.add_dependency", "Add or fix the missing dependency/import path", 0.5)]
    if any(token in text for token in ["cannot find name", "cannot find value", "undefined", "undeclared", "unresolved reference", "not found", "does not exist in the current context"]):
        return "ancp.diag.symbol.unresolved", "symbol", [doc.repair_hint("ancp.repair.symbol.import_missing", "Import or declare the missing symbol", 0.55)]
    if any(token in text for token in ["type mismatch", "mismatched types", "not assignable", "cannot convert", "incompatible types"]):
        return "ancp.diag.type.mismatch", "type", [doc.repair_hint("ancp.repair.type.convert_value", "Convert value or adjust type annotation", 0.45)]
    if any(token in text for token in ["unused", "never used"]):
        return "ancp.diag.symbol.unused", "symbol", [doc.repair_hint("ancp.repair.lint.apply_fix", "Remove or use the unused symbol", 0.7)]
    if any(token in text for token in ["syntax", "parse", "expected", "unexpected token", "missing ')'", "missing ']'", "missing '}'", "missing end"]):
        return "ancp.diag.syntax.invalid", "syntax", [doc.repair_hint("ancp.repair.syntax.insert_token", "Fix invalid syntax", 0.45)]
    if any(token in text for token in ["test", "assert", "failed"]):
        return "ancp.diag.test.assertion_failed", "test", [doc.repair_hint("ancp.repair.test.fix_subject", "Fix the code under test or the expectation", 0.35)]
    return default, "unknown", []


def parse_text_lines(
    text: str,
    regex: re.Pattern[str],
    root: pathlib.Path,
    language_id: str,
    source: str,
    diag_prefix: str,
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        match = regex.match(line.strip())
        if not match:
            continue
        groups = match.groupdict()
        path = pathlib.Path(groups["file"])
        if not path.is_absolute():
            path = (root / path).resolve()
        line_no = max(int(groups.get("line") or "1") - 1, 0)
        col_no = max(int(groups.get("col") or "1") - 1, 0)
        severity = "warning" if "warning" in (groups.get("severity") or "").lower() else "error"
        native_code = groups.get("code")
        message = groups["message"].strip()
        canonical, kind, hints = canonical_for_native(native_code, message)
        diagnostics.append(
            doc.diagnostic(
                f"{diag_prefix}-{index:04d}",
                canonical,
                native_code,
                severity,
                kind,
                message,
                doc.location(path, language_id, line_no, col_no, line_no, col_no + 1),
                source,
                hints,
                {"raw": line.strip()},
            )
        )
    return diagnostics


def parse_pyright_json(text: str, root: pathlib.Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    diagnostics: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("generalDiagnostics", []), start=1):
        file_path = pathlib.Path(item.get("file") or root)
        if not file_path.is_absolute():
            file_path = root / file_path
        rng = item.get("range", {})
        start = rng.get("start", {})
        end = rng.get("end", start)
        native_code = item.get("rule")
        message = item.get("message", "")
        canonical, kind, hints = canonical_for_native(native_code, message)
        diagnostics.append(
            doc.diagnostic(
                f"diag-pyright-{index:04d}",
                canonical,
                native_code,
                "warning" if item.get("severity") == "warning" else "error",
                kind,
                message,
                doc.location(
                    file_path,
                    "python",
                    int(start.get("line", 0)),
                    int(start.get("character", 0)),
                    int(end.get("line", start.get("line", 0))),
                    int(end.get("character", start.get("character", 0))),
                ),
                "pyright",
                hints,
                {"native": item},
            )
        )
    return diagnostics


def parse_ruff_json(text: str, root: pathlib.Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    diagnostics: list[dict[str, Any]] = []
    if not isinstance(payload, list):
        return diagnostics
    for index, item in enumerate(payload, start=1):
        filename = item.get("filename") or item.get("file") or "."
        file_path = pathlib.Path(filename)
        if not file_path.is_absolute():
            file_path = root / file_path
        loc = item.get("location") or {}
        end = item.get("end_location") or loc
        native_code = item.get("code")
        message = item.get("message", "")
        canonical, kind, hints = canonical_for_native(native_code, message, "ancp.diag.lint.rule_violation")
        if item.get("fix"):
            hints.append(doc.repair_hint("ancp.repair.lint.apply_fix", "Apply Ruff fix", 0.85))
        diagnostics.append(
            doc.diagnostic(
                f"diag-ruff-{index:04d}",
                canonical,
                native_code,
                "warning",
                "lint" if canonical == "ancp.diag.lint.rule_violation" else kind,
                message,
                doc.location(
                    file_path,
                    "python",
                    int(loc.get("row", 1)) - 1,
                    int(loc.get("column", 1)) - 1,
                    int(end.get("row", loc.get("row", 1))) - 1,
                    int(end.get("column", loc.get("column", 1))) - 1,
                ),
                "ruff",
                hints,
                {"native": item},
            )
        )
    return diagnostics


def parse_rust_json_lines(text: str, root: pathlib.Path) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    counter = 0
    for line in text.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = payload.get("message") if payload.get("reason") == "compiler-message" else payload
        if not isinstance(message, dict) or message.get("$message_type") != "diagnostic":
            continue
        level = message.get("level", "error")
        if level in {"note", "help"}:
            continue
        spans = [span for span in message.get("spans", []) if span.get("is_primary")]
        if not spans:
            spans = message.get("spans", [])
        span = spans[0] if spans else {}
        file_name = span.get("file_name") or "unknown.rs"
        file_path = pathlib.Path(file_name)
        if not file_path.is_absolute():
            file_path = root / file_path
        native_code = None
        if isinstance(message.get("code"), dict):
            native_code = message["code"].get("code")
        msg = message.get("message", "")
        canonical, kind, hints = canonical_for_native(native_code, msg)
        for child in message.get("children", []):
            if child.get("level") == "help":
                hints.append(doc.repair_hint("ancp.repair.lint.apply_fix", child.get("message", "Apply compiler suggestion"), 0.65))
        counter += 1
        diagnostics.append(
            doc.diagnostic(
                f"diag-rust-{counter:04d}",
                canonical,
                native_code,
                "warning" if level == "warning" else "error",
                kind,
                msg,
                doc.location(
                    file_path,
                    "rust",
                    int(span.get("line_start", 1)) - 1,
                    int(span.get("column_start", 1)) - 1,
                    int(span.get("line_end", span.get("line_start", 1))) - 1,
                    int(span.get("column_end", span.get("column_start", 1))) - 1,
                    unit="byte",
                ),
                "rustc",
                hints,
                {"native": message},
            )
        )
    return diagnostics


def parse_go_test_json(text: str, root: pathlib.Path) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    counter = 0
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        output = event.get("Output", "")
        match = GO_FILE_RE.search(output)
        if match:
            counter += 1
            file_path = root / match.group("file")
            message = match.group("message").strip()
            canonical, kind, hints = canonical_for_native(None, message)
            diagnostics.append(
                doc.diagnostic(
                    f"diag-go-{counter:04d}",
                    canonical,
                    None,
                    "error",
                    kind,
                    message,
                    doc.location(file_path, "go", int(match.group("line")) - 1, int(match.group("col")) - 1),
                    "go",
                    hints,
                    {"package": event.get("Package"), "raw": output.strip()},
                )
            )
        elif event.get("Action") == "fail" and event.get("Test"):
            counter += 1
            diagnostics.append(
                doc.diagnostic(
                    f"diag-go-test-{counter:04d}",
                    "ancp.diag.test.assertion_failed",
                    None,
                    "error",
                    "test",
                    f"Go test failed: {event.get('Test')}",
                    doc.location(root, "go", 0, 0),
                    "go test",
                    [doc.repair_hint("ancp.repair.test.fix_subject", "Fix failing Go test", 0.35)],
                    {"native": event},
                )
            )
    return diagnostics


def parse_go_text(text: str, root: pathlib.Path) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    counter = 0
    for line in text.splitlines():
        match = GO_FILE_RE.search(line)
        if not match:
            continue
        counter += 1
        file_path = root / match.group("file")
        message = match.group("message").strip()
        canonical, kind, hints = canonical_for_native(None, message)
        diagnostics.append(
            doc.diagnostic(
                f"diag-go-text-{counter:04d}",
                canonical,
                None,
                "error",
                kind,
                message,
                doc.location(file_path, "go", int(match.group("line")) - 1, int(match.group("col")) - 1),
                "go",
                hints,
                {"raw": line.strip()},
            )
        )
    return diagnostics
