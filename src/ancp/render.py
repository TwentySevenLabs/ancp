"""Render ANCP JSON into agent-facing text formats."""

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


def _short_location_label(diagnostic: dict[str, Any]) -> str:
    loc = diagnostic.get("primaryLocation", {})
    artifact = loc.get("artifact", {})
    uri = artifact.get("uri", "")
    rng = loc.get("range", {})
    start = rng.get("start", {})
    line = int(start.get("line", 0)) + 1
    if uri.startswith("file://"):
        uri = uri.replace("file:///", "").replace("file://", "")
    if uri:
        text = uri.replace("\\", "/")
        parts = [part for part in text.split("/") if part]
        short = "/".join(parts[-2:]) if len(parts) >= 2 else parts[0] if parts else "<unknown>"
    else:
        short = "<unknown>"
    return f"{short}:{line}"


def _repair_label(diagnostic: dict[str, Any]) -> str:
    hints = diagnostic.get("repairHints") or []
    if not hints:
        return "No safe repair hint emitted."
    best = sorted(hints, key=lambda item: item.get("confidence", 0), reverse=True)[0]
    confidence = best.get("confidence", 0)
    return f"{best.get('title', best.get('repairId'))} ({best.get('safetyLevel')}, confidence {confidence:.2f})"


def _repair_title(diagnostic: dict[str, Any]) -> str:
    hints = diagnostic.get("repairHints") or []
    if not hints:
        return "none"
    best = sorted(hints, key=lambda item: item.get("confidence", 0), reverse=True)[0]
    title = best.get("title") or best.get("repairId") or "repair"
    safety = best.get("safetyLevel") or "unknown"
    confidence = best.get("confidence")
    suffix = f" [{safety}]"
    if isinstance(confidence, int | float):
        suffix += f" c={confidence:.2f}"
    return title + suffix


def _repair_ultra(diagnostic: dict[str, Any]) -> str:
    hints = diagnostic.get("repairHints") or []
    if not hints:
        return ""
    best = sorted(hints, key=lambda item: item.get("confidence", 0), reverse=True)[0]
    title = best.get("title") or best.get("repairId") or ""
    replacements = {
        "Fix Python syntax": "fix syntax",
        "Fix invalid syntax": "fix syntax",
        "Import missing symbol": "import symbol",
        "Add or fix the missing dependency/import path": "fix import",
    }
    return replacements.get(title, str(title).strip().lower())[:60]


def _short_code(diagnostic: dict[str, Any]) -> str:
    native = diagnostic.get("nativeCode")
    canonical = str(diagnostic.get("canonicalCode", "diag")).removeprefix("ancp.diag.")
    kind = str(diagnostic.get("kind", "")).strip()
    if native and len(str(native)) <= 16 and str(native) not in {"ArgumentError"}:
        return str(native)
    if canonical:
        return canonical
    return kind or "diag"


def _ultra_message(diagnostic: dict[str, Any]) -> str:
    message = " ".join(str(diagnostic.get("message", "")).split())
    native = diagnostic.get("nativeCode")
    if native and message.lower().startswith(str(native).lower() + ":"):
        message = message[len(str(native)) + 1 :].strip()
    if diagnostic.get("kind") == "import":
        message = message.removeprefix("package ")
        if " is not in std " in message:
            message = message.split(" is not in std ", 1)[0] + " not found"
        message = message.replace("Package ", "").replace(" not found in current path.", " not found")
    return message[:160]


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


