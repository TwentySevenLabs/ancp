"""Helpers for constructing ANCP documents."""

from __future__ import annotations

import pathlib
from typing import Any

from .constants import ANCP_VERSION, SCHEMA_URI
from .util import path_to_uri, sha256_file, utc_now


def producer(name: str = "ancp-reference-cli", version: str = "1.0.0") -> dict[str, Any]:
    return {
        "name": name,
        "version": version,
        "homepage": "https://agent-native-compiler-protocol.org",
        "sourceUri": "https://github.com/agent-native-compiler-protocol/ancp",
        "license": "Apache-2.0",
    }


def envelope(kind: str, producer_name: str = "ancp-reference-cli") -> dict[str, Any]:
    return {
        "ancpVersion": ANCP_VERSION,
        "documentKind": kind,
        "producer": producer(producer_name),
        "createdAt": utc_now(),
        "schemaUri": SCHEMA_URI,
    }


def workspace_object(root: pathlib.Path) -> dict[str, Any]:
    return {
        "rootUri": path_to_uri(root),
        "workspaceId": (sha256_file(root / ".git" / "HEAD") or f"path:{root.name}") if (root / ".git").exists() else f"path:{root.name}",
        "name": root.name,
        "vcs": detect_vcs(root),
        "packageManager": detect_package_manager(root),
    }


def detect_vcs(root: pathlib.Path) -> dict[str, Any]:
    if (root / ".git").exists():
        return {"kind": "git", "rootUri": path_to_uri(root), "dirty": False}
    return {"kind": "unknown"}


def detect_package_manager(root: pathlib.Path) -> str:
    markers = [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
        ("uv.lock", "uv"),
        ("poetry.lock", "poetry"),
        ("requirements.txt", "pip"),
        ("Cargo.lock", "cargo"),
        ("go.sum", "go"),
        ("pom.xml", "maven"),
        ("build.gradle", "gradle"),
        ("settings.gradle", "gradle"),
        ("pubspec.lock", "dart"),
        ("Project.toml", "julia"),
    ]
    for marker, name in markers:
        if (root / marker).exists():
            return name
    return "unknown"


def artifact(path: pathlib.Path, language_id: str | None = None, role: str = "source") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "uri": path_to_uri(path),
        "role": role,
    }
    if language_id:
        payload["languageId"] = language_id
    digest = sha256_file(path)
    if digest:
        payload["digest"] = digest
    return payload


def range_object(
    start_line: int,
    start_character: int,
    end_line: int | None = None,
    end_character: int | None = None,
    unit: str = "utf16",
) -> dict[str, Any]:
    end_line = start_line if end_line is None else end_line
    end_character = start_character if end_character is None else end_character
    return {
        "unit": unit,
        "start": {"line": max(start_line, 0), "character": max(start_character, 0)},
        "end": {"line": max(end_line, 0), "character": max(end_character, 0)},
    }


def location(
    path: pathlib.Path,
    language_id: str,
    start_line: int,
    start_character: int,
    end_line: int | None = None,
    end_character: int | None = None,
    unit: str = "utf16",
    selectors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = {
        "artifact": artifact(path, language_id),
        "range": range_object(start_line, start_character, end_line, end_character, unit),
    }
    if selectors:
        payload["selectors"] = selectors
    return payload


def diagnostic(
    diag_id: str,
    canonical_code: str,
    native_code: str | None,
    severity: str,
    kind: str,
    message: str,
    primary_location: dict[str, Any],
    source: str,
    repair_hints: list[dict[str, Any]] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": diag_id,
        "canonicalCode": canonical_code,
        "severity": severity,
        "kind": kind,
        "message": message,
        "source": source,
        "primaryLocation": primary_location,
        "repairHints": repair_hints or [],
    }
    if native_code:
        payload["nativeCode"] = native_code
    if data:
        payload["data"] = data
    payload["fingerprint"] = fingerprint(payload)
    return payload


def repair_hint(repair_id: str, title: str, confidence: float, safety_level: str = "review_required") -> dict[str, Any]:
    return {
        "repairId": repair_id,
        "title": title,
        "confidence": max(0.0, min(confidence, 1.0)),
        "safetyLevel": safety_level,
    }


def fingerprint(diag: dict[str, Any]) -> str:
    import hashlib
    import json

    loc = diag.get("primaryLocation", {})
    art = loc.get("artifact", {})
    selectors = loc.get("selectors") or []
    anchor = ""
    for selector in selectors:
        if selector.get("kind") in {"text", "context", "symbol"}:
            anchor = selector.get("value", "")
            break
    if not anchor:
        anchor = diag.get("message", "")[:120]
    parts = {
        "canonicalCode": diag.get("canonicalCode"),
        "nativeCode": diag.get("nativeCode"),
        "artifact": art.get("uri"),
        "anchor": anchor,
    }
    return "sha256:" + hashlib.sha256(json.dumps(parts, sort_keys=True).encode("utf-8")).hexdigest()

