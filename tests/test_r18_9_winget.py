from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.winget import (
    DEFAULT_LOCALE,
    INSTALLER_NAME,
    MANIFEST_VERSION,
    PACKAGE_IDENTIFIER,
    PREVIEW_HOST,
    WinGetInstallerEvidence,
    WinGetManifestBundle,
    WinGetManifestError,
    build_winget_bundle,
    validate_winget_bundle,
    validate_with_winget,
)

SOURCE_SHA = "1" * 40
INSTALLER_SHA = "2" * 64
PUBLIC_URL = (
    "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
    f"v{CURRENT_RELEASE.public_version}/{INSTALLER_NAME}"
)


def _preview_evidence() -> WinGetInstallerEvidence:
    return WinGetInstallerEvidence(source_sha=SOURCE_SHA, installer_sha256=INSTALLER_SHA)


def _published_evidence(*, signed: bool = True) -> WinGetInstallerEvidence:
    return WinGetInstallerEvidence(
        source_sha=SOURCE_SHA,
        installer_sha256=INSTALLER_SHA,
        installer_url=PUBLIC_URL,
        public_release_verified=True,
        immutable_release_verified=True,
        production_signed=signed,
    )


def _parsed(bundle: WinGetManifestBundle) -> dict[str, dict[str, object]]:
    return {name: yaml.safe_load(text) for name, text in bundle.files.items()}


def test_preview_bundle_is_deterministic_and_non_publishable() -> None:
    evidence = _preview_evidence()
    first = build_winget_bundle(evidence)
    second = build_winget_bundle(evidence)

    assert first.files == second.files
    assert first.digest == second.digest
    assert first.readiness["preview"] is True
    assert first.readiness["publishable"] is False
    assert first.readiness["public_submission_performed"] is False
    assert first.readiness["publication_blockers"] == [
        "public_release_not_verified",
        "immutable_release_not_verified",
        "production_signing_not_verified",
    ]
    assert PREVIEW_HOST in first.readiness["installer_url"]


def test_bundle_is_exact_multi_file_manifest_set() -> None:
    bundle = build_winget_bundle(_preview_evidence())
    manifests = _parsed(bundle)

    assert len(manifests) == 4
    assert {payload["ManifestType"] for payload in manifests.values()} == {
        "version",
        "installer",
        "defaultLocale",
        "locale",
    }
    assert {payload["ManifestVersion"] for payload in manifests.values()} == {MANIFEST_VERSION}
    assert {payload["PackageIdentifier"] for payload in manifests.values()} == {PACKAGE_IDENTIFIER}
    assert {payload["PackageVersion"] for payload in manifests.values()} == {
        CURRENT_RELEASE.public_version
    }


def test_installer_manifest_maps_inno_x64_user_scope_and_silent_switches() -> None:
    bundle = build_winget_bundle(_preview_evidence())
    installer = next(
        payload for payload in _parsed(bundle).values() if payload["ManifestType"] == "installer"
    )

    assert installer["InstallerType"] == "inno"
    assert installer["Scope"] == "user"
    assert installer["UpgradeBehavior"] == "install"
    assert installer["InstallerSwitches"] == {
        "Silent": "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART",
        "SilentWithProgress": "/SILENT /SUPPRESSMSGBOXES /NORESTART",
    }
    item = installer["Installers"][0]
    assert item["Architecture"] == "x64"
    assert item["InstallerSha256"] == INSTALLER_SHA.upper()


def test_default_and_secondary_locales_are_governed() -> None:
    bundle = build_winget_bundle(_preview_evidence())
    parsed = _parsed(bundle)
    version = next(payload for payload in parsed.values() if payload["ManifestType"] == "version")
    locales = {
        payload["PackageLocale"]: payload
        for payload in parsed.values()
        if payload["ManifestType"] in {"defaultLocale", "locale"}
    }

    assert version["DefaultLocale"] == DEFAULT_LOCALE
    assert set(locales) == {"fr-FR", "en-US"}
    assert locales["fr-FR"]["ManifestType"] == "defaultLocale"
    assert locales["en-US"]["ManifestType"] == "locale"


def test_verified_signed_immutable_public_release_is_publishable() -> None:
    evidence = _published_evidence()
    bundle = build_winget_bundle(evidence)

    assert bundle.readiness["preview"] is False
    assert bundle.readiness["publishable"] is True
    assert bundle.readiness["publication_blockers"] == []
    assert bundle.readiness["installer_url"] == PUBLIC_URL
    assert bundle.readiness["public_submission_performed"] is False
    validate_winget_bundle(bundle, evidence=evidence)


