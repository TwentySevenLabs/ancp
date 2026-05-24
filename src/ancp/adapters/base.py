"""Adapter base classes."""

from __future__ import annotations

import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any, Callable

from ancp import documents as doc
from ancp.native import (
    DOTNET_RE,
    GCC_RE,
    JAVAC_RE,
    PHP_RE,
    RUBY_RE,
    TSC_RE,
    canonical_for_native,
    parse_go_test_json,
    parse_pyright_json,
    parse_ruff_json,
    parse_rust_json_lines,
    parse_text_lines,
)
from ancp.util import CommandResult, command_run_object, find_executable, list_files, run_command


@dataclass(frozen=True)
class ToolSpec:
    name: str
    role: str
    command: list[str]
    transport: str = "cli"
    version_args: list[str] | None = None


class Adapter:
    """Base adapter for native tool-backed language checks."""

    key = "base"
    language_id = "unknown"
    display_name = "Unknown"
    file_extensions: set[str] = set()
    markers: set[str] = set()
    tools: list[ToolSpec] = []
    profiles = ["core", "explain", "repair-plan", "verify", "graph", "effects", "skills", "export"]

    def matches(self, root: pathlib.Path) -> bool:
        if any((root / marker).exists() for marker in self.markers):
            return True
        return bool(list_files(root, self.file_extensions, limit=1)) if self.file_extensions else False

    def available_tool(self) -> ToolSpec | None:
        for tool in self.tools:
            if find_executable(tool.command[0]):
                if tool.command[0] == "npx" and self._tool_version(tool) is None:
                    continue
                return tool
        return None

    def toolchain_entries(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for tool in self.tools:
            if not find_executable(tool.command[0]):
                continue
            version = self._tool_version(tool)
            if tool.command[0] == "npx" and version is None:
                continue
            entry: dict[str, Any] = {
                "name": tool.name,
                "role": tool.role,
                "command": tool.command,
                "transport": tool.transport,
            }
            if version:
                entry["version"] = version
            entries.append(entry)
        return entries

    def _tool_version(self, tool: ToolSpec) -> str | None:
        args = tool.version_args or [tool.command[0], "--version"]
        result = run_command(args, pathlib.Path.cwd(), timeout=10)
        if result.missing:
            return None
        if result.exit_code not in (0, None):
            return None
        text = (result.stdout or result.stderr).strip().splitlines()
        if not text:
            return None
        import re

        cleaned = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text[0]).strip()
        if not cleaned or all(not char.isalnum() for char in cleaned):
            return None
        return cleaned[:120]

    def language_entry(self) -> dict[str, Any]:
        return {
            "languageId": self.language_id,
            "names": [self.display_name],
            "fileExtensions": sorted(self.file_extensions),
        }

    def check(self, root: pathlib.Path, timeout: int = 60) -> dict[str, Any]:
        tool = self.available_tool()
        if not tool:
            return self.tool_missing_document(root)
        result = self.run_check(root, tool, timeout)
        diagnostics = self.parse_result(root, result, tool)
        document = doc.envelope("result.check", f"ancp-{self.key}-adapter")
        document.update(
            {
                "status": "failed" if diagnostics else ("tool_failed" if result.exit_code not in (0, None) and result.missing else "passed"),
                "workspace": doc.workspace_object(root),
                "run": command_run_object(result),
                "toolchain": self.toolchain_entries(),
                "diagnostics": diagnostics,
            }
        )
        if result.exit_code not in (0, None) and not diagnostics:
            document["status"] = "tool_failed"
            document["data"] = {"stderrSummary": result.stderr[-4000:], "stdoutSummary": result.stdout[-4000:]}
        return document

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        return run_command(tool.command, root, timeout=timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return []

    def tool_missing_document(self, root: pathlib.Path) -> dict[str, Any]:
        document = doc.envelope("result.check", f"ancp-{self.key}-adapter")
        document.update(
            {
                "status": "tool_failed",
                "workspace": doc.workspace_object(root),
                "run": {
                    "runId": f"missing-{self.key}",
                    "command": [self.tools[0].command[0] if self.tools else self.key],
                    "workingDirectory": str(root),
                    "startedAt": document["createdAt"],
                    "endedAt": document["createdAt"],
                    "durationMs": 0,
                },
                "toolchain": [],
                "diagnostics": [],
                "data": {
                    "reason": "No supported native tool was found on PATH.",
                    "adapter": self.key,
                    "expectedTools": [tool.command[0] for tool in self.tools],
                },
            }
        )
        return document

    def verification_steps(self, root: pathlib.Path) -> list[dict[str, Any]]:
        tool = self.available_tool()
        if not tool:
            return []
        return [
            {
                "name": f"{self.display_name} check",
                "argv": tool.command,
                "workingDirectory": str(root),
                "expectedStatus": "passed",
                "produces": ["result.check"],
                "effects": [
                    {
                        "kind": "filesystem.read",
                        "scope": "workspace",
                        "reason": f"Read {self.display_name} source and configuration",
                        "safetyLevel": "automatic",
                        "evidence": "manifest",
                    },
                    {
                        "kind": "process.spawn",
                        "scope": "workspace",
                        "reason": f"Run native {self.display_name} tool",
                        "safetyLevel": "review_required",
                        "evidence": "manifest",
                    },
                ],
            }
        ]


class TypeScriptAdapter(Adapter):
    key = "typescript"
    language_id = "typescript"
    display_name = "TypeScript"
    file_extensions = {".ts", ".tsx"}
    markers = {"tsconfig.json"}
    tools = [
        ToolSpec("typescript", "typechecker", ["tsc", "--noEmit", "--pretty", "false"]),
        ToolSpec("typescript", "typechecker", ["npx", "--no-install", "tsc", "--noEmit", "--pretty", "false"], version_args=["npx", "--no-install", "tsc", "--version"]),
    ]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        if tool.command[0] == "tsc" and not find_executable("tsc") and find_executable("npx"):
            return run_command(["npx", "--no-install", "tsc", "--noEmit", "--pretty", "false"], root, timeout)
        return run_command(tool.command, root, timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stdout + "\n" + result.stderr, TSC_RE, root, "typescript", "typescript", "diag-ts")


class JavaScriptAdapter(Adapter):
    key = "javascript"
    language_id = "javascript"
    display_name = "JavaScript"
    file_extensions = {".js", ".jsx", ".mjs", ".cjs"}
    markers = {"package.json", ".eslintrc", ".eslintrc.json", "eslint.config.js", "eslint.config.mjs"}
    tools = [
        ToolSpec("eslint", "linter", ["eslint", "--format", "json", "."]),
        ToolSpec("eslint", "linter", ["npx", "--no-install", "eslint", "--format", "json", "."], version_args=["npx", "--no-install", "eslint", "--version"]),
    ]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        import json

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        diagnostics: list[dict[str, Any]] = []
        counter = 0
        for file_item in payload if isinstance(payload, list) else []:
            file_path = pathlib.Path(file_item.get("filePath") or root)
            for msg in file_item.get("messages", []):
                counter += 1
                native_code = msg.get("ruleId")
                message = msg.get("message", "")
                canonical, kind, hints = canonical_for_native(native_code, message, "ancp.diag.lint.rule_violation")
                if msg.get("fix") or msg.get("suggestions"):
                    hints.append(doc.repair_hint("ancp.repair.lint.apply_fix", "Apply ESLint fix or suggestion", 0.8))
                diagnostics.append(
                    doc.diagnostic(
                        f"diag-eslint-{counter:04d}",
                        canonical,
                        native_code,
                        "error" if msg.get("severity") == 2 else "warning",
                        "lint" if canonical == "ancp.diag.lint.rule_violation" else kind,
                        message,
                        doc.location(file_path, "javascript", int(msg.get("line", 1)) - 1, int(msg.get("column", 1)) - 1),
                        "eslint",
                        hints,
                        {"native": msg},
                    )
                )
        return diagnostics


class PythonAdapter(Adapter):
    key = "python"
    language_id = "python"
    display_name = "Python"
    file_extensions = {".py"}
    markers = {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "tox.ini", "mypy.ini", "ruff.toml"}
    tools = [
        ToolSpec("pyright", "typechecker", ["pyright", "--outputjson"]),
        ToolSpec("ruff", "linter", ["ruff", "check", "--output-format", "json", "."]),
        ToolSpec("python", "compiler", ["python", "-m", "compileall", "-q", "."]),
    ]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        if tool.name == "pyright":
            return parse_pyright_json(result.stdout, root)
        if tool.name == "ruff":
            return parse_ruff_json(result.stdout, root)
        return self._parse_compileall(root, result.stderr + "\n" + result.stdout)

    def _parse_compileall(self, root: pathlib.Path, text: str) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        file_pattern = re_file = __import__("re").compile(r'File "(.+?)", line (\d+)')
        lines = text.splitlines()
        nonempty_lines = [line.strip() for line in lines if line.strip()]
        counter = 0
        for i, line in enumerate(lines):
            match = file_pattern.search(line)
            if not match:
                continue
            counter += 1
            path = pathlib.Path(match.group(1))
            if not path.is_absolute():
                path = root / path
            message = nonempty_lines[-1] if nonempty_lines else "Python syntax error"
            diagnostics.append(
                doc.diagnostic(
                    f"diag-python-{counter:04d}",
                    "ancp.diag.syntax.invalid",
                    "SyntaxError",
                    "error",
                    "syntax",
                    message,
                    doc.location(path, "python", int(match.group(2)) - 1, 0),
                    "python",
                    [doc.repair_hint("ancp.repair.syntax.insert_token", "Fix Python syntax", 0.4)],
                    {"raw": "\n".join(lines[max(i - 2, 0) : i + 4])},
                )
            )
        return diagnostics


class RustAdapter(Adapter):
    key = "rust"
    language_id = "rust"
    display_name = "Rust"
    file_extensions = {".rs"}
    markers = {"Cargo.toml"}
    tools = [ToolSpec("cargo", "build", ["cargo", "check", "--message-format=json"])]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_rust_json_lines(result.stdout + "\n" + result.stderr, root)


class GoAdapter(Adapter):
    key = "go"
    language_id = "go"
    display_name = "Go"
    file_extensions = {".go"}
    markers = {"go.mod", "go.work"}
    tools = [ToolSpec("go", "test", ["go", "test", "-json", "./..."], version_args=["go", "version"])]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        diagnostics = parse_go_test_json(result.stdout, root)
        if not diagnostics:
            diagnostics = parse_text_lines(result.stderr + "\n" + result.stdout, GCC_RE, root, "go", "go", "diag-go")
        return diagnostics


class CCppAdapter(Adapter):
    key = "c-cpp"
    language_id = "c-cpp"
    display_name = "C/C++"
    file_extensions = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh"}
    markers = {"compile_commands.json", "CMakeLists.txt", "Makefile"}
    tools = [
        ToolSpec("gcc", "compiler", ["gcc", "-fdiagnostics-format=json", "-fsyntax-only"]),
        ToolSpec("clang", "compiler", ["clang", "-fsyntax-only"]),
    ]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        files = [path for path in list_files(root, self.file_extensions, limit=25) if path.suffix.lower() in {".c", ".cc", ".cpp", ".cxx"}]
        if not files:
            return run_command([tool.command[0], "--version"], root, timeout=timeout)
        argv = tool.command + [str(path) for path in files]
        return run_command(argv, root, timeout=timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        if tool.name == "gcc":
            parsed = self._parse_gcc_json(result.stderr + "\n" + result.stdout, root)
            if parsed:
                return parsed
        return parse_text_lines(result.stderr + "\n" + result.stdout, GCC_RE, root, "c-cpp", tool.name, "diag-cc")

    def _parse_gcc_json(self, text: str, root: pathlib.Path) -> list[dict[str, Any]]:
        import json

        start = text.find("[")
        end = text.rfind("]")
        if start < 0 or end < start:
            return []
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
        diagnostics: list[dict[str, Any]] = []
        for index, item in enumerate(payload, start=1):
            loc = (item.get("locations") or [{}])[0].get("caret") or {}
            file_path = pathlib.Path(loc.get("file") or root)
            if not file_path.is_absolute():
                file_path = root / file_path
            message = item.get("message", "")
            canonical, kind, hints = canonical_for_native(item.get("option"), message)
            diagnostics.append(
                doc.diagnostic(
                    f"diag-gcc-{index:04d}",
                    canonical,
                    item.get("option"),
                    "warning" if item.get("kind") == "warning" else "error",
                    kind,
                    message,
                    doc.location(file_path, "c-cpp", int(loc.get("line", 1)) - 1, int(loc.get("column", 1)) - 1),
                    "gcc",
                    hints,
                    {"native": item},
                )
            )
        return diagnostics


class JavaAdapter(Adapter):
    key = "java"
    language_id = "java"
    display_name = "Java"
    file_extensions = {".java"}
    markers = {"pom.xml", "build.gradle", "settings.gradle"}
    tools = [ToolSpec("javac", "compiler", ["javac", "-Xlint:all"])]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        files = list_files(root, self.file_extensions, limit=100)
        if not files:
            return run_command(["javac", "-version"], root, timeout=timeout)
        return run_command(tool.command + [str(path) for path in files], root, timeout=timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stderr + "\n" + result.stdout, JAVAC_RE, root, "java", "javac", "diag-java")


class KotlinAdapter(Adapter):
    key = "kotlin"
    language_id = "kotlin"
    display_name = "Kotlin"
    file_extensions = {".kt", ".kts"}
    markers = {"build.gradle.kts", "settings.gradle.kts"}
    tools = [ToolSpec("kotlinc", "compiler", ["kotlinc"])]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        files = list_files(root, self.file_extensions, limit=100)
        if not files:
            return run_command(["kotlinc", "-version"], root, timeout=timeout)
        out_dir = pathlib.Path(tempfile.mkdtemp(prefix="ancp-kotlinc-"))
        return run_command(["kotlinc", *[str(path) for path in files], "-d", str(out_dir)], root, timeout=timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        regex = __import__("re").compile(r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s+(?P<severity>error|warning):\s+(?P<message>.+)$")
        return parse_text_lines(result.stderr + "\n" + result.stdout, regex, root, "kotlin", "kotlinc", "diag-kotlin")


class DotnetAdapter(Adapter):
    key = "csharp"
    language_id = "csharp"
    display_name = "C#/.NET"
    file_extensions = {".cs", ".fs", ".vb"}
    markers = {".sln", ".csproj", ".fsproj", ".vbproj", "Directory.Build.props"}
    tools = [ToolSpec("dotnet", "build", ["dotnet", "build", "--nologo"])]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stdout + "\n" + result.stderr, DOTNET_RE, root, "csharp", "dotnet", "diag-dotnet")


class SwiftAdapter(Adapter):
    key = "swift"
    language_id = "swift"
    display_name = "Swift"
    file_extensions = {".swift"}
    markers = {"Package.swift"}
    tools = [ToolSpec("swift", "build", ["swift", "build"])]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stderr + "\n" + result.stdout, GCC_RE, root, "swift", "swift", "diag-swift")


class ZigAdapter(Adapter):
    key = "zig"
    language_id = "zig"
    display_name = "Zig"
    file_extensions = {".zig"}
    markers = {"build.zig", "build.zig.zon"}
    tools = [ToolSpec("zig", "build", ["zig", "build"])]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stderr + "\n" + result.stdout, GCC_RE, root, "zig", "zig", "diag-zig")


class RubyAdapter(Adapter):
    key = "ruby"
    language_id = "ruby"
    display_name = "Ruby"
    file_extensions = {".rb"}
    markers = {"Gemfile", ".ruby-version"}
    tools = [ToolSpec("ruby", "compiler", ["ruby", "-c"])]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        files = list_files(root, self.file_extensions, limit=100)
        if not files:
            return run_command(["ruby", "--version"], root, timeout=timeout)
        # ruby -c accepts one file at a time; use the first failing file as a fast syntax gate.
        combined_stdout = []
        combined_stderr = []
        last: CommandResult | None = None
        for path in files:
            last = run_command(["ruby", "-c", str(path)], root, timeout=timeout)
            combined_stdout.append(last.stdout)
            combined_stderr.append(last.stderr)
            if last.exit_code not in (0, None):
                break
        assert last is not None
        return CommandResult(last.argv, root, last.started_at, last.ended_at, last.duration_ms, last.exit_code, "\n".join(combined_stdout), "\n".join(combined_stderr))

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stderr + "\n" + result.stdout, RUBY_RE, root, "ruby", "ruby", "diag-ruby")


