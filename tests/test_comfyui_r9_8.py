from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from kodepoia.comfyui import ComfyEndpoint, ComfyFreeMemoryEvidence
from kodepoia.comfyui.errors import ComfyProtocolError
from kodepoia.comfyui.r9_8_acceptance import (
    _seal_evidence,
    load_r98_evidence,
    write_r98_evidence,
)
from kodepoia.comfyui.resources import (
    ComfyDeviceMemory,
    ComfyVramSnapshot,
    ComfyVramTelemetryAdapter,
    GpuAdmissionDecision,
    GpuAdmissionPolicy,
    GpuResourceCoordinator,
    GpuResourceProfile,
    OllamaCoexistenceState,
    OllamaMemorySnapshot,
    OllamaRunningModelMemory,
    WorkflowMemoryObservation,
    vram_budget_observation,
    vram_health_metric,
)
from kodepoia.comfyui.serialization import canonical_sha256
from kodepoia.core.audit import AuditLog
from kodepoia.quality.budget import BudgetMetric
from kodepoia.quality.health import HealthDimension, HealthStatus

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_8_vram.json"
PAYLOAD_SCHEMA = ROOT / "schemas" / "comfy-vram-evidence-payload-v1.schema.json"


class _HTTP:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document

    def get_json(self, path: str) -> dict[str, Any]:
        assert path == "/system_stats"
        return json.loads(json.dumps(self.document))


class _Client:
    def __init__(self, document: dict[str, Any]) -> None:
        self.endpoint = ComfyEndpoint.parse("http://127.0.0.1:8188")
        self._http = _HTTP(document)


def _snapshot(*, free_gib: int, total_gib: int = 12, index: int = 0) -> ComfyVramSnapshot:
    device = ComfyDeviceMemory(
        name=f"gpu-{index}",
        backend_type="fixture",
        index=index,
        vram_total_bytes=total_gib * 1024**3,
        vram_free_bytes=free_gib * 1024**3,
        torch_vram_total_bytes=None,
        torch_vram_free_bytes=None,
    )
    payload = {
        "endpoint": "http://127.0.0.1:8188",
        "comfyui_version": "fixture",
        "python_version": "3.12",
        "devices": [device.canonical()],
    }
    return ComfyVramSnapshot(
        endpoint=payload["endpoint"],
        comfyui_version=payload["comfyui_version"],
        python_version=payload["python_version"],
        devices=(device,),
        digest_sha256=canonical_sha256(payload),
    )


class _Telemetry:
    def __init__(self, snapshots: list[ComfyVramSnapshot]) -> None:
        self.snapshots = list(snapshots)
        self.calls = 0

    def sample(self) -> ComfyVramSnapshot:
        self.calls += 1
        if len(self.snapshots) > 1:
            return self.snapshots.pop(0)
        return self.snapshots[0]


class _Lifecycle:
    def __init__(self) -> None:
        self.calls = 0

    def request_free_memory(self) -> ComfyFreeMemoryEvidence:
        self.calls += 1
        return ComfyFreeMemoryEvidence(
            endpoint="http://127.0.0.1:8188",
            unload_models=True,
            free_memory=True,
            request_digest_sha256="a" * 64,
            before_system_digest_sha256="b" * 64,
            after_system_digest_sha256="c" * 64,
            request_acknowledged=True,
            reclaimed_bytes=None,
        )


class _Ollama:
    def __init__(self) -> None:
        model = OllamaRunningModelMemory("fixture:latest", 2 * 1024**3, None)
        payload = {
            "base_url": "http://127.0.0.1:11434",
            "state": OllamaCoexistenceState.TESTED.value,
            "models": [model.canonical()],
        }
        self.snapshot = OllamaMemorySnapshot(
            "http://127.0.0.1:11434",
            OllamaCoexistenceState.TESTED,
            (model,),
            canonical_sha256(payload),
        )
        self.unloaded: list[str] = []
        self.restored: list[str] = []

    def sample(self) -> OllamaMemorySnapshot:
        return self.snapshot

    def unload_approved(
        self,
        snapshot: OllamaMemorySnapshot,
        approved_names: tuple[str, ...],
    ) -> tuple[str, ...]:
        assert snapshot is self.snapshot
        self.unloaded.extend(approved_names)
        return approved_names

    def restore_explicit(self, names: tuple[str, ...]) -> None:
        self.restored.extend(names)


