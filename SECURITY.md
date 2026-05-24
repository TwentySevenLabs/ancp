# Security Policy

ANCP handles compiler, linter, build, and test commands. Those commands can execute project code, build scripts, package-manager hooks, and tests. The protocol therefore treats process execution and filesystem mutation as explicit effects, not background details.

## Supported Versions

| Version | Supported |
| --- | --- |
| 1.0.x | Yes |

## Reporting A Vulnerability

Before a public security contact exists, report issues privately to the repository owner through GitHub. After the project is published, enable GitHub private vulnerability reporting and update this file with the final contact path.

Please include:

- affected ANCP version,
- operating system,
- command or adapter involved,
- proof-of-concept input,
- expected behavior,
- observed behavior,
- whether the issue can execute commands, write files, leak paths, or bypass declared safety levels.

## Security Expectations

ANCP implementations must:

- preserve native command arguments unless explicitly configured,
- never run repair apply actions in plan mode,
- declare process, filesystem, network, and package-manager effects,
- report missing or failing tools honestly,
- avoid hiding native stdout/stderr/exit code,
- validate generated ANCP documents,
- avoid sending source code or diagnostics to network services unless the user explicitly configures that behavior.

## Reference Implementation Scope

The Python reference implementation runs local native tools and writes local JSON/Markdown artifacts. It does not intentionally upload source code, diagnostics, or generated documents.

Compiler-name shims execute the real compiler later in `PATH`. Users should prepend only trusted shim directories and should review project build/test scripts before running commands in untrusted repositories.
