from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Callable, TypeVar

from kodepoia.bench.decision import (
    BackendCapability,
    BudgetStatus,
    DecisionDisposition,
    DecisionEvidence,
    DiagnosticComponent,
    DiagnosticProbe,
    ExpectedImpact,
    GapDecisionEngine,
    ProbeStatus,
)
from kodepoia.bench.evaluation import (
    BaseAdapterEvaluator,
    CandidateBinding,
    CandidateDisposition,
    CandidateEvaluationError,
    CandidateEvaluationPolicy,
    TrainingLossContext,
)
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.experience.contracts import (
    ContentRef,
    EligibilityDenied,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    PolicyDecision,
    ProvenanceDescriptor,
    SanitizationEvidence,
    SanitizationStatus,
    TrainingAuthorization as ExperienceTrainingAuthorization,
    TransformationRef,
    transition_experience,
)
from kodepoia.experience.dataset import (
    DatasetBuilder,
    DatasetPolicy,
    DatasetSource,
    DatasetSplit,
    DuplicateHandling,
)
from kodepoia.experience.dedup import (
    DedupItem,
    DedupPolicy,
    ProtectedHoldout,
    ProtectedHoldoutRegistry,
    cluster_items,
    fingerprint_text,
    scan_contamination,
)
from kodepoia.experience.governance import (
    GovernancePolicy,
    RevocationIndex,
    sanitize_experience,
)
from kodepoia.models.router import ModelRole
from kodepoia.tuning.export import (
    ExportBinding,
    ExportRequest,
    ModelExportError,
    export_candidate,
)
from kodepoia.tuning.gguf import (
    ConversionBinding,
    ConversionPlan,
    DomainScore,
    GgufConversionError,
    GgufToolchain,
    QualityDisposition,
    QuantizationTarget,
    SourceKind,
    assess_quantization_quality,
    digest_path,
    run_high_precision_conversion,
)
from kodepoia.tuning.model_registry import (
    ModelArtifactKind,
    ModelArtifactVariant,
    ModelVersionState,
    SpecializedModelRegistry,
    SpecializedModelVersion,
)
from kodepoia.tuning.ollama_packaging import (
    ArtifactKind,
    OllamaBinding,
    OllamaPackagingError,
)
from kodepoia.tuning.runtime import HostResources
from kodepoia.tuning.training import (
    DatasetBinding,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization as TuningTrainingAuthorization,
    TrainingError,
    TrainingMode,
    TrainingPlan,
    TrainingRunner,
    TrainingRunState,
)

