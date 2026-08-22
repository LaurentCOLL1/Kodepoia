from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

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
    ProvenanceRef,
    ReuseScope,
)
from kodepoia.assets.serialization import asset_record_document, asset_revision_document, canonical_json, verify_content
from kodepoia.assets.store import VaultStore
from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch


class DeterminismState(StrEnum):
    DETERMINISTIC = "deterministic"
    SEEDED = "seeded"
    NONDETERMINISTIC = "nondeterministic"


class CacheState(StrEnum):
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"
    CORRUPT = "corrupt"


@dataclass(frozen=True, slots=True)
class ToolIdentity:
    name: str
    version: str
    build_identity: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.version.strip():
            raise ValueError("Tool name and version must be non-empty")

    def canonical(self) -> dict[str, str | None]:
        return {"name": self.name, "version": self.version, "build_identity": self.build_identity}


@dataclass(frozen=True, slots=True)
class TransformRecipe:
    transform_id: str
    schema_version: int
    parameters: dict[str, Any]
    output_kind: AssetKind
    determinism: DeterminismState = DeterminismState.DETERMINISTIC
    seed: int | None = None

    def __post_init__(self) -> None:
        if not self.transform_id.strip():
            raise ValueError("transform_id must be non-empty")
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if self.determinism is DeterminismState.SEEDED and self.seed is None:
            raise ValueError("Seeded recipes require a seed")
        canonical_json(self.parameters)

    def canonical(self) -> dict[str, Any]:
        return {
            "transform_id": self.transform_id,
            "schema_version": self.schema_version,
            "parameters": self.parameters,
            "output_kind": self.output_kind.value,
            "determinism": self.determinism.value,
            "seed": self.seed,
        }


class TransformAdapter(Protocol):
    transform_id: str
    tool_identity: ToolIdentity

    def execute(self, inputs: tuple[Path, ...], output_dir: Path, parameters: dict[str, Any]) -> tuple[Path, ...]: ...


@dataclass(frozen=True, slots=True)
class TransformResult:
    cache_key: str
    cache_state: CacheState
    output_revision_ids: tuple[AssetRevisionId, ...]


class TransformRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, TransformAdapter] = {}

    def register(self, adapter: TransformAdapter) -> None:
        transform_id = adapter.transform_id.strip()
        if not transform_id:
            raise ValueError("Transform adapter ID must be non-empty")
        if transform_id in self._adapters:
            raise ValueError(f"Transform already registered: {transform_id}")
        self._adapters[transform_id] = adapter

    def get(self, transform_id: str) -> TransformAdapter:
        try:
            return self._adapters[transform_id]
        except KeyError as exc:
            raise LookupError(f"Unknown registered transform: {transform_id}") from exc


class DeterministicTextTransform:
    """Small pure-Python transform used as deterministic CI acceptance evidence."""

    transform_id = "fixture.text-uppercase.v1"
    tool_identity = ToolIdentity("kodepoia-fixture-transform", "1")

    def execute(self, inputs: tuple[Path, ...], output_dir: Path, parameters: dict[str, Any]) -> tuple[Path, ...]:
        if len(inputs) != 1:
            raise ValueError("fixture.text-uppercase.v1 requires exactly one input")
        suffix = str(parameters.get("suffix", ""))
        text = inputs[0].read_text(encoding="utf-8")
        output = output_dir / "output.txt"
        output.write_text(text.upper() + suffix, encoding="utf-8", newline="\n")
        return (output,)


