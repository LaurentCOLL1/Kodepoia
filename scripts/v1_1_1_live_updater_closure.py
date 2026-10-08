from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from kodepoia.release.identity import CURRENT_RELEASE, ReleaseIdentity
from kodepoia.update.bootstrap import load_production_packaged_root
from kodepoia.update.corrective import (
    PolicyUpdateDiscoveryService,
    PolicyVerifiedUpdateDownloader,
    PowerShellAuthenticodeVerifier,
    PowerShellInstallerIdentityVerifier,
)
from kodepoia.update.network import NetworkUpdateTransport

ROOT = Path(__file__).resolve().parents[1]

BASELINE_VERSION = "1.1.0"
BASELINE_SOURCE_SHA = "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
TARGET_VERSION = "1.1.1"
TARGET_SOURCE_SHA = "aa1c80389b10f5ef44737241bf192c04f847e4ec"
TARGET_SIZE = 38_880_869
TARGET_SHA256 = "c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd"
TARGET_PATH = (
    "channels/stable/windows-x86_64/1.1.1/"
    "aa1c80389b10f5ef44737241bf192c04f847e4ec/KodepoiaSetup.exe"
)


def _exact_head(expected: str) -> str:
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip().lower()
    requested = expected.strip().lower()
    if actual != requested:
        raise SystemExit(f"exact-source mismatch: expected {requested}, got {actual}")
    return actual


def baseline_identity() -> ReleaseIdentity:
    return ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        package="kodepoia",
        channel="stable",
        build_type="release",
        source_binding="exact-head",
        major=1,
        minor=1,
        patch=0,
        stage="final",
        serial=0,
    )


def _seed_packaged_root(state_dir: Path) -> object:
    root = load_production_packaged_root()
    trusted = state_dir / "tuf-discovery"
    trusted.mkdir(parents=True, exist_ok=True)
    (trusted / "root.json").write_bytes(root.root_bytes)
    return root


def _trusted_state(state_dir: Path) -> dict[str, object]:
    path = state_dir / "tuf-discovery" / "state.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("trusted discovery state is malformed")
    return payload


def _candidate_dict(candidate) -> dict[str, object]:
    return {
        "path": candidate.target.path,
        "public_version": candidate.target.public_version,
        "source_sha": candidate.target.source_sha,
        "channel": candidate.target.channel,
        "size_bytes": candidate.size_bytes,
        "sha256": candidate.sha256,
        "authenticode_policy": candidate.authenticode_policy,
        "withdrawn": candidate.withdrawn,
    }


def build_live_report(
    source_sha: str,
    *,
    mode: str,
    state_dir: Path,
) -> dict[str, object]:
    _exact_head(source_sha)
    if CURRENT_RELEASE.public_version != TARGET_VERSION:
        raise SystemExit("current release identity drift")
    state_dir.mkdir(parents=True, exist_ok=True)
    root = _seed_packaged_root(state_dir)
    transport = NetworkUpdateTransport()
    installed = baseline_identity() if mode == "baseline" else CURRENT_RELEASE
    discovery = PolicyUpdateDiscoveryService(
        state_dir,
        root_pin=root.pin,
        transport=transport,
        platform="windows-x86_64",
        installed_release=installed,
    )
    result = discovery.check("stable")
    expected_status = "update-available" if mode == "baseline" else "up-to-date"
    if result.status != expected_status:
        raise SystemExit(
            f"live stable discovery status mismatch: expected {expected_status}, got "
            f"{result.status}: {result.detail}"
        )
    candidate = result.candidate
    if candidate is None:
        raise SystemExit("live stable discovery returned no candidate")
    if candidate.target.path != TARGET_PATH:
        raise SystemExit("live stable target path drift")
    if candidate.target.public_version != TARGET_VERSION:
        raise SystemExit("live stable target version drift")
    if candidate.target.source_sha != TARGET_SOURCE_SHA:
        raise SystemExit("live stable target source drift")
    if candidate.size_bytes != TARGET_SIZE:
        raise SystemExit("live stable target size drift")
    if candidate.sha256 != TARGET_SHA256:
        raise SystemExit("live stable target SHA-256 drift")
    if candidate.authenticode_policy != "allow-unsigned":
        raise SystemExit("live stable target Authenticode policy drift")
    if candidate.withdrawn:
        raise SystemExit("live stable target is withdrawn")

    artifact_payload: dict[str, object] | None = None
    if mode == "baseline":
        downloader = PolicyVerifiedUpdateDownloader(
            state_dir / "downloads",
            authenticode=PowerShellAuthenticodeVerifier(),
            identity=PowerShellInstallerIdentityVerifier(),
        )
        artifact = downloader.stage(candidate, transport)
        if artifact.public_version != TARGET_VERSION:
            raise SystemExit("staged live installer version drift")
        if artifact.source_sha != TARGET_SOURCE_SHA:
            raise SystemExit("staged live installer source drift")
        if artifact.size_bytes != TARGET_SIZE:
            raise SystemExit("staged live installer size drift")
        if artifact.sha256 != TARGET_SHA256:
            raise SystemExit("staged live installer SHA-256 drift")
        data = artifact.path.read_bytes()
        if hashlib.sha256(data).hexdigest() != TARGET_SHA256:
            raise SystemExit("staged live installer bytes drift after verification")
        artifact_payload = artifact.to_dict()

    trusted = _trusted_state(state_dir)
    expected_tuf = {"root_version": 2, "targets_version": 10, "snapshot_version": 12, "timestamp_version": 12}
    for role, expected_version in expected_tuf.items():
        if int(trusted.get(role, -1)) != expected_version:
            raise SystemExit(f"live TUF {role} drift: expected {expected_version}, got {trusted.get(role)}")
    report: dict[str, object] = {
        "schema_version": 1,
        "release": "1.1.1",
        "mode": mode,
        "status": "PASS",
        "source_sha": source_sha.lower(),
        "installed_public_version": installed.public_version,
        "discovery_status": result.status,
        "candidate": _candidate_dict(candidate),
        "trusted_state": trusted,
        "staged_artifact": artifact_payload,
        "network_metadata_base": transport.policy.metadata_base_url,
        "network_release_base": transport.policy.release_asset_base_url,
        "public_network_proof": True,
        "production_metadata_mutated": False,
        "public_release_mutated": False,
        "winget_submission": False,
    }
    rendered = json.dumps(report, sort_keys=True, separators=(",", ":"))
    report["evidence_sha256"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Kodepoia 1.1.1 live updater closure evidence.")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--mode", choices=("baseline", "stable"), required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_live_report(
        args.source_sha,
        mode=args.mode,
        state_dir=args.state_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
