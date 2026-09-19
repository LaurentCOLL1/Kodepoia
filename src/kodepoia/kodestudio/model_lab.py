from __future__ import annotations

import hashlib
import importlib.util
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from kodepoia.kodestudio.model_manager import (
    OllamaModelManager,
    saved_model_roles,
    saved_ollama_base_url,
)
from kodepoia.kodestudio.preferences import ApplicationPreferences, DEFAULT_SETTINGS_PATH
from kodepoia.tuning.model_registry import SpecializedModelVersion


MODEL_LAB_SCHEMA = "kodepoia.v2.3.1.model-lab"
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_EVIDENCE_FILES = 512
_EVIDENCE_ROOTS: tuple[tuple[str, str], ...] = (
    ("experience", ".kodepoia/experience"),
    ("dataset", ".kodepoia/datasets"),
    ("benchmark", ".kodepoia/benchmarks"),
    ("tuning", ".kodepoia/tuning"),
)
_REGISTRY_PATHS = (
    ".kodepoia/models/specialized.json",
    ".kodepoia/model-registry.json",
)
_LINEAGE_KEYS = (
    "dataset_digest",
    "manifest_digest",
    "training_plan_digest",
    "plan_digest",
    "evaluation_digest",
    "adapter_digest",
    "base_digest",
    "base_model_digest",
    "export_digest",
    "conversion_digest",
    "package_digest",
)
_ID_KEYS = (
    "dataset_id",
    "run_id",
    "candidate_id",
    "version_id",
    "report_id",
    "plan_id",
    "artifact_id",
    "model_id",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return "<external-path>"


def _state_from_payload(payload: Mapping[str, object]) -> str:
    for key in ("state", "status", "disposition"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            normalized = value.strip().lower().replace(" ", "_")
            if normalized in {
                "stale",
                "invalidated",
                "tampered",
                "quarantined",
                "unavailable",
                "blocked",
                "cancelled",
                "failed",
                "rejected",
                "retired",
                "active",
                "candidate",
                "completed",
                "ready",
                "ok",
                "pass",
            }:
                return normalized
    return "ready"


def _evidence_id(payload: Mapping[str, object], path: Path, digest: str) -> str:
    for key in _ID_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("report_digest", "record_digest", "digest", "evidence_sha256"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{path.stem}:{digest[:12]}"


def _schema_name(payload: Mapping[str, object], path: Path) -> str:
    schema = payload.get("schema")
    if isinstance(schema, str) and schema.strip():
        return schema.strip()
    return path.stem


def _lineage_pairs(payload: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    pairs: set[tuple[str, str]] = set()

    def visit(value: object, *, prefix: str = "") -> None:
        if isinstance(value, Mapping):
            for raw_key, item in value.items():
                key = str(raw_key)
                qualified = f"{prefix}.{key}" if prefix else key
                if key in _LINEAGE_KEYS and isinstance(item, str) and item.strip():
                    pairs.add((qualified, item.strip()))
                elif key == "lineage" and isinstance(item, Mapping):
                    for lineage_key, lineage_digest in item.items():
                        if isinstance(lineage_digest, str) and lineage_digest.strip():
                            pairs.add((str(lineage_key), lineage_digest.strip()))
                elif isinstance(item, Mapping):
                    visit(item, prefix=qualified)
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    visit(item, prefix=f"{prefix}[{index}]" if prefix else f"[{index}]")

    visit(payload)
    return tuple(sorted(pairs))


class ModelLabInventoryService:
    """Read-only V2.3.1 inventory facade over accepted R15 evidence stores.

    The service never creates missing R15 stores and never exposes a mutation
    method. Optional Ollama/Kaggle probes are executed only by runtime_snapshot().
    """

    schema = MODEL_LAB_SCHEMA

    def __init__(
        self,
        project_root: Path,
        *,
        preferences: ApplicationPreferences | None = None,
        ollama_snapshot_provider: Callable[[], Mapping[str, object]] | None = None,
        kaggle_doctor_provider: Callable[[], Mapping[str, object]] | None = None,
        kaggle_quota_provider: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        self.root = Path(project_root).resolve(strict=False)
        self.preferences = preferences or ApplicationPreferences(DEFAULT_SETTINGS_PATH)
        self._ollama_snapshot_provider = ollama_snapshot_provider
        self._kaggle_doctor_provider = kaggle_doctor_provider
        self._kaggle_quota_provider = kaggle_quota_provider

    @classmethod
    def for_project(cls, project_root: Path) -> "ModelLabInventoryService":
        return cls(project_root)

    def _read_json_record(self, path: Path, category: str) -> dict[str, object]:
        relative = _relative(self.root, path)
        try:
            size = path.stat().st_size
        except OSError as exc:
            return {
                "category": category,
                "kind": path.stem,
                "evidence_id": path.stem,
                "state": "unavailable",
                "path": relative,
                "bytes": None,
                "sha256": None,
                "schema": None,
                "lineage": [],
                "detail": str(exc),
            }
        if size > _MAX_JSON_BYTES:
            return {
                "category": category,
                "kind": path.stem,
                "evidence_id": path.stem,
                "state": "unavailable",
                "path": relative,
                "bytes": size,
                "sha256": None,
                "schema": None,
                "lineage": [],
                "detail": "bounded reader refused oversized JSON evidence",
            }
        try:
            raw_bytes = path.read_bytes()
            digest = hashlib.sha256(raw_bytes).hexdigest()
            payload = json.loads(raw_bytes.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return {
                "category": category,
                "kind": path.stem,
                "evidence_id": path.stem,
                "state": "invalid",
                "path": relative,
                "bytes": size,
                "sha256": None,
                "schema": None,
                "lineage": [],
                "detail": f"invalid JSON evidence: {exc}",
            }
        if not isinstance(payload, dict):
            return {
                "category": category,
                "kind": path.stem,
                "evidence_id": path.stem,
                "state": "invalid",
                "path": relative,
                "bytes": size,
                "sha256": digest,
                "schema": None,
                "lineage": [],
                "detail": "JSON evidence root is not an object",
            }
        lineage = _lineage_pairs(payload)
        return {
            "category": category,
            "kind": _schema_name(payload, path),
            "evidence_id": _evidence_id(payload, path, digest),
            "state": _state_from_payload(payload),
            "path": relative,
            "bytes": size,
            "sha256": digest,
            "schema": payload.get("schema"),
            "lineage": [{"key": key, "digest": value} for key, value in lineage],
            "detail": "",
        }

    def _evidence_snapshot(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        records: list[dict[str, object]] = []
        stores: list[dict[str, object]] = []
        remaining = _MAX_EVIDENCE_FILES
        for category, relative in _EVIDENCE_ROOTS:
            directory = self.root / relative
            if not directory.exists():
                stores.append(
                    {
                        "category": category,
                        "path": relative,
                        "state": "missing",
                        "file_count": 0,
                    }
                )
                continue
            if not directory.is_dir():
                stores.append(
                    {
                        "category": category,
                        "path": relative,
                        "state": "invalid",
                        "file_count": 0,
                    }
                )
                continue
            json_files = sorted(
                (item for item in directory.rglob("*.json") if item.is_file()),
                key=lambda item: item.as_posix(),
            )
            bounded = json_files[:remaining]
            stores.append(
                {
                    "category": category,
                    "path": relative,
                    "state": "ready",
                    "file_count": len(json_files),
                    "truncated": len(json_files) > len(bounded),
                }
            )
            records.extend(self._read_json_record(path, category) for path in bounded)
            remaining -= len(bounded)
            if remaining <= 0:
                break
        return records, stores

    def _registry_snapshot(self) -> dict[str, object]:
        selected: Path | None = None
        for relative in _REGISTRY_PATHS:
            candidate = self.root / relative
            if candidate.is_file():
                selected = candidate
                break
        if selected is None:
            return {
                "state": "missing",
                "path": _REGISTRY_PATHS[0],
                "sha256": None,
                "records": [],
                "active_roles": {},
                "rollback_roles": {},
                "detail": "specialized-model registry is not present",
            }
        relative = _relative(self.root, selected)
        try:
            raw_bytes = selected.read_bytes()
            digest = hashlib.sha256(raw_bytes).hexdigest()
            document = json.loads(raw_bytes.decode("utf-8"))
            if not isinstance(document, dict) or document.get("schema_version") != 1:
                raise ValueError("unsupported specialized-model registry schema")
            raw_records = document.get("records")
            active_roles = document.get("active_roles")
            rollback_roles = document.get("rollback_roles")
            if not isinstance(raw_records, dict):
                raise ValueError("malformed specialized-model registry records")
            if not isinstance(active_roles, dict) or not isinstance(rollback_roles, dict):
                raise ValueError("malformed specialized-model registry role mappings")
            records: list[dict[str, object]] = []
            for version_id, raw in sorted(raw_records.items()):
                if not isinstance(raw, dict):
                    raise ValueError("malformed specialized-model registry record")
                record = SpecializedModelVersion.from_document(raw)
                if version_id != record.version_id:
                    raise ValueError("registry key/version_id mismatch")
                records.append(
                    {
                        "version_id": record.version_id,
                        "candidate_id": record.candidate_id,
                        "state": record.state.value,
                        "disposition": record.disposition,
                        "base_model_id": record.base_model_id,
                        "base_digest": record.base_digest,
                        "roles": sorted(role.value for role in record.role_eligibility),
                        "domain_tags": sorted(record.domain_tags),
                        "preferred_variant": record.preferred_variant.value,
                        "record_digest": record.digest,
                        "lineage": [
                            {"key": key, "digest": lineage_digest}
                            for key, lineage_digest in sorted(record.lineage)
                        ],
                    }
                )
            return {
                "state": "ready",
                "path": relative,
                "sha256": digest,
                "records": records,
                "active_roles": dict(sorted((str(k), str(v)) for k, v in active_roles.items())),
                "rollback_roles": dict(sorted((str(k), v) for k, v in rollback_roles.items())),
                "detail": "",
            }
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            return {
                "state": "tampered",
                "path": relative,
                "sha256": _sha256_file(selected) if selected.is_file() else None,
                "records": [],
                "active_roles": {},
                "rollback_roles": {},
                "detail": str(exc),
            }

    @staticmethod
    def _dependency_capabilities() -> list[dict[str, str]]:
        modules = (
            ("torch", "PyTorch"),
            ("transformers", "Transformers"),
            ("accelerate", "Accelerate"),
            ("datasets", "Datasets"),
            ("peft", "PEFT"),
            ("trl", "TRL"),
            ("bitsandbytes", "bitsandbytes"),
            ("kaggle", "Kaggle CLI package"),
        )
        return [
            {
                "capability": label,
                "state": "available" if importlib.util.find_spec(module) is not None else "unavailable",
                "detail": module,
            }
            for module, label in modules
        ]

    def snapshot(self) -> dict[str, object]:
        evidence, stores = self._evidence_snapshot()
        registry = self._registry_snapshot()
        roles = saved_model_roles(self.preferences)

        lineage: list[dict[str, str]] = []
        for item in evidence:
            target = str(item.get("evidence_id", ""))
            for edge in item.get("lineage", []):
                if isinstance(edge, Mapping):
                    lineage.append(
                        {
                            "source": str(edge.get("key", "")),
                            "digest": str(edge.get("digest", "")),
                            "target": target,
                            "target_kind": str(item.get("category", "evidence")),
                        }
                    )
        for record in registry.get("records", []):
            if isinstance(record, Mapping):
                target = str(record.get("version_id", ""))
                for edge in record.get("lineage", []):
                    if isinstance(edge, Mapping):
                        lineage.append(
                            {
                                "source": str(edge.get("key", "")),
                                "digest": str(edge.get("digest", "")),
                                "target": target,
                                "target_kind": "model_registry",
                            }
                        )

        return {
            "schema": self.schema,
            "status": "ok",
            "read_only": True,
            "project_root": ".",
            "stores": stores,
            "evidence": sorted(
                evidence,
                key=lambda item: (
                    str(item.get("category", "")),
                    str(item.get("evidence_id", "")),
                    str(item.get("path", "")),
                ),
            ),
            "registry": registry,
            "ollama": {
                "state": "not_checked",
                "base_url": saved_ollama_base_url(self.preferences),
                "models": [],
                "roles": roles,
                "detail": "runtime inventory is refreshed only on explicit request",
            },
            "kaggle": {
                "state": "not_checked",
                "doctor": None,
                "quota": None,
                "detail": "Kaggle state is refreshed only on explicit request",
            },
            "capabilities": self._dependency_capabilities(),
            "lineage": sorted(
                lineage,
                key=lambda edge: (
                    edge["target_kind"],
                    edge["target"],
                    edge["source"],
                    edge["digest"],
                ),
            ),
            "mutations": {
                "dataset_build": False,
                "training": False,
                "conversion": False,
                "promotion": False,
                "rollback": False,
            },
        }

    def runtime_snapshot(self) -> dict[str, object]:
        if self._ollama_snapshot_provider is None:
            ollama_provider: Callable[[], Mapping[str, object]] = OllamaModelManager(
                self.preferences
            ).snapshot
        else:
            ollama_provider = self._ollama_snapshot_provider

        if self._kaggle_doctor_provider is None:
            from kodepoia.tuning.kaggle_remote import KaggleRemoteTrainer

            kaggle_doctor_provider: Callable[[], Mapping[str, object]] = (
                lambda: KaggleRemoteTrainer().doctor().to_dict()
            )
        else:
            kaggle_doctor_provider = self._kaggle_doctor_provider

        if self._kaggle_quota_provider is None:
            from kodepoia.kodestudio.kaggle_quota import KaggleQuotaService

            kaggle_quota_provider: Callable[[], Mapping[str, object]] = (
                lambda: KaggleQuotaService().snapshot().to_dict()
            )
        else:
            kaggle_quota_provider = self._kaggle_quota_provider

        roles = saved_model_roles(self.preferences)
        try:
            ollama_raw = dict(ollama_provider())
            ollama = {
                "state": "ready",
                "base_url": str(ollama_raw.get("base_url", saved_ollama_base_url(self.preferences))),
                "version": ollama_raw.get("version"),
                "models": sorted(
                    (str(item) for item in ollama_raw.get("models", []) if str(item).strip()),
                    key=str.casefold,
                ),
                "roles": roles,
                "detail": "",
            }
        except Exception as exc:
            ollama = {
                "state": "unavailable",
                "base_url": saved_ollama_base_url(self.preferences),
                "version": None,
                "models": [],
                "roles": roles,
                "detail": str(exc),
            }

        try:
            doctor = dict(kaggle_doctor_provider())
            doctor_ready = bool(doctor.get("ready"))
            kaggle_state = "ready" if doctor_ready else "unavailable"
            kaggle_detail = str(doctor.get("detail", ""))
        except Exception as exc:
            doctor = None
            kaggle_state = "unavailable"
            kaggle_detail = str(exc)

        try:
            quota = dict(kaggle_quota_provider())
        except Exception as exc:
            quota = None
            if kaggle_detail:
                kaggle_detail += f"; quota: {exc}"
            else:
                kaggle_detail = f"quota: {exc}"

        return {
            "schema": self.schema,
            "status": "ok",
            "read_only": True,
            "ollama": ollama,
            "kaggle": {
                "state": kaggle_state,
                "doctor": doctor,
                "quota": quota,
                "detail": kaggle_detail,
            },
        }


__all__ = ["MODEL_LAB_SCHEMA", "ModelLabInventoryService"]
