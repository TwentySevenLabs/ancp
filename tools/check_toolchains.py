#!/usr/bin/env python3
"""Report native compiler/checker availability for ANCP adapters."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Toolchain:
    language: str
    required_any: tuple[str, ...]
    notes: str


TOOLCHAINS = [
    Toolchain("python", ("python", "python3"), "Required for ANCP itself and Python syntax checks."),
    Toolchain("typescript", ("tsc",), "TypeScript compiler checks."),
    Toolchain("javascript", ("eslint", "node"), "ESLint preferred; Node --check syntax fallback accepted."),
    Toolchain("rust", ("cargo", "rustc"), "Cargo/rustc JSON diagnostics."),
    Toolchain("go", ("go",), "Go build/test tooling."),
    Toolchain("c", ("gcc", "clang"), "GCC or Clang C frontend."),
    Toolchain("cpp", ("g++", "clang++"), "GCC or Clang C++ frontend."),
    Toolchain("java", ("javac",), "JDK compiler."),
    Toolchain("kotlin", ("kotlinc",), "Kotlin compiler."),
    Toolchain("csharp", ("dotnet",), ".NET SDK."),
    Toolchain("swift", ("swift",), "Swift compiler/test tooling."),
    Toolchain("zig", ("zig",), "Zig compiler/build tooling."),
    Toolchain("ruby", ("ruby",), "ruby -c syntax checks."),
    Toolchain("php", ("php",), "php -l syntax checks."),
    Toolchain("dart", ("dart",), "Dart analyzer/compiler."),
    Toolchain("scala", ("scala-cli", "scalac"), "scala-cli preferred, scalac accepted."),
    Toolchain("julia", ("julia",), "Julia parser/runtime checks."),
    Toolchain("shell", ("shellcheck", "bash"), "ShellCheck JSON preferred, bash -n fallback."),
    Toolchain("powershell", ("pwsh", "powershell"), "PowerShell Parser API."),
    Toolchain("lua", ("luac", "lua"), "luac preferred, lua loadfile fallback."),
    Toolchain("perl", ("perl",), "perl -c syntax checks."),
    Toolchain("r", ("Rscript",), "R parser checks."),
    Toolchain("haskell", ("ghc",), "GHC -fno-code checks."),
    Toolchain("ocaml", ("ocamlc",), "ocamlc syntax/type checks."),
    Toolchain("erlang", ("erlc",), "erlc module checks."),
    Toolchain("elixir", ("elixirc",), "elixirc compiler checks."),
    Toolchain("clojure", ("clj-kondo",), "clj-kondo JSON diagnostics."),
    Toolchain("nix", ("nix-instantiate",), "nix-instantiate --parse checks."),
    Toolchain("terraform", ("terraform",), "terraform validate -json checks."),
    Toolchain("dockerfile", ("hadolint",), "Hadolint JSON diagnostics."),
    Toolchain("sql", ("sqlfluff",), "SQLFluff JSON diagnostics."),
]


def availability(languages: set[str] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for toolchain in TOOLCHAINS:
        if languages and toolchain.language not in languages:
            continue
        found = {name: shutil.which(name) for name in toolchain.required_any}
        available = any(found.values())
        if toolchain.language == "csharp":
            available = _dotnet_sdk_available()
        rows.append(
            {
                "language": toolchain.language,
                "available": available,
                "tools": found,
                "notes": toolchain.notes,
            }
        )
    return rows


def _dotnet_sdk_available() -> bool:
    if not shutil.which("dotnet"):
        return False
    try:
        result = subprocess.run(
            ["dotnet", "--list-sdks"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def print_table(rows: list[dict[str, object]]) -> None:
    width = max(len(str(row["language"])) for row in rows)
    for row in rows:
        tools = row["tools"]
        assert isinstance(tools, dict)
        present = [name for name, path in tools.items() if path]
        missing = [name for name, path in tools.items() if not path]
        status = "ok" if row["available"] else "missing"
        detail = ", ".join(present) if present and row["available"] else "missing: " + ", ".join(missing)
        if row["language"] == "csharp" and present and not row["available"]:
            detail = "dotnet present, SDK missing"
        print(f"{str(row['language']).ljust(width)}  {status.ljust(7)}  {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any selected native toolchain is missing.",
    )
    parser.add_argument(
        "--language",
        action="append",
        choices=[toolchain.language for toolchain in TOOLCHAINS],
        help="Restrict the report to one language. May be repeated.",
    )
    args = parser.parse_args(argv)

    rows = availability(set(args.language) if args.language else None)
    if args.json:
        print(json.dumps({"toolchains": rows}, indent=2, sort_keys=True))
    else:
        print_table(rows)

    if args.strict and not all(row["available"] for row in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
