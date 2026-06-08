"""ANCP reference command-line interface."""

from __future__ import annotations

import argparse
import json
import pathlib
import os
import subprocess
import sys
from typing import Any

from . import __version__
from .adapters import ADAPTERS, get_adapter, matching_adapters
from .documents import envelope, producer, workspace_object
from .install import disable as disable_ancp
from .install import enable as enable_ancp
from .install import status as install_status
from .install import uninstall as uninstall_ancp
from .install import write_shims
from .proxy import compile_main
from .render import render_markdown, render_text, render_ultra
from .schema import load_schema, validate_document, validate_path
from .shim import executable_names
from .util import find_executable, find_workspace, read_json, write_json_stdout


def resolve_workspace(value: str | None) -> pathlib.Path:
    if value:
        return pathlib.Path(value).resolve()
    return find_workspace(pathlib.Path.cwd())


def manifest_document() -> dict[str, Any]:
    doc = envelope("manifest.adapter")
    doc.update(
        {
            "profiles": ["core", "explain", "repair-plan", "verify", "graph", "effects", "skills", "export"],
            "operations": [
                {"name": "manifest", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "capabilities", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "check", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "compile", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "explain", "profile": "explain", "supported": True, "stability": "stable"},
                {"name": "repair --plan", "profile": "repair-plan", "supported": True, "stability": "stable"},
                {"name": "verify", "profile": "verify", "supported": True, "stability": "stable"},
                {"name": "graph", "profile": "graph", "supported": True, "stability": "stable"},
                {"name": "skills", "profile": "skills", "supported": True, "stability": "stable"},
                {"name": "render", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "raw", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "off", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "enable", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "disable", "profile": "core", "supported": True, "stability": "stable"},
                {"name": "export sarif", "profile": "export", "supported": True, "stability": "experimental"},
            ],
            "languages": [adapter.language_entry() for adapter in ADAPTERS],
            "data": {
                "integrationModes": [
                    "reference-cli",
                    "compiler-proxy",
                    "native-json-tool",
                    "language-server-input",
                ],
                "compilerProxyShims": [
                    "ancp-tsc",
                    "ancp-eslint",
                    "ancp-pyright",
                    "ancp-ruff",
                    "ancp-python",
                    "ancp-cargo",
                    "ancp-rustc",
                    "ancp-go",
                    "ancp-gcc",
                    "ancp-clang",
                    "ancp-javac",
                    "ancp-kotlinc",
                    "ancp-dotnet",
                    "ancp-swift",
                    "ancp-zig",
                    "ancp-ruby",
                    "ancp-php",
                    "ancp-dart",
                    "ancp-scalac",
                    "ancp-julia",
                    "ancp-bash",
                    "ancp-pwsh",
                    "ancp-lua",
                    "ancp-perl",
                    "ancp-rscript",
                    "ancp-ghc",
                    "ancp-ocamlc",
                    "ancp-erlc",
                    "ancp-elixirc",
                    "ancp-clj-kondo",
                    "ancp-nix-instantiate",
                    "ancp-terraform",
                    "ancp-hadolint",
                    "ancp-sqlfluff",
                ],
            },
        }
    )
    return doc


def capabilities_document(root: pathlib.Path) -> dict[str, Any]:
    matches = matching_adapters(root)
    doc = envelope("manifest.capabilities")
    doc.update(
        {
            "workspace": workspace_object(root),
            "profiles": ["core", "explain", "repair-plan", "verify", "graph", "effects", "skills", "export"],
            "operations": [
                {
                    "name": "check",
                    "profile": "core",
                    "supported": True,
                    "stability": "stable",
                    "effects": [
                        {
                            "kind": "process.spawn",
                            "scope": "workspace",
                            "reason": "Runs native compiler/checker tools when available.",
                            "safetyLevel": "review_required",
                            "evidence": "manifest",
                        }
                    ],
                },
                {"name": "compile", "profile": "core", "supported": True, "stability": "stable"},
            ],
            "languages": [adapter.language_entry() for adapter in matches],
            "toolchain": [entry for adapter in matches for entry in adapter.toolchain_entries()],
            "data": {
                "matchedAdapters": [adapter.key for adapter in matches],
                "missingTools": {
                    adapter.key: [tool.command[0] for tool in adapter.tools if not __import__("shutil").which(tool.command[0])]
                    for adapter in matches
                },
            },
        }
    )
    return doc


