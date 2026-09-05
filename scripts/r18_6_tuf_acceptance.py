from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from kodepoia.release.tuf_security import (
    SyntheticTufRepositoryBuilder,
    TufUpdateVerifier,
    TufVerificationError,
)

REFERENCE_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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
    except TufVerificationError as exc:
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
                timestamp_expires=datetime(2026, 9, 4, tzinfo=timezone.utc),
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


def build_report(source_sha: str) -> dict[str, object]:
    source = source_sha.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(source):
        raise ValueError("source SHA must be an exact lowercase 40-character Git commit")
    cases = [
        _run_case("valid_update_from_trusted_state", "PASS", _valid_update),
        _run_case("timestamp_rollback", "REFUSED", _timestamp_rollback),
        _run_case("snapshot_rollback", "REFUSED", _snapshot_rollback),
        _run_case("freeze_expired_metadata", "REFUSED", _freeze_expired),
        _run_case("targets_wrong_digest", "REFUSED", _targets_wrong_digest),
        _run_case("root_threshold_insufficient", "REFUSED", _root_threshold),
        _run_case("trusted_state_restart_restore", "PASS", _restart_restore),
    ]
    return {
        "schema_version": 1,
        "phase": "R18.6",
        "source_sha": source,
        "reference_time": REFERENCE_TIME.isoformat(),
        "library_contract": {
            "tuf": ">=7,<8",
            "securesystemslib_crypto": ">=1.4,<2",
            "network_required": False,
            "production_keys_used": False,
        },
        "cases_total": len(cases),
        "cases_passed": sum(case.passed for case in cases),
        "cases": [case.to_dict() for case in cases],
        "trusted_state_persistent": True,
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
    return 0 if report["cases_passed"] == report["cases_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
