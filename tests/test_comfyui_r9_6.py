from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets import AssetId, AssetKind, AssetRevisionId
from kodepoia.assets.service import AssetService
from kodepoia.comfyui import (
    ComfyCaptureState,
    ComfyEndpoint,
    ComfyGovernanceError,
    ComfyOutputCaptureService,
    ComfyOutputCaptureStore,
    ComfyOutputReference,
    ComfyOutputSpec,
    ComfyProtocolError,
    ComfyRunManifest,
    ComfyRunState,
    ComfyRunStore,
    ComfySubmissionOutcome,
    canonical_json_bytes,
    canonical_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
PNG_FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_6_output.png"
CAPTURE_SCHEMA = ROOT / "schemas" / "comfy-output-capture-payload-v1.schema.json"


class _OutputClient:
    def __init__(self, payloads: dict[tuple[str, int], bytes | Exception]) -> None:
        self.endpoint = ComfyEndpoint.parse("http://127.0.0.1:8188")
        self.payloads = dict(payloads)
        self.calls: list[ComfyOutputReference] = []

    def retrieve_output(self, reference: ComfyOutputReference) -> bytes:
        self.calls.append(reference)
        value = self.payloads[(reference.node_id, reference.output_index)]
        if isinstance(value, Exception):
            raise value
        return value


def _sealed_run(
    *,
    state: ComfyRunState = ComfyRunState.SUCCEEDED,
    references: tuple[ComfyOutputReference, ...] | None = None,
) -> ComfyRunManifest:
    prompt_id = "kp_" + "b" * 32
    refs = references or (
        ComfyOutputReference(prompt_id, "2", 0, "fixture.png", "generated", "output"),
    )
    model_evidence: dict[str, Any] = {}
    model_digest = canonical_sha256(model_evidence)
    draft = ComfyRunManifest(
        run_id="run_" + "a" * 32,
        revision=0,
        previous_manifest_digest_sha256=None,
        prompt_id=prompt_id,
        client_id="kc_" + "c" * 32,
        state=state,
        submission_outcome=ComfySubmissionOutcome.ACCEPTED,
        definition_id="wf_" + "d" * 32,
        definition_digest_sha256=canonical_sha256({"definition": 1}),
        capability_identity_sha256=canonical_sha256({"capability": 1}),
        capability_endpoint="http://127.0.0.1:8188",
        comfyui_version="0.3.fixture",
        python_version="3.12.fixture",
        model_resolution_digest_sha256=model_digest,
        model_resolution_evidence_json=canonical_json_bytes(model_evidence).decode("utf-8"),
        instance_digest_sha256=canonical_sha256({"instance": 1}),
        prompt_digest_sha256=canonical_sha256({"2": {"class_type": "SaveImage", "inputs": {}}}),
        parameter_values=(("steps", 20), ("seed", 42)),
        input_bindings=(),
        seed_values=(("seed", 42),),
        required_output_node_ids=("2",),
        submission_attempts=1,
        submission_response_digest_sha256=canonical_sha256({"accepted": True}),
        progress_fraction=1.0 if state is ComfyRunState.SUCCEEDED else None,
        queue_digest_sha256=canonical_sha256({"queue": []}),
        history_digest_sha256=canonical_sha256({"history": state.value}),
        output_references=refs,
        manifest_digest_sha256="",
    )
    return replace(draft, manifest_digest_sha256=canonical_sha256(draft.canonical_without_digest()))


def _services(tmp_path: Path, run: ComfyRunManifest, payloads: dict[tuple[str, int], bytes | Exception]):
    project = tmp_path / "project"
    project.mkdir()
    run_store = ComfyRunStore(tmp_path / "runs")
    run_store.save(run)
    assets = AssetService(project)
    client = _OutputClient(payloads)
    service = ComfyOutputCaptureService(client, run_store, assets)
    return project, run_store, assets, client, service


def test_successful_capture_promotes_derived_revision_with_reconstructable_lineage(tmp_path: Path) -> None:
    png = PNG_FIXTURE.read_bytes()
    digest = hashlib.sha256(png).hexdigest()
    run = _sealed_run()
    project, _run_store, assets, client, service = _services(tmp_path, run, {("2", 0): png})
    try:
        (project / "input.txt").write_text("source", encoding="utf-8")
        source = assets.ingest("input.txt", kind=AssetKind.DOCUMENT, display_name="source")
        source_revision = AssetRevisionId(source.summary.revision_id or "")
        result = service.capture(
            run.run_id,
            (
                ComfyOutputSpec(
                    "2",
                    0,
                    AssetKind.IMAGE,
                    "Generated fixture",
                    expected_sha256=digest,
                    expected_length=len(png),
                ),
            ),
            source_revision_ids=(source_revision,),
        )
        assert result.state is ComfyCaptureState.COMPLETE
        assert len(result.outputs) == 1
        output = result.outputs[0]
        detail = assets.show(output.revision_id)
        assert detail.summary.role == "derived"
        assert detail.content_sha256 == digest
        assert detail.content_length == len(png)
        assert detail.summary.license_state == "unknown"
        lineage = assets.lineage(output.revision_id)
        input_ids = {item["input_revision_id"] for item in lineage["inputs"]}
        assert str(source_revision) in input_ids
        assert result.evidence_revision_id in input_ids
        assert all(item["transform_id"] == "comfyui.generated-output.capture.v1" for item in lineage["inputs"])
        assert len(client.calls) == 1
        assert not (project / ".kodepoia" / "comfyui" / "output-staging" / run.run_id).exists()
        assert (project / ".kodepoia" / "comfyui" / "generation-evidence" / f"{run.run_id}.json").is_file()
        schema = json.loads(CAPTURE_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(result.payload())
        loaded = service.capture_store.load(run.run_id)
        assert loaded.capture_digest_sha256 == result.capture_digest_sha256
    finally:
        assets.close()


def test_cross_prompt_reference_is_rejected_by_r9_6_guard() -> None:
    run = _sealed_run()
    foreign = ComfyOutputReference("kp_" + "e" * 32, "2", 0, "fixture.png", "", "output")
    with pytest.raises(ComfyProtocolError, match="different prompt"):
        ComfyOutputCaptureService._verify_reference(run, foreign)


@pytest.mark.parametrize(
    "filename,subfolder",
    [
        ("../escape.png", ""),
        ("C:escape.png", ""),
        ("fixture.png", "../escape"),
        ("fixture.png", "C:escape"),
        ("nested/fixture.png", ""),
    ],
)
def test_output_reference_path_escape_is_rejected_before_retrieval(
    tmp_path: Path, filename: str, subfolder: str
) -> None:
    png = PNG_FIXTURE.read_bytes()
    run = _sealed_run(
        references=(ComfyOutputReference("kp_" + "b" * 32, "2", 0, filename, subfolder, "output"),)
    )
    _project, _run_store, assets, client, service = _services(tmp_path, run, {("2", 0): png})
    try:
        with pytest.raises(ComfyProtocolError, match="boundary|relative|basename|subfolder"):
            service.capture(run.run_id, (ComfyOutputSpec("2", 0, AssetKind.IMAGE, "bad"),))
        assert client.calls == []
        assert assets.store.list_revisions() == []
    finally:
        assets.close()


@pytest.mark.parametrize("field", ["sha", "length"])
def test_hash_or_length_mismatch_fails_before_any_vault_promotion(tmp_path: Path, field: str) -> None:
    png = PNG_FIXTURE.read_bytes()
    run = _sealed_run()
    _project, _run_store, assets, _client, service = _services(tmp_path, run, {("2", 0): png})
    try:
        spec = ComfyOutputSpec(
            "2",
            0,
            AssetKind.IMAGE,
            "bad",
            expected_sha256=("0" * 64 if field == "sha" else None),
            expected_length=(len(png) + 1 if field == "length" else None),
        )
        with pytest.raises(ComfyProtocolError, match="SHA-256|byte length"):
            service.capture(run.run_id, (spec,))
        assert assets.store.list_revisions() == []
    finally:
        assets.close()


@pytest.mark.parametrize("state", [ComfyRunState.FAILED, ComfyRunState.CANCELLED, ComfyRunState.RUNNING])
def test_non_successful_run_never_promotes_output(tmp_path: Path, state: ComfyRunState) -> None:
    png = PNG_FIXTURE.read_bytes()
    run = _sealed_run(state=state)
    _project, _run_store, assets, client, service = _services(tmp_path, run, {("2", 0): png})
    try:
        with pytest.raises(ComfyGovernanceError, match="SUCCEEDED"):
            service.capture(run.run_id, (ComfyOutputSpec("2", 0, AssetKind.IMAGE, "blocked"),))
        assert client.calls == []
        assert assets.store.list_revisions() == []
    finally:
        assets.close()


def test_multi_output_retrieval_failure_happens_before_any_promotion(tmp_path: Path) -> None:
    png = PNG_FIXTURE.read_bytes()
    prompt_id = "kp_" + "b" * 32
    refs = (
        ComfyOutputReference(prompt_id, "2", 0, "one.png", "", "output"),
        ComfyOutputReference(prompt_id, "2", 1, "two.png", "", "output"),
    )
    run = _sealed_run(references=refs)
    _project, _run_store, assets, _client, service = _services(
        tmp_path,
        run,
        {("2", 0): png, ("2", 1): ComfyProtocolError("fixture retrieval failure")},
    )
    try:
        with pytest.raises(ComfyProtocolError, match="fixture retrieval failure"):
            service.capture(
                run.run_id,
                (
                    ComfyOutputSpec("2", 0, AssetKind.IMAGE, "one"),
                    ComfyOutputSpec("2", 1, AssetKind.IMAGE, "two"),
                ),
            )
        assert assets.store.list_revisions() == []
    finally:
        assets.close()


def test_invalid_image_signature_is_rejected_before_promotion(tmp_path: Path) -> None:
    run = _sealed_run()
    _project, _run_store, assets, _client, service = _services(tmp_path, run, {("2", 0): b"not-a-png"})
    try:
        with pytest.raises(ComfyProtocolError, match="image signature"):
            service.capture(run.run_id, (ComfyOutputSpec("2", 0, AssetKind.IMAGE, "bad image"),))
        assert assets.store.list_revisions() == []
    finally:
        assets.close()


def test_capture_store_rejects_tampering(tmp_path: Path) -> None:
    png = PNG_FIXTURE.read_bytes()
    run = _sealed_run()
    _project, run_store, assets, _client, service = _services(tmp_path, run, {("2", 0): png})
    try:
        result = service.capture(run.run_id, (ComfyOutputSpec("2", 0, AssetKind.IMAGE, "fixture"),))
        capture_path = run_store.root / ".captures" / f"{run.run_id}.json"
        doc = json.loads(capture_path.read_text(encoding="utf-8"))
        doc["payload"]["outputs"][0]["content_length"] += 1
        capture_path.write_text(json.dumps(doc), encoding="utf-8")
        with pytest.raises(ComfyProtocolError, match="digest"):
            ComfyOutputCaptureStore(run_store.root / ".captures").load(result.run_id)
    finally:
        assets.close()