def aggregate_status(documents: list[dict[str, Any]]) -> str:
    """Return a conservative status for a set of ANCP result documents."""
    statuses = [str(document.get("status", "protocol_error")) for document in documents]
    if not statuses:
        return "passed"
    if any(status == "failed" for status in statuses):
        return "failed"
    problem_statuses = {"tool_failed", "protocol_error"}
    if any(status in problem_statuses for status in statuses):
        if any(status == "passed" for status in statuses) or any(status == "partial" for status in statuses):
            return "partial"
        if any(status == "protocol_error" for status in statuses):
            return "protocol_error"
        return "tool_failed"
    if any(status == "partial" for status in statuses):
        return "partial"
    return "passed"


def status_exit_code(status: str) -> int:
    if status == "passed":
        return 0
    if status == "failed":
        return 1
    return 2


def check_command(args: argparse.Namespace) -> int:
    root = resolve_workspace(args.workspace)
    if args.language:
        adapter = get_adapter(args.language)
        if not adapter:
            print(f"Unknown language/adapter: {args.language}", file=sys.stderr)
            return 3
        documents = [adapter.check(root, timeout=args.timeout)]
    else:
        documents = [adapter.check(root, timeout=args.timeout) for adapter in matching_adapters(root)]

    if len(documents) == 1:
        write_json_stdout(documents[0])
    else:
        combined = envelope("result.check")
        diagnostics = [diag for document in documents for diag in document.get("diagnostics", [])]
        combined_status = "failed" if diagnostics else aggregate_status(documents)
        combined.update(
            {
                "status": combined_status,
                "workspace": workspace_object(root),
                "run": {
                    "runId": "combined-check",
                    "command": ["ancp", "check"],
                    "workingDirectory": str(root),
                    "startedAt": combined["createdAt"],
                    "endedAt": combined["createdAt"],
                    "durationMs": sum(document.get("run", {}).get("durationMs", 0) for document in documents),
                },
                "toolchain": [entry for document in documents for entry in document.get("toolchain", [])],
                "diagnostics": diagnostics,
                "data": {
                    "subdocuments": documents,
                    "subdocumentStatuses": [document.get("status", "protocol_error") for document in documents],
                },
            }
        )
        write_json_stdout(combined)
    return status_exit_code("failed" if any(document.get("diagnostics") for document in documents) else aggregate_status(documents))


def explain_document(query: str) -> dict[str, Any]:
    mapping = {
        "ancp.diag.symbol.unresolved": {
            "title": "Unresolved symbol",
            "summary": "A reference cannot be resolved in the current scope, module, package, or build context.",
            "repairs": ["ancp.repair.symbol.import_missing", "ancp.repair.symbol.declare_missing", "ancp.repair.symbol.rename_reference"],
        },
        "ancp.diag.import.missing": {
            "title": "Missing import or module",
            "summary": "A module, package, include, namespace, crate, assembly, or dependency path is unavailable.",
            "repairs": ["ancp.repair.module.add_dependency", "ancp.repair.config.adjust_option"],
        },
        "ancp.diag.type.mismatch": {
            "title": "Type mismatch",
            "summary": "The actual value type does not satisfy the expected type, signature, or generic bound.",
            "repairs": ["ancp.repair.type.adjust_annotation", "ancp.repair.type.convert_value"],
        },
    }
    item = mapping.get(query, {"title": query, "summary": "No detailed explanation is registered for this code yet.", "repairs": ["ancp.repair.manual"]})
    document = envelope("result.explain")
    document["explanation"] = {
        "query": query,
        "title": item["title"],
        "summary": item["summary"],
        "appliesTo": [adapter.language_id for adapter in ADAPTERS],
        "commonCauses": [
            "The native compiler/checker cannot see a dependency or symbol.",
            "The build context differs from the editor context.",
            "The source changed after the previous diagnostic was produced.",
        ],
        "repairIds": item["repairs"],
        "references": [{"title": "ANCP language mapping", "uri": "https://agent-native-compiler-protocol.org/docs/language-mapping"}],
    }
    return document


