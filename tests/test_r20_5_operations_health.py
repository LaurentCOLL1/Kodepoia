from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata

from kodepoia.update.operations_health import (
    ONLINE_CRITICAL_SECONDS,
    ONLINE_WARNING_SECONDS,
    REFRESH_SUCCESS_CRITICAL_SECONDS,
    REFRESH_SUCCESS_WARNING_SECONDS,
    assess_metadata_health,
    assess_refresh_workflow_health,
    build_operations_health_report,
    temporary_update_service_message,
)


def _serialize(metadata: Metadata[object]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _signed(payload: dict[str, object], signer: CryptoSigner) -> bytes:
    metadata = Metadata.from_dict({"signatures": [], "signed": payload})
    metadata.sign(signer)
    return _serialize(metadata)


def _fixture(*, online_expires: str) -> dict[str, bytes]:
    root_signer = CryptoSigner.generate_ed25519()
    targets_signer = CryptoSigner.generate_ed25519()
    snapshot_signer = CryptoSigner.generate_ed25519()
    timestamp_signer = CryptoSigner.generate_ed25519()
    authority_expires = "2027-09-10T00:00:00Z"
    signers = {
        "root": root_signer,
        "targets": targets_signer,
        "snapshot": snapshot_signer,
        "timestamp": timestamp_signer,
    }
    keys = {signer.public_key.keyid: signer.public_key.to_dict() for signer in signers.values()}
    roles = {
        role: {"keyids": [signer.public_key.keyid], "threshold": 1}
        for role, signer in signers.items()
    }
    root_bytes = _signed(
        {
            "_type": "root",
            "consistent_snapshot": False,
            "expires": authority_expires,
            "keys": keys,
            "roles": roles,
            "spec_version": "1.0.31",
            "version": 2,
        },
        root_signer,
    )
    targets_bytes = _signed(
        {
            "_type": "targets",
            "expires": authority_expires,
            "spec_version": "1.0.31",
            "targets": {},
            "version": 2,
        },
        targets_signer,
    )
    snapshot_bytes = _signed(
        {
            "_type": "snapshot",
            "expires": online_expires,
            "meta": {
                "targets.json": {
                    "hashes": {"sha256": hashlib.sha256(targets_bytes).hexdigest()},
                    "length": len(targets_bytes),
                    "version": 2,
                }
            },
            "spec_version": "1.0.31",
            "version": 4,
        },
        snapshot_signer,
    )
    timestamp_bytes = _signed(
        {
            "_type": "timestamp",
            "expires": online_expires,
            "meta": {
                "snapshot.json": {
                    "hashes": {"sha256": hashlib.sha256(snapshot_bytes).hexdigest()},
                    "length": len(snapshot_bytes),
                    "version": 4,
                }
            },
            "spec_version": "1.0.31",
            "version": 4,
        },
        timestamp_signer,
    )
    return {
        "root": root_bytes,
        "targets": targets_bytes,
        "snapshot": snapshot_bytes,
        "timestamp": timestamp_bytes,
    }


def _run(
    *,
    started: str,
    conclusion: str = "success",
    status: str = "completed",
    event: str = "schedule",
    branch: str | None = "main",
    run_id: int = 1,
) -> dict[str, object]:
    return {
        "id": run_id,
        "event": event,
        "head_branch": branch,
        "head_sha": "a" * 40,
        "status": status,
        "conclusion": conclusion,
        "run_started_at": started,
        "updated_at": started,
        "html_url": f"https://github.com/LaurentCOLL1/Kodepoia/actions/runs/{run_id}",
    }


def test_metadata_lifetime_thresholds_warn_then_fail_before_expiry() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    warning = _fixture(online_expires="2026-09-11T23:00:00Z")
    warning_health = assess_metadata_health(
        root_bytes=warning["root"],
        targets_bytes=warning["targets"],
        snapshot_bytes=warning["snapshot"],
        timestamp_bytes=warning["timestamp"],
        reference_time=now,
    )
    assert ONLINE_WARNING_SECONDS == 36 * 60 * 60
    assert warning_health["state"] == "warning"

    critical = _fixture(online_expires="2026-09-11T12:00:00Z")
    critical_health = assess_metadata_health(
        root_bytes=critical["root"],
        targets_bytes=critical["targets"],
        snapshot_bytes=critical["snapshot"],
        timestamp_bytes=critical["timestamp"],
        reference_time=now,
    )
    assert ONLINE_CRITICAL_SECONDS == 24 * 60 * 60
    assert critical_health["state"] == "critical"
    assert critical_health["verified"] is True


def test_expired_or_unverifiable_metadata_is_critical_and_never_accepted() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-10T11:59:59Z")
    health = assess_metadata_health(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        snapshot_bytes=fixture["snapshot"],
        timestamp_bytes=fixture["timestamp"],
        reference_time=now,
    )
    assert health["state"] == "critical"
    assert health["verified"] is False

    corrupted = dict(fixture)
    corrupted["snapshot"] = fixture["snapshot"] + b" "
    health = assess_metadata_health(
        root_bytes=corrupted["root"],
        targets_bytes=corrupted["targets"],
        snapshot_bytes=corrupted["snapshot"],
        timestamp_bytes=corrupted["timestamp"],
        reference_time=now,
    )
    assert health["state"] == "critical"
    assert health["verified"] is False


def test_refresh_workflow_detects_missed_schedule_and_repeated_failures() -> None:
    now = datetime(2026, 9, 10, 20, 0, tzinfo=UTC)
    healthy = assess_refresh_workflow_health(
        {"workflow_runs": [_run(started="2026-09-10T18:17:00Z")]},
        reference_time=now,
    )
    assert healthy.state == "healthy"
    assert REFRESH_SUCCESS_WARNING_SECONDS == 9 * 60 * 60
    assert REFRESH_SUCCESS_CRITICAL_SECONDS == 18 * 60 * 60

    warning = assess_refresh_workflow_health(
        {"workflow_runs": [_run(started="2026-09-10T10:30:00Z")]},
        reference_time=now,
    )
    assert warning.state == "warning"

    critical = assess_refresh_workflow_health(
        {"workflow_runs": [_run(started="2026-09-10T01:00:00Z")]},
        reference_time=now,
    )
    assert critical.state == "critical"

    failures = assess_refresh_workflow_health(
        {
            "workflow_runs": [
                _run(started="2026-09-10T19:00:00Z", conclusion="failure", run_id=3),
                _run(started="2026-09-10T13:00:00Z", conclusion="failure", run_id=2),
                _run(started="2026-09-10T07:00:00Z", run_id=1),
            ]
        },
        reference_time=now,
    )
    assert failures.state == "critical"
    assert failures.consecutive_failures == 2


def test_refresh_evidence_ignores_unrelated_branch_and_event() -> None:
    now = datetime(2026, 9, 10, 20, 0, tzinfo=UTC)
    health = assess_refresh_workflow_health(
        {
            "workflow_runs": [
                _run(started="2026-09-10T19:00:00Z", event="push", run_id=2),
                _run(started="2026-09-10T19:00:00Z", branch="feature", run_id=1),
            ]
        },
        reference_time=now,
    )
    assert health.state == "warning"
    assert health.considered_runs == 0


def test_combined_report_is_secret_free_and_non_blocking_for_application() -> None:
    now = datetime(2026, 9, 10, 20, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-13T20:00:00Z")
    report = build_operations_health_report(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        snapshot_bytes=fixture["snapshot"],
        timestamp_bytes=fixture["timestamp"],
        workflow_runs={"workflow_runs": [_run(started="2026-09-10T18:17:00Z")]},
        reference_time=now,
        source_sha="b" * 40,
    )
    assert report["state"] == "healthy"
    assert report["blocks_application_startup"] is False
    assert report["blocks_local_work"] is False
    assert report["accepts_expired_or_unverifiable_metadata"] is False
    assert report["private_material_in_output"] is False
    assert "TUF_SNAPSHOT_ED25519_SEED_B64" not in str(report)
    assert "TUF_TIMESTAMP_ED25519_SEED_B64" not in str(report)


def test_localized_temporary_service_messages_are_retryable_and_safe() -> None:
    english = temporary_update_service_message("metadata-expired", "en-US")
    french = temporary_update_service_message("refresh-outage", "fr-FR")
    fallback = temporary_update_service_message("verification-failed", "de-DE")

    assert "temporarily" in str(english["message"]).lower()
    assert "temporairement" in str(french["message"]).lower()
    assert fallback["locale"] == "en"
    for payload in (english, french, fallback):
        assert payload["retryable"] is True
        assert payload["blocks_application_startup"] is False
        assert payload["local_work_available"] is True
        assert payload["accepts_expired_metadata"] is False
        assert payload["accepts_unverifiable_metadata"] is False
