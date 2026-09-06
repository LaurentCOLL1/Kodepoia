from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.winget import (
    INSTALLER_NAME,
    MANIFEST_VERSION,
    WinGetInstallerEvidence,
    WinGetManifestError,
    build_winget_bundle,
    validate_with_winget,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exact_checkout() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


def _public_url() -> str:
    return (
        "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
        f"v{CURRENT_RELEASE.public_version}/{INSTALLER_NAME}"
    )


def _negative_controls(source_sha: str, installer_sha256: str) -> dict[str, bool]:
    checks: dict[str, bool] = {}

    try:
        WinGetInstallerEvidence(
            source_sha=source_sha,
            installer_sha256=installer_sha256,
            installer_url=_public_url(),
        )
    except WinGetManifestError:
        checks["unverified_public_url_rejected"] = True
    else:
        checks["unverified_public_url_rejected"] = False

    bad_urls = {
        "http_url_rejected": _public_url().replace("https://", "http://", 1),
        "latest_redirect_rejected": (
            "https://github.com/LaurentCOLL1/Kodepoia/releases/latest/download/KodepoiaSetup.exe"
        ),
        "ci_artifact_url_rejected": (
            "https://api.github.com/repos/LaurentCOLL1/Kodepoia/actions/artifacts/1/zip"
        ),
        "wrong_version_url_rejected": (
            "https://github.com/LaurentCOLL1/Kodepoia/releases/download/v9.9.9/KodepoiaSetup.exe"
        ),
    }
    for name, url in bad_urls.items():
        evidence = WinGetInstallerEvidence(
            source_sha=source_sha,
            installer_sha256=installer_sha256,
            installer_url=url,
            public_release_verified=True,
            immutable_release_verified=True,
            production_signed=True,
        )
        try:
            build_winget_bundle(evidence)
        except WinGetManifestError:
            checks[name] = True
        else:
            checks[name] = False

    unsigned = build_winget_bundle(
        WinGetInstallerEvidence(
            source_sha=source_sha,
            installer_sha256=installer_sha256,
            installer_url=_public_url(),
            public_release_verified=True,
            immutable_release_verified=True,
            production_signed=False,
        )
    )
    checks["unsigned_public_release_not_publishable"] = not unsigned.readiness["publishable"]

    signed = build_winget_bundle(
        WinGetInstallerEvidence(
            source_sha=source_sha,
            installer_sha256=installer_sha256,
            installer_url=_public_url(),
            public_release_verified=True,
            immutable_release_verified=True,
            production_signed=True,
        )
    )
    checks["fully_verified_release_can_be_manifest_publishable"] = bool(
        signed.readiness["publishable"]
    )
    checks["generation_never_submits_public_pr"] = (
        signed.readiness["public_submission_performed"] is False
        and signed.readiness["public_pr_url"] is None
    )
    return checks


def _inno_checks() -> dict[str, bool]:
    content = Path("packaging/windows/Kodepoia.iss").read_text(encoding="utf-8")
    return {
        "inno_user_scope": "PrivilegesRequired=lowest" in content,
        "inno_x64compatible": "ArchitecturesAllowed=x64compatible" in content,
        "inno_64bit_mode": "ArchitecturesInstallIn64BitMode=x64compatible" in content,
        "inno_silent_run_guard": "skipifsilent" in content,
    }


def run_acceptance(
    *,
    source_sha: str,
    installer: Path,
    manifest_dir: Path,
    output: Path,
) -> dict[str, Any]:
    actual_source = _exact_checkout()
    if actual_source != source_sha:
        raise RuntimeError(f"exact-source mismatch: expected {source_sha}, got {actual_source}")
    if not installer.is_file() or installer.stat().st_size <= 0:
        raise RuntimeError("installer fixture/artifact is missing or empty")

    installer_sha256 = _sha256_file(installer)
    preview_evidence = WinGetInstallerEvidence(
        source_sha=source_sha,
        installer_sha256=installer_sha256,
    )
    preview = build_winget_bundle(preview_evidence)
    preview.write(manifest_dir)
    winget_validation = validate_with_winget(
        manifest_dir,
        publishable=bool(preview.readiness["publishable"]),
    )

    checks = {
        "exact_source_bound": actual_source == source_sha,
        "installer_sha256_bound": preview.readiness["installer_sha256"] == installer_sha256,
        "manifest_version_current": preview.readiness["manifest_version"] == MANIFEST_VERSION,
        "multi_file_manifest_count": len(preview.files) == 4,
        "preview_is_non_publishable": preview.readiness["preview"] is True
        and preview.readiness["publishable"] is False,
        "preview_uses_reserved_invalid_host": "preview.invalid" in preview.readiness["installer_url"],
        "public_submission_not_performed": preview.readiness["public_submission_performed"] is False,
        "winget_validate_deferred_until_publishable": (
            winget_validation["status"] == "SKIPPED_NON_PUBLISHABLE_PREVIEW"
            and winget_validation["returncode"] is None
        ),
        **_inno_checks(),
        **_negative_controls(source_sha, installer_sha256),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError(f"R18.9 acceptance failed: {failed}")

    report: dict[str, Any] = {
        "schema_version": 1,
        "r18_subdivision": "R18.9",
        "source_sha": source_sha,
        "release": CURRENT_RELEASE.to_dict(),
        "installer": {
            "filename": installer.name,
            "bytes": installer.stat().st_size,
            "sha256": installer_sha256,
        },
        "manifest": {
            "manifest_version": MANIFEST_VERSION,
            "bundle_sha256": preview.digest,
            "files": preview.readiness["manifest_files"],
            "file_sha256": preview.readiness["manifest_file_sha256"],
            "preview": True,
            "publishable": False,
            "publication_blockers": preview.readiness["publication_blockers"],
        },
        "winget_validation": winget_validation,
        "checks": checks,
        "check_count": len(checks),
        "manual_state": "CONDITIONAL_NOT_TRIGGERED",
        "public_submission_authorized": False,
        "public_submission_performed": False,
        "production_signed": False,
        "public_release_verified": False,
        "immutable_release_verified": False,
        "network_publication_calls": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run R18.9 WinGet readiness acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_acceptance(
        source_sha=args.source_sha,
        installer=args.installer,
        manifest_dir=args.manifest_dir,
        output=args.output,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())