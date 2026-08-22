from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRecord,
    AssetRevision,
    AssetRevisionId,
    AssetRole,
    AssetStatus,
    LineageRef,
    PreservationPolicy,
    ProjectAssetReference,
    ProvenanceRef,
    ReuseScope,
)

ASSET_RECORD_SCHEMA = "kodepoia.asset-record"
ASSET_REVISION_SCHEMA = "kodepoia.asset-revision"
PROJECT_REFERENCE_SCHEMA = "kodepoia.project-asset-reference"
SCHEMA_VERSION = 1


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def manifest_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_content(path: Path, expected_sha256: str, expected_length: int, *, chunk_size: int = 1024 * 1024) -> None:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
            total += len(chunk)
    if total != expected_length:
        raise ValueError(f"Content length mismatch: expected {expected_length}, got {total}")
    actual = digest.hexdigest()
    if actual != expected_sha256.lower():
        raise ValueError(f"Content SHA-256 mismatch: expected {expected_sha256.lower()}, got {actual}")


def asset_record_document(record: AssetRecord) -> dict[str, Any]:
    return {
        "schema": ASSET_RECORD_SCHEMA,
        "version": SCHEMA_VERSION,
        "payload": {
            "asset_id": str(record.asset_id),
            "kind": record.kind.value,
            "display_name": record.display_name,
            "tags": list(record.tags),
            "current_revision_id": str(record.current_revision_id) if record.current_revision_id else None,
        },
    }


def asset_revision_document(revision: AssetRevision) -> dict[str, Any]:
    return {
        "schema": ASSET_REVISION_SCHEMA,
        "version": SCHEMA_VERSION,
        "payload": revision.manifest_payload(),
    }


def project_reference_document(reference: ProjectAssetReference) -> dict[str, Any]:
    return {
        "schema": PROJECT_REFERENCE_SCHEMA,
        "version": SCHEMA_VERSION,
        "payload": {
            "project_id": reference.project_id,
            "asset_id": str(reference.asset_id),
            "revision_id": str(reference.revision_id),
            "target_path": reference.target_path,
            "metadata": dict(sorted(reference.metadata.items())),
        },
    }


def _payload(document: dict[str, Any], expected_schema: str) -> dict[str, Any]:
    if document.get("schema") != expected_schema or document.get("version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported asset document schema/version: {document.get('schema')} v{document.get('version')}")
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Asset document payload must be an object")
    return payload


def load_asset_record(document: dict[str, Any]) -> AssetRecord:
    payload = _payload(document, ASSET_RECORD_SCHEMA)
    current = payload.get("current_revision_id")
    return AssetRecord(
        asset_id=AssetId(str(payload["asset_id"])),
        kind=AssetKind(str(payload["kind"])),
        display_name=str(payload["display_name"]),
        tags=tuple(str(value) for value in payload.get("tags", [])),
        current_revision_id=AssetRevisionId(str(current)) if current else None,
    )


def load_asset_revision(document: dict[str, Any]) -> AssetRevision:
    payload = _payload(document, ASSET_REVISION_SCHEMA)
    provenance = tuple(
        ProvenanceRef(
            source_kind=str(item["source_kind"]),
            locator=str(item["locator"]),
            evidence_sha256=str(item["evidence_sha256"]) if item.get("evidence_sha256") else None,
        )
        for item in payload.get("provenance", [])
    )
    lineage = tuple(
        LineageRef(
            input_revision_id=AssetRevisionId(str(item["input_revision_id"])),
            relation=str(item.get("relation", "input")),
            transform_id=str(item["transform_id"]) if item.get("transform_id") else None,
        )
        for item in payload.get("lineage", [])
    )
    return AssetRevision(
        asset_id=AssetId(str(payload["asset_id"])),
        revision_id=AssetRevisionId(str(payload["revision_id"])),
        role=AssetRole(str(payload["role"])),
        kind=AssetKind(str(payload["kind"])),
        content_sha256=str(payload["content_sha256"]),
        content_length=int(payload["content_length"]),
        reuse_scope=ReuseScope(str(payload["reuse_scope"])),
        preservation=PreservationPolicy(str(payload["preservation"])),
        provenance=provenance,
        lineage=lineage,
        status=AssetStatus(str(payload["status"])),
    )


def load_project_reference(document: dict[str, Any]) -> ProjectAssetReference:
    payload = _payload(document, PROJECT_REFERENCE_SCHEMA)
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("Project reference metadata must be an object")
    return ProjectAssetReference(
        project_id=str(payload["project_id"]),
        asset_id=AssetId(str(payload["asset_id"])),
        revision_id=AssetRevisionId(str(payload["revision_id"])),
        target_path=str(payload["target_path"]) if payload.get("target_path") is not None else None,
        metadata={str(key): str(value) for key, value in metadata.items()},
    )
