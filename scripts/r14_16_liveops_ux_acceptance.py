from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

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
from kodepoia.kodestudio.r14_localization import R14Translator

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class AcceptanceDomain:
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
            "resource": request.resource_id,
            "access_token": "acceptance-token-must-not-leak",
            "database_secret_ref": "kode-secrets://backend/database",
            "nested": {"password": "acceptance-password-must-not-leak"},
        }


def _request(
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


def _raises_policy(service: BackendLiveOpsUXService, request: LiveOpsUXRequest) -> bool:
    try:
        service.execute(request)
    except LiveOpsUXPolicyError:
        return True
    return False


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_evidence(source_sha: str, root: Path) -> dict[str, object]:
    if _SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be exactly 40 lowercase hexadecimal characters")

    domain = AcceptanceDomain()
    service = BackendLiveOpsUXService(domain)
    catalog = service.catalog()
    catalog_json = stable_liveops_json(catalog)

    preview = service.execute(
        _request(
            LiveOpsOperation.REMOTE_CONFIG,
            mode=LiveOpsMode.PREVIEW,
            action="preview",
            resource_id="feature.release-ring",
        )
    )
    preview_json = stable_liveops_json(preview)

    unconfirmed_domain = AcceptanceDomain()
    unconfirmed = BackendLiveOpsUXService(unconfirmed_domain).execute(
        _request(
            LiveOpsOperation.CONTENT,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            resource_id="content.bundle.42",
        )
    )

    denied_domain = AcceptanceDomain(allow=False)
    denied = BackendLiveOpsUXService(denied_domain).execute(
        _request(
            LiveOpsOperation.MIGRATION,
            mode=LiveOpsMode.APPLY,
            action="apply",
            resource_id="migration.2026-08-29",
            confirmed=True,
        )
    )

    production_domain = AcceptanceDomain(allow=True, production=False)
    production_denied = BackendLiveOpsUXService(production_domain).execute(
        _request(
            LiveOpsOperation.CAMPAIGN,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            environment=BackendEnvironmentKind.PRODUCTION,
            resource_id="campaign.autumn",
            confirmed=True,
        )
    )

    authorized_domain = AcceptanceDomain(allow=True, production=True)
    authorized = BackendLiveOpsUXService(authorized_domain).execute(
        _request(
            LiveOpsOperation.REMOTE_CONFIG,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            resource_id="flag.release",
            confirmed=True,
        )
    )
    authorized_json = stable_liveops_json(authorized)

    local_stack_blocked = BackendLiveOpsUXService(AcceptanceDomain()).execute(
        _request(
            LiveOpsOperation.LOCAL_STACK,
            mode=LiveOpsMode.APPLY,
            action="start",
            environment=BackendEnvironmentKind.STAGING,
            confirmed=True,
        )
    )

    fallback = BackendLiveOpsUXService(ProjectLiveOpsDomain(root))
    provider_status = fallback.execute(
        _request(LiveOpsOperation.PROVIDER_CAPABILITY, mode=LiveOpsMode.INSPECT)
    )
    load_report = fallback.execute(_request(LiveOpsOperation.LOAD_REPORT, mode=LiveOpsMode.INSPECT))
    backup_report = fallback.execute(_request(LiveOpsOperation.BACKUP_REPORT, mode=LiveOpsMode.INSPECT))
    fallback_mutation = fallback.execute(
        _request(
            LiveOpsOperation.CONTENT,
            mode=LiveOpsMode.APPLY,
            action="rollout",
            resource_id="content.bundle.43",
            confirmed=True,
        )
    )

    cli_text = (root / "src/kodepoia/backend/r14_cli.py").read_text(encoding="utf-8")
    ui_text = (root / "src/kodepoia/kodestudio/backend_liveops_panel.py").read_text(encoding="utf-8")
    app_text = (root / "src/kodepoia/kodestudio/app.py").read_text(encoding="utf-8")

    forbidden_cli_flags = (
        "--command",
        "--cmd",
        "--shell",
        "--endpoint",
        "--url",
        "--secret",
        "--token",
        "--password",
        "--permission-granted",
    )
    required_ui_ids = (
        "backendLiveOpsPage",
        "r14Environment",
        "r14Operation",
        "r14Action",
        "r14Mode",
        "r14ResourceId",
        "r14ConfirmMutation",
        "r14CatalogButton",
        "r14ExecuteButton",
        "r14StructuredResult",
    )

    raw_service = BackendLiveOpsUXService(AcceptanceDomain())
    checks: dict[str, bool] = {
        "catalog_schema_v1": catalog.get("schema") == "kodepoia.r14.liveops-ux.v1",
        "catalog_has_all_15_operations": len(catalog.get("operations", {})) == 15
        and set(catalog.get("operations", {})) == {item.value for item in LiveOpsOperation},
        "catalog_preview_defaults_frozen": catalog.get("defaults")
        == {
            "migration": "preview",
            "event_replay": "preview",
            "remote_config": "preview",
            "content": "preview",
            "campaign": "preview",
        },
        "catalog_forbids_raw_authority_inputs": {
            "command",
            "endpoint",
            "secret",
            "token",
            "password",
            "dsn",
        }.issubset(set(catalog.get("forbidden_input_fields", []))),
        "preview_uses_typed_domain_port": preview.get("status") == "ok" and len(domain.requests) == 1,
        "preview_output_redacts_token": preview.get("result", {}).get("access_token") == "<redacted>",
        "preview_output_redacts_secret_reference": preview.get("result", {}).get("database_secret_ref")
        == "<secret-ref>",
        "preview_output_redacts_nested_password": preview.get("result", {}).get("nested", {}).get("password")
        == "<redacted>",
        "stable_json_is_deterministic": preview_json == stable_liveops_json(preview)
        and catalog_json == stable_liveops_json(catalog),
        "confirmation_required_before_mutation": unconfirmed.get("status") == "blocked"
        and unconfirmed.get("reason") == "explicit_confirmation_required"
        and not unconfirmed_domain.requests,
        "confirmation_does_not_self_grant_permission": denied.get("status") == "blocked"
        and denied.get("reason") == "domain_permission_denied"
        and not denied_domain.requests,
        "production_requires_separate_authority": production_denied.get("status") == "blocked"
        and production_denied.get("reason") == "production_authority_denied"
        and not production_domain.requests,
        "authorized_mutation_only_via_domain": authorized.get("status") == "ok"
        and len(authorized_domain.requests) == 1
        and authorized.get("authority", {}).get("mutation") is True,
        "authorized_mutation_output_is_redacted": "acceptance-token-must-not-leak" not in authorized_json
        and "acceptance-password-must-not-leak" not in authorized_json,
        "local_stack_mutation_restricted_to_local_test": local_stack_blocked.get("status") == "blocked"
        and local_stack_blocked.get("reason") == "local_stack_mutation_forbidden_outside_local_test",
        "raw_command_field_rejected": _raises_policy(
            raw_service,
            _request(
                LiveOpsOperation.EVENT_REPLAY,
                mode=LiveOpsMode.PREVIEW,
                resource_id="event.batch.1",
                payload={"command": "echo unsafe"},
            ),
        ),
        "raw_endpoint_field_rejected": _raises_policy(
            raw_service,
            _request(
                LiveOpsOperation.EVENT_REPLAY,
                mode=LiveOpsMode.PREVIEW,
                resource_id="event.batch.1",
                payload={"endpoint": "https://example.invalid"},
            ),
        ),
        "nested_token_field_rejected": _raises_policy(
            raw_service,
            _request(
                LiveOpsOperation.EVENT_REPLAY,
                mode=LiveOpsMode.PREVIEW,
                resource_id="event.batch.1",
                payload={"nested": {"token": "unsafe"}},
            ),
        ),
        "endpoint_like_value_rejected": _raises_policy(
            raw_service,
            _request(
                LiveOpsOperation.EVENT_REPLAY,
                mode=LiveOpsMode.PREVIEW,
                resource_id="event.batch.1",
                payload={"value": "https://example.invalid"},
            ),
        ),
        "resource_id_endpoint_escape_rejected": _raises_policy(
            raw_service,
            _request(
                LiveOpsOperation.SAVE_INSPECT,
                mode=LiveOpsMode.INSPECT,
                resource_id="https://example.invalid/save/1",
            ),
        ),
        "action_mode_mismatch_rejected": _raises_policy(
            raw_service,
            _request(LiveOpsOperation.LOCAL_STACK, mode=LiveOpsMode.INSPECT, action="start"),
        ),
        "provider_status_truthfully_unavailable": provider_status.get("status") == "unavailable"
        and provider_status.get("result", {}).get("provider_live_claim") is False,
        "load_report_makes_no_external_load_claim": load_report.get("status") == "unavailable"
        and load_report.get("result", {}).get("external_load_claim") is False,
        "backup_report_makes_no_production_pitr_claim": backup_report.get("status") == "unavailable"
        and backup_report.get("result", {}).get("production_pitr_claim") is False,
        "project_fallback_never_authorizes_mutation": fallback_mutation.get("status") == "blocked"
        and fallback_mutation.get("reason") == "domain_permission_denied",
        "cli_exposes_no_raw_escape_flags": all(flag not in cli_text for flag in forbidden_cli_flags),
        "ui_has_only_structured_governed_controls": all(item in ui_text for item in required_ui_ids)
        and "QLineEdit" in ui_text,
        "ui_is_wired_into_kodestudio": "backend_liveops_panel" in app_text and "r14_service" in app_text,
        "english_localization_available": R14Translator("en").text("nav") == "Backend & LiveOps",
        "french_localization_available": R14Translator("fr").text("nav") == "Backend et LiveOps",
        "pseudo_localization_expands_r14_surface": R14Translator("qps-ploc").text("nav").startswith("⟦")
        and R14Translator("qps-ploc").text("nav").endswith("⟧"),
    }

    passed_count = sum(checks.values())
    status = "pass" if passed_count == len(checks) else "fail"
    return {
        "schema": "kodepoia.r14.liveops-ux-acceptance.v1",
        "source_sha": source_sha,
        "status": status,
        "manual_state": "none",
        "provider_live_claim": False,
        "external_provider_required": False,
        "secrets_exposed": False,
        "raw_command_input_exposed": False,
        "raw_endpoint_input_exposed": False,
        "automatic_production_publish": False,
        "operation_count": len(catalog.get("operations", {})),
        "check_count": len(checks),
        "passed_count": passed_count,
        "checks": checks,
        "digests": {
            "catalog_sha256": _sha256_text(catalog_json),
            "preview_sha256": _sha256_text(preview_json),
            "authorized_mutation_sha256": _sha256_text(authorized_json),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="R14.16 deterministic Backend/LiveOps UX acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve(strict=False)
    evidence = build_evidence(args.source_sha, root)
    destination = (root / args.output).resolve(strict=False)
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise SystemExit("acceptance output must remain inside the repository workspace") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if evidence["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
