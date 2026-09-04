from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import kodepoia
from kodepoia.release import CURRENT_RELEASE, ReleaseIdentity

ROOT = Path(__file__).resolve().parents[1]


def _release(
    *,
    channel: str,
    stage: str,
    serial: int,
    major: int = 1,
    minor: int = 1,
    patch: int = 0,
) -> ReleaseIdentity:
    build_type = {
        "stable": "release",
        "beta": "prerelease",
        "nightly": "development",
    }[channel]
    return ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        package="kodepoia",
        channel=channel,
        build_type=build_type,
        source_binding="exact-head",
        major=major,
        minor=minor,
        patch=patch,
        stage=stage,
        serial=serial,
    )


def test_current_release_identity_is_canonical_beta_rc1() -> None:
    assert CURRENT_RELEASE.package == "kodepoia"
    assert CURRENT_RELEASE.channel == "beta"
    assert CURRENT_RELEASE.build_type == "prerelease"
    assert CURRENT_RELEASE.source_binding == "exact-head"
    assert CURRENT_RELEASE.pep440_version == "1.1.0rc1"
    assert CURRENT_RELEASE.public_version == "1.1.0-rc1"
    assert CURRENT_RELEASE.installer_version == "1.1.0-rc1"
    assert kodepoia.__version__ == CURRENT_RELEASE.pep440_version

    identity_path = ROOT / "src/kodepoia/release/release_identity.json"
    payload = json.loads(identity_path.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": 1,
        "product": "Kodepoia",
        "package": "kodepoia",
        "channel": "beta",
        "build_type": "prerelease",
        "source_binding": "exact-head",
        "version": {"major": 1, "minor": 1, "patch": 0, "stage": "rc", "serial": 1},
    }
    assert not (ROOT / "src/kodepoia/release_identity.json").exists()

    schema = json.loads((ROOT / "schemas/release_identity.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
    bound = CURRENT_RELEASE.bind_source("A" * 40).to_dict()
    Draft202012Validator(schema).validate(bound)
    assert bound["source_sha"] == "a" * 40


def test_channel_stage_build_type_and_source_contract_is_strict() -> None:
    with pytest.raises(ValueError, match="incompatible"):
        _release(channel="stable", stage="rc", serial=1)
    with pytest.raises(ValueError, match="incompatible"):
        _release(channel="nightly", stage="final", serial=0)
    with pytest.raises(ValueError, match="serial 0"):
        _release(channel="stable", stage="final", serial=1)
    with pytest.raises(ValueError, match="serial >= 1"):
        _release(channel="beta", stage="rc", serial=0)

    beta = _release(channel="beta", stage="rc", serial=1)
    with pytest.raises(ValueError, match="requires build type"):
        ReleaseIdentity(
            **{**beta.__dict__, "build_type": "release"},
        )
    with pytest.raises(ValueError, match="source SHA"):
        beta.bind_source("not-a-sha")


def test_pep440_monotonicity_across_channels() -> None:
    ordered = [
        _release(channel="nightly", stage="dev", serial=1),
        _release(channel="nightly", stage="dev", serial=2),
        _release(channel="beta", stage="a", serial=1),
        _release(channel="beta", stage="b", serial=1),
        _release(channel="beta", stage="rc", serial=1),
        _release(channel="stable", stage="final", serial=0),
    ]
    assert [item.pep440_version for item in ordered] == [
        "1.1.0.dev1",
        "1.1.0.dev2",
        "1.1.0a1",
        "1.1.0b1",
        "1.1.0rc1",
        "1.1.0",
    ]
    assert all(new.is_newer_than(old) for old, new in zip(ordered[:-1], ordered[1:], strict=True))


def test_channel_transition_rules_block_same_release_regressions() -> None:
    nightly = _release(channel="nightly", stage="dev", serial=2)
    beta = _release(channel="beta", stage="rc", serial=1)
    beta2 = _release(channel="beta", stage="rc", serial=2)
    stable = _release(channel="stable", stage="final", serial=0)
    next_nightly = _release(channel="nightly", stage="dev", serial=1, minor=2)

    assert nightly.can_transition_to(beta)
    assert beta.can_transition_to(beta2)
    assert beta.can_transition_to(stable)
    assert not stable.can_transition_to(beta)
    assert stable.can_transition_to(next_nightly)


def test_repository_surfaces_match_canonical_identity() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == CURRENT_RELEASE.pep440_version

    iss = (ROOT / "packaging/windows/Kodepoia.iss").read_text(encoding="utf-8")
    assert '#define AppVersion "1.1.0-rc1"' not in iss
    assert "#error AppVersion must be supplied from the canonical Kodepoia release identity" in iss
    assert "AppVersion={#AppVersion}" in iss

    build_script = (ROOT / "scripts/build_windows_installer.ps1").read_text(encoding="utf-8")
    assert '[string]$SourceSha = ""' in build_script
    assert "kodepoia.release.identity --source-sha" in build_script
    assert "does not match canonical release identity" in build_script
    assert "pyproject.toml version" in build_script
    assert "source_sha = [string]$ReleaseIdentity.source_sha" in build_script
    assert "build_type = [string]$ReleaseIdentity.build_type" in build_script
    assert 'Join-Path $Root "src\\kodepoia\\release\\release_identity.json"' in build_script
    assert "Canonical release identity data file is missing" in build_script
    assert (
        "--include-data-files=$ReleaseIdentityData=kodepoia/release/release_identity.json"
        in build_script
    )

    ui = (ROOT / "src/kodepoia/kodestudio/app_v11.py").read_text(encoding="utf-8")
    assert 'setProperty("kodepoiaReleaseVersion", CURRENT_RELEASE.display_version)' in ui
    assert 'setProperty("kodepoiaReleaseChannel", CURRENT_RELEASE.channel)' in ui


def test_cli_and_compatibility_surface_match_canonical_identity() -> None:
    from kodepoia.release_identity import CURRENT_RELEASE as COMPAT_RELEASE

    assert COMPAT_RELEASE is CURRENT_RELEASE
    result = subprocess.run(
        [sys.executable, "-m", "kodepoia.cli", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "kodepoia 1.1.0-rc1 (beta)"
