from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d.acceptance import (
    R10IntegrationReport,
    R10IntegrationStatus,
    R10ManualState,
    build_continuity_evidence,
    build_local_evidence,
    build_prior_phase_evidence,
    build_subdivision_evidence,
    validate_repository_evidence,
)
from kodepoia.blender3d.boundary import (
    BlenderExecutableBoundary,
    validate_environment_overrides,
)
from kodepoia.blender3d.contracts import BlenderJobRecipe, BlenderOperation
from kodepoia.blender3d.errors import (
    BlenderBoundaryError,
    BlenderProtocolError,
    BlenderVersionError,
)
from kodepoia.blender3d.gltf_validator import parse_glb_bytes, parse_gltf_json_bytes
from kodepoia.blender3d.serialization import parse_envelope

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "key",
    [
        "addon",
        "argv",
        "code",
        "command",
        "cwd",
        "env",
        "environment",
        "executable",
        "operator",
        "path",
        "python",
        "script",
        "url",
    ],
)
def test_r10_12_recipe_injection_surface_is_fail_closed(key: str) -> None:
    with pytest.raises(ValueError, match="Forbidden recipe parameter key"):
        BlenderJobRecipe(
            BlenderOperation.BUILD_GEOMETRY,
            parameters=((key, "malicious"),),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_r10_12_nonfinite_recipe_parameters_are_rejected(value: float) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        BlenderJobRecipe(
            BlenderOperation.BUILD_GEOMETRY,
            parameters=(("scale", value),),
        )


@pytest.mark.parametrize(
    "key",
    [
        "PYTHONPATH",
        "PYTHONHOME",
        "BLENDER_USER_SCRIPTS",
        "BLENDER_SYSTEM_SCRIPTS",
        "BLENDER_SYSTEM_EXTENSIONS",
        "BLENDER_SYSTEM_PYTHON",
        "PATH",
    ],
)
def test_r10_12_environment_injection_is_rejected(key: str) -> None:
    with pytest.raises(BlenderBoundaryError, match="not allowlisted"):
        validate_environment_overrides({key: "escape"})


def test_r10_12_fixed_blender_argv_and_script_boundary(tmp_path: Path) -> None:
    install = tmp_path / "install"
    staging = tmp_path / "staging"
    outside = tmp_path / "outside"
    install.mkdir()
    staging.mkdir()
    outside.mkdir()
    executable = install / ("blender.exe" if os.name == "nt" else "blender")
    executable.write_bytes(b"fake")
    script = staging / "job.py"
    script.write_text("pass\n", encoding="utf-8")
    escaped = outside / "job.py"
    escaped.write_text("pass\n", encoding="utf-8")

    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=staging)
    argv = boundary.build_job_argv(executable, script)
    assert argv[1:] == (
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--offline-mode",
        "--python-exit-code",
        "17",
        "--python",
        str(script.resolve()),
    )
    assert "--enable-autoexec" not in argv
    assert "--online-mode" not in argv
    assert "--python-expr" not in argv
    assert "--python-text" not in argv
    assert "--python-use-system-env" not in argv

    with pytest.raises(BlenderBoundaryError, match="escapes staging root"):
        boundary.validate_job_script(escaped)


@pytest.mark.parametrize(
    "uri",
    [
        "../escape.bin",
        "dir/../../escape.bin",
        "https://evil.invalid/a.bin",
        "file:///tmp/a.bin",
        "/absolute/a.bin",
    ],
)
def test_r10_12_gltf_external_uri_escape_is_rejected(uri: str) -> None:
    payload = json.dumps(
        {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 4, "uri": uri}]}
    ).encode("utf-8")
    with pytest.raises(BlenderProtocolError, match="external URI"):
        parse_gltf_json_bytes(payload, max_bytes=4096)


def test_r10_12_gltf_data_uri_remains_bounded_and_valid() -> None:
    payload = json.dumps(
        {
            "asset": {"version": "2.0"},
            "buffers": [
                {
                    "byteLength": 3,
                    "uri": "data:application/octet-stream;base64,AAEC",
                }
            ],
        }
    ).encode("utf-8")
    document, facts = parse_gltf_json_bytes(payload, max_bytes=4096)
    assert document["asset"]["version"] == "2.0"
    assert facts.buffer_count == 1


def test_r10_12_glb_chunk_spoofing_and_length_mismatch_are_rejected() -> None:
    json_chunk = b'{"asset":{"version":"2.0"}}'
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    bad_chunk = b"evil"
    body = (
        struct.pack("<II", len(json_chunk), 0x4E4F534A)
        + json_chunk
        + struct.pack("<II", len(bad_chunk), 0x12345678)
        + bad_chunk
    )
    data = struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body
    with pytest.raises(BlenderProtocolError, match="unsupported chunk type"):
        parse_glb_bytes(data, max_bytes=4096)

    forged = bytearray(data)
    struct.pack_into("<I", forged, 8, len(data) + 4)
    with pytest.raises(BlenderProtocolError, match="header/version/declared length"):
        parse_glb_bytes(bytes(forged), max_bytes=4096)


