from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from kodepoia.comfyui import (
    ComfyEndpoint,
    ComfyExecutionBudget,
    ComfyExecutionHistory,
    ComfyFreeMemoryEvidence,
    ComfyGovernanceError,
    ComfyLifecycleAction,
    ComfyLifecycleAuditStore,
    ComfyLifecycleOutcome,
    ComfyLifecycleService,
    ComfyProtocolError,
    ComfyQueueSnapshot,
    ComfyRunManifest,
    ComfyRunState,
    ComfyRunStore,
    ComfySubmissionOutcome,
    ComfySystemSnapshot,
    ComfyTransportLimits,
    canonical_json_bytes,
    canonical_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCHEMA = ROOT / "schemas" / "comfy-lifecycle-audit-payload-v1.schema.json"
PROMPT = {"1": {"class_type": "KSampler", "inputs": {"steps": 1}}}


@dataclass(frozen=True)
class _Instance:
    instance_digest_sha256: str
    parameter_values: tuple[tuple[str, Any], ...] = ()
    input_bindings: tuple[tuple[str, Any], ...] = ()

    def prompt(self) -> dict[str, Any]:
        return PROMPT


class _LifecycleHTTP:
    def __init__(self, owner: "_LifecycleClient", *, modern: bool = True) -> None:
        self.owner = owner
        self.modern = modern
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def post_json(self, path: str, document: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((path, dict(document)))
        if not self.modern:
            raise ComfyProtocolError("ComfyUI HTTP POST failed with status 404")
        assert path.endswith(f"/{self.owner.prompt_id}/cancel")
        dispatched = self.owner.pending or self.owner.running
        if dispatched:
            self.owner.pending = False
            self.owner.running = False
            self.owner.history_state = ComfyRunState.CANCELLED
        return {"cancelled": dispatched}

    def _post_target(self, path: str, *, body: bytes, max_bytes: int):
        assert max_bytes > 0
        document = json.loads(body.decode("utf-8"))
        self.calls.append((path, document))
        if path == "/queue":
            assert document == {"delete": [self.owner.prompt_id]}
            self.owner.pending = False
            self.owner.history_state = ComfyRunState.CANCELLED
        elif path == "/interrupt":
            assert document == {"prompt_id": self.owner.prompt_id}
            self.owner.running = False
            self.owner.history_state = ComfyRunState.CANCELLED
        elif path == "/free":
            self.owner.free_requests.append(document)
            self.owner.system_counter += 1
        else:
            raise AssertionError(f"unexpected fixed route {path}")
        return SimpleNamespace(body=b"")


class _LifecycleClient:
    def __init__(self, prompt_id: str, *, state: str = "pending", modern: bool = True) -> None:
        self.endpoint = ComfyEndpoint.parse("http://127.0.0.1:8188")
        self.limits = ComfyTransportLimits()
        self.prompt_id = prompt_id
        self.pending = state == "pending"
        self.running = state == "running"
        self.history_state: ComfyRunState | None = None
        self.system_counter = 0
        self.free_requests: list[dict[str, Any]] = []
        self._http = _LifecycleHTTP(self, modern=modern)

    def queue(self) -> ComfyQueueSnapshot:
        payload = {
            "running": [self.prompt_id] if self.running else [],
            "pending": [self.prompt_id] if self.pending else [],
        }
        return ComfyQueueSnapshot(
            running_prompt_ids=tuple(payload["running"]),
            pending_prompt_ids=tuple(payload["pending"]),
            queue_remaining=int(self.pending),
            digest_sha256=canonical_sha256(payload),
        )

    def execution_history(self, prompt_id: str) -> ComfyExecutionHistory:
        assert prompt_id == self.prompt_id
        if self.history_state is None:
            return ComfyExecutionHistory(
                prompt_id=prompt_id,
                present=False,
                state=ComfyRunState.UNKNOWN,
                prompt_digest_sha256=None,
                extra_data_digest_sha256=None,
                correlation=(),
                output_references=(),
                digest_sha256=canonical_sha256({}),
            )
        correlation = (
            ("definition_id", "wf_" + "d" * 32),
            ("instance_digest_sha256", canonical_sha256({"instance": 7})),
            ("run_id", "run_" + "a" * 32),
        )
        return ComfyExecutionHistory(
            prompt_id=prompt_id,
            present=True,
            state=self.history_state,
            prompt_digest_sha256=canonical_sha256(PROMPT),
            extra_data_digest_sha256=canonical_sha256({"kodepoia": dict(correlation)}),
            correlation=correlation,
            output_references=(),
            digest_sha256=canonical_sha256({"state": self.history_state.value}),
        )

    def system_stats(self) -> ComfySystemSnapshot:
        return ComfySystemSnapshot(
            comfyui_version="fixture",
            python_version="3.12",
            device_count=1,
            digest_sha256=canonical_sha256({"system_counter": self.system_counter}),
        )


def _run(*, state: ComfyRunState = ComfyRunState.QUEUED) -> ComfyRunManifest:
    evidence: dict[str, Any] = {}
    draft = ComfyRunManifest(
        run_id="run_" + "a" * 32,
        revision=0,
        previous_manifest_digest_sha256=None,
        prompt_id="kp_" + "b" * 32,
        client_id="kc_" + "c" * 32,
        state=state,
        submission_outcome=ComfySubmissionOutcome.ACCEPTED,
        definition_id="wf_" + "d" * 32,
        definition_digest_sha256=canonical_sha256({"definition": 7}),
        capability_identity_sha256=canonical_sha256({"capability": 7}),
        capability_endpoint="http://127.0.0.1:8188",
        comfyui_version="fixture",
        python_version="3.12",
        model_resolution_digest_sha256=canonical_sha256(evidence),
        model_resolution_evidence_json=canonical_json_bytes(evidence).decode("utf-8"),
        instance_digest_sha256=canonical_sha256({"instance": 7}),
        prompt_digest_sha256=canonical_sha256(PROMPT),
        parameter_values=(),
        input_bindings=(),
        seed_values=(),
        required_output_node_ids=(),
        submission_attempts=1,
        submission_response_digest_sha256=canonical_sha256({"accepted": True}),
        progress_fraction=None,
        queue_digest_sha256=None,
        history_digest_sha256=None,
        output_references=(),
        manifest_digest_sha256="",
    )
    return replace(draft, manifest_digest_sha256=canonical_sha256(draft.canonical_without_digest()))


def _service(tmp_path: Path, *, queue_state: str, modern: bool = True, run_state: ComfyRunState = ComfyRunState.QUEUED):
    manifest = _run(state=run_state)
    store = ComfyRunStore(tmp_path / "runs")
    store.save(manifest)
    client = _LifecycleClient(manifest.prompt_id, state=queue_state, modern=modern)
    service = ComfyLifecycleService(client, store)
    instance = _Instance(manifest.instance_digest_sha256)
    return manifest, store, client, service, instance


def test_modern_pending_cancel_uses_atomic_job_endpoint_and_reconciles_cancelled(tmp_path: Path) -> None:
    run, _store, client, service, instance = _service(tmp_path, queue_state="pending")
    result = service.cancel(
        run.run_id,
        instance,
        budget=ComfyExecutionBudget(max_poll_attempts=3, poll_interval_seconds=0, max_wait_seconds=2),
    )
    assert result.state is ComfyRunState.CANCELLED
    assert [path for path, _ in client._http.calls] == [f"/api/jobs/{run.prompt_id}/cancel"]
    audit = service.audit.load(run.run_id)
    assert audit.events[-2].action is ComfyLifecycleAction.JOB_CANCEL
    assert audit.events[-2].outcome is ComfyLifecycleOutcome.DISPATCHED
    assert audit.events[-1].observed_state is ComfyRunState.CANCELLED
    schema = json.loads(AUDIT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(audit.payload())


def test_modern_running_cancel_never_calls_global_interrupt(tmp_path: Path) -> None:
    run, _store, client, service, instance = _service(tmp_path, queue_state="running", run_state=ComfyRunState.RUNNING)
    result = service.cancel(run.run_id, instance, budget=ComfyExecutionBudget(max_poll_attempts=3, poll_interval_seconds=0))
    assert result.state is ComfyRunState.CANCELLED
    assert all(path != "/interrupt" for path, _ in client._http.calls)
    assert client._http.calls[0][0] == f"/api/jobs/{run.prompt_id}/cancel"


@pytest.mark.parametrize(
    "queue_state,expected_path,run_state",
    [
        ("pending", "/queue", ComfyRunState.QUEUED),
        ("running", "/interrupt", ComfyRunState.RUNNING),
    ],
)
def test_legacy_fallback_is_state_classified_and_targeted(
    tmp_path: Path, queue_state: str, expected_path: str, run_state: ComfyRunState
) -> None:
    run, _store, client, service, instance = _service(
        tmp_path, queue_state=queue_state, modern=False, run_state=run_state
    )
    result = service.cancel(run.run_id, instance, budget=ComfyExecutionBudget(max_poll_attempts=3, poll_interval_seconds=0))
    assert result.state is ComfyRunState.CANCELLED
    assert client._http.calls[0][0] == f"/api/jobs/{run.prompt_id}/cancel"
    assert client._http.calls[1][0] == expected_path
    if expected_path == "/interrupt":
        assert client._http.calls[1][1] == {"prompt_id": run.prompt_id}


def test_terminal_race_becomes_noop_without_any_cancel_side_effect(tmp_path: Path) -> None:
    run, _store, client, service, instance = _service(tmp_path, queue_state="none")
    client.history_state = ComfyRunState.SUCCEEDED
    result = service.cancel(run.run_id, instance)
    assert result.state is ComfyRunState.SUCCEEDED
    assert client._http.calls == []
    audit = service.audit.load(run.run_id)
    assert audit.events[-1].action is ComfyLifecycleAction.NONE


def test_disappeared_unknown_job_never_fabricates_cancelled(tmp_path: Path) -> None:
    run, _store, client, service, instance = _service(tmp_path, queue_state="none")
    result = service.cancel(run.run_id, instance)
    assert result.state is ComfyRunState.QUEUED
    assert client._http.calls == []
    assert service.audit.load(run.run_id).events[-1].outcome in {
        ComfyLifecycleOutcome.NOOP,
        ComfyLifecycleOutcome.RECONCILED,
    }


def test_restart_recovery_repairs_current_pointer_then_reconciles(tmp_path: Path) -> None:
    run, store, client, service, instance = _service(tmp_path, queue_state="none")
    current_path = store.root / f"{run.run_id}.json"
    current_path.write_text("{}", encoding="utf-8")
    client.history_state = ComfyRunState.CANCELLED
    result = service.recover(run.run_id, instance)
    assert result.state is ComfyRunState.CANCELLED
    assert store.load(run.run_id).state is ComfyRunState.CANCELLED


def test_free_memory_request_is_ack_only_and_never_fabricates_reclaimed_bytes(tmp_path: Path) -> None:
    run, store, client, service, _instance = _service(
        tmp_path, queue_state="none", run_state=ComfyRunState.CANCELLED
    )
    evidence = service.request_free_memory(known_run_ids=(run.run_id,), settle_seconds=0)
    assert isinstance(evidence, ComfyFreeMemoryEvidence)
    assert evidence.request_acknowledged is True
    assert evidence.reclaimed_bytes is None
    assert evidence.before_system_digest_sha256 != evidence.after_system_digest_sha256
    assert client.free_requests == [{"free_memory": True, "unload_models": True}]


def test_free_memory_is_blocked_while_known_run_is_active(tmp_path: Path) -> None:
    run, _store, client, service, _instance = _service(tmp_path, queue_state="running", run_state=ComfyRunState.RUNNING)
    with pytest.raises(ComfyGovernanceError, match="non-terminal"):
        service.request_free_memory(known_run_ids=(run.run_id,))
    assert client.free_requests == []


def test_lifecycle_audit_tamper_is_rejected(tmp_path: Path) -> None:
    run, _store, _client, service, _instance = _service(tmp_path, queue_state="none")
    service.audit.append(
        run,
        action=ComfyLifecycleAction.RECOVER,
        outcome=ComfyLifecycleOutcome.NOOP,
        observed_state=run.state,
    )
    path = service.audit.root / f"{run.run_id}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["payload"]["events"][0]["outcome"] = "dispatched"
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ComfyProtocolError, match="digest"):
        ComfyLifecycleAuditStore(service.audit.root).load(run.run_id)
