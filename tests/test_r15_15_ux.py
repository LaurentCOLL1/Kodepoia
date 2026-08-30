from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.tuning.r15_ux import (
    R15UXPolicyError,
    R15UXService,
    R15WorkflowMode,
    R15WorkflowRequest,
)


def test_catalog_covers_frozen_r15_workflow_families(tmp_path: Path) -> None:
    service = R15UXService(tmp_path)
    catalog = service.catalog()
    assert set(catalog["domains"]) == {
        "experience",
        "dataset",
        "bench",
        "gap",
        "training",
        "conversion",
        "ollama",
        "registry",
    }
    keys = {spec.key for spec in service.actions()}
    required = {
        "experience.status",
        "experience.curate",
        "dataset.build",
        "dataset.inspect",
        "bench.run",
        "bench.compare",
        "gap.diagnose",
        "training.doctor",
        "training.plan",
        "training.run",
        "training.status",
        "training.cancel",
        "conversion.doctor",
        "ollama.status",
        "registry.candidates",
        "registry.promote",
        "registry.rollback",
    }
    assert required <= keys
    assert catalog["raw_shell_exposed"] is False
    assert catalog["raw_secret_editor_exposed"] is False
    assert catalog["public_model_upload_exposed"] is False


def test_mutating_action_defaults_to_safe_dry_run_and_does_not_call_handler(tmp_path: Path) -> None:
    calls: list[R15WorkflowRequest] = []

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "ok"}

    service = R15UXService(tmp_path, handlers={"training.run": handler})
    payload = service.execute(
        R15WorkflowRequest(
            domain="training",
            action="run",
            mode=R15WorkflowMode.DRY_RUN,
            identifier="run.plan.1",
        )
    )
    assert payload["status"] == "dry_run"
    assert payload["would_mutate"] is True
    assert calls == []


def test_mutation_requires_confirmation_and_configured_backend(tmp_path: Path) -> None:
    service = R15UXService(tmp_path)
    request = R15WorkflowRequest(
        domain="registry",
        action="promote",
        mode=R15WorkflowMode.APPLY,
        identifier="candidate.1",
    )
    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.execute(request)
    with pytest.raises(R15UXPolicyError, match="backend is not configured"):
        service.execute(
            R15WorkflowRequest(
                domain="registry",
                action="promote",
                mode=R15WorkflowMode.APPLY,
                identifier="candidate.1",
                confirmed=True,
            )
        )


def test_configured_handler_result_is_redacted_and_external_path_hidden(tmp_path: Path) -> None:
    outside = tmp_path.parent / "private.txt"

    def handler(_request: R15WorkflowRequest) -> dict[str, object]:
        return {
            "status": "ok",
            "token": "never-visible",
            "nested": {"api_key": "also-never-visible"},
            "path": str(outside),
            "candidate_id": "candidate.1",
        }

    service = R15UXService(tmp_path, handlers={"registry.promote": handler})
    payload = service.execute(
        R15WorkflowRequest(
            domain="registry",
            action="promote",
            mode=R15WorkflowMode.APPLY,
            identifier="candidate.1",
            confirmed=True,
        )
    )
    rendered = json.dumps(payload, sort_keys=True)
    assert "never-visible" not in rendered
    assert payload["token"] == "<redacted>"
    assert payload["nested"]["api_key"] == "<redacted>"
    assert payload["path"] == "<external-path>"


def test_status_and_evidence_export_are_digest_bound_and_project_scoped(tmp_path: Path) -> None:
    registry = tmp_path / ".kodepoia" / "model-registry.json"
    registry.parent.mkdir(parents=True)
    registry.write_text('{"schema_version":1}\n', encoding="utf-8")
    service = R15UXService(tmp_path)
    status = service.status()
    item = next(entry for entry in status["evidence"] if entry["kind"] == "file")
    assert item["path"] == ".kodepoia/model-registry.json"
    assert len(item["sha256"]) == 64

    exported = service.export_evidence(Path(".kodepoia/tuning/evidence.json"))
    assert exported["status"] == "ok"
    assert len(exported["sha256"]) == 64
    contents = (tmp_path / exported["output"]).read_text(encoding="utf-8")
    assert str(tmp_path) not in contents

    with pytest.raises(R15UXPolicyError, match="inside the project root"):
        service.export_evidence(Path("../outside.json"))
