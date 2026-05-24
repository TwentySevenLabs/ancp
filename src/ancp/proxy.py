"""Compiler-facing ANCP proxy mode.

Proxy mode is the bridge between "agent calls a tool" and "normal compiler
workflow emits ANCP". It runs the native compiler unchanged, preserves stdout,
stderr, and exit code, and mirrors a structured ANCP document to disk.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

from . import documents as doc
from .adapters import get_adapter
from .adapters.base import ToolSpec
from .schema import validate_document
from .util import command_run_object, find_workspace, run_command


SHIM_TO_ADAPTER_AND_COMMAND = {
    "ancp-tsc": ("typescript", "tsc"),
    "ancp-eslint": ("javascript", "eslint"),
    "ancp-pyright": ("python", "pyright"),
    "ancp-ruff": ("python", "ruff"),
    "ancp-python": ("python", "python"),
    "ancp-cargo": ("rust", "cargo"),
    "ancp-rustc": ("rust", "rustc"),
    "ancp-go": ("go", "go"),
    "ancp-gcc": ("c-cpp", "gcc"),
    "ancp-clang": ("c-cpp", "clang"),
    "ancp-javac": ("java", "javac"),
    "ancp-kotlinc": ("kotlin", "kotlinc"),
    "ancp-dotnet": ("csharp", "dotnet"),
    "ancp-swift": ("swift", "swift"),
    "ancp-zig": ("zig", "zig"),
    "ancp-ruby": ("ruby", "ruby"),
    "ancp-php": ("php", "php"),
    "ancp-dart": ("dart", "dart"),
    "ancp-scala-cli": ("scala", "scala-cli"),
    "ancp-scalac": ("scala", "scalac"),
    "ancp-julia": ("julia", "julia"),
}


def proxy_document(
    adapter_key: str,
    native_command: list[str],
    root: pathlib.Path,
    timeout: int,
) -> tuple[dict[str, Any], int, str, str]:
    adapter = get_adapter(adapter_key)
    if adapter is None:
        raise SystemExit(f"Unknown adapter: {adapter_key}")
    result = run_command(native_command, root, timeout=timeout)
    tool = ToolSpec(native_command[0], "compiler", native_command)
    diagnostics = adapter.parse_result(root, result, tool)
    document = doc.envelope("result.check", f"ancp-{adapter.key}-compiler-proxy")
    document.update(
        {
            "status": "failed" if diagnostics else ("passed" if result.exit_code == 0 else "tool_failed"),
            "workspace": doc.workspace_object(root),
            "run": command_run_object(result),
            "toolchain": [
                {
                    "name": native_command[0],
                    "role": "compiler",
                    "command": native_command,
                    "transport": "cli",
                }
            ],
            "diagnostics": diagnostics,
            "data": {
                "integrationMode": "compiler-proxy",
                "nativeExitCode": result.exit_code,
                "passthrough": True,
            },
        }
    )
    if result.exit_code not in (0, None) and not diagnostics:
        document["data"]["stderrSummary"] = result.stderr[-4000:]
        document["data"]["stdoutSummary"] = result.stdout[-4000:]
    return document, result.exit_code if result.exit_code is not None else 2, result.stdout, result.stderr


def write_proxy_output(document: dict[str, Any], out_path: pathlib.Path | None, root: pathlib.Path) -> pathlib.Path:
    import json

    target = out_path or (root / ".ancp" / "last-check.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return target


def compile_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a native compiler command and mirror ANCP JSON.")
    parser.add_argument("adapter", help="Adapter key, such as typescript, rust, kotlin, julia.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--ancp-out", default=None, help="Where to write ANCP JSON. Defaults to .ancp/last-check.json.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Native command after --.")
    args = parser.parse_args(argv)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("missing native command; use: ancp compile <adapter> -- <compiler> <args>")
    root = find_workspace(pathlib.Path(args.workspace))
    document, exit_code, stdout, stderr = proxy_document(args.adapter, command, root, args.timeout)
    errors = validate_document(document)
    if errors:
        document.setdefault("data", {})["validationErrors"] = errors
    write_proxy_output(document, pathlib.Path(args.ancp_out) if args.ancp_out else None, root)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return exit_code


def shim_main(shim_name: str, argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    adapter_key, native = SHIM_TO_ADAPTER_AND_COMMAND[shim_name]
    out_path: pathlib.Path | None = None
    timeout = 120
    workspace = pathlib.Path.cwd()
    native_args: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--ancp-out" and i + 1 < len(argv):
            out_path = pathlib.Path(argv[i + 1])
            i += 2
            continue
        if arg == "--ancp-workspace" and i + 1 < len(argv):
            workspace = pathlib.Path(argv[i + 1])
            i += 2
            continue
        if arg == "--ancp-timeout" and i + 1 < len(argv):
            timeout = int(argv[i + 1])
            i += 2
            continue
        native_args.append(arg)
        i += 1
    root = find_workspace(workspace)
    command = [native, *native_args]
    document, exit_code, stdout, stderr = proxy_document(adapter_key, command, root, timeout)
    errors = validate_document(document)
    if errors:
        document.setdefault("data", {})["validationErrors"] = errors
    write_proxy_output(document, out_path, root)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return exit_code


def make_shim(name: str):
    def _main() -> int:
        return shim_main(name)

    return _main


tsc_main = make_shim("ancp-tsc")
eslint_main = make_shim("ancp-eslint")
pyright_main = make_shim("ancp-pyright")
ruff_main = make_shim("ancp-ruff")
python_main = make_shim("ancp-python")
cargo_main = make_shim("ancp-cargo")
rustc_main = make_shim("ancp-rustc")
go_main = make_shim("ancp-go")
gcc_main = make_shim("ancp-gcc")
clang_main = make_shim("ancp-clang")
javac_main = make_shim("ancp-javac")
kotlinc_main = make_shim("ancp-kotlinc")
dotnet_main = make_shim("ancp-dotnet")
swift_main = make_shim("ancp-swift")
zig_main = make_shim("ancp-zig")
ruby_main = make_shim("ancp-ruby")
php_main = make_shim("ancp-php")
dart_main = make_shim("ancp-dart")
scala_cli_main = make_shim("ancp-scala-cli")
scalac_main = make_shim("ancp-scalac")
julia_main = make_shim("ancp-julia")