def test_r10_12_schema_version_drift_is_rejected() -> None:
    with pytest.raises(BlenderVersionError, match="Unsupported"):
        parse_envelope(
            {"schema": "kodepoia.test", "version": 2, "payload": {}},
            expected_schema="kodepoia.test",
        )


def _fake_report() -> tuple[R10IntegrationReport, dict[str, bytes]]:
    repository: dict[str, bytes] = {}
    source_sha = "f" * 40
    subdivisions = []
    accepted_heads: list[str] = []

    for index in range(1, 13):
        subdivision = f"R10.{index}"
        accepted_head = source_sha if index == 12 else f"{index:040x}"
        accepted_heads.append(accepted_head)
        source = f"docs/roadmap/R10_{index}_ACCEPTANCE.md"
        if index == 11:
            repository[source] = (
                "# R10.11\n"
                "The pull request metadata is authoritative for exact-head binding.\n"
            ).encode("utf-8")
        else:
            repository[source] = (
                f"# {subdivision}\naccepted head `{accepted_head}`\nmanual state satisfied\n"
            ).encode("utf-8")

        if index in {2, 10}:
            manual = R10ManualState.REQUIRED_SATISFIED
        elif index == 12:
            manual = R10ManualState.CONDITIONAL_NOT_TRIGGERED
        else:
            manual = R10ManualState.NONE
        subdivisions.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=accepted_head,
                manual_state=manual,
                manual_reason=f"{subdivision} fixture manual state is satisfied.",
                canonical_bytes=repository[source],
            )
        )

    continuity_text = "# Kodepoia continuity\n" + "\n".join(
        f"- accepted `{head}`" for head in accepted_heads
    )
    repository["docs/continuity/KODEPOIA_CONTINUITY.md"] = (
        continuity_text + "\n"
    ).encode("utf-8")
    continuity = build_continuity_evidence(
        canonical_bytes=repository["docs/continuity/KODEPOIA_CONTINUITY.md"]
    )

    r2 = {
        "schema": "kodepoia.r10.local_blender_evidence",
        "version": 1,
        "source_sha": "2" * 40,
        "status": "pass",
        "blockers": [],
        "runtime": {"version": "5.2.0"},
        "command_policy": {
            "background": True,
            "factory_startup": True,
            "autoexec_disabled": True,
            "offline_mode": True,
        },
    }
    r10 = {
        "schema": "kodepoia.r10.gltf_local_acceptance",
        "version": 1,
        "source_sha": "a" * 40,
        "status": "pass",
        "blockers": [],
        "blender": {
            "version": "5.2.0 LTS",
            "background": True,
            "online_access": False,
        },
        "godot": {
            "version": {"major": 4, "minor": 7, "patch": 2},
            "semantic_smoke": {"pass_marker": True},
        },
    }
    repository["docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json"] = json.dumps(
        r2, sort_keys=True
    ).encode("utf-8")
    repository["docs/roadmap/R10_10_LOCAL_ACCEPTANCE.json"] = json.dumps(
        r10, sort_keys=True
    ).encode("utf-8")
    local_evidence = (
        build_local_evidence(
            "R10.2",
            canonical_bytes=repository["docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json"],
        ),
        build_local_evidence(
            "R10.10",
            canonical_bytes=repository["docs/roadmap/R10_10_LOCAL_ACCEPTANCE.json"],
            godot_major=4,
            godot_minor=7,
        ),
    )

    prior_phases = []
    for offset, phase in enumerate(("R7", "R8", "R9"), start=7):
        evidence_digest = f"{offset}" * 64
        document = {
            "schema_version": 1,
            "source_sha": f"{offset}" * 40,
            "status": "pass",
            "blockers": [],
            "evidence_sha256": evidence_digest,
        }
        path = f"docs/roadmap/{phase}_INTEGRATED_ACCEPTANCE.json"
        repository[path] = json.dumps(document, sort_keys=True).encode("utf-8")
        prior_phases.append(
            build_prior_phase_evidence(phase, canonical_bytes=repository[path])
        )

    report = R10IntegrationReport(
        generated_at="2026-08-24T10:00:00Z",
        source_sha=source_sha,
        subdivisions=tuple(subdivisions),
        continuity=continuity,
        local_evidence=local_evidence,
        prior_phases=tuple(prior_phases),
        status=R10IntegrationStatus.PASS,
    )
    return report, repository


def _replace_report(
    report: R10IntegrationReport,
    *,
    continuity=None,
    local_evidence=None,
    prior_phases=None,
) -> R10IntegrationReport:
    return R10IntegrationReport(
        generated_at=report.generated_at,
        source_sha=report.source_sha,
        subdivisions=report.subdivisions,
        continuity=report.continuity if continuity is None else continuity,
        local_evidence=report.local_evidence if local_evidence is None else local_evidence,
        prior_phases=report.prior_phases if prior_phases is None else prior_phases,
        status=R10IntegrationStatus.PASS,
    )


