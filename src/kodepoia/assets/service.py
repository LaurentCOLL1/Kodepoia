from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from pathlib import Path
from threading import Event
from typing import Any, Mapping

from kodepoia.assets.boundary import VaultBoundary
from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRevisionId,
    AssetRole,
    PreservationPolicy,
    ProjectAssetReference,
    ProvenanceRef,
    ReuseScope,
)
from kodepoia.assets.duplicates import DuplicateDetector
from kodepoia.assets.governance import AssetGovernanceService, AssetLicenseEvidence
from kodepoia.assets.lfs import GitLfsService, LfsCapabilityState
from kodepoia.assets.search import AssetSearchIndex, EmbeddingProvider, SearchDocumentBuilder, SearchFilters
from kodepoia.assets.serialization import load_asset_record
from kodepoia.assets.store import VaultStore
from kodepoia.assets.vcs import AssetVcsService
from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.license_bom import LicensePolicy


class AssetOperationState(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"


class AssetOperationCancelled(RuntimeError):
    pass


class AssetCancellationToken:
    """Thread-safe cooperative cancellation token used by CLI/UI service calls."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def require_active(self) -> None:
        if self.cancelled:
            raise AssetOperationCancelled("Asset operation cancelled")


@dataclass(frozen=True, slots=True)
class AssetSummary:
    asset_id: str
    revision_id: str | None
    display_name: str
    kind: str
    role: str | None
    status: str | None
    reuse_scope: str | None
    license_state: str
    license_token: str


@dataclass(frozen=True, slots=True)
class AssetDetail:
    summary: AssetSummary
    content_sha256: str | None
    content_length: int | None
    preservation: str | None
    provenance: tuple[dict[str, str | None], ...]
    lineage_inputs: tuple[dict[str, str | None], ...]
    project_references: tuple[dict[str, str | None], ...]


@dataclass(frozen=True, slots=True)
class AssetSearchResult:
    summary: AssetSummary
    score: float
    lexical_score: float
    semantic_score: float | None
    mode: str
    embedding_state: str


@dataclass(frozen=True, slots=True)
class AssetRebuildResult:
    state: AssetOperationState
    asset_count: int
    revision_count: int
    project_reference_count: int
    search_documents: int
    corrupt_manifests: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AssetRepositoryEvidence:
    state: AssetOperationState
    revision_id: str
    target_path: str | None
    vcs: dict[str, Any] | None
    lfs: dict[str, Any] | None
    reason: str = ""


def jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [jsonable(item) for item in value]
    return value


class AssetService:
    """Single governed R8 façade used by both the CLI and KodeStudio.

    UI callers never need direct access to Git, Git LFS, SQLite, ProcessSandbox,
    VaultStore or license/BOM internals. The default Vault is project-local;
    callers that already own an accepted inter-project Vault may inject it.
    """

    def __init__(
        self,
        project_root: Path,
        *,
        vault_root: Path | None = None,
        store: VaultStore | None = None,
        search_index: AssetSearchIndex | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        governance: AssetGovernanceService | None = None,
        license_evidence: Mapping[AssetRevisionId, AssetLicenseEvidence] | None = None,
    ) -> None:
        self.project = WorkspaceBoundary(project_root.resolve(strict=False))
        self.vault_root = (vault_root or self.project.resolve(".kodepoia/vault")).resolve(strict=False)
        self.store = store or VaultStore(VaultBoundary(self.vault_root))
        self.search_index = search_index or AssetSearchIndex(self.store)
        self.embedding_provider = embedding_provider
        self.license_evidence = dict(license_evidence or {})
        self.governance = governance or AssetGovernanceService(
            self.store,
            LicensePolicy("r8.10-conservative-unknown-block"),
        )
        self.duplicates = DuplicateDetector(self.store)
        self.vcs = AssetVcsService(self.project, store=self.store)
        self.lfs = GitLfsService(self.project)
        self._closed = False

    def fork(self) -> "AssetService":
        """Create a worker-safe façade with independent SQLite connections."""
        return AssetService(
            self.project.root,
            vault_root=self.vault_root,
            embedding_provider=self.embedding_provider,
            license_evidence=self.license_evidence,
        )

    def __enter__(self) -> "AssetService":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self.search_index.close()
        self.store.close()
        self._closed = True

    def _license_state(self, revision_id: AssetRevisionId) -> tuple[str, str, bool]:
        evidence = self.governance.evidence_or_unknown(revision_id, self.license_evidence)
        decision = self.governance.decision(revision_id, evidence)
        token = evidence.concluded.spdx_token
        state = "unknown" if token in {"NOASSERTION", "NONE"} else decision.outcome.value
        return state, token, decision.blocking

    def _summary_for_row(self, row: Any) -> AssetSummary:
        revision_raw = row["current_revision_id"]
        if not revision_raw:
            return AssetSummary(
                str(row["asset_id"]), None, str(row["display_name"]), str(row["kind"]),
                None, None, None, "unknown", "NOASSERTION",
            )
        revision_id = AssetRevisionId(str(revision_raw))
        revision = self.store._load_revision_manifest(revision_id)
        license_state, license_token, _ = self._license_state(revision_id)
        return AssetSummary(
            str(row["asset_id"]), str(revision_id), str(row["display_name"]), str(row["kind"]),
            revision.role.value, revision.status.value, revision.reuse_scope.value,
            license_state, license_token,
        )

    def list_assets(self) -> tuple[AssetSummary, ...]:
        rows = self.store.db.execute(
            "SELECT asset_id, kind, display_name, current_revision_id FROM assets ORDER BY display_name, asset_id"
        ).fetchall()
        return tuple(self._summary_for_row(row) for row in rows)

    def show(self, revision_id: str | AssetRevisionId) -> AssetDetail:
        identity = revision_id if isinstance(revision_id, AssetRevisionId) else AssetRevisionId(str(revision_id))
        revision = self.store._load_revision_manifest(identity)
        record_path = self.store.boundary.resolve(
            f"manifests/assets/{revision.asset_id}.json", must_exist=True
        )
        import json
        record = load_asset_record(json.loads(record_path.read_text(encoding="utf-8")))
        license_state, license_token, _ = self._license_state(identity)
        summary = AssetSummary(
            str(record.asset_id), str(identity), record.display_name, record.kind.value,
            revision.role.value, revision.status.value, revision.reuse_scope.value,
            license_state, license_token,
        )
        rows = self.store.db.execute(
            "SELECT project_id, target_path FROM project_refs WHERE revision_id = ? ORDER BY project_id, target_path",
            (str(identity),),
        ).fetchall()
        return AssetDetail(
            summary,
            revision.content_sha256,
            revision.content_length,
            revision.preservation.value,
            tuple(item.canonical() for item in revision.provenance),
            tuple(item.canonical() for item in revision.lineage),
            tuple(
                {"project_id": str(row["project_id"]), "target_path": row["target_path"]}
                for row in rows
            ),
        )

    def status(self) -> dict[str, Any]:
        asset_count = int(self.store.db.execute("SELECT COUNT(*) FROM assets").fetchone()[0])
        revision_count = int(self.store.db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0])
        ref_count = int(self.store.db.execute("SELECT COUNT(*) FROM project_refs").fetchone()[0])
        try:
            vcs_available = self.vcs.is_repository()
            vcs_state = "available" if vcs_available else "unavailable"
        except Exception as exc:
            vcs_state = "unavailable"
            vcs_available = False
            vcs_reason = f"{type(exc).__name__}: {exc}"
        else:
            vcs_reason = ""
        try:
            capability = self.lfs.capability()
            gaps = self.lfs.required_policy_gaps() if vcs_available else ()
        except Exception as exc:
            lfs_state = "unavailable"
            lfs_version = None
            gaps = ()
            lfs_reason = f"{type(exc).__name__}: {exc}"
        else:
            lfs_state = capability.state.value
            lfs_version = capability.version
            lfs_reason = capability.detail
        return {
            "state": AssetOperationState.READY.value,
            "vault": {
                "root": ".kodepoia/vault" if self.vault_root == self.project.resolve(".kodepoia/vault") else "configured-vault",
                "assets": asset_count,
                "revisions": revision_count,
                "project_references": ref_count,
            },
            "vcs": {"state": vcs_state, "reason": vcs_reason},
            "lfs": {"state": lfs_state, "version": lfs_version, "policy_gaps": list(gaps), "reason": lfs_reason},
        }

    def doctor(self) -> dict[str, Any]:
        status = self.status()
        status["search"] = {
            "documents": int(self.search_index.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]),
            "embeddings": int(self.search_index.db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]),
            "provider": (
                jsonable(self.embedding_provider.identity) if self.embedding_provider is not None else {"state": "unavailable"}
            ),
        }
        status["manual_intervention"] = "NONE"
        return status

    def ingest(
        self,
        source_path: str,
        *,
        kind: AssetKind = AssetKind.GENERIC,
        display_name: str | None = None,
        asset_id: AssetId | None = None,
        project_id: str | None = None,
        target_path: str | None = None,
        reuse_scope: ReuseScope = ReuseScope.PROJECT_ONLY,
        preservation: PreservationPolicy = PreservationPolicy.PINNED_SOURCE,
        token: AssetCancellationToken | None = None,
    ) -> AssetDetail:
        active = token or AssetCancellationToken()
        active.require_active()
        source = self.project.resolve(source_path, must_exist=True)
        if not source.is_file():
            raise ValueError("Asset ingest source must be a file")
        relative = self.project.relative(source)
        identity = asset_id or AssetId.from_seed("r8.10-project-asset", f"{project_id or 'local'}:{relative}")
        revision = self.store.ingest(
            project_boundary=self.project,
            source_path=relative,
            asset_id=identity,
            kind=kind,
            display_name=display_name or source.name,
            provenance=(ProvenanceRef("project-file", relative),),
            reuse_scope=reuse_scope,
            preservation=preservation,
        )
        if project_id is not None:
            self.store.add_project_reference(
                ProjectAssetReference(project_id, identity, revision.revision_id, target_path or relative),
                project_boundary=self.project,
            )
        active.require_active()
        self._index_revision(revision.revision_id)
        return self.show(revision.revision_id)

    def _index_revision(self, revision_id: AssetRevisionId) -> None:
        state, _token, blocked = self._license_state(revision_id)
        document = SearchDocumentBuilder(self.store).build(
            revision_id,
            license_state=state,
            blocked=blocked,
        )
        self.search_index.index_documents((document,), self.embedding_provider)

    def search(
        self,
        query: str,
        *,
        filters: SearchFilters | None = None,
        limit: int = 50,
        token: AssetCancellationToken | None = None,
    ) -> tuple[AssetSearchResult, ...]:
        active = token or AssetCancellationToken()
        active.require_active()
        hits = self.search_index.search(
            query,
            provider=self.embedding_provider,
            filters=filters,
            limit=limit,
        )
        results: list[AssetSearchResult] = []
        for hit in hits:
            active.require_active()
            detail = self.show(hit.revision_id)
            results.append(
                AssetSearchResult(
                    detail.summary,
                    hit.score,
                    hit.lexical_score,
                    hit.semantic_score,
                    hit.mode.value,
                    hit.embedding_state.value,
                )
            )
        return tuple(results)

    def duplicate_candidates(
        self,
        *,
        threshold: float = 0.90,
        token: AssetCancellationToken | None = None,
    ) -> dict[str, Any]:
        active = token or AssetCancellationToken()
        active.require_active()
        exact = [[str(item) for item in group] for group in self.duplicates.exact_groups()]
        active.require_active()
        near = []
        for candidate in self.duplicates.near_candidates(threshold=threshold):
            active.require_active()
            near.append(jsonable(candidate))
        return {"exact_groups": exact, "near_candidates": near, "threshold": threshold}

    def lineage(self, revision_id: str | AssetRevisionId) -> dict[str, Any]:
        identity = revision_id if isinstance(revision_id, AssetRevisionId) else AssetRevisionId(str(revision_id))
        revision = self.store._load_revision_manifest(identity)
        outputs: list[dict[str, str | None]] = []
        for candidate_id in self.store.list_revisions():
            candidate = self.store._load_revision_manifest(candidate_id)
            for edge in candidate.lineage:
                if edge.input_revision_id == identity:
                    outputs.append({
                        "revision_id": str(candidate_id),
                        "relation": edge.relation,
                        "transform_id": edge.transform_id,
                    })
        return {
            "revision_id": str(identity),
            "role": revision.role.value,
            "inputs": [item.canonical() for item in revision.lineage],
            "outputs": sorted(outputs, key=lambda item: str(item["revision_id"])),
        }

    def rebuild(self, *, token: AssetCancellationToken | None = None) -> AssetRebuildResult:
        active = token or AssetCancellationToken()
        active.require_active()
        canonical = self.store.rebuild_index()
        if canonical.corrupt_manifests:
            return AssetRebuildResult(
                AssetOperationState.BLOCKED, 0, 0, 0, 0, canonical.corrupt_manifests
            )
        active.require_active()
        documents = []
        builder = SearchDocumentBuilder(self.store)
        for revision_id in self.store.list_revisions():
            active.require_active()
            state, _license_token, blocked = self._license_state(revision_id)
            documents.append(builder.build(revision_id, license_state=state, blocked=blocked))
        active.require_active()
        with self.search_index.db:
            self.search_index.db.execute("DELETE FROM embeddings")
            self.search_index.db.execute("DELETE FROM documents")
        if documents:
            active.require_active()
            self.search_index.index_documents(tuple(documents), self.embedding_provider)
        return AssetRebuildResult(
            AssetOperationState.READY,
            canonical.asset_count,
            canonical.revision_count,
            canonical.project_reference_count,
            len(documents),
        )

    def materialize(
        self,
        revision_id: str | AssetRevisionId,
        target_path: str,
        *,
        overwrite: bool = False,
        confirmed: bool = False,
        token: AssetCancellationToken | None = None,
    ) -> dict[str, Any]:
        active = token or AssetCancellationToken()
        active.require_active()
        identity = revision_id if isinstance(revision_id, AssetRevisionId) else AssetRevisionId(str(revision_id))
        target = self.project.resolve(target_path)
        if target.exists() and overwrite and not confirmed:
            raise PermissionError("Explicit confirmation is required before overwriting a materialized asset")
        result = self.store.materialize(
            identity,
            project_boundary=self.project,
            target_path=target_path,
            overwrite=overwrite,
        )
        active.require_active()
        return {"revision_id": str(identity), "target_path": self.project.relative(result), "overwritten": overwrite}

    def deletion_plan(self, revision_id: str | AssetRevisionId) -> dict[str, Any]:
        identity = revision_id if isinstance(revision_id, AssetRevisionId) else AssetRevisionId(str(revision_id))
        return jsonable(self.store.deletion_plan(identity))

    def delete_revision(self, revision_id: str | AssetRevisionId, *, confirmed: bool) -> dict[str, Any]:
        if not confirmed:
            raise PermissionError("Explicit confirmation is required before deleting a Vault revision")
        identity = revision_id if isinstance(revision_id, AssetRevisionId) else AssetRevisionId(str(revision_id))
        return jsonable(self.store.delete_revision(identity, confirm=True))

    def export_plan(self, project_id: str) -> dict[str, Any]:
        plan = self.governance.plan_export(project_id, self.license_evidence)
        return {
            "project_id": project_id,
            "allowed": plan.allowed,
            "blockers": list(plan.blockers),
            "decisions": [item.to_dict() for item in plan.decisions],
        }

    def export_project(
        self,
        project_id: str,
        target_dir: str,
        *,
        confirmed: bool,
        token: AssetCancellationToken | None = None,
    ) -> dict[str, Any]:
        if not confirmed:
            raise PermissionError("Explicit confirmation is required before exporting project assets")
        active = token or AssetCancellationToken()
        active.require_active()
        plan = self.governance.plan_export(project_id, self.license_evidence)
        if not plan.allowed:
            raise PermissionError("Asset export blocked: " + ", ".join(plan.blockers))
        active.require_active()
        report = self.governance.export_project(
            project_id,
            self.license_evidence,
            export_boundary=self.project,
            target_dir=target_dir,
        )
        active.require_active()
        return report.to_dict()

    def vcs_status(self) -> dict[str, Any]:
        try:
            if not self.vcs.is_repository():
                return {"state": AssetOperationState.UNAVAILABLE.value, "reason": "not-a-git-repository", "files": []}
            status = self.vcs.repository_status()
        except Exception as exc:
            return {"state": AssetOperationState.UNAVAILABLE.value, "reason": f"{type(exc).__name__}: {exc}", "files": []}
        return {"state": AssetOperationState.READY.value, **jsonable(status)}

    def lfs_doctor(self) -> dict[str, Any]:
        try:
            capability = self.lfs.capability()
            if capability.state is LfsCapabilityState.UNAVAILABLE:
                return {
                    "state": AssetOperationState.UNAVAILABLE.value,
                    "version": None,
                    "detail": capability.detail,
                    "policy_gaps": [],
                    "files": [],
                }
            return {
                "state": AssetOperationState.READY.value,
                "version": capability.version,
                "detail": capability.detail,
                "policy_gaps": list(self.lfs.required_policy_gaps()),
                "files": list(self.lfs.lfs_files()),
            }
        except Exception as exc:
            return {
                "state": AssetOperationState.UNAVAILABLE.value,
                "version": None,
                "detail": f"{type(exc).__name__}: {exc}",
                "policy_gaps": [],
                "files": [],
            }

    def repository_evidence(self, revision_id: str | AssetRevisionId) -> AssetRepositoryEvidence:
        identity = revision_id if isinstance(revision_id, AssetRevisionId) else AssetRevisionId(str(revision_id))
        row = self.store.db.execute(
            "SELECT target_path FROM project_refs WHERE revision_id = ? AND target_path IS NOT NULL ORDER BY project_id, target_path LIMIT 1",
            (str(identity),),
        ).fetchone()
        if row is None:
            return AssetRepositoryEvidence(
                AssetOperationState.UNAVAILABLE, str(identity), None, None, None, "no-materialized-project-reference"
            )
        target = str(row["target_path"])
        path = self.project.resolve(target)
        if not path.is_file():
            return AssetRepositoryEvidence(
                AssetOperationState.UNAVAILABLE, str(identity), target, None, None, "materialized-source-missing"
            )
        try:
            vcs = jsonable(self.vcs.asset_evidence(identity, target)) if self.vcs.is_repository() else None
        except Exception as exc:
            vcs = {"state": "unavailable", "reason": f"{type(exc).__name__}: {exc}"}
        try:
            lfs = jsonable(self.lfs.diagnose(target)) if self.vcs.is_repository() else None
        except Exception as exc:
            lfs = {"state": "unavailable", "reason": f"{type(exc).__name__}: {exc}"}
        return AssetRepositoryEvidence(AssetOperationState.READY, str(identity), target, vcs, lfs)
