from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.models.router import ModelRegistry, ModelRole, ModelSpec

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_PROMOTABLE = "PROMOTE_TO_EXPORT"


class ModelArtifactKind(StrEnum):
    BASE = "base"
    ADAPTER = "adapter"
    GGUF = "gguf"
    OLLAMA = "ollama"


class ModelVersionState(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    REJECTED = "rejected"
    RETIRED = "retired"


def _stable_id(value: str, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _sha(value: str, field: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256 hex")
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ModelArtifactVariant:
    kind: ModelArtifactKind
    artifact_id: str
    digest: str
    runtime_ref: str | None = None
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.artifact_id, "artifact_id")
        _sha(self.digest, "artifact digest")
        if self.runtime_ref is not None and (
            not isinstance(self.runtime_ref, str) or not self.runtime_ref.strip()
        ):
            raise ValueError("runtime_ref must be non-empty text when provided")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("capabilities must be unique")
        for capability in self.capabilities:
            _stable_id(capability, "capability")

    def canonical(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "artifact_id": self.artifact_id,
            "digest": self.digest,
            "runtime_ref": self.runtime_ref,
            "capabilities": sorted(self.capabilities),
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> ModelArtifactVariant:
        return cls(
            kind=ModelArtifactKind(value["kind"]),
            artifact_id=str(value["artifact_id"]),
            digest=str(value["digest"]),
            runtime_ref=value.get("runtime_ref"),
            capabilities=tuple(value.get("capabilities", ())),
        )


@dataclass(frozen=True, slots=True)
class SpecializedModelVersion:
    version_id: str
    candidate_id: str
    state: ModelVersionState
    disposition: str
    base_model_id: str
    base_digest: str
    lineage: tuple[tuple[str, str], ...]
    role_eligibility: tuple[ModelRole, ...]
    domain_tags: tuple[str, ...]
    variants: tuple[ModelArtifactVariant, ...]
    preferred_variant: ModelArtifactKind

    def __post_init__(self) -> None:
        _stable_id(self.version_id, "version_id")
        _stable_id(self.candidate_id, "candidate_id")
        _stable_id(self.base_model_id, "base_model_id")
        _sha(self.base_digest, "base_digest")
        if not isinstance(self.disposition, str) or not self.disposition:
            raise ValueError("disposition is required")
        keys = [key for key, _ in self.lineage]
        if len(keys) != len(set(keys)):
            raise ValueError("lineage keys must be unique")
        for key, digest in self.lineage:
            _stable_id(key, "lineage key")
            _sha(digest, f"lineage {key}")
        if not self.role_eligibility:
            raise ValueError("at least one role must be eligible")
        if len(set(self.role_eligibility)) != len(self.role_eligibility):
            raise ValueError("role eligibility must be unique")
        if len(set(self.domain_tags)) != len(self.domain_tags):
            raise ValueError("domain tags must be unique")
        for tag in self.domain_tags:
            _stable_id(tag, "domain tag")
        if not self.variants:
            raise ValueError("at least one artifact variant is required")
        kinds = [variant.kind for variant in self.variants]
        if len(kinds) != len(set(kinds)):
            raise ValueError("artifact variant kinds must be unique")
        if self.preferred_variant not in kinds:
            raise ValueError("preferred variant must exist")
        if self.state is ModelVersionState.ACTIVE and self.disposition != _PROMOTABLE:
            raise ValueError("active model must have promotable disposition")

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical_bytes(self.canonical())).hexdigest()

    def variant(
        self, kind: ModelArtifactKind | None = None
    ) -> ModelArtifactVariant:
        wanted = kind or self.preferred_variant
        for variant in self.variants:
            if variant.kind is wanted:
                return variant
        raise KeyError(wanted.value)

    def with_state(self, state: ModelVersionState) -> SpecializedModelVersion:
        return SpecializedModelVersion(
            version_id=self.version_id,
            candidate_id=self.candidate_id,
            state=state,
            disposition=self.disposition,
            base_model_id=self.base_model_id,
            base_digest=self.base_digest,
            lineage=self.lineage,
            role_eligibility=self.role_eligibility,
            domain_tags=self.domain_tags,
            variants=self.variants,
            preferred_variant=self.preferred_variant,
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "candidate_id": self.candidate_id,
            "state": self.state.value,
            "disposition": self.disposition,
            "base_model_id": self.base_model_id,
            "base_digest": self.base_digest,
            "lineage": {key: digest for key, digest in sorted(self.lineage)},
            "role_eligibility": sorted(role.value for role in self.role_eligibility),
            "domain_tags": sorted(self.domain_tags),
            "variants": [
                variant.canonical()
                for variant in sorted(self.variants, key=lambda item: item.kind.value)
            ],
            "preferred_variant": self.preferred_variant.value,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> SpecializedModelVersion:
        record = cls(
            version_id=str(value["version_id"]),
            candidate_id=str(value["candidate_id"]),
            state=ModelVersionState(value["state"]),
            disposition=str(value["disposition"]),
            base_model_id=str(value["base_model_id"]),
            base_digest=str(value["base_digest"]),
            lineage=tuple(
                sorted(
                    (str(key), str(digest))
                    for key, digest in value["lineage"].items()
                )
            ),
            role_eligibility=tuple(
                ModelRole(role) for role in value["role_eligibility"]
            ),
            domain_tags=tuple(value.get("domain_tags", ())),
            variants=tuple(
                ModelArtifactVariant.from_document(item) for item in value["variants"]
            ),
            preferred_variant=ModelArtifactKind(value["preferred_variant"]),
        )
        if value.get("record_digest") != record.digest:
            raise ValueError("registry record digest mismatch")
        return record

    def persisted(self) -> dict[str, Any]:
        value = self.canonical()
        value["record_digest"] = self.digest
        return value


AuditSink = Callable[[dict[str, Any]], None]
HealthProbe = Callable[[ModelRole, SpecializedModelVersion, ModelArtifactVariant], bool]
RuntimeDigestResolver = Callable[[str], str]


class SpecializedModelRegistry:
    """Immutable-identity model promotion state compatible with the R3 router."""

    def __init__(
        self,
        path: Path,
        *,
        safe_change: SafeChangeManager | None = None,
        audit_sink: AuditSink | None = None,
    ) -> None:
        self.path = Path(path)
        self.safe_change = safe_change
        self.audit_sink = audit_sink or (lambda _event: None)
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write(self._empty())

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "schema_version": 1,
            "records": {},
            "active_roles": {},
            "rollback_roles": {},
        }

    def _read(self) -> dict[str, Any]:
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if value.get("schema_version") != 1:
            raise ValueError("unsupported specialized-model registry schema")
        required_maps = ("records", "active_roles", "rollback_roles")
        if not all(isinstance(value.get(key), dict) for key in required_maps):
            raise ValueError("malformed specialized-model registry")
        for version_id, raw in value["records"].items():
            record = SpecializedModelVersion.from_document(raw)
            if version_id != record.version_id:
                raise ValueError("registry key/version_id mismatch")
        for role, version_id in value["active_roles"].items():
            ModelRole(role)
            if version_id not in value["records"]:
                raise ValueError("active role points to missing model version")
        return value

    def _write(self, value: Mapping[str, Any]) -> None:
        payload = json.dumps(
            value, sort_keys=True, indent=2, ensure_ascii=False
        ) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", dir=self.path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def register(self, record: SpecializedModelVersion) -> None:
        document = self._read()
        current = document["records"].get(record.version_id)
        persisted = record.persisted()
        if current is not None and current != persisted:
            raise ValueError("immutable version_id already has different content")
        document["records"][record.version_id] = persisted
        self._write(document)
        self.audit_sink(
            {
                "event": "model_registry.register",
                "version_id": record.version_id,
                "record_digest": record.digest,
            }
        )

    def record(self, version_id: str) -> SpecializedModelVersion:
        _stable_id(version_id, "version_id")
        document = self._read()
        try:
            raw = document["records"][version_id]
        except KeyError as exc:
            raise KeyError(version_id) from exc
        return SpecializedModelVersion.from_document(raw)

    def active_version(self, role: ModelRole) -> SpecializedModelVersion | None:
        document = self._read()
        version_id = document["active_roles"].get(role.value)
        if version_id is None:
            return None
        return SpecializedModelVersion.from_document(document["records"][version_id])

    @staticmethod
    def _verify_runtime_identity(
        variant: ModelArtifactVariant,
        resolver: RuntimeDigestResolver | None,
    ) -> None:
        if variant.runtime_ref is None:
            return
        if resolver is None:
            raise ValueError("runtime digest resolver required for mutable runtime_ref")
        actual = resolver(variant.runtime_ref)
        _sha(actual, "resolved runtime digest")
        if actual != variant.digest:
            raise ValueError("mutable runtime reference digest drift detected")

    def promote(
        self,
        version_id: str,
        role: ModelRole,
        *,
        health_probe: HealthProbe,
        runtime_digest_resolver: RuntimeDigestResolver | None = None,
    ) -> str:
        before = self._read()
        record = SpecializedModelVersion.from_document(
            before["records"][version_id]
        )
        if record.state is ModelVersionState.REJECTED:
            raise ValueError("rejected candidate cannot be activated")
        if record.disposition != _PROMOTABLE:
            raise ValueError("candidate disposition does not authorize promotion")
        if role not in record.role_eligibility:
            raise ValueError("candidate is not eligible for requested role")
        variant = record.variant()
        self._verify_runtime_identity(variant, runtime_digest_resolver)
        prior_version = before["active_roles"].get(role.value)
        transaction = hashlib.sha256(
            _canonical_bytes(
                {
                    "role": role.value,
                    "prior": prior_version,
                    "next": version_id,
                    "digest": record.digest,
                }
            )
        ).hexdigest()
        if self.safe_change is not None:
            self.safe_change.snapshot([self.path])
        after = copy.deepcopy(before)
        if prior_version is not None and prior_version != version_id:
            old = SpecializedModelVersion.from_document(
                after["records"][prior_version]
            )
            after["records"][prior_version] = old.with_state(
                ModelVersionState.RETIRED
            ).persisted()
        after["records"][version_id] = record.with_state(
            ModelVersionState.ACTIVE
        ).persisted()
        after["active_roles"][role.value] = version_id
        after["rollback_roles"][role.value] = {
            "prior_version_id": prior_version,
            "promoted_version_id": version_id,
            "transaction_id": transaction,
        }
        self._write(after)
        if not health_probe(role, record, variant):
            self._write(before)
            self.audit_sink(
                {
                    "event": "model_registry.promotion_rolled_back",
                    "role": role.value,
                    "version_id": version_id,
                    "transaction_id": transaction,
                }
            )
            raise RuntimeError(
                "post-promotion health probe failed; exact mapping restored"
            )
        self.audit_sink(
            {
                "event": "model_registry.promoted",
                "role": role.value,
                "version_id": version_id,
                "transaction_id": transaction,
                "record_digest": record.digest,
            }
        )
        return transaction

    def rollback(self, role: ModelRole, *, health_probe: HealthProbe) -> str | None:
        before = self._read()
        point = before["rollback_roles"].get(role.value)
        if point is None:
            raise ValueError("no rollback point for role")
        active = before["active_roles"].get(role.value)
        if active != point["promoted_version_id"]:
            raise ValueError("active role no longer matches rollback point")
        prior = point["prior_version_id"]
        after = copy.deepcopy(before)
        promoted = SpecializedModelVersion.from_document(
            after["records"][active]
        )
        after["records"][active] = promoted.with_state(
            ModelVersionState.RETIRED
        ).persisted()
        if prior is None:
            after["active_roles"].pop(role.value, None)
        else:
            restored = SpecializedModelVersion.from_document(
                after["records"][prior]
            )
            restored_variant = restored.variant()
            if not health_probe(role, restored, restored_variant):
                raise RuntimeError("rollback target failed health probe")
            after["records"][prior] = restored.with_state(
                ModelVersionState.ACTIVE
            ).persisted()
            after["active_roles"][role.value] = prior
        after["rollback_roles"].pop(role.value, None)
        self._write(after)
        self.audit_sink(
            {
                "event": "model_registry.rollback",
                "role": role.value,
                "restored_version_id": prior,
                "transaction_id": point["transaction_id"],
            }
        )
        return prior

    def router_registry(self) -> ModelRegistry:
        document = self._read()
        models: list[ModelSpec] = []
        for role_name, version_id in sorted(document["active_roles"].items()):
            role = ModelRole(role_name)
            record = SpecializedModelVersion.from_document(
                document["records"][version_id]
            )
            variant = record.variant()
            caps = set(variant.capabilities)
            models.append(
                ModelSpec(
                    name=variant.runtime_ref or variant.artifact_id,
                    role=role,
                    supports_vision="vision" in caps,
                    supports_tools="tools" in caps,
                    supports_structured="structured" in caps,
                )
            )
        return ModelRegistry(models=models)
