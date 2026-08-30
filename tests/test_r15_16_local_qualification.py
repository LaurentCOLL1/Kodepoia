from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.tuning.contracts import (
    CapabilityReport,
    CapabilityState,
    ResourcePreflight,
    RuntimeDisposition,
    RuntimeRequest,
    TrainingBackend,
)
from kodepoia.tuning.local_qualification import (
    LocalQualificationService,
    QualificationError,
    QualificationPolicy,
    safe_output_path,
)

_SHA = "a" * 40


class FakeSource:
    def __init__(self, value: str = _SHA) -> None:
        self.value = value

    def head(self, root: Path) -> str:
        return self.value


class FakeTools:
    def __init__(self, *, available: bool = False) -> None:
        self.available = available

    def ollama(self) -> dict[str, object]:
        return {
            "available": self.available,
            "version": "ollama version fixture" if self.available else None,
        }


class FakeRuntime:
    def __init__(self, report: CapabilityReport) -> None:
        self.report = report
        self.calls = 0

    def probe(self, request: RuntimeRequest) -> CapabilityReport:
        self.calls += 1
        return self.report


def capability(disposition: RuntimeDisposition) -> CapabilityReport:
    state = (
        CapabilityState.SUPPORTED
        if disposition is RuntimeDisposition.READY
        else CapabilityState.UNSUPPORTED
    )
    return CapabilityReport(
        disposition=disposition,
        request_digest="b" * 64,
        backend=TrainingBackend.CPU,
        backend_capability=state,
        dtype_supported=disposition is RuntimeDisposition.READY,
        four_bit_supported=False,
        packages=(("torch", None),),
        python_version="3.12.0",
        torch_backend_version=None,
        device=None,
        resources=ResourcePreflight(1_000_000, 2_000_000, None, None),
        seed_applied=True,
        model_load=None,
        blockers=() if disposition is RuntimeDisposition.READY else ("backend_unavailable",),
    )


def test_source_mismatch_blocks_before_runtime_probe(tmp_path: Path) -> None:
    runtime = FakeRuntime(capability(RuntimeDisposition.READY))
    report = LocalQualificationService(
        tmp_path,
        runtime=runtime,
        source_probe=FakeSource("c" * 40),
        tool_probe=FakeTools(),
    ).doctor(expected_source_sha=_SHA, runtime_request=RuntimeRequest())

    assert report["status"] == "blocked"
    assert report["result"] == "source_sha_mismatch"
    assert report["blockers"] == ["source_sha_mismatch"]
    assert runtime.calls == 0


def test_no_train_required_accepts_truthful_unsupported_backend(tmp_path: Path) -> None:
    report = LocalQualificationService(
        tmp_path,
        runtime=FakeRuntime(capability(RuntimeDisposition.UNSUPPORTED)),
        source_probe=FakeSource(),
        tool_probe=FakeTools(),
    ).doctor(expected_source_sha=_SHA, runtime_request=RuntimeRequest())

    assert report["status"] == "pass"
    assert report["result"] == "no_train_required"
    assert report["blockers"] == []
    assert "training_probe:unsupported" in report["warnings"]
    assert "ollama_unavailable" in report["warnings"]


def test_training_required_fails_closed_when_backend_is_unavailable(tmp_path: Path) -> None:
    report = LocalQualificationService(
        tmp_path,
        runtime=FakeRuntime(capability(RuntimeDisposition.UNSUPPORTED)),
        source_probe=FakeSource(),
        tool_probe=FakeTools(available=True),
    ).doctor(
        expected_source_sha=_SHA,
        runtime_request=RuntimeRequest(),
        policy=QualificationPolicy(training_required=True),
    )

    assert report["status"] == "blocked"
    assert report["result"] == "training_backend_unavailable"
    assert report["blockers"] == ["training_backend_unavailable"]


def test_training_required_passes_only_for_ready_backend(tmp_path: Path) -> None:
    report = LocalQualificationService(
        tmp_path,
        runtime=FakeRuntime(capability(RuntimeDisposition.READY)),
        source_probe=FakeSource(),
        tool_probe=FakeTools(available=True),
    ).doctor(
        expected_source_sha=_SHA,
        runtime_request=RuntimeRequest(),
        policy=QualificationPolicy(training_required=True, ollama_required=True),
    )

    assert report["status"] == "pass"
    assert report["result"] == "training_backend_ready"
    assert report["blockers"] == []


def test_required_ollama_is_a_separate_fail_closed_gate(tmp_path: Path) -> None:
    report = LocalQualificationService(
        tmp_path,
        runtime=FakeRuntime(capability(RuntimeDisposition.READY)),
        source_probe=FakeSource(),
        tool_probe=FakeTools(),
    ).doctor(
        expected_source_sha=_SHA,
        runtime_request=RuntimeRequest(),
        policy=QualificationPolicy(ollama_required=True),
    )

    assert report["status"] == "blocked"
    assert report["result"] == "ollama_required_unavailable"
    assert report["blockers"] == ["ollama_unavailable"]


def test_report_digest_is_canonical_and_excludes_itself(tmp_path: Path) -> None:
    report = LocalQualificationService(
        tmp_path,
        runtime=FakeRuntime(capability(RuntimeDisposition.READY)),
        source_probe=FakeSource(),
        tool_probe=FakeTools(available=True),
    ).doctor(expected_source_sha=_SHA, runtime_request=RuntimeRequest())

    digest = report.pop("report_sha256")
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_output_must_remain_inside_project_root(tmp_path: Path) -> None:
    assert safe_output_path(tmp_path, Path(".kodepoia/report.json")).is_relative_to(tmp_path)
    with pytest.raises(QualificationError, match="inside the project root"):
        safe_output_path(tmp_path, Path("../escape.json"))


def test_expected_sha_is_strict(tmp_path: Path) -> None:
    service = LocalQualificationService(
        tmp_path,
        runtime=FakeRuntime(capability(RuntimeDisposition.READY)),
        source_probe=FakeSource(),
        tool_probe=FakeTools(),
    )
    with pytest.raises(QualificationError, match="40-character"):
        service.doctor(expected_source_sha="main", runtime_request=RuntimeRequest())