INTEGRATED_SCHEMA = "kodepoia.r15.integrated-acceptance"
CHECK_NAMES = (
    "unvalidated_unopted_experience_blocked",
    "secret_private_fixture_not_emitted",
    "unknown_disallowed_license_blocked",
    "revocation_invalidates_dependent_lineage",
    "duplicate_groups_do_not_cross_splits",
    "benchmark_holdout_training_firewall",
    "mixed_identity_evidence_rejected",
    "system_defect_yields_fix_system_first",
    "qlora_resume_lineage_mismatch_rejected",
    "critical_regression_veto",
    "wrong_base_export_ollama_rejected",
    "quantization_quality_loss_rejected",
    "rejected_promotion_and_exact_rollback",
    "optional_capability_truthful_unavailable",
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_T = TypeVar("_T", bound=BaseException)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _tree_digest(path: Path) -> str:
    rows = []
    for item in sorted(
        (entry for entry in path.rglob("*") if entry.is_file()),
        key=lambda entry: entry.relative_to(path).as_posix(),
    ):
        rows.append(
            {
                "path": item.relative_to(path).as_posix(),
                "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
                "size_bytes": item.stat().st_size,
            }
        )
    return canonical_sha256(rows)


def _expect(exc_type: type[_T], action: Callable[[], object]) -> bool:
    try:
        action()
    except exc_type:
        return True
    return False


def _allowed_governance() -> GovernancePolicy:
    return GovernancePolicy(
        allowed_source_types=frozenset({"repository_fixture"}),
        trusted_provenance_source_types=frozenset({"repository_fixture"}),
        allowed_licenses=frozenset({"MIT", "Apache-2.0"}),
    )


def _experience_record(
    source_id: str,
    text: str,
    *,
    license_expression: str | None = "MIT",
    authorization: ExperienceTrainingAuthorization | None = None,
    state: ExperienceState = ExperienceState.OBSERVED,
    sanitizer_digest: str | None = None,
    governance_digest: str | None = None,
) -> ExperienceRecord:
    origin_digest = _digest_text(f"origin:{source_id}")
    content_digest = _digest_text(text)
    transformations = ()
    sanitization = SanitizationEvidence()
    if sanitizer_digest is not None and governance_digest is not None:
        sanitization = SanitizationEvidence(
            status=SanitizationStatus.PASSED,
            sanitizer_digest=sanitizer_digest,
        )
        transformations = (
            TransformationRef(
                transformation_id="r15.17-fixture-sanitize",
                input_digest=origin_digest,
                output_digest=content_digest,
                policy_digest=governance_digest,
            ),
        )
    return ExperienceRecord(
        experience_id=ExperienceId.derive(
            workspace_id="r15-17-workspace",
            source_id=source_id,
            origin_digest=origin_digest,
        ),
        workspace_id="r15-17-workspace",
        project_id="r15-17-project",
        task_label="repair",
        domain_label="python",
        state=state,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="r15-17-workspace",
            storage_key=f"experience/sanitized/r15-17/{content_digest}.txt",
            sha256=content_digest,
            byte_length=len(text.encode("utf-8")),
        ),
        provenance=ProvenanceDescriptor(
            source_type="repository_fixture",
            source_id=source_id,
            origin_digest=origin_digest,
            project_scope="r15-17-project",
            license_expression=license_expression,
        ),
        authorization=authorization or ExperienceTrainingAuthorization(),
        sanitization=sanitization,
        transformations=transformations,
    )


def _allowed_authorization() -> ExperienceTrainingAuthorization:
    return ExperienceTrainingAuthorization(
        source_scope=PolicyDecision.ALLOW,
        consent=PolicyDecision.ALLOW,
        provenance=PolicyDecision.ALLOW,
        license=PolicyDecision.ALLOW,
        privacy=PolicyDecision.ALLOW,
    )


def _dedup_item(source: DatasetSource, policy: DedupPolicy) -> DedupItem:
    return DedupItem(
        item_id=source.item_id,
        content_digest=source.record.content.sha256,
        fingerprint=fingerprint_text(source.text, policy),
    )


def _gap_report(dataset_digest: str) -> dict[str, object]:
    outcomes = []
    for repeat in range(2):
        outcomes.append(
            {
                "category": "wrong_answer",
                "critical": True,
                "domain": "python",
                "error": None,
                "model_ref": "fixture/base",
                "passed": False,
                "repeat": repeat,
                "resources": {},
                "response_digest": "1" * 64,
                "scorer_digest": "2" * 64,
                "seed": 1517 + repeat,
                "task_id": "python-gap",
            }
        )
    return {
        "config_digest": "3" * 64,
        "model_identities": [
            {
                "model_digest": "4" * 64,
                "model_ref": "fixture/base",
                "resolved": True,
                "runtime": "fixture",
                "runtime_version": "1",
            }
        ],
        "outcomes": outcomes,
        "protection_manifest_digest": "5" * 64,
        "suite_digest": "6" * 64,
        "dataset_digest": dataset_digest,
    }


