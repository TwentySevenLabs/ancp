"""Built-in adapter registry."""

from __future__ import annotations

import pathlib

from .base import (
    Adapter,
    CCppAdapter,
    DartAdapter,
    DotnetAdapter,
    GoAdapter,
    JavaAdapter,
    JavaScriptAdapter,
    JuliaAdapter,
    KotlinAdapter,
    PhpAdapter,
    PythonAdapter,
    RubyAdapter,
    RustAdapter,
    ScalaAdapter,
    SwiftAdapter,
    TypeScriptAdapter,
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
    }
    normalized = aliases.get(normalized, normalized)
    for adapter in ADAPTERS:
        if adapter.key == normalized or adapter.language_id == normalized:
            return adapter
    return None


def matching_adapters(root: pathlib.Path) -> list[Adapter]:
    matches = [adapter for adapter in ADAPTERS if adapter.matches(root)]
    return matches or ADAPTERS

