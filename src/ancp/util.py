"""General ANCP utilities."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_to_uri(path: pathlib.Path) -> str:
    return path.resolve().as_uri()


def uri_to_path(uri: str) -> pathlib.Path | None:
    if not uri.startswith("file://"):
        return None
    try:
        from urllib.parse import unquote, urlparse

        parsed = urlparse(uri)
        if parsed.netloc and sys.platform.startswith("win"):
            return pathlib.Path(f"//{parsed.netloc}{unquote(parsed.path)}")
        return pathlib.Path(unquote(parsed.path))
    except Exception:
        return None


def read_json(path: pathlib.Path) -> Any:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return json.loads(data.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return json.loads(data.decode("utf-8", errors="replace"))


def write_json_stdout(document: dict[str, Any]) -> None:
    print(json.dumps(document, indent=2, sort_keys=False))


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def sha256_file(path: pathlib.Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return "sha256:" + digest.hexdigest()
    except OSError:
        return None


def find_executable(name: str) -> str | None:
    return shutil.which(name)


def find_workspace(start: pathlib.Path | None = None) -> pathlib.Path:
    current = (start or pathlib.Path.cwd()).resolve()
    markers = [
        ".git",
        "pyproject.toml",
        "package.json",
        "tsconfig.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "settings.gradle",
        "Package.swift",
        "build.zig",
        "pubspec.yaml",
        "Project.toml",
    ]
    for path in [current, *current.parents]:
        if any((path / marker).exists() for marker in markers):
            return path
    return current


def list_files(root: pathlib.Path, extensions: set[str], limit: int = 5000) -> list[pathlib.Path]:
    ignored_dirs = {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "target",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        "__pycache__",
    }
    files: list[pathlib.Path] = []
    for current, dirs, filenames in os.walk(root):
        dirs[:] = [item for item in dirs if item not in ignored_dirs]
        base = pathlib.Path(current)
        for filename in filenames:
            path = base / filename
            if path.suffix.lower() in extensions:
                files.append(path)
                if len(files) >= limit:
                    return files
    return files


@dataclass
class CommandResult:
    argv: list[str]
    cwd: pathlib.Path
    started_at: str
    ended_at: str
    duration_ms: int
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    missing: bool = False


def run_command(argv: list[str], cwd: pathlib.Path, timeout: int = 60) -> CommandResult:
    started = _dt.datetime.now(_dt.timezone.utc)
    started_text = started.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    resolved_executable = shutil.which(argv[0]) if argv else None
    if not argv or not resolved_executable:
        ended = _dt.datetime.now(_dt.timezone.utc)
        return CommandResult(
            argv=argv,
            cwd=cwd,
            started_at=started_text,
            ended_at=ended.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            duration_ms=int((ended - started).total_seconds() * 1000),
            exit_code=None,
            stdout="",
            stderr=f"Executable not found: {argv[0] if argv else '<empty>'}",
            missing=True,
        )
    try:
        run_argv = [resolved_executable, *argv[1:]]
        proc = subprocess.run(
            run_argv,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            shell=False,
        )
        ended = _dt.datetime.now(_dt.timezone.utc)
        return CommandResult(
            argv=argv,
            cwd=cwd,
            started_at=started_text,
            ended_at=ended.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            duration_ms=int((ended - started).total_seconds() * 1000),
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        ended = _dt.datetime.now(_dt.timezone.utc)
        return CommandResult(
            argv=argv,
            cwd=cwd,
            started_at=started_text,
            ended_at=ended.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            duration_ms=int((ended - started).total_seconds() * 1000),
            exit_code=None,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nCommand timed out after {timeout}s",
            timed_out=True,
        )


def command_run_object(result: CommandResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "runId": sha256_text(" ".join(result.argv) + result.started_at)[:24],
        "command": result.argv,
        "workingDirectory": str(result.cwd),
        "startedAt": result.started_at,
        "endedAt": result.ended_at,
        "durationMs": result.duration_ms,
    }
    if result.exit_code is not None:
        payload["exitCode"] = result.exit_code
    return payload
