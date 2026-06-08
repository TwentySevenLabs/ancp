"""Compiler-facing ANCP proxy mode.

Proxy mode is the bridge between "agent calls a tool" and "normal compiler
workflow emits ANCP". It runs the native compiler unchanged, preserves stdout,
stderr, and exit code, and mirrors a structured ANCP document to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any

from . import documents as doc
from .adapters import get_adapter
from .adapters.base import ToolSpec
from .render import estimate_tokens, render_text
from .schema import validate_document
from .util import command_run_object, find_workspace, path_to_uri, run_command, sha256_text


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
    "ancp-shellcheck": ("shell", "shellcheck"),
    "ancp-bash": ("shell", "bash"),
    "ancp-pwsh": ("powershell", "pwsh"),
    "ancp-powershell": ("powershell", "powershell"),
    "ancp-luac": ("lua", "luac"),
    "ancp-lua": ("lua", "lua"),
    "ancp-perl": ("perl", "perl"),
    "ancp-Rscript": ("r", "Rscript"),
    "ancp-rscript": ("r", "Rscript"),
    "ancp-ghc": ("haskell", "ghc"),
    "ancp-ocamlc": ("ocaml", "ocamlc"),
    "ancp-erlc": ("erlang", "erlc"),
    "ancp-elixirc": ("elixir", "elixirc"),
    "ancp-clj-kondo": ("clojure", "clj-kondo"),
    "ancp-nix-instantiate": ("nix", "nix-instantiate"),
    "ancp-terraform": ("terraform", "terraform"),
    "ancp-hadolint": ("dockerfile", "hadolint"),
    "ancp-sqlfluff": ("sql", "sqlfluff"),
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
    executable_name = pathlib.Path(native_command[0]).name
    if executable_name.lower().endswith((".exe", ".cmd", ".bat")):
        executable_name = pathlib.Path(executable_name).stem
    tool = ToolSpec(executable_name, "compiler", native_command)
    diagnostics = adapter.parse_result(root, result, tool)
    run_object = command_run_object(result)
    raw_output = write_raw_output(root, run_object["runId"], result.stdout, result.stderr)
    document = doc.envelope("result.check", f"ancp-{adapter.key}-compiler-proxy")
    document.update(
        {
            "status": "failed" if diagnostics else ("passed" if result.exit_code == 0 else "tool_failed"),
            "workspace": doc.workspace_object(root),
            "run": run_object,
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
                "rawOutput": raw_output,
            },
        }
    )
    if result.exit_code not in (0, None) and not diagnostics:
        document["data"]["stderrSummary"] = result.stderr[-4000:]
        document["data"]["stdoutSummary"] = result.stdout[-4000:]
    annotate_signal_metrics(document, result.stdout, result.stderr)
    return document, result.exit_code if result.exit_code is not None else 2, result.stdout, result.stderr


def write_raw_output(root: pathlib.Path, run_id: str, stdout: str, stderr: str) -> dict[str, Any]:
    safe_run_id = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in run_id)
    run_dir = root / ".ancp" / "runs" / safe_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    combined_path = run_dir / "native.log"
    stdout_path.write_text(stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(stderr, encoding="utf-8", errors="replace")
    combined = "".join(
        [
            "ANCP native stdout\n",
            stdout,
            "\nANCP native stderr\n",
            stderr,
        ]
    )
    combined_path.write_text(combined, encoding="utf-8", errors="replace")
    native_text = stdout + stderr
    return {
        "stdoutPath": str(stdout_path),
        "stderrPath": str(stderr_path),
        "combinedPath": str(combined_path),
        "stdoutUri": path_to_uri(stdout_path),
        "stderrUri": path_to_uri(stderr_path),
        "combinedUri": path_to_uri(combined_path),
        "nativeBytes": len(native_text.encode("utf-8", errors="replace")),
        "nativeSha256": sha256_text(native_text),
    }


def annotate_signal_metrics(document: dict[str, Any], stdout: str, stderr: str) -> None:
    native_text = stdout + stderr
    native_tokens = estimate_tokens(native_text)
    compact_tokens = estimate_tokens(render_text(document, max_diagnostics=12, token_budget=None))
    savings = 0
    if native_tokens:
        savings = max(0, round((1 - (compact_tokens / native_tokens)) * 100))
    document.setdefault("data", {})["signalMetrics"] = {
        "nativeBytes": len(native_text.encode("utf-8", errors="replace")),
        "compactBytes": 0,
        "estimatedNativeTokens": native_tokens,
        "estimatedCompactTokens": compact_tokens,
        "estimatedSavingsPercent": savings,
        "renderer": "raw-text",
    }
    final_compact = render_text(document, max_diagnostics=12, token_budget=None)
    final_compact_tokens = estimate_tokens(final_compact)
    final_savings = max(0, round((1 - (final_compact_tokens / native_tokens)) * 100)) if native_tokens else 0
    document["data"]["signalMetrics"].update(
        {
            "compactBytes": len(final_compact.encode("utf-8", errors="replace")),
            "estimatedCompactTokens": final_compact_tokens,
            "estimatedSavingsPercent": final_savings,
        }
    )


def format_proxy_output(
    document: dict[str, Any],
    stdout: str,
    stderr: str,
    mode: str = "passthrough",
    token_budget: int | None = None,
) -> tuple[str, str]:
    normalized = mode.lower().replace("_", "-")
    if normalized in {"passthrough", "native", "raw"}:
        return stdout, stderr
    if normalized in {"compact", "text", "minimal"}:
        return render_text(document, token_budget=token_budget), ""
    if normalized in {"json", "result"}:
        return json.dumps(document, indent=2) + "\n", ""
    if normalized in {"both", "native-and-compact"}:
        compact = render_text(document, token_budget=token_budget)
        return stdout, stderr + ("\n" if stderr and not stderr.endswith("\n") else "") + compact
    if normalized in {"auto", "auto-compact", "agent"}:
        if document.get("status") == "passed":
            return stdout, stderr
        return render_text(document, token_budget=token_budget), ""
    raise ValueError(f"unknown ANCP output mode: {mode}")


def write_proxy_output(document: dict[str, Any], out_path: pathlib.Path | None, root: pathlib.Path) -> pathlib.Path:
    target = out_path or (root / ".ancp" / "last-check.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return target


def compile_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a native compiler command and mirror ANCP JSON.")
    parser.add_argument("adapter", help="Adapter key, such as typescript, rust, kotlin, julia.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--ancp-out", default=None, help="Where to write ANCP JSON. Defaults to .ancp/last-check.json.")
    parser.add_argument("--ancp-output", default=None, help="Output mode: passthrough, auto-compact, compact, json, both.")
    parser.add_argument("--ancp-budget", type=int, default=None, help="Approximate token budget for compact text output.")
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
    output_mode = args.ancp_output or "passthrough"
    final_stdout, final_stderr = format_proxy_output(document, stdout, stderr, output_mode, args.ancp_budget)
    sys.stdout.write(final_stdout)
    sys.stderr.write(final_stderr)
    return exit_code


def shim_main(shim_name: str, argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    adapter_key, native = SHIM_TO_ADAPTER_AND_COMMAND[shim_name]
    out_path: pathlib.Path | None = None
    timeout = 120
    output_mode: str | None = None
    token_budget: int | None = None
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
        if arg == "--ancp-output" and i + 1 < len(argv):
            output_mode = argv[i + 1]
            i += 2
            continue
        if arg == "--ancp-budget" and i + 1 < len(argv):
            token_budget = int(argv[i + 1])
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
    env_budget = int(os.environ["ANCP_OUTPUT_BUDGET"]) if os.environ.get("ANCP_OUTPUT_BUDGET") else None
    final_stdout, final_stderr = format_proxy_output(
        document,
        stdout,
        stderr,
        output_mode or os.environ.get("ANCP_OUTPUT_MODE", "passthrough"),
        token_budget or env_budget,
    )
    sys.stdout.write(final_stdout)
    sys.stderr.write(final_stderr)
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
shellcheck_main = make_shim("ancp-shellcheck")
bash_main = make_shim("ancp-bash")
pwsh_main = make_shim("ancp-pwsh")
powershell_main = make_shim("ancp-powershell")
luac_main = make_shim("ancp-luac")
lua_main = make_shim("ancp-lua")
perl_main = make_shim("ancp-perl")
rscript_main = make_shim("ancp-rscript")
ghc_main = make_shim("ancp-ghc")
ocamlc_main = make_shim("ancp-ocamlc")
erlc_main = make_shim("ancp-erlc")
elixirc_main = make_shim("ancp-elixirc")
clj_kondo_main = make_shim("ancp-clj-kondo")
nix_instantiate_main = make_shim("ancp-nix-instantiate")
terraform_main = make_shim("ancp-terraform")
hadolint_main = make_shim("ancp-hadolint")
sqlfluff_main = make_shim("ancp-sqlfluff")
