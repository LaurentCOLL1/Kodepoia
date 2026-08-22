from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.build import redact_sensitive
from kodepoia.quality.health import HealthDimension, HealthMetric, HealthStatus
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1
SPDX_BASELINE = "3.0"
SPDX_SERIALIZATION_VERSION = "3.0.1"
SPDX_JSONLD_CONTEXT = "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{1,191}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DEPENDENCY_NAME_RE = re.compile(r"^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")
_SPDX_ALLOWED_RE = re.compile(r"^[A-Za-z0-9.()+:\- ]+$")
_LICENSE_REF_ONLY_RE = re.compile(
    r"^(?:DocumentRef-[A-Za-z0-9.-]+:)?LicenseRef-[A-Za-z0-9.-]+$"
)


def _parse_timestamp(value: str, *, field_name: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _stable_id(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _ID_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a stable lowercase identifier")
    return normalized


def canonical_python_name(value: str) -> str:
    normalized = re.sub(r"[-_.]+", "-", value.strip()).lower()
    if not normalized or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", normalized):
        raise ValueError("invalid Python package name")
    return normalized


def normalize_spdx_expression(value: str) -> str:
    expression = " ".join(value.strip().split())
    if not expression or not _SPDX_ALLOWED_RE.fullmatch(expression):
        raise ValueError("invalid SPDX expression characters")
    balance = 0
    for character in expression:
        if character == "(":
            balance += 1
        elif character == ")":
            balance -= 1
            if balance < 0:
                raise ValueError("unbalanced SPDX expression parentheses")
    if balance:
        raise ValueError("unbalanced SPDX expression parentheses")
    for operator in ("AND", "OR", "WITH"):
        expression = re.sub(rf"\b{operator}\b", operator, expression, flags=re.IGNORECASE)
    if expression.startswith(("AND ", "OR ", "WITH ")) or expression.endswith(
        (" AND", " OR", " WITH")
    ):
        raise ValueError("SPDX expression cannot start or end with an operator")
    return expression


def _require_sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return normalized


class ComponentKind(StrEnum):
    PROJECT = "project"
    PACKAGE = "package"
    ASSET = "asset"


class ComponentResolution(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"


class IntegrityStatus(StrEnum):
    RECORDED = "recorded"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class LicenseAssertionState(StrEnum):
    SPDX_EXPRESSION = "spdx_expression"
    NOASSERTION = "noassertion"
    NONE = "none"


class LicensePolicyAction(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"
    UNKNOWN = "unknown"


class BomStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class LicenseReportStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class IntegrityEvidence:
    status: IntegrityStatus
    source: str
    algorithm: str = "sha256"
    digest: str = ""
    expected_digest: str = ""

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("integrity evidence requires source provenance")
        if self.algorithm.lower() != "sha256":
            raise ValueError("R6.11 integrity evidence supports SHA-256 only")
        object.__setattr__(self, "algorithm", "sha256")
        if self.status is IntegrityStatus.RECORDED:
            object.__setattr__(self, "digest", _require_sha256(self.digest, field_name="digest"))
            if self.expected_digest:
                raise ValueError("recorded integrity evidence cannot carry expected_digest")
        elif self.status is IntegrityStatus.MISMATCH:
            digest = _require_sha256(self.digest, field_name="digest")
            expected = _require_sha256(self.expected_digest, field_name="expected_digest")
            if digest == expected:
                raise ValueError("mismatch integrity evidence requires different digests")
            object.__setattr__(self, "digest", digest)
            object.__setattr__(self, "expected_digest", expected)
        else:
            if self.digest or self.expected_digest:
                raise ValueError("unknown/not-applicable integrity evidence cannot carry digests")

    def to_dict(self) -> dict[str, str]:
        return {
            "status": self.status.value,
            "source": self.source,
            "algorithm": self.algorithm,
            "digest": self.digest,
            "expected_digest": self.expected_digest,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "IntegrityEvidence":
        return cls(
            status=IntegrityStatus(str(payload["status"])),
            source=str(payload["source"]),
            algorithm=str(payload.get("algorithm", "sha256")),
            digest=str(payload.get("digest", "")),
            expected_digest=str(payload.get("expected_digest", "")),
        )


@dataclass(frozen=True, slots=True)
class LicenseAssertion:
    state: LicenseAssertionState
    evidence_source: str
    expression: str = ""
    rationale: str = ""
    custom_text_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_source.strip():
            raise ValueError("license assertion requires evidence_source")
        if self.state is LicenseAssertionState.SPDX_EXPRESSION:
            object.__setattr__(self, "expression", normalize_spdx_expression(self.expression))
            if self.custom_text_sha256:
                object.__setattr__(
                    self,
                    "custom_text_sha256",
                    _require_sha256(self.custom_text_sha256, field_name="custom_text_sha256"),
                )
                if not _LICENSE_REF_ONLY_RE.fullmatch(self.expression):
                    raise ValueError(
                        "custom license text hash requires one unambiguous LicenseRef expression"
                    )
        else:
            if self.expression.strip() or self.custom_text_sha256:
                raise ValueError("NOASSERTION/NONE license assertion cannot carry expression data")
            if not self.rationale.strip():
                raise ValueError("NOASSERTION/NONE license assertion requires rationale")

    @property
    def spdx_token(self) -> str:
        if self.state is LicenseAssertionState.SPDX_EXPRESSION:
            return self.expression
        if self.state is LicenseAssertionState.NOASSERTION:
            return "NOASSERTION"
        return "NONE"

    def to_dict(self) -> dict[str, str]:
        return {
            "state": self.state.value,
            "evidence_source": self.evidence_source,
            "expression": self.expression,
            "rationale": self.rationale,
            "custom_text_sha256": self.custom_text_sha256,
            "spdx_token": self.spdx_token,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LicenseAssertion":
        assertion = cls(
            state=LicenseAssertionState(str(payload["state"])),
            evidence_source=str(payload["evidence_source"]),
            expression=str(payload.get("expression", "")),
            rationale=str(payload.get("rationale", "")),
            custom_text_sha256=str(payload.get("custom_text_sha256", "")),
        )
        if str(payload.get("spdx_token", "")) != assertion.spdx_token:
            raise ValueError("serialized SPDX token does not match license assertion")
        return assertion


@dataclass(frozen=True, slots=True)
class DependencyRequirement:
    group: str
    requirement: str
    source: str

    def __post_init__(self) -> None:
        if not self.group.strip() or not self.requirement.strip() or not self.source.strip():
            raise ValueError("dependency requirement group/requirement/source cannot be empty")

    def to_dict(self) -> dict[str, str]:
        return {"group": self.group, "requirement": self.requirement, "source": self.source}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DependencyRequirement":
        return cls(str(payload["group"]), str(payload["requirement"]), str(payload["source"]))


@dataclass(frozen=True, slots=True)
class BomComponent:
    id: str
    name: str
    kind: ComponentKind
    resolution: ComponentResolution
    source_locator: str
    provenance_source: str
    concluded_license: LicenseAssertion
    integrity: IntegrityEvidence
    version: str = ""
    purl: str = ""
    source_sha256: str = ""
    declared_license: LicenseAssertion | None = None
    requirements: tuple[DependencyRequirement, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="component id"))
        if not self.name.strip() or not self.source_locator.strip() or not self.provenance_source.strip():
            raise ValueError("component name/source_locator/provenance_source cannot be empty")
        if self.source_sha256:
            object.__setattr__(
                self,
                "source_sha256",
                _require_sha256(self.source_sha256, field_name="source_sha256"),
            )
        if self.resolution is ComponentResolution.RESOLVED and not self.version.strip():
            raise ValueError("resolved component requires exact version")
        if self.resolution in {ComponentResolution.UNRESOLVED, ComponentResolution.NOT_APPLICABLE} and self.version.strip():
            raise ValueError("unresolved/not-applicable component cannot claim an exact version")
        if self.resolution is ComponentResolution.NOT_APPLICABLE:
            if self.integrity.status is not IntegrityStatus.NOT_APPLICABLE:
                raise ValueError("not-applicable component requires not-applicable integrity evidence")
        elif self.integrity.status is IntegrityStatus.NOT_APPLICABLE:
            raise ValueError("applicable component cannot use not-applicable integrity evidence")
        if self.purl and not self.purl.startswith("pkg:"):
            raise ValueError("component purl must start with pkg:")
        requirement_keys = [(item.group, item.requirement, item.source) for item in self.requirements]
        if len(requirement_keys) != len(set(requirement_keys)):
            raise ValueError("component requirements must be unique")
        object.__setattr__(
            self,
            "requirements",
            tuple(sorted(self.requirements, key=lambda x: (x.group, x.requirement))),
        )
        object.__setattr__(self, "details", dict(redact_sensitive(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind.value,
            "resolution": self.resolution.value,
            "version": self.version,
            "purl": self.purl,
            "source_locator": self.source_locator,
            "provenance_source": self.provenance_source,
            "source_sha256": self.source_sha256,
            "integrity": self.integrity.to_dict(),
            "declared_license": self.declared_license.to_dict() if self.declared_license else None,
            "concluded_license": self.concluded_license.to_dict(),
            "requirements": [item.to_dict() for item in self.requirements],
            "details": redact_sensitive(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BomComponent":
        declared = payload.get("declared_license")
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            kind=ComponentKind(str(payload["kind"])),
            resolution=ComponentResolution(str(payload["resolution"])),
            version=str(payload.get("version", "")),
            purl=str(payload.get("purl", "")),
            source_locator=str(payload["source_locator"]),
            provenance_source=str(payload["provenance_source"]),
            source_sha256=str(payload.get("source_sha256", "")),
            integrity=IntegrityEvidence.from_dict(payload["integrity"]),
            declared_license=(LicenseAssertion.from_dict(declared) if declared else None),
            concluded_license=LicenseAssertion.from_dict(payload["concluded_license"]),
            requirements=tuple(
                DependencyRequirement.from_dict(item) for item in payload.get("requirements", [])
            ),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True, slots=True)
class BomReport:
    generated_at: str
    project_name: str
    inventory_scope: str
    inventory_complete: bool
    inventory_review_source: str
    components: tuple[BomComponent, ...]
    status: BomStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION
    spdx_baseline: str = SPDX_BASELINE
    spdx_serialization_version: str = SPDX_SERIALIZATION_VERSION

    @property
    def counts(self) -> dict[str, int]:
        return {
            "components_total": len(self.components),
            "projects": sum(item.kind is ComponentKind.PROJECT for item in self.components),
            "packages": sum(item.kind is ComponentKind.PACKAGE for item in self.components),
            "assets": sum(item.kind is ComponentKind.ASSET for item in self.components),
            "resolved": sum(item.resolution is ComponentResolution.RESOLVED for item in self.components),
            "unresolved": sum(item.resolution is ComponentResolution.UNRESOLVED for item in self.components),
            "not_applicable": sum(
                item.resolution is ComponentResolution.NOT_APPLICABLE for item in self.components
            ),
            "integrity_recorded": sum(
                item.integrity.status is IntegrityStatus.RECORDED for item in self.components
            ),
            "integrity_unknown": sum(
                item.integrity.status is IntegrityStatus.UNKNOWN for item in self.components
            ),
            "integrity_mismatch": sum(
                item.integrity.status is IntegrityStatus.MISMATCH for item in self.components
            ),
            "integrity_not_applicable": sum(
                item.integrity.status is IntegrityStatus.NOT_APPLICABLE for item in self.components
            ),
        }

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(
            f"integrity:{item.id}"
            for item in self.components
            if item.resolution is not ComponentResolution.NOT_APPLICABLE
            and item.integrity.status is IntegrityStatus.MISMATCH
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "inventory_scope": self.inventory_scope,
            "inventory_complete": self.inventory_complete,
            "inventory_review_source": self.inventory_review_source,
            "spdx_baseline": self.spdx_baseline,
            "spdx_serialization_version": self.spdx_serialization_version,
            "status": self.status.value,
            "counts": self.counts,
            "blockers": list(self.blockers),
            "components": [item.to_dict() for item in self.components],
        }

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported BOM report schema version")
        _parse_timestamp(self.generated_at, field_name="generated_at")
        if not self.project_name.strip() or not self.inventory_scope.strip():
            raise ValueError("BOM project_name/inventory_scope cannot be empty")
        if self.inventory_complete and not self.inventory_review_source.strip():
            raise ValueError("complete BOM inventory requires inventory_review_source")
        if self.spdx_baseline != SPDX_BASELINE or self.spdx_serialization_version != SPDX_SERIALIZATION_VERSION:
            raise ValueError("unsupported SPDX baseline/serialization version")
        ids = [item.id for item in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("BOM component ids must be unique")
        expected = KodeBOM.status_for(self.components, inventory_complete=self.inventory_complete)
        if self.status is not expected:
            raise ValueError("BOM report status does not match component evidence")
        if self.evidence_sha256 != _sha256(self._payload()):
            raise ValueError("BOM report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        project_name: str,
        inventory_scope: str,
        components: Iterable[BomComponent],
        *,
        inventory_complete: bool,
        inventory_review_source: str = "",
        generated_at: str | None = None,
    ) -> "BomReport":
        component_tuple = tuple(sorted(components, key=lambda item: item.id))
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        status = KodeBOM.status_for(component_tuple, inventory_complete=inventory_complete)
        provisional = cls(
            timestamp,
            project_name,
            inventory_scope,
            inventory_complete,
            inventory_review_source,
            component_tuple,
            status,
            "",
        )
        report = cls(
            timestamp,
            project_name,
            inventory_scope,
            inventory_complete,
            inventory_review_source,
            component_tuple,
            status,
            _sha256(provisional._payload()),
        )
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BomReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            project_name=str(payload["project_name"]),
            inventory_scope=str(payload["inventory_scope"]),
            inventory_complete=bool(payload.get("inventory_complete", False)),
            inventory_review_source=str(payload.get("inventory_review_source", "")),
            components=tuple(BomComponent.from_dict(item) for item in payload.get("components", [])),
            status=BomStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
            spdx_baseline=str(payload.get("spdx_baseline", "")),
            spdx_serialization_version=str(payload.get("spdx_serialization_version", "")),
        )
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized BOM counts do not match components")
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized BOM blockers do not match components")
        report.validate()
        return report


@dataclass(frozen=True, slots=True)
class LicensePolicyRule:
    expression: str
    action: LicensePolicyAction
    source: str
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "expression", normalize_spdx_expression(self.expression))
        if not self.source.strip():
            raise ValueError("license policy rule requires source provenance")
        if self.action is LicensePolicyAction.UNKNOWN:
            raise ValueError("explicit license policy rule cannot use UNKNOWN action")

    def to_dict(self) -> dict[str, str]:
        return {
            "expression": self.expression,
            "action": self.action.value,
            "source": self.source,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LicensePolicyRule":
        return cls(
            expression=str(payload["expression"]),
            action=LicensePolicyAction(str(payload["action"])),
            source=str(payload["source"]),
            rationale=str(payload.get("rationale", "")),
        )


@dataclass(frozen=True, slots=True)
class LicensePolicy:
    name: str
    rules: tuple[LicensePolicyRule, ...] = ()
    default_action: LicensePolicyAction = LicensePolicyAction.UNKNOWN

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("license policy name cannot be empty")
        if self.default_action is LicensePolicyAction.ALLOW:
            raise ValueError("license policy cannot silently allow unmatched expressions")
        expressions = [item.expression for item in self.rules]
        if len(expressions) != len(set(expressions)):
            raise ValueError("license policy expressions must be unique")
        object.__setattr__(self, "rules", tuple(sorted(self.rules, key=lambda item: item.expression)))

    @property
    def fingerprint(self) -> str:
        payload = {
            "name": self.name,
            "default_action": self.default_action.value,
            "rules": [item.to_dict() for item in self.rules],
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

    def evaluate(self, assertion: LicenseAssertion) -> tuple[LicensePolicyAction, str]:
        if assertion.state is not LicenseAssertionState.SPDX_EXPRESSION:
            return LicensePolicyAction.UNKNOWN, "known-unknown license assertion"
        for rule in self.rules:
            if rule.expression == assertion.expression:
                return rule.action, rule.source
        return self.default_action, "policy default"


@dataclass(frozen=True, slots=True)
class LicenseDecision:
    component_id: str
    license_token: str
    action: LicensePolicyAction
    policy_source: str
    evidence_source: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "component_id",
            _stable_id(self.component_id, field_name="decision component id"),
        )
        if not self.license_token.strip() or not self.policy_source.strip() or not self.evidence_source.strip():
            raise ValueError("license decision token/policy_source/evidence_source cannot be empty")

    @property
    def blocking(self) -> bool:
        return self.action is LicensePolicyAction.DENY

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "license_token": self.license_token,
            "action": self.action.value,
            "policy_source": self.policy_source,
            "evidence_source": self.evidence_source,
            "blocking": self.blocking,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LicenseDecision":
        decision = cls(
            component_id=str(payload["component_id"]),
            license_token=str(payload["license_token"]),
            action=LicensePolicyAction(str(payload["action"])),
            policy_source=str(payload["policy_source"]),
            evidence_source=str(payload["evidence_source"]),
        )
        if bool(payload.get("blocking", False)) is not decision.blocking:
            raise ValueError("serialized license blocker does not match decision")
        return decision


@dataclass(frozen=True, slots=True)
class LicenseReport:
    generated_at: str
    project_name: str
    bom_evidence_sha256: str
    inventory_complete: bool
    inventory_review_source: str
    policy_name: str
    policy_fingerprint: str
    decisions: tuple[LicenseDecision, ...]
    status: LicenseReportStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def counts(self) -> dict[str, int]:
        return {
            "components_total": len(self.decisions),
            "allow": sum(item.action is LicensePolicyAction.ALLOW for item in self.decisions),
            "warn": sum(item.action is LicensePolicyAction.WARN for item in self.decisions),
            "deny": sum(item.action is LicensePolicyAction.DENY for item in self.decisions),
            "unknown": sum(item.action is LicensePolicyAction.UNKNOWN for item in self.decisions),
        }

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(f"license:{item.component_id}" for item in self.decisions if item.blocking)

    @property
    def score(self) -> float | None:
        if not self.decisions:
            return None
        weights = {
            LicensePolicyAction.ALLOW: 100.0,
            LicensePolicyAction.WARN: 70.0,
            LicensePolicyAction.UNKNOWN: 40.0,
            LicensePolicyAction.DENY: 0.0,
        }
        score = sum(weights[item.action] for item in self.decisions) / len(self.decisions)
        if not self.inventory_complete:
            score *= 0.9
        return round(score, 2)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "bom_evidence_sha256": self.bom_evidence_sha256,
            "inventory_complete": self.inventory_complete,
            "inventory_review_source": self.inventory_review_source,
            "policy_name": self.policy_name,
            "policy_fingerprint": self.policy_fingerprint,
            "status": self.status.value,
            "score": self.score,
            "counts": self.counts,
            "blockers": list(self.blockers),
            "decisions": [item.to_dict() for item in self.decisions],
        }

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported license report schema version")
        _parse_timestamp(self.generated_at, field_name="generated_at")
        _require_sha256(self.bom_evidence_sha256, field_name="bom_evidence_sha256")
        _require_sha256(self.policy_fingerprint, field_name="policy_fingerprint")
        if self.inventory_complete and not self.inventory_review_source.strip():
            raise ValueError("complete license inventory requires review provenance")
        ids = [item.component_id for item in self.decisions]
        if len(ids) != len(set(ids)):
            raise ValueError("license decision component ids must be unique")
        expected = KodeLicense.status_for(self.decisions, inventory_complete=self.inventory_complete)
        if self.status is not expected:
            raise ValueError("license report status does not match decisions")
        if self.evidence_sha256 != _sha256(self._payload()):
            raise ValueError("license report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        bom: BomReport,
        policy: LicensePolicy,
        *,
        generated_at: str | None = None,
    ) -> "LicenseReport":
        bom.validate()
        decisions: list[LicenseDecision] = []
        for item in bom.components:
            if item.resolution is ComponentResolution.NOT_APPLICABLE:
                continue
            action, policy_source = policy.evaluate(item.concluded_license)
            decisions.append(
                LicenseDecision(
                    component_id=item.id,
                    license_token=item.concluded_license.spdx_token,
                    action=action,
                    policy_source=policy_source,
                    evidence_source=item.concluded_license.evidence_source,
                )
            )
        decision_tuple = tuple(decisions)
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        status = KodeLicense.status_for(decision_tuple, inventory_complete=bom.inventory_complete)
        provisional = cls(
            timestamp,
            bom.project_name,
            bom.evidence_sha256,
            bom.inventory_complete,
            bom.inventory_review_source,
            policy.name,
            policy.fingerprint,
            decision_tuple,
            status,
            "",
        )
        report = cls(
            timestamp,
            bom.project_name,
            bom.evidence_sha256,
            bom.inventory_complete,
            bom.inventory_review_source,
            policy.name,
            policy.fingerprint,
            decision_tuple,
            status,
            _sha256(provisional._payload()),
        )
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LicenseReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            project_name=str(payload["project_name"]),
            bom_evidence_sha256=str(payload["bom_evidence_sha256"]),
            inventory_complete=bool(payload.get("inventory_complete", False)),
            inventory_review_source=str(payload.get("inventory_review_source", "")),
            policy_name=str(payload["policy_name"]),
            policy_fingerprint=str(payload["policy_fingerprint"]),
            decisions=tuple(LicenseDecision.from_dict(item) for item in payload.get("decisions", [])),
            status=LicenseReportStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized license counts do not match decisions")
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized license blockers do not match decisions")
        if payload.get("score") != report.score:
            raise ValueError("serialized license score does not match decisions")
        report.validate()
        return report


class KodeBOM:
    @staticmethod
    def status_for(
        components: Iterable[BomComponent], *, inventory_complete: bool
    ) -> BomStatus:
        values = tuple(components)
        applicable = tuple(
            item for item in values if item.resolution is not ComponentResolution.NOT_APPLICABLE
        )
        if not applicable:
            return BomStatus.UNKNOWN
        if any(item.integrity.status is IntegrityStatus.MISMATCH for item in applicable):
            return BomStatus.FAIL
        if not inventory_complete:
            return BomStatus.WARN
        if any(
            item.resolution is ComponentResolution.UNRESOLVED
            or item.integrity.status is not IntegrityStatus.RECORDED
            for item in applicable
        ):
            return BomStatus.WARN
        return BomStatus.PASS

    @staticmethod
    def from_pyproject(
        project_root: str | Path,
        *,
        project_license: LicenseAssertion | None = None,
        generated_at: str | None = None,
    ) -> BomReport:
        root = Path(project_root).resolve(strict=False)
        boundary = WorkspaceBoundary(root)
        pyproject = boundary.resolve("pyproject.toml", must_exist=True)
        raw = pyproject.read_bytes()
        parsed = tomllib.loads(raw.decode("utf-8"))
        project = dict(parsed.get("project") or {})
        name = str(project.get("name", "")).strip()
        version = str(project.get("version", "")).strip()
        if not name or not version:
            raise ValueError("pyproject project name/version are required for BOM generation")
        manifest_hash = _sha256_bytes(raw)
        unresolved_project_license = LicenseAssertion(
            state=LicenseAssertionState.NOASSERTION,
            evidence_source="pyproject.toml",
            rationale="Project license metadata was not converted into an SPDX expression automatically.",
        )
        concluded = project_license or unresolved_project_license
        project_component = BomComponent(
            id=f"project:{canonical_python_name(name)}",
            name=name,
            kind=ComponentKind.PROJECT,
            resolution=ComponentResolution.RESOLVED,
            version=version,
            source_locator="pyproject.toml",
            provenance_source="pyproject project metadata",
            source_sha256=manifest_hash,
            integrity=IntegrityEvidence(
                status=IntegrityStatus.RECORDED,
                source="pyproject.toml content digest",
                digest=manifest_hash,
            ),
            declared_license=project_license,
            concluded_license=concluded,
        )

        grouped: dict[str, list[DependencyRequirement]] = {}

        def collect(requirements: Iterable[Any], group: str) -> None:
            for raw_requirement in requirements:
                requirement = str(raw_requirement).strip()
                match = _DEPENDENCY_NAME_RE.match(requirement)
                if not match:
                    raise ValueError(f"cannot identify dependency name: {requirement}")
                package = canonical_python_name(match.group(1))
                grouped.setdefault(package, []).append(
                    DependencyRequirement(group, requirement, "pyproject.toml")
                )

        collect((parsed.get("build-system") or {}).get("requires", []), "build")
        collect(project.get("dependencies", []), "runtime")
        for group_name, requirements in sorted((project.get("optional-dependencies") or {}).items()):
            collect(requirements, f"optional:{group_name}")

        components: list[BomComponent] = [project_component]
        for package_name, requirements in sorted(grouped.items()):
            components.append(
                BomComponent(
                    id=f"python:{package_name}",
                    name=package_name,
                    kind=ComponentKind.PACKAGE,
                    resolution=ComponentResolution.UNRESOLVED,
                    purl=f"pkg:pypi/{package_name}",
                    source_locator="pyproject.toml",
                    provenance_source="declared Python dependency requirement",
                    source_sha256=manifest_hash,
                    integrity=IntegrityEvidence(
                        status=IntegrityStatus.UNKNOWN,
                        source="no exact resolved artifact/hash in pyproject.toml",
                    ),
                    concluded_license=LicenseAssertion(
                        state=LicenseAssertionState.NOASSERTION,
                        evidence_source="pyproject.toml",
                        rationale=(
                            "Dependency range is unresolved; no exact package license is inferred from "
                            "name, range, website or current external metadata."
                        ),
                    ),
                    requirements=tuple(requirements),
                )
            )
        return BomReport.build(
            name,
            "python-project-metadata",
            components,
            inventory_complete=True,
            inventory_review_source="KodeBOM deterministic pyproject dependency-section parser",
            generated_at=generated_at,
        )

    @staticmethod
    def spdx_compatibility_view(report: BomReport) -> dict[str, Any]:
        """Return an SPDX 3.0-family normalization view, not a conformance claim."""

        report.validate()
        applicable = [
            item for item in report.components if item.resolution is not ComponentResolution.NOT_APPLICABLE
        ]
        return {
            "spdx_baseline": report.spdx_baseline,
            "spdx_serialization_version": report.spdx_serialization_version,
            "jsonld_context": SPDX_JSONLD_CONTEXT,
            "document_name": f"{report.project_name}-bom",
            "bom_evidence_sha256": report.evidence_sha256,
            "packages": [
                {
                    "id": item.id,
                    "name": item.name,
                    "package_version": item.version or "NOASSERTION",
                    "package_url": item.purl or "NOASSERTION",
                    "declared_license": (
                        item.declared_license.spdx_token if item.declared_license else "NOASSERTION"
                    ),
                    "concluded_license": item.concluded_license.spdx_token,
                    "integrity": item.integrity.to_dict(),
                }
                for item in applicable
            ],
            "not_applicable_component_ids": [
                item.id
                for item in report.components
                if item.resolution is ComponentResolution.NOT_APPLICABLE
            ],
            "conformance_claim": False,
        }

    @staticmethod
    def to_dependencies_health_metric(report: BomReport) -> HealthMetric:
        report.validate()
        packages = [
            item
            for item in report.components
            if item.kind is ComponentKind.PACKAGE
            and item.resolution is not ComponentResolution.NOT_APPLICABLE
        ]
        if not packages:
            return HealthMetric(
                dimension=HealthDimension.DEPENDENCIES,
                status=HealthStatus.UNKNOWN,
                summary="No applicable package dependency evidence is available",
                source="KodeBOM",
                details={"bom_evidence_sha256": report.evidence_sha256},
            )
        package_status = KodeBOM.status_for(packages, inventory_complete=report.inventory_complete)
        status_map = {
            BomStatus.PASS: HealthStatus.PASS,
            BomStatus.WARN: HealthStatus.WARN,
            BomStatus.FAIL: HealthStatus.FAIL,
            BomStatus.UNKNOWN: HealthStatus.UNKNOWN,
        }
        status = status_map[package_status]
        if status is HealthStatus.UNKNOWN:
            return HealthMetric(
                dimension=HealthDimension.DEPENDENCIES,
                status=status,
                summary="Dependency BOM evidence is unknown",
                source="KodeBOM",
                details={"bom_evidence_sha256": report.evidence_sha256},
            )
        weights = []
        for item in packages:
            if item.integrity.status is IntegrityStatus.MISMATCH:
                weights.append(0.0)
            elif (
                item.resolution is ComponentResolution.RESOLVED
                and item.integrity.status is IntegrityStatus.RECORDED
            ):
                weights.append(100.0)
            elif item.resolution is ComponentResolution.RESOLVED:
                weights.append(70.0)
            else:
                weights.append(40.0)
        score = sum(weights) / len(weights)
        if not report.inventory_complete:
            score *= 0.9
        return HealthMetric(
            dimension=HealthDimension.DEPENDENCIES,
            status=status,
            score=round(score, 2),
            summary=(
                f"{sum(item.resolution is ComponentResolution.RESOLVED for item in packages)} resolved "
                f"and {sum(item.resolution is ComponentResolution.UNRESOLVED for item in packages)} "
                "unresolved applicable package dependency component(s)"
            ),
            source="KodeBOM",
            blocking=any(item.integrity.status is IntegrityStatus.MISMATCH for item in packages),
            details={
                "counts": report.counts,
                "blockers": list(report.blockers),
                "inventory_complete": report.inventory_complete,
                "bom_evidence_sha256": report.evidence_sha256,
            },
        )

    @staticmethod
    def to_test_cases(report: BomReport) -> tuple[TestCaseResult, ...]:
        report.validate()
        cases: list[TestCaseResult] = []
        for item in report.components:
            if item.resolution is ComponentResolution.NOT_APPLICABLE:
                status = TestCaseStatus.SKIP
            elif item.integrity.status is IntegrityStatus.MISMATCH:
                status = TestCaseStatus.FAIL
            elif (
                item.resolution is ComponentResolution.RESOLVED
                and item.integrity.status is IntegrityStatus.RECORDED
            ):
                status = TestCaseStatus.PASS
            else:
                status = TestCaseStatus.SKIP
            cases.append(
                TestCaseResult(
                    id=f"bom:{item.id}",
                    status=status,
                    duration_s=0.0,
                    message=f"BOM component {item.name}",
                    source="KodeBOM",
                    details={
                        "resolution": item.resolution.value,
                        "integrity": item.integrity.status.value,
                        "purl": item.purl,
                    },
                )
            )
        return tuple(cases)


class KodeLicense:
    @staticmethod
    def status_for(
        decisions: Iterable[LicenseDecision], *, inventory_complete: bool
    ) -> LicenseReportStatus:
        values = tuple(decisions)
        if not values:
            return LicenseReportStatus.UNKNOWN
        if any(item.action is LicensePolicyAction.DENY for item in values):
            return LicenseReportStatus.FAIL
        if not inventory_complete or any(
            item.action in {LicensePolicyAction.WARN, LicensePolicyAction.UNKNOWN} for item in values
        ):
            return LicenseReportStatus.WARN
        return LicenseReportStatus.PASS

    @staticmethod
    def to_health_metric(report: LicenseReport) -> HealthMetric:
        report.validate()
        if report.status is LicenseReportStatus.UNKNOWN:
            return HealthMetric(
                dimension=HealthDimension.LICENSES,
                status=HealthStatus.UNKNOWN,
                summary="No measured license policy evidence is available",
                source="KodeLicense",
                details={"license_evidence_sha256": report.evidence_sha256},
            )
        status_map = {
            LicenseReportStatus.PASS: HealthStatus.PASS,
            LicenseReportStatus.WARN: HealthStatus.WARN,
            LicenseReportStatus.FAIL: HealthStatus.FAIL,
        }
        if report.score is None:
            raise ValueError("measured license report requires score")
        return HealthMetric(
            dimension=HealthDimension.LICENSES,
            status=status_map[report.status],
            score=report.score,
            summary=(
                f"{report.counts['allow']} allowed, {report.counts['warn']} warned, "
                f"{report.counts['deny']} denied, {report.counts['unknown']} unknown license decision(s)"
            ),
            source="KodeLicense",
            blocking=bool(report.blockers),
            details={
                "counts": report.counts,
                "blockers": list(report.blockers),
                "policy_name": report.policy_name,
                "policy_fingerprint": report.policy_fingerprint,
                "bom_evidence_sha256": report.bom_evidence_sha256,
                "license_evidence_sha256": report.evidence_sha256,
            },
        )

    @staticmethod
    def to_test_cases(report: LicenseReport) -> tuple[TestCaseResult, ...]:
        report.validate()
        status_map = {
            LicensePolicyAction.ALLOW: TestCaseStatus.PASS,
            LicensePolicyAction.DENY: TestCaseStatus.FAIL,
            LicensePolicyAction.WARN: TestCaseStatus.SKIP,
            LicensePolicyAction.UNKNOWN: TestCaseStatus.SKIP,
        }
        return tuple(
            TestCaseResult(
                id=f"license:{item.component_id}",
                status=status_map[item.action],
                duration_s=0.0,
                message=f"License policy decision for {item.component_id}: {item.license_token}",
                source="KodeLicense",
                details={
                    "action": item.action.value,
                    "policy_source": item.policy_source,
                    "blocking": item.blocking,
                },
            )
            for item in report.decisions
        )


class BomStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.root = self.boundary.resolve(".kodepoia/bom", must_exist=False)

    def save(self, report: BomReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.root.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", report.project_name).strip(".-") or "project"
        latest = self.boundary.resolve(f".kodepoia/bom/{safe}-latest.json")
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(f".kodepoia/bom/bom-{safe}-{stamp}.json")
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, project_name: str) -> BomReport:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", project_name).strip(".-") or "project"
        path = self.boundary.resolve(f".kodepoia/bom/{safe}-latest.json", must_exist=True)
        return BomReport.from_dict(json.loads(path.read_text(encoding="utf-8")))


class LicenseStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.root = self.boundary.resolve(".kodepoia/licenses", must_exist=False)

    def save(self, report: LicenseReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.root.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", report.project_name).strip(".-") or "project"
        latest = self.boundary.resolve(f".kodepoia/licenses/{safe}-latest.json")
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(f".kodepoia/licenses/licenses-{safe}-{stamp}.json")
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, project_name: str) -> LicenseReport:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", project_name).strip(".-") or "project"
        path = self.boundary.resolve(f".kodepoia/licenses/{safe}-latest.json", must_exist=True)
        return LicenseReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
