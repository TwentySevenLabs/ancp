"""Shared ANCP constants."""

from __future__ import annotations

ANCP_VERSION = "1.0.0"
SCHEMA_URI = "https://agent-native-compiler-protocol.org/schemas/ancp-1.0.schema.json"

CORE_PROFILES = ["core", "explain", "repair-plan", "verify", "graph", "effects", "skills", "export"]

CORE_DOCUMENT_KINDS = [
    "manifest.adapter",
    "manifest.capabilities",
    "result.check",
    "result.explain",
    "plan.repair",
    "result.apply",
    "result.verify",
    "graph.code",
    "result.skills",
]

SAFETY_AUTOMATIC = "automatic"
SAFETY_REVIEW = "review_required"
SAFETY_DANGEROUS = "dangerous"
SAFETY_UNSUPPORTED = "unsupported"

