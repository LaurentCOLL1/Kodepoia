from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.media.acceptance import (
    R11IntegratedReport,
    build_repository_report,
    validate_repository_evidence,
)
from kodepoia.media.boundary import (
    MediaBoundaryError,
    MediaRuntimeBoundary,
    validate_environment_overrides,
)
from kodepoia.media.franchise.canon import (
    AuthorityTier,
    CanonRecord,
    CanonSnapshot,
    CanonStatus,
)
from kodepoia.media.savebridge.migration import (
    MigrationRegistry,
    MigrationStep,
    build_save_document,
    parse_save_document,
)
from kodepoia.media.serialization import (
    MediaProtocolError,
    canonical_json_bytes,
    canonical_sha256,
    parse_envelope,
)
from kodepoia.media.voice.markup import SpeechSegment, SpeechSegmentKind
from kodepoia.media.voice.profiles import normalize_voice_text

ROOT = Path(__file__).resolve().parents[1]

_ACCEPTED_LOCAL_DIGESTS = {
    "R11.5": "12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe",
    "R11.9": "6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5",
}
_ACCEPTED_PRIOR_DIGESTS = {
    "R7": "5b56bb94b6c5c0b8a11e0d1883d0123f0803418414509517e88204990647e2fc",
    "R8": "c73868d7f89453c65d3b633ccdded70d031766c1ce05b77c02e8e4a0d51ed8c5",
    "R9": "ad8ad9d16682f54dd942e76dccf333234065d27f320409301cbb8dd67036dcdc",
    "R10": "48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8",
}
_ACCEPTED_HEADS = {
    "R11.1": "46ee14f3e94ed8c5c1cadbf139a890fab853929f",
    "R11.2": "103365dc7d5e3d725e0a9d23a839283079fe959c",
    "R11.3": "a835ab4491b5c49268ac85e389a2584ba379fcf3",
    "R11.4": "a662046c9fd38a198cc76c33b9012774f254407c",
    "R11.5": "a9862b3bf475b259fe154d1e2486116ad04602f3",
    "R11.6": "ea86762ecaa5ab16f6637701638c3461eea9d5ce",
    "R11.7": "1d2347178b804ae46e8696a8fd78e88e8cb2d84b",
    "R11.8": "26703862a91b5d6a86e83be4f0c2dfabd0541efc",
    "R11.9": "087eae19ea03dd544d75a08c1eb348fe187624c5",
    "R11.10": "5fb1b80a212880bd510977d54a570859c532c206",
    "R11.11": "38dc7dce1bf288b61eabfa3b174add11ade4ae49",
    "R11.12": "66ccd03bf486ac325ee2fba7133a6fc2a9c244b0",
    "R11.13": "79a891eaede7e5ecf7d8daf35846b20b1d3d02f9",
}


