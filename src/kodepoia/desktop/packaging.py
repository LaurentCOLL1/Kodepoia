from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Iterable

from .contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
    canonical_sha256,
)

_SHA256_LEN = 64
_MAX_FILES = 10_000
_MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
_MAX_TOTAL_BYTES = 8 * 1024 * 1024 * 1024


class PackagingError(RuntimeError):
    """Base error for governed desktop package/update contracts."""


class PackageIntegrityError(PackagingError):
    """Artifact bytes do not match the accepted semantic manifest."""


class UpdateRejectedError(PackagingError):
    """An update is incompatible with the explicit update policy."""


class SigningState(StrEnum):
    UNSIGNED = "UNSIGNED"
    TEST_SIGNED = "TEST_SIGNED"
    SIGNED = "SIGNED"
    SIGNING_UNAVAILABLE = "SIGNING_UNAVAILABLE"


class PackageCapabilityState(StrEnum):
    SUPPORTED_DEFINITION = "SUPPORTED_DEFINITION"
    TOOLCHAIN_REQUIRED = "TOOLCHAIN_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class ArtifactRole(StrEnum):
    EXECUTABLE = "executable"
    LIBRARY = "library"
    RESOURCE = "resource"
    METADATA = "metadata"
    OTHER = "other"


class UpdateApplyState(StrEnum):
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(frozen=True, order=True, slots=True)
class DesktopVersion:
    major: int
    minor: int
    patch: int
    revision: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("major", self.major),
            ("minor", self.minor),
            ("patch", self.patch),
            ("revision", self.revision),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 65535:
                raise ValueError(f"{name} must be an integer from 0 to 65535")

    @classmethod
    def parse(cls, value: str) -> DesktopVersion:
        if not isinstance(value, str) or not value:
            raise ValueError("version must be non-empty text")
        parts = value.split(".")
        if len(parts) not in {3, 4} or any(not part.isdigit() for part in parts):
            raise ValueError("version must contain three or four numeric components")
        numbers = [int(part) for part in parts]
        if len(numbers) == 3:
            numbers.append(0)
        return cls(*numbers)

    def canonical(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}.{self.revision}"


@dataclass(frozen=True, slots=True)
class SigningIdentity:
    subject: str
    fingerprint_sha256: str
    production: bool

    def __post_init__(self) -> None:
        subject = self.subject.strip()
        if not subject or len(subject) > 256 or "\x00" in subject:
            raise ValueError("signing subject must be bounded non-empty text")
        lowered = subject.lower()
        forbidden = ("private key", "begin private", ".pfx", ".p12", "password=", "secret=")
        if any(marker in lowered for marker in forbidden):
            raise ValueError("signing identity must never contain private-key or secret material")
        _require_sha256(self.fingerprint_sha256, field="fingerprint_sha256")
        object.__setattr__(self, "subject", subject)

    def canonical(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "fingerprint_sha256": self.fingerprint_sha256,
            "production": self.production,
        }


