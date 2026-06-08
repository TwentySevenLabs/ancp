"""Reversible ANCP shim installation and global enablement helpers."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
from typing import Any, Iterable

from . import __version__
from .shim import executable_names


SHELL_TOOL_NAMES = {"bash", "powershell", "pwsh"}
STATE_FILE_NAME = "state.json"


def default_home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("ANCP_HOME", pathlib.Path.home() / ".ancp")).resolve()


def default_shim_dir(home: pathlib.Path | None = None) -> pathlib.Path:
    return (home or default_home()) / "bin"


def profile_tools(profile: str) -> list[str]:
    normalized = profile.lower()
    names = executable_names()
    if normalized == "full":
        return names
    if normalized == "agent":
        return [name for name in names if name not in SHELL_TOOL_NAMES]
    raise ValueError(f"unknown ANCP profile: {profile}")


def write_shims(
    directory: pathlib.Path,
    *,
    force: bool = False,
    names: Iterable[str] | None = None,
    output_mode: str = "passthrough",
    output_budget: int | None = None,
) -> list[pathlib.Path]:
    directory.mkdir(parents=True, exist_ok=True)
    created: list[pathlib.Path] = []
    python_exe = pathlib.Path(sys.executable).resolve()
    selected = sorted(names or executable_names())
    for name in selected:
        if os.name == "nt":
            target = directory / f"{name}.cmd"
            if target.exists() and not force:
                continue
            lines = [
                "@echo off",
                "setlocal",
                "set ANCP_SHIM_DIR=%~dp0",
                f"set ANCP_OUTPUT_MODE={output_mode}",
            ]
            if output_budget is not None:
                lines.append(f"set ANCP_OUTPUT_BUDGET={output_budget}")
            lines.extend(
                [
                    f'"{python_exe}" -m ancp.shim {name} %*',
                    "exit /b %ERRORLEVEL%",
                    "",
                ]
            )
            target.write_text("\n".join(lines), encoding="utf-8")
            created.append(target)
        else:
            target = directory / name
            if target.exists() and not force:
                continue
            lines = [
                "#!/usr/bin/env sh",
                'ANCP_SHIM_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"',
                "export ANCP_SHIM_DIR",
                f'ANCP_OUTPUT_MODE="{output_mode}"',
                "export ANCP_OUTPUT_MODE",
            ]
            if output_budget is not None:
                lines.extend([f'ANCP_OUTPUT_BUDGET="{output_budget}"', "export ANCP_OUTPUT_BUDGET"])
            lines.extend(
                [
                    f'exec "{python_exe}" -m ancp.shim {name} "$@"',
                    "",
                ]
            )
            target.write_text("\n".join(lines), encoding="utf-8")
            target.chmod(0o755)
            created.append(target)
    return created


def _path_entries(path_value: str) -> list[str]:
    return [entry for entry in path_value.split(os.pathsep) if entry]


def _path_contains(path_value: str, directory: pathlib.Path) -> bool:
    wanted = str(directory.resolve()).casefold()
    for entry in _path_entries(path_value):
        try:
            if str(pathlib.Path(entry).resolve()).casefold() == wanted:
                return True
        except OSError:
            continue
    return False


def _remove_path_entry(path_value: str, directory: pathlib.Path) -> str:
    wanted = str(directory.resolve()).casefold()
    kept: list[str] = []
    for entry in _path_entries(path_value):
        try:
            if str(pathlib.Path(entry).resolve()).casefold() == wanted:
                continue
        except OSError:
            pass
        kept.append(entry)
    return os.pathsep.join(kept)


def _user_path_windows() -> str:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "Path")
            return str(value)
        except FileNotFoundError:
            return ""


def _set_user_path_windows(value: str) -> None:
    import ctypes
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, value)
    try:
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
    except Exception:
        pass


def user_path_value() -> str:
    if os.name == "nt":
        return _user_path_windows()
    return os.environ.get("PATH", "")


def set_user_path_value(value: str) -> None:
    if os.name != "nt":
        raise RuntimeError("persistent user PATH management is currently implemented for Windows only")
    _set_user_path_windows(value)


def state_path(home: pathlib.Path) -> pathlib.Path:
    return home / STATE_FILE_NAME


def write_state(home: pathlib.Path, payload: dict[str, Any]) -> None:
    home.mkdir(parents=True, exist_ok=True)
    state_path(home).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_state(home: pathlib.Path) -> dict[str, Any]:
    path = state_path(home)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"stateError": f"invalid JSON in {path}"}


def enable(
    *,
    scope: str = "user",
    profile: str = "agent",
    home: pathlib.Path | None = None,
    force: bool = False,
    dry_run: bool = False,
    output_mode: str = "auto-compact",
    output_budget: int | None = 800,
) -> dict[str, Any]:
    resolved_home = (home or default_home()).resolve()
    shim_dir = default_shim_dir(resolved_home)
    names = profile_tools(profile)
    would_create = [str(shim_dir / (f"{name}.cmd" if os.name == "nt" else name)) for name in names]
    created: list[pathlib.Path] = [] if dry_run else write_shims(
        shim_dir,
        force=force,
        names=names,
        output_mode=output_mode,
        output_budget=output_budget,
    )

    path_before = user_path_value() if scope == "user" and os.name == "nt" else os.environ.get("PATH", "")
    path_after = path_before
    path_changed = False
    enabled_before = _path_contains(path_before, shim_dir)
    if scope == "user":
        if os.name != "nt":
            if not dry_run:
                raise RuntimeError("ancp enable --scope user currently supports Windows persistent PATH only")
            path_after = str(shim_dir) + (os.pathsep + path_before if path_before else "")
            path_changed = not enabled_before
        elif not _path_contains(path_before, shim_dir):
            path_after = str(shim_dir) + (os.pathsep + path_before if path_before else "")
            path_changed = True
            if not dry_run:
                set_user_path_value(path_after)
    elif scope == "session":
        path_after = str(shim_dir) + os.pathsep + os.environ.get("PATH", "")
    else:
        raise ValueError(f"unknown enable scope: {scope}")

    payload = {
        "ancpVersion": __version__,
        "enabled": enabled_before if dry_run else scope == "user" and _path_contains(path_after, shim_dir),
        "enabledBefore": enabled_before,
        "wouldEnable": scope == "user" and not enabled_before,
        "scope": scope,
        "profile": profile,
        "home": str(resolved_home),
        "shimDirectory": str(shim_dir),
        "outputMode": output_mode,
        "outputBudget": output_budget,
        "pathChanged": path_changed,
        "dryRun": dry_run,
        "created": [str(path) for path in created],
        "wouldCreate": would_create,
        "sessionPowerShell": f'$env:PATH="{shim_dir};$env:PATH"',
        "sessionCmd": f'set PATH={shim_dir};%PATH%',
        "tools": names,
    }
    if not dry_run:
        write_state(resolved_home, payload)
    return payload


def disable(*, scope: str = "user", home: pathlib.Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    resolved_home = (home or default_home()).resolve()
    shim_dir = default_shim_dir(resolved_home)
    if scope == "session":
        return {
            "ancpVersion": __version__,
            "scope": scope,
            "shimDirectory": str(shim_dir),
            "message": "Remove the ANCP shim directory from the current process PATH to disable this session.",
            "sessionPowerShell": "$env:PATH = ($env:PATH -split ';' | Where-Object { $_ -ne '" + str(shim_dir) + "' }) -join ';'",
        }
    if scope != "user":
        raise ValueError(f"unknown disable scope: {scope}")
    if os.name != "nt":
        raise RuntimeError("ancp disable --scope user currently supports Windows persistent PATH only")
    before = user_path_value()
    after = _remove_path_entry(before, shim_dir)
    changed = before != after
    if changed and not dry_run:
        set_user_path_value(after)
    payload = {
        "ancpVersion": __version__,
        "scope": scope,
        "shimDirectory": str(shim_dir),
        "pathChanged": changed,
        "dryRun": dry_run,
        "enabled": _path_contains(after, shim_dir),
    }
    if not dry_run:
        state = read_state(resolved_home)
        state.update({"enabled": False, "lastDisable": payload})
        write_state(resolved_home, state)
    return payload


def uninstall(*, home: pathlib.Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    resolved_home = (home or default_home()).resolve()
    shim_dir = default_shim_dir(resolved_home)
    disable_payload = disable(scope="user", home=resolved_home, dry_run=dry_run) if os.name == "nt" else {"scope": "user"}
    would_remove = shim_dir.exists()
    removed = False
    if would_remove:
        if not dry_run:
            shutil.rmtree(shim_dir)
            removed = True
    state_file = state_path(resolved_home)
    if state_file.exists() and not dry_run:
        state_file.unlink()
    return {
        "ancpVersion": __version__,
        "home": str(resolved_home),
        "shimDirectory": str(shim_dir),
        "disable": disable_payload,
        "wouldRemoveShimDirectory": would_remove,
        "removedShimDirectory": removed,
        "dryRun": dry_run,
    }


def status(*, home: pathlib.Path | None = None) -> dict[str, Any]:
    resolved_home = (home or default_home()).resolve()
    shim_dir = default_shim_dir(resolved_home)
    path_value = user_path_value() if os.name == "nt" else os.environ.get("PATH", "")
    shim_count = len(list(shim_dir.glob("*.cmd" if os.name == "nt" else "*"))) if shim_dir.exists() else 0
    installed = shim_count > 0
    return {
        "ancpVersion": __version__,
        "home": str(resolved_home),
        "shimDirectory": str(shim_dir),
        "installed": installed,
        "shimCount": shim_count,
        "enabledInUserPath": _path_contains(path_value, shim_dir),
        "state": read_state(resolved_home),
    }
