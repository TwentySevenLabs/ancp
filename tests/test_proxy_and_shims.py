from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from ancp.cli import install_shims
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


def test_install_shims_creates_native_names(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bin"
    created = install_shims(shim_dir, force=True)
    assert created
    if os.name == "nt":
      assert (shim_dir / "cargo.cmd").exists()
      assert (shim_dir / "python.cmd").exists()
    else:
      assert (shim_dir / "cargo").exists()
      assert (shim_dir / "python").exists()


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
