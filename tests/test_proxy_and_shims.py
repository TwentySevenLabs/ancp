from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from ancp.cli import install_shims
from ancp.install import enable, status, uninstall, write_shims
from ancp.proxy import format_proxy_output
from ancp.proxy import proxy_document
from ancp.schema import validate_document
from ancp.shim import find_real_executable
from ancp.util import find_executable


def test_proxy_preserves_python_failure_and_emits_valid_ancp(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text("def broken(:\n    pass\n", encoding="utf-8")
    document, exit_code, stdout, stderr = proxy_document(
        "python",
        [sys.executable, "-m", "py_compile", str(source)],
        tmp_path,
        30,
    )
    assert exit_code != 0
    assert document["documentKind"] == "result.check"
    assert document["status"] in {"failed", "tool_failed"}
    assert validate_document(document) == []
    assert stdout == "" or isinstance(stdout, str)
    assert isinstance(stderr, str)
    raw = document["data"]["rawOutput"]
    assert Path(raw["combinedPath"]).exists()
    assert document["data"]["signalMetrics"]["estimatedNativeTokens"] >= 1
    assert document["data"]["signalMetrics"]["renderer"] == "raw-text"


def test_auto_compact_replaces_failure_output_with_minimal_signal(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text("def broken(:\n    pass\n", encoding="utf-8")
    document, _, stdout, stderr = proxy_document(
        "python",
        [sys.executable, "-m", "py_compile", str(source)],
        tmp_path,
        30,
    )
    compact_stdout, compact_stderr = format_proxy_output(document, stdout, stderr, "auto-compact", 120)
    assert compact_stderr == ""
    assert "ANCP result.check failed" in compact_stdout
    assert "code=ancp.diag.syntax.invalid" in compact_stdout
    assert "SyntaxError" in compact_stdout
    assert "File \"" not in compact_stdout


def test_install_shims_creates_native_names(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bin"
    created = install_shims(shim_dir, force=True, output_mode="auto-compact", output_budget=800)
    assert created
    if os.name == "nt":
        assert (shim_dir / "cargo.cmd").exists()
        assert (shim_dir / "python.cmd").exists()
        assert "ANCP_OUTPUT_MODE=auto-compact" in (shim_dir / "python.cmd").read_text(encoding="utf-8")
    else:
        assert (shim_dir / "cargo").exists()
        assert (shim_dir / "python").exists()
        assert "ANCP_OUTPUT_MODE=\"auto-compact\"" in (shim_dir / "python").read_text(encoding="utf-8")


def test_enable_dry_run_profiles_global_shims_without_mutating_path(tmp_path: Path) -> None:
    payload = enable(home=tmp_path / "ancp-home", profile="agent", dry_run=True)
    assert payload["dryRun"] is True
    assert payload["enabled"] is False
    assert payload["wouldEnable"] is True
    assert payload["outputMode"] == "auto-compact"
    assert "python" in payload["tools"]
    assert "powershell" not in payload["tools"]
    assert payload["wouldCreate"]
    assert not (tmp_path / "ancp-home" / "bin").exists()


def test_uninstall_dry_run_reports_without_removing_shims(tmp_path: Path) -> None:
    home = tmp_path / "ancp-home"
    shim_dir = home / "bin"
    write_shims(shim_dir, force=True, names=["python"], output_mode="auto-compact")
    payload = uninstall(home=home, dry_run=True)
    assert payload["dryRun"] is True
    assert payload["wouldRemoveShimDirectory"] is True
    assert payload["removedShimDirectory"] is False
    assert (shim_dir / ("python.cmd" if os.name == "nt" else "python")).exists()


def test_status_requires_at_least_one_shim(tmp_path: Path) -> None:
    home = tmp_path / "ancp-home"
    (home / "bin").mkdir(parents=True)
    payload = status(home=home)
    assert payload["shimCount"] == 0
    assert payload["installed"] is False


def test_find_real_executable_skips_other_ancp_shims(tmp_path: Path, monkeypatch) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    real = tmp_path / "real"
    first.mkdir()
    second.mkdir()
    real.mkdir()
    if os.name == "nt":
        (first / "python.cmd").write_text('@echo off\npython -m ancp.shim python %*\n', encoding="utf-8")
        (second / "python.cmd").write_text('@echo off\npython -m ancp.shim python %*\n', encoding="utf-8")
        real_python = real / "python.exe"
    else:
        (first / "python").write_text('#!/usr/bin/env sh\nexec python -m ancp.shim python "$@"\n', encoding="utf-8")
        (second / "python").write_text('#!/usr/bin/env sh\nexec python -m ancp.shim python "$@"\n', encoding="utf-8")
        real_python = real / "python"
    real_python.write_text("", encoding="utf-8")
    monkeypatch.setenv("PATH", os.pathsep.join([str(first), str(second), str(real)]))
    assert find_real_executable("python", [first]) == str(real_python)
    assert find_executable("python") == str(real_python)
