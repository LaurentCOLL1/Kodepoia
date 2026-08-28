from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.backend import (
    BackendBoundaryError,
    BackendCapabilitySnapshot,
    BackendCapabilityState,
    BackendEndpointDefinition,
    BackendEnvironmentIdentity,
    BackendEnvironmentKind,
    BackendNetworkBoundary,
    BackendNetworkPolicy,
    BackendRuntimeBudget,
    BackendServiceIdentity,
    BackendServiceKind,
    canonical_json_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def _environment(
    kind: BackendEnvironmentKind = BackendEnvironmentKind.PRODUCTION,
    environment_id: str = "backend.production",
) -> BackendEnvironmentIdentity:
    return BackendEnvironmentIdentity(environment_id=environment_id, kind=kind)


def _endpoint(
    *,
    environment_id: str = "backend.production",
    endpoint_id: str = "endpoint.api",
    host: str = "api.example.com",
    scheme: str = "https",
    port: int = 443,
    allow_redirects: bool = False,
) -> BackendEndpointDefinition:
    return BackendEndpointDefinition(
        endpoint_id=endpoint_id,
        service_id="service.authoritative",
        environment_id=environment_id,
        scheme=scheme,
        host=host,
        port=port,
        base_path="/v1",
        allow_redirects=allow_redirects,
    )


def _boundary(
    *,
    environment: BackendEnvironmentIdentity | None = None,
    endpoint: BackendEndpointDefinition | None = None,
    resolved: tuple[str, ...] = ("1.1.1.1",),
    permit_loopback: bool = False,
    permit_private: bool = False,
) -> BackendNetworkBoundary:
    environment = environment or _environment()
    endpoint = endpoint or _endpoint(environment_id=environment.environment_id)
    policy = BackendNetworkPolicy(
        environment_id=environment.environment_id,
        allowed_endpoint_ids=(endpoint.endpoint_id,),
        allowed_hosts=(endpoint.host,),
        permit_loopback=permit_loopback,
        permit_private=permit_private,
    )
    return BackendNetworkBoundary(
        environments=(environment,),
        endpoints=(endpoint,),
        policies=(policy,),
        resolver=lambda _host, _port: resolved,
    )


def test_r14_1_backend_identities_are_immutable_and_deterministic() -> None:
    service = BackendServiceIdentity(
        service_id="service.authoritative",
        service_kind=BackendServiceKind.AUTHORITATIVE_SERVER,
    )
    same = BackendServiceIdentity(
        service_id="service.authoritative",
        service_kind=BackendServiceKind.AUTHORITATIVE_SERVER,
    )
    environment = _environment()
    assert service.digest() == same.digest()
    assert service.digest() != environment.digest()
    assert service.provider_id == "provider-neutral"

    with pytest.raises(ValueError, match="stable identifier"):
        BackendServiceIdentity(
            service_id="../escape",
            service_kind=BackendServiceKind.AUTH,
        )


def test_r14_1_endpoint_contract_normalizes_host_and_rejects_url_injection() -> None:
    endpoint = _endpoint(host="API.Example.COM")
    assert endpoint.host == "api.example.com"
    assert endpoint.scheme == "https"

    for host in (
        "https://api.example.com",
        "user:password@api.example.com",
        "api.example.com/path",
        "api.example.com?next=http://127.0.0.1",
        " api.example.com",
    ):
        with pytest.raises(ValueError):
            _endpoint(host=host)

    with pytest.raises(ValueError, match="traversal"):
        BackendEndpointDefinition(
            endpoint_id="endpoint.bad.path",
            service_id="service.authoritative",
            environment_id="backend.production",
            scheme="https",
            host="api.example.com",
            port=443,
            base_path="/v1/../admin",
        )


def test_r14_1_runtime_budget_is_bounded_and_deterministic() -> None:
    budget = BackendRuntimeBudget(
        connect_timeout_ms=1000,
        read_timeout_ms=4000,
        total_timeout_ms=5000,
        max_retries=2,
        retry_backoff_ms=200,
        max_response_bytes=1024,
    )
    assert budget.digest() == BackendRuntimeBudget(
        connect_timeout_ms=1000,
        read_timeout_ms=4000,
        total_timeout_ms=5000,
        max_retries=2,
        retry_backoff_ms=200,
        max_response_bytes=1024,
    ).digest()
    with pytest.raises(ValueError, match="connect_timeout_ms"):
        BackendRuntimeBudget(connect_timeout_ms=0)
    with pytest.raises(ValueError, match="max_retries"):
        BackendRuntimeBudget(max_retries=9)
    with pytest.raises(ValueError, match="shorter than read_timeout_ms"):
        BackendRuntimeBudget(read_timeout_ms=5000, total_timeout_ms=4000)


def test_r14_1_capability_state_cannot_be_manufactured() -> None:
    with pytest.raises(ValueError, match="AVAILABLE requires"):
        BackendCapabilitySnapshot(
            snapshot_id="snapshot.bad.available",
            environment_id="backend.test",
            provider_id="local",
            state=BackendCapabilityState.AVAILABLE,
        )
    with pytest.raises(ValueError, match="BLOCKED requires"):
        BackendCapabilitySnapshot(
            snapshot_id="snapshot.bad.blocked",
            environment_id="backend.test",
            provider_id="local",
            state=BackendCapabilityState.BLOCKED,
        )
    with pytest.raises(ValueError, match="NOT_PROBED"):
        BackendCapabilitySnapshot(
            snapshot_id="snapshot.bad.not-probed",
            environment_id="backend.test",
            provider_id="local",
            state=BackendCapabilityState.NOT_PROBED,
            capabilities=("network.probe",),
        )

    endpoint = _endpoint(environment_id="backend.test")
    service = BackendServiceIdentity(
        service_id="service.authoritative",
        service_kind=BackendServiceKind.AUTHORITATIVE_SERVER,
    )
    snapshot = BackendCapabilitySnapshot(
        snapshot_id="snapshot.good",
        environment_id="backend.test",
        provider_id="local",
        state=BackendCapabilityState.AVAILABLE,
        capabilities=("network.probe", "network.probe", "runtime.budget"),
        service_digests=(service.digest(),),
        endpoint_digests=(endpoint.digest(),),
    )
    assert snapshot.capabilities == ("network.probe", "runtime.budget")
    assert len(snapshot.digest()) == 64


def test_r14_1_canonical_payload_rejects_nonfinite_data() -> None:
    with pytest.raises(ValueError, match="not serializable"):
        canonical_json_bytes({"latency_ms": float("nan")})


def test_r14_1_json_schemas_accept_canonical_contracts_and_reject_extra_fields() -> None:
    endpoint_schema = json.loads(
        (ROOT / "schemas/r14/backend-endpoint-definition.schema.json").read_text(encoding="utf-8")
    )
    capability_schema = json.loads(
        (ROOT / "schemas/r14/backend-capability-snapshot.schema.json").read_text(encoding="utf-8")
    )
    auth_schema = json.loads(
        (ROOT / "schemas/r14/backend-network-authorization.schema.json").read_text(encoding="utf-8")
    )
    for schema in (endpoint_schema, capability_schema, auth_schema):
        Draft202012Validator.check_schema(schema)

    endpoint = _endpoint()
    snapshot = BackendCapabilitySnapshot(
        snapshot_id="snapshot.schema",
        environment_id="backend.production",
        provider_id="provider-neutral",
        state=BackendCapabilityState.AVAILABLE,
        capabilities=("network.probe",),
        endpoint_digests=(endpoint.digest(),),
    )
    authorization = _boundary(endpoint=endpoint).authorize(
        endpoint.endpoint_id,
        budget=BackendRuntimeBudget(),
    )
    Draft202012Validator(endpoint_schema).validate(endpoint.canonical())
    Draft202012Validator(capability_schema).validate(snapshot.canonical())
    Draft202012Validator(auth_schema).validate(authorization.canonical())

    forged = dict(endpoint.canonical())
    forged["raw_url"] = "http://169.254.169.254/latest/meta-data"
    with pytest.raises(Exception):
        Draft202012Validator(endpoint_schema).validate(forged)
    forged_auth = dict(authorization.canonical())
    forged_auth["token"] = "secret"
    with pytest.raises(Exception):
        Draft202012Validator(auth_schema).validate(forged_auth)


def test_r14_1_network_is_denied_without_explicit_policy() -> None:
    environment = _environment()
    endpoint = _endpoint()
    boundary = BackendNetworkBoundary(
        environments=(environment,),
        endpoints=(endpoint,),
        policies=(),
        resolver=lambda _host, _port: ("1.1.1.1",),
    )
    with pytest.raises(BackendBoundaryError, match="denied by default"):
        boundary.authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())


