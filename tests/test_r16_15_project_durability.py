from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.project.r16_15_acceptance import (
    FIXTURE_RELATIVE,
    DurabilityGovernanceError,
    _load_fixture,
    build_project_durability_report,
    qualify_extended_local_soak,
    validate_fixture_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def _fixture() -> dict[str, object]:
    return json.loads((ROOT / FIXTURE_RELATIVE).read_text(encoding="utf-8"))


def test_r16_15_fixture_is_deterministic_and_bounded() -> None:
    payload = _fixture()
    validated = validate_fixture_payload(payload)
    assert validated["name"] == "r16.15-long-term-project-durability-resume-upgrade-soak"
    assert len(validated["sessions"]) == 3
    assert validated["budgets"]["soak_cycles"] == 8
    assert validated["authority"]["permission_epoch"] == 7


def test_r16_15_fixture_digest_is_line_ending_independent(tmp_path: Path) -> None:
    raw = (ROOT / FIXTURE_RELATIVE).read_bytes().replace(b"\r\n", b"\n")
    digests: list[str] = []
    for name, content in (
        ("lf", raw),
        ("crlf", raw.replace(b"\n", b"\r\n")),
    ):
        root = tmp_path / name
        fixture_path = root / FIXTURE_RELATIVE
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_bytes(content)
        _payload, canonical_bytes = _load_fixture(root)
        digests.append(hashlib.sha256(canonical_bytes).hexdigest())
    assert digests[0] == digests[1]


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("artifact", "../../escape.txt", "escapes"),
        ("artifact", ".kodepoia/authority.json", "internal recovery state"),
    ],
)
def test_r16_15_fixture_rejects_unsafe_artifact_path(
    field: str,
    value: str,
    match: str,
) -> None:
    payload = copy.deepcopy(_fixture())
    payload["sessions"][0][field] = value
    with pytest.raises(DurabilityGovernanceError, match=match):
        validate_fixture_payload(payload)


def test_r16_15_fixture_rejects_secret_material_instead_of_secret_ref() -> None:
    payload = copy.deepcopy(_fixture())
    payload["authority"]["secret_refs"] = ["ghp_" + "a" * 32]
    with pytest.raises(DurabilityGovernanceError, match="references only"):
        validate_fixture_payload(payload)


def test_r16_15_extended_soak_is_never_inferred() -> None:
    core = qualify_extended_local_soak(requested=False)
    requested = qualify_extended_local_soak(requested=True)
    assert core["state"] == "NOT_EXERCISED"
    assert core["claim_satisfied"] is False
    assert core["manual_required"] is False
    assert requested["state"] == "MANUAL_REQUIRED"
    assert requested["manual_required"] is True
    assert requested["claim_satisfied"] is False


def test_r16_15_full_project_durability_report() -> None:
    report = build_project_durability_report(
        ROOT,
        source_sha="1" * 40,
        platform="synthetic-test",
    )
    failed = [item for item in report["cases"] if not item["pass"]]
    assert report["durability_claim"] is True, failed
    assert report["critical_veto"] is False
    assert report["secret_free"] is True
    assert report["manual_state"] == "CONDITIONAL_NOT_TRIGGERED"
    assert report["core_manual_required"] is False
    assert report["external_network_calls"] == 0
    assert report["destructive_host_actions"] == 0
    assert report["clean_process_sessions"] == 3
    assert report["bounded_soak_cycles"] == 8
    assert report["summary"] == {"total": 20, "passed": 20, "failed": 0}
    assert report["memory_recovery"]["tamper_quarantined"] is True
    assert report["memory_recovery"]["memory_restored"] is True
    assert report["database_migration"]["failed_migration_rolled_back"] is True
    assert report["database_migration"]["final_version"] == 2
    assert report["registry_recovery"]["interruption_blocked"] is True
    assert report["registry_recovery"]["baseline_restored"] is True
    for key in (
        "fixture_sha256",
        "semantic_sha256",
        "expected_semantic_sha256",
        "evidence_sha256",
    ):
        assert len(report[key]) == 64
