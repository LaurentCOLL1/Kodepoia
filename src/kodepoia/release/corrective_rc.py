from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from kodepoia.update.repository_bootstrap import build_target_binding
from kodepoia.update.trust import UpdateTargetSpec

PREVIOUS_PUBLIC_VERSION = "1.1.0-rc1"
CORRECTIVE_PUBLIC_VERSION = "1.1.0-rc2"
PREVIOUS_INSTALLER_SHA256 = "3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0"
PREVIOUS_RELEASE_SOURCE_SHA = "c64bac012ef3afa332526a539901b11428fd966f"
REQUIRED_TUF_ROLE_VERSIONS = {"targets": 2, "snapshot": 2, "timestamp": 2}
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class CorrectiveRcReleaseError(ValueError):
    """Raised when the R19.5 corrective release handoff is not exact-source safe."""


@dataclass(frozen=True, slots=True)
class CorrectiveRcReleaseHandoff:
    source_sha: str
    previous_public_version: str
    public_version: str
    tag: str
    channel: str
    prerelease: bool
    installer_path: str
    installer_size: int
    installer_sha256: str
    target_path: str
    target_custom: dict[str, object]
    production_signed: bool
    publication_triggered: bool
    tuf_role_versions: dict[str, int]
    manual_boundary: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _require_source_sha(value: str) -> str:
    normalized = value.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(normalized):
        raise CorrectiveRcReleaseError(
            "source SHA must be an exact 40-character lowercase hexadecimal Git commit"
        )
    return normalized


def build_corrective_rc_handoff(
    installer: str | Path,
    *,
    source_sha: str,
    production_signed: bool = False,
    release_notes_summary: str = "Corrective v1.1 Windows installed-experience update.",
    provenance_status: str = "exact-source-r18-provenance-required-before-publication",
) -> CorrectiveRcReleaseHandoff:
    """Replay the immutable R19.5 rc2 release handoff independently of later releases.

    R19.5 is historical evidence for v1.1.0-rc2.  The repository's canonical
    release identity is allowed to advance after that release, so this replay
    must remain bound to the frozen rc2 constants instead of CURRENT_RELEASE.
    """
    source = _require_source_sha(source_sha)
    path = Path(installer)
    if not path.is_file():
        raise CorrectiveRcReleaseError("corrective RC installer is missing")

    payload = path.read_bytes()
    if not payload:
        raise CorrectiveRcReleaseError("corrective RC installer is empty")
    digest = hashlib.sha256(payload).hexdigest()
    target = UpdateTargetSpec(
        channel="beta",
        platform="windows-x86_64",
        public_version=CORRECTIVE_PUBLIC_VERSION,
        source_sha=source,
        filename="KodepoiaSetup.exe",
    )
    signing_status = (
        "production-authenticode-valid"
        if production_signed
        else "unsigned; production trust is not claimed"
    )
    binding = build_target_binding(
        target,
        payload,
        release_notes_summary=release_notes_summary,
        signing_status=signing_status,
        provenance_status=provenance_status,
    )
    return CorrectiveRcReleaseHandoff(
        source_sha=source,
        previous_public_version=PREVIOUS_PUBLIC_VERSION,
        public_version=CORRECTIVE_PUBLIC_VERSION,
        tag=f"v{CORRECTIVE_PUBLIC_VERSION}",
        channel="beta",
        prerelease=True,
        installer_path=str(path),
        installer_size=len(payload),
        installer_sha256=digest,
        target_path=binding.target_path,
        target_custom=dict(binding.custom),
        production_signed=production_signed,
        publication_triggered=False,
        tuf_role_versions=dict(REQUIRED_TUF_ROLE_VERSIONS),
        manual_boundary={
            "required": True,
            "reason": "production TUF metadata must be re-signed before beta authorization",
            "private_keys_must_not_enter_repository": True,
            "roles_requiring_signature": ["targets", "snapshot", "timestamp"],
            "public_release_requires_explicit_effect": True,
            "authenticode_is_optional_but_truthful": True,
        },
    )


__all__ = [
    "CORRECTIVE_PUBLIC_VERSION",
    "PREVIOUS_INSTALLER_SHA256",
    "PREVIOUS_PUBLIC_VERSION",
    "PREVIOUS_RELEASE_SOURCE_SHA",
    "REQUIRED_TUF_ROLE_VERSIONS",
    "CorrectiveRcReleaseError",
    "CorrectiveRcReleaseHandoff",
    "build_corrective_rc_handoff",
]