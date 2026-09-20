from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.kodestudio.model_lab_candidate import (
    CandidateLifecycleUXError,
    ModelLabCandidateLifecycleService,
)
from kodepoia.models.router import ModelRole
from kodepoia.tuning.model_registry import (
    ModelArtifactKind,
    ModelArtifactVariant,
    ModelVersionState,
    SpecializedModelRegistry,
    SpecializedModelVersion,
)
from kodepoia.tuning.r15_ux import R15UXPolicyError, R15UXService, R15WorkflowRequest

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def _save(root: Path, name: str, payload: dict[str, object], digest_key: str) -> str:
    descriptor = dict(payload)
    descriptor.pop(digest_key, None)
    payload[digest_key] = _digest(descriptor)
    path = root / ".kodepoia" / "tuning" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(payload[digest_key])


def _evaluation(candidate_id: str = "candidate-1", *, disposition: str = "promote_to_export") -> dict[str, object]:
    can_export = disposition == "promote_to_export"
    return {
        "schema": "kodepoia.r15.10.candidate-evaluation",
        "schema_version": 1,
        "binding": {
            "candidate_id": candidate_id,
            "base_model_ref": "base",
            "base_model_digest": A,
            "candidate_model_ref": "candidate",
            "candidate_model_digest": B,
            "adapter_digest": C,
            "training_plan_digest": D,
            "dataset_digest": E,
        },
        "binding_digest": F,
        "policy": {"version": "fixture"},
        "policy_digest": F,
        "reports": {"base": A, "candidate": B},
        "suite_digest": C,
        "config_digest": D,
        "protection_manifest_digest": E,
        "aggregate": {"base_score": 0.5, "candidate_score": 0.75, "delta": 0.25, "target_gain": 0.5},
        "task_deltas": {
            "critical": {
                "base_score": 1.0,
                "candidate_score": 1.0,
                "critical": True,
                "delta": 0.0,
                "domain": "security",
                "pairs": 2,
            }
        },
        "domain_deltas": {
            "security": {"base_score": 1.0, "candidate_score": 1.0, "delta": 0.0, "pairs": 2},
            "target": {"base_score": 0.0, "candidate_score": 1.0, "delta": 1.0, "pairs": 2},
        },
        "critical_regressions": [],
        "errors": {"base": 0, "candidate": 0, "delta": 0},
        "repeat_stddev": {"base": 0.0, "candidate": 0.0},
        "resources": {
            "elapsed_s_mean": {"base": 1.0, "candidate": 1.1, "ratio": 1.1},
            "tokens_per_second_mean": {"base": 4.0, "candidate": 4.2, "ratio": 1.05},
            "vram_bytes_mean": {"base": 100, "candidate": 105, "ratio": 1.05},
        },
        "overfit_risk": False,
        "disposition": disposition,
        "reasons": ["promotion_thresholds_satisfied"] if can_export else ["critical_regression"],
        "training_loss": {"train_loss": 0.2, "validation_loss": 0.3, "validation_to_train_ratio": 1.5},
        "can_export": can_export,
    }