def _diagnostics(
    defect: DiagnosticComponent | None = None,
) -> tuple[DiagnosticProbe, ...]:
    probes = []
    for index, component in enumerate(
        (
            DiagnosticComponent.TOOL,
            DiagnosticComponent.RETRIEVAL,
            DiagnosticComponent.ROUTER,
            DiagnosticComponent.CONTEXT,
        )
    ):
        status = ProbeStatus.DEFECT if component is defect else ProbeStatus.PASS
        probes.append(
            DiagnosticProbe(
                component,
                status,
                f"{index + 8:x}" * 64,
                ("python",) if status is ProbeStatus.DEFECT else (),
            )
        )
    return tuple(probes)


def _decision_evidence(
    defect: DiagnosticComponent | None = None,
) -> DecisionEvidence:
    return DecisionEvidence(
        benchmark_reproducible=True,
        contamination_valid=True,
        dataset_license=PolicyDecision.ALLOW,
        base_model_license=PolicyDecision.ALLOW,
        backend_capability=BackendCapability.SUPPORTED,
        budget_status=BudgetStatus.WITHIN_BUDGET,
        rollback_ready=True,
        expected_impact=ExpectedImpact.MEANINGFUL,
        diagnostics=_diagnostics(defect),
        evidence_digests=(("integrated", "c" * 64),),
    )


def _evaluation_outcome(
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
        "response_digest": "3" * 64,
        "scorer_digest": "2" * 64,
        "seed": 100 + repeat,
        "task_id": task_id,
    }


def _evaluation_rows(
    model_ref: str,
    *,
    critical: tuple[bool, bool],
    target: tuple[bool, bool],
    general: tuple[bool, bool],
) -> list[dict[str, object]]:
    rows = []
    for task_id, domain, is_critical, passes in (
        ("critical", "critical", True, critical),
        ("target", "target", False, target),
        ("general", "general", False, general),
    ):
        for repeat, passed in enumerate(passes, start=1):
            rows.append(
                _evaluation_outcome(
                    model_ref,
                    task_id,
                    domain,
                    critical=is_critical,
                    repeat=repeat,
                    passed=passed,
                )
            )
    return rows


def _evaluation_report(
    model_ref: str,
    model_digest: str,
    rows: list[dict[str, object]],
    *,
    protection_digest: str = "5" * 64,
) -> dict[str, object]:
    suite = {
        "suite_id": "r15-17-integrated",
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
        "config_digest": canonical_sha256(config),
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
        "protection_manifest_digest": protection_digest,
        "schema": "kodepoia.kodebench.v2.report",
        "schema_version": 1,
        "suite": suite,
        "suite_digest": canonical_sha256(suite),
        "summary": {},
    }
    payload["report_digest"] = canonical_sha256(payload)
    return payload


class _FixedResources:
    def sample(self, _root: Path) -> HostResources:
        return HostResources(10**12, 10**12)


def _training_plan(dataset_digest: str) -> TrainingPlan:
    model = ModelBinding(
        model_ref="fixture/base",
        model_revision="fixture-rev-1",
        model_digest="a" * 64,
        tokenizer_ref="fixture/tokenizer",
        tokenizer_revision="fixture-tokenizer-rev-1",
        tokenizer_digest="b" * 64,
        assistant_mask_capable=True,
    )
    dataset = DatasetBinding(
        dataset_id="r15-17-dataset",
        dataset_digest=dataset_digest,
        manifest_digest="d" * 64,
        train_export_digest="e" * 64,
        validation_export_digest="f" * 64,
        train_rows=8,
        validation_rows=3,
    )
    return TrainingPlan(
        mode=TrainingMode.FIXTURE_SFT,
        authorization=TuningTrainingAuthorization.FIXTURE,
        fixture_authorization="repository-owned-r15.17-fixture",
        model=model,
        dataset=dataset,
        sft=SFTTrainingConfig(max_steps=4, checkpoint_steps=2, eval_steps=2),
    )


