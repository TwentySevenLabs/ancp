"""Built-in adapter registry."""

from __future__ import annotations

import pathlib

from .base import (
    Adapter,
    CCppAdapter,
    ClojureAdapter,
    DartAdapter,
    DockerfileAdapter,
    DotnetAdapter,
    ElixirAdapter,
    ErlangAdapter,
    GoAdapter,
    HaskellAdapter,
    JavaAdapter,
    JavaScriptAdapter,
    JsonAdapter,
    JuliaAdapter,
    KotlinAdapter,
    LuaAdapter,
    NixAdapter,
    OcamlAdapter,
    PerlAdapter,
    PhpAdapter,
    PowerShellAdapter,
    PythonAdapter,
    RAdapter,
    RubyAdapter,
    RustAdapter,
    ScalaAdapter,
    ShellAdapter,
    SqlAdapter,
    SwiftAdapter,
    TerraformAdapter,
    TomlAdapter,
    TypeScriptAdapter,
    YamlAdapter,
    ZigAdapter,
)


ADAPTERS: list[Adapter] = [
    PythonAdapter(),
    TypeScriptAdapter(),
    JavaScriptAdapter(),
    RustAdapter(),
    GoAdapter(),
    CCppAdapter(),
    JavaAdapter(),
    KotlinAdapter(),
    DotnetAdapter(),
    SwiftAdapter(),
    ZigAdapter(),
    RubyAdapter(),
    PhpAdapter(),
    DartAdapter(),
    ScalaAdapter(),
    JuliaAdapter(),
    JsonAdapter(),
    TomlAdapter(),
    YamlAdapter(),
    ShellAdapter(),
    PowerShellAdapter(),
    LuaAdapter(),
    PerlAdapter(),
    RAdapter(),
    HaskellAdapter(),
    OcamlAdapter(),
    ErlangAdapter(),
    ElixirAdapter(),
    ClojureAdapter(),
    NixAdapter(),
    TerraformAdapter(),
    DockerfileAdapter(),
    SqlAdapter(),
]


def get_adapter(key: str) -> Adapter | None:
    normalized = key.lower()
    aliases = {
        "ts": "typescript",
        "js": "javascript",
        "c++": "c-cpp",
        "cpp": "c-cpp",
        "c": "c-cpp",
        "c#": "csharp",
        "dotnet": "csharp",
        "cs": "csharp",
        "rb": "ruby",
        "jl": "julia",
        "jsonc": "json",
        "yml": "yaml",
        "ps1": "powershell",
        "ps": "powershell",
        "sh": "shell",
        "bash": "shell",
        "rscript": "r",
        "hs": "haskell",
        "ml": "ocaml",
        "erl": "erlang",
        "ex": "elixir",
        "clj": "clojure",
        "hcl": "terraform",
        "tf": "terraform",
    }
    normalized = aliases.get(normalized, normalized)
    for adapter in ADAPTERS:
        if adapter.key == normalized or adapter.language_id == normalized:
            return adapter
    return None


def matching_adapters(root: pathlib.Path) -> list[Adapter]:
    matches = [adapter for adapter in ADAPTERS if adapter.matches(root)]
    return matches or ADAPTERS