def test_r14_1_exact_endpoint_and_host_allowlists_are_both_required() -> None:
    environment = _environment()
    endpoint = _endpoint()
    wrong_endpoint_policy = BackendNetworkPolicy(
        environment_id=environment.environment_id,
        allowed_endpoint_ids=("endpoint.other",),
        allowed_hosts=(endpoint.host,),
    )
    boundary = BackendNetworkBoundary(
        environments=(environment,),
        endpoints=(endpoint,),
        policies=(wrong_endpoint_policy,),
        resolver=lambda _host, _port: ("1.1.1.1",),
    )
    with pytest.raises(BackendBoundaryError, match="exact allowlist"):
        boundary.authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())

    wrong_host_policy = BackendNetworkPolicy(
        environment_id=environment.environment_id,
        allowed_endpoint_ids=(endpoint.endpoint_id,),
        allowed_hosts=("other.example.com",),
    )
    boundary = BackendNetworkBoundary(
        environments=(environment,),
        endpoints=(endpoint,),
        policies=(wrong_host_policy,),
        resolver=lambda _host, _port: ("1.1.1.1",),
    )
    with pytest.raises(BackendBoundaryError, match="host.*exact allowlist"):
        boundary.authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())


def test_r14_1_production_requires_https_and_disables_redirects() -> None:
    http_endpoint = _endpoint(scheme="http", port=80)
    with pytest.raises(BackendBoundaryError, match="require HTTPS"):
        _boundary(endpoint=http_endpoint).authorize(
            http_endpoint.endpoint_id,
            budget=BackendRuntimeBudget(),
        )

    redirecting = _endpoint(allow_redirects=True)
    with pytest.raises(BackendBoundaryError, match="redirect-following"):
        _boundary(endpoint=redirecting).authorize(
            redirecting.endpoint_id,
            budget=BackendRuntimeBudget(),
        )


