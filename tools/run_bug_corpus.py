#!/usr/bin/env python3
"""Run ANCP adapters against intentionally buggy sample programs."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from ancp.documents import envelope, workspace_object


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / ".ancp" / "bug-corpus"


CASES = [
    ("python", ROOT / "examples/buggy/python", ["ancp", "check", "--workspace", ".", "--language", "python"]),
    ("typescript", ROOT / "examples/buggy/typescript", ["ancp", "check", "--workspace", ".", "--language", "typescript"]),
    ("rust", ROOT / "examples/buggy/rust", ["ancp", "check", "--workspace", ".", "--language", "rust"]),
    ("go", ROOT / "examples/buggy/go", ["ancp", "check", "--workspace", ".", "--language", "go"]),
    ("c-cpp-c", ROOT / "examples/buggy/c", ["ancp", "check", "--workspace", ".", "--language", "c-cpp"]),
    ("c-cpp-cpp", ROOT / "examples/buggy/cpp", ["ancp", "check", "--workspace", ".", "--language", "c-cpp"]),
    ("java", ROOT / "examples/buggy/java", ["ancp", "check", "--workspace", ".", "--language", "java"]),
    ("kotlin", ROOT / "examples/buggy/kotlin", ["ancp", "check", "--workspace", ".", "--language", "kotlin"]),
    ("julia", ROOT / "examples/buggy/julia", ["ancp", "check", "--workspace", ".", "--language", "julia"]),
    ("csharp", ROOT / "examples/buggy/csharp", ["ancp", "check", "--workspace", ".", "--language", "csharp"]),
    ("swift", ROOT / "examples/buggy/swift", ["ancp", "check", "--workspace", ".", "--language", "swift"]),
    ("zig", ROOT / "examples/buggy/zig", ["ancp", "check", "--workspace", ".", "--language", "zig"]),
    ("ruby", ROOT / "examples/buggy/ruby", ["ancp", "check", "--workspace", ".", "--language", "ruby"]),
    ("php", ROOT / "examples/buggy/php", ["ancp", "check", "--workspace", ".", "--language", "php"]),
    ("dart", ROOT / "examples/buggy/dart", ["ancp", "check", "--workspace", ".", "--language", "dart"]),
    ("scala", ROOT / "examples/buggy/scala", ["ancp", "check", "--workspace", ".", "--language", "scala"]),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report_entries = []
    steps = []
    total_diagnostics = 0
    invalid_json = False
    for name, cwd, argv in CASES:
        proc = subprocess.run(argv, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        out_file = OUT / f"{name}.json"
        md_file = OUT / f"{name}.md"
        out_file.write_text(proc.stdout, encoding="utf-8")
        render = subprocess.run(["ancp", "render", "--from", str(out_file)], cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        md_file.write_text(render.stdout, encoding="utf-8")
        try:
            document = json.loads(proc.stdout)
            diagnostics = len(document.get("diagnostics", []))
            status = document.get("status")
        except json.JSONDecodeError:
            invalid_json = True
            diagnostics = 0
            status = "invalid-json"
        total_diagnostics += diagnostics
        report_entries.append(
            {
                "name": name,
                "cwd": str(cwd),
                "exitCode": proc.returncode,
                "status": status,
                "diagnostics": diagnostics,
                "json": str(out_file),
                "markdown": str(md_file),
                "stderr": proc.stderr[-1000:],
            }
        )
        steps.append(
            {
                "name": f"Bug corpus: {name}",
                "argv": argv,
                "workingDirectory": str(cwd),
                "expectedStatus": "any",
                "produces": ["result.check"],
                "result": {
                    "status": status if status in {"passed", "failed", "partial", "tool_failed", "protocol_error"} else "protocol_error",
                    "exitCode": proc.returncode,
                    "summary": f"{diagnostics} diagnostics; status {status}.",
                },
            }
        )
        print(f"{name}: status={status} diagnostics={diagnostics} exit={proc.returncode}")
    report = envelope("result.verify", "ancp-bug-corpus")
    report.update(
        {
            "status": "protocol_error" if invalid_json else "passed",
            "workspace": workspace_object(ROOT),
            "verification": {
                "policy": "all",
                "steps": steps,
                "notes": "The corpus is intentionally broken. Passing means every case emitted parseable ANCP JSON; failed/tool_failed case statuses are expected depending on local tool availability.",
            },
            "diagnosticDelta": {
                "beforeCount": 0,
                "afterCount": total_diagnostics,
                "resolvedDiagnosticIds": [],
                "newDiagnosticIds": [],
                "unchangedDiagnosticIds": [],
            },
            "data": {
                "cases": report_entries,
                "summary": {
                    "cases": len(report_entries),
                    "diagnostics": total_diagnostics,
                    "invalidJson": invalid_json,
                    "toolFailedCases": sum(1 for item in report_entries if item["status"] == "tool_failed"),
                    "failedCasesWithDiagnostics": sum(1 for item in report_entries if item["status"] == "failed" and item["diagnostics"] > 0),
                },
            },
        }
    )
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT / 'report.json'}")
    return 1 if invalid_json else 0


if __name__ == "__main__":
    raise SystemExit(main())
