from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from kodepoia.release.identity import CURRENT_RELEASE, ReleaseIdentity

MANIFEST_VERSION = "1.12.0"
PACKAGE_IDENTIFIER = "LaurentCOLL1.Kodepoia"
PUBLISHER = "LaurentCOLL1"
DEFAULT_LOCALE = "fr-FR"
SECONDARY_LOCALE = "en-US"
INSTALLER_NAME = "KodepoiaSetup.exe"
PREVIEW_HOST = "preview.invalid"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class WinGetManifestError(ValueError):
    """Raised when WinGet readiness evidence is inconsistent or unsafe."""


@dataclass(frozen=True)
class WinGetInstallerEvidence:
    source_sha: str
    installer_sha256: str
    installer_url: str | None = None
    public_release_verified: bool = False
    immutable_release_verified: bool = False
    production_signed: bool = False

    def __post_init__(self) -> None:
        source_sha = self.source_sha.strip().lower()
        installer_sha256 = self.installer_sha256.strip().lower()
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise WinGetManifestError("source_sha must be an exact 40-character Git SHA")
        if not _SHA256_RE.fullmatch(installer_sha256):
            raise WinGetManifestError("installer_sha256 must be an exact SHA-256 hex digest")
        object.__setattr__(self, "source_sha", source_sha)
        object.__setattr__(self, "installer_sha256", installer_sha256)

        if self.immutable_release_verified and not self.public_release_verified:
            raise WinGetManifestError("immutable release verification requires a verified public release")
        if self.installer_url and not self.public_release_verified:
            raise WinGetManifestError("an installer URL cannot enter manifests before public release verification")

    @property
    def publication_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.public_release_verified:
            blockers.append("public_release_not_verified")
        if not self.immutable_release_verified:
            blockers.append("immutable_release_not_verified")
        if not self.production_signed:
            blockers.append("production_signing_not_verified")
        if self.public_release_verified and self.installer_url is None:
            blockers.append("public_installer_url_missing")
        return tuple(blockers)


@dataclass(frozen=True)
class WinGetManifestBundle:
    files: dict[str, str]
    readiness: dict[str, Any]

    @property
    def digest(self) -> str:
        payload = b"".join(
            name.encode("utf-8") + b"\0" + self.files[name].encode("utf-8")
            for name in sorted(self.files)
        )
        return hashlib.sha256(payload).hexdigest()

    def write(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in self.files.items():
            (output_dir / name).write_text(content, encoding="utf-8", newline="\n")


def _preview_url(identity: ReleaseIdentity) -> str:
    return (
        f"https://{PREVIEW_HOST}/{PACKAGE_IDENTIFIER}/{identity.public_version}/"
        f"{INSTALLER_NAME}"
    )


def _expected_public_url(identity: ReleaseIdentity) -> str:
    return (
        "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
        f"v{identity.public_version}/{INSTALLER_NAME}"
    )


def _validate_public_url(url: str, identity: ReleaseIdentity) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise WinGetManifestError("public installer URL must be a clean HTTPS URL")
    if url != _expected_public_url(identity):
        raise WinGetManifestError("public installer URL must match the immutable version-specific release asset")
    return url


def _yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )


def _manifest_names(identity: ReleaseIdentity) -> dict[str, str]:
    stem = PACKAGE_IDENTIFIER
    return {
        "version": f"{stem}.yaml",
        "installer": f"{stem}.installer.yaml",
        "default_locale": f"{stem}.locale.{DEFAULT_LOCALE}.yaml",
        "secondary_locale": f"{stem}.locale.{SECONDARY_LOCALE}.yaml",
    }


def build_winget_bundle(
    evidence: WinGetInstallerEvidence,
    *,
    identity: ReleaseIdentity = CURRENT_RELEASE,
) -> WinGetManifestBundle:
    if evidence.public_release_verified:
        if evidence.installer_url is None:
            raise WinGetManifestError("verified public release requires installer_url")
        installer_url = _validate_public_url(evidence.installer_url, identity)
        preview = False
    else:
        installer_url = _preview_url(identity)
        preview = True

    names = _manifest_names(identity)
    common = {
        "PackageIdentifier": PACKAGE_IDENTIFIER,
        "PackageVersion": identity.public_version,
    }

    version_manifest = {
        **common,
        "DefaultLocale": DEFAULT_LOCALE,
        "ManifestType": "version",
        "ManifestVersion": MANIFEST_VERSION,
    }
    installer_manifest = {
        **common,
        "InstallerType": "inno",
        "Scope": "user",
        "UpgradeBehavior": "install",
        "InstallerSwitches": {
            "Silent": "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART",
            "SilentWithProgress": "/SILENT /SUPPRESSMSGBOXES /NORESTART",
        },
        "Installers": [
            {
                "Architecture": "x64",
                "InstallerUrl": installer_url,
                "InstallerSha256": evidence.installer_sha256.upper(),
            }
        ],
        "ManifestType": "installer",
        "ManifestVersion": MANIFEST_VERSION,
    }
    default_locale_manifest = {
        **common,
        "PackageLocale": DEFAULT_LOCALE,
        "Publisher": PUBLISHER,
        "PublisherUrl": "https://github.com/LaurentCOLL1",
        "PackageName": identity.product,
        "PackageUrl": "https://github.com/LaurentCOLL1/Kodepoia",
        "License": "Proprietary",
        "ShortDescription": "Environnement local de conception et de développement assisté par IA.",
        "ManifestType": "defaultLocale",
        "ManifestVersion": MANIFEST_VERSION,
    }
    secondary_locale_manifest = {
        **common,
        "PackageLocale": SECONDARY_LOCALE,
        "Publisher": PUBLISHER,
        "PackageName": identity.product,
        "ShortDescription": "Local-first AI-assisted design and development environment.",
        "ManifestType": "locale",
        "ManifestVersion": MANIFEST_VERSION,
    }

    files = {
        names["version"]: _yaml(version_manifest),
        names["installer"]: _yaml(installer_manifest),
        names["default_locale"]: _yaml(default_locale_manifest),
        names["secondary_locale"]: _yaml(secondary_locale_manifest),
    }
    blockers = list(evidence.publication_blockers)
    publishable = not preview and not blockers
    readiness: dict[str, Any] = {
        "schema_version": 1,
        "manifest_version": MANIFEST_VERSION,
        "package_identifier": PACKAGE_IDENTIFIER,
        "package_version": identity.public_version,
        "source_sha": evidence.source_sha,
        "installer_sha256": evidence.installer_sha256,
        "installer_url": installer_url,
        "preview": preview,
        "publishable": publishable,
        "publication_blockers": blockers,
        "public_release_verified": evidence.public_release_verified,
        "immutable_release_verified": evidence.immutable_release_verified,
        "production_signed": evidence.production_signed,
        "public_submission_performed": False,
        "public_pr_url": None,
        "manifest_files": sorted(files),
    }
    bundle = WinGetManifestBundle(files=files, readiness=readiness)
    readiness["manifest_bundle_sha256"] = bundle.digest
    readiness["manifest_file_sha256"] = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in sorted(files.items())
    }
    validate_winget_bundle(bundle, evidence=evidence, identity=identity)
    return bundle


