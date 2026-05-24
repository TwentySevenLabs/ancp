from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from ancp.cli import install_shims
from ancp.proxy import proxy_document
from ancp.schema import validate_document


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