class PhpAdapter(Adapter):
    key = "php"
    language_id = "php"
    display_name = "PHP"
    file_extensions = {".php"}
    markers = {"composer.json"}
    tools = [ToolSpec("php", "compiler", ["php", "-l"])]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        files = list_files(root, self.file_extensions, limit=100)
        if not files:
            return run_command(["php", "--version"], root, timeout=timeout)
        outputs: list[str] = []
        errors: list[str] = []
        last: CommandResult | None = None
        for path in files:
            last = run_command(["php", "-l", str(path)], root, timeout=timeout)
            outputs.append(last.stdout)
            errors.append(last.stderr)
            if last.exit_code not in (0, None):
                break
        assert last is not None
        return CommandResult(last.argv, root, last.started_at, last.ended_at, last.duration_ms, last.exit_code, "\n".join(outputs), "\n".join(errors))

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        return parse_text_lines(result.stderr + "\n" + result.stdout, PHP_RE, root, "php", "php", "diag-php")


class DartAdapter(Adapter):
    key = "dart"
    language_id = "dart"
    display_name = "Dart"
    file_extensions = {".dart"}
    markers = {"pubspec.yaml"}
    tools = [ToolSpec("dart", "typechecker", ["dart", "analyze"])]

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        regex = __import__("re").compile(r"^(?P<severity>error|warning|info)\s+-\s+(?P<file>.+?):(?P<line>\d+):(?P<col>\d+)\s+-\s+(?P<message>.+?)(?:\s+-\s+(?P<code>[a-zA-Z0-9_]+))?$")
        return parse_text_lines(result.stdout + "\n" + result.stderr, regex, root, "dart", "dart", "diag-dart")