def _registry_version(
    version_id: str,
    digest: str,
    *,
    state: ModelVersionState = ModelVersionState.CANDIDATE,
    disposition: str = "PROMOTE_TO_EXPORT",
) -> SpecializedModelVersion:
    return SpecializedModelVersion(
        version_id=version_id,
        candidate_id=f"candidate:{version_id}",
        state=state,
        disposition=disposition,
        base_model_id="base:r15-17",
        base_digest="a" * 64,
        lineage=(("dataset", "b" * 64), ("training", "c" * 64), ("evaluation", "d" * 64)),
        role_eligibility=(ModelRole.CORE,),
        domain_tags=("general",),
        variants=(
            ModelArtifactVariant(
                kind=ModelArtifactKind.OLLAMA,
                artifact_id=f"artifact:{version_id}",
                digest=digest,
                capabilities=("structured", "tools"),
            ),
        ),
        preferred_variant=ModelArtifactKind.OLLAMA,
    )


def _payload_without_digest(evidence: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in evidence.items() if key != "semantic_digest"}


def validate_integrated_evidence(evidence: dict[str, object]) -> None:
    required = {
        "schema",
        "schema_version",
        "source_sha",
        "checks",
        "check_count",
        "identities",
        "manual_state",
        "optional_capability_state",
        "secrets_exposed",
        "status",
        "blockers",
        "semantic_digest",
    }
    if set(evidence) != required:
        raise ValueError("R15.17 integrated evidence has invalid keys")
    if evidence["schema"] != INTEGRATED_SCHEMA or evidence["schema_version"] != 1:
        raise ValueError("unsupported R15.17 integrated evidence schema")
    source_sha = evidence["source_sha"]
    if not isinstance(source_sha, str) or _COMMIT.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be an exact lowercase commit SHA")
    checks = evidence["checks"]
    if not isinstance(checks, dict) or tuple(checks) != CHECK_NAMES:
        raise ValueError("R15.17 integrated check inventory mismatch")
    if evidence["check_count"] != len(CHECK_NAMES):
        raise ValueError("R15.17 integrated check count mismatch")
    if not all(value is True for value in checks.values()):
        raise ValueError("R15.17 cannot pass while an adversarial check is false")
    identities = evidence["identities"]
    if not isinstance(identities, dict) or not identities:
        raise ValueError("R15.17 identities are required")
    for name, value in identities.items():
        if not isinstance(name, str) or not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            raise ValueError("R15.17 identity digests must be lowercase SHA-256")
    if evidence["manual_state"] != "conditional_not_triggered":
        raise ValueError("R15.17 core scenario cannot fabricate optional manual evidence")
    if evidence["optional_capability_state"] != "unavailable":
        raise ValueError("R15.17 optional fixture must remain truthful unavailable")
    if evidence["secrets_exposed"] is not False:
        raise ValueError("R15.17 evidence must not expose secrets")
    if evidence["status"] != "pass" or evidence["blockers"] != []:
        raise ValueError("accepted R15.17 evidence must be blocker-free pass")
    semantic_digest = evidence["semantic_digest"]
    if not isinstance(semantic_digest, str) or _SHA256.fullmatch(semantic_digest) is None:
        raise ValueError("semantic_digest must be lowercase SHA-256")
    if semantic_digest != canonical_sha256(_payload_without_digest(evidence)):
        raise ValueError("R15.17 semantic digest mismatch")