def _write_chain(root: Path, candidate_id: str = "candidate-1") -> dict[str, str]:
    evaluation = _evaluation(candidate_id)
    evaluation_digest = _save(root, "evaluation.json", evaluation, "evaluation_digest")
    export = {
        "schema": "kodepoia.r15.11.model-export",
        "schema_version": 1,
        "binding": {
            "candidate_id": candidate_id,
            "evaluation_digest": evaluation_digest,
            "training_plan_digest": D,
            "dataset_digest": E,
            "adapter_digest": C,
            "base_model_ref": "base",
            "base_model_digest": A,
        },
        "adapter": {"tree_digest": C, "files": [{"path": "adapter.safetensors", "sha256": C}]},
        "merge": {"disposition": "merged", "files": [{"path": "model.safetensors", "sha256": D}]},
        "model_card": {"path": "README.md", "sha256": E},
        "source_overwritten": False,
    }
    export_digest = _save(root, "export.json", export, "manifest_digest")
    conversion = {
        "schema": "kodepoia.r15.12.gguf-conversion",
        "schema_version": 1,
        "binding": {
            "candidate_id": candidate_id,
            "evaluation_digest": evaluation_digest,
            "export_manifest_digest": export_digest,
            "source_digest": C,
            "source_kind": "hf_directory",
            "source_precision": "F16",
        },
        "high_precision": {"operation": "convert", "quant_type": "F16"},
        "variants": [
            {
                "artifact": {
                    "quant_type": "Q4_K_M",
                    "output": {"sha256": D, "size_bytes": 1024},
                },
                "quality": {
                    "disposition": "accept",
                    "aggregate_loss": 0.01,
                    "critical_regressions": [],
                },
            }
        ],
    }
    conversion_digest = _save(root, "conversion.json", conversion, "report_digest")
    package = {
        "schema": "kodepoia.r15.13.ollama-package",
        "schema_version": 1,
        "binding": {
            "candidate_id": candidate_id,
            "artifact_kind": "gguf",
            "artifact_sha256": D,
            "base_model": "base:fixture",
            "base_digest": A,
            "evaluation_digest": evaluation_digest,
            "export_manifest_digest": export_digest,
            "gguf_report_digest": conversion_digest,
        },
        "candidate_tag": "kodepoia-candidate-candidate-1:r15-13-fixture",
        "ollama_version": "fixture",
        "model_digest": F,
        "quality": {"disposition": "accept", "aggregate_loss": 0.01, "critical_regressions": []},
        "behavior": {"structured_output": True, "tool_call": True},
        "provider_live_claim": False,
        "public_push": False,
        "secrets_exposed": False,
    }
    package_digest = _save(root, "package.json", package, "report_digest")
    return {
        "evaluation": evaluation_digest,
        "export": export_digest,
        "conversion": conversion_digest,
        "package": package_digest,
    }


def _register_candidate(root: Path, digests: dict[str, str], candidate_id: str = "candidate-1") -> None:
    store = SpecializedModelRegistry(root / ".kodepoia" / "models" / "specialized.json")
    store.register(
        SpecializedModelVersion(
            version_id="version-1",
            candidate_id=candidate_id,
            state=ModelVersionState.CANDIDATE,
            disposition="PROMOTE_TO_EXPORT",
            base_model_id="base-fixture",
            base_digest=A,
            lineage=tuple(sorted(digests.items())),
            role_eligibility=(ModelRole.CORE,),
            domain_tags=("target",),
            variants=(
                ModelArtifactVariant(
                    kind=ModelArtifactKind.OLLAMA,
                    artifact_id="artifact-version-1",
                    digest=F,
                    runtime_ref="kodepoia-candidate-candidate-1:r15-13-fixture",
                    capabilities=("structured", "tools"),
                ),
            ),
            preferred_variant=ModelArtifactKind.OLLAMA,
        )
    )


def test_snapshot_projects_paired_evaluation_artifacts_and_registry(tmp_path: Path) -> None:
    digests = _write_chain(tmp_path)
    _register_candidate(tmp_path, digests)
    payload = ModelLabCandidateLifecycleService(tmp_path).snapshot()
    assert payload["schema"] == "kodepoia.v2.3.5.model-lab-candidate-lifecycle"
    assert payload["candidates"][0]["candidate_id"] == "candidate-1"
    assert payload["candidates"][0]["promotable_evaluation"] is True
    assert payload["candidates"][0]["accepted_package"] is True
    assert payload["evaluations"][0]["critical_regressions"] == []
    assert payload["evaluations"][0]["domain_deltas"]["target"]["delta"] == 1.0
    assert payload["conversions"][0]["accepted_variants"] == 1
    assert payload["packages"][0]["public_push"] is False
    record = payload["registry"]["records"][0]
    assert record["preferred_variant"] == "ollama"
    assert record["variants"][0]["artifact_id"] == "artifact-version-1"
    assert payload["reference_context"]["promotion_authority"] is False
    assert payload["boundaries"]["v2_3_6"] is False