def repair_plan_document(root: pathlib.Path, check_path: pathlib.Path | None = None) -> dict[str, Any]:
    check_doc = read_json(check_path) if check_path else None
    diagnostics = check_doc.get("diagnostics", []) if isinstance(check_doc, dict) else []
    document = envelope("plan.repair")
    actions = []
    for diag in diagnostics:
        hints = diag.get("repairHints") or []
        if not hints:
            continue
        hint = hints[0]
        actions.append(
            {
                "actionId": f"action-{diag['id']}",
                "repairId": hint["repairId"],
                "title": hint["title"],
                "intent": "Native adapter generated a conservative repair action. Review before applying.",
                "confidence": min(float(hint.get("confidence", 0.3)), 0.65),
                "safetyLevel": "review_required",
                "targetDiagnostics": [diag["id"]],
                "preconditions": [
                    {
                        "kind": "custom",
                        "required": True,
                        "value": "diagnostic-still-present",
                        "message": "Run ancp verify/check before applying semantic changes.",
                    }
                ],
                "explanation": "The reference implementation produces safe repair intent. Language-specific auto-edits should be added by compiler-integrated adapters.",
            }
        )
    document.update(
        {
            "status": "available" if actions else "unavailable",
            "planId": "plan-reference-" + (diagnostics[0]["id"] if diagnostics else "none"),
            "targetDiagnostics": [diag["id"] for diag in diagnostics],
            "actions": actions,
            "verification": {
                "policy": "all",
                "steps": [
                    {
                        "name": "ANCP check",
                        "argv": ["ancp", "check"],
                        "workingDirectory": str(root),
                        "expectedStatus": "passed",
                        "produces": ["result.check"],
                    }
                ],
            },
        }
    )
    return document


def verify_document(root: pathlib.Path, language: str | None, timeout: int) -> dict[str, Any]:
    adapter = get_adapter(language) if language else None
    docs = [adapter.check(root, timeout=timeout)] if adapter else [item.check(root, timeout=timeout) for item in matching_adapters(root)]
    diagnostics = [diag for item in docs for diag in item.get("diagnostics", [])]
    status = "failed" if diagnostics else aggregate_status(docs)
    document = envelope("result.verify")
    document.update(
        {
            "status": status,
            "verification": {
                "policy": "all",
                "steps": [
                    {
                        "name": "ANCP native check",
                        "argv": ["ancp", "check"] + (["--language", language] if language else []),
                        "workingDirectory": str(root),
                        "expectedStatus": "passed",
                        "result": {
                            "status": status,
                            "exitCode": status_exit_code(status),
                            "summary": f"{len(diagnostics)} diagnostics after verification run; aggregate status {status}.",
                        },
                    }
                ],
            },
            "diagnosticDelta": {
                "beforeCount": 0,
                "afterCount": len(diagnostics),
                "resolvedDiagnosticIds": [],
                "newDiagnosticIds": [diag["id"] for diag in diagnostics],
                "unchangedDiagnosticIds": [],
            },
            "data": {"checkDocuments": docs},
        }
    )
    return document


