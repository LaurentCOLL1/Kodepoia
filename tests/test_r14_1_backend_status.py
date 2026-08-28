from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.backend import (
    BackendErrorCode,
    BackendOperationStatus,
    BackendStatusSnapshot,
    canonical_sha256,
)

ROOT = Path(__file__).resolve().parents[1]


def test_r14_1_status_failure_and_blocked_require_structured_error_code() -> None:
    with pytest.raises(ValueError, match="requires an error_code"):
        BackendStatusSnapshot(operation_id="operation.blocked", status=BackendOperationStatus.BLOCKED)
    with pytest.raises(ValueError, match="requires an error_code"):
        BackendStatusSnapshot(operation_id="operation.failed", status=BackendOperationStatus.FAILED)

    blocked = BackendStatusSnapshot(
        operation_id="operation.blocked",
        status=BackendOperationStatus.BLOCKED,
        error_code=BackendErrorCode.PERMISSION_DENIED,
    )
    assert blocked.canonical()["error_code"] == "PERMISSION_DENIED"


def test_r14_1_success_requires_evidence_and_nonterminal_states_cannot_claim_it() -> None:
    with pytest.raises(ValueError, match="SUCCEEDED requires"):
        BackendStatusSnapshot(operation_id="operation.success", status=BackendOperationStatus.SUCCEEDED)

    evidence = canonical_sha256({"result": "accepted"})
    success = BackendStatusSnapshot(
        operation_id="operation.success",
        status=BackendOperationStatus.SUCCEEDED,
        evidence_digest=evidence,
    )
    assert success.evidence_digest == evidence

    with pytest.raises(ValueError, match="cannot claim result evidence"):
        BackendStatusSnapshot(
            operation_id="operation.authorized",
            status=BackendOperationStatus.AUTHORIZED,
            evidence_digest=evidence,
        )


def test_r14_1_error_code_cannot_be_attached_to_nonfailure_status() -> None:
    with pytest.raises(ValueError, match="only valid"):
        BackendStatusSnapshot(
            operation_id="operation.progress",
            status=BackendOperationStatus.IN_PROGRESS,
            error_code=BackendErrorCode.PROVIDER_FAILED,
        )


def test_r14_1_status_schema_round_trip_is_strict() -> None:
    schema = json.loads(
        (ROOT / "schemas/r14/backend-status-snapshot.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    snapshot = BackendStatusSnapshot(
        operation_id="operation.status.schema",
        status=BackendOperationStatus.BLOCKED,
        error_code=BackendErrorCode.NETWORK_DENIED,
    )
    Draft202012Validator(schema).validate(snapshot.canonical())
    forged = dict(snapshot.canonical())
    forged["provider_message"] = "secret raw provider response"
    with pytest.raises(Exception):
        Draft202012Validator(schema).validate(forged)
