"""Built-in ANCP adapters."""

from __future__ import annotations

from .registry import ADAPTERS, get_adapter, matching_adapters

__all__ = ["ADAPTERS", "get_adapter", "matching_adapters"]

