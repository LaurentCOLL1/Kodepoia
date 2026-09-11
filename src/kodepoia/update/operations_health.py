from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from tuf.api.metadata import Metadata

from kodepoia.update.steady_state_refresh import (
    SteadyStateRefreshError,
    evaluate_refresh,
)

HEALTH_FORMAT = "kodepoia-r20-5-update-operations-health"
HEALTH_SCHEMA_VERSION = 1

ROOT_WARNING_SECONDS = 90 * 24 * 60 * 60
ROOT_CRITICAL_SECONDS = 30 * 24 * 60 * 60
TARGETS_WARNING_SECONDS = 90 * 24 * 60 * 60
TARGETS_CRITICAL_SECONDS = 30 * 24 * 60 * 60
ONLINE_WARNING_SECONDS = 36 * 60 * 60
ONLINE_CRITICAL_SECONDS = 24 * 60 * 60
REFRESH_SUCCESS_WARNING_SECONDS = 9 * 60 * 60
REFRESH_SUCCESS_CRITICAL_SECONDS = 18 * 60 * 60

_SEVERITY = {"healthy": 0, "warning": 1, "critical": 2}


@dataclass(frozen=True, slots=True)
class RoleLifetimeHealth:
    role: str
    state: str
    version: int
    expires: str
    remaining_seconds: int
    warning_seconds: int
    critical_seconds: int

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "state": self.state,
            "version": self.version,
            "expires": self.expires,
            "remaining_seconds": self.remaining_seconds,
            "warning_seconds": self.warning_seconds,
            "critical_seconds": self.critical_seconds,
        }


@dataclass(frozen=True, slots=True)
class RefreshWorkflowHealth:
    state: str
    reason: str
    considered_runs: int
    last_success_at: str | None
    last_success_age_seconds: int | None
    latest_run: dict[str, object] | None
    consecutive_failures: int

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "reason": self.reason,
            "considered_runs": self.considered_runs,
            "last_success_at": self.last_success_at,
            "last_success_age_seconds": self.last_success_age_seconds,
            "latest_run": self.latest_run,
            "consecutive_failures": self.consecutive_failures,
        }


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _as_utc(value).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return _as_utc(datetime.fromisoformat(text))
    except ValueError:
        return None


def _state_for_remaining(
    remaining_seconds: int,
    *,
    warning_seconds: int,
    critical_seconds: int,
) -> str:
    if remaining_seconds <= critical_seconds:
        return "critical"
    if remaining_seconds <= warning_seconds:
        return "warning"
    return "healthy"


def _metadata_role_health(
    *,
    role: str,
    data: bytes,
    now: datetime,
    warning_seconds: int,
    critical_seconds: int,
) -> RoleLifetimeHealth:
    metadata = Metadata.from_bytes(data)
    remaining = int((_as_utc(metadata.signed.expires) - now).total_seconds())
    return RoleLifetimeHealth(
        role=role,
        state=_state_for_remaining(
            remaining,
            warning_seconds=warning_seconds,
            critical_seconds=critical_seconds,
        ),
        version=metadata.signed.version,
        expires=_iso(metadata.signed.expires),
        remaining_seconds=remaining,
        warning_seconds=warning_seconds,
        critical_seconds=critical_seconds,
    )


def assess_metadata_health(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    snapshot_bytes: bytes,
    timestamp_bytes: bytes,
    reference_time: datetime,
) -> dict[str, object]:
    """Verify the exact TUF view and classify remaining metadata lifetimes."""

    now = _as_utc(reference_time).replace(microsecond=0)
    try:
        decision = evaluate_refresh(
            root_bytes=root_bytes,
            targets_bytes=targets_bytes,
            snapshot_bytes=snapshot_bytes,
            timestamp_bytes=timestamp_bytes,
            reference_time=now,
        )
    except (SteadyStateRefreshError, ValueError, TypeError) as exc:
        return {
            "state": "critical",
            "verified": False,
            "verification_error": str(exc),
            "roles": {},
            "refresh_required": None,
        }

    roles = {
        "root": _metadata_role_health(
            role="root",
            data=root_bytes,
            now=now,
            warning_seconds=ROOT_WARNING_SECONDS,
            critical_seconds=ROOT_CRITICAL_SECONDS,
        ),
        "targets": _metadata_role_health(
            role="targets",
            data=targets_bytes,
            now=now,
            warning_seconds=TARGETS_WARNING_SECONDS,
            critical_seconds=TARGETS_CRITICAL_SECONDS,
        ),
        "snapshot": _metadata_role_health(
            role="snapshot",
            data=snapshot_bytes,
            now=now,
            warning_seconds=ONLINE_WARNING_SECONDS,
            critical_seconds=ONLINE_CRITICAL_SECONDS,
        ),
        "timestamp": _metadata_role_health(
            role="timestamp",
            data=timestamp_bytes,
            now=now,
            warning_seconds=ONLINE_WARNING_SECONDS,
            critical_seconds=ONLINE_CRITICAL_SECONDS,
        ),
    }
    state = max((item.state for item in roles.values()), key=_SEVERITY.__getitem__)
    return {
        "state": state,
        "verified": True,
        "verification_error": None,
        "roles": {name: item.to_dict() for name, item in roles.items()},
        "refresh_required": decision.refresh_required,
        "refresh_decision": decision.to_dict(),
    }


