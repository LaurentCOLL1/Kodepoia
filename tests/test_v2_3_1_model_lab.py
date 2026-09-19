from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kodepoia.kodestudio.model_lab import ModelLabInventoryService
from kodepoia.kodestudio.preferences import ApplicationPreferences
from kodepoia.models.router import ModelRole
from kodepoia.tuning.model_registry import (
    ModelArtifactKind,
    ModelArtifactVariant,
    ModelVersionState,
    SpecializedModelVersion,
)


def _digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate() -> SpecializedModelVersion:
    return SpecializedModelVersion(
        version_id="candidate-v1",
        candidate_id="candidate-v1",
        state=ModelVersionState.CANDIDATE,
        disposition="PROMOTE_TO_EXPORT",
        base_model_id="base-model-v1",
        base_digest=_digest("base"),
        lineage=(
            ("dataset", _digest("dataset")),
            ("evaluation", _digest("evaluation")),
            ("training", _digest("training")),
        ),
        role_eligibility=(ModelRole.CODER,),
        domain_tags=("code",),
        variants=(
            ModelArtifactVariant(
                kind=ModelArtifactKind.GGUF,
                artifact_id="candidate-v1-gguf",
                digest=_digest("gguf"),
                runtime_ref="kodepoia/candidate-v1:Q4_K_M",
                capabilities=("structured", "tools"),
            ),
        ),
        preferred_variant=ModelArtifactKind.GGUF,
    )


def _project_fixture(tmp_path: Path) -> tuple[Path, ApplicationPreferences]:
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)

    _write_json(
        root / ".kodepoia" / "datasets" / "fixture-dataset.json",
        {
            "schema": "kodepoia.r15.dataset.manifest",
            "dataset_id": "fixture-dataset-v1",
            "manifest_digest": _digest("dataset-manifest"),
            "state": "ready",
        },
    )
    _write_json(
        root / ".kodepoia" / "benchmarks" / "base-report.json",
        {
            "schema": "kodepoia.kodebench.v2.report",
            "report_digest": _digest("bench-report"),
            "status": "completed",
            "dataset_digest": _digest("dataset"),
        },
    )
    _write_json(
        root / ".kodepoia" / "tuning" / "training-plan.json",
        {
            "schema": "kodepoia.r15.training-plan",
            "plan_digest": _digest("training"),
            "dataset_digest": _digest("dataset"),
            "base_model_digest": _digest("base"),
            "status": "ready",
        },
    )
    _write_json(
        root / ".kodepoia" / "tuning" / "evaluation.json",
        {
            "schema": "kodepoia.r15.candidate-evaluation",
            "evaluation_digest": _digest("evaluation"),
            "training_plan_digest": _digest("training"),
            "dataset_digest": _digest("dataset"),
            "status": "completed",
        },
    )
    _write_json(
        root / ".kodepoia" / "tuning" / "exports" / "manifest.json",
        {
            "schema": "kodepoia.r15.model-export",
            "artifact_id": "candidate-v1",
            "export_digest": _digest("export"),
            "evaluation_digest": _digest("evaluation"),
            "status": "ready",
        },
    )

    candidate = _candidate()
    _write_json(
        root / ".kodepoia" / "models" / "specialized.json",
        {
            "schema_version": 1,
            "records": {candidate.version_id: candidate.persisted()},
            "active_roles": {},
            "rollback_roles": {},
        },
    )

    preferences = ApplicationPreferences(tmp_path / "settings.json")
    preferences.update(
        {
            "model_roles": {
                "code": "kodepoia/candidate-v1:Q4_K_M",
                "core": "qwen3.5:9b",
            },
            "ollama_base_url": "http://127.0.0.1:11434",
        }
    )
    return root, preferences


def test_model_lab_inventory_discovers_r15_evidence_and_registry_without_mutation(
    tmp_path: Path,
) -> None:
    root, preferences = _project_fixture(tmp_path)
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

    service = ModelLabInventoryService(root, preferences=preferences)
    snapshot = service.snapshot()

    assert snapshot["schema"] == "kodepoia.v2.3.1.model-lab"
    assert snapshot["read_only"] is True
    assert snapshot["mutations"] == {
        "dataset_build": False,
        "training": False,
        "conversion": False,
        "promotion": False,
        "rollback": False,
    }
    categories = {item["category"] for item in snapshot["evidence"]}
    assert {"dataset", "benchmark", "tuning"} <= categories
    assert snapshot["registry"]["state"] == "ready"
    assert snapshot["registry"]["records"][0]["version_id"] == "candidate-v1"
    assert snapshot["ollama"]["roles"] == {
        "code": "kodepoia/candidate-v1:Q4_K_M",
        "core": "qwen3.5:9b",
    }
    lineage = snapshot["lineage"]
    assert any(edge["target"] == "candidate-v1" and edge["source"] == "dataset" for edge in lineage)
    assert any(edge["source"].endswith("training_plan_digest") for edge in lineage)

    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert before == after


