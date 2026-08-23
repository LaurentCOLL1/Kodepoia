from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from kodepoia.cli import build_parser
from kodepoia.comfyui import ComfyCapabilityState, ComfyProbeSnapshot, ComfyUIClient

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "comfy-protocol-probe-v1.schema.json"
_DIGEST = "0" * 64


def _ready_probe() -> ComfyProbeSnapshot:
    return ComfyProbeSnapshot(
        endpoint="http://127.0.0.1:8188",
        system=ComfyCapabilityState.CURRENT,
        features=ComfyCapabilityState.CURRENT,
        prompt_metadata=ComfyCapabilityState.CURRENT,
        queue=ComfyCapabilityState.CURRENT,
        history=ComfyCapabilityState.CURRENT,
        system_digest_sha256=_DIGEST,
        feature_digest_sha256=_DIGEST,
        prompt_digest_sha256=_DIGEST,
        queue_digest_sha256=_DIGEST,
        history_digest_sha256=_DIGEST,
    )


def test_comfy_probe_cli_writes_versioned_confined_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ComfyUIClient, "probe", lambda self: _ready_probe())
    args = build_parser().parse_args(
        [
            "comfy-probe",
            "--endpoint",
            "http://127.0.0.1:8188",
            "--output",
            ".kodepoia/evidence/probe.json",
        ]
    )
    assert args.func(args) == 0
    output = tmp_path / ".kodepoia" / "evidence" / "probe.json"
    document = json.loads(output.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validate(document, schema)
    assert document["schema"] == "kodepoia.comfy-protocol-probe"
    assert document["version"] == 1
    assert document["payload"]["ready"] is True


def test_comfy_probe_cli_rejects_output_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ComfyUIClient, "probe", lambda self: _ready_probe())
    args = build_parser().parse_args(["comfy-probe", "--output", "../escape.json"])
    with pytest.raises(SystemExit, match="workspace"):
        args.func(args)


def test_probe_schema_rejects_unknown_root_or_payload_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = {
        "schema": "kodepoia.comfy-protocol-probe",
        "version": 1,
        "payload": _ready_probe().canonical(),
    }
    validate(document, schema)
    with pytest.raises(Exception):
        validate({**document, "unexpected": True}, schema)
    with pytest.raises(Exception):
        validate(
            {
                **document,
                "payload": {**document["payload"], "unexpected": True},
            },
            schema,
        )