def test_r98_fixture_normalizes_all_devices_and_preserves_bytes() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    adapter = ComfyVramTelemetryAdapter(_Client(fixture["system_stats"]))
    snapshot = adapter.sample()
    assert [item.index for item in snapshot.devices] == [0, 1]
    assert snapshot.devices[0].vram_total_bytes == 12 * 1024**3
    assert snapshot.devices[1].vram_free_bytes == 6 * 1024**3
    assert snapshot.primary is snapshot.devices[0]
    assert snapshot.device(1) is snapshot.devices[1]
    assert snapshot.digest_sha256 == canonical_sha256(snapshot.canonical_without_digest())


def test_r98_telemetry_rejects_impossible_free_memory() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["system_stats"]["devices"][0]["vram_free"] = 13 * 1024**3
    with pytest.raises(ComfyProtocolError, match="greater than total"):
        ComfyVramTelemetryAdapter(_Client(fixture["system_stats"])).sample()


def test_r98_policy_emits_admit_defer_reject_unknown_and_honors_total_limit() -> None:
    policy = GpuAdmissionPolicy()
    snapshot = _snapshot(free_gib=10, total_gib=12)

    admitted = policy.decide(
        snapshot,
        GpuResourceProfile(
            estimate_bytes=4 * 1024**3,
            reserve_bytes=1 * 1024**3,
            headroom_bytes=0,
            total_limit_bytes=6 * 1024**3,
        ),
    )
    assert admitted.decision is GpuAdmissionDecision.ADMIT
    assert admitted.policy_total_bytes == 6 * 1024**3

    rejected = policy.decide(
        snapshot,
        GpuResourceProfile(
            estimate_bytes=5 * 1024**3,
            reserve_bytes=1 * 1024**3,
            headroom_bytes=1 * 1024**3,
            total_limit_bytes=6 * 1024**3,
        ),
    )
    assert rejected.decision is GpuAdmissionDecision.REJECT

    deferred = policy.decide(
        _snapshot(free_gib=6),
        GpuResourceProfile(
            estimate_bytes=4 * 1024**3,
            reserve_bytes=1 * 1024**3,
            headroom_bytes=2 * 1024**3,
        ),
    )
    assert deferred.decision is GpuAdmissionDecision.DEFER

    unknown = policy.decide(
        snapshot,
        GpuResourceProfile(1, 0, 0, device_index=7),
    )
    assert unknown.decision is GpuAdmissionDecision.UNKNOWN


def test_r98_coordinator_cleanup_order_requires_explicit_ollama_authorization(tmp_path: Path) -> None:
    telemetry = _Telemetry([_snapshot(free_gib=4), _snapshot(free_gib=9)])
    lifecycle = _Lifecycle()
    ollama = _Ollama()
    audit = AuditLog(tmp_path / "resource.jsonl")
    coordinator = GpuResourceCoordinator(
        telemetry,
        lifecycle,
        ollama=ollama,
        audit_log=audit,
    )
    profile = GpuResourceProfile(
        estimate_bytes=6 * 1024**3,
        reserve_bytes=1 * 1024**3,
        headroom_bytes=1 * 1024**3,
    )

    trace = coordinator.admit_with_cleanup(
        profile,
        approved_ollama_unloads=("fixture:latest",),
    )
    assert trace.initial.decision is GpuAdmissionDecision.DEFER
    assert trace.final.decision is GpuAdmissionDecision.ADMIT
    assert trace.ollama_unloaded == ("fixture:latest",)
    assert lifecycle.calls == 1
    assert telemetry.calls == 2
    assert ollama.unloaded == ["fixture:latest"]
    assert audit.verify()

    restored = coordinator.restore_prior_ollama(trace)
    assert restored == ("fixture:latest",)
    assert ollama.restored == ["fixture:latest"]
    assert audit.verify()


