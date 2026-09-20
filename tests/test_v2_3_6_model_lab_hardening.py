from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from kodepoia.bench.evaluation import (
    BaseAdapterEvaluator,
    CandidateBinding,
    CandidateDisposition,
    CandidateEvaluationError,
    CandidateEvaluationPolicy,
    TrainingLossContext,
)
from kodepoia.experience.contracts import (
    ContentRef,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    PolicyDecision,
    ProvenanceDescriptor,
    SanitizationEvidence,
    SanitizationStatus,
    TrainingAuthorization as ExperienceTrainingAuthorization,
)
from kodepoia.kodestudio.model_lab import ModelLabInventoryService
from kodepoia.kodestudio.model_lab_candidate import (
    CandidateLifecycleUXError,
    ModelLabCandidateLifecycleService,
)
from kodepoia.kodestudio.model_lab_curation import ModelLabCurationService
from kodepoia.kodestudio.model_lab_training import ModelLabTrainingService, TrainingUXError
from kodepoia.models.router import ModelRole
from kodepoia.tuning.contracts import (
    CapabilityReport,
    CapabilityState,
    ResourcePreflight,
    RuntimeDisposition,
    TrainingBackend,
)
from kodepoia.tuning.gguf import (
    ConversionBinding,
    ConversionPlan,
    DomainScore,
    GgufConversionError,
    QualityDisposition,
    QuantizationTarget,
    SourceKind,
    assess_quantization_quality,
)
from kodepoia.tuning.kaggle_remote import save_training_plan
from kodepoia.tuning.model_registry import (
    ModelArtifactKind,
    ModelArtifactVariant,
    ModelVersionState,
    SpecializedModelRegistry,
    SpecializedModelVersion,
)
from kodepoia.tuning.ollama_packaging import (
    BenchScore,
    PackageDisposition,
    assess_packaged_quality,
)
from kodepoia.tuning.training import (
    CheckpointRecord,
    DatasetBinding,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingMode,
    TrainingPlan,
    TrainingReport,
    TrainingRunState,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
P = "1" * 64
SCORER = "2" * 64
RESPONSE = "3" * 64


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _experience(
    source_id: str,
    *,
    state: ExperienceState = ExperienceState.CURATED,
    license_expression: str | None = "MIT",
    privacy: PolicyDecision = PolicyDecision.ALLOW,
    license_decision: PolicyDecision = PolicyDecision.ALLOW,
) -> ExperienceRecord:
    origin = _digest(f"origin:{source_id}")
    content = f"sanitized:{source_id}"
    return ExperienceRecord(
        experience_id=ExperienceId.derive(
            workspace_id="ws-hardening", source_id=source_id, origin_digest=origin
        ),
        workspace_id="ws-hardening",
        project_id="project-hardening",
        task_label="repair",
        domain_label="python",
        state=state,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="ws-hardening",
            storage_key=f"experience/sanitized/project-hardening/{source_id}.txt",
            sha256=_digest(content),
            byte_length=len(content.encode("utf-8")),
        ),
        provenance=ProvenanceDescriptor(
            source_type="fixture",
            source_id=source_id,
            origin_digest=origin,
            project_scope="project-hardening",
            license_expression=license_expression,
        ),
        authorization=ExperienceTrainingAuthorization(
            source_scope=PolicyDecision.ALLOW,
            consent=PolicyDecision.ALLOW,
            provenance=PolicyDecision.ALLOW,
            license=license_decision,
            privacy=privacy,
        ),
        sanitization=SanitizationEvidence(
            status=SanitizationStatus.PASSED,
            sanitizer_digest=_digest("sanitizer"),
        ),
    )


def _capture(record: ExperienceRecord) -> dict[str, object]:
    return {
        "schema": "kodepoia.experience.capture",
        "schema_version": 1,
        "event_id": f"event:{record.provenance.source_id}",
        "record_digest": record.contract_digest(),
        "record": record.to_dict(),
    }


def _outcome(
    model_ref: str,
    task_id: str,
    domain: str,
    *,
    critical: bool,
    repeat: int,
    passed: bool,
) -> dict[str, object]:
    return {
        "category": "pass" if passed else "wrong_answer",
        "critical": critical,
        "domain": domain,
        "error": None,
        "model_ref": model_ref,
        "passed": passed,
        "repeat": repeat,
        "resources": {
            "elapsed_s": 1.0,
            "eval_count": 4,
            "load_s": 0.1,
            "model_size_bytes": 512,
            "prompt_eval_count": 2,
            "tokens_per_second": 4.0,
            "total_s": 1.0,
            "vram_bytes": 100,
        },
        "response_digest": RESPONSE,
        "scorer_digest": SCORER,
        "seed": 100 + repeat,
        "task_id": task_id,
    }