class TransformService:
    """Reproducible transform orchestration over immutable Vault revisions.

    Callers select a registered transform ID and typed JSON parameters. They do
    not supply executable names, argv, cwd or process environment. External
    process adapters added in later phases must own fixed ProcessSandbox launch
    templates; R8.3 authoritative acceptance uses the pure-Python fixture.
    """

    def __init__(
        self,
        store: VaultStore,
        registry: TransformRegistry,
        *,
        kill_switch: KillSwitch | None = None,
        environment_identity: dict[str, str] | None = None,
    ) -> None:
        self.store = store
        self.registry = registry
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH
        self.environment_identity = dict(sorted((environment_identity or {}).items()))
        self.cache_root = store.boundary.resolve("cache/transforms")
        self.cache_root.mkdir(parents=True, exist_ok=True)

    def cache_key(self, input_revision_ids: tuple[AssetRevisionId, ...], recipe: TransformRecipe) -> str:
        adapter = self.registry.get(recipe.transform_id)
        inputs: list[dict[str, Any]] = []
        for revision_id in input_revision_ids:
            revision = self.store._load_revision_manifest(revision_id)
            if revision.status is not AssetStatus.READY:
                raise ValueError(f"Input revision is not READY: {revision_id}")
            inputs.append(
                {
                    "revision_id": str(revision.revision_id),
                    "content_sha256": revision.content_sha256,
                    "content_length": revision.content_length,
                }
            )
        payload = {
            "inputs": inputs,
            "recipe": recipe.canonical(),
            "tool": adapter.tool_identity.canonical(),
            "environment": self.environment_identity,
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.store.boundary.resolve(f"cache/transforms/{key}.json")

    def _read_cache(self, key: str) -> TransformResult | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("schema_version") != 1 or document.get("cache_key") != key:
                return TransformResult(key, CacheState.STALE, ())
            output_ids: list[AssetRevisionId] = []
            for item in document.get("outputs", []):
                revision_id = AssetRevisionId(str(item["revision_id"]))
                revision = self.store._load_revision_manifest(revision_id)
                if revision.content_sha256 != str(item["content_sha256"]) or revision.content_length != int(item["content_length"]):
                    return TransformResult(key, CacheState.STALE, ())
                self.store.object_path(revision_id)
                output_ids.append(revision_id)
            if not output_ids:
                return TransformResult(key, CacheState.STALE, ())
            return TransformResult(key, CacheState.HIT, tuple(output_ids))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, FileNotFoundError):
            return TransformResult(key, CacheState.CORRUPT, ())

    def _assert_acyclic(self, output_asset_id: AssetId, input_revision_ids: tuple[AssetRevisionId, ...]) -> None:
        pending = list(input_revision_ids)
        seen: set[AssetRevisionId] = set()
        while pending:
            revision_id = pending.pop()
            if revision_id in seen:
                continue
            seen.add(revision_id)
            revision = self.store._load_revision_manifest(revision_id)
            if revision.asset_id == output_asset_id:
                raise ValueError("Transform lineage cycle: output asset is already an input ancestor")
            pending.extend(edge.input_revision_id for edge in revision.lineage)

    @staticmethod
    def _hash_file(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
                total += len(chunk)
        return digest.hexdigest(), total

    def _promote_output(
        self,
        output: Path,
        *,
        output_asset_id: AssetId,
        recipe: TransformRecipe,
        input_revision_ids: tuple[AssetRevisionId, ...],
        display_name: str,
    ) -> AssetRevision:
        digest, length = self._hash_file(output)
        verify_content(output, digest, length)
        object_path = self.store._object_path(digest)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        if object_path.exists():
            verify_content(object_path, digest, length)
        else:
            temporary = object_path.with_name(f".{object_path.name}.{uuid.uuid4().hex}.tmp")
            shutil.copyfile(output, temporary)
            verify_content(temporary, digest, length)
            os.replace(temporary, object_path)
        lineage = tuple(LineageRef(item, relation="transform_input", transform_id=recipe.transform_id) for item in input_revision_ids)
        revision = AssetRevision.create(
            asset_id=output_asset_id,
            role=AssetRole.DERIVED,
            kind=recipe.output_kind,
            content_sha256=digest,
            content_length=length,
            reuse_scope=ReuseScope.VAULT_LOCAL,
            preservation=PreservationPolicy.EVICTABLE_DERIVED,
            provenance=(ProvenanceRef("transform", recipe.transform_id),),
            lineage=lineage,
            status=AssetStatus.READY,
        )
        revision_rel = f"manifests/revisions/{revision.revision_id}.json"
        record = AssetRecord(output_asset_id, recipe.output_kind, display_name, current_revision_id=revision.revision_id)
        self.store._atomic_json(revision_rel, asset_revision_document(revision))
        self.store._atomic_json(f"manifests/assets/{output_asset_id}.json", asset_record_document(record))
        with self.store.db:
            self.store.db.execute(
                "INSERT OR REPLACE INTO assets(asset_id, kind, display_name, current_revision_id) VALUES(?, ?, ?, ?)",
                (str(output_asset_id), recipe.output_kind.value, display_name, str(revision.revision_id)),
            )
            self.store.db.execute(
                "INSERT OR REPLACE INTO revisions(revision_id, asset_id, content_sha256, content_length, role, kind, status, manifest_rel) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(revision.revision_id),
                    str(output_asset_id),
                    digest,
                    length,
                    revision.role.value,
                    revision.kind.value,
                    revision.status.value,
                    revision_rel,
                ),
            )
        return revision

    def run(
        self,
        input_revision_ids: tuple[AssetRevisionId, ...],
        recipe: TransformRecipe,
        *,
        output_asset_id: AssetId,
        display_name: str,
    ) -> TransformResult:
        if not input_revision_ids:
            raise ValueError("A transform requires at least one input revision")
        if self.kill_switch.triggered:
            raise RuntimeError("Kodepoia kill switch is active")
        adapter = self.registry.get(recipe.transform_id)
        if adapter.transform_id != recipe.transform_id:
            raise ValueError("Transform adapter identity mismatch")
        self._assert_acyclic(output_asset_id, input_revision_ids)
        key = self.cache_key(input_revision_ids, recipe)
        cached = self._read_cache(key)
        if cached is not None and cached.cache_state is CacheState.HIT:
            return cached

        stage_root = self.store.boundary.resolve(f".staging/transforms/{uuid.uuid4().hex}")
        stage_root.mkdir(parents=True, exist_ok=False)
        try:
            inputs = tuple(self.store.object_path(item) for item in input_revision_ids)
            outputs = adapter.execute(inputs, stage_root, dict(recipe.parameters))
            if self.kill_switch.triggered:
                raise RuntimeError("Transform cancelled by Kodepoia kill switch")
            if len(outputs) != 1:
                raise ValueError("R8.3 transform service currently requires exactly one declared output")
            output = outputs[0].resolve(strict=True)
            stage_resolved = stage_root.resolve(strict=True)
            if output != stage_resolved and stage_resolved not in output.parents:
                raise PermissionError("Transform output escapes managed staging directory")
            if not output.is_file():
                raise ValueError("Transform output must be a file")
            revision = self._promote_output(
                output,
                output_asset_id=output_asset_id,
                recipe=recipe,
                input_revision_ids=input_revision_ids,
                display_name=display_name,
            )
            document = {
                "schema_version": 1,
                "cache_key": key,
                "inputs": [str(item) for item in input_revision_ids],
                "recipe": recipe.canonical(),
                "tool": adapter.tool_identity.canonical(),
                "environment": self.environment_identity,
                "outputs": [
                    {
                        "revision_id": str(revision.revision_id),
                        "content_sha256": revision.content_sha256,
                        "content_length": revision.content_length,
                    }
                ],
            }
            self.store._atomic_json(f"cache/transforms/{key}.json", document)
            return TransformResult(key, CacheState.MISS, (revision.revision_id,))
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)
