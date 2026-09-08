from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.release.corrective_rc import (
    CORRECTIVE_PUBLIC_VERSION,
    PREVIOUS_INSTALLER_SHA256,
    PREVIOUS_PUBLIC_VERSION,
    PREVIOUS_RELEASE_SOURCE_SHA,
    REQUIRED_TUF_ROLE_VERSIONS,
    CorrectiveRcReleaseError,
    build_corrective_rc_handoff,
)
from kodepoia.release.identity import CURRENT_RELEASE, ReleaseIdentity

SOURCE_SHA = "a" * 40


def installer(tmp_path: Path, payload: bytes = b"synthetic-r19.5-installer") -> Path:
    path = tmp_path / "KodepoiaSetup.exe"
    path.write_bytes(payload)
    return path


def test_canonical_identity_is_authorized_corrective_rc2() -> None:
    assert CURRENT_RELEASE.public_version == CORRECTIVE_PUBLIC_VERSION == "1.1.0-rc2"
    assert CURRENT_RELEASE.pep440_version == "1.1.0rc2"
    assert CURRENT_RELEASE.channel == "beta"
    assert CURRENT_RELEASE.build_type == "prerelease"
    assert CURRENT_RELEASE.source_binding == "exact-head"


def test_rc1_to_rc2_is_strict_forward_transition() -> None:
    rc1 = ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        package="kodepoia",
        channel="beta",
        build_type="prerelease",
        source_binding="exact-head",
        major=1,
        minor=1,
        patch=0,
        stage="rc",
        serial=1,
    )
    assert CURRENT_RELEASE.is_newer_than(rc1)
    assert rc1.can_transition_to(CURRENT_RELEASE)
    assert not CURRENT_RELEASE.can_transition_to(rc1)


def test_handoff_binds_exact_installer_source_and_tuf_path(tmp_path: Path) -> None:
    path = installer(tmp_path)
    handoff = build_corrective_rc_handoff(path, source_sha=SOURCE_SHA)
    assert handoff.source_sha == SOURCE_SHA
    assert handoff.previous_public_version == PREVIOUS_PUBLIC_VERSION
    assert handoff.public_version == CORRECTIVE_PUBLIC_VERSION
    assert handoff.tag == "v1.1.0-rc2"
    assert handoff.prerelease is True
    assert handoff.production_signed is False
    assert handoff.publication_triggered is False
    assert handoff.installer_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert handoff.installer_size == path.stat().st_size
    assert handoff.target_path == (
        f"channels/beta/windows-x86_64/1.1.0-rc2/{SOURCE_SHA}/KodepoiaSetup.exe"
    )
    assert handoff.target_custom["source_sha"] == SOURCE_SHA
    assert handoff.target_custom["channel"] == "beta"
    assert handoff.target_custom["public_version"] == "1.1.0-rc2"
    assert handoff.target_custom["withdrawn"] is False
    assert handoff.target_custom["payload_url"].endswith(
        "/releases/download/v1.1.0-rc2/KodepoiaSetup.exe"
    )


def test_unsigned_handoff_never_claims_production_authenticode(tmp_path: Path) -> None:
    handoff = build_corrective_rc_handoff(installer(tmp_path), source_sha=SOURCE_SHA)
    assert "unsigned" in str(handoff.target_custom["signing_status"]).lower()
    assert handoff.manual_boundary["authenticode_is_optional_but_truthful"] is True


def test_production_signed_claim_is_explicit_only(tmp_path: Path) -> None:
    handoff = build_corrective_rc_handoff(
        installer(tmp_path),
        source_sha=SOURCE_SHA,
        production_signed=True,
    )
    assert handoff.production_signed is True
    assert handoff.target_custom["signing_status"] == "production-authenticode-valid"


def test_handoff_stops_at_real_tuf_private_key_boundary(tmp_path: Path) -> None:
    handoff = build_corrective_rc_handoff(installer(tmp_path), source_sha=SOURCE_SHA)
    assert handoff.tuf_role_versions == REQUIRED_TUF_ROLE_VERSIONS
    assert handoff.manual_boundary["required"] is True
    assert handoff.manual_boundary["private_keys_must_not_enter_repository"] is True
    assert handoff.manual_boundary["roles_requiring_signature"] == [
        "targets",
        "snapshot",
        "timestamp",
    ]
    assert handoff.manual_boundary["public_release_requires_explicit_effect"] is True


def test_invalid_source_sha_and_missing_or_empty_installer_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CorrectiveRcReleaseError, match="source SHA"):
        build_corrective_rc_handoff(installer(tmp_path), source_sha="not-a-sha")
    with pytest.raises(CorrectiveRcReleaseError, match="missing"):
        build_corrective_rc_handoff(tmp_path / "missing.exe", source_sha=SOURCE_SHA)
    empty = tmp_path / "empty.exe"
    empty.write_bytes(b"")
    with pytest.raises(CorrectiveRcReleaseError, match="empty"):
        build_corrective_rc_handoff(empty, source_sha=SOURCE_SHA)


def test_historical_rc1_release_binding_remains_immutable() -> None:
    assert PREVIOUS_PUBLIC_VERSION == "1.1.0-rc1"
    assert PREVIOUS_RELEASE_SOURCE_SHA == "c64bac012ef3afa332526a539901b11428fd966f"
    assert PREVIOUS_INSTALLER_SHA256 == (
        "3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0"
    )
