from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.intelligence.memory import MemoryStore
from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeBuilder,
    ProjectKnowledgeCatalog,
    ProjectKnowledgeItem,
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
    ProjectKnowledgeStore,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary

PROJECT_KNOWLEDGE_LIFECYCLE_SCHEMA_VERSION = 1
_DEFAULT_MAX_DELETE_ITEMS = 100
_SHA256_CHARS = frozenset("0123456789abcdef")


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _required_text(value: str, name: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError(f"{name} must not be empty")
    return clean


def _project_scope(value: str) -> str:
    scope = _required_text(value, "project_scope")
    lowered = scope.casefold()
    if lowered == "global" or lowered.startswith("global:"):
        raise ValueError("Project Knowledge lifecycle requires a non-global project scope")
    return scope


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in _SHA256_CHARS for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _normalize_versions(values: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_key, raw_value in values.items():
        key = _required_text(str(raw_key), "version fingerprint key")
        value = _required_text(str(raw_value), f"version fingerprint {key}")
        if key in normalized and normalized[key] != value:
            raise ValueError("Version fingerprint keys must be unique")
        normalized[key] = value
    return dict(sorted(normalized.items()))


def _source_fingerprint(item: ProjectKnowledgeItem) -> str:
    return _sha256_payload(
        {
            "source_kind": item.source_kind.value,
            "source_identity": item.source_identity,
            "source_digest_sha256": item.source_digest_sha256,
            "content_sha256": item.content_sha256,
            "version": item.version,
            "provenance": dict(item.provenance),
        }
    )


class ProjectKnowledgeSelection(StrEnum):
    AUTO = "auto"
    INCLUDE = "include"
    EXCLUDE = "exclude"


class ProjectKnowledgeLifecycleStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    INVALIDATED = "invalidated"
    MISSING = "missing"


class ProjectKnowledgeLifecycleReason(StrEnum):
    CURRENT = "current"
    SOURCE_CHANGED = "source_changed"
    VERSION_CHANGED = "version_changed"
    VERSION_INPUT_MISSING = "version_input_missing"
    BASELINE_MISSING = "baseline_missing"
    SOURCE_MISSING = "source_missing"


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeVersionInputs:
    values: Mapping[str, str] = field(default_factory=dict)
    schema_version: int = PROJECT_KNOWLEDGE_LIFECYCLE_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_KNOWLEDGE_LIFECYCLE_SCHEMA_VERSION:
            raise ValueError("Unsupported Project Knowledge version-input schema")
        normalized = _normalize_versions(self.values)
        object.__setattr__(self, "values", normalized)
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(
                {
                    "schema_version": self.schema_version,
                    "values": normalized,
                }
            ),
        )

    def subset_digest(self, keys: Iterable[str]) -> str:
        ordered = tuple(sorted(set(str(value).strip() for value in keys if str(value).strip())))
        missing = [key for key in ordered if key not in self.values]
        if missing:
            raise KeyError(",".join(missing))
        return _sha256_payload({key: self.values[key] for key in ordered})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "values": dict(self.values),
            "digest_sha256": self.digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectKnowledgeVersionInputs:
        raw_values = payload.get("values", {})
        if not isinstance(raw_values, Mapping):
            raise ValueError("Project Knowledge version inputs must be an object")
        value = cls(
            values={str(key): str(raw) for key, raw in raw_values.items()},
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("digest_sha256", "")) != value.digest_sha256:
            raise ValueError("Project Knowledge version-input digest mismatch")
        return value


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeLifecycleEntry:
    knowledge_id: str
    source_kind: ProjectKnowledgeSourceKind
    source_identity: str
    locator: str
    source_fingerprint_sha256: str
    source_digest_sha256: str
    content_sha256: str
    source_version: str
    version_keys: tuple[str, ...]
    version_fingerprint_sha256: str
    selection: ProjectKnowledgeSelection = ProjectKnowledgeSelection.AUTO

    def __post_init__(self) -> None:
        _require_sha256(self.knowledge_id, "knowledge_id")
        _require_sha256(self.source_fingerprint_sha256, "source_fingerprint_sha256")
        _require_sha256(self.source_digest_sha256, "source_digest_sha256")
        _require_sha256(self.content_sha256, "content_sha256")
        object.__setattr__(self, "source_identity", _required_text(self.source_identity, "source_identity"))
        object.__setattr__(self, "locator", _required_text(self.locator, "locator"))
        keys = tuple(sorted(set(_required_text(value, "version_key") for value in self.version_keys)))
        object.__setattr__(self, "version_keys", keys)
        _require_sha256(self.version_fingerprint_sha256, "version_fingerprint_sha256")
        object.__setattr__(self, "source_version", self.source_version.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "source_kind": self.source_kind.value,
            "source_identity": self.source_identity,
            "locator": self.locator,
            "source_fingerprint_sha256": self.source_fingerprint_sha256,
            "source_digest_sha256": self.source_digest_sha256,
            "content_sha256": self.content_sha256,
            "source_version": self.source_version,
            "version_keys": list(self.version_keys),
            "version_fingerprint_sha256": self.version_fingerprint_sha256,
            "selection": self.selection.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectKnowledgeLifecycleEntry:
        return cls(
            knowledge_id=str(payload["knowledge_id"]),
            source_kind=ProjectKnowledgeSourceKind(str(payload["source_kind"])),
            source_identity=str(payload["source_identity"]),
            locator=str(payload["locator"]),
            source_fingerprint_sha256=str(payload["source_fingerprint_sha256"]),
            source_digest_sha256=str(payload["source_digest_sha256"]),
            content_sha256=str(payload["content_sha256"]),
            source_version=str(payload.get("source_version", "")),
            version_keys=tuple(str(value) for value in payload.get("version_keys", [])),
            version_fingerprint_sha256=str(payload["version_fingerprint_sha256"]),
            selection=ProjectKnowledgeSelection(str(payload.get("selection", "auto"))),
        )


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeLifecycleState:
    project_scope: str
    version_inputs: ProjectKnowledgeVersionInputs
    entries: tuple[ProjectKnowledgeLifecycleEntry, ...]
    schema_version: int = PROJECT_KNOWLEDGE_LIFECYCLE_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_KNOWLEDGE_LIFECYCLE_SCHEMA_VERSION:
            raise ValueError("Unsupported Project Knowledge lifecycle schema")
        scope = _project_scope(self.project_scope)
        ordered = tuple(sorted(self.entries, key=lambda item: item.knowledge_id))
        ids = [item.knowledge_id for item in ordered]
        if len(ids) != len(set(ids)):
            raise ValueError("Project Knowledge lifecycle identities must be unique")
        object.__setattr__(self, "project_scope", scope)
        object.__setattr__(self, "entries", ordered)
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_scope": self.project_scope,
            "version_inputs": self.version_inputs.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectKnowledgeLifecycleState:
        raw_inputs = payload.get("version_inputs", {})
        if not isinstance(raw_inputs, Mapping):
            raise ValueError("Project Knowledge lifecycle version_inputs must be an object")
        raw_entries = payload.get("entries", [])
        if not isinstance(raw_entries, list):
            raise ValueError("Project Knowledge lifecycle entries must be an array")
        state = cls(
            project_scope=str(payload["project_scope"]),
            version_inputs=ProjectKnowledgeVersionInputs.from_dict(raw_inputs),
            entries=tuple(ProjectKnowledgeLifecycleEntry.from_dict(value) for value in raw_entries),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("digest_sha256", "")) != state.digest_sha256:
            raise ValueError("Project Knowledge lifecycle digest mismatch")
        return state


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeLifecycleAssessment:
    knowledge_id: str
    source_kind: ProjectKnowledgeSourceKind
    locator: str
    selection: ProjectKnowledgeSelection
    status: ProjectKnowledgeLifecycleStatus
    reason: ProjectKnowledgeLifecycleReason
    effective_state: ProjectKnowledgeState
    version_keys: tuple[str, ...]
    baseline_source_fingerprint_sha256: str
    current_source_fingerprint_sha256: str
    baseline_version_fingerprint_sha256: str
    current_version_fingerprint_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "source_kind": self.source_kind.value,
            "locator": self.locator,
            "selection": self.selection.value,
            "status": self.status.value,
            "reason": self.reason.value,
            "effective_state": self.effective_state.value,
            "version_keys": list(self.version_keys),
            "baseline_source_fingerprint_sha256": self.baseline_source_fingerprint_sha256,
            "current_source_fingerprint_sha256": self.current_source_fingerprint_sha256,
            "baseline_version_fingerprint_sha256": self.baseline_version_fingerprint_sha256,
            "current_version_fingerprint_sha256": self.current_version_fingerprint_sha256,
        }


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeLifecycleReport:
    project_scope: str
    catalog_digest_sha256: str
    lifecycle_digest_sha256: str
    items: tuple[ProjectKnowledgeLifecycleAssessment, ...]

    @property
    def stale_count(self) -> int:
        return sum(item.status is ProjectKnowledgeLifecycleStatus.STALE for item in self.items)

    @property
    def invalidated_count(self) -> int:
        return sum(item.status is ProjectKnowledgeLifecycleStatus.INVALIDATED for item in self.items)

    @property
    def missing_count(self) -> int:
        return sum(item.status is ProjectKnowledgeLifecycleStatus.MISSING for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_scope": self.project_scope,
            "catalog_digest_sha256": self.catalog_digest_sha256,
            "lifecycle_digest_sha256": self.lifecycle_digest_sha256,
            "items": [item.to_dict() for item in self.items],
            "summary": {
                "total": len(self.items),
                "stale": self.stale_count,
                "invalidated": self.invalidated_count,
                "missing": self.missing_count,
            },
        }


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeDeletionResult:
    removed_knowledge_ids: tuple[str, ...]
    source_records_deleted: bool = False
    source_paths_touched: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "removed_knowledge_ids", tuple(sorted(set(self.removed_knowledge_ids))))
        if self.source_records_deleted or self.source_paths_touched:
            raise ValueError("delete-derived must never delete or mutate source records")


