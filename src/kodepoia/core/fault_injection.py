from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass


FAULT_STAGES = ("prepare", "write", "commit", "verify", "cleanup")


class InjectedFault(RuntimeError):
    """Deterministic, test-scoped fault raised at an explicit fault point."""


@dataclass(frozen=True, slots=True)
class FaultRule:
    component: str
    stage: str
    occurrence: int = 1
    reason: str = "injected fault"

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("Fault component cannot be empty")
        if self.stage not in FAULT_STAGES:
            raise ValueError(f"Unsupported fault stage: {self.stage}")
        if self.occurrence < 1:
            raise ValueError("Fault occurrence must be >= 1")


@dataclass(frozen=True, slots=True)
class FaultEvent:
    component: str
    stage: str
    occurrence: int
    injected: bool
    reason: str | None = None


class DeterministicFaultInjector:
    """Explicit deterministic fault injector for synthetic acceptance drills.

    The injector is inert unless rules are provided. Rules are matched by
    component, stage, and 1-based occurrence. There is intentionally no
    randomness, environment-variable trigger, or production-global state.
    """

    def __init__(self, rules: Iterable[FaultRule] = ()) -> None:
        self._rules = tuple(rules)
        keys = [(rule.component, rule.stage, rule.occurrence) for rule in self._rules]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate deterministic fault rule")
        self._counts: dict[tuple[str, str], int] = {}
        self._events: list[FaultEvent] = []

    @property
    def events(self) -> tuple[FaultEvent, ...]:
        return tuple(self._events)

    def report(self) -> list[dict[str, object]]:
        return [asdict(event) for event in self._events]

    def hit(self, component: str, stage: str) -> None:
        component = component.strip()
        if not component:
            raise ValueError("Fault component cannot be empty")
        if stage not in FAULT_STAGES:
            raise ValueError(f"Unsupported fault stage: {stage}")
        key = (component, stage)
        occurrence = self._counts.get(key, 0) + 1
        self._counts[key] = occurrence
        rule = next(
            (
                item
                for item in self._rules
                if item.component == component
                and item.stage == stage
                and item.occurrence == occurrence
            ),
            None,
        )
        self._events.append(
            FaultEvent(
                component=component,
                stage=stage,
                occurrence=occurrence,
                injected=rule is not None,
                reason=rule.reason if rule else None,
            )
        )
        if rule is not None:
            raise InjectedFault(
                f"{rule.reason}: {component}:{stage} occurrence {occurrence}"
            )
