"""Native-name compiler shim support.

`ancp install-shims` creates files named like real compilers (`cargo`,
`rustc`, `tsc`, `python`, `julia`, `kotlinc`, `gcc`, `clang`, ...). When a
user prepends that shim directory to PATH, normal commands pass through ANCP
without changing project build scripts.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
from typing import Iterable

from .proxy import proxy_document, write_proxy_output
from .schema import validate_document
from .util import find_workspace


NATIVE_TO_ADAPTER = {
    "tsc": "typescript",
    "eslint": "javascript",
    "pyright": "python",
    "ruff": "python",
    "python": "python",
    "python3": "python",
    "cargo": "rust",
    "rustc": "rust",
    "go": "go",
    "gcc": "c-cpp",
    "g++": "c-cpp",
    "clang": "c-cpp",
    "clang++": "c-cpp",
    "javac": "java",
    "kotlinc": "kotlin",
    "dotnet": "csharp",
    "swift": "swift",
    "zig": "zig",
    "ruby": "ruby",
    "php": "php",
    "dart": "dart",
    "scala-cli": "scala",
    "scalac": "scala",
    "julia": "julia",
    "shellcheck": "shell",
    "bash": "shell",
    "pwsh": "powershell",
    "powershell": "powershell",
    "luac": "lua",
    "lua": "lua",
    "perl": "perl",
    "rscript": "r",
    "ghc": "haskell",
    "ocamlc": "ocaml",
    "erlc": "erlang",
    "elixirc": "elixir",
    "clj-kondo": "clojure",
    "nix-instantiate": "nix",
    "terraform": "terraform",
    "hadolint": "dockerfile",
    "sqlfluff": "sql",
}


def executable_names() -> list[str]:
    return sorted(NATIVE_TO_ADAPTER)


def find_real_executable(name: str, skip_dirs: Iterable[pathlib.Path]) -> str | None:
    skip_resolved = {path.resolve() for path in skip_dirs}
    candidates: list[str] = []
    path_exts = [""]
    if os.name == "nt":
        path_exts = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
    for path_text in os.environ.get("PATH", "").split(os.pathsep):
        if not path_text:
            continue
        directory = pathlib.Path(path_text)
        try:
            if directory.resolve() in skip_resolved:
                continue
        except OSError:
            continue
        names = [name] if os.name != "nt" else [name + ext.lower() for ext in path_exts] + [name + ext.upper() for ext in path_exts]
        for candidate_name in names:
            candidate = directory / candidate_name
            if candidate.exists() and not candidate.is_dir():
                candidates.append(str(candidate))
    return candidates[0] if candidates else shutil.which(name)


def run_native_name(native_name: str, argv: list[str], shim_dir: pathlib.Path | None = None) -> int:
    adapter = NATIVE_TO_ADAPTER.get(native_name.lower())
    if not adapter:
        print(f"ANCP shim does not know native tool: {native_name}", file=sys.stderr)
        return 127
    skip = [shim_dir] if shim_dir else []
    real = find_real_executable(native_name, [item for item in skip if item])
    if not real:
        print(f"ANCP shim could not find real executable for {native_name}", file=sys.stderr)
        return 127
    root = pathlib.Path(os.environ["ANCP_WORKSPACE"]).resolve() if os.environ.get("ANCP_WORKSPACE") else pathlib.Path.cwd().resolve()
    timeout = int(os.environ.get("ANCP_TIMEOUT", "120"))
    out = pathlib.Path(os.environ["ANCP_OUT"]) if os.environ.get("ANCP_OUT") else None
    document, exit_code, stdout, stderr = proxy_document(adapter, [real, *argv], root, timeout)
    errors = validate_document(document)
    if errors:
        document.setdefault("data", {})["validationErrors"] = errors
    write_proxy_output(document, out, root)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return exit_code


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python -m ancp.shim <native-tool> [args...]", file=sys.stderr)
        return 2
    native = argv[0]
    shim_dir = pathlib.Path(os.environ["ANCP_SHIM_DIR"]) if os.environ.get("ANCP_SHIM_DIR") else None
    return run_native_name(native, argv[1:], shim_dir)


if __name__ == "__main__":
    raise SystemExit(main())