def test_model_lab_reports_missing_invalid_stale_and_tampered_states(tmp_path: Path) -> None:
    root, preferences = _project_fixture(tmp_path)
    stale = root / ".kodepoia" / "tuning" / "stale.json"
    _write_json(stale, {"schema": "fixture.stale", "status": "stale"})
    invalid = root / ".kodepoia" / "benchmarks" / "broken.json"
    invalid.write_text("{not-json", encoding="utf-8")

    registry_path = root / ".kodepoia" / "models" / "specialized.json"
    document = json.loads(registry_path.read_text(encoding="utf-8"))
    document["records"]["candidate-v1"]["record_digest"] = "0" * 64
    _write_json(registry_path, document)
    registry_before = registry_path.read_bytes()

    snapshot = ModelLabInventoryService(root, preferences=preferences).snapshot()
    by_path = {item["path"]: item for item in snapshot["evidence"]}
    assert by_path[".kodepoia/tuning/stale.json"]["state"] == "stale"
    assert by_path[".kodepoia/benchmarks/broken.json"]["state"] == "invalid"
    assert snapshot["registry"]["state"] == "tampered"
    assert "digest mismatch" in snapshot["registry"]["detail"]
    assert registry_path.read_bytes() == registry_before

    fresh = tmp_path / "fresh"
    fresh.mkdir()
    fresh_preferences = ApplicationPreferences(tmp_path / "fresh-settings.json")
    fresh_snapshot = ModelLabInventoryService(
        fresh,
        preferences=fresh_preferences,
    ).snapshot()
    assert all(store["state"] == "missing" for store in fresh_snapshot["stores"])
    assert fresh_snapshot["registry"]["state"] == "missing"
    assert not (fresh / ".kodepoia").exists()


def test_runtime_probes_are_explicit_read_only_and_degraded_states_are_structured(
    tmp_path: Path,
) -> None:
    root, preferences = _project_fixture(tmp_path)
    calls = {"ollama": 0, "doctor": 0, "quota": 0}

    def ollama() -> dict[str, object]:
        calls["ollama"] += 1
        return {
            "base_url": "http://127.0.0.1:11434",
            "version": "0.fixture",
            "models": ["qwen3.5:9b", "kodepoia/candidate-v1:Q4_K_M"],
        }

    def doctor() -> dict[str, object]:
        calls["doctor"] += 1
        return {
            "installed": True,
            "authenticated": True,
            "version": "Kaggle API 2.fixture",
            "detail": "fixture ready",
            "ready": True,
        }

    def quota() -> dict[str, object]:
        calls["quota"] += 1
        return {
            "version": "Kaggle API 2.fixture",
            "entries": [
                {
                    "resource": "GPU",
                    "used_hours": 1.0,
                    "remaining_hours": 29.0,
                    "total_hours": 30.0,
                    "refresh_at": None,
                }
            ],
        }

    service = ModelLabInventoryService(
        root,
        preferences=preferences,
        ollama_snapshot_provider=ollama,
        kaggle_doctor_provider=doctor,
        kaggle_quota_provider=quota,
    )
    inventory = service.snapshot()
    assert calls == {"ollama": 0, "doctor": 0, "quota": 0}
    assert inventory["ollama"]["state"] == "not_checked"
    assert inventory["kaggle"]["state"] == "not_checked"

    runtime = service.runtime_snapshot()
    assert calls == {"ollama": 1, "doctor": 1, "quota": 1}
    assert runtime["read_only"] is True
    assert runtime["ollama"]["state"] == "ready"
    assert runtime["ollama"]["models"] == [
        "kodepoia/candidate-v1:Q4_K_M",
        "qwen3.5:9b",
    ]
    assert runtime["kaggle"]["state"] == "ready"

    unavailable = ModelLabInventoryService(
        root,
        preferences=preferences,
        ollama_snapshot_provider=lambda: (_ for _ in ()).throw(RuntimeError("Ollama offline")),
        kaggle_doctor_provider=lambda: {
            "ready": False,
            "detail": "authentication unavailable",
        },
        kaggle_quota_provider=lambda: (_ for _ in ()).throw(RuntimeError("quota unavailable")),
    ).runtime_snapshot()
    assert unavailable["ollama"]["state"] == "unavailable"
    assert "Ollama offline" in unavailable["ollama"]["detail"]
    assert unavailable["kaggle"]["state"] == "unavailable"
    assert "quota unavailable" in unavailable["kaggle"]["detail"]