def test_r10_12_integrated_verifier_passes_only_immutable_bound_evidence() -> None:
    report, repository = _fake_report()
    validate_repository_evidence(report, repository.__getitem__)

    tampered = dict(repository)
    tampered["docs/roadmap/R10_5_ACCEPTANCE.md"] += b"tamper"
    with pytest.raises(ValueError, match="R10 acceptance identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)


def test_r10_12_normalized_continuity_is_immutable_head_authority() -> None:
    report, repository = _fake_report()
    tampered = dict(repository)
    tampered["docs/continuity/KODEPOIA_CONTINUITY.md"] += b"tamper"
    with pytest.raises(ValueError, match="continuity evidence identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    missing = dict(repository)
    missing["docs/continuity/KODEPOIA_CONTINUITY.md"] = (
        "# continuity without R10.11 accepted head\n"
    ).encode("utf-8")
    continuity = build_continuity_evidence(
        canonical_bytes=missing["docs/continuity/KODEPOIA_CONTINUITY.md"]
    )
    forged_report = _replace_report(report, continuity=continuity)
    with pytest.raises(ValueError, match="absent from both"):
        validate_repository_evidence(forged_report, missing.__getitem__)


def test_r10_12_required_local_runtime_spoofing_is_rejected() -> None:
    report, repository = _fake_report()
    tampered = dict(repository)
    document = json.loads(tampered["docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json"])
    document["runtime"]["version"] = "5.3.0"
    forged = json.dumps(document, sort_keys=True).encode("utf-8")
    local = list(report.local_evidence)
    local[0] = build_local_evidence("R10.2", canonical_bytes=forged)
    forged_report = _replace_report(report, local_evidence=tuple(local))
    tampered["docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json"] = forged
    with pytest.raises(ValueError, match="does not bind Blender 5.2"):
        validate_repository_evidence(forged_report, tampered.__getitem__)


def test_r10_12_prior_phase_fail_cannot_be_rebound_into_pass() -> None:
    report, repository = _fake_report()
    tampered = dict(repository)
    bad = json.loads(tampered["docs/roadmap/R8_INTEGRATED_ACCEPTANCE.json"])
    bad["status"] = "fail"
    bad["blockers"] = ["synthetic"]
    forged = json.dumps(bad, sort_keys=True).encode("utf-8")
    prior = list(report.prior_phases)
    prior[1] = build_prior_phase_evidence("R8", canonical_bytes=forged)
    forged_report = _replace_report(report, prior_phases=tuple(prior))
    tampered["docs/roadmap/R8_INTEGRATED_ACCEPTANCE.json"] = forged
    with pytest.raises(ValueError, match="R8 integrated report is not PASS"):
        validate_repository_evidence(forged_report, tampered.__getitem__)


def test_r10_12_report_digest_and_schema_detect_tampering() -> None:
    report, _ = _fake_report()
    payload = report.to_dict()
    Draft202012Validator(
        json.loads(
            (ROOT / "schemas/r10-integrated-acceptance-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
    ).validate(payload)
    roundtrip = R10IntegrationReport.from_dict(json.loads(json.dumps(payload)))
    assert roundtrip.evidence_sha256 == report.evidence_sha256

    payload["runtime_policy"]["blender"]["minor"] = 3
    with pytest.raises(ValueError, match="runtime policy"):
        R10IntegrationReport.from_dict(payload)


def test_r10_12_real_required_local_evidence_is_repository_bound_and_pass() -> None:
    r2_bytes = (ROOT / "docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json").read_bytes()
    r10_bytes = (ROOT / "docs/roadmap/R10_10_LOCAL_ACCEPTANCE.json").read_bytes()
    r2_document = json.loads(r2_bytes)
    r10_document = json.loads(r10_bytes)

    r2 = build_local_evidence("R10.2", canonical_bytes=r2_bytes)
    r10 = build_local_evidence(
        "R10.10",
        canonical_bytes=r10_bytes,
        godot_major=4,
        godot_minor=7,
    )

    assert r2.sha256 and r2.bytes == len(r2_bytes)
    assert r10.sha256 and r10.bytes == len(r10_bytes)
    assert r2.source_sha == "0a2da2334cc6ebe116819110ba80ad1729e22057"
    assert r10.source_sha == "85e2db277ce1cb467aeb9b056700150bc1d67fa7"
    assert r2_document["status"] == "pass" and r2_document["blockers"] == []
    assert r2_document["runtime"]["version"].startswith("5.2.")
    assert r2_document["command_policy"]["autoexec_disabled"] is True
    assert r2_document["command_policy"]["offline_mode"] is True
    assert r10_document["status"] == "pass" and r10_document["blockers"] == []
    assert r10_document["blender"]["version"].startswith("5.2.")
    assert r10_document["blender"]["online_access"] is False
    assert r10_document["godot"]["version"]["major"] == 4
    assert r10_document["godot"]["version"]["minor"] == 7
    assert r10_document["godot"]["semantic_smoke"]["pass_marker"] is True
