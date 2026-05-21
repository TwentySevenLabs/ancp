# Standards And Source Notes

This document records the standards and public references used when designing ANCP 1.0.

ANCP is not a clone of any one standard. It borrows the parts that are already solved and adds the agent-specific contracts that are missing.

## JSON Schema Draft 2020-12

ANCP schemas use JSON Schema Draft 2020-12.

Reference:

- https://json-schema.org/draft/2020-12

Why it matters:

- mature JSON validation model,
- supports reusable definitions,
- supports unevaluated property handling,
- supported by many validators,
- compatible with modern OpenAPI schema thinking.

## Language Server Protocol

ANCP borrows concepts from LSP diagnostics, locations, commands, and code actions, but it is not an editor protocol.

Reference:

- https://microsoft.github.io/language-server-protocol/

Why it matters:

- established cross-language tooling shape,
- strong fit for diagnostics and source positions,
- many language servers already exist,
- adapters can use LSP as an input source.

## SARIF 2.1.0

ANCP is designed to export static-analysis-like diagnostics to SARIF.

Reference:

- https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html

Why it matters:

- mature static analysis result interchange,
- supported by GitHub code scanning and security tooling,
- useful for CI and compliance pipelines.

## JSON Patch

ANCP supports RFC 6902 JSON Patch only for JSON-like targets and metadata operations. Source-code edits use the ANCP text edit model because source files need ranges, anchors, and expected text.

Reference:

- https://www.rfc-editor.org/rfc/rfc6902.html

## JSON Canonicalization Scheme

ANCP recommends RFC 8785 JSON Canonicalization Scheme for deterministic hashing and signing of protocol documents.

Reference:

- https://www.rfc-editor.org/rfc/rfc8785.html

## SPDX

ANCP may reference SPDX identifiers for license and package metadata.

Reference:

- https://spdx.github.io/spdx-spec/v3.0.1/

## CycloneDX

ANCP may reference CycloneDX component identifiers and export dependency or SBOM-related facts.

Reference:

- https://cyclonedx.org/specification/overview

## Zero Language Article

The immediate design spark was the article on Zero's agent-facing toolchain: structured JSON diagnostics, stable codes, typed repair metadata, explain/fix commands, and version-matched agent guidance.

Reference:

- https://www.marktechpost.com/2026/05/17/vercel-labs-introduces-zero-a-systems-programming-language-designed-so-ai-agents-can-read-repair-and-ship-native-programs/

ANCP generalizes that idea over existing language ecosystems.

