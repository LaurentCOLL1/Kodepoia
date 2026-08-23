from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .errors import BlenderProtocolError, BlenderVersionError


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise BlenderProtocolError("R10 canonical JSON payload is not serializable") from exc
    return text.encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def make_envelope(*, schema: str, version: int, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not schema.strip():
        raise ValueError("schema must be non-empty")
    if version < 1:
        raise ValueError("version must be >= 1")
    return {"schema": schema, "version": version, "payload": dict(payload)}


def parse_envelope(
    document: Mapping[str, Any],
    *,
    expected_schema: str,
    supported_version: int = 1,
) -> dict[str, Any]:
    if set(document) != {"schema", "version", "payload"}:
        raise BlenderProtocolError("R10 envelope must contain exactly schema, version and payload")
    if document.get("schema") != expected_schema:
        raise BlenderProtocolError(f"Unexpected R10 schema: {document.get('schema')!r}")
    version = document.get("version")
    if version != supported_version:
        raise BlenderVersionError(
            f"Unsupported {expected_schema} version {version!r}; expected {supported_version}"
        )
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise BlenderProtocolError("R10 envelope payload must be an object")
    return dict(payload)