def graph_document(root: pathlib.Path) -> dict[str, Any]:
    nodes = []
    edges = []
    for adapter in matching_adapters(root):
        for path in __import__("ancp.util", fromlist=["list_files"]).list_files(root, adapter.file_extensions, limit=500):
            node_id = f"file:{path.relative_to(root).as_posix()}"
            nodes.append(
                {
                    "id": node_id,
                    "kind": "file",
                    "label": path.relative_to(root).as_posix(),
                    "location": {
                        "artifact": {"uri": path.resolve().as_uri(), "languageId": adapter.language_id, "role": "source"},
                        "range": {"unit": "utf16", "start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                    },
                }
            )
    document = envelope("graph.code")
    document.update({"workspace": workspace_object(root), "graph": {"nodes": nodes, "edges": edges}, "data": {"partial": True, "reason": "Reference graph lists files; language-specific symbol graphs belong in adapter extensions."}})
    return document


def skills_document() -> dict[str, Any]:
    document = envelope("result.skills")
    document["skills"] = {
        "toolchain": [{"name": "ancp", "version": __version__, "role": "custom", "transport": "cli"}],
        "sections": [
            {
                "id": "compiler-proxy-loop",
                "title": "Compiler Proxy Loop",
                "content": "Prefer normal compiler commands through ANCP proxy shims when integrating with existing builds. The native output remains visible and ANCP JSON is written to .ancp/last-check.json.",
                "appliesTo": [adapter.language_id for adapter in ADAPTERS],
            },
            {
                "id": "repair-discipline",
                "title": "Repair Discipline",
                "content": "Use diagnostics and repair plans as structured intent. Do not claim verification until a verify command or native build/test command has actually passed.",
                "appliesTo": [adapter.language_id for adapter in ADAPTERS],
            },
        ],
    }
    return document


def install_shims(
    directory: pathlib.Path,
    force: bool = False,
    output_mode: str = "passthrough",
    output_budget: int | None = None,
) -> list[pathlib.Path]:
    return write_shims(directory, force=force, output_mode=output_mode, output_budget=output_budget)


def install_shims_document(root: pathlib.Path, directory: pathlib.Path, created: list[pathlib.Path]) -> dict[str, Any]:
    document = envelope("result.skills")
    path_instruction = str(directory.resolve())
    document["skills"] = {
        "toolchain": [{"name": "ancp", "version": __version__, "role": "custom", "transport": "cli"}],
        "sections": [
            {
                "id": "shim-install-complete",
                "title": "Compiler Shim Install Complete",
                "content": (
                    "Compiler-name ANCP shims were installed. Put this directory first in PATH: "
                    f"{path_instruction}. Then run normal compiler commands. The native output is preserved and "
                    "ANCP JSON is written to .ancp/last-check.json by default."
                ),
                "appliesTo": [adapter.language_id for adapter in ADAPTERS],
            }
        ],
    }
    document["data"] = {
        "workspace": str(root),
        "shimDirectory": path_instruction,
        "created": [str(path) for path in created],
        "pathPrependPowerShell": f'$env:PATH="{path_instruction};$env:PATH"',
        "pathPrependPosix": f'export PATH="{path_instruction}:$PATH"',
        "nativeTools": executable_names(),
    }
    return document


def validate_command(args: argparse.Namespace) -> int:
    failures = 0
    for item in args.paths:
        path = pathlib.Path(item)
        paths = sorted(path.rglob("*.json")) if path.is_dir() else [path]
        for json_path in paths:
            errors = validate_path(json_path)
            if errors:
                failures += 1
                print(f"FAIL {json_path}")
                for error in errors:
                    print(f"  {error}")
            else:
                print(f"PASS {json_path}")
    return 1 if failures else 0


def raw_command(args: argparse.Namespace) -> int:
    path = pathlib.Path(args.from_path)
    document = read_json(path)
    raw = ((document.get("data") or {}).get("rawOutput") or {}) if isinstance(document, dict) else {}
    key = "combinedPath"
    if args.stream == "stdout":
        key = "stdoutPath"
    elif args.stream == "stderr":
        key = "stderrPath"
    raw_path_text = raw.get(key)
    if not raw_path_text:
        print(f"No raw {args.stream} log recorded in {path}", file=sys.stderr)
        return 2
    raw_path = pathlib.Path(raw_path_text)
    if args.path:
        print(raw_path)
        return 0
    if args.open:
        if os.name == "nt":
            os.startfile(raw_path)  # type: ignore[attr-defined]
            return 0
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([opener, str(raw_path)])
        return 0
    try:
        if args.tail and args.tail > 0:
            lines = raw_path.read_text(encoding="utf-8", errors="replace").splitlines()
            print("\n".join(lines[-args.tail:]))
        else:
            sys.stdout.write(raw_path.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        print(f"Could not read raw log {raw_path}: {exc}", file=sys.stderr)
        return 2
    return 0


def off_command(args: argparse.Namespace) -> int:
    command = list(args.command_args)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("usage: ancp off -- <command> [args...]", file=sys.stderr)
        return 2
    executable = find_executable(command[0])
    if not executable:
        print(f"Executable not found: {command[0]}", file=sys.stderr)
        return 127
    env = os.environ.copy()
    env["ANCP_BYPASS"] = "1"
    proc = subprocess.run(
        [executable, *command[1:]],
        cwd=os.getcwd(),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ancp", description="Agent Native Compiler Protocol reference CLI.")
    parser.add_argument("--version", action="version", version=f"ancp {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("manifest")

    cap = sub.add_parser("capabilities")
    cap.add_argument("--workspace", default=None)

    check = sub.add_parser("check")
    check.add_argument("--workspace", default=None)
    check.add_argument("--language", default=None)
    check.add_argument("--timeout", type=int, default=120)

    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("compile_args", nargs=argparse.REMAINDER)

    explain = sub.add_parser("explain")
    explain.add_argument("query")

    repair = sub.add_parser("repair")
    repair.add_argument("--workspace", default=None)
    repair.add_argument("--from", dest="from_path", default=None)
    repair.add_argument("--plan", action="store_true")

    verify = sub.add_parser("verify")
    verify.add_argument("--workspace", default=None)
    verify.add_argument("--language", default=None)
    verify.add_argument("--timeout", type=int, default=120)

    graph = sub.add_parser("graph")
    graph.add_argument("--workspace", default=None)

    sub.add_parser("skills")

    shims = sub.add_parser("install-shims")
    shims.add_argument("--workspace", default=None)
    shims.add_argument("--dir", default=".ancp/bin")
    shims.add_argument("--force", action="store_true")
    shims.add_argument("--output-mode", default="passthrough", choices=["passthrough", "auto-compact", "auto-ultra", "ultra", "compact", "json", "both"])
    shims.add_argument("--output-budget", type=int, default=None)

    enable = sub.add_parser("enable")
    enable.add_argument("--scope", default="user", choices=["user", "session"])
    enable.add_argument("--profile", default="agent", choices=["agent", "full"])
    enable.add_argument("--home", default=None)
    enable.add_argument("--force", action="store_true")
    enable.add_argument("--dry-run", action="store_true")
    enable.add_argument("--output-mode", default="auto-ultra", choices=["passthrough", "auto-compact", "auto-ultra", "ultra", "compact", "json", "both"])
    enable.add_argument("--output-budget", type=int, default=200)

    disable = sub.add_parser("disable")
    disable.add_argument("--scope", default="user", choices=["user", "session"])
    disable.add_argument("--home", default=None)
    disable.add_argument("--dry-run", action="store_true")

    uninstall = sub.add_parser("uninstall")
    uninstall.add_argument("--home", default=None)
    uninstall.add_argument("--dry-run", action="store_true")

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--home", default=None)

    raw = sub.add_parser("raw")
    raw.add_argument("--from", dest="from_path", default=".ancp/last-check.json")
    raw.add_argument("--stream", choices=["combined", "stdout", "stderr"], default="combined")
    raw.add_argument("--path", action="store_true")
    raw.add_argument("--open", action="store_true")
    raw.add_argument("--tail", type=int, default=None)

    off = sub.add_parser("off")
    off.add_argument("command_args", nargs=argparse.REMAINDER)

    validate = sub.add_parser("validate")
    validate.add_argument("paths", nargs="+")

    render = sub.add_parser("render")
    render.add_argument("--from", dest="from_path", required=True)
    render.add_argument("--max-diagnostics", type=int, default=40)
    render.add_argument("--format", default="markdown", choices=["markdown", "text", "ultra"])
    render.add_argument("--budget", type=int, default=None)

    schema = sub.add_parser("schema")
    schema.add_argument("--print", action="store_true", dest="print_schema")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "manifest":
        write_json_stdout(manifest_document())
        return 0
    if args.command == "capabilities":
        write_json_stdout(capabilities_document(resolve_workspace(args.workspace)))
        return 0
    if args.command == "check":
        return check_command(args)
    if args.command == "compile":
        return compile_main(args.compile_args)
    if args.command == "explain":
        write_json_stdout(explain_document(args.query))
        return 0
    if args.command == "repair":
        if not args.plan:
            print("Only --plan is supported by the safe reference implementation.", file=sys.stderr)
            return 5
        write_json_stdout(repair_plan_document(resolve_workspace(args.workspace), pathlib.Path(args.from_path) if args.from_path else None))
        return 0
    if args.command == "verify":
        write_json_stdout(verify_document(resolve_workspace(args.workspace), args.language, args.timeout))
        return 0
    if args.command == "graph":
        write_json_stdout(graph_document(resolve_workspace(args.workspace)))
        return 0
    if args.command == "skills":
        write_json_stdout(skills_document())
        return 0
    if args.command == "install-shims":
        root = resolve_workspace(args.workspace)
        shim_dir = pathlib.Path(args.dir)
        if not shim_dir.is_absolute():
            shim_dir = root / shim_dir
        created = install_shims(shim_dir, force=args.force, output_mode=args.output_mode, output_budget=args.output_budget)
        write_json_stdout(install_shims_document(root, shim_dir, created))
        return 0
    if args.command == "enable":
        write_json_stdout(
            enable_ancp(
                scope=args.scope,
                profile=args.profile,
                home=pathlib.Path(args.home) if args.home else None,
                force=args.force,
                dry_run=args.dry_run,
                output_mode=args.output_mode,
                output_budget=args.output_budget,
            )
        )
        return 0
    if args.command == "disable":
        write_json_stdout(
            disable_ancp(
                scope=args.scope,
                home=pathlib.Path(args.home) if args.home else None,
                dry_run=args.dry_run,
            )
        )
        return 0
    if args.command == "uninstall":
        write_json_stdout(uninstall_ancp(home=pathlib.Path(args.home) if args.home else None, dry_run=args.dry_run))
        return 0
    if args.command == "status":
        write_json_stdout(install_status(home=pathlib.Path(args.home) if args.home else None))
        return 0
    if args.command == "raw":
        return raw_command(args)
    if args.command == "off":
        return off_command(args)
    if args.command == "validate":
        return validate_command(args)
    if args.command == "render":
        document = read_json(pathlib.Path(args.from_path))
        if args.format == "ultra":
            sys.stdout.write(render_ultra(document, token_budget=args.budget))
        elif args.format == "text":
            sys.stdout.write(render_text(document, max_diagnostics=args.max_diagnostics, token_budget=args.budget))
        else:
            print(render_markdown(document, max_diagnostics=args.max_diagnostics))
        return 0
    if args.command == "schema":
        write_json_stdout(load_schema())
        return 0
    parser.error("unknown command")
    return 3


def validate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ancp-validate", description="Validate ANCP JSON documents.")
    parser.add_argument("paths", nargs="+")
    return validate_command(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