def test_export_conversion_and_package_mutations_are_typed_dry_run_then_confirmed(tmp_path: Path) -> None:
    _write_chain(tmp_path)
    calls: list[R15WorkflowRequest] = []

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "ok", "candidate_id": request.identifier}

    r15 = R15UXService(
        tmp_path,
        handlers={
            "export.run": handler,
            "conversion.run": handler,
            "ollama.package": handler,
        },
    )
    service = ModelLabCandidateLifecycleService(tmp_path, r15_service=r15)
    assert service.preview_export("candidate-1")["request"]["status"] == "dry_run"
    assert service.preview_conversion("candidate-1")["request"]["status"] == "dry_run"
    assert service.preview_package("candidate-1")["request"]["status"] == "dry_run"
    assert calls == []

    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.export_candidate("candidate-1")
    service.export_candidate("candidate-1", confirmed=True)
    service.run_conversion("candidate-1", confirmed=True)
    service.package_candidate("candidate-1", confirmed=True)
    assert [request.key for request in calls] == [
        "export.run",
        "conversion.run",
        "ollama.package",
    ]


def test_promotion_is_evidence_bound_role_specific_and_confirmed(tmp_path: Path) -> None:
    digests = _write_chain(tmp_path)
    _register_candidate(tmp_path, digests)
    calls: list[R15WorkflowRequest] = []

    def promote(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "ok", "version_id": request.identifier, "role": request.role}

    service = ModelLabCandidateLifecycleService(
        tmp_path,
        r15_service=R15UXService(tmp_path, handlers={"registry.promote": promote}),
    )
    preview = service.preview_promotion("candidate-1", "core")
    assert preview["preflight"]["current_mapping"] is None
    assert preview["preflight"]["proposed_mapping"] == "version-1"
    assert preview["preflight"]["artifact"]["digest"] == F
    assert preview["request"]["status"] == "dry_run"
    assert calls == []

    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.promote("candidate-1", "core")
    result = service.promote("candidate-1", "core", confirmed=True)
    assert result["request"]["role"] == "core"
    assert calls[0].identifier == "version-1"
    assert calls[0].role == "core"


def test_critical_rejection_or_tampered_lineage_fails_closed(tmp_path: Path) -> None:
    rejected = _evaluation(disposition="reject")
    rejected["critical_regressions"] = ["security"]
    rejected["reasons"] = ["critical_regression"]
    _save(tmp_path, "evaluation.json", rejected, "evaluation_digest")
    service = ModelLabCandidateLifecycleService(tmp_path)
    with pytest.raises(CandidateLifecycleUXError, match="not PROMOTE_TO_EXPORT"):
        service.preview_export("candidate-1")

    other = tmp_path / "tampered"
    digests = _write_chain(other)
    _register_candidate(other, {**digests, "package": A})
    with pytest.raises(CandidateLifecycleUXError, match="registry lineage"):
        ModelLabCandidateLifecycleService(other).promotion_preflight("candidate-1", "core")


def test_rollback_preflight_preserves_exact_prior_mapping(tmp_path: Path) -> None:
    store = SpecializedModelRegistry(tmp_path / ".kodepoia" / "models" / "specialized.json")

    def version(version_id: str, digest: str) -> SpecializedModelVersion:
        return SpecializedModelVersion(
            version_id=version_id,
            candidate_id=f"candidate-{version_id}",
            state=ModelVersionState.CANDIDATE,
            disposition="PROMOTE_TO_EXPORT",
            base_model_id="base-fixture",
            base_digest=A,
            lineage=(("evaluation", B),),
            role_eligibility=(ModelRole.CORE,),
            domain_tags=("target",),
            variants=(
                ModelArtifactVariant(
                    kind=ModelArtifactKind.OLLAMA,
                    artifact_id=f"artifact-{version_id}",
                    digest=digest,
                    capabilities=("structured",),
                ),
            ),
            preferred_variant=ModelArtifactKind.OLLAMA,
        )

    store.register(version("version-1", C))
    store.register(version("version-2", D))
    store.promote("version-1", ModelRole.CORE, health_probe=lambda *_: True)
    store.promote("version-2", ModelRole.CORE, health_probe=lambda *_: True)

    calls: list[R15WorkflowRequest] = []
    service = ModelLabCandidateLifecycleService(
        tmp_path,
        r15_service=R15UXService(
            tmp_path,
            handlers={"registry.rollback": lambda request: calls.append(request) or {"status": "ok"}},
        ),
    )
    preflight = service.rollback_preflight("core")
    assert preflight["current_mapping"] == "version-2"
    assert preflight["prior_mapping"] == "version-1"
    preview = service.preview_rollback("core")
    assert preview["request"]["status"] == "dry_run"
    assert calls == []
    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.rollback("core")
    service.rollback("core", confirmed=True)
    assert calls[0].role == "core"