def test_r11_14_environment_and_path_injection_fail_closed(tmp_path: Path) -> None:
    for key in ("PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "FFREPORT", "PATH"):
        with pytest.raises(MediaBoundaryError, match="not allowlisted"):
            validate_environment_overrides({key: "escape"})
    with pytest.raises(MediaBoundaryError, match="NUL"):
        validate_environment_overrides({"KODEPOIA_RUN_ID": "ok\x00escape"})

    runtime_root = tmp_path / "runtime"
    staging = tmp_path / "staging"
    runtime_root.mkdir()
    staging.mkdir()
    boundary = MediaRuntimeBoundary(allowed_roots=(runtime_root,), staging_root=staging)
    with pytest.raises(MediaBoundaryError, match="escapes staging root"):
        boundary.validate_output(tmp_path / "outside.wav", suffixes=frozenset({".wav"}))


def test_r11_14_unicode_bidi_control_and_raw_markup_fail_closed() -> None:
    for payload in ("safe\u202Eevil", "safe\u2066evil\u2069", "safe\x00evil"):
        with pytest.raises(ValueError):
            normalize_voice_text(payload)
    with pytest.raises(ValueError, match="XML/SSML"):
        SpeechSegment(SpeechSegmentKind.TEXT, text="<speak>unsafe</speak>")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_r11_14_nonfinite_values_do_not_enter_semantic_payloads(value: float) -> None:
    with pytest.raises(MediaProtocolError):
        canonical_json_bytes({"value": value})
    with pytest.raises(ValueError, match="pause_seconds"):
        SpeechSegment(SpeechSegmentKind.PAUSE, pause_seconds=value)


def test_r11_14_schema_version_substitution_is_rejected() -> None:
    with pytest.raises(MediaProtocolError, match="Unexpected R11 schema/version"):
        parse_envelope(
            {"schema": "kodepoia.r11.test", "version": 2, "payload": {}},
            expected_schema="kodepoia.r11.test",
        )


def _canon_record(
    record_id: str,
    *,
    authority: AuthorityTier = AuthorityTier.PROJECT,
    status: CanonStatus = CanonStatus.PROPOSED,
    supersedes: tuple[str, ...] = (),
) -> CanonRecord:
    return CanonRecord(
        record_id=record_id,
        subject="character.hero",
        predicate="identity.name",
        value="A",
        authority=authority,
        status=status,
        source_refs=("source.fixture",),
        content_version="1",
        supersedes=supersedes,
    )


def test_r11_14_canon_unauthorized_promotion_and_graph_cycle_fail_closed() -> None:
    with pytest.raises(ValueError, match="research authority cannot be canonical"):
        _canon_record(
            "canon.research",
            authority=AuthorityTier.RESEARCH,
            status=CanonStatus.CANONICAL,
        )

    left = _canon_record("canon.left", supersedes=("canon.right",))
    right = _canon_record("canon.right", supersedes=("canon.left",))
    with pytest.raises(ValueError, match="Circular canon"):
        CanonSnapshot("snapshot.test", "franchise.test", (left, right))


def test_r11_14_save_checksum_and_migration_cycle_fail_closed() -> None:
    document = build_save_document(
        schema_id="save.test",
        schema_version=1,
        project_id="project.test",
        franchise_dna_id="franchise.test",
        content_version="1",
        canon_snapshot_digest="a" * 64,
        state={"score": 1},
    )
    forged = document.canonical()
    forged["checksum"] = "0" * 64
    with pytest.raises(ValueError, match="checksum mismatch"):
        parse_save_document(forged)

    registry = MigrationRegistry()
    registry.register(MigrationStep("one-to-two", 1, 2, lambda value: dict(value)))
    with pytest.raises(ValueError, match="cycle"):
        registry.register(MigrationStep("two-to-one", 2, 1, lambda value: dict(value)))


def _digest_payload(payload: dict[str, object]) -> dict[str, object]:
    result = dict(payload)
    result["evidence_digest"] = canonical_sha256(result)
    return result


def _fake_r11_5() -> bytes:
    payload: dict[str, object] = {
        "schema": "kodepoia.r11_5_local_acceptance",
        "version": 1,
        "source_sha": _ACCEPTED_HEADS["R11.5"],
        "status": "pass",
        "blockers": [],
        "approval": {"license_reviewed": True},
        "capability": {
            "status": "pass",
            "capabilities": {"network_required": False},
        },
        "synthesis": {
            "status": "pass",
            "process": {
                "timed_out": False,
                "cancelled": False,
                "text_passed_via_argv": False,
                "ephemeral_input_deleted": True,
            },
            "qa": {"state": "PASS", "blockers": []},
        },
        "privacy": {
            "audio_retained": False,
            "network_download_performed_by_collector": False,
            "private_recording_used": False,
            "voice_clone_used": False,
        },
    }
    return json.dumps(
        _digest_payload(payload), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _fake_r11_9() -> bytes:
    payload: dict[str, object] = {
        "schema": "kodepoia.r11_9_local_acceptance",
        "version": 1,
        "source_sha": _ACCEPTED_HEADS["R11.9"],
        "status": "pass",
        "blockers": [],
        "runtime": {"godot_compatible_47": True, "godot_version": "4.7.2.test"},
        "fixture": {"kind": "repository_synthetic"},
        "capture": {
            "status": "pass",
            "reported_frames": 90,
            "expected_frames": 90,
            "av_sync_error_seconds": 0.0,
            "av_sync_limit_seconds": 0.1,
        },
    }
    return json.dumps(
        _digest_payload(payload), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _fake_report() -> tuple[R11IntegratedReport, dict[str, bytes]]:
    source_sha = "f" * 40
    repository: dict[str, bytes] = {}
    heads = dict(_ACCEPTED_HEADS)
    heads["R11.14"] = source_sha
    for index in range(1, 15):
        subdivision = f"R11.{index}"
        path = f"docs/roadmap/R11_{index}_ACCEPTANCE.md"
        repository[path] = (
            f"# {subdivision} acceptance\naccepted implementation head `{heads[subdivision]}`\n"
        ).encode("utf-8")
    repository["docs/continuity/KODEPOIA_CONTINUITY.md"] = (
        "# continuity\n" + "\n".join(f"- {key} `{value}`" for key, value in heads.items())
    ).encode("utf-8")
    repository["docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json"] = _fake_r11_5()
    repository["docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json"] = _fake_r11_9()
    for phase in ("R7", "R8", "R9", "R10"):
        repository[f"docs/roadmap/{phase}_INTEGRATED_ACCEPTANCE.json"] = json.dumps(
            {
                "schema_version": 1,
                "source_sha": "1" * 40,
                "status": "pass",
                "blockers": [],
                "evidence_sha256": (phase.lower().replace("r", "a") * 64)[:64],
            },
            sort_keys=True,
        ).encode("utf-8")
    report = build_repository_report(
        source_sha=source_sha,
        generated_at="2026-08-24T20:00:00Z",
        read_bytes=repository.__getitem__,
    )
    return report, repository


def test_r11_14_integrated_evidence_detects_acceptance_and_continuity_substitution() -> None:
    report, repository = _fake_report()
    validate_repository_evidence(report, repository.__getitem__)

    tampered = dict(repository)
    tampered["docs/roadmap/R11_8_ACCEPTANCE.md"] += b"tamper"
    with pytest.raises(ValueError, match="acceptance identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    tampered = dict(repository)
    tampered["docs/continuity/KODEPOIA_CONTINUITY.md"] += b"tamper"
    with pytest.raises(ValueError, match="continuity evidence identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)


def test_r11_14_prior_phase_failure_cannot_be_rebound_as_pass() -> None:
    report, repository = _fake_report()
    tampered = dict(repository)
    prior_path = "docs/roadmap/R10_INTEGRATED_ACCEPTANCE.json"
    document = json.loads(tampered[prior_path])
    document["status"] = "fail"
    document["blockers"] = ["synthetic"]
    tampered[prior_path] = json.dumps(document, sort_keys=True).encode("utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)


def test_r11_14_timestamp_is_not_part_of_semantic_digest_and_schema_is_strict() -> None:
    report, _ = _fake_report()
    payload = report.to_dict()
    Draft202012Validator(
        json.loads(
            (ROOT / "schemas/r11-integrated-acceptance-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
    ).validate(payload)

    changed = dict(payload)
    changed["generated_at"] = "2099-01-01T00:00:00Z"
    roundtrip = R11IntegratedReport.from_dict(changed)
    assert roundtrip.evidence_sha256 == report.evidence_sha256

    forged = dict(payload)
    forged["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="semantic digest mismatch"):
        R11IntegratedReport.from_dict(forged)


def test_r11_14_accepted_local_and_prior_semantic_digests_are_frozen() -> None:
    for subdivision, expected in _ACCEPTED_LOCAL_DIGESTS.items():
        index = subdivision.split(".")[1]
        document = json.loads(
            (ROOT / f"docs/roadmap/R11_{index}_LOCAL_ACCEPTANCE.json").read_text(
                encoding="utf-8"
            )
        )
        assert document["status"] == "pass"
        assert document["blockers"] == []
        assert document["evidence_digest"] == expected

    for phase, expected in _ACCEPTED_PRIOR_DIGESTS.items():
        document = json.loads(
            (ROOT / f"docs/roadmap/{phase}_INTEGRATED_ACCEPTANCE.json").read_text(
                encoding="utf-8"
            )
        )
        assert document["status"] == "pass"
        assert document["blockers"] == []
        assert document["evidence_sha256"] == expected
