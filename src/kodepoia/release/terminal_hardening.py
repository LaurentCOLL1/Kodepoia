from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_CRITICAL_DOMAINS = (
    "v2-regression",
    "security-privacy",
    "workspace-memory-research",
    "model-lab",
    "orchestration",
    "packaged-windows",
    "resilience",
    "updater",
    "release-freeze",
    "ci-evidence",
)


class TerminalHardeningError(ValueError):
    """Raised when terminal V2 hardening evidence is incomplete or inconsistent."""


@dataclass(frozen=True, slots=True)
class TerminalHardeningCheck:
    name: str
    domain: str
    passed: bool
    detail: str
    critical: bool = True

    def __post_init__(self) -> None:
        if not self.name or any(char.isspace() for char in self.name):
            raise TerminalHardeningError("hardening check name must be a non-empty token")
        if self.domain not in REQUIRED_CRITICAL_DOMAINS:
            raise TerminalHardeningError(f"unknown hardening domain: {self.domain}")
        if not isinstance(self.passed, bool):
            raise TerminalHardeningError("hardening check passed must be boolean")
        if not isinstance(self.critical, bool):
            raise TerminalHardeningError("hardening check critical must be boolean")
        if not self.detail.strip():
            raise TerminalHardeningError("hardening check detail must be non-empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "domain": self.domain,
            "passed": self.passed,
            "critical": self.critical,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class TerminalHardeningDecision:
    source_sha: str
    checks: tuple[TerminalHardeningCheck, ...]

    @classmethod
    def from_checks(
        cls,
        source_sha: str,
        checks: tuple[TerminalHardeningCheck, ...] | list[TerminalHardeningCheck],
    ) -> TerminalHardeningDecision:
        return cls(source_sha=source_sha.strip().lower(), checks=tuple(checks))

    def __post_init__(self) -> None:
        if not _SHA_RE.fullmatch(self.source_sha):
            raise TerminalHardeningError("source_sha must be an exact lowercase Git SHA")
        if not self.checks:
            raise TerminalHardeningError("terminal hardening requires checks")

        names = [check.name for check in self.checks]
        if len(names) != len(set(names)):
            raise TerminalHardeningError("terminal hardening check names must be unique")

        domains = {check.domain for check in self.checks}
        missing = set(REQUIRED_CRITICAL_DOMAINS) - domains
        if missing:
            raise TerminalHardeningError(
                "missing terminal hardening domains: " + ", ".join(sorted(missing))
            )

        critical_domains = {check.domain for check in self.checks if check.critical}
        missing_critical = set(REQUIRED_CRITICAL_DOMAINS) - critical_domains
        if missing_critical:
            raise TerminalHardeningError(
                "every terminal hardening domain requires a critical check: "
                + ", ".join(sorted(missing_critical))
            )

    @property
    def failed_checks(self) -> tuple[TerminalHardeningCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    @property
    def critical_vetoes(self) -> tuple[TerminalHardeningCheck, ...]:
        return tuple(check for check in self.failed_checks if check.critical)

    @property
    def passed(self) -> bool:
        return not self.failed_checks

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"

    def domain_summary(self) -> dict[str, dict[str, object]]:
        summary: dict[str, dict[str, object]] = {}
        for domain in REQUIRED_CRITICAL_DOMAINS:
            checks = tuple(check for check in self.checks if check.domain == domain)
            failed = tuple(check for check in checks if not check.passed)
            vetoes = tuple(check for check in failed if check.critical)
            summary[domain] = {
                "passed": len(checks) - len(failed),
                "total": len(checks),
                "failed": [check.name for check in failed],
                "critical_vetoes": [check.name for check in vetoes],
                "status": "PASS" if not failed else "FAIL",
            }
        return summary

    def to_dict(self) -> dict[str, object]:
        ordered = tuple(sorted(self.checks, key=lambda check: (check.domain, check.name)))
        payload: dict[str, object] = {
            "schema_version": 1,
            "subdivision": "V2.6.2",
            "title": "Full V2 integrated regression and adversarial hardening",
            "source_sha": self.source_sha,
            "status": self.status,
            "critical_veto": bool(self.critical_vetoes),
            "critical_vetoes": [check.name for check in sorted(
                self.critical_vetoes, key=lambda check: (check.domain, check.name)
            )],
            "summary": {
                "passed": len(ordered) - len(self.failed_checks),
                "total": len(ordered),
                "failed": len(self.failed_checks),
                "critical_vetoes": len(self.critical_vetoes),
            },
            "domains": self.domain_summary(),
            "checks": [check.to_dict() for check in ordered],
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        payload["evidence_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return payload


__all__ = [
    "REQUIRED_CRITICAL_DOMAINS",
    "TerminalHardeningCheck",
    "TerminalHardeningDecision",
    "TerminalHardeningError",
]
