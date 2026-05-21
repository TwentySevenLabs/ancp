# ANCP Overview

ANCP is the missing contract between existing programming toolchains and coding agents.

The protocol assumes a practical reality: most serious codebases will keep using TypeScript, Python, Rust, Go, Java, C++, and other existing languages. The path to agent-native development is not only new languages. It is a standard adapter protocol that makes current compilers and tools expose structured, stable, repair-oriented data.

## The Problem

Human-facing tool output is not enough for agents:

- compiler messages are often prose,
- message formats change,
- diagnostics point at lines that move,
- error codes are not normalized across languages,
- repair intent is implicit,
- quick fixes are tied to IDE-specific APIs,
- test failures are structurally different from type errors,
- agents cannot easily know whether a proposed command is safe,
- documentation may not match the installed tool version.

ANCP makes this explicit.

## The ANCP Loop

```text
discover -> check -> explain -> plan -> apply -> verify
```

The loop can stop early. A core adapter only needs discovery and check output. A richer adapter can produce explanations, repair plans, code graph facts, effects, and skills.

## What Agents Read

Agents should primarily read:

- `documentKind`
- `ancpVersion`
- `producer`
- `toolchain`
- `diagnostics[].canonicalCode`
- `diagnostics[].nativeCode`
- `diagnostics[].kind`
- `diagnostics[].primaryLocation`
- `diagnostics[].repairHints`
- `plan.repair.actions`
- `verification`

Agents should not parse human prose when stable fields are available.

## What Humans Read

Humans should primarily read:

- `message`
- `title`
- `explanation`
- `safetyLevel`
- `verification` summaries

ANCP keeps human-readable text, but text is not the operational contract.

## Why Not Just LSP?

LSP is excellent for editor-language-server interactions. It gives diagnostics, code actions, hover, references, and other language features. ANCP can consume LSP.

ANCP is different because it standardizes the agent repair loop:

- CLI-first operation for agents and CI,
- durable diagnostic envelopes,
- explicit repair hints,
- repair plans with safety metadata,
- verification result contracts,
- adapter profiles,
- effect/capability reporting,
- version-matched agent guidance.

## Why Not Just SARIF?

SARIF is excellent for static analysis interchange and code scanning. ANCP can export to SARIF.

ANCP is different because it covers compiler, test, build, repair, apply, verify, graph, and agent guidance workflows. It also has a repair-plan model, not only an analysis-result model.

## What Counts As Production Quality

For an ANCP adapter, production quality means:

- every JSON output validates against the schema,
- native tool versions are reported,
- native diagnostic codes are preserved,
- canonical codes are stable,
- locations include enough anchors to survive edits where possible,
- repair plans include preconditions,
- repair plans include verification steps,
- unsafe actions are not mislabeled as automatic,
- failed native tools still produce valid ANCP error documents,
- conformance tests pass.

