"""Render ANCP JSON into compact agent-facing Markdown."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def _location_label(diagnostic: dict[str, Any]) -> str:
    loc = diagnostic.get("primaryLocation", {})
    artifact = loc.get("artifact", {})
    uri = artifact.get("uri", "<unknown>")
    rng = loc.get("range", {})
    start = rng.get("start", {})
    line = int(start.get("line", 0)) + 1
    char = int(start.get("character", 0)) + 1
    if uri.startswith("file://"):
        uri = uri.replace("file:///", "").replace("file://", "")
    return f"{uri}:{line}:{char}"


def _repair_label(diagnostic: dict[str, Any]) -> str:
    hints = diagnostic.get("repairHints") or []
    if not hints:
        return "No safe repair hint emitted."
    best = sorted(hints, key=lambda item: item.get("confidence", 0), reverse=True)[0]
    confidence = best.get("confidence", 0)
    return f"{best.get('title', best.get('repairId'))} ({best.get('safetyLevel')}, confidence {confidence:.2f})"


def _group_key(diagnostic: dict[str, Any]) -> tuple[str, str, str]:
    return (
        diagnostic.get("canonicalCode", "ancp.diag.unknown"),
        diagnostic.get("nativeCode", ""),
        diagnostic.get("kind", "unknown"),
    )


def render_markdown(document: dict[str, Any], max_diagnostics: int = 40) -> str:
    """Render a compact Markdown briefing for agents."""

    kind = document.get("documentKind", "unknown")
    status = document.get("status", "unknown")
    diagnostics = document.get("diagnostics") or []
    title = f"ANCP {kind} - {status}"
    lines = [f"# {title}", ""]

    workspace = document.get("workspace", {})
    if workspace.get("rootUri"):
        lines.append(f"- Workspace: `{workspace['rootUri']}`")
    if document.get("producer", {}).get("name"):
        producer = document["producer"]
        lines.append(f"- Producer: `{producer.get('name')} {producer.get('version', '')}`".rstrip())
    toolchain = document.get("toolchain") or []
    if toolchain:
        tools = ", ".join(f"{tool.get('name')}:{tool.get('role')}" for tool in toolchain)
        lines.append(f"- Tools: {tools}")
    lines.append(f"- Diagnostics: {len(diagnostics)}")
    lines.append("")

    if not diagnostics:
        data = document.get("data") or {}
        reason = data.get("reason") or data.get("stderrSummary") or data.get("stdoutSummary")
        if reason:
            lines.extend(["## Tool Result", "", str(reason).strip(), ""])
        else:
            lines.extend(["No diagnostics were emitted.", ""])
        return "\n".join(lines).rstrip() + "\n"

    severity_counts = Counter(diag.get("severity", "unknown") for diag in diagnostics)
    kind_counts = Counter(diag.get("kind", "unknown") for diag in diagnostics)
    code_counts = Counter(diag.get("canonicalCode", "ancp.diag.unknown") for diag in diagnostics)

    lines.extend(
        [
            "## Signal Summary",
            "",
            "- Severity: " + ", ".join(f"{key}={value}" for key, value in severity_counts.most_common()),
            "- Kinds: " + ", ".join(f"{key}={value}" for key, value in kind_counts.most_common(8)),
            "- Top codes: " + ", ".join(f"`{key}`={value}" for key, value in code_counts.most_common(8)),
            "",
        ]
    )

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for diagnostic in diagnostics:
        grouped[_group_key(diagnostic)].append(diagnostic)

    lines.extend(["## Root-Cause Groups", ""])
    for index, (key, group) in enumerate(sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True), start=1):
        canonical, native, kind_name = key
        example = group[0]
        native_text = f" / `{native}`" if native else ""
        lines.append(f"{index}. `{canonical}`{native_text} ({kind_name}) - {len(group)} occurrence(s)")
        lines.append(f"   - Example: {_location_label(example)}")
        lines.append(f"   - Message: {example.get('message', '').strip()[:300]}")
        lines.append(f"   - Best hint: {_repair_label(example)}")
    lines.append("")

    lines.extend(["## High-Signal Diagnostics", ""])
    for diagnostic in diagnostics[:max_diagnostics]:
        native = f" `{diagnostic.get('nativeCode')}`" if diagnostic.get("nativeCode") else ""
        lines.append(f"- `{diagnostic.get('severity')}` `{diagnostic.get('canonicalCode')}`{native}")
        lines.append(f"  - Where: {_location_label(diagnostic)}")
        lines.append(f"  - Message: {diagnostic.get('message', '').strip()[:500]}")
        lines.append(f"  - Repair: {_repair_label(diagnostic)}")
    if len(diagnostics) > max_diagnostics:
        lines.append(f"- Truncated {len(diagnostics) - max_diagnostics} additional diagnostics. Use ANCP JSON for full detail.")
    lines.append("")

    lines.extend(
        [
            "## Agent Guidance",
            "",
            "1. Fix root-cause groups before individual repeated symptoms.",
            "2. Prefer diagnostics with native codes and precise locations.",
            "3. Apply only repair plans whose safety level matches the allowed policy.",
            "4. Re-run the native compiler or `ancp verify` before claiming the fix is verified.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"