@dataclass(slots=True)
class ProjectKnowledgeLifecycleStore:
    project_root: Path
    project_scope: str
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve(strict=False)
        self.project_scope = _project_scope(self.project_scope)
        self._boundary = WorkspaceBoundary(self.project_root)

    @property
    def path(self) -> Path:
        return self._boundary.resolve(".kodepoia/knowledge/lifecycle-v1.json")

    def _require_project(self) -> None:
        metadata = self._boundary.resolve(".kodepoia", must_exist=True)
        if not metadata.is_dir():
            raise FileNotFoundError("Kodepoia project metadata not found")

    def save(self, state: ProjectKnowledgeLifecycleState) -> Path:
        self._require_project()
        if state.project_scope != self.project_scope:
            raise ValueError("Project Knowledge lifecycle scope does not match store scope")
        path = self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(
            state.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ) + "\n"
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
        return path

    def load(self) -> ProjectKnowledgeLifecycleState:
        self._require_project()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Project Knowledge lifecycle document must be an object")
        state = ProjectKnowledgeLifecycleState.from_dict(payload)
        if state.project_scope != self.project_scope:
            raise ValueError("Project Knowledge lifecycle scope does not match store scope")
        return state


@dataclass(slots=True)
class ProjectKnowledgeLifecycleManager:
    project_root: Path
    project_scope: str
    max_delete_items: int = _DEFAULT_MAX_DELETE_ITEMS
    _catalog_store: ProjectKnowledgeStore = field(init=False, repr=False)
    _lifecycle_store: ProjectKnowledgeLifecycleStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve(strict=False)
        self.project_scope = _project_scope(self.project_scope)
        if self.max_delete_items < 1:
            raise ValueError("max_delete_items must be positive")
        self._catalog_store = ProjectKnowledgeStore(self.project_root, self.project_scope)
        self._lifecycle_store = ProjectKnowledgeLifecycleStore(self.project_root, self.project_scope)

    @staticmethod
    def _selection_state(selection: ProjectKnowledgeSelection) -> ProjectKnowledgeState:
        if selection is ProjectKnowledgeSelection.INCLUDE:
            return ProjectKnowledgeState.INCLUDED
        if selection is ProjectKnowledgeSelection.EXCLUDE:
            return ProjectKnowledgeState.EXCLUDED
        return ProjectKnowledgeState.ACTIVE

    @staticmethod
    def _entry_by_id(state: ProjectKnowledgeLifecycleState) -> dict[str, ProjectKnowledgeLifecycleEntry]:
        return {entry.knowledge_id: entry for entry in state.entries}

    def _report_and_catalog(
        self,
        catalog: ProjectKnowledgeCatalog,
        state: ProjectKnowledgeLifecycleState,
        version_inputs: ProjectKnowledgeVersionInputs,
    ) -> tuple[ProjectKnowledgeLifecycleReport, ProjectKnowledgeCatalog]:
        if catalog.project_scope != self.project_scope or state.project_scope != self.project_scope:
            raise ValueError("Project Knowledge lifecycle project scope mismatch")
        entries = self._entry_by_id(state)
        current = {item.knowledge_id: item for item in catalog.items}
        assessments: list[ProjectKnowledgeLifecycleAssessment] = []
        effective_items: list[ProjectKnowledgeItem] = []

        for item in catalog.items:
            entry = entries.get(item.knowledge_id)
            current_source = _source_fingerprint(item)
            current_version = ""
            if entry is None:
                status = ProjectKnowledgeLifecycleStatus.INVALIDATED
                reason = ProjectKnowledgeLifecycleReason.BASELINE_MISSING
                selection = ProjectKnowledgeSelection.AUTO
                version_keys: tuple[str, ...] = ()
                baseline_source = ""
                baseline_version = ""
            else:
                selection = entry.selection
                version_keys = entry.version_keys
                baseline_source = entry.source_fingerprint_sha256
                baseline_version = entry.version_fingerprint_sha256
                try:
                    current_version = version_inputs.subset_digest(version_keys)
                except KeyError:
                    status = ProjectKnowledgeLifecycleStatus.INVALIDATED
                    reason = ProjectKnowledgeLifecycleReason.VERSION_INPUT_MISSING
                else:
                    if current_source != entry.source_fingerprint_sha256:
                        status = ProjectKnowledgeLifecycleStatus.STALE
                        reason = ProjectKnowledgeLifecycleReason.SOURCE_CHANGED
                    elif current_version != entry.version_fingerprint_sha256:
                        status = ProjectKnowledgeLifecycleStatus.INVALIDATED
                        reason = ProjectKnowledgeLifecycleReason.VERSION_CHANGED
                    else:
                        status = ProjectKnowledgeLifecycleStatus.FRESH
                        reason = ProjectKnowledgeLifecycleReason.CURRENT

            if status is ProjectKnowledgeLifecycleStatus.FRESH:
                effective_state = self._selection_state(selection)
                effective_item = replace(item, state=effective_state)
            else:
                effective_state = ProjectKnowledgeState.INVALIDATED
                effective_item = replace(
                    item,
                    state=ProjectKnowledgeState.INVALIDATED,
                    freshness=status.value,
                )
            effective_items.append(effective_item)
            assessments.append(
                ProjectKnowledgeLifecycleAssessment(
                    knowledge_id=item.knowledge_id,
                    source_kind=item.source_kind,
                    locator=item.locator,
                    selection=selection,
                    status=status,
                    reason=reason,
                    effective_state=effective_state,
                    version_keys=version_keys,
                    baseline_source_fingerprint_sha256=baseline_source,
                    current_source_fingerprint_sha256=current_source,
                    baseline_version_fingerprint_sha256=baseline_version,
                    current_version_fingerprint_sha256=current_version,
                )
            )

        for entry in state.entries:
            if entry.knowledge_id in current:
                continue
            assessments.append(
                ProjectKnowledgeLifecycleAssessment(
                    knowledge_id=entry.knowledge_id,
                    source_kind=entry.source_kind,
                    locator=entry.locator,
                    selection=entry.selection,
                    status=ProjectKnowledgeLifecycleStatus.MISSING,
                    reason=ProjectKnowledgeLifecycleReason.SOURCE_MISSING,
                    effective_state=ProjectKnowledgeState.INVALIDATED,
                    version_keys=entry.version_keys,
                    baseline_source_fingerprint_sha256=entry.source_fingerprint_sha256,
                    current_source_fingerprint_sha256="",
                    baseline_version_fingerprint_sha256=entry.version_fingerprint_sha256,
                    current_version_fingerprint_sha256="",
                )
            )

        effective = ProjectKnowledgeCatalog(
            project_scope=self.project_scope,
            items=tuple(effective_items),
        )
        report = ProjectKnowledgeLifecycleReport(
            project_scope=self.project_scope,
            catalog_digest_sha256=effective.digest_sha256,
            lifecycle_digest_sha256=state.digest_sha256,
            items=tuple(sorted(assessments, key=lambda value: value.knowledge_id)),
        )
        return report, effective

    def assess(
        self,
        catalog: ProjectKnowledgeCatalog,
        version_inputs: ProjectKnowledgeVersionInputs,
    ) -> ProjectKnowledgeLifecycleReport:
        state = self._lifecycle_store.load()
        report, _ = self._report_and_catalog(catalog, state, version_inputs)
        return report

    def effective_catalog(
        self,
        catalog: ProjectKnowledgeCatalog,
        version_inputs: ProjectKnowledgeVersionInputs,
    ) -> ProjectKnowledgeCatalog:
        state = self._lifecycle_store.load()
        _, effective = self._report_and_catalog(catalog, state, version_inputs)
        return effective

    def refresh(
        self,
        catalog: ProjectKnowledgeCatalog,
        version_inputs: ProjectKnowledgeVersionInputs,
        *,
        version_dependencies: Mapping[str, Iterable[str]] | None = None,
    ) -> ProjectKnowledgeLifecycleReport:
        if catalog.project_scope != self.project_scope:
            raise ValueError("Project Knowledge catalog scope does not match lifecycle scope")
        previous: ProjectKnowledgeLifecycleState | None = None
        if self._lifecycle_store.path.exists():
            previous = self._lifecycle_store.load()
        previous_entries = {} if previous is None else self._entry_by_id(previous)
        dependencies = dict(version_dependencies or {})
        unknown_dependencies = sorted(set(dependencies) - {item.knowledge_id for item in catalog.items})
        if unknown_dependencies:
            raise ValueError("Version dependencies reference unknown Project Knowledge")

        entries: list[ProjectKnowledgeLifecycleEntry] = []
        for item in catalog.items:
            old = previous_entries.get(item.knowledge_id)
            raw_keys = dependencies.get(
                item.knowledge_id,
                () if old is None else old.version_keys,
            )
            keys = tuple(sorted(set(_required_text(str(value), "version_key") for value in raw_keys)))
            try:
                version_fingerprint = version_inputs.subset_digest(keys)
            except KeyError as exc:
                raise ValueError(
                    f"Missing required version fingerprint for {item.knowledge_id}: {exc}"
                ) from exc
            if old is not None:
                selection = old.selection
            elif item.state is ProjectKnowledgeState.INCLUDED:
                selection = ProjectKnowledgeSelection.INCLUDE
            elif item.state is ProjectKnowledgeState.EXCLUDED:
                selection = ProjectKnowledgeSelection.EXCLUDE
            else:
                selection = ProjectKnowledgeSelection.AUTO
            entries.append(
                ProjectKnowledgeLifecycleEntry(
                    knowledge_id=item.knowledge_id,
                    source_kind=item.source_kind,
                    source_identity=item.source_identity,
                    locator=item.locator,
                    source_fingerprint_sha256=_source_fingerprint(item),
                    source_digest_sha256=item.source_digest_sha256,
                    content_sha256=item.content_sha256,
                    source_version=item.version,
                    version_keys=keys,
                    version_fingerprint_sha256=version_fingerprint,
                    selection=selection,
                )
            )

        state = ProjectKnowledgeLifecycleState(
            project_scope=self.project_scope,
            version_inputs=version_inputs,
            entries=tuple(entries),
        )
        self._lifecycle_store.save(state)
        report, effective = self._report_and_catalog(catalog, state, version_inputs)
        self._catalog_store.save(effective)
        return report

    def rebuild(
        self,
        builder: ProjectKnowledgeBuilder,
        version_inputs: ProjectKnowledgeVersionInputs,
        *,
        project_files: Iterable[str | Path] = (),
        memory: MemoryStore | None = None,
        version_dependencies: Mapping[str, Iterable[str]] | None = None,
    ) -> ProjectKnowledgeLifecycleReport:
        if builder.project_scope != self.project_scope:
            raise ValueError("Project Knowledge builder scope does not match lifecycle scope")
        catalog = builder.build(project_files=project_files, memory=memory)
        return self.refresh(
            catalog,
            version_inputs,
            version_dependencies=version_dependencies,
        )

    def set_selection(
        self,
        catalog: ProjectKnowledgeCatalog,
        version_inputs: ProjectKnowledgeVersionInputs,
        knowledge_id: str,
        selection: ProjectKnowledgeSelection | str,
    ) -> ProjectKnowledgeLifecycleReport:
        state = self._lifecycle_store.load()
        requested = ProjectKnowledgeSelection(str(selection))
        found = False
        entries: list[ProjectKnowledgeLifecycleEntry] = []
        for entry in state.entries:
            if entry.knowledge_id == knowledge_id:
                entries.append(replace(entry, selection=requested))
                found = True
            else:
                entries.append(entry)
        if not found:
            raise ValueError("Selection references unknown Project Knowledge")
        updated = ProjectKnowledgeLifecycleState(
            project_scope=self.project_scope,
            version_inputs=state.version_inputs,
            entries=tuple(entries),
        )
        self._lifecycle_store.save(updated)
        report, effective = self._report_and_catalog(catalog, updated, version_inputs)
        self._catalog_store.save(effective)
        return report

    def delete_derived(
        self,
        knowledge_ids: Iterable[str],
    ) -> ProjectKnowledgeDeletionResult:
        requested = tuple(sorted(set(_required_text(value, "knowledge_id") for value in knowledge_ids)))
        if not requested:
            raise ValueError("delete-derived requires at least one Project Knowledge identity")
        if len(requested) > self.max_delete_items:
            raise ValueError("delete-derived exceeds the bounded item limit")

        state = self._lifecycle_store.load()
        catalog = self._catalog_store.load()
        known = {entry.knowledge_id for entry in state.entries} | {
            item.knowledge_id for item in catalog.items
        }
        unknown = sorted(set(requested) - known)
        if unknown:
            raise ValueError("delete-derived references unknown Project Knowledge")

        updated_state = ProjectKnowledgeLifecycleState(
            project_scope=self.project_scope,
            version_inputs=state.version_inputs,
            entries=tuple(entry for entry in state.entries if entry.knowledge_id not in requested),
        )
        updated_catalog = ProjectKnowledgeCatalog(
            project_scope=self.project_scope,
            items=tuple(item for item in catalog.items if item.knowledge_id not in requested),
        )
        self._lifecycle_store.save(updated_state)
        self._catalog_store.save(updated_catalog)
        return ProjectKnowledgeDeletionResult(
            removed_knowledge_ids=requested,
            source_records_deleted=False,
            source_paths_touched=(),
        )