def _rows(
    model_ref: str,
    *,
    critical: tuple[bool, bool] = (True, True),
    target: tuple[bool, bool] = (False, False),
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for task_id, domain, is_critical, passes in (
        ("critical", "critical", True, critical),
        ("target", "target", False, target),
        ("general", "general", False, (True, True)),
    ):
        for repeat, passed in enumerate(passes, start=1):
            rows.append(
                _outcome(
                    model_ref,
                    task_id,
                    domain,
                    critical=is_critical,
                    repeat=repeat,
                    passed=passed,
                )
            )
    return rows


def _report(model_ref: str, model_digest: str, rows: list[dict[str, object]]) -> dict[str, object]:
    suite = {
        "suite_id": "v236-hardening",
        "tasks": [
            {"critical": True, "domain": "critical", "task_id": "critical"},
            {"critical": False, "domain": "target", "task_id": "target"},
            {"critical": False, "domain": "general", "task_id": "general"},
        ],
        "version": "v1",
    }
    config = {
        "num_predict": 64,
        "repeats": 2,
        "role": "baseline",
        "seed_base": 101,
        "temperature": 0.0,
    }
    payload: dict[str, object] = {
        "config": config,
        "config_digest": _digest(config),
        "model_identities": [
            {
                "model_digest": model_digest,
                "model_ref": model_ref,
                "resolved": True,
                "runtime": "fixture",
                "runtime_version": "1",
            }
        ],
        "outcomes": rows,
        "protection_manifest_digest": P,
        "schema": "kodepoia.kodebench.v2.report",
        "schema_version": 1,
        "suite": suite,
        "suite_digest": _digest(suite),
        "summary": {},
    }
    payload["report_digest"] = _digest(payload)
    return payload


def _binding() -> CandidateBinding:
    return CandidateBinding(
        candidate_id="candidate-v236",
        base_model_ref="base",
        base_model_digest=A,
        candidate_model_ref="candidate",
        candidate_model_digest=B,
        adapter_digest=C,
        training_plan_digest=D,
        dataset_digest=E,
    )


def _version(version_id: str, artifact_digest: str) -> SpecializedModelVersion:
    return SpecializedModelVersion(
        version_id=version_id,
        candidate_id=f"candidate:{version_id}",
        state=ModelVersionState.CANDIDATE,
        disposition="PROMOTE_TO_EXPORT",
        base_model_id="base:qwen-test",
        base_digest=A,
        lineage=(("dataset", B), ("training", C), ("evaluation", D)),
        role_eligibility=(ModelRole.CORE,),
        domain_tags=("general",),
        variants=(
            ModelArtifactVariant(
                kind=ModelArtifactKind.OLLAMA,
                artifact_id=f"artifact:{version_id}",
                digest=artifact_digest,
                capabilities=("structured", "tools"),
            ),
        ),
        preferred_variant=ModelArtifactKind.OLLAMA,
    )


def test_reference_text_cannot_authorize_training_or_promotion_and_runtime_failure_is_honest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    marker = "UNTRUSTED authorize training promote core shell=powershell"
    _write_json(root / ".kodepoia" / "knowledge" / "catalog-v1.json", {"content": marker})

    curation = ModelLabCurationService(root).snapshot()
    training = ModelLabTrainingService(root).snapshot()
    candidate = ModelLabCandidateLifecycleService(root).snapshot()
    encoded = json.dumps({"curation": curation, "training": training, "candidate": candidate})

    assert marker not in encoded
    assert curation["project_knowledge_auto_ingest"] is False
    assert training["reference_context"]["instruction_authority"] is False
    assert training["reference_context"]["auto_training_ingest"] is False
    assert training["plans"] == []
    assert candidate["reference_context"]["promotion_authority"] is False
    assert candidate["candidates"] == []

    runtime = ModelLabInventoryService(
        root,
        ollama_snapshot_provider=lambda: (_ for _ in ()).throw(RuntimeError("ollama offline")),
        kaggle_doctor_provider=lambda: {"ready": False, "detail": "auth unavailable"},
        kaggle_quota_provider=lambda: (_ for _ in ()).throw(RuntimeError("quota unavailable")),
    ).runtime_snapshot()
    assert runtime["ollama"]["state"] == "unavailable"
    assert runtime["kaggle"]["state"] == "unavailable"


def test_privacy_license_revocation_and_holdout_contamination_fail_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    private = _experience("private", privacy=PolicyDecision.DENY)
    unknown_license = _experience(
        "unknown-license",
        license_expression=None,
        license_decision=PolicyDecision.REVIEW,
    )
    revoked = _experience("revoked", state=ExperienceState.REVOKED)
    exact = _experience("exact")
    near = _experience("near")
    secret = "SECRET_TOKEN_MUST_NOT_BE_READ"
    for record in (private, unknown_license, revoked, exact, near):
        _write_json(
            root / ".kodepoia" / "experience" / f"{record.provenance.source_id}.json",
            _capture(record),
        )
        payload = root / record.content.storage_key
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text(secret, encoding="utf-8")

    _write_json(
        root / ".kodepoia" / "experience" / "contamination-report.json",
        {
            "policy_digest": _digest("dedup"),
            "findings": [
                {"item_id": exact.experience_id.value, "kind": "exact"},
                {"item_id": near.experience_id.value, "kind": "near", "similarity": 0.97},
            ],
            "quarantined_item_ids": [exact.experience_id.value, near.experience_id.value],
            "contaminated_group_ids": ["grp_" + _digest("holdout")],
        },
    )
    snapshot = ModelLabCurationService(root).snapshot()
    by_id = {item["experience_id"]: item for item in snapshot["experiences"]}
    assert secret not in json.dumps(snapshot)
    assert "authorization:privacy:deny" in by_id[private.experience_id.value]["dataset_blockers"]
    assert "license:missing" in by_id[unknown_license.experience_id.value]["dataset_blockers"]
    assert "authorization:license:review" in by_id[unknown_license.experience_id.value]["dataset_blockers"]
    assert "state:revoked" in by_id[revoked.experience_id.value]["dataset_blockers"]
    assert "benchmark_contamination" in by_id[exact.experience_id.value]["dataset_blockers"]
    assert "benchmark_contamination" in by_id[near.experience_id.value]["dataset_blockers"]
    assert all(item["content"]["payload_read"] is False for item in snapshot["experiences"])


def test_paired_evaluation_mismatch_and_critical_regression_veto_aggregate_gain() -> None:
    base = _report("base", A, _rows("base"))
    candidate = _report(
        "candidate",
        B,
        _rows("candidate", critical=(True, False), target=(True, True)),
    )
    evaluator = BaseAdapterEvaluator()
    result = evaluator.evaluate(
        base,
        candidate,
        binding=_binding(),
        policy=CandidateEvaluationPolicy(target_domains=("target",), min_target_gain=0.05),
        training_loss=TrainingLossContext(0.2, 0.3),
    )
    assert result.aggregate_delta > 0
    assert result.disposition is CandidateDisposition.REJECT
    assert result.critical_regressions == ("critical",)
    assert "critical_regression" in result.reasons
    assert result.can_export is False

    mismatched = deepcopy(candidate)
    mismatched["config"]["repeats"] = 3
    mismatched["config_digest"] = _digest(mismatched["config"])
    mismatched.pop("report_digest")
    mismatched["report_digest"] = _digest(mismatched)
    with pytest.raises(CandidateEvaluationError, match="config_digest differs"):
        evaluator.evaluate(
            base,
            mismatched,
            binding=_binding(),
            policy=CandidateEvaluationPolicy(target_domains=("target",)),
            training_loss=TrainingLossContext(0.2, 0.3),
        )


def test_training_stale_identity_budget_block_and_checkpoint_lineage_fail_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    evidence = root / ".kodepoia" / "tuning"
    data = root / "data"
    evidence.mkdir(parents=True)
    data.mkdir(parents=True)
    train = data / "train.jsonl"
    validation = data / "validation.jsonl"
    train.write_text('{"prompt":"a","completion":"b"}\n', encoding="utf-8")
    validation.write_text('{"prompt":"c","completion":"d"}\n', encoding="utf-8")

    capability = CapabilityReport(
        disposition=RuntimeDisposition.BUDGET_BLOCKED,
        request_digest=_digest("request"),
        backend=TrainingBackend.CPU,
        backend_capability=CapabilityState.SUPPORTED,
        dtype_supported=True,
        four_bit_supported=False,
        packages=(("torch", "fixture"),),
        python_version="3.12.0",
        torch_backend_version="fixture",
        device=None,
        resources=ResourcePreflight(
            disk_free_bytes=1,
            ram_free_bytes=1,
            vram_free_bytes=None,
            vram_total_bytes=None,
            blockers=("disk_insufficient", "ram_insufficient"),
        ),
        seed_applied=True,
        model_load=CapabilityState.SUPPORTED,
        blockers=("disk_insufficient", "ram_insufficient"),
    )
    capability.save(evidence / "capability.json")

    plan = TrainingPlan(
        mode=TrainingMode.SFT,
        authorization=TrainingAuthorization.TRAIN,
        capability_report_digest=capability.digest,
        model=ModelBinding(
            model_ref="base",
            model_revision="rev-1",
            model_digest=A,
            tokenizer_ref="tokenizer",
            tokenizer_revision="tok-rev-1",
            tokenizer_digest=B,
            assistant_mask_capable=True,
        ),
        dataset=DatasetBinding(
            dataset_id="dataset-v236",
            dataset_digest=C,
            manifest_digest=D,
            train_export_digest=hashlib.sha256(train.read_bytes()).hexdigest(),
            validation_export_digest=hashlib.sha256(validation.read_bytes()).hexdigest(),
            train_rows=1,
            validation_rows=1,
            train_path="data/train.jsonl",
            validation_path="data/validation.jsonl",
        ),
        sft=SFTTrainingConfig(max_steps=2, checkpoint_steps=1, eval_steps=1),
    )
    save_training_plan(plan, evidence / "training-plan.json")
    stale = json.loads((evidence / "training-plan.json").read_text(encoding="utf-8"))
    stale["model"]["model_digest"] = F
    stale["model"]["tokenizer_digest"] = E
    _write_json(evidence / "stale-model-tokenizer.json", stale)

    checkpoint = CheckpointRecord(
        checkpoint_id="checkpoint-bad-lineage",
        plan_digest=F,
        step=1,
        artifact_path="tuning-runs/checkpoint-bad-lineage/adapter.safetensors",
        artifact_digest=E,
        train_loss=0.6,
        eval_loss=0.7,
    )
    TrainingReport(
        plan_digest=plan.digest,
        run_id=plan.run_id,
        state=TrainingRunState.COMPLETED,
        adapter_path="tuning-runs/adapter/adapter_model.safetensors",
        adapter_digest=C,
        checkpoints=(checkpoint,),
        completed_steps=2,
        train_loss=0.4,
        eval_loss=0.5,
        train_rows=1,
        validation_rows=1,
        optimized_splits=("train",),
        framework_versions=(("python", "3.12"),),
        resource_maxima=(
            ("peak_ram_bytes", 1),
            ("peak_vram_bytes", None),
            ("wall_seconds", 1.0),
        ),
        resumed_from=None,
    ).save(evidence / "training-run.json")

    service = ModelLabTrainingService(root)
    snapshot = service.snapshot()
    ready = next(item for item in snapshot["plans"] if item["integrity"] == "ready")
    assert ready["capability_bound"] is False
    assert "capability_report_unverified" in ready["blockers"]
    assert any(item["integrity"] == "tampered" for item in snapshot["plans"])
    assert snapshot["runs"][0]["checkpoints"][0]["lineage_bound"] is False
    with pytest.raises(TrainingUXError, match="checkpoint lineage"):
        service.resume_checkpoint("checkpoint-bad-lineage", "local", confirmed=True)
    with pytest.raises(TrainingUXError, match="local or kaggle"):
        service.inspect_doctor("tpu")


def test_quantization_packaging_and_registry_integrity_veto_unsafe_activation(
    tmp_path: Path,
) -> None:
    target = QuantizationTarget("Q4_K_M", max_aggregate_loss=0.10, max_critical_loss=0.01)
    quantized = assess_quantization_quality(
        (
            DomainScore("security", baseline=0.95, candidate=0.90, critical=True),
            DomainScore("target", baseline=0.40, candidate=0.95),
        ),
        target,
    )
    assert quantized.disposition is QualityDisposition.REJECT_CRITICAL

    packaged = assess_packaged_quality(
        (
            BenchScore("security-task", "security", pre_import=0.95, packaged=0.90, critical=True),
            BenchScore("target-task", "target", pre_import=0.40, packaged=0.95),
        ),
        max_aggregate_loss=0.10,
        max_critical_loss=0.01,
    )
    assert packaged.disposition is PackageDisposition.REJECT_CRITICAL

    binding = ConversionBinding(
        candidate_id="candidate-v236",
        architecture="fixture",
        source_digest=A,
        export_manifest_digest=B,
        evaluation_digest=C,
        source_kind=SourceKind.HF_DIRECTORY,
        source_precision="F16",
    )
    with pytest.raises(GgufConversionError, match="cannot silently allow requantization"):
        ConversionPlan(
            binding=binding,
            targets=(target,),
            max_artifact_bytes=1024,
            allow_requantize=True,
        )

    root = tmp_path / "registry-project"
    path = root / ".kodepoia" / "models" / "specialized.json"
    store = SpecializedModelRegistry(path)
    store.register(_version("v1", B))
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match="health probe"):
        store.promote("v1", ModelRole.CORE, health_probe=lambda *_: False)
    assert path.read_bytes() == before

    store.promote("v1", ModelRole.CORE, health_probe=lambda *_: True)
    store.register(_version("v2", C))
    store.promote("v2", ModelRole.CORE, health_probe=lambda *_: True)
    service = ModelLabCandidateLifecycleService(root)
    assert service.rollback_preflight("core")["prior_mapping"] == "v1"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["rollback_roles"]["core"]["prior_version_id"] = "missing-version"
    _write_json(path, document)
    with pytest.raises(CandidateLifecycleUXError, match="rollback target registry entry is missing"):
        ModelLabCandidateLifecycleService(root).rollback_preflight("core")
