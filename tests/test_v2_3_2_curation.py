from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

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
    TrainingAuthorization,
)
from kodepoia.kodestudio.model_lab_curation import ModelLabCurationService
from kodepoia.tuning.r15_ux import (
    R15UXPolicyError,
    R15UXService,
    R15WorkflowRequest,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _record(
    source_id: str,
    *,
    state: ExperienceState = ExperienceState.CURATED,
    license_expression: str | None = "MIT",
    benchmark_protected: bool = False,
) -> ExperienceRecord:
    origin = _digest(f"origin:{source_id}")
    text = f"sanitized:{source_id}"
    authorization = TrainingAuthorization(
        source_scope=PolicyDecision.ALLOW,
        consent=PolicyDecision.ALLOW,
        provenance=PolicyDecision.ALLOW,
        license=PolicyDecision.ALLOW,
        privacy=PolicyDecision.ALLOW,
    )
    sanitization = SanitizationEvidence(
        status=SanitizationStatus.PASSED,
        sanitizer_digest=_digest("sanitizer"),
    )
    return ExperienceRecord(
        experience_id=ExperienceId.derive(
            workspace_id="ws-demo",
            source_id=source_id,
            origin_digest=origin,
        ),
        workspace_id="ws-demo",
        project_id="project-demo",
        task_label="repair",
        domain_label="python",
        state=state,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="ws-demo",
            storage_key=f"experience/sanitized/project-demo/{source_id}.txt",
            sha256=_digest(text),
            byte_length=len(text.encode("utf-8")),
        ),
        provenance=ProvenanceDescriptor(
            source_type="fixture",
            source_id=source_id,
            origin_digest=origin,
            project_scope="project-demo",
            license_expression=license_expression,
        ),
        authorization=authorization,
        sanitization=sanitization,
        benchmark_protected=benchmark_protected,
    )


def _capture_manifest(record: ExperienceRecord) -> dict[str, object]:
    return {
        "schema": "kodepoia.experience.capture",
        "schema_version": 1,
        "event_id": f"event:{record.provenance.source_id}",
        "record_digest": record.contract_digest(),
        "record": record.to_dict(),
    }


def _dataset_manifest(record: ExperienceRecord) -> dict[str, object]:
    entry = {
        "domain": record.domain_label,
        "example_id": "ex_" + _digest("example"),
        "experience_id": record.experience_id.value,
        "format": "text",
        "group_id": "grp_" + _digest("group"),
        "language": "en",
        "license_expression": "MIT",
        "origin_digest": record.provenance.origin_digest,
        "project_scope": record.project_id,
        "representation_digest": _digest("representation"),
        "row_digest": _digest("row"),
        "source_contract_digest": record.contract_digest(),
        "source_digest": record.content.sha256,
        "source_id": record.provenance.source_id,
        "source_type": record.provenance.source_type,
        "split": "train",
        "task": record.task_label,
        "transformations": [],
    }
    core = {
        "dedup_policy_digest": _digest("dedup"),
        "entries": [entry],
        "export_digests": {
            "test": _digest(""),
            "train": _digest("train-export"),
            "validation": _digest("validation-export"),
        },
        "policy": {
            "seed": 42,
            "version": "r15.5-dataset-v1",
        },
        "policy_digest": _digest("dataset-policy"),
        "representation_version": "r15.5-representation-v1",
        "selection_summary": {
            "excluded_by_reason": {
                "benchmark_contamination": 1,
                "state:revoked": 1,
            },
            "input_records": 3,
            "selected_groups": 1,
            "selected_records": 1,
        },
        "split_stats": {
            "test": {"rows": 0, "groups": 0, "bytes": 0},
            "train": {"rows": 1, "groups": 1, "bytes": 100},
            "validation": {"rows": 0, "groups": 0, "bytes": 0},
        },
    }
    digest = hashlib.sha256(_canonical(core).encode("utf-8")).hexdigest()
    return {
        "schema": "kodepoia.experience.dataset-manifest",
        "schema_version": 1,
        "dataset_id": f"ds_{digest}",
        "dataset_digest": digest,
        **core,
    }