def test_r14_1_public_resolution_produces_redacted_canonical_authorization() -> None:
    endpoint = _endpoint()
    budget = BackendRuntimeBudget(max_retries=0)
    authorization = _boundary(endpoint=endpoint, resolved=("8.8.8.8", "1.1.1.1", "1.1.1.1")).authorize(
        endpoint.endpoint_id,
        budget=budget,
    )
    assert authorization.resolved_ips == ("1.1.1.1", "8.8.8.8")
    assert authorization.endpoint_digest == endpoint.digest()
    assert authorization.runtime_budget_digest == budget.digest()
    assert authorization.redirects_allowed is False
    payload = json.dumps(authorization.canonical(), sort_keys=True)
    assert "password" not in payload.lower()
    assert "token" not in payload.lower()
    assert len(authorization.digest()) == 64


@pytest.mark.parametrize(
    "unsafe_ip",
    (
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.10",
        "169.254.169.254",
        "0.0.0.0",
        "224.0.0.1",
        "::1",
        "fe80::1",
        "fc00::1",
    ),
)
def test_r14_1_production_rejects_non_global_and_special_addresses(unsafe_ip: str) -> None:
    endpoint = _endpoint()
    with pytest.raises(BackendBoundaryError):
        _boundary(endpoint=endpoint, resolved=(unsafe_ip,)).authorize(
            endpoint.endpoint_id,
            budget=BackendRuntimeBudget(),
        )


