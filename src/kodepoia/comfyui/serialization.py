from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .errors import ComfyProtocolError, ComfyVersionError


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Encode a mapping with the deterministic JSON rules used by R9 identities."""
    try:
        text = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ComfyProtocolError("R9 canonical JSON payload is not serializable") from exc
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
        raise ComfyProtocolError("R9 envelope must contain exactly schema, version and payload")
    if document.get("schema") != expected_schema:
        raise ComfyProtocolError(f"Unexpected R9 schema: {document.get('schema')!r}")
    version = document.get("version")
    if version != supported_version:
        raise ComfyVersionError(
            f"Unsupported {expected_schema} version {version!r}; expected {supported_version}"
        )
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise ComfyProtocolError("R9 envelope payload must be an object")
    return dict(payload)