def _normalized_runs(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    raw: Iterable[Mapping[str, Any]]
    if isinstance(payload, Mapping):
        candidate = payload.get("workflow_runs", [])
        raw = candidate if isinstance(candidate, list) else []
    else:
        raw = payload

    normalized: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        if item.get("event") not in {"schedule", "workflow_dispatch"}:
            continue
        branch = item.get("head_branch")
        if branch not in {None, "main"}:
            continue
        stamp = (
            _parse_iso(item.get("run_started_at"))
            or _parse_iso(item.get("created_at"))
            or _parse_iso(item.get("updated_at"))
        )
        if stamp is None:
            continue
        normalized.append({**dict(item), "_stamp": stamp})
    normalized.sort(key=lambda item: item["_stamp"], reverse=True)
    return normalized


def _public_run(run: Mapping[str, Any]) -> dict[str, object]:
    result: dict[str, object] = {
        "id": run.get("id"),
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "head_sha": run.get("head_sha"),
        "run_started_at": run.get("run_started_at") or run.get("created_at"),
        "updated_at": run.get("updated_at"),
    }
    html_url = run.get("html_url")
    if isinstance(html_url, str) and html_url.startswith("https://github.com/"):
        result["html_url"] = html_url
    return result


def assess_refresh_workflow_health(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    reference_time: datetime,
) -> RefreshWorkflowHealth:
    """Classify whether the six-hour R20.4 production freshness loop is operating."""

    now = _as_utc(reference_time).replace(microsecond=0)
    runs = _normalized_runs(payload)
    if not runs:
        return RefreshWorkflowHealth(
            state="warning",
            reason="no scheduled/manual R20.4 production refresh run is visible yet",
            considered_runs=0,
            last_success_at=None,
            last_success_age_seconds=None,
            latest_run=None,
            consecutive_failures=0,
        )

    latest = runs[0]
    completed = [item for item in runs if item.get("status") == "completed"]
    consecutive_failures = 0
    for item in completed:
        if item.get("conclusion") == "success":
            break
        consecutive_failures += 1

    successes = [
        item
        for item in completed
        if item.get("conclusion") == "success"
    ]
    last_success = successes[0] if successes else None
    last_success_time = None
    if last_success is not None:
        last_success_time = (
            _parse_iso(last_success.get("updated_at"))
            or _parse_iso(last_success.get("run_started_at"))
            or last_success["_stamp"]
        )
    age = (
        int((now - last_success_time).total_seconds())
        if last_success_time is not None
        else None
    )

    state = "healthy"
    reasons: list[str] = []
    if consecutive_failures >= 2:
        state = "critical"
        reasons.append("two or more consecutive completed refresh runs failed")
    elif consecutive_failures == 1:
        state = "warning"
        reasons.append("latest completed refresh run failed")

    if age is None:
        state = "critical"
        reasons.append("no successful R20.4 production refresh run is visible")
    elif age > REFRESH_SUCCESS_CRITICAL_SECONDS:
        state = "critical"
        reasons.append("last successful refresh run is older than 18 hours")
    elif age > REFRESH_SUCCESS_WARNING_SECONDS and state != "critical":
        state = "warning"
        reasons.append("last successful refresh run is older than 9 hours")

    if latest.get("status") in {"queued", "in_progress", "waiting", "pending"}:
        reasons.append("a refresh run is currently active")

    if not reasons:
        reasons.append("scheduled/manual refresh evidence is recent and successful")

    return RefreshWorkflowHealth(
        state=state,
        reason="; ".join(reasons),
        considered_runs=len(runs),
        last_success_at=_iso(last_success_time) if last_success_time else None,
        last_success_age_seconds=age,
        latest_run=_public_run(latest),
        consecutive_failures=consecutive_failures,
    )


def build_operations_health_report(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    snapshot_bytes: bytes,
    timestamp_bytes: bytes,
    workflow_runs: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    reference_time: datetime,
    source_sha: str | None = None,
) -> dict[str, object]:
    """Build secret-free maintainer evidence for R20.5 update operations."""

    now = _as_utc(reference_time).replace(microsecond=0)
    metadata = assess_metadata_health(
        root_bytes=root_bytes,
        targets_bytes=targets_bytes,
        snapshot_bytes=snapshot_bytes,
        timestamp_bytes=timestamp_bytes,
        reference_time=now,
    )
    workflow = assess_refresh_workflow_health(workflow_runs, reference_time=now)
    state = max(
        (str(metadata["state"]), workflow.state),
        key=_SEVERITY.__getitem__,
    )
    return {
        "format": HEALTH_FORMAT,
        "schema_version": HEALTH_SCHEMA_VERSION,
        "reference_time": _iso(now),
        "source_sha": source_sha,
        "state": state,
        "critical": state == "critical",
        "metadata": metadata,
        "refresh_workflow": workflow.to_dict(),
        "policy": {
            "root_warning_seconds": ROOT_WARNING_SECONDS,
            "root_critical_seconds": ROOT_CRITICAL_SECONDS,
            "targets_warning_seconds": TARGETS_WARNING_SECONDS,
            "targets_critical_seconds": TARGETS_CRITICAL_SECONDS,
            "online_warning_seconds": ONLINE_WARNING_SECONDS,
            "online_critical_seconds": ONLINE_CRITICAL_SECONDS,
            "refresh_success_warning_seconds": REFRESH_SUCCESS_WARNING_SECONDS,
            "refresh_success_critical_seconds": REFRESH_SUCCESS_CRITICAL_SECONDS,
        },
        "startup_blocked": False,
        "local_work_blocked": False,
        "expired_metadata_accepted": False,
        "unverifiable_metadata_accepted": False,
        "private_material_in_output": False,
    }


_MESSAGES: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        "offline": (
            "Updates temporarily unavailable",
            "Kodepoia cannot reach the update service right now. "
            "Local work remains available; retry the update check later.",
        ),
        "metadata-expired": (
            "Update service maintenance required",
            "Trusted update metadata is no longer fresh, so Kodepoia will not install "
            "updates until the service is renewed. Local work remains available.",
        ),
        "verification-failed": (
            "Update verification unavailable",
            "Kodepoia could not verify the update metadata and will not install an "
            "unverified update. Local work remains available; retry later.",
        ),
        "channel-unavailable": (
            "Update channel temporarily unavailable",
            "The selected update channel is temporarily unavailable. Local work remains "
            "available; retry the update check later.",
        ),
        "refresh-outage": (
            "Update service is being restored",
            "Automated update-metadata maintenance needs attention. Kodepoia will not "
            "weaken verification; local work remains available.",
        ),
    },
    "fr": {
        "offline": (
            "Mises à jour temporairement indisponibles",
            "Kodepoia ne peut pas joindre le service de mise à jour pour le moment. "
            "Le travail local reste disponible ; réessayez plus tard.",
        ),
        "metadata-expired": (
            "Maintenance du service de mise à jour requise",
            "Les métadonnées de mise à jour fiables ne sont plus assez récentes. "
            "Kodepoia n’installera aucune mise à jour avant leur renouvellement. "
            "Le travail local reste disponible.",
        ),
        "verification-failed": (
            "Vérification des mises à jour indisponible",
            "Kodepoia n’a pas pu vérifier les métadonnées et n’installera aucune mise à "
            "jour non vérifiée. Le travail local reste disponible ; réessayez plus tard.",
        ),
        "channel-unavailable": (
            "Canal de mise à jour temporairement indisponible",
            "Le canal de mise à jour sélectionné est temporairement indisponible. "
            "Le travail local reste disponible ; réessayez plus tard.",
        ),
        "refresh-outage": (
            "Rétablissement du service de mise à jour",
            "La maintenance automatisée des métadonnées de mise à jour nécessite une "
            "intervention. Kodepoia ne réduira pas les contrôles de sécurité ; "
            "le travail local reste disponible.",
        ),
    },
}


def temporary_update_service_message(
    status: str,
    locale: str = "en",
) -> dict[str, object]:
    """Map update-service failures to safe localized, non-blocking user messaging."""

    language = locale.lower().split("-", 1)[0].split("_", 1)[0]
    catalog = _MESSAGES.get(language, _MESSAGES["en"])
    effective_status = status if status in catalog else "verification-failed"
    title, body = catalog[effective_status]
    return {
        "category": "temporary-update-service",
        "status": effective_status,
        "locale": language if language in _MESSAGES else "en",
        "title": title,
        "body": body,
        "retryable": True,
        "blocks_startup": False,
        "local_work_available": True,
        "accepts_expired_metadata": False,
        "accepts_unverifiable_metadata": False,
    }