def test_curation_snapshot_is_structured_metadata_only_and_project_knowledge_is_not_ingested(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    curated = _record("safe-source")
    contaminated = _record("contaminated-source")

    _write_json(
        root / ".kodepoia" / "experience" / "safe.json",
        _capture_manifest(curated),
    )
    _write_json(
        root / ".kodepoia" / "experience" / "contaminated.json",
        _capture_manifest(contaminated),
    )
    _write_json(
        root / ".kodepoia" / "experience" / "contamination-report.json",
        {
            "policy_digest": _digest("dedup"),
            "findings": [{"item_id": contaminated.experience_id.value}],
            "quarantined_item_ids": [contaminated.experience_id.value],
            "contaminated_group_ids": ["grp_" + _digest("contaminated")],
        },
    )
    _write_json(
        root / ".kodepoia" / "datasets" / "fixture" / "manifest.json",
        _dataset_manifest(curated),
    )
    knowledge_marker = "PROJECT-KNOWLEDGE-MUST-NOT-BECOME-TRAINING-DATA"
    _write_json(
        root / ".kodepoia" / "knowledge" / "catalog-v1.json",
        {"content": knowledge_marker},
    )

    snapshot = ModelLabCurationService(root).snapshot()
    encoded = json.dumps(snapshot, sort_keys=True)

    assert snapshot["schema"] == "kodepoia.v2.3.2.model-lab-curation"
    assert snapshot["raw_payloads_exposed"] is False
    assert snapshot["project_knowledge_auto_ingest"] is False
    assert knowledge_marker not in encoded
    assert len(snapshot["experiences"]) == 2
    by_id = {item["experience_id"]: item for item in snapshot["experiences"]}
    assert by_id[curated.experience_id.value]["integrity"] == "ready"
    assert by_id[curated.experience_id.value]["dataset_eligible"] is True
    assert by_id[curated.experience_id.value]["content"]["payload_read"] is False
    assert by_id[contaminated.experience_id.value]["dataset_eligible"] is False
    assert "benchmark_contamination" in by_id[contaminated.experience_id.value][
        "dataset_blockers"
    ]
    assert snapshot["datasets"][0]["integrity"] == "ready"
    assert snapshot["datasets"][0]["payload_rows_read"] is False
    assert snapshot["datasets"][0]["excluded_by_reason"] == {
        "benchmark_contamination": 1,
        "state:revoked": 1,
    }


def test_curation_snapshot_keeps_revoked_unknown_license_and_tamper_fail_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"

    revoked = _record("revoked-source", state=ExperienceState.REVOKED)
    missing_license = _record("missing-license", license_expression=None)

    revoked_manifest = _capture_manifest(revoked)
    _write_json(
        root / ".kodepoia" / "experience" / "revoked.json",
        revoked_manifest,
    )
    missing_manifest = _capture_manifest(missing_license)
    missing_manifest["record"]["task_label"] = "tampered-task"
    _write_json(
        root / ".kodepoia" / "experience" / "missing-license.json",
        missing_manifest,
    )

    snapshot = ModelLabCurationService(root).snapshot()
    by_id = {item["experience_id"]: item for item in snapshot["experiences"]}

    assert by_id[revoked.experience_id.value]["dataset_eligible"] is False
    assert "state:revoked" in by_id[revoked.experience_id.value]["dataset_blockers"]
    assert by_id[missing_license.experience_id.value]["integrity"] == "tampered"
    assert by_id[missing_license.experience_id.value]["dataset_eligible"] is False
    assert "license:missing" in by_id[missing_license.experience_id.value][
        "dataset_blockers"
    ]


def test_curation_and_dataset_mutations_delegate_only_to_r15_typed_handlers(
    tmp_path: Path,
) -> None:
    calls: list[R15WorkflowRequest] = []

    def curate_handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {
            "status": "ok",
            "experience_id": request.identifier,
            "transition": "sanitized->curated",
        }

    def dataset_handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {
            "status": "ok",
            "dataset_id": "ds_" + _digest("built"),
            "selection_summary": {
                "selected_records": 3,
                "excluded_by_reason": {"benchmark_contamination": 1},
            },
        }

    r15 = R15UXService(
        tmp_path,
        handlers={
            "experience.curate": curate_handler,
            "dataset.build": dataset_handler,
        },
    )
    service = ModelLabCurationService(tmp_path, r15_service=r15)

    preview = service.preview_curation("exp_" + "1" * 64)
    assert preview["status"] == "dry_run"
    assert calls == []

    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.apply_curation("exp_" + "1" * 64, confirmed=False)
    assert calls == []

    applied = service.apply_curation("exp_" + "1" * 64, confirmed=True)
    assert applied["status"] == "ok"
    assert calls[-1].key == "experience.curate"

    dataset_preview = service.preview_dataset_build()
    assert dataset_preview["status"] == "dry_run"
    assert dataset_preview["preview"]["raw_payloads_read"] is False
    assert "licenses" in dataset_preview["preview"]
    assert "domains" in dataset_preview["preview"]
    assert "tasks" in dataset_preview["preview"]
    assert "split_summary" in dataset_preview["preview"]
    assert len(calls) == 1

    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.apply_dataset_build(confirmed=False)
    assert len(calls) == 1

    built = service.apply_dataset_build(confirmed=True)
    assert built["status"] == "ok"
    assert calls[-1].key == "dataset.build"
    assert len(calls) == 2


def test_unconfigured_mutation_backend_is_explicit_and_does_not_write(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

    service = ModelLabCurationService(root)
    snapshot = service.snapshot()
    assert snapshot["actions"]["experience_curate"]["available"] is False
    assert snapshot["actions"]["dataset_build"]["available"] is False

    preview = service.preview_dataset_build()
    assert preview["status"] == "dry_run"
    with pytest.raises(R15UXPolicyError, match="backend is not configured"):
        service.apply_dataset_build(confirmed=True)

    after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
    assert before == after





def test_curation_rejects_cross_project_r15_service_binding(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    with pytest.raises(ValueError, match="project root"):
        ModelLabCurationService(
            left,
            r15_service=R15UXService(right),
        )


def test_dataset_manifest_tamper_is_explicit_without_reading_jsonl(tmp_path: Path) -> None:
    root = tmp_path / "project"
    record = _record("dataset-source")
    manifest = _dataset_manifest(record)
    _write_json(
        root / ".kodepoia" / "datasets" / "fixture" / "manifest.json",
        manifest,
    )
    raw_marker = "RAW-TRAINING-MARKER-MUST-NOT-BE-READ"
    data_file = root / ".kodepoia" / "datasets" / "fixture" / "train.jsonl"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(raw_marker, encoding="utf-8")

    manifest["selection_summary"]["selected_records"] = 99
    _write_json(
        root / ".kodepoia" / "datasets" / "fixture" / "manifest.json",
        manifest,
    )

    snapshot = ModelLabCurationService(root).snapshot()
    encoded = json.dumps(snapshot, sort_keys=True)
    assert snapshot["datasets"][0]["integrity"] == "tampered"
    assert raw_marker not in encoded
    assert snapshot["datasets"][0]["payload_rows_read"] is False
