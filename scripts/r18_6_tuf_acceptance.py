from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.tuf_security import (
    SyntheticTufRepositoryBuilder,
    TufUpdateVerifier,
    TufVerificationError,
)
from kodepoia.update.bootstrap import load_synthetic_packaged_root
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateClient,
    UpdateTargetSpec,
    UpdateTransportError,
)

REFERENCE_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_PLATFORM = "windows-x86_64"
_INSTALLER_V1 = b"synthetic-kodepoia-installer-v1\n"
_INSTALLER_V2 = b"synthetic-kodepoia-installer-v2\n"


@dataclass(frozen=True, slots=True)
class CaseResult:
    name: str
    expected: str
    actual: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "detail": self.detail,
        }


def _run_case(name: str, expected: str, operation: Callable[[], None]) -> CaseResult:
    try:
        operation()
    except (TufVerificationError, UpdateTransportError) as exc:
        actual = "REFUSED"
        detail = str(exc)
    except Exception as exc:
        actual = "ERROR"
        detail = f"{type(exc).__name__}: {exc}"
    else:
        actual = "PASS"
        detail = "verification completed"
    return CaseResult(name, expected, actual, actual == expected, detail)


def _valid_update() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder()
        verifier = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        first = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
        verifier.verify(first, bootstrap_root=first.root)
        second = builder.build(timestamp_version=2, snapshot_version=2, targets_version=2)
        verifier.verify(second)


def _timestamp_rollback() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder()
        verifier = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        trusted = builder.build(timestamp_version=2, snapshot_version=2, targets_version=2)
        verifier.verify(trusted, bootstrap_root=trusted.root)
        verifier.verify(builder.build(timestamp_version=1, snapshot_version=3, targets_version=3))


def _snapshot_rollback() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder()
        verifier = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        trusted = builder.build(timestamp_version=2, snapshot_version=2, targets_version=2)
        verifier.verify(trusted, bootstrap_root=trusted.root)
        verifier.verify(builder.build(timestamp_version=3, snapshot_version=1, targets_version=3))


def _freeze_expired() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder()
        verifier = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        trusted = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
        verifier.verify(trusted, bootstrap_root=trusted.root)
        verifier.verify(
            builder.build(
                timestamp_version=2,
                snapshot_version=2,
                targets_version=2,
                timestamp_expires=datetime(2026, 9, 4, tzinfo=UTC),
            )
        )


def _targets_wrong_digest() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder()
        verifier = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        trusted = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
        verifier.verify(trusted, bootstrap_root=trusted.root)
        verifier.verify(
            builder.build(
                timestamp_version=2,
                snapshot_version=2,
                targets_version=2,
                corrupt_targets_reference=True,
            )
        )


def _root_threshold() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder(root_threshold=2)
        verifier = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        trusted = builder.build(root_version=1)
        verifier.verify(trusted, bootstrap_root=trusted.root)
        verifier.verify(
            builder.build(
                root_version=2,
                root_signature_count=1,
                timestamp_version=2,
                snapshot_version=2,
                targets_version=2,
            )
        )


def _restart_restore() -> None:
    with tempfile.TemporaryDirectory() as temp:
        builder = SyntheticTufRepositoryBuilder()
        first = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
        TufUpdateVerifier(temp, reference_time=REFERENCE_TIME).verify(
            first, bootstrap_root=first.root
        )
        second = builder.build(timestamp_version=2, snapshot_version=2, targets_version=2)
        restarted = TufUpdateVerifier(temp, reference_time=REFERENCE_TIME)
        state = restarted.verify(second)
        if state.timestamp_version != 2 or restarted.load_state() != state:
            raise RuntimeError("persisted trusted state was not restored after restart")


def _target(source_sha: str, *, channel: str | None = None) -> UpdateTargetSpec:
    if channel is None:
        return UpdateTargetSpec.from_release(
            CURRENT_RELEASE,
            source_sha=source_sha,
            platform=_PLATFORM,
        )
    return UpdateTargetSpec(
        channel=channel,
        platform=_PLATFORM,
        public_version=CURRENT_RELEASE.public_version,
        source_sha=source_sha,
    )


