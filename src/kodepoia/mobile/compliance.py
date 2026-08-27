from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlparse

from .contracts import MobilePlatform, canonical_sha256

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_STABLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_REGION_RE = re.compile(r"^(?:GLOBAL|[A-Z]{2})$")
_FACT_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")
_MAX_RULES = 512
_MAX_FACTS = 512
_MAX_SDKS = 256
_MAX_SET_ITEMS = 256
_MAX_TEXT = 2048


class ComplianceProvider(StrEnum):
    GOOGLE_PLAY = "GOOGLE_PLAY"
    APPLE_APP_STORE = "APPLE_APP_STORE"


class ComplianceRuleOperator(StrEnum):
    PRESENT = "PRESENT"
    TRUE = "TRUE"
    MIN_INTEGER = "MIN_INTEGER"
    EQUALS = "EQUALS"
    CONTAINS_ALL = "CONTAINS_ALL"


class ComplianceRuleCurrentness(StrEnum):
    CURRENT = "CURRENT"
    FUTURE = "FUTURE"
    EXPIRED = "EXPIRED"
    STALE = "STALE"
    UNOFFICIAL = "UNOFFICIAL"


class ComplianceSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


class ComplianceFindingStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_CURRENT = "NOT_CURRENT"
    NEEDS_ACCOUNT_CONFIRMATION = "NEEDS_ACCOUNT_CONFIRMATION"
    CONFLICT = "CONFLICT"