class ScalaAdapter(Adapter):
    key = "scala"
    language_id = "scala"
    display_name = "Scala"
    file_extensions = {".scala", ".sc"}
    markers = {"build.sbt", "scala-cli.toml"}
    tools = [
        ToolSpec("scala-cli", "build", ["scala-cli", "compile", "."]),
        ToolSpec("scalac", "compiler", ["scalac"]),
    ]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        if tool.name == "scalac":
            files = list_files(root, self.file_extensions, limit=100)
            if not files:
                return run_command(["scalac", "-version"], root, timeout=timeout)
            out_dir = pathlib.Path(tempfile.mkdtemp(prefix="ancp-scalac-"))
            return run_command(["scalac", "-d", str(out_dir), *[str(path) for path in files]], root, timeout=timeout)
        return run_command(tool.command, root, timeout=timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        regex = __import__("re").compile(r"^(?P<file>.+?):(?P<line>\d+):\s+(?P<severity>error|warning):\s+(?P<message>.+)$")
        return parse_text_lines(result.stderr + "\n" + result.stdout, regex, root, "scala", tool.name, "diag-scala")


class JuliaAdapter(Adapter):
    key = "julia"
    language_id = "julia"
    display_name = "Julia"
    file_extensions = {".jl"}
    markers = {"Project.toml", "Manifest.toml"}
    tools = [ToolSpec("julia", "compiler", ["julia", "--startup-file=no", "--history-file=no"])]

    def run_check(self, root: pathlib.Path, tool: ToolSpec, timeout: int) -> CommandResult:
        files = list_files(root, self.file_extensions, limit=100)
        if not files:
            return run_command(["julia", "--version"], root, timeout=timeout)
        program = (
            "for f in ARGS\n"
            "  try\n"
            "    parsed = Meta.parseall(read(f, String); filename=f)\n"
            "    rendered = repr(parsed)\n"
            "    if occursin(\"Expr(:incomplete\", rendered) || occursin(\"ParseError\", rendered)\n"
            "      println(stderr, rendered)\n"
            "      exit(1)\n"
            "    end\n"
            "  catch e\n"
            "    showerror(stderr, e)\n"
            "    println(stderr)\n"
            "    exit(1)\n"
            "  end\n"
            "end\n"
        )
        return run_command(["julia", "--startup-file=no", "--history-file=no", "-e", program, *[str(path) for path in files]], root, timeout=timeout)

    def parse_result(self, root: pathlib.Path, result: CommandResult, tool: ToolSpec) -> list[dict[str, Any]]:
        if result.exit_code in (0, None):
            return []
        import re

        text = result.stderr + "\n" + result.stdout
        match = re.search(r"# Error @ (?P<file>.+?):(?P<line>\d+):(?P<col>\d+)", text)
        files = list_files(root, self.file_extensions, limit=1)
        file_path = pathlib.Path(match.group("file")) if match else (files[0] if files else root)
        if not file_path.is_absolute():
            file_path = root / file_path
        line = int(match.group("line")) - 1 if match else 0
        col = int(match.group("col")) - 1 if match else 0
        concise_messages = re.findall(r"Expected `[^`]+`|premature end of input", text)
        if concise_messages:
            message = "; ".join(dict.fromkeys(concise_messages))
        else:
            message_match = re.search(r"ParseError:[^\n]+", text)
            message = message_match.group(0) if message_match else "Julia parse/check failed"
        return [
            doc.diagnostic(
                "diag-julia-0001",
                "ancp.diag.syntax.invalid",
                "ParseError",
                "error",
                "syntax",
                message,
                doc.location(file_path, "julia", line, col, line, col + 1),
                "julia",
                [doc.repair_hint("ancp.repair.syntax.insert_token", "Fix Julia syntax", 0.35)],
                {"stderrSummary": text[-2000:]},
            )
        ]