def test_verified_public_release_without_production_signing_stays_blocked() -> None:
    bundle = build_winget_bundle(_published_evidence(signed=False))

    assert bundle.readiness["preview"] is False
    assert bundle.readiness["publishable"] is False
    assert bundle.readiness["publication_blockers"] == ["production_signing_not_verified"]


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/LaurentCOLL1/Kodepoia/releases/download/v1.1.0-rc1/KodepoiaSetup.exe",
        "https://api.github.com/repos/LaurentCOLL1/Kodepoia/actions/artifacts/1/zip",
        "https://github.com/LaurentCOLL1/Kodepoia/releases/latest/download/KodepoiaSetup.exe",
        "https://github.com/LaurentCOLL1/Kodepoia/releases/download/v9.9.9/KodepoiaSetup.exe",
        "https://user:secret@github.com/LaurentCOLL1/Kodepoia/releases/download/"
        "v1.1.0-rc1/KodepoiaSetup.exe",
    ],
)
def test_publishable_url_is_strictly_version_specific_and_direct(url: str) -> None:
    evidence = WinGetInstallerEvidence(
        source_sha=SOURCE_SHA,
        installer_sha256=INSTALLER_SHA,
        installer_url=url,
        public_release_verified=True,
        immutable_release_verified=True,
        production_signed=True,
    )
    with pytest.raises(WinGetManifestError):
        build_winget_bundle(evidence)


def test_unverified_url_is_rejected_before_manifest_generation() -> None:
    with pytest.raises(WinGetManifestError, match="before public release verification"):
        WinGetInstallerEvidence(
            source_sha=SOURCE_SHA,
            installer_sha256=INSTALLER_SHA,
            installer_url=PUBLIC_URL,
        )


def test_immutable_release_cannot_be_claimed_without_public_release() -> None:
    with pytest.raises(WinGetManifestError, match="requires a verified public release"):
        WinGetInstallerEvidence(
            source_sha=SOURCE_SHA,
            installer_sha256=INSTALLER_SHA,
            immutable_release_verified=True,
        )


@pytest.mark.parametrize(
    ("source_sha", "installer_sha"),
    [("abc", INSTALLER_SHA), (SOURCE_SHA, "deadbeef"), ("G" * 40, INSTALLER_SHA)],
)
def test_exact_digest_inputs_fail_closed(source_sha: str, installer_sha: str) -> None:
    with pytest.raises(WinGetManifestError):
        WinGetInstallerEvidence(source_sha=source_sha, installer_sha256=installer_sha)


def test_manifest_file_digests_are_bound_to_exact_bytes() -> None:
    bundle = build_winget_bundle(_preview_evidence())
    expected = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in sorted(bundle.files.items())
    }
    assert bundle.readiness["manifest_file_sha256"] == expected
    assert bundle.readiness["manifest_bundle_sha256"] == bundle.digest


def test_write_uses_only_governed_manifest_names(tmp_path: Path) -> None:
    bundle = build_winget_bundle(_preview_evidence())
    bundle.write(tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(bundle.files)
    assert all(path.read_bytes().endswith(b"\n") for path in tmp_path.iterdir())


def test_preview_validation_is_deferred_without_subprocess(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("kodepoia.release.winget.shutil.which", lambda _: "winget")

    def _unexpected_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("winget must not run for non-publishable preview manifests")

    monkeypatch.setattr("kodepoia.release.winget.subprocess.run", _unexpected_run)
    result = validate_with_winget(tmp_path, publishable=False)

    assert result["status"] == "SKIPPED_NON_PUBLISHABLE_PREVIEW"
    assert result["executable"] == "winget"
    assert result["returncode"] is None
    assert ".invalid" in result["reason"]


def test_winget_unavailable_is_truthful(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("kodepoia.release.winget.shutil.which", lambda _: None)
    result = validate_with_winget(tmp_path, publishable=True)

    assert result["status"] == "UNAVAILABLE"
    assert result["returncode"] is None


def test_inno_packaging_contract_matches_winget_mapping() -> None:
    iss = Path("packaging/windows/Kodepoia.iss").read_text(encoding="utf-8")

    assert "PrivilegesRequired=lowest" in iss
    assert "ArchitecturesAllowed=x64compatible" in iss
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in iss
    assert "skipifsilent" in iss