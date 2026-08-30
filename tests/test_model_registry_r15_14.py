from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.models.router import KodeModelRouter, ModelRole, TaskProfile
from kodepoia.tuning.model_registry import (
    ModelArtifactKind,
    ModelArtifactVariant,
    ModelVersionState,
    SpecializedModelRegistry,
    SpecializedModelVersion,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def version(
    version_id: str,
    digest: str,
    *,
    state: ModelVersionState = ModelVersionState.CANDIDATE,
    disposition: str = "PROMOTE_TO_EXPORT",
    role: ModelRole = ModelRole.CORE,
    runtime_ref: str | None = None,
) -> SpecializedModelVersion:
    return SpecializedModelVersion(
        version_id=version_id,
        candidate_id=f"candidate:{version_id}",
        state=state,
        disposition=disposition,
        base_model_id="base:qwen-test",
        base_digest=A,
        lineage=(("dataset", B), ("training", C), ("evaluation", D)),
        role_eligibility=(role,),
        domain_tags=("general",),
        variants=(
            ModelArtifactVariant(
                kind=ModelArtifactKind.OLLAMA,
                artifact_id=f"artifact:{version_id}",
                digest=digest,
                runtime_ref=runtime_ref,
                capabilities=("structured", "tools"),
            ),
        ),
        preferred_variant=ModelArtifactKind.OLLAMA,
    )


def registry(
    tmp_path: Path, events: list[dict[str, object]] | None = None
) -> SpecializedModelRegistry:
    root = tmp_path / "project"
    root.mkdir()
    path = root / ".kodepoia" / "models" / "specialized.json"
    safe = SafeChangeManager(root, tmp_path / "snapshots")
    sink = events.append if events is not None else None
    return SpecializedModelRegistry(path, safe_change=safe, audit_sink=sink)


def test_canonical_record_digest_is_order_stable() -> None:
    left = version("v1", B)
    right = SpecializedModelVersion(
        version_id=left.version_id,
        candidate_id=left.candidate_id,
        state=left.state,
        disposition=left.disposition,
        base_model_id=left.base_model_id,
        base_digest=left.base_digest,
        lineage=tuple(reversed(left.lineage)),
        role_eligibility=left.role_eligibility,
        domain_tags=left.domain_tags,
        variants=left.variants,
        preferred_variant=left.preferred_variant,
    )
    assert left.digest == right.digest


def test_rejected_and_non_promoted_candidates_fail_closed(tmp_path: Path) -> None:
    store = registry(tmp_path)
    rejected = version("rejected", B, state=ModelVersionState.REJECTED)
    inconclusive = version("inconclusive", C, disposition="INCONCLUSIVE")
    store.register(rejected)
    store.register(inconclusive)

    def probe(*_args: object) -> bool:
        return True

    with pytest.raises(ValueError, match="rejected"):
        store.promote(rejected.version_id, ModelRole.CORE, health_probe=probe)
    with pytest.raises(ValueError, match="disposition"):
        store.promote(inconclusive.version_id, ModelRole.CORE, health_probe=probe)


def test_atomic_promotion_restart_router_and_audit(tmp_path: Path) -> None:
    events: list[dict[str, object]] = []
    store = registry(tmp_path, events)
    candidate = version("v1", B)
    store.register(candidate)
    transaction = store.promote(
        candidate.version_id, ModelRole.CORE, health_probe=lambda *_args: True
    )
    assert len(transaction) == 64
    reloaded = SpecializedModelRegistry(store.path)
    active = reloaded.active_version(ModelRole.CORE)
    assert active is not None and active.version_id == "v1"
    router = KodeModelRouter(reloaded.router_registry())
    selected = router.route(TaskProfile(needs_tools=True, needs_structured=True))
    assert selected.name == "artifact:v1"
    assert any(event["event"] == "model_registry.promoted" for event in events)
    assert any((tmp_path / "snapshots").iterdir())


def test_health_failure_restores_exact_document(tmp_path: Path) -> None:
    store = registry(tmp_path)
    candidate = version("v1", B)
    store.register(candidate)
    before = store.path.read_bytes()
    with pytest.raises(RuntimeError, match="health probe"):
        store.promote(
            candidate.version_id,
            ModelRole.CORE,
            health_probe=lambda *_args: False,
        )
    assert store.path.read_bytes() == before
    assert store.active_version(ModelRole.CORE) is None


def test_rollback_restores_prior_exact_role_mapping_after_restart(
    tmp_path: Path,
) -> None:
    store = registry(tmp_path)
    store.register(version("v1", B))
    store.register(version("v2", C))
    store.promote("v1", ModelRole.CORE, health_probe=lambda *_args: True)
    store.promote("v2", ModelRole.CORE, health_probe=lambda *_args: True)
    restarted = SpecializedModelRegistry(store.path)
    assert restarted.rollback(
        ModelRole.CORE, health_probe=lambda *_args: True
    ) == "v1"
    active = restarted.active_version(ModelRole.CORE)
    assert active is not None and active.version_id == "v1"


def test_mutable_runtime_tag_must_resolve_to_immutable_digest(
    tmp_path: Path,
) -> None:
    store = registry(tmp_path)
    candidate = version("v1", B, runtime_ref="kodepoia/candidate:v1")
    store.register(candidate)
    with pytest.raises(ValueError, match="resolver required"):
        store.promote("v1", ModelRole.CORE, health_probe=lambda *_args: True)
    with pytest.raises(ValueError, match="drift"):
        store.promote(
            "v1",
            ModelRole.CORE,
            health_probe=lambda *_args: True,
            runtime_digest_resolver=lambda _ref: C,
        )
    store.promote(
        "v1",
        ModelRole.CORE,
        health_probe=lambda *_args: True,
        runtime_digest_resolver=lambda _ref: B,
    )
    active = store.active_version(ModelRole.CORE)
    assert active is not None and active.version_id == "v1"


def test_role_scope_is_not_global_default(tmp_path: Path) -> None:
    store = registry(tmp_path)
    coder = version("coder", B, role=ModelRole.CODER)
    store.register(coder)
    with pytest.raises(ValueError, match="not eligible"):
        store.promote("coder", ModelRole.CORE, health_probe=lambda *_args: True)


def test_tampered_record_digest_rejected_on_reload(tmp_path: Path) -> None:
    store = registry(tmp_path)
    store.register(version("v1", B))
    document = json.loads(store.path.read_text(encoding="utf-8"))
    document["records"]["v1"]["base_digest"] = C
    store.path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        SpecializedModelRegistry(store.path).record("v1")