def test_r14_1_mixed_public_and_metadata_resolution_fails_closed() -> None:
    endpoint = _endpoint()
    with pytest.raises(BackendBoundaryError, match="forbidden special-purpose"):
        _boundary(endpoint=endpoint, resolved=("1.1.1.1", "169.254.169.254")).authorize(
            endpoint.endpoint_id,
            budget=BackendRuntimeBudget(),
        )


def test_r14_1_literal_metadata_ip_is_rejected_without_dns() -> None:
    endpoint = _endpoint(host="169.254.169.254")
    calls = 0

    def resolver(_host: str, _port: int) -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        return ("1.1.1.1",)

    policy = BackendNetworkPolicy(
        environment_id="backend.production",
        allowed_endpoint_ids=(endpoint.endpoint_id,),
        allowed_hosts=(endpoint.host,),
    )
    boundary = BackendNetworkBoundary(
        environments=(_environment(),),
        endpoints=(endpoint,),
        policies=(policy,),
        resolver=resolver,
    )
    with pytest.raises(BackendBoundaryError):
        boundary.authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())
    assert calls == 0


def test_r14_1_dns_rebinding_is_rechecked_on_every_authorization() -> None:
    endpoint = _endpoint()
    answers = iter((("1.1.1.1",), ("127.0.0.1",)))

    def resolver(_host: str, _port: int) -> tuple[str, ...]:
        return next(answers)

    policy = BackendNetworkPolicy(
        environment_id="backend.production",
        allowed_endpoint_ids=(endpoint.endpoint_id,),
        allowed_hosts=(endpoint.host,),
    )
    boundary = BackendNetworkBoundary(
        environments=(_environment(),),
        endpoints=(endpoint,),
        policies=(policy,),
        resolver=resolver,
    )
    first = boundary.authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())
    assert first.resolved_ips == ("1.1.1.1",)
    with pytest.raises(BackendBoundaryError, match="loopback"):
        boundary.authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())


def test_r14_1_local_loopback_requires_explicit_permission() -> None:
    environment = _environment(BackendEnvironmentKind.LOCAL, "backend.local")
    endpoint = _endpoint(
        environment_id=environment.environment_id,
        host="127.0.0.1",
        scheme="http",
        port=8080,
    )
    with pytest.raises(BackendBoundaryError, match="requires explicit"):
        _boundary(environment=environment, endpoint=endpoint, resolved=("127.0.0.1",)).authorize(
            endpoint.endpoint_id,
            budget=BackendRuntimeBudget(),
        )

    authorization = _boundary(
        environment=environment,
        endpoint=endpoint,
        resolved=("127.0.0.1",),
        permit_loopback=True,
    ).authorize(endpoint.endpoint_id, budget=BackendRuntimeBudget())
    assert authorization.resolved_ips == ("127.0.0.1",)


def test_r14_1_production_policy_cannot_enable_private_address_exception() -> None:
    environment = _environment()
    endpoint = _endpoint()
    policy = BackendNetworkPolicy(
        environment_id=environment.environment_id,
        allowed_endpoint_ids=(endpoint.endpoint_id,),
        allowed_hosts=(endpoint.host,),
        permit_private=True,
    )
    with pytest.raises(BackendBoundaryError, match="cannot permit"):
        BackendNetworkBoundary(
            environments=(environment,),
            endpoints=(endpoint,),
            policies=(policy,),
            resolver=lambda _host, _port: ("1.1.1.1",),
        )


def test_r14_1_resolver_failure_empty_or_malformed_output_fails_closed() -> None:
    endpoint = _endpoint()
    with pytest.raises(BackendBoundaryError, match="no addresses"):
        _boundary(endpoint=endpoint, resolved=()).authorize(
            endpoint.endpoint_id,
            budget=BackendRuntimeBudget(),
        )
    with pytest.raises(BackendBoundaryError, match="non-IP"):
        _boundary(endpoint=endpoint, resolved=("not-an-ip",)).authorize(
            endpoint.endpoint_id,
            budget=BackendRuntimeBudget(),
        )
