from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import BackendServiceKind, canonical_sha256


BACKEND_DNA_SERVICE_KINDS = frozenset(
    {
        BackendServiceKind.AUTH,
        BackendServiceKind.AUTHORITATIVE_SERVER,
        BackendServiceKind.MATCHMAKING,
        BackendServiceKind.CLOUD_SAVE,
        BackendServiceKind.PROGRESSION,
        BackendServiceKind.CATALOG,
        BackendServiceKind.ENTITLEMENT,
        BackendServiceKind.BILLING,
        BackendServiceKind.REMOTE_CONFIG,
        BackendServiceKind.CONTENT_DELIVERY,
        BackendServiceKind.EVENTS,
    }
)

BACKEND_SERVICE_DEPENDENCIES: dict[BackendServiceKind, tuple[BackendServiceKind, ...]] = {
    BackendServiceKind.MATCHMAKING: (BackendServiceKind.AUTHORITATIVE_SERVER,),
    BackendServiceKind.BILLING: (
        BackendServiceKind.CATALOG,
        BackendServiceKind.ENTITLEMENT,
    ),
}


def _service_sort_key(service: BackendServiceKind) -> str:
    return service.value


def _normalize_services(
    services: tuple[BackendServiceKind, ...],
) -> tuple[BackendServiceKind, ...]:
    if not isinstance(services, tuple):
        raise ValueError("backend services must be an immutable tuple")
    for service in services:
        if not isinstance(service, BackendServiceKind):
            raise ValueError("backend services must use BackendServiceKind")
        if service not in BACKEND_DNA_SERVICE_KINDS:
            raise ValueError(
                f"backend service {service.value!r} is not a Project DNA service intent"
            )
    return tuple(sorted(set(services), key=_service_sort_key))


@dataclass(frozen=True, slots=True)
class BackendRuntimeIntent:
    intent_id: str
    service_kind: BackendServiceKind
    dependencies: tuple[BackendServiceKind, ...] = ()

    def __post_init__(self) -> None:
        expected = f"backend.{self.service_kind.value}"
        if self.intent_id != expected:
            raise ValueError("backend runtime intent_id must be derived from service_kind")
        normalized = tuple(sorted(set(self.dependencies), key=_service_sort_key))
        if normalized != self.dependencies:
            raise ValueError("backend runtime dependencies must be unique and sorted")
        if any(item not in BACKEND_DNA_SERVICE_KINDS for item in normalized):
            raise ValueError("backend runtime dependencies must be Project DNA service kinds")

    def canonical(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "service_kind": self.service_kind.value,
            "dependencies": [item.value for item in self.dependencies],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendProjectProfile:
    enabled: bool = False
    services: tuple[BackendServiceKind, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("backend enabled must be boolean")
        normalized = _normalize_services(self.services)
        object.__setattr__(self, "services", normalized)
        self.validate()

    def validate(self) -> None:
        if not self.enabled:
            if self.services:
                raise ValueError("disabled backend profile cannot contain service intents")
            return
        if not self.services:
            raise ValueError("enabled backend profile requires at least one service intent")
        selected = set(self.services)
        for service, dependencies in BACKEND_SERVICE_DEPENDENCIES.items():
            if service not in selected:
                continue
            missing = tuple(item for item in dependencies if item not in selected)
            if missing:
                required = ", ".join(item.value for item in missing)
                raise ValueError(
                    f"backend service {service.value} requires service intent: {required}"
                )

    def canonical(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "services": [item.value for item in self.services],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    def runtime_intents(self) -> tuple[BackendRuntimeIntent, ...]:
        if not self.enabled:
            return ()
        selected = set(self.services)
        intents: list[BackendRuntimeIntent] = []
        for service in self.services:
            dependencies = tuple(
                item
                for item in BACKEND_SERVICE_DEPENDENCIES.get(service, ())
                if item in selected
            )
            intents.append(
                BackendRuntimeIntent(
                    intent_id=f"backend.{service.value}",
                    service_kind=service,
                    dependencies=dependencies,
                )
            )
        return tuple(intents)


def backend_runtime_intents(
    profile: BackendProjectProfile | None,
) -> tuple[BackendRuntimeIntent, ...]:
    if profile is None:
        return ()
    return profile.runtime_intents()


def backend_wizard_questions(
    profile: BackendProjectProfile | None,
    *,
    backend_relevant: bool = False,
) -> tuple[str, ...]:
    if profile is None:
        return ("backend_enabled",) if backend_relevant else ()
    if not profile.enabled:
        return ("backend_enabled",) if backend_relevant else ()

    selected = set(profile.services)
    questions: list[str] = ["backend_enabled", "backend_services"]
    mappings: tuple[tuple[frozenset[BackendServiceKind], str], ...] = (
        (frozenset({BackendServiceKind.AUTH}), "backend_identity"),
        (
            frozenset({BackendServiceKind.AUTHORITATIVE_SERVER}),
            "backend_authoritative_state",
        ),
        (frozenset({BackendServiceKind.MATCHMAKING}), "backend_matchmaking"),
        (frozenset({BackendServiceKind.CLOUD_SAVE}), "backend_cloud_saves"),
        (frozenset({BackendServiceKind.PROGRESSION}), "backend_progression"),
        (
            frozenset(
                {
                    BackendServiceKind.CATALOG,
                    BackendServiceKind.ENTITLEMENT,
                    BackendServiceKind.BILLING,
                }
            ),
            "backend_commerce",
        ),
        (frozenset({BackendServiceKind.REMOTE_CONFIG}), "backend_config_flags"),
        (frozenset({BackendServiceKind.CONTENT_DELIVERY}), "backend_content"),
        (frozenset({BackendServiceKind.EVENTS}), "backend_events"),
    )
    for services, question in mappings:
        if services & selected:
            questions.append(question)
    return tuple(questions)