@dataclass(frozen=True, slots=True)
class ArtifactFile:
    path: str
    size: int
    sha256: str
    role: ArtifactRole = ArtifactRole.OTHER

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _safe_relative_path(self.path))
        if not isinstance(self.size, int) or isinstance(self.size, bool) or not 0 <= self.size <= _MAX_FILE_BYTES:
            raise ValueError("artifact file size is outside the bounded package policy")
        _require_sha256(self.sha256, field="artifact sha256")

    def canonical(self) -> dict[str, object]:
        return {
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
            "role": self.role.value,
        }


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    package_id: str
    version: DesktopVersion
    framework: DesktopFramework
    platform: DesktopOS
    architecture: DesktopArchitecture
    package_kind: DesktopPackageKind
    signing_state: SigningState
    files: tuple[ArtifactFile, ...]
    signing_identity: SigningIdentity | None = None

    def __post_init__(self) -> None:
        _stable_token(self.package_id, field="package_id")
        files = tuple(sorted(self.files, key=lambda item: item.path))
        if not files or len(files) > _MAX_FILES:
            raise ValueError("artifact manifest must contain 1..10000 files")
        paths = [item.path for item in files]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact manifest contains duplicate paths")
        if sum(item.size for item in files) > _MAX_TOTAL_BYTES:
            raise ValueError("artifact manifest exceeds package byte budget")
        _validate_signing_contract(self.signing_state, self.signing_identity)
        object.__setattr__(self, "files", files)

    @property
    def total_bytes(self) -> int:
        return sum(item.size for item in self.files)

    def canonical(self) -> dict[str, object]:
        return {
            "package_id": self.package_id,
            "version": self.version.canonical(),
            "framework": self.framework.value,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "package_kind": self.package_kind.value,
            "signing_state": self.signing_state.value,
            "signing_identity": None if self.signing_identity is None else self.signing_identity.canonical(),
            "files": [item.canonical() for item in self.files],
            "total_bytes": self.total_bytes,
        }

    def digest(self) -> str:
        """Semantic digest; independent of nondeterministic package-container metadata."""
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class PackageDefinition:
    definition_id: str
    package_id: str
    version: DesktopVersion
    framework: DesktopFramework
    platform: DesktopOS
    architecture: DesktopArchitecture
    package_kind: DesktopPackageKind
    signing_state: SigningState
    signing_identity: SigningIdentity | None = None

    def __post_init__(self) -> None:
        _stable_token(self.definition_id, field="definition_id")
        _stable_token(self.package_id, field="package_id")
        _validate_signing_contract(self.signing_state, self.signing_identity)
        capability = package_capability(self.framework, self.platform, self.package_kind)
        if capability is PackageCapabilityState.UNSUPPORTED:
            raise ValueError(
                f"{self.framework.value}/{self.platform.value} does not support "
                f"package kind {self.package_kind.value} in the frozen R12 model"
            )

    def canonical(self) -> dict[str, object]:
        return {
            "definition_id": self.definition_id,
            "package_id": self.package_id,
            "version": self.version.canonical(),
            "framework": self.framework.value,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "package_kind": self.package_kind.value,
            "capability_state": package_capability(
                self.framework, self.platform, self.package_kind
            ).value,
            "signing_state": self.signing_state.value,
            "signing_identity": None if self.signing_identity is None else self.signing_identity.canonical(),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class FrameworkPackageCapability:
    framework: DesktopFramework
    platform: DesktopOS
    kinds: tuple[tuple[DesktopPackageKind, PackageCapabilityState], ...]

    def canonical(self) -> dict[str, object]:
        return {
            "framework": self.framework.value,
            "platform": self.platform.value,
            "kinds": [
                {"kind": kind.value, "state": state.value}
                for kind, state in self.kinds
            ],
        }


@dataclass(frozen=True, slots=True)
class UpdatePolicy:
    policy_id: str
    channel: str
    allow_downgrade: bool = False
    accepted_signing_states: tuple[SigningState, ...] = (SigningState.UNSIGNED,)
    allow_signer_rotation: bool = False

    def __post_init__(self) -> None:
        _stable_token(self.policy_id, field="policy_id")
        _stable_token(self.channel, field="channel")
        states = tuple(sorted(set(self.accepted_signing_states), key=lambda item: item.value))
        if not states:
            raise ValueError("accepted_signing_states cannot be empty")
        if SigningState.SIGNING_UNAVAILABLE in states:
            raise ValueError("SIGNING_UNAVAILABLE cannot be an accepted update artifact state")
        object.__setattr__(self, "accepted_signing_states", states)

    def canonical(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "channel": self.channel,
            "allow_downgrade": self.allow_downgrade,
            "accepted_signing_states": [item.value for item in self.accepted_signing_states],
            "allow_signer_rotation": self.allow_signer_rotation,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class UpdateManifest:
    update_id: str
    channel: str
    source_manifest_digest: str
    target_manifest_digest: str
    package_id: str
    source_version: DesktopVersion
    target_version: DesktopVersion
    framework: DesktopFramework
    platform: DesktopOS
    architecture: DesktopArchitecture
    package_kind: DesktopPackageKind
    signing_state: SigningState
    signer_fingerprint_sha256: str | None

    def __post_init__(self) -> None:
        _stable_token(self.update_id, field="update_id")
        _stable_token(self.channel, field="channel")
        _stable_token(self.package_id, field="package_id")
        _require_sha256(self.source_manifest_digest, field="source_manifest_digest")
        _require_sha256(self.target_manifest_digest, field="target_manifest_digest")
        if self.signer_fingerprint_sha256 is not None:
            _require_sha256(self.signer_fingerprint_sha256, field="signer_fingerprint_sha256")
        if self.signing_state in {SigningState.SIGNED, SigningState.TEST_SIGNED}:
            if self.signer_fingerprint_sha256 is None:
                raise ValueError("signed update manifest requires signer fingerprint")
        elif self.signer_fingerprint_sha256 is not None:
            raise ValueError("unsigned/unavailable update manifest cannot carry a signer fingerprint")

    @classmethod
    def from_manifests(
        cls,
        *,
        update_id: str,
        channel: str,
        source: ArtifactManifest,
        target: ArtifactManifest,
    ) -> UpdateManifest:
        fingerprint = (
            None
            if target.signing_identity is None
            else target.signing_identity.fingerprint_sha256
        )
        return cls(
            update_id=update_id,
            channel=channel,
            source_manifest_digest=source.digest(),
            target_manifest_digest=target.digest(),
            package_id=target.package_id,
            source_version=source.version,
            target_version=target.version,
            framework=target.framework,
            platform=target.platform,
            architecture=target.architecture,
            package_kind=target.package_kind,
            signing_state=target.signing_state,
            signer_fingerprint_sha256=fingerprint,
        )

    def canonical(self) -> dict[str, object]:
        return {
            "update_id": self.update_id,
            "channel": self.channel,
            "source_manifest_digest": self.source_manifest_digest,
            "target_manifest_digest": self.target_manifest_digest,
            "package_id": self.package_id,
            "source_version": self.source_version.canonical(),
            "target_version": self.target_version.canonical(),
            "framework": self.framework.value,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "package_kind": self.package_kind.value,
            "signing_state": self.signing_state.value,
            "signer_fingerprint_sha256": self.signer_fingerprint_sha256,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class UpdateValidationResult:
    accepted: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UpdateAuditEvent:
    sequence: int
    action: str
    detail: str


@dataclass(frozen=True, slots=True)
class UpdateApplyResult:
    state: UpdateApplyState
    previous_manifest_digest: str
    target_manifest_digest: str
    audit: tuple[UpdateAuditEvent, ...]
    error: str | None = None


def package_capabilities(
    framework: DesktopFramework, platform: DesktopOS
) -> FrameworkPackageCapability:
    all_kinds = tuple(DesktopPackageKind)
    supported: set[DesktopPackageKind] = set()
    toolchain: set[DesktopPackageKind] = set()

    if framework in {DesktopFramework.WPF, DesktopFramework.WINUI3}:
        if platform is DesktopOS.WINDOWS:
            supported.add(DesktopPackageKind.ARCHIVE)
            toolchain.add(DesktopPackageKind.MSIX)
    elif framework is DesktopFramework.AVALONIA:
        supported.add(DesktopPackageKind.ARCHIVE)
        if platform is DesktopOS.WINDOWS:
            toolchain.add(DesktopPackageKind.MSIX)
    elif framework is DesktopFramework.QT6:
        supported.add(DesktopPackageKind.ARCHIVE)
        if platform is DesktopOS.WINDOWS:
            toolchain.add(DesktopPackageKind.MSIX)
    elif framework is DesktopFramework.TAURI2:
        supported.add(DesktopPackageKind.ARCHIVE)
        if platform is DesktopOS.WINDOWS:
            toolchain.add(DesktopPackageKind.MSI)

    entries: list[tuple[DesktopPackageKind, PackageCapabilityState]] = []
    for kind in all_kinds:
        if kind is DesktopPackageKind.UNPACKAGED:
            state = PackageCapabilityState.SUPPORTED_DEFINITION
        elif kind in supported:
            state = PackageCapabilityState.SUPPORTED_DEFINITION
        elif kind in toolchain:
            state = PackageCapabilityState.TOOLCHAIN_REQUIRED
        else:
            state = PackageCapabilityState.UNSUPPORTED
        entries.append((kind, state))
    return FrameworkPackageCapability(framework, platform, tuple(entries))


def package_capability(
    framework: DesktopFramework,
    platform: DesktopOS,
    kind: DesktopPackageKind,
) -> PackageCapabilityState:
    for candidate, state in package_capabilities(framework, platform).kinds:
        if candidate is kind:
            return state
    raise AssertionError("unreachable package capability lookup")


def build_artifact_manifest(
    root: Path,
    *,
    package_id: str,
    version: DesktopVersion,
    framework: DesktopFramework,
    platform: DesktopOS,
    architecture: DesktopArchitecture,
    package_kind: DesktopPackageKind,
    signing_state: SigningState,
    signing_identity: SigningIdentity | None = None,
    executable_paths: Iterable[str] = (),
) -> ArtifactManifest:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("artifact root must be an existing directory")
    executable_set = {_safe_relative_path(item) for item in executable_paths}
    files: list[ArtifactFile] = []
    for candidate in sorted(root.rglob("*")):
        if candidate.is_symlink():
            raise ValueError("artifact trees may not contain symbolic links")
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(root).as_posix()
        size = candidate.stat().st_size
        role = ArtifactRole.EXECUTABLE if relative in executable_set else _infer_role(relative)
        files.append(
            ArtifactFile(
                path=relative,
                size=size,
                sha256=_file_sha256(candidate),
                role=role,
            )
        )
    return ArtifactManifest(
        package_id=package_id,
        version=version,
        framework=framework,
        platform=platform,
        architecture=architecture,
        package_kind=package_kind,
        signing_state=signing_state,
        signing_identity=signing_identity,
        files=tuple(files),
    )


def verify_artifact_tree(root: Path, manifest: ArtifactManifest) -> None:
    root = root.resolve()
    if not root.is_dir():
        raise PackageIntegrityError("artifact root is missing")
    actual_paths: list[str] = []
    expected = {item.path: item for item in manifest.files}
    for candidate in sorted(root.rglob("*")):
        if candidate.is_symlink():
            raise PackageIntegrityError("artifact tree contains a symbolic link")
        if candidate.is_file():
            actual_paths.append(candidate.relative_to(root).as_posix())
    if tuple(actual_paths) != tuple(sorted(expected)):
        raise PackageIntegrityError("artifact file set differs from semantic manifest")
    for relative, item in expected.items():
        candidate = root / PurePosixPath(relative)
        if candidate.stat().st_size != item.size:
            raise PackageIntegrityError(f"artifact size mismatch: {relative}")
        if _file_sha256(candidate) != item.sha256:
            raise PackageIntegrityError(f"artifact digest mismatch: {relative}")


def validate_update_candidate(
    *,
    current: ArtifactManifest,
    target: ArtifactManifest,
    update: UpdateManifest,
    policy: UpdatePolicy,
) -> UpdateValidationResult:
    blockers: list[str] = []

    if update.channel != policy.channel:
        blockers.append("channel_mismatch")
    if update.source_manifest_digest != current.digest():
        blockers.append("source_manifest_digest_mismatch")
    if update.target_manifest_digest != target.digest():
        blockers.append("target_manifest_digest_mismatch")
    if update.package_id != current.package_id or target.package_id != current.package_id:
        blockers.append("package_identity_mismatch")
    if update.source_version != current.version:
        blockers.append("source_version_mismatch")
    if update.target_version != target.version:
        blockers.append("target_version_mismatch")
    if target.version < current.version and not policy.allow_downgrade:
        blockers.append("downgrade_forbidden")
    if target.version == current.version:
        blockers.append("same_version_update_forbidden")

    immutable_pairs = (
        ("framework_mismatch", current.framework, target.framework, update.framework),
        ("platform_mismatch", current.platform, target.platform, update.platform),
        ("architecture_mismatch", current.architecture, target.architecture, update.architecture),
        ("package_kind_mismatch", current.package_kind, target.package_kind, update.package_kind),
    )
    for blocker, source_value, target_value, update_value in immutable_pairs:
        if target_value != source_value or update_value != target_value:
            blockers.append(blocker)

    if target.signing_state not in policy.accepted_signing_states:
        blockers.append("signing_state_not_allowed")
    if update.signing_state != target.signing_state:
        blockers.append("signing_state_substitution")

    target_fingerprint = (
        None if target.signing_identity is None else target.signing_identity.fingerprint_sha256
    )
    if update.signer_fingerprint_sha256 != target_fingerprint:
        blockers.append("signer_identity_substitution")

    current_fingerprint = (
        None if current.signing_identity is None else current.signing_identity.fingerprint_sha256
    )
    if (
        current_fingerprint is not None
        and target_fingerprint is not None
        and current_fingerprint != target_fingerprint
        and not policy.allow_signer_rotation
    ):
        blockers.append("signer_rotation_forbidden")

    return UpdateValidationResult(not blockers, tuple(sorted(set(blockers))))


class LocalUpdateEngine:
    """Local-fixture update promotion with digest checks and bounded rollback.

    This engine proves Kodepoia's update state machine only. It does not install an
    OS package, trust a certificate, contact an update server, or claim Store/MSIX
    deployment success.
    """

    def __init__(self, workspace_root: Path) -> None:
        root = workspace_root.resolve()
        if not root.is_dir():
            raise ValueError("workspace_root must be an existing directory")
        self._root = root

    def apply(
        self,
        *,
        current_root: Path,
        candidate_root: Path,
        current_manifest: ArtifactManifest,
        target_manifest: ArtifactManifest,
        update: UpdateManifest,
        policy: UpdatePolicy,
        inject_failure_after_promotion: bool = False,
    ) -> UpdateApplyResult:
        current_root = self._bounded_path(current_root)
        candidate_root = self._bounded_path(candidate_root)
        if current_root == candidate_root:
            raise ValueError("current and candidate roots must differ")

        audit: list[UpdateAuditEvent] = []
        self._audit(audit, "verify_current", current_manifest.digest())
        verify_artifact_tree(current_root, current_manifest)
        self._audit(audit, "verify_candidate", target_manifest.digest())
        verify_artifact_tree(candidate_root, target_manifest)

        validation = validate_update_candidate(
            current=current_manifest,
            target=target_manifest,
            update=update,
            policy=policy,
        )
        if not validation.accepted:
            self._audit(audit, "reject", ",".join(validation.blockers))
            raise UpdateRejectedError(",".join(validation.blockers))

        staging = self._root / ".kodepoia-r12-update-staging"
        backup = self._root / ".kodepoia-r12-update-backup"
        if staging.exists() or backup.exists():
            raise PackagingError("stale update staging/backup path requires explicit recovery")

        shutil.copytree(candidate_root, staging)
        verify_artifact_tree(staging, target_manifest)
        self._audit(audit, "stage_verified", target_manifest.digest())

        os.replace(current_root, backup)
        self._audit(audit, "backup_created", current_manifest.digest())
        promoted = False
        try:
            os.replace(staging, current_root)
            promoted = True
            self._audit(audit, "promoted", target_manifest.digest())
            if inject_failure_after_promotion:
                raise PackagingError("injected post-promotion failure")
            verify_artifact_tree(current_root, target_manifest)
            self._audit(audit, "promotion_verified", target_manifest.digest())
        except Exception as exc:
            if promoted and current_root.exists():
                shutil.rmtree(current_root)
            if staging.exists():
                shutil.rmtree(staging)
            os.replace(backup, current_root)
            verify_artifact_tree(current_root, current_manifest)
            self._audit(audit, "rollback_verified", current_manifest.digest())
            return UpdateApplyResult(
                state=UpdateApplyState.ROLLED_BACK,
                previous_manifest_digest=current_manifest.digest(),
                target_manifest_digest=target_manifest.digest(),
                audit=tuple(audit),
                error=str(exc),
            )

        shutil.rmtree(backup)
        self._audit(audit, "backup_retired", current_manifest.digest())
        return UpdateApplyResult(
            state=UpdateApplyState.APPLIED,
            previous_manifest_digest=current_manifest.digest(),
            target_manifest_digest=target_manifest.digest(),
            audit=tuple(audit),
        )

    def _bounded_path(self, value: Path) -> Path:
        resolved = value.resolve()
        try:
            resolved.relative_to(self._root)
        except ValueError as exc:
            raise ValueError("update path escapes workspace boundary") from exc
        if resolved == self._root:
            raise ValueError("update path cannot be the workspace root")
        return resolved

    @staticmethod
    def _audit(events: list[UpdateAuditEvent], action: str, detail: str) -> None:
        events.append(UpdateAuditEvent(len(events) + 1, action, detail))


def _validate_signing_contract(
    state: SigningState, identity: SigningIdentity | None
) -> None:
    if state is SigningState.SIGNED:
        if identity is None or not identity.production:
            raise ValueError("SIGNED requires a production signing identity")
    elif state is SigningState.TEST_SIGNED:
        if identity is None or identity.production:
            raise ValueError("TEST_SIGNED requires a non-production signing identity")
    elif state in {SigningState.UNSIGNED, SigningState.SIGNING_UNAVAILABLE}:
        if identity is not None:
            raise ValueError(f"{state.value} cannot carry a signing identity")


def _safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValueError("artifact path must be normalized POSIX relative text")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("artifact path must stay within the artifact root")
    normalized = path.as_posix()
    if normalized.startswith("/") or ":" in path.parts[0]:
        raise ValueError("artifact path must be relative")
    return normalized


def _stable_token(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise ValueError(f"{field} must be bounded non-empty text")
    if not all(character.isalnum() or character in "._-" for character in value):
        raise ValueError(f"{field} contains unsupported characters")
    return value


def _require_sha256(value: str, *, field: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != _SHA256_LEN
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field} must be lowercase SHA-256")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _infer_role(relative: str) -> ArtifactRole:
    suffix = PurePosixPath(relative).suffix.lower()
    if suffix in {".dll", ".so", ".dylib"}:
        return ArtifactRole.LIBRARY
    if suffix in {".json", ".xml", ".manifest", ".toml"}:
        return ArtifactRole.METADATA
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".ico", ".qm", ".resw"}:
        return ArtifactRole.RESOURCE
    return ArtifactRole.OTHER