class StoreComplianceState(StrEnum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    BLOCKED = "BLOCKED"
    INDETERMINATE = "INDETERMINATE"


def _iso(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _stable(value: str, field: str) -> str:
    if not isinstance(value, str) or _STABLE_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _sha(value: str, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256")
    return value


def _bounded_text(value: str, field: str, maximum: int = _MAX_TEXT) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or "\x00" in value
        or len(value) > maximum
    ):
        raise ValueError(f"{field} must be non-empty bounded text")
    return value


def _official_hosts(provider: ComplianceProvider) -> frozenset[str]:
    if provider is ComplianceProvider.GOOGLE_PLAY:
        return frozenset({"support.google.com", "developer.android.com"})
    return frozenset({"developer.apple.com"})


def _validate_https_source(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("source_url must be HTTPS")
    return value


def _canonical_fact_value(value: object) -> object:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if not -(2**31) <= value <= 2**31 - 1:
            raise ValueError("integer fact outside bounded range")
        return value
    if isinstance(value, str):
        if "\x00" in value or len(value) > _MAX_TEXT:
            raise ValueError("text fact outside bounded range")
        return value
    if isinstance(value, (tuple, list, frozenset, set)):
        items: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item or "\x00" in item or len(item) > 256:
                raise ValueError("set fact items must be bounded strings")
            items.append(item)
        if len(items) > _MAX_SET_ITEMS:
            raise ValueError("set fact contains too many items")
        return tuple(sorted(set(items)))
    raise ValueError("unsupported compliance fact value")


@dataclass(frozen=True, slots=True)
class ComplianceScope:
    platforms: tuple[MobilePlatform, ...]
    regions: tuple[str, ...] = ("GLOBAL",)
    app_categories: tuple[str, ...] = ("all",)

    def __post_init__(self) -> None:
        platforms = tuple(sorted(set(self.platforms), key=lambda item: item.value))
        if not platforms:
            raise ValueError("scope requires at least one platform")
        regions = tuple(sorted(set(self.regions)))
        if not regions or len(regions) > 64:
            raise ValueError("scope requires 1..64 regions")
        for region in regions:
            if _REGION_RE.fullmatch(region) is None:
                raise ValueError("region must be GLOBAL or ISO alpha-2 uppercase")
        categories = tuple(sorted(set(self.app_categories)))
        if not categories or len(categories) > 64:
            raise ValueError("scope requires 1..64 app categories")
        for category in categories:
            _stable(category, "app category")
        object.__setattr__(self, "platforms", platforms)
        object.__setattr__(self, "regions", regions)
        object.__setattr__(self, "app_categories", categories)

    def matches(self, context: "ComplianceContext") -> bool:
        return (
            context.platform in self.platforms
            and ("GLOBAL" in self.regions or context.region in self.regions)
            and ("all" in self.app_categories or context.app_category in self.app_categories)
        )

    def overlaps(self, other: "ComplianceScope") -> bool:
        if not set(self.platforms).intersection(other.platforms):
            return False
        region_overlap = (
            "GLOBAL" in self.regions
            or "GLOBAL" in other.regions
            or bool(set(self.regions).intersection(other.regions))
        )
        category_overlap = (
            "all" in self.app_categories
            or "all" in other.app_categories
            or bool(set(self.app_categories).intersection(other.app_categories))
        )
        return region_overlap and category_overlap

    def to_dict(self) -> dict[str, object]:
        return {
            "platforms": [item.value for item in self.platforms],
            "regions": list(self.regions),
            "app_categories": list(self.app_categories),
        }


@dataclass(frozen=True, slots=True)
class ComplianceRule:
    rule_id: str
    provider: ComplianceProvider
    requirement: str
    operator: ComplianceRuleOperator
    expected: str | int | bool | tuple[str, ...] | None
    source_url: str
    source_sha256: str
    retrieved_on: str
    effective_from: str
    scope: ComplianceScope
    severity: ComplianceSeverity
    remediation: str
    expires_on: str | None = None
    freshness_days: int = 30
    account_only: bool = False

    def __post_init__(self) -> None:
        _stable(self.rule_id, "rule_id")
        if _FACT_KEY_RE.fullmatch(self.requirement) is None:
            raise ValueError("requirement must be a bounded fact key")
        _validate_https_source(self.source_url)
        _sha(self.source_sha256, "source_sha256")
        retrieved = _iso(self.retrieved_on, "retrieved_on")
        effective = _iso(self.effective_from, "effective_from")
        if self.expires_on is not None:
            expires = _iso(self.expires_on, "expires_on")
            if expires < effective:
                raise ValueError("expires_on cannot precede effective_from")
        if not 1 <= self.freshness_days <= 366:
            raise ValueError("freshness_days must be 1..366")
        _bounded_text(self.remediation, "remediation", 1024)
        expected = self.expected
        if self.operator is ComplianceRuleOperator.PRESENT:
            if expected is not None:
                raise ValueError("PRESENT rule expected must be null")
        elif self.operator is ComplianceRuleOperator.TRUE:
            if expected is not True:
                raise ValueError("TRUE rule expected must be true")
        elif self.operator is ComplianceRuleOperator.MIN_INTEGER:
            if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
                raise ValueError("MIN_INTEGER rule expected must be a non-negative integer")
        elif self.operator is ComplianceRuleOperator.EQUALS:
            if not isinstance(expected, (str, int, bool)):
                raise ValueError("EQUALS rule requires scalar expected value")
            if isinstance(expected, str):
                _bounded_text(expected, "expected")
        elif self.operator is ComplianceRuleOperator.CONTAINS_ALL:
            if not isinstance(expected, tuple) or not expected:
                raise ValueError("CONTAINS_ALL rule requires a non-empty tuple")
            normalized = tuple(sorted(set(expected)))
            if len(normalized) != len(expected) or len(normalized) > _MAX_SET_ITEMS:
                raise ValueError("CONTAINS_ALL expected values must be unique and bounded")
            for item in normalized:
                _bounded_text(item, "expected set item", 256)
            object.__setattr__(self, "expected", normalized)
        if retrieved.year < 2000:
            raise ValueError("retrieved_on is implausibly old")

    def currentness(self, evaluated_on: str) -> ComplianceRuleCurrentness:
        evaluated = _iso(evaluated_on, "evaluated_on")
        retrieved = _iso(self.retrieved_on, "retrieved_on")
        effective = _iso(self.effective_from, "effective_from")
        if retrieved > evaluated:
            raise ValueError("rule evidence cannot be retrieved after evaluation date")
        if evaluated < effective:
            return ComplianceRuleCurrentness.FUTURE
        if self.expires_on is not None and evaluated > _iso(self.expires_on, "expires_on"):
            return ComplianceRuleCurrentness.EXPIRED
        if (evaluated - retrieved).days > self.freshness_days:
            return ComplianceRuleCurrentness.STALE
        parsed = urlparse(self.source_url)
        if parsed.hostname not in _official_hosts(self.provider):
            return ComplianceRuleCurrentness.UNOFFICIAL
        return ComplianceRuleCurrentness.CURRENT

    def to_dict(self) -> dict[str, object]:
        expected: object = self.expected
        if isinstance(expected, tuple):
            expected = list(expected)
        return {
            "rule_id": self.rule_id,
            "provider": self.provider.value,
            "requirement": self.requirement,
            "operator": self.operator.value,
            "expected": expected,
            "source_url": self.source_url,
            "source_sha256": self.source_sha256,
            "retrieved_on": self.retrieved_on,
            "effective_from": self.effective_from,
            "expires_on": self.expires_on,
            "freshness_days": self.freshness_days,
            "scope": self.scope.to_dict(),
            "severity": self.severity.value,
            "remediation": self.remediation,
            "account_only": self.account_only,
        }


@dataclass(frozen=True, slots=True)
class ComplianceRuleSet:
    ruleset_id: str
    rules: tuple[ComplianceRule, ...]

    def __post_init__(self) -> None:
        _stable(self.ruleset_id, "ruleset_id")
        rules = tuple(sorted(self.rules, key=lambda item: item.rule_id))
        if not rules or len(rules) > _MAX_RULES:
            raise ValueError("rule set requires 1..512 rules")
        ids = [item.rule_id for item in rules]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate compliance rule_id")
        object.__setattr__(self, "rules", rules)

    def to_dict(self) -> dict[str, object]:
        return {"ruleset_id": self.ruleset_id, "rules": [item.to_dict() for item in self.rules]}

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class ComplianceFact:
    key: str
    value: object

    def __post_init__(self) -> None:
        if _FACT_KEY_RE.fullmatch(self.key) is None:
            raise ValueError("fact key must be a bounded identifier")
        object.__setattr__(self, "value", _canonical_fact_value(self.value))

    def to_dict(self) -> dict[str, object]:
        value: object = self.value
        if isinstance(value, tuple):
            value = list(value)
        return {"key": self.key, "value": value}


@dataclass(frozen=True, slots=True)
class ThirdPartySdkEvidence:
    sdk_id: str
    version: str
    platforms: tuple[MobilePlatform, ...]
    data_practices_reviewed: bool
    google_data_safety_accounted: bool = False
    apple_app_privacy_accounted: bool = False
    apple_privacy_manifest_present: bool = False
    permissions: tuple[str, ...] = ()
    data_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable(self.sdk_id, "sdk_id")
        if _VERSION_RE.fullmatch(self.version) is None:
            raise ValueError("SDK version must be numeric dotted version")
        platforms = tuple(sorted(set(self.platforms), key=lambda item: item.value))
        if not platforms:
            raise ValueError("SDK evidence requires a platform")
        permissions = tuple(sorted(set(self.permissions)))
        data_types = tuple(sorted(set(self.data_types)))
        if len(permissions) > _MAX_SET_ITEMS or len(data_types) > _MAX_SET_ITEMS:
            raise ValueError("SDK evidence sets are too large")
        for item in permissions + data_types:
            _bounded_text(item, "SDK evidence item", 256)
        object.__setattr__(self, "platforms", platforms)
        object.__setattr__(self, "permissions", permissions)
        object.__setattr__(self, "data_types", data_types)

    def to_dict(self) -> dict[str, object]:
        return {
            "sdk_id": self.sdk_id,
            "version": self.version,
            "platforms": [item.value for item in self.platforms],
            "data_practices_reviewed": self.data_practices_reviewed,
            "google_data_safety_accounted": self.google_data_safety_accounted,
            "apple_app_privacy_accounted": self.apple_app_privacy_accounted,
            "apple_privacy_manifest_present": self.apple_privacy_manifest_present,
            "permissions": list(self.permissions),
            "data_types": list(self.data_types),
        }


@dataclass(frozen=True, slots=True)
class ComplianceInput:
    facts: tuple[ComplianceFact, ...]
    third_party_sdks: tuple[ThirdPartySdkEvidence, ...] = ()

    def __post_init__(self) -> None:
        facts = tuple(sorted(self.facts, key=lambda item: item.key))
        if len(facts) > _MAX_FACTS:
            raise ValueError("too many compliance facts")
        keys = [item.key for item in facts]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate compliance fact key")
        sdks = tuple(sorted(self.third_party_sdks, key=lambda item: (item.sdk_id, item.version)))
        if len(sdks) > _MAX_SDKS:
            raise ValueError("too many third-party SDKs")
        ids = [item.sdk_id for item in sdks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate third-party SDK id")
        object.__setattr__(self, "facts", facts)
        object.__setattr__(self, "third_party_sdks", sdks)

    def fact_map(self) -> dict[str, object]:
        return {item.key: item.value for item in self.facts}

    def to_dict(self) -> dict[str, object]:
        return {
            "facts": [item.to_dict() for item in self.facts],
            "third_party_sdks": [item.to_dict() for item in self.third_party_sdks],
        }

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class ComplianceContext:
    provider: ComplianceProvider
    platform: MobilePlatform
    region: str
    app_category: str
    account_connected: bool = False

    def __post_init__(self) -> None:
        if self.provider is ComplianceProvider.GOOGLE_PLAY and self.platform is not MobilePlatform.ANDROID:
            raise ValueError("Google Play context requires Android platform")
        if self.provider is ComplianceProvider.APPLE_APP_STORE and self.platform is MobilePlatform.ANDROID:
            raise ValueError("Apple App Store context requires iOS/iPadOS platform")
        if _REGION_RE.fullmatch(self.region) is None or self.region == "GLOBAL":
            raise ValueError("evaluation region must be an ISO alpha-2 uppercase code")
        _stable(self.app_category, "app_category")

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "platform": self.platform.value,
            "region": self.region,
            "app_category": self.app_category,
            "account_connected": self.account_connected,
        }


@dataclass(frozen=True, slots=True)
class ComplianceFinding:
    finding_id: str
    rule_id: str | None
    requirement: str
    status: ComplianceFindingStatus
    severity: ComplianceSeverity
    currentness: ComplianceRuleCurrentness | None
    message: str
    remediation: str

    def __post_init__(self) -> None:
        _stable(self.finding_id, "finding_id")
        if self.rule_id is not None:
            _stable(self.rule_id, "rule_id")
        if _FACT_KEY_RE.fullmatch(self.requirement) is None:
            raise ValueError("finding requirement must be a fact key")
        _bounded_text(self.message, "finding message", 1024)
        _bounded_text(self.remediation, "finding remediation", 1024)

    def to_dict(self) -> dict[str, object]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "requirement": self.requirement,
            "status": self.status.value,
            "severity": self.severity.value,
            "currentness": self.currentness.value if self.currentness is not None else None,
            "message": self.message,
            "remediation": self.remediation,
        }


@dataclass(frozen=True, slots=True)
class StoreComplianceSnapshot:
    schema_version: int
    source_sha: str
    evaluated_on: str
    context: ComplianceContext
    ruleset_sha256: str
    input_sha256: str
    applicable_rules: tuple[ComplianceRule, ...]
    findings: tuple[ComplianceFinding, ...]
    state: StoreComplianceState
    current_rule_ids: tuple[str, ...]
    noncurrent_rule_ids: tuple[str, ...]
    account_confirmations: tuple[str, ...]
    legal_certification: bool = False
    live_account_query_attempted: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("store compliance schema version must be 1")
        if _GIT_SHA_RE.fullmatch(self.source_sha) is None:
            raise ValueError("source_sha must be exact lowercase Git SHA")
        _iso(self.evaluated_on, "evaluated_on")
        _sha(self.ruleset_sha256, "ruleset_sha256")
        _sha(self.input_sha256, "input_sha256")
        if self.legal_certification:
            raise ValueError("R13.15 readiness evidence cannot claim legal certification")
        if self.live_account_query_attempted:
            raise ValueError("R13.15 core cannot perform a live account query")
        applicable_rules = tuple(sorted(self.applicable_rules, key=lambda item: item.rule_id))
        applicable_ids = {item.rule_id for item in applicable_rules}
        if len(applicable_ids) != len(applicable_rules):
            raise ValueError("applicable compliance rules must have unique IDs")
        findings = tuple(
            sorted(
                self.findings,
                key=lambda item: (
                    item.severity.value,
                    item.requirement,
                    item.rule_id or "",
                    item.finding_id,
                ),
            )
        )
        current = tuple(sorted(set(self.current_rule_ids)))
        noncurrent = tuple(sorted(set(self.noncurrent_rule_ids)))
        confirmations = tuple(sorted(set(self.account_confirmations)))
        if set(current).intersection(noncurrent):
            raise ValueError("rule cannot be both current and non-current")
        if set(current).union(noncurrent) != applicable_ids:
            raise ValueError("current/non-current rule IDs must cover applicable rule evidence")
        blockers = any(
            item.severity is ComplianceSeverity.BLOCKER
            and item.status in {ComplianceFindingStatus.FAIL, ComplianceFindingStatus.CONFLICT}
            for item in findings
        )
        if blockers and self.state is not StoreComplianceState.BLOCKED:
            raise ValueError("blocker findings require BLOCKED state")
        object.__setattr__(self, "applicable_rules", applicable_rules)
        object.__setattr__(self, "findings", findings)
        object.__setattr__(self, "current_rule_ids", current)
        object.__setattr__(self, "noncurrent_rule_ids", noncurrent)
        object.__setattr__(self, "account_confirmations", confirmations)

    @property
    def current_policy_claim(self) -> bool:
        return bool(self.current_rule_ids) and self.state in {StoreComplianceState.READY, StoreComplianceState.READY_WITH_WARNINGS}

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(
            item.finding_id
            for item in self.findings
            if item.severity is ComplianceSeverity.BLOCKER
            and item.status in {ComplianceFindingStatus.FAIL, ComplianceFindingStatus.CONFLICT}
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "evaluated_on": self.evaluated_on,
            "context": self.context.to_dict(),
            "ruleset_sha256": self.ruleset_sha256,
            "input_sha256": self.input_sha256,
            "applicable_rules": [item.to_dict() for item in self.applicable_rules],
            "findings": [item.to_dict() for item in self.findings],
            "state": self.state.value,
            "current_policy_claim": self.current_policy_claim,
            "current_rule_ids": list(self.current_rule_ids),
            "noncurrent_rule_ids": list(self.noncurrent_rule_ids),
            "account_confirmations": list(self.account_confirmations),
            "blockers": list(self.blockers),
            "legal_certification": self.legal_certification,
            "live_account_query_attempted": self.live_account_query_attempted,
        }

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


def _evaluate_operator(rule: ComplianceRule, facts: Mapping[str, object]) -> bool:
    present = rule.requirement in facts
    if rule.operator is ComplianceRuleOperator.PRESENT:
        if not present:
            return False
        value = facts[rule.requirement]
        return value is not None and value != "" and value != ()
    if not present:
        return False
    observed = facts[rule.requirement]
    if rule.operator is ComplianceRuleOperator.TRUE:
        return observed is True
    if rule.operator is ComplianceRuleOperator.MIN_INTEGER:
        return isinstance(observed, int) and not isinstance(observed, bool) and observed >= rule.expected
    if rule.operator is ComplianceRuleOperator.EQUALS:
        return observed == rule.expected
    if rule.operator is ComplianceRuleOperator.CONTAINS_ALL:
        if not isinstance(observed, tuple):
            return False
        return set(rule.expected or ()).issubset(observed)
    raise AssertionError("unsupported compliance operator")


def _conflicting_rule_pairs(rules: Sequence[ComplianceRule]) -> tuple[tuple[ComplianceRule, ComplianceRule], ...]:
    pairs: list[tuple[ComplianceRule, ComplianceRule]] = []
    for index, left in enumerate(rules):
        for right in rules[index + 1 :]:
            if (
                left.provider is right.provider
                and left.requirement == right.requirement
                and left.scope.overlaps(right.scope)
                and (left.operator is not right.operator or left.expected != right.expected)
            ):
                pairs.append((left, right))
    return tuple(pairs)


def _sdk_findings(
    context: ComplianceContext,
    evidence: ComplianceInput,
) -> tuple[ComplianceFinding, ...]:
    findings: list[ComplianceFinding] = []
    for sdk in evidence.third_party_sdks:
        if context.platform not in sdk.platforms:
            continue
        if not sdk.data_practices_reviewed:
            findings.append(
                ComplianceFinding(
                    finding_id=f"sdk-review-{sdk.sdk_id}",
                    rule_id=None,
                    requirement="sdk.data-practices-reviewed",
                    status=ComplianceFindingStatus.FAIL,
                    severity=ComplianceSeverity.BLOCKER,
                    currentness=None,
                    message=f"Third-party SDK {sdk.sdk_id} data practices were not reviewed.",
                    remediation="Review SDK permissions, data collection/sharing, and provider policy guidance.",
                )
            )
        if context.provider is ComplianceProvider.GOOGLE_PLAY and not sdk.google_data_safety_accounted:
            findings.append(
                ComplianceFinding(
                    finding_id=f"sdk-play-data-safety-{sdk.sdk_id}",
                    rule_id=None,
                    requirement="sdk.google-data-safety-accounted",
                    status=ComplianceFindingStatus.FAIL,
                    severity=ComplianceSeverity.BLOCKER,
                    currentness=None,
                    message=f"Third-party SDK {sdk.sdk_id} is not represented in Google Data safety evidence.",
                    remediation="Account for the SDK data practices in the local Data safety evidence before store submission.",
                )
            )
        if context.provider is ComplianceProvider.APPLE_APP_STORE and not sdk.apple_app_privacy_accounted:
            findings.append(
                ComplianceFinding(
                    finding_id=f"sdk-apple-app-privacy-{sdk.sdk_id}",
                    rule_id=None,
                    requirement="sdk.apple-app-privacy-accounted",
                    status=ComplianceFindingStatus.FAIL,
                    severity=ComplianceSeverity.BLOCKER,
                    currentness=None,
                    message=f"Third-party SDK {sdk.sdk_id} is not represented in Apple App Privacy evidence.",
                    remediation="Account for third-party SDK data practices in App Privacy evidence.",
                )
            )
    return tuple(findings)


def evaluate_store_compliance(
    *,
    source_sha: str,
    evaluated_on: str,
    context: ComplianceContext,
    ruleset: ComplianceRuleSet,
    evidence: ComplianceInput,
) -> StoreComplianceSnapshot:
    if _GIT_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be exact lowercase Git SHA")
    _iso(evaluated_on, "evaluated_on")
    facts = evidence.fact_map()

    applicable = tuple(
        rule
        for rule in ruleset.rules
        if rule.provider is context.provider and rule.scope.matches(context)
    )
    if not applicable:
        finding = ComplianceFinding(
            finding_id="no-applicable-rules",
            rule_id=None,
            requirement="policy.current-evidence",
            status=ComplianceFindingStatus.FAIL,
            severity=ComplianceSeverity.BLOCKER,
            currentness=None,
            message="No provider rule applies to this platform/region/category.",
            remediation="Retrieve and validate official provider rules for this exact scope.",
        )
        return StoreComplianceSnapshot(
            schema_version=1,
            source_sha=source_sha,
            evaluated_on=evaluated_on,
            context=context,
            ruleset_sha256=ruleset.digest(),
            input_sha256=evidence.digest(),
            applicable_rules=(),
            findings=(finding,),
            state=StoreComplianceState.BLOCKED,
            current_rule_ids=(),
            noncurrent_rule_ids=(),
            account_confirmations=(),
        )

    current: list[ComplianceRule] = []
    noncurrent: list[tuple[ComplianceRule, ComplianceRuleCurrentness]] = []
    for rule in applicable:
        status = rule.currentness(evaluated_on)
        if status is ComplianceRuleCurrentness.CURRENT:
            current.append(rule)
        else:
            noncurrent.append((rule, status))

    findings: list[ComplianceFinding] = []
    confirmations: list[str] = []

    for rule, currentness in noncurrent:
        findings.append(
            ComplianceFinding(
                finding_id=f"noncurrent-{rule.rule_id}",
                rule_id=rule.rule_id,
                requirement=rule.requirement,
                status=ComplianceFindingStatus.NOT_CURRENT,
                severity=ComplianceSeverity.INFO,
                currentness=currentness,
                message=f"Rule evidence is {currentness.value} and cannot support a CURRENT compliance claim.",
                remediation="Use the rule only within its valid effective/freshness window and refresh official evidence when needed.",
            )
        )

    current_requirements = {rule.requirement for rule in current}
    all_requirements = {rule.requirement for rule in applicable}
    for requirement in sorted(all_requirements - current_requirements):
        findings.append(
            ComplianceFinding(
                finding_id=f"no-current-{requirement.replace('.', '-')}",
                rule_id=None,
                requirement=requirement,
                status=ComplianceFindingStatus.FAIL,
                severity=ComplianceSeverity.BLOCKER,
                currentness=None,
                message="No CURRENT official rule is available for this applicable requirement.",
                remediation="Refresh official provider evidence before claiming current store readiness.",
            )
        )

    for left, right in _conflicting_rule_pairs(current):
        findings.append(
            ComplianceFinding(
                finding_id=f"conflict-{left.rule_id}-{right.rule_id}"[:128],
                rule_id=None,
                requirement=left.requirement,
                status=ComplianceFindingStatus.CONFLICT,
                severity=ComplianceSeverity.BLOCKER,
                currentness=ComplianceRuleCurrentness.CURRENT,
                message=f"Current official rules {left.rule_id} and {right.rule_id} conflict for the same scope.",
                remediation="Resolve the provider-source conflict explicitly; never choose a winner silently.",
            )
        )

    for rule in current:
        if rule.account_only and not context.account_connected:
            confirmations.append(rule.rule_id)
            findings.append(
                ComplianceFinding(
                    finding_id=f"account-{rule.rule_id}",
                    rule_id=rule.rule_id,
                    requirement=rule.requirement,
                    status=ComplianceFindingStatus.NEEDS_ACCOUNT_CONFIRMATION,
                    severity=ComplianceSeverity.WARNING,
                    currentness=ComplianceRuleCurrentness.CURRENT,
                    message="This current rule depends on an account-only form/state that was not queried.",
                    remediation="Confirm the value in the provider account UI when preparing a live submission.",
                )
            )
            continue
        passed = _evaluate_operator(rule, facts)
        findings.append(
            ComplianceFinding(
                finding_id=f"rule-{rule.rule_id}",
                rule_id=rule.rule_id,
                requirement=rule.requirement,
                status=ComplianceFindingStatus.PASS if passed else ComplianceFindingStatus.FAIL,
                severity=ComplianceSeverity.INFO if passed else rule.severity,
                currentness=ComplianceRuleCurrentness.CURRENT,
                message=(
                    "Observed local evidence satisfies the current rule."
                    if passed
                    else "Observed local evidence does not satisfy the current rule."
                ),
                remediation=rule.remediation,
            )
        )

    findings.extend(_sdk_findings(context, evidence))

    blockers = any(
        item.severity is ComplianceSeverity.BLOCKER
        and item.status in {ComplianceFindingStatus.FAIL, ComplianceFindingStatus.CONFLICT}
        for item in findings
    )
    if blockers:
        state = StoreComplianceState.BLOCKED
    elif confirmations or any(
        item.severity is ComplianceSeverity.WARNING and item.status is ComplianceFindingStatus.FAIL
        for item in findings
    ):
        state = StoreComplianceState.READY_WITH_WARNINGS
    else:
        state = StoreComplianceState.READY

    return StoreComplianceSnapshot(
        schema_version=1,
        source_sha=source_sha,
        evaluated_on=evaluated_on,
        context=context,
        ruleset_sha256=ruleset.digest(),
        input_sha256=evidence.digest(),
        applicable_rules=applicable,
        findings=tuple(findings),
        state=state,
        current_rule_ids=tuple(rule.rule_id for rule in current),
        noncurrent_rule_ids=tuple(rule.rule_id for rule, _ in noncurrent),
        account_confirmations=tuple(confirmations),
    )


def facts_from_mapping(values: Mapping[str, object]) -> tuple[ComplianceFact, ...]:
    if len(values) > _MAX_FACTS:
        raise ValueError("too many compliance facts")
    return tuple(ComplianceFact(key=key, value=value) for key, value in sorted(values.items()))


def build_store_surface_facts(
    *,
    localizations: Iterable[str],
    asset_kinds: Iterable[str],
    accessibility_reviewed: bool,
    privacy_policy_url: str | None = None,
) -> tuple[ComplianceFact, ...]:
    values: dict[str, object] = {
        "store.localizations": tuple(localizations),
        "store.assets": tuple(asset_kinds),
        "store.accessibility-reviewed": accessibility_reviewed,
    }
    if privacy_policy_url is not None:
        parsed = urlparse(privacy_policy_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("privacy_policy_url must be HTTPS")
        values["store.privacy-policy-url"] = privacy_policy_url
    return facts_from_mapping(values)
