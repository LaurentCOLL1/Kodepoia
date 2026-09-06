from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.release.signing import (
    SigningMode,
    SigningPolicy,
    SubjectEvidence,
    build_signing_evidence,
)
from kodepoia.release.tuf_security import (
    SyntheticTufRepositoryBuilder,
    TufUpdateVerifier,
    TufVerificationError,
)
from kodepoia.update.delivery import (
    AuthenticodeEvidence,
    InstallerIdentityEvidence,
    MemoryStreamingTargetTransport,
    UpdateInstallCoordinator,
    UpdateVerificationFailed,
    VerifiedUpdateDownloader,
)
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryResult
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateClient,
    UpdateTargetSpec,
)

INCIDENT_REPORT_FORMAT = "kodepoia-r18-10-incident-drill"
INCIDENT_REPORT_SCHEMA_VERSION = 1
REFERENCE_TIME = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_THUMBPRINT_RE = re.compile(r"^[0-9A-F]{40}$")


class IncidentDrillError(RuntimeError):
    """Raised when an R18.10 incident/recovery invariant is violated."""


class DrillVerdict(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    RECOVER = "RECOVER"
    NOT_EXECUTED = "NOT_EXECUTED"


@dataclass(frozen=True, slots=True)
class IncidentScenarioResult:
    scenario_id: str
    expected_verdict: str
    actual_verdict: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProviderEffectRecord:
    action: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IncidentDrillReport:
    source_sha: str
    scenarios: tuple[IncidentScenarioResult, ...]
    provider_effects: tuple[ProviderEffectRecord, ...]
    project_data_mutation: bool = False
    manual_intervention: str = "NONE"

    @property
    def critical_bypass_count(self) -> int:
        return sum(1 for item in self.scenarios if not item.passed)

    @property
    def provider_effect_count(self) -> int:
        return sum(
            1
            for item in self.provider_effects
            if item.status != DrillVerdict.NOT_EXECUTED.value
        )

    @property
    def status(self) -> str:
        return (
            "PASS"
            if self.critical_bypass_count == 0 and self.provider_effect_count == 0
            else "FAIL"
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "format": INCIDENT_REPORT_FORMAT,
            "schema_version": INCIDENT_REPORT_SCHEMA_VERSION,
            "source_sha": self.source_sha,
            "status": self.status,
            "critical_bypass_count": self.critical_bypass_count,
            "provider_effect_count": self.provider_effect_count,
            "project_data_mutation": self.project_data_mutation,
            "manual_intervention": self.manual_intervention,
            "scenarios": [item.to_dict() for item in self.scenarios],
            "provider_effects": [item.to_dict() for item in self.provider_effects],
        }
        digest_material = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        payload["report_sha256"] = hashlib.sha256(digest_material).hexdigest()
        return payload


@dataclass(frozen=True, slots=True)
class CompromisedCertificateTrustPolicy:
    blocked_thumbprints: frozenset[str]

    @classmethod
    def from_thumbprints(
        cls, thumbprints: Sequence[str]
    ) -> CompromisedCertificateTrustPolicy:
        normalized: set[str] = set()
        for value in thumbprints:
            thumbprint = value.replace(" ", "").upper()
            if not _THUMBPRINT_RE.fullmatch(thumbprint):
                raise ValueError(
                    "blocked certificate thumbprints must be exact 40-hex values"
                )
            normalized.add(thumbprint)
        if not normalized:
            raise ValueError("at least one blocked certificate thumbprint is required")
        return cls(frozenset(normalized))

    def assert_trusted(self, evidence: Mapping[str, Any]) -> None:
        subjects = evidence.get("subjects")
        if not isinstance(subjects, Sequence) or isinstance(subjects, (str, bytes)):
            raise IncidentDrillError("signing evidence subjects are missing")
        for item in subjects:
            if not isinstance(item, Mapping):
                raise IncidentDrillError("signing evidence subject is malformed")
            thumbprint = (
                str(item.get("signer_thumbprint") or "").replace(" ", "").upper()
            )
            if thumbprint in self.blocked_thumbprints:
                raise IncidentDrillError(
                    "signing certificate is blocked by incident trust policy: "
                    f"{thumbprint}"
                )


@dataclass(frozen=True, slots=True)
class ReleaseIncidentDirective:
    source_sha: str
    public_version: str
    withdrawn: bool = False
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        source = self.source_sha.strip().lower()
        if not _SOURCE_SHA_RE.fullmatch(source):
            raise ValueError("incident directive source_sha must be an exact Git SHA")
        version = self.public_version.strip()
        if not version:
            raise ValueError("incident directive public_version must be non-empty")
        replacement = self.superseded_by.strip() if self.superseded_by else None
        if self.withdrawn and replacement:
            raise ValueError("incident directive cannot be both withdrawn and superseded")
        object.__setattr__(self, "source_sha", source)
        object.__setattr__(self, "public_version", version)
        object.__setattr__(self, "superseded_by", replacement)

    def apply(self, result: UpdateDiscoveryResult) -> UpdateDiscoveryResult:
        candidate = result.candidate
        if candidate is None:
            return result
        if candidate.source_verification_state != "tuf-verified-metadata":
            raise IncidentDrillError(
                "incident directive requires a TUF-verified candidate"
            )
        if candidate.target.source_sha != self.source_sha:
            raise IncidentDrillError(
                "incident directive source SHA does not match candidate"
            )
        if candidate.target.public_version != self.public_version:
            raise IncidentDrillError("incident directive version does not match candidate")
        if self.withdrawn:
            return UpdateDiscoveryResult(
                status="update-withdrawn",
                candidate=candidate,
                detail="trusted incident metadata marks this release withdrawn",
            )
        if self.superseded_by:
            return UpdateDiscoveryResult(
                status="update-superseded",
                candidate=candidate,
                detail=(
                    "trusted incident metadata supersedes this release with "
                    f"{self.superseded_by}"
                ),
            )
        return result


class _SyntheticAuthenticodeVerifier:
    def verify(self, path: Path) -> AuthenticodeEvidence:
        return AuthenticodeEvidence(
            True,
            "valid",
            "synthetic offline Authenticode fixture",
        )


class _SyntheticIdentityVerifier:
    def verify(
        self, path: Path, *, expected_public_version: str
    ) -> InstallerIdentityEvidence:
        return InstallerIdentityEvidence(
            True,
            expected_public_version,
            f"ProductVersion={expected_public_version!r}",
        )


class _NoopLauncher:
    def launch(self, path: Path) -> None:
        raise IncidentDrillError(
            "synthetic incident drills must never launch an installer"
        )


def _candidate(
    source_sha: str,
    data: bytes,
    *,
    public_version: str = "1.1.0-rc1",
    withdrawn: bool = False,
) -> UpdateDiscoveryCandidate:
    target = UpdateTargetSpec(
        channel="beta",
        platform="windows-x86_64",
        public_version=public_version,
        source_sha=source_sha,
    )
    return UpdateDiscoveryCandidate(
        target=target,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        withdrawn=withdrawn,
    )


def _result(
    scenario_id: str,
    *,
    expected: DrillVerdict,
    actual: DrillVerdict,
    detail: str,
) -> IncidentScenarioResult:
    return IncidentScenarioResult(
        scenario_id=scenario_id,
        expected_verdict=expected.value,
        actual_verdict=actual.value,
        passed=expected is actual,
        detail=detail,
    )


def _tuf_block_scenario(
    state_dir: Path,
    *,
    scenario_id: str,
    candidate_factory,
) -> IncidentScenarioResult:
    builder = SyntheticTufRepositoryBuilder()
    trusted = builder.build(
        root_version=2,
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
    )
    verifier = TufUpdateVerifier(state_dir, reference_time=REFERENCE_TIME)
    verifier.verify(trusted, bootstrap_root=trusted.root)
    candidate = candidate_factory(builder)
    try:
        verifier.verify(candidate)
    except TufVerificationError as exc:
        return _result(
            scenario_id,
            expected=DrillVerdict.BLOCK,
            actual=DrillVerdict.BLOCK,
            detail=str(exc),
        )
    return _result(
        scenario_id,
        expected=DrillVerdict.BLOCK,
        actual=DrillVerdict.ALLOW,
        detail="malicious/stale TUF state was unexpectedly accepted",
    )


def run_synthetic_incident_drills(
    *,
    source_sha: str,
    work_dir: str | Path,
) -> IncidentDrillReport:
    source = source_sha.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(source):
        raise ValueError("source_sha must be an exact 40-character lowercase Git SHA")
    root = Path(work_dir)
    root.mkdir(parents=True, exist_ok=True)
    scenarios: list[IncidentScenarioResult] = []

    compromised_thumbprint = "A" * 40
    signing = build_signing_evidence(
        SigningPolicy(
            mode=SigningMode.TEST,
            source_sha=source,
            timestamp_url="https://timestamp.invalid/r18-10",
            certificate_thumbprint=compromised_thumbprint,
        ),
        signtool_version="synthetic-r18.10",
        subjects=(
            SubjectEvidence(
                filename="KodepoiaSetup.exe",
                sha256="1" * 64,
                authenticode_status="Valid",
                signer_subject="CN=Kodepoia R18.10 Synthetic Compromised",
                signer_thumbprint=compromised_thumbprint,
                timestamp_subject="CN=R18.10 Synthetic Timestamp",
                timestamp_verified=True,
                signtool_verified=True,
                pre_sign_sha256="0" * 64,
            ),
        ),
    )
    cert_policy = CompromisedCertificateTrustPolicy.from_thumbprints(
        [compromised_thumbprint]
    )
    try:
        cert_policy.assert_trusted(signing.to_dict())
    except IncidentDrillError as exc:
        scenarios.append(
            _result(
                "CERT-COMPROMISED-01",
                expected=DrillVerdict.BLOCK,
                actual=DrillVerdict.BLOCK,
                detail=str(exc),
            )
        )
    else:
        scenarios.append(
            _result(
                "CERT-COMPROMISED-01",
                expected=DrillVerdict.BLOCK,
                actual=DrillVerdict.ALLOW,
                detail="blocked synthetic certificate was unexpectedly trusted",
            )
        )

    target = UpdateTargetSpec(
        channel="beta",
        platform="windows-x86_64",
        public_version="1.1.0-rc1",
        source_sha=source,
    )
    rotation_builder = SyntheticUpdateRepositoryBuilder(root_threshold=2)
    first = rotation_builder.build(
        target,
        b"r18.10-root-v1",
        root_version=1,
        timestamp_version=1,
        snapshot_version=1,
        targets_version=1,
    )
    rotation_client = UpdateClient(
        root / "root-rotation",
        root_pin=PackagedRootPin.from_root(first.root),
        reference_time=REFERENCE_TIME,
    )
    rotation_client.verify_refresh(
        MemoryUpdateTransport.from_repository(first), target
    )
    rotation_builder.rotate_root_keys()
    second = rotation_builder.build(
        target,
        b"r18.10-root-v2",
        root_version=2,
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
    )
    rotated = rotation_client.verify_refresh(
        MemoryUpdateTransport.from_repository(second), target
    )
    scenarios.append(
        _result(
            "TUF-ROOT-ROTATION-01",
            expected=DrillVerdict.ALLOW,
            actual=(
                DrillVerdict.ALLOW
                if rotated.tuf_state.root_version == 2
                else DrillVerdict.BLOCK
            ),
            detail=(
                "sequential Root rotation accepted under old+new threshold signatures"
                if rotated.tuf_state.root_version == 2
                else "sequential Root rotation did not advance trusted root"
            ),
        )
    )

    scenarios.extend(
        (
            _tuf_block_scenario(
                root / "root-rollback",
                scenario_id="TUF-ROOT-ROLLBACK-01",
                candidate_factory=lambda builder: builder.build(
                    root_version=1,
                    timestamp_version=3,
                    snapshot_version=3,
                    targets_version=3,
                ),
            ),
            _tuf_block_scenario(
                root / "timestamp-rollback",
                scenario_id="TUF-TIMESTAMP-ROLLBACK-01",
                candidate_factory=lambda builder: builder.build(
                    root_version=2,
                    timestamp_version=1,
                    snapshot_version=3,
                    targets_version=3,
                ),
            ),
            _tuf_block_scenario(
                root / "snapshot-rollback",
                scenario_id="TUF-SNAPSHOT-ROLLBACK-01",
                candidate_factory=lambda builder: builder.build(
                    root_version=2,
                    timestamp_version=3,
                    snapshot_version=1,
                    targets_version=3,
                ),
            ),
            _tuf_block_scenario(
                root / "targets-rollback",
                scenario_id="TUF-TARGETS-ROLLBACK-01",
                candidate_factory=lambda builder: builder.build(
                    root_version=2,
                    timestamp_version=3,
                    snapshot_version=3,
                    targets_version=1,
                ),
            ),
            _tuf_block_scenario(
                root / "timestamp-freeze",
                scenario_id="TUF-TIMESTAMP-FREEZE-01",
                candidate_factory=lambda builder: builder.build(
                    root_version=2,
                    timestamp_version=3,
                    snapshot_version=3,
                    targets_version=3,
                    timestamp_expires=datetime(2026, 9, 5, tzinfo=UTC),
                ),
            ),
        )
    )

    good_bytes = b"r18.10-good-installer"
    downloader = VerifiedUpdateDownloader(
        root / "download-cache",
        authenticode=_SyntheticAuthenticodeVerifier(),
        identity=_SyntheticIdentityVerifier(),
    )
    withdrawn_candidate = _candidate(source, good_bytes, withdrawn=True)
    try:
        downloader.stage(
            withdrawn_candidate,
            MemoryStreamingTargetTransport(
                {withdrawn_candidate.target.path: good_bytes}
            ),
        )
    except UpdateVerificationFailed as exc:
        scenarios.append(
            _result(
                "RELEASE-WITHDRAWN-01",
                expected=DrillVerdict.BLOCK,
                actual=DrillVerdict.BLOCK,
                detail=str(exc),
            )
        )
    else:
        scenarios.append(
            _result(
                "RELEASE-WITHDRAWN-01",
                expected=DrillVerdict.BLOCK,
                actual=DrillVerdict.ALLOW,
                detail="withdrawn release was unexpectedly staged",
            )
        )

    base_result = UpdateDiscoveryResult(
        status="update-available",
        candidate=_candidate(source, good_bytes),
        detail="trusted metadata authorizes a newer update",
    )
    superseded = ReleaseIncidentDirective(
        source_sha=source,
        public_version="1.1.0-rc1",
        superseded_by="1.1.0-rc2",
    ).apply(base_result)
    scenarios.append(
        _result(
            "RELEASE-SUPERSEDED-01",
            expected=DrillVerdict.BLOCK,
            actual=(
                DrillVerdict.BLOCK
                if superseded.status == "update-superseded"
                else DrillVerdict.ALLOW
            ),
            detail=superseded.detail,
        )
    )

    expected_candidate = _candidate(source, good_bytes)
    tampered_bytes = b"r18.10-malicious-installer"
    try:
        downloader.stage(
            expected_candidate,
            MemoryStreamingTargetTransport(
                {expected_candidate.target.path: tampered_bytes}
            ),
        )
    except UpdateVerificationFailed as exc:
        scenarios.append(
            _result(
                "ASSET-TAMPER-01",
                expected=DrillVerdict.BLOCK,
                actual=DrillVerdict.BLOCK,
                detail=str(exc),
            )
        )
    else:
        scenarios.append(
            _result(
                "ASSET-TAMPER-01",
                expected=DrillVerdict.BLOCK,
                actual=DrillVerdict.ALLOW,
                detail="wrong release asset was unexpectedly staged",
            )
        )

    recovery_dir = root / "recovery"
    previous_installer = recovery_dir / "KodepoiaSetup.previous.exe"
    previous_installer.parent.mkdir(parents=True, exist_ok=True)
    previous_installer.write_bytes(b"last-known-good")
    project_sentinel = recovery_dir / "project-sentinel.txt"
    project_sentinel.write_text("unchanged\n", encoding="utf-8")
    recovery_downloader = VerifiedUpdateDownloader(
        recovery_dir / "cache",
        authenticode=_SyntheticAuthenticodeVerifier(),
        identity=_SyntheticIdentityVerifier(),
    )
    recovery_candidate = _candidate(source, good_bytes)
    coordinator = UpdateInstallCoordinator(
        recovery_dir / "state",
        downloader=recovery_downloader,
        transport=MemoryStreamingTargetTransport(
            {recovery_candidate.target.path: good_bytes}
        ),
        launcher=_NoopLauncher(),
        current_public_version="1.0.0",
        previous_installer=previous_installer,
    )
    coordinator.stage(recovery_candidate)
    coordinator.record_outcome(
        success=False,
        detail="synthetic compromised release rejected",
    )
    recovery = coordinator.recovery_instructions()
    recovered = (
        recovery.get("available") is True
        and recovery.get("previous_installer") == str(previous_installer)
        and project_sentinel.read_text(encoding="utf-8") == "unchanged\n"
    )
    scenarios.append(
        _result(
            "RECOVERY-LAST-KNOWN-GOOD-01",
            expected=DrillVerdict.RECOVER,
            actual=DrillVerdict.RECOVER if recovered else DrillVerdict.BLOCK,
            detail=(
                "last-known-good installer remains available and project data is unchanged"
                if recovered
                else "last-known-good recovery evidence is incomplete"
            ),
        )
    )

    provider_effects = tuple(
        ProviderEffectRecord(
            action=action,
            status=DrillVerdict.NOT_EXECUTED.value,
            detail=(
                "provider-side production action is outside authoritative synthetic drills"
            ),
        )
        for action in (
            "revoke-production-authenticode-certificate",
            "rotate-production-tuf-root-keys",
            "delete-or-withdraw-public-github-release",
            "delete-public-release-tag-or-asset",
            "delete-github-artifact-attestation",
            "submit-public-winget-supersession",
        )
    )
    report = IncidentDrillReport(
        source_sha=source,
        scenarios=tuple(scenarios),
        provider_effects=provider_effects,
    )
    payload = report.to_dict()
    digest = payload.get("report_sha256")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise IncidentDrillError("incident report digest is invalid")
    if report.status != "PASS":
        raise IncidentDrillError(
            "R18.10 incident drill failed with "
            f"{report.critical_bypass_count} critical bypasses"
        )
    return report


def write_incident_report(
    report: IncidentDrillReport,
    output: str | Path,
) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


__all__ = [
    "CompromisedCertificateTrustPolicy",
    "DrillVerdict",
    "IncidentDrillError",
    "IncidentDrillReport",
    "IncidentScenarioResult",
    "ProviderEffectRecord",
    "ReleaseIncidentDirective",
    "run_synthetic_incident_drills",
    "write_incident_report",
]