def run_integrated_scenario(source_sha: str, work_root: Path) -> dict[str, object]:
    if _COMMIT.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be an exact lowercase commit SHA")
    work_root.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {}

    untrusted = _experience_record("untrusted", "unvalidated fixture")
    checks[CHECK_NAMES[0]] = _expect(
        EligibilityDenied,
        lambda: transition_experience(
            untrusted,
            ExperienceState.ELIGIBLE,
            actor="integrated",
            reason="must fail closed",
        ),
    )

    secret = "ghp_R15_17_SYNTHETIC_SECRET_123456789"
    secret_result = sanitize_experience(
        _experience_record("secret-source", f"api_key={secret}"),
        f"api_key={secret}",
        policy=_allowed_governance(),
        consent=PolicyDecision.ALLOW,
        actor="integrated",
    )
    rendered_secret_report = json.dumps(secret_result.report.to_dict(), sort_keys=True)
    checks[CHECK_NAMES[1]] = (
        secret not in secret_result.sanitized_text
        and secret not in rendered_secret_report
        and secret_result.report.finding_count >= 1
    )

    license_result = sanitize_experience(
        _experience_record("license-source", "clean", license_expression="Unknown-9.9"),
        "clean",
        policy=_allowed_governance(),
        consent=PolicyDecision.ALLOW,
        actor="integrated",
    )
    checks[CHECK_NAMES[2]] = (
        license_result.record.state is ExperienceState.QUARANTINED
        and license_result.record.authorization.license in {PolicyDecision.REVIEW, PolicyDecision.DENY}
    )

    safe_result = sanitize_experience(
        _experience_record("safe-source", "safe python repair fixture"),
        "safe python repair fixture",
        policy=_allowed_governance(),
        consent=PolicyDecision.ALLOW,
        actor="integrated",
    )
    safe_record = transition_experience(
        safe_result.record,
        ExperienceState.CURATED,
        actor="integrated",
        reason="repository-owned fixture",
    ).record
    revocations = RevocationIndex()
    revocations.register("dataset:r15-17-revoked", [safe_record.experience_id.value])
    revocations.register("candidate:r15-17-revoked", ["dataset:r15-17-revoked"])
    _, revocation_report = revocations.revoke_source(
        "safe-source",
        [safe_record],
        actor="integrated",
        reason="fixture revocation",
    )
    checks[CHECK_NAMES[3]] = set(revocation_report.invalidated_artifact_ids) == {
        "dataset:r15-17-revoked",
        "candidate:r15-17-revoked",
    }

    dedup_policy = DedupPolicy(lowercase_comparison=False, near_threshold=0.60, shingle_size=2)
    sanitizer_digest = "1" * 64
    governance_digest = "2" * 64
    records_and_text = (
        (
            _experience_record(
                "duplicate-a",
                "alpha beta gamma delta epsilon",
                authorization=_allowed_authorization(),
                state=ExperienceState.CURATED,
                sanitizer_digest=sanitizer_digest,
                governance_digest=governance_digest,
            ),
            "alpha beta gamma delta epsilon",
        ),
        (
            _experience_record(
                "duplicate-b",
                "alpha beta gamma delta zeta",
                authorization=_allowed_authorization(),
                state=ExperienceState.CURATED,
                sanitizer_digest=sanitizer_digest,
                governance_digest=governance_digest,
            ),
            "alpha beta gamma delta zeta",
        ),
        (
            _experience_record(
                "safe-c",
                "ordinary theta iota kappa lambda",
                authorization=_allowed_authorization(),
                state=ExperienceState.CURATED,
                sanitizer_digest=sanitizer_digest,
                governance_digest=governance_digest,
            ),
            "ordinary theta iota kappa lambda",
        ),
    )
    sources = [DatasetSource(record, text, language="en") for record, text in records_and_text]
    items = [_dedup_item(source, dedup_policy) for source in sources]
    dedup = cluster_items(items, dedup_policy)
    duplicate_group = dedup.group_for(sources[0].item_id)
    checks[CHECK_NAMES[4]] = (
        duplicate_group == dedup.group_for(sources[1].item_id)
    )

    holdouts = ProtectedHoldoutRegistry(dedup_policy.digest)
    holdouts.register(
        ProtectedHoldout.from_text(
            "protected-r15-17",
            "alpha beta gamma delta epsilon",
            dedup_policy,
        )
    )
    contamination = scan_contamination(items, dedup, holdouts, dedup_policy)
    dataset_policy = DatasetPolicy(
        seed=1517,
        sanitizer_digest=sanitizer_digest,
        governance_policy_digest=governance_digest,
        dedup_policy_digest=dedup_policy.digest,
        duplicate_handling=DuplicateHandling.KEEP_GROUP,
    )
    build = DatasetBuilder(dataset_policy).build(
        sources,
        dedup=dedup,
        contamination=contamination,
    )
    split_by_group: dict[str, set[DatasetSplit]] = {}
    for entry in build.manifest.entries:
        split_by_group.setdefault(entry.group_id, set()).add(entry.split)
    checks[CHECK_NAMES[4]] = checks[CHECK_NAMES[4]] and all(
        len(splits) == 1 for splits in split_by_group.values()
    )
    included_ids = {entry.experience_id for entry in build.manifest.entries}
    checks[CHECK_NAMES[5]] = (
        sources[0].item_id not in included_ids
        and sources[1].item_id not in included_ids
        and sources[2].item_id in included_ids
    )
    dataset_digest = hashlib.sha256(build.manifest.canonical_json().encode("utf-8")).hexdigest()

    gap_report = _gap_report(dataset_digest)
    system_decision = GapDecisionEngine().evaluate(
        gap_report,
        base_model_ref="fixture/base",
        evidence=_decision_evidence(DiagnosticComponent.CONTEXT),
        dataset={
            "dataset_digest": dataset_digest,
            "dataset_id": "r15-17-dataset",
            "entries": [
                {"domain": "python", "example_id": f"example-{index}", "split": "train"}
                for index in range(4)
            ],
        },
    )
    checks[CHECK_NAMES[7]] = system_decision.disposition is DecisionDisposition.FIX_SYSTEM_FIRST

    training_plan = _training_plan(dataset_digest)
    training_root = work_root / "training"
    training_report = TrainingRunner(
        training_root,
        resource_probe=_FixedResources(),
    ).run(training_plan)
    if training_report.state is not TrainingRunState.COMPLETED:
        raise RuntimeError("R15.17 fixture training did not complete")
    checkpoint = (
        Path("tuning-runs")
        / training_plan.run_id
        / "checkpoints"
        / "checkpoint-00000002"
        / "checkpoint.json"
    )
    changed_training_plan = replace(
        training_plan,
        dataset=replace(training_plan.dataset, dataset_digest="9" * 64),
    )
    checks[CHECK_NAMES[8]] = _expect(
        TrainingError,
        lambda: TrainingRunner(
            training_root,
            resource_probe=_FixedResources(),
        ).run(changed_training_plan, resume_checkpoint=str(checkpoint)),
    )

    base_rows = _evaluation_rows(
        "base",
        critical=(True, True),
        target=(False, False),
        general=(False, False),
    )
    candidate_rows = _evaluation_rows(
        "candidate",
        critical=(True, False),
        target=(True, True),
        general=(True, True),
    )
    base_report = _evaluation_report("base", "a" * 64, base_rows)
    candidate_report = _evaluation_report("candidate", "b" * 64, candidate_rows)
    binding = CandidateBinding(
        candidate_id="candidate-r15-17",
        base_model_ref="base",
        base_model_digest="a" * 64,
        candidate_model_ref="candidate",
        candidate_model_digest="b" * 64,
        adapter_digest=training_report.adapter_digest or "c" * 64,
        training_plan_digest=training_plan.digest,
        dataset_digest=dataset_digest,
    )
    policy = CandidateEvaluationPolicy(
        target_domains=("target",),
        min_target_gain=0.05,
        require_protected_benchmark=True,
    )
    evaluation = BaseAdapterEvaluator().evaluate(
        base_report,
        candidate_report,
        binding=binding,
        policy=policy,
        training_loss=TrainingLossContext(0.2, 0.3),
    )
    checks[CHECK_NAMES[9]] = (
        evaluation.aggregate_delta > 0
        and evaluation.disposition is CandidateDisposition.REJECT
        and evaluation.critical_regressions == ("critical",)
    )

    mixed_candidate = _evaluation_report("candidate", "8" * 64, candidate_rows)
    checks[CHECK_NAMES[6]] = _expect(
        CandidateEvaluationError,
        lambda: BaseAdapterEvaluator().evaluate(
            base_report,
            mixed_candidate,
            binding=binding,
            policy=policy,
            training_loss=TrainingLossContext(0.2, 0.3),
        ),
    )

    adapter_dir = work_root / "wrong-base-adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    (adapter_dir / "adapter_config.json").write_text(
        json.dumps(
            {
                "base_model_name_or_path": "wrong/base",
                "revision": "abc123",
                "peft_type": "LORA",
                "task_type": "CAUSAL_LM",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (adapter_dir / "adapter_model.safetensors").write_bytes(b"r15-17-adapter")
    adapter_tree_digest = _tree_digest(adapter_dir)
    export_binding = ExportBinding(
        candidate_id="candidate-r15-17-export",
        base_model_ref="fixture/base",
        base_model_revision="abc123",
        base_model_digest="a" * 64,
        adapter_digest=adapter_tree_digest,
        dataset_digest=dataset_digest,
        training_plan_digest=training_plan.digest,
        evaluation_digest="4" * 64,
        base_license="apache-2.0",
        adapter_license="apache-2.0",
    )
    export_request = ExportRequest(
        binding=export_binding,
        intended_use="Repository-owned R15.17 integrated fixture.",
        limitations="Fixture-only acceptance.",
        eval_summary="Synthetic accepted export precondition for wrong-base rejection.",
    )
    export_evaluation = {
        "disposition": "promote_to_export",
        "can_export": True,
        "binding": {
            "candidate_id": export_binding.candidate_id,
            "base_model_ref": export_binding.base_model_ref,
            "base_model_digest": export_binding.base_model_digest,
            "adapter_digest": export_binding.adapter_digest,
            "dataset_digest": export_binding.dataset_digest,
            "training_plan_digest": export_binding.training_plan_digest,
        },
    }
    export_wrong_base = _expect(
        ModelExportError,
        lambda: export_candidate(
            adapter_dir=adapter_dir,
            output_root=work_root / "wrong-base-export",
            request=export_request,
            evaluation=export_evaluation,
        ),
    )
    ollama_wrong_base = _expect(
        OllamaPackagingError,
        lambda: OllamaBinding(
            candidate_id="candidate-r15-17-ollama",
            artifact_kind=ArtifactKind.SAFETENSORS_ADAPTER,
            artifact_sha256=adapter_tree_digest,
            base_model="fixture/base",
            base_digest="a" * 64,
            export_manifest_digest="1" * 64,
            evaluation_digest="2" * 64,
            gguf_report_digest="3" * 64,
            architecture="fixture",
            trained_base_model="other/base",
            trained_base_digest="a" * 64,
            direct_adapter_authorized=True,
        ),
    )
    checks[CHECK_NAMES[10]] = export_wrong_base and ollama_wrong_base

    quant_target = QuantizationTarget(
        "Q4_K_M",
        max_aggregate_loss=0.20,
        max_critical_loss=0.01,
    )
    quant_quality = assess_quantization_quality(
        (
            DomainScore(
                "security",
                baseline=0.95,
                candidate=0.90,
                critical=True,
            ),
        ),
        quant_target,
    )
    checks[CHECK_NAMES[11]] = (
        quant_quality.disposition is QualityDisposition.REJECT_CRITICAL
        and quant_quality.critical_regressions == ("security",)
    )

    project_root = work_root / "registry-project"
    project_root.mkdir(parents=True, exist_ok=True)
    registry_path = project_root / ".kodepoia" / "models" / "specialized.json"
    registry = SpecializedModelRegistry(
        registry_path,
        safe_change=SafeChangeManager(project_root, work_root / "registry-snapshots"),
    )
    rejected = _registry_version(
        "rejected",
        "1" * 64,
        state=ModelVersionState.REJECTED,
    )
    first_version = _registry_version("v1", "2" * 64)
    second_version = _registry_version("v2", "3" * 64)
    registry.register(rejected)
    registry.register(first_version)
    registry.register(second_version)
    rejected_promotion = _expect(
        ValueError,
        lambda: registry.promote(
            rejected.version_id,
            ModelRole.CORE,
            health_probe=lambda *_args: True,
        ),
    )
    registry.promote("v1", ModelRole.CORE, health_probe=lambda *_args: True)
    registry.promote("v2", ModelRole.CORE, health_probe=lambda *_args: True)
    restarted = SpecializedModelRegistry(registry.path)
    rolled_back = restarted.rollback(ModelRole.CORE, health_probe=lambda *_args: True)
    active = restarted.active_version(ModelRole.CORE)
    checks[CHECK_NAMES[12]] = (
        rejected_promotion
        and rolled_back == "v1"
        and active is not None
        and active.version_id == "v1"
    )

    optional_source = work_root / "optional-source"
    optional_source.mkdir(parents=True, exist_ok=True)
    (optional_source / "config.json").write_text(
        '{"model_type":"fixture"}',
        encoding="utf-8",
    )
    (optional_source / "model.safetensors").write_bytes(b"fixture")
    optional_binding = ConversionBinding(
        candidate_id="optional-r15-17",
        architecture="fixture",
        source_digest=digest_path(optional_source),
        export_manifest_digest="6" * 64,
        evaluation_digest="7" * 64,
        source_kind=SourceKind.HF_DIRECTORY,
        source_precision="F16",
    )
    optional_plan = ConversionPlan(
        binding=optional_binding,
        targets=(QuantizationTarget("Q4_K_M", max_aggregate_loss=0.05),),
        max_artifact_bytes=1024 * 1024,
    )
    optional_tools = GgufToolchain(
        converter=work_root / "missing-convert_hf_to_gguf.py",
        quantizer=work_root / "missing-llama-quantize",
        revision="unavailable-r15-17-fixture",
    )
    optional_unavailable = _expect(
        GgufConversionError,
        lambda: run_high_precision_conversion(
            toolchain=optional_tools,
            plan=optional_plan,
            source=optional_source,
            output=work_root / "optional.gguf",
            runner=lambda _argv: None,  # type: ignore[arg-type]
        ),
    )
    checks[CHECK_NAMES[13]] = optional_unavailable

    if tuple(checks) != CHECK_NAMES:
        raise RuntimeError("R15.17 scenario did not execute the exact adversarial inventory")

    identities = {
        "dataset": dataset_digest,
        "benchmark_suite": str(base_report["suite_digest"]),
        "benchmark_protection": str(base_report["protection_manifest_digest"]),
        "base_model": binding.base_model_digest,
        "training_plan": training_plan.digest,
        "adapter": training_report.adapter_digest or "0" * 64,
        "evaluation_binding": canonical_sha256(binding.to_dict()),
        "quantization_policy": canonical_sha256(
            {
                "quant_type": quant_target.quant_type,
                "max_aggregate_loss": quant_target.max_aggregate_loss,
                "max_critical_loss": quant_target.max_critical_loss,
            }
        ),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    evidence: dict[str, object] = {
        "schema": INTEGRATED_SCHEMA,
        "schema_version": 1,
        "source_sha": source_sha,
        "checks": checks,
        "check_count": len(CHECK_NAMES),
        "identities": identities,
        "manual_state": "conditional_not_triggered",
        "optional_capability_state": "unavailable",
        "secrets_exposed": False,
        "status": "pass" if not blockers else "fail",
        "blockers": blockers,
    }
    evidence["semantic_digest"] = canonical_sha256(evidence)
    if secret in json.dumps(evidence, sort_keys=True):
        raise RuntimeError("R15.17 evidence leaked the synthetic secret fixture")
    validate_integrated_evidence(evidence)
    return evidence