def test_r98_coordinator_never_unloads_ollama_without_explicit_allowlist(tmp_path: Path) -> None:
    telemetry = _Telemetry([_snapshot(free_gib=4), _snapshot(free_gib=9)])
    ollama = _Ollama()
    coordinator = GpuResourceCoordinator(
        telemetry,
        _Lifecycle(),
        ollama=ollama,
        audit_log=AuditLog(tmp_path / "resource.jsonl"),
    )
    trace = coordinator.admit_with_cleanup(
        GpuResourceProfile(
            estimate_bytes=6 * 1024**3,
            reserve_bytes=1 * 1024**3,
            headroom_bytes=1 * 1024**3,
        )
    )
    assert trace.final.decision is GpuAdmissionDecision.ADMIT
    assert trace.ollama_unloaded == ()
    assert ollama.unloaded == []


def test_r98_oom_feedback_only_raises_estimate() -> None:
    observation = WorkflowMemoryObservation.create(
        "wf_" + "d" * 32,
        (8 * 1024**3, 6 * 1024**3, 7 * 1024**3),
        oom_observed=False,
    )
    assert observation.observed_peak_delta_bytes == 2 * 1024**3
    assert observation.updated_estimate(3 * 1024**3) == 3 * 1024**3

    oom = WorkflowMemoryObservation.create(
        "wf_" + "d" * 32,
        (8 * 1024**3, 7 * 1024**3),
        oom_observed=True,
    )
    assert oom.updated_estimate(3 * 1024**3) > 3 * 1024**3


def test_r98_health_and_budget_bridge_reuses_frozen_quality_contracts() -> None:
    snapshot = _snapshot(free_gib=8, total_gib=12)
    observation = vram_budget_observation(snapshot)
    assert observation.metric is BudgetMetric.VRAM_MB
    assert observation.value == 4096.0

    result = GpuAdmissionPolicy().decide(
        snapshot,
        GpuResourceProfile(
            estimate_bytes=4 * 1024**3,
            reserve_bytes=1 * 1024**3,
            headroom_bytes=1 * 1024**3,
        ),
    )
    metric = vram_health_metric(result)
    assert metric.dimension is HealthDimension.MEMORY
    assert metric.status is HealthStatus.PASS


def test_r98_payload_schema_and_tamper_checked_round_trip(tmp_path: Path) -> None:
    evidence = _seal_evidence(
        candidate_head="a" * 40,
        status="pass",
        endpoint="http://127.0.0.1:8188",
        capability_identity_sha256="b" * 64,
        comfyui_version="fixture",
        device={"index": 0},
        resource_profile={"estimate_bytes": 1},
        scheduler_trace={"final": {"decision": "admit"}},
        workflow_definition_id="wf_" + "c" * 32,
        workflow_instance_digest_sha256="d" * 64,
        run_id="run_" + "e" * 32,
        run_manifest_digest_sha256="f" * 64,
        output_sha256="1" * 64,
        output_length=1,
        memory_observation={"observed_peak_delta_bytes": 1},
        terminal_cleanup={"request_acknowledged": True},
        ollama_state="n/a",
        ollama_reason="no pre-existing Ollama workload",
        ollama_restored=(),
        resource_audit_relative_path=".kodepoia/evidence/r9-8/resource-audit.jsonl",
        resource_audit_valid=True,
        lifecycle_audit_valid=True,
        failure_reason=None,
    )
    schema = json.loads(PAYLOAD_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(evidence.payload())

    path = write_r98_evidence(tmp_path, ".kodepoia/evidence/r9-8-local-vram.json", evidence)
    loaded = load_r98_evidence(path)
    assert loaded == evidence

    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload"]["output_length"] = 2
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ComfyProtocolError, match="digest"):
        load_r98_evidence(path)