def _channel_refresh(source_sha: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = _target(source_sha)
        builder = SyntheticUpdateRepositoryBuilder()
        repository = builder.build(target, _INSTALLER_V1)
        client = UpdateClient(
            temp,
            root_pin=PackagedRootPin.from_root(repository.root),
            reference_time=REFERENCE_TIME,
        )
        result = client.check(MemoryUpdateTransport.from_repository(repository), target)
        if result.status != "verified" or result.candidate is None:
            raise RuntimeError(f"channel-aware refresh failed: {result.detail}")
        if result.candidate.size_bytes != len(_INSTALLER_V1):
            raise RuntimeError("verified installer size was not preserved")


def _compromised_mirror(source_sha: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = _target(source_sha)
        builder = SyntheticUpdateRepositoryBuilder()
        repository = builder.build(target, _INSTALLER_V1)
        transport = MemoryUpdateTransport.from_repository(repository)
        client = UpdateClient(
            temp,
            root_pin=PackagedRootPin.from_root(repository.root),
            reference_time=REFERENCE_TIME,
        )
        client.verify_refresh(transport, target)
        transport.targets[target.path] = b"tampered installer\n"
        client.verify_refresh(transport, target)


def _wrong_channel(source_sha: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        beta_target = _target(source_sha)
        stable_target = _target(source_sha, channel="stable")
        builder = SyntheticUpdateRepositoryBuilder()
        repository = builder.build(beta_target, _INSTALLER_V1)
        client = UpdateClient(
            temp,
            root_pin=PackagedRootPin.from_root(repository.root),
            reference_time=REFERENCE_TIME,
        )
        client.verify_refresh(MemoryUpdateTransport.from_repository(repository), stable_target)


def _root_rotation(source_sha: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = _target(source_sha)
        builder = SyntheticUpdateRepositoryBuilder(root_threshold=2)
        first = builder.build(target, _INSTALLER_V1, root_version=1)
        client = UpdateClient(
            temp,
            root_pin=PackagedRootPin.from_root(first.root),
            reference_time=REFERENCE_TIME,
        )
        client.verify_refresh(MemoryUpdateTransport.from_repository(first), target)
        builder.rotate_root_keys()
        second = builder.build(
            target,
            _INSTALLER_V2,
            root_version=2,
            timestamp_version=2,
            snapshot_version=2,
            targets_version=2,
        )
        rotated = client.verify_refresh(MemoryUpdateTransport.from_repository(second), target)
        if rotated.tuf_state.root_version != 2:
            raise RuntimeError("root rotation did not advance trusted root version")


def _offline_cached(source_sha: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = _target(source_sha)
        builder = SyntheticUpdateRepositoryBuilder()
        repository = builder.build(target, _INSTALLER_V1)
        transport = MemoryUpdateTransport.from_repository(repository)
        client = UpdateClient(
            temp,
            root_pin=PackagedRootPin.from_root(repository.root),
            reference_time=REFERENCE_TIME,
        )
        verified = client.check(transport, target)
        if verified.status != "verified":
            raise RuntimeError("initial cached update verification failed")
        transport.online = False
        offline = client.check(transport, target)
        if offline.status != "offline-cached" or offline.candidate != verified.candidate:
            raise RuntimeError("offline check did not return last verified candidate")


def _wrong_root_pin(source_sha: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = _target(source_sha)
        trusted = SyntheticUpdateRepositoryBuilder().build(target, _INSTALLER_V1)
        attacker = SyntheticUpdateRepositoryBuilder().build(target, _INSTALLER_V1)
        client = UpdateClient(
            temp,
            root_pin=PackagedRootPin.from_root(trusted.root),
            reference_time=REFERENCE_TIME,
        )
        client.verify_refresh(MemoryUpdateTransport.from_repository(attacker), target)


def _packaged_root_embedding() -> None:
    material = load_synthetic_packaged_root(allow_synthetic=True)
    if material.pin.version != 1:
        raise RuntimeError("packaged synthetic root version is not 1")
    if material.production_trust_claim or material.private_keys_persisted:
        raise RuntimeError("packaged synthetic root safety flags are invalid")
    material.pin.verify(material.root_bytes)


def build_report(source_sha: str) -> dict[str, object]:
    source = source_sha.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(source):
        raise ValueError("source SHA must be an exact lowercase 40-character Git commit")
    core_cases = [
        _run_case("valid_update_from_trusted_state", "PASS", _valid_update),
        _run_case("timestamp_rollback", "REFUSED", _timestamp_rollback),
        _run_case("snapshot_rollback", "REFUSED", _snapshot_rollback),
        _run_case("freeze_expired_metadata", "REFUSED", _freeze_expired),
        _run_case("targets_wrong_digest", "REFUSED", _targets_wrong_digest),
        _run_case("root_threshold_insufficient", "REFUSED", _root_threshold),
        _run_case("trusted_state_restart_restore", "PASS", _restart_restore),
    ]
    product_cases = [
        _run_case("channel_platform_installer_refresh", "PASS", lambda: _channel_refresh(source)),
        _run_case("compromised_mirror_target", "REFUSED", lambda: _compromised_mirror(source)),
        _run_case("wrong_channel_target", "REFUSED", lambda: _wrong_channel(source)),
        _run_case("root_key_rotation", "PASS", lambda: _root_rotation(source)),
        _run_case("offline_cached_state", "PASS", lambda: _offline_cached(source)),
        _run_case("wrong_packaged_root_pin", "REFUSED", lambda: _wrong_root_pin(source)),
        _run_case("packaged_synthetic_root_embedding", "PASS", _packaged_root_embedding),
    ]
    packaged = load_synthetic_packaged_root(allow_synthetic=True)
    return {
        "schema_version": 3,
        "phase": "R18.6",
        "source_sha": source,
        "reference_time": REFERENCE_TIME.isoformat(),
        "release_identity": CURRENT_RELEASE.to_dict(),
        "platform": _PLATFORM,
        "library_contract": {
            "tuf": ">=7,<8",
            "securesystemslib_crypto": ">=1.4,<2",
            "network_required": False,
            "production_keys_used": False,
        },
        "packaged_root": {
            "purpose": packaged.purpose,
            "version": packaged.pin.version,
            "sha256": packaged.pin.sha256,
            "production_trust_claim": packaged.production_trust_claim,
            "private_keys_persisted": packaged.private_keys_persisted,
        },
        "core_cases_total": len(core_cases),
        "core_cases_passed": sum(case.passed for case in core_cases),
        "core_cases": [case.to_dict() for case in core_cases],
        "product_cases_total": len(product_cases),
        "product_cases_passed": sum(case.passed for case in product_cases),
        "product_cases": [case.to_dict() for case in product_cases],
        "trusted_state_persistent": True,
        "channel_platform_bound": True,
        "offline_cache_non_blocking": True,
        "public_release_created": False,
        "production_signing_triggered": False,
        "public_winget_submission_triggered": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run R18.6 offline TUF acceptance.")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    all_passed = (
        report["core_cases_passed"] == report["core_cases_total"]
        and report["product_cases_passed"] == report["product_cases_total"]
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