def estimate_tokens(text: str) -> int:
    """Return a conservative dependency-free token estimate for telemetry."""

    if not text:
        return 0
    return max(1, (len(text.encode("utf-8", errors="replace")) + 3) // 4)


def truncate_to_budget(lines: list[str], token_budget: int | None) -> list[str]:
    if token_budget is None or token_budget <= 0:
        return lines
    output: list[str] = []
    used = 0
    for line in lines:
        cost = estimate_tokens(line + "\n")
        if output and used + cost > token_budget:
            output.append(f"truncated remaining output to stay under {token_budget} tokens")
            break
        output.append(line)
        used += cost
    return output


def render_text(
    document: dict[str, Any],
    max_diagnostics: int = 12,
    token_budget: int | None = None,
    include_guidance: bool = True,
) -> str:
    """Render a minimal raw-text ANCP briefing for agents.

    This intentionally avoids Markdown headings, bullets, tables, and fences.
    It is optimized for terminals and agent context, not human documentation.
    """

    kind = document.get("documentKind", "unknown")
    status = document.get("status", "unknown")
    diagnostics = document.get("diagnostics") or []
    data = document.get("data") or {}
    run = document.get("run") or {}
    raw = data.get("rawOutput") or {}
    metrics = data.get("signalMetrics") or {}
    lines: list[str] = [f"ANCP {kind} {status} diagnostics={len(diagnostics)}"]

    if run.get("exitCode") is not None:
        lines.append(f"exit={run.get('exitCode')} durationMs={run.get('durationMs', 0)}")
    if raw.get("combinedPath"):
        lines.append(f"raw={raw['combinedPath']}")
    if metrics:
        native = metrics.get("estimatedNativeTokens")
        compact = metrics.get("estimatedCompactTokens")
        savings = metrics.get("estimatedSavingsPercent")
        if native is not None and compact is not None and savings is not None:
            lines.append(f"tokens native~{native} compact~{compact} saved~{savings}%")

    if not diagnostics:
        reason = data.get("stderrSummary") or data.get("stdoutSummary")
        if reason:
            compact_reason = " ".join(str(reason).split())
            lines.append(f"tool_output={compact_reason[:500]}")
        return "\n".join(truncate_to_budget(lines, token_budget)).rstrip() + "\n"

    severity_counts = Counter(diag.get("severity", "unknown") for diag in diagnostics)
    kind_counts = Counter(diag.get("kind", "unknown") for diag in diagnostics)
    lines.append(
        "summary "
        + "severity="
        + ",".join(f"{key}:{value}" for key, value in severity_counts.most_common())
        + " kind="
        + ",".join(f"{key}:{value}" for key, value in kind_counts.most_common(6))
    )

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for diagnostic in diagnostics:
        grouped[_group_key(diagnostic)].append(diagnostic)

    lines.append(f"root_causes={len(grouped)}")
    for index, (key, group) in enumerate(sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True), start=1):
        canonical, native, kind_name = key
        example = group[0]
        native_part = f" native={native}" if native else ""
        message = " ".join(str(example.get("message", "")).split())[:240]
        lines.append(f"{index}. code={canonical}{native_part} kind={kind_name} count={len(group)}")
        lines.append(f"   at={_location_label(example)}")
        lines.append(f"   msg={message}")
        lines.append(f"   fix={_repair_title(example)}")

    shown = 0
    for diagnostic in diagnostics:
        if shown >= max_diagnostics:
            break
        if _group_key(diagnostic) in grouped and grouped[_group_key(diagnostic)][0] is diagnostic:
            continue
        message = " ".join(str(diagnostic.get("message", "")).split())[:180]
        lines.append(
            f"diag code={diagnostic.get('canonicalCode')} native={diagnostic.get('nativeCode', '')} "
            f"at={_location_label(diagnostic)} msg={message}"
        )
        shown += 1
    remaining = max(0, len(diagnostics) - len(grouped) - shown)
    if remaining:
        lines.append(f"more_diagnostics={remaining} see_json_or_raw")

    if include_guidance:
        lines.append("agent_next=fix root_causes first; rerun native command before claiming verified")
    return "\n".join(truncate_to_budget(lines, token_budget)).rstrip() + "\n"


def render_ultra(document: dict[str, Any], max_groups: int = 8, token_budget: int | None = 200) -> str:
    """Render the smallest useful agent-facing diagnostic output.

    Ultra output intentionally hides protocol metadata, raw paths, token stats,
    guidance, and document identity. Full detail remains in JSON/raw logs.
    """

    diagnostics = document.get("diagnostics") or []
    data = document.get("data") or {}
    if not diagnostics:
        reason = data.get("stderrSummary") or data.get("stdoutSummary")
        if reason:
            text = " ".join(str(reason).split())[:180]
            return truncate_text(f"tool_failed {text}\n", token_budget)
        status = document.get("status", "ok")
        return f"{status}\n"

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for diagnostic in diagnostics:
        grouped[_group_key(diagnostic)].append(diagnostic)

    lines: list[str] = []
    for _, group in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:max_groups]:
        diagnostic = group[0]
        count = f" x{len(group)}" if len(group) > 1 else ""
        location = _short_location_label(diagnostic)
        code = _short_code(diagnostic)
        message = _ultra_message(diagnostic)
        repair = _repair_ultra(diagnostic)
        line = f"{code} {location} {message}{count}".strip()
        if repair and repair not in line.lower():
            line += f" fix:{repair}"
        lines.append(line)
    if len(grouped) > max_groups:
        lines.append(f"+{len(grouped) - max_groups} more")
    return truncate_text("\n".join(lines).rstrip() + "\n", token_budget)


def truncate_text(text: str, token_budget: int | None) -> str:
    if token_budget is None or token_budget <= 0 or estimate_tokens(text) <= token_budget:
        return text
    byte_budget = max(16, token_budget * 4)
    encoded = text.encode("utf-8", errors="replace")[:byte_budget]
    return encoded.decode("utf-8", errors="ignore").rstrip() + "\n"
