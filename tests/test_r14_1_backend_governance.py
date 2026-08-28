from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.backend import (
    BackendBoundaryError,
    BackendEndpointDefinition,
    BackendEnvironmentIdentity,
    BackendEnvironmentKind,
    BackendGovernanceBoundary,
    BackendOperationIntent,
    BackendOperationKind,
    BackendOperationRisk,
    BackendProviderRequest,
    canonical_sha256,
)
from kodepoia.core.audit import AuditLog
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet

ROOT = Path(__file__).resolve().parents[1]


def _intent(kind: BackendOperationKind = BackendOperationKind.CONNECT) -> BackendOperationIntent:
    environment = BackendEnvironmentIdentity(
        environment_id="backend.test",
        kind=BackendEnvironmentKind.TEST,
    )
    return BackendOperationIntent(
        operation_id="operation.test",
        operation_kind=kind,
        environment_id=environment.environment_id,
        service_id="service.authoritative",
        endpoint_id="endpoint.api",
        request_digest=canonical_sha256({"method": "GET", "path": "/health"}),
        expected_environment_digest=environment.digest(),
    )


def test_r14_1_operation_risk_and_permission_are_derived_not_model_selected() -> None:
    assert _intent(BackendOperationKind.PROBE).risk is BackendOperationRisk.NETWORK_ACTIVE
    assert _intent(BackendOperationKind.CONNECT).risk is BackendOperationRisk.NETWORK_ACTIVE
    assert _intent(BackendOperationKind.DEPLOY).risk is BackendOperationRisk.MUTATING
    assert _intent(BackendOperationKind.MIGRATE).risk is BackendOperationRisk.MUTATING
    assert _intent(BackendOperationKind.MUTATE).risk is BackendOperationRisk.MUTATING
    assert _intent(BackendOperationKind.PROMOTE).risk is BackendOperationRisk.MUTATING
    assert _intent(BackendOperationKind.ROLLBACK).risk is BackendOperationRisk.DESTRUCTIVE
    assert _intent().required_capability is Capability.NETWORK
    payload = _intent().canonical()
    assert payload["required_capability"] == "network"
    assert "command" not in payload
    assert "raw_url" not in payload
    assert "token" not in payload


def test_r14_1_permission_denial_fails_closed_and_is_audited(tmp_path: Path) -> None:
    audit = AuditLog(tmp_path / "audit.jsonl")
    boundary = BackendGovernanceBoundary(
        permissions=PermissionSet(),
        audit_log=audit,
        actor="test.backend",
        kill_switch=KillSwitch(),
    )
    with pytest.raises(BackendBoundaryError, match="not granted"):
        boundary.authorize(_intent())
    assert audit.verify()
    event = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert event["outcome"] == "denied_permission"
    assert event["details"]["required_capability"] == "network"
    assert "token" not in json.dumps(event).lower()
    assert "password" not in json.dumps(event).lower()


def test_r14_1_kill_switch_blocks_before_permission_and_is_audited(tmp_path: Path) -> None:
    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.NETWORK))
    audit = AuditLog(tmp_path / "audit.jsonl")
    kill_switch = KillSwitch()
    kill_switch.trigger()
    boundary = BackendGovernanceBoundary(
        permissions=permissions,
        audit_log=audit,
        actor="test.backend",
        kill_switch=kill_switch,
    )
    with pytest.raises(BackendBoundaryError, match="kill switch"):
        boundary.authorize(_intent())
    assert audit.verify()
    event = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert event["outcome"] == "blocked_kill_switch"


def test_r14_1_allowed_operation_binds_permission_to_audit_hash(tmp_path: Path) -> None:
    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.NETWORK))
    audit = AuditLog(tmp_path / "audit.jsonl")
    boundary = BackendGovernanceBoundary(
        permissions=permissions,
        audit_log=audit,
        actor="test.backend",
        kill_switch=KillSwitch(),
    )
    intent = _intent(BackendOperationKind.CONNECT)
    authorization = boundary.authorize(intent)
    assert authorization.operation_intent_digest == intent.digest()
    assert authorization.permission_capability == "network"
    assert authorization.outcome == "allowed"
    assert len(authorization.audit_event_hash) == 64
    assert audit.verify()
    event = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert event["event_hash"] == authorization.audit_event_hash
    assert event["details"]["operation_intent_digest"] == intent.digest()


def test_r14_1_provider_request_is_digest_only_and_deterministic() -> None:
    intent = _intent()
    endpoint = BackendEndpointDefinition(
        endpoint_id="endpoint.api",
        service_id="service.authoritative",
        environment_id="backend.test",
        scheme="http",
        host="127.0.0.1",
        port=8080,
        base_path="/v1",
    )
    payload_digest = canonical_sha256({"bounded": "payload"})
    idempotency_digest = canonical_sha256({"key": "request-123"})
    request = BackendProviderRequest(
        request_id="provider.request.1",
        provider_id="local",
        operation_intent_digest=intent.digest(),
        endpoint_digest=endpoint.digest(),
        payload_digest=payload_digest,
        idempotency_key_digest=idempotency_digest,
    )
    same = BackendProviderRequest(
        request_id="provider.request.1",
        provider_id="local",
        operation_intent_digest=intent.digest(),
        endpoint_digest=endpoint.digest(),
        payload_digest=payload_digest,
        idempotency_key_digest=idempotency_digest,
    )
    assert request.digest() == same.digest()
    assert set(request.canonical()) == {
        "request_id",
        "provider_id",
        "operation_intent_digest",
        "endpoint_digest",
        "payload_digest",
        "idempotency_key_digest",
    }
    serialized = json.dumps(request.canonical(), sort_keys=True)
    assert "bounded" not in serialized
    assert "request-123" not in serialized


def test_r14_1_operation_and_provider_schemas_are_strict() -> None:
    operation_schema = json.loads(
        (ROOT / "schemas/r14/backend-operation-intent.schema.json").read_text(encoding="utf-8")
    )
    provider_schema = json.loads(
        (ROOT / "schemas/r14/backend-provider-request.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(operation_schema)
    Draft202012Validator.check_schema(provider_schema)

    intent = _intent()
    endpoint = BackendEndpointDefinition(
        endpoint_id="endpoint.api",
        service_id="service.authoritative",
        environment_id="backend.test",
        scheme="http",
        host="127.0.0.1",
        port=8080,
    )
    request = BackendProviderRequest(
        request_id="provider.request.schema",
        provider_id="local",
        operation_intent_digest=intent.digest(),
        endpoint_digest=endpoint.digest(),
    )
    Draft202012Validator(operation_schema).validate(intent.canonical())
    Draft202012Validator(provider_schema).validate(request.canonical())

    forged_intent = dict(intent.canonical())
    forged_intent["raw_argv"] = ["curl", "http://169.254.169.254"]
    with pytest.raises(Exception):
        Draft202012Validator(operation_schema).validate(forged_intent)
    forged_request = dict(request.canonical())
    forged_request["access_token"] = "secret"
    with pytest.raises(Exception):
        Draft202012Validator(provider_schema).validate(forged_request)
