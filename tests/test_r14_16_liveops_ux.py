from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.backend.contracts import BackendEnvironmentKind
from kodepoia.backend.liveops_ux import (
    BackendLiveOpsUXService,
    LiveOpsMode,
    LiveOpsOperation,
    LiveOpsUXPolicyError,
    LiveOpsUXRequest,
    ProjectLiveOpsDomain,
    stable_liveops_json,
)


class FixtureDomain:
    def __init__(self, *, allow: bool = True, production: bool = False) -> None:
        self.allow = allow
        self.production = production
        self.requests: list[LiveOpsUXRequest] = []

    def authorize(self, request: LiveOpsUXRequest) -> bool:
        return self.allow

    def authorize_production(self, request: LiveOpsUXRequest) -> bool:
        return self.production

    def invoke(self, request: LiveOpsUXRequest) -> dict[str, object]:
        self.requests.append(request)
        return {
            "status": "ok",
            "echo": request.resource_id,
            "access_token": "must-not-leak",
            "database_secret_ref": "kode-secrets://backend/database",
            "nested": {"password": "must-not-leak"},
        }


def request(
    operation: LiveOpsOperation,
    *,
    mode: LiveOpsMode,
    action: str = "show",
    environment: BackendEnvironmentKind = BackendEnvironmentKind.LOCAL,
    resource_id: str | None = None,
    confirmed: bool = False,
    payload: dict[str, object] | None = None,
) -> LiveOpsUXRequest:
    return LiveOpsUXRequest(
        operation=operation,
        environment=environment,
        mode=mode,
        action=action,
        resource_id=resource_id,
        confirmed=confirmed,
        payload=payload or {},
    )


def test_catalog_freezes_preview_defaults_and_forbidden_raw_inputs() -> None:
    catalog = BackendLiveOpsUXService(FixtureDomain()).catalog()
    assert catalog["schema"] == "kodepoia.r14.liveops-ux.v1"
    assert catalog["defaults"] == {
        "migration": "preview",
        "event_replay": "preview",
        "remote_config": "preview",
        "content": "preview",
        "campaign": "preview",
    }
    forbidden = set(catalog["forbidden_input_fields"])
    assert {"command", "endpoint", "secret", "token", "password", "dsn"} <= forbidden


def test_preview_delegates_through_typed_domain_port_and_redacts_output() -> None:
    domain = FixtureDomain()
    service = BackendLiveOpsUXService(domain)
    payload = service.execute(
        request(
            LiveOpsOperation.REMOTE_CONFIG,
            mode=LiveOpsMode.PREVIEW,
            action="preview",
            resource_id="feature.release-ring",
        )
    )
    assert payload["status"] == "ok"
    assert len(domain.requests) == 1
    result = payload["result"]
    assert result["access_token"] == "<redacted>"
    assert result["database_secret_ref"] == "<secret-ref>"
    assert result["nested"]["password"] == "<redacted>"
    rendered = stable_liveops_json(payload)
    assert "must-not-leak" not in rendered
    assert rendered == stable_liveops_json(payload)


def test_mutation_requires_confirmation_before_domain_authorization() -> None:
    domain = FixtureDomain()
    service = BackendLiveOpsUXService(domain)
    payload = service.execute(
        request(
            LiveOpsOperation.CONTENT,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            resource_id="content.bundle.42",
        )
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "explicit_confirmation_required"
    assert domain.requests == []


def test_confirmed_mutation_cannot_self_grant_domain_permission() -> None:
    domain = FixtureDomain(allow=False)
    service = BackendLiveOpsUXService(domain)
    payload = service.execute(
        request(
            LiveOpsOperation.MIGRATION,
            mode=LiveOpsMode.APPLY,
            action="apply",
            resource_id="migration.2026-08-29",
            confirmed=True,
        )
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "domain_permission_denied"
    assert domain.requests == []


def test_production_mutation_requires_separate_authoritative_permission() -> None:
    domain = FixtureDomain(allow=True, production=False)
    service = BackendLiveOpsUXService(domain)
    payload = service.execute(
        request(
            LiveOpsOperation.CAMPAIGN,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            environment=BackendEnvironmentKind.PRODUCTION,
            resource_id="campaign.autumn",
            confirmed=True,
        )
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "production_authority_denied"
    assert domain.requests == []


def test_local_stack_start_stop_are_forbidden_outside_local_or_test() -> None:
    service = BackendLiveOpsUXService(FixtureDomain())
    payload = service.execute(
        request(
            LiveOpsOperation.LOCAL_STACK,
            mode=LiveOpsMode.APPLY,
            action="start",
            environment=BackendEnvironmentKind.STAGING,
            confirmed=True,
        )
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "local_stack_mutation_forbidden_outside_local_test"


@pytest.mark.parametrize(
    "payload",
    [
        {"command": "rm -rf ."},
        {"endpoint": "https://example.invalid"},
        {"nested": {"token": "abc"}},
        {"value": "https://example.invalid"},
    ],
)
def test_raw_command_endpoint_and_secret_inputs_are_rejected(payload: dict[str, object]) -> None:
    service = BackendLiveOpsUXService(FixtureDomain())
    with pytest.raises(LiveOpsUXPolicyError):
        service.execute(
            request(
                LiveOpsOperation.EVENT_REPLAY,
                mode=LiveOpsMode.PREVIEW,
                resource_id="event.batch.1",
                payload=payload,
            )
        )


def test_resource_id_cannot_be_used_as_endpoint_escape_hatch() -> None:
    service = BackendLiveOpsUXService(FixtureDomain())
    with pytest.raises(LiveOpsUXPolicyError):
        service.execute(
            request(
                LiveOpsOperation.SAVE_INSPECT,
                mode=LiveOpsMode.INSPECT,
                resource_id="https://example.invalid/save/1",
            )
        )


def test_action_mode_pairs_are_not_interchangeable() -> None:
    service = BackendLiveOpsUXService(FixtureDomain())
    with pytest.raises(LiveOpsUXPolicyError):
        service.execute(
            request(
                LiveOpsOperation.LOCAL_STACK,
                mode=LiveOpsMode.INSPECT,
                action="start",
            )
        )
    with pytest.raises(LiveOpsUXPolicyError):
        service.execute(
            request(
                LiveOpsOperation.MIGRATION,
                mode=LiveOpsMode.APPLY,
                action="plan",
                resource_id="migration.1",
                confirmed=True,
            )
        )


def test_project_fallback_reports_provider_unavailable_without_live_claim(tmp_path: Path) -> None:
    service = BackendLiveOpsUXService(ProjectLiveOpsDomain(tmp_path))
    payload = service.execute(
        request(
            LiveOpsOperation.PROVIDER_CAPABILITY,
            mode=LiveOpsMode.INSPECT,
        )
    )
    assert payload["status"] == "unavailable"
    assert payload["result"]["provider_live_claim"] is False


def test_project_fallback_never_authorizes_mutation_from_confirmation_alone(tmp_path: Path) -> None:
    service = BackendLiveOpsUXService.for_project(tmp_path)
    payload = service.execute(
        request(
            LiveOpsOperation.REMOTE_CONFIG,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            resource_id="flag.release",
            confirmed=True,
        )
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "domain_permission_denied"
