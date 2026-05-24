"""ANCP schema loading and validation."""

from __future__ import annotations

import json
import pathlib
from importlib import resources
from typing import Any

import jsonschema


def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def schema_path() -> pathlib.Path | None:
    root_schema = project_root() / "schemas" / "ancp-1.0.schema.json"
    if root_schema.exists():
        return root_schema
    return None


def load_schema() -> dict[str, Any]:
    path = schema_path()
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    with resources.files("ancp").joinpath("resources/schemas/ancp-1.0.schema.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load_schema())


def validate_document(document: dict[str, Any]) -> list[str]:
    errors = sorted(validator().iter_errors(document), key=lambda err: list(err.path))
    messages: list[str] = []
    for error in errors:
        path = "/" + "/".join(str(part) for part in error.path)
        messages.append(f"{path}: {error.message}")
    return messages


def validate_path(path: pathlib.Path) -> list[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return validate_document(document)

