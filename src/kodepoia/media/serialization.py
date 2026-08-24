from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


class MediaProtocolError(ValueError):
    pass


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MediaProtocolError("R11 canonical JSON payload is not serializable") from exc
    return text.encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def make_envelope(*, schema: str, version: int, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, str) or not schema.startswith("kodepoia.r11."):
        raise ValueError("R11 schema name must start with kodepoia.r11.")
    if version != 1:
        raise ValueError("R11.1 supports schema version 1 only")
    return {"schema": schema, "version": version, "payload": dict(payload)}


def parse_envelope(document: Mapping[str, Any], *, expected_schema: str) -> dict[str, Any]:
    if set(document) != {"schema", "version", "payload"}:
        raise MediaProtocolError("R11 envelope must contain exactly schema, version and payload")
    if document.get("schema") != expected_schema or document.get("version") != 1:
        raise MediaProtocolError("Unexpected R11 schema/version")
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise MediaProtocolError("R11 payload must be an object")
    return dict(payload)
