from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from kodepoia.comfyui.beta_acceptance import (
    FIXTURE_RELATIVE,
    build_comfyui_beta_report,
    qualify_live_local_comfyui,
    validate_fixture_payload,
)
from kodepoia.comfyui.errors import ComfyGovernanceError
from kodepoia.comfyui.serialization import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def _fixture() -> dict[str, object]:
    return json.loads((ROOT / FIXTURE_RELATIVE).read_text(encoding="utf-8"))


def test_r16_13_fixture_digest_is_line_ending_independent() -> None:
    raw = (ROOT / FIXTURE_RELATIVE).read_bytes()
    payload_lf = json.loads(raw.decode("utf-8"))
    payload_crlf = json.loads(raw.replace(b"\n", b"\r\n").decode("utf-8"))
    assert canonical_sha256(payload_lf) == canonical_sha256(payload_crlf)


def test_r16_13_fixture_is_deterministic_and_bounded() -> None:
    payload = _fixture()
    definition, budgets = validate_fixture_payload(payload)
    assert definition.name == "r16.13-representative-comfyui-beta"
    assert set(definition.allowed_node_classes) == {
        "R16FixtureSource",
        "R16FixtureOutput",
    }
    assert budgets.ram_bytes == 512 * 1024 * 1024
    assert budgets.disk_bytes == 1024 * 1024
    assert budgets.gpu_profile().required_free_bytes == 512 * 1024 * 1024


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("output_relative", "../../escape.bin", "must not escape"),
        ("command_intent", "R16_13_COMMAND_INTENT_SHOULD_NOT_RUN", "command intent"),
        ("external_reference", "https://example.invalid/model", "external workflow references"),
    ],
)
def test_r16_13_fixture_rejects_security_metadata(
    field: str,
    value: str,
    match: str,
) -> None:
    payload = copy.deepcopy(_fixture())
    metadata = payload["metadata"]
    assert isinstance(metadata, dict)
    metadata[field] = value
    with pytest.raises(ComfyGovernanceError, match=match):
        validate_fixture_payload(payload)


def test_r16_13_live_qualification_rejects_non_loopback_without_claim() -> None:
    report = qualify_live_local_comfyui("https://example.com:8188")
    assert report["state"] == "UNAVAILABLE"
    assert report["claim_satisfied"] is False


def test_r16_13_full_loopback_fixture_report() -> None:
    report = build_comfyui_beta_report(
        ROOT,
        source_sha="1" * 40,
        platform="synthetic-test",
    )
    failed = [item for item in report["cases"] if not item["pass"]]
    assert report["security_claim"] is True, failed
    assert report["critical_veto"] is False
    assert report["manual_state"] == "CONDITIONAL_NOT_TRIGGERED"
    assert report["core_manual_required"] is False
    assert report["external_network_calls"] == 0
    assert report["fixture_is_real_comfyui"] is False
    assert report["fixture_is_real_gpu"] is False
    assert report["live_local_qualification"]["state"] == "NOT_EXERCISED"
    assert report["summary"] == {"total": 12, "passed": 12, "failed": 0}
    assert report["secret_free"] is True
    assert len(report["fixture_sha256"]) == 64
    assert report["fixture_sha256"] == canonical_sha256(_fixture())
    assert len(report["workflow_sha256"]) == 64
    assert len(report["budget_sha256"]) == 64
    assert len(report["output_sha256"]) == 64
    assert len(report["binding_sha256"]) == 64
    assert len(report["semantic_sha256"]) == 64
    assert len(report["evidence_sha256"]) == 64
