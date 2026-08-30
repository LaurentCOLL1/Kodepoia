from __future__ import annotations

import json
from pathlib import Path

import jsonschema

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
    QualificationPolicy,
)


class Source:
    def head(self, root: Path) -> str:
        return "d" * 40


class Runtime:
    def probe(self, request: RuntimeRequest) -> CapabilityReport:
        return CapabilityReport(
            disposition=RuntimeDisposition.READY,
            request_digest="e" * 64,
            backend=TrainingBackend.CPU,
            backend_capability=CapabilityState.SUPPORTED,
            dtype_supported=True,
            four_bit_supported=None,
            packages=(("torch", "fixture"),),
            python_version="3.12.0",
            torch_backend_version="cpu",
            device={"backend_type": "cpu", "index": 0, "name": "fixture"},
            resources=ResourcePreflight(1, 1, None, None),
            seed_applied=True,
            model_load=None,
            blockers=(),
        )


class Tools:
    def ollama(self) -> dict[str, object]:
        return {"available": True, "version": "fixture"}


def test_local_qualification_report_matches_repository_schema(tmp_path: Path) -> None:
    report = LocalQualificationService(
        tmp_path,
        runtime=Runtime(),
        source_probe=Source(),
        tool_probe=Tools(),
    ).doctor(
        expected_source_sha="d" * 40,
        runtime_request=RuntimeRequest(),
        policy=QualificationPolicy(training_required=True, ollama_required=True),
    )
    schema = json.loads(
        Path("schemas/r15-16-local-qualification-v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(report)