def validate_winget_bundle(
    bundle: WinGetManifestBundle,
    *,
    evidence: WinGetInstallerEvidence,
    identity: ReleaseIdentity = CURRENT_RELEASE,
) -> None:
    names = _manifest_names(identity)
    if set(bundle.files) != set(names.values()):
        raise WinGetManifestError("WinGet bundle must contain exactly four governed manifest files")

    parsed = {name: yaml.safe_load(text) for name, text in bundle.files.items()}
    if any(not isinstance(value, dict) for value in parsed.values()):
        raise WinGetManifestError("every WinGet manifest must decode to an object")

    manifest_types = {value.get("ManifestType") for value in parsed.values()}
    if manifest_types != {"version", "installer", "defaultLocale", "locale"}:
        raise WinGetManifestError("multi-file manifest types are incomplete or duplicated")

    for payload in parsed.values():
        if payload.get("PackageIdentifier") != PACKAGE_IDENTIFIER:
            raise WinGetManifestError("package identifier mismatch")
        if payload.get("PackageVersion") != identity.public_version:
            raise WinGetManifestError("package version mismatch")
        if payload.get("ManifestVersion") != MANIFEST_VERSION:
            raise WinGetManifestError("manifest schema version mismatch")

    installer = parsed[names["installer"]]
    if installer.get("InstallerType") != "inno":
        raise WinGetManifestError("installer type must remain Inno Setup")
    if installer.get("Scope") != "user" or installer.get("UpgradeBehavior") != "install":
        raise WinGetManifestError("installer scope/upgrade behavior mismatch")
    installers = installer.get("Installers")
    if not isinstance(installers, list) or len(installers) != 1:
        raise WinGetManifestError("exactly one governed x64 installer is required")
    item = installers[0]
    if not isinstance(item, dict) or item.get("Architecture") != "x64":
        raise WinGetManifestError("installer architecture must be x64")
    if str(item.get("InstallerSha256", "")).lower() != evidence.installer_sha256:
        raise WinGetManifestError("installer SHA-256 mismatch")

    url = str(item.get("InstallerUrl", ""))
    if evidence.public_release_verified:
        _validate_public_url(url, identity)
    elif urlparse(url).hostname != PREVIEW_HOST:
        raise WinGetManifestError("unpublished manifests must use the reserved preview host")

    if bundle.readiness.get("public_submission_performed") is not False:
        raise WinGetManifestError("manifest generation must never claim or perform public submission")
    if bundle.readiness.get("publishable") and evidence.publication_blockers:
        raise WinGetManifestError("publication blockers cannot be bypassed")


def validate_with_winget(manifest_dir: Path) -> dict[str, Any]:
    executable = shutil.which("winget")
    if executable is None:
        return {
            "status": "UNAVAILABLE",
            "executable": None,
            "returncode": None,
            "stdout": "",
            "stderr": "winget executable is not available on this runner",
        }
    process = subprocess.run(
        [executable, "validate", "--manifest", str(manifest_dir), "--disable-interactivity"],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "status": "PASS" if process.returncode == 0 else "FAIL",
        "executable": executable,
        "returncode": process.returncode,
        "stdout": process.stdout[-12000:],
        "stderr": process.stderr[-12000:],
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate governed WinGet readiness manifests")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--readiness-json", type=Path)
    parser.add_argument("--installer-url")
    parser.add_argument("--public-release-verified", action="store_true")
    parser.add_argument("--immutable-release-verified", action="store_true")
    parser.add_argument("--production-signed", action="store_true")
    args = parser.parse_args()

    if not args.installer.is_file():
        parser.error(f"installer does not exist: {args.installer}")
    evidence = WinGetInstallerEvidence(
        source_sha=args.source_sha,
        installer_sha256=_sha256_file(args.installer),
        installer_url=args.installer_url,
        public_release_verified=args.public_release_verified,
        immutable_release_verified=args.immutable_release_verified,
        production_signed=args.production_signed,
    )
    bundle = build_winget_bundle(evidence)
    bundle.write(args.output_dir)
    readiness = dict(bundle.readiness)
    readiness["winget_validation"] = validate_with_winget(args.output_dir)
    if readiness["winget_validation"]["status"] == "FAIL":
        print(json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    output = args.readiness_json or args.output_dir.parent / "winget-readiness.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(readiness, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
