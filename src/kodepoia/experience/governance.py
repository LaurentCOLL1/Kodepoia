from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from typing import Iterable, Mapping, Pattern

from .contracts import (
    ContentRef,
    ExperienceRecord,
    ExperienceState,
    PolicyDecision,
    SanitizationEvidence,
    SanitizationStatus,
    TrainingAuthorization,
    TransformationRef,
    transition_experience,
)

SANITIZER_VERSION = "r15.3-sanitizer-v1"
_TOKEN = re.compile(r"\(|\)|\bAND\b|\bOR\b|\bWITH\b|[A-Za-z0-9][A-Za-z0-9.+:-]*")
_SAFE_CATEGORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


class GovernanceError(ValueError):
    """Base error for R15.3 sanitization/governance failures."""


class LicenseExpressionError(GovernanceError):
    """Raised for syntactically invalid SPDX-style expressions."""


@dataclass(frozen=True, slots=True)
class RedactionRule:
    category: str
    pattern: str
    flags: int = 0

    def __post_init__(self) -> None:
        if not _SAFE_CATEGORY.fullmatch(self.category):
            raise GovernanceError("redaction category must be a stable safe identifier")
        re.compile(self.pattern, self.flags)

    def compiled(self) -> Pattern[str]:
        return re.compile(self.pattern, self.flags)


_BUILTIN_RULES: tuple[RedactionRule, ...] = (
    RedactionRule(
        "credential",
        r"(?i)(?P<prefix>\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\s*[:=]\s*['\"]?)(?P<value>[A-Za-z0-9_./+\-=]{8,})",
    ),
    RedactionRule(
        "private_key",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    ),
    RedactionRule("email", r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    RedactionRule("windows_path", r"(?i)\b[A-Z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]*"),
    RedactionRule("unix_home_path", r"(?<![A-Za-z0-9])/(?:home|Users)/[^\s'\"`]+"),
)


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    allowed_source_types: frozenset[str] = frozenset()
    denied_source_types: frozenset[str] = frozenset()
    trusted_provenance_source_types: frozenset[str] = frozenset()
    allowed_licenses: frozenset[str] = frozenset()
    denied_licenses: frozenset[str] = frozenset()
    allowed_exceptions: frozenset[str] = frozenset()
    extra_redaction_rules: tuple[RedactionRule, ...] = ()
    deny_categories: frozenset[str] = frozenset()
    allow_license_refs: bool = False
    privacy_after_redaction: PolicyDecision = PolicyDecision.ALLOW

    def __post_init__(self) -> None:
        overlap = self.allowed_source_types & self.denied_source_types
        if overlap:
            raise GovernanceError(f"source type cannot be both allowed and denied: {sorted(overlap)!r}")
        overlap = self.allowed_licenses & self.denied_licenses
        if overlap:
            raise GovernanceError(f"license cannot be both allowed and denied: {sorted(overlap)!r}")
        for category in self.deny_categories:
            if not _SAFE_CATEGORY.fullmatch(category):
                raise GovernanceError("deny category must be a stable safe identifier")

    def digest(self) -> str:
        payload = {
            "allowed_source_types": sorted(self.allowed_source_types),
            "denied_source_types": sorted(self.denied_source_types),
            "trusted_provenance_source_types": sorted(self.trusted_provenance_source_types),
            "allowed_licenses": sorted(self.allowed_licenses),
            "denied_licenses": sorted(self.denied_licenses),
            "allowed_exceptions": sorted(self.allowed_exceptions),
            "extra_redaction_rules": [
                {"category": rule.category, "pattern": rule.pattern, "flags": rule.flags}
                for rule in self.extra_redaction_rules
            ],
            "deny_categories": sorted(self.deny_categories),
            "allow_license_refs": self.allow_license_refs,
            "privacy_after_redaction": self.privacy_after_redaction.value,
            "sanitizer_version": SANITIZER_VERSION,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class LicenseAssessment:
    expression: str | None
    decision: PolicyDecision
    identifiers: tuple[str, ...] = ()
    operators: tuple[str, ...] = ()
    reason: str = ""

    def safe_summary(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "identifier_count": len(self.identifiers),
            "operators": list(self.operators),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class SanitizationReport:
    input_digest: str
    output_digest: str
    policy_digest: str
    sanitizer_digest: str
    categories: tuple[str, ...]
    finding_count: int
    authorization: TrainingAuthorization
    license_summary: Mapping[str, object]
    disposition: str
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
            "policy_digest": self.policy_digest,
            "sanitizer_digest": self.sanitizer_digest,
            "categories": list(self.categories),
            "finding_count": self.finding_count,
            "authorization": {
                "source_scope": self.authorization.source_scope.value,
                "consent": self.authorization.consent.value,
                "provenance": self.authorization.provenance.value,
                "license": self.authorization.license.value,
                "privacy": self.authorization.privacy.value,
            },
            "license": dict(self.license_summary),
            "disposition": self.disposition,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True, slots=True)
class SanitizationResult:
    record: ExperienceRecord
    sanitized_text: str
    report: SanitizationReport


@dataclass(frozen=True, slots=True)
class RevocationReport:
    source_id: str
    revoked_experience_ids: tuple[str, ...]
    quarantined_experience_ids: tuple[str, ...]
    invalidated_artifact_ids: tuple[str, ...]
    reason_digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "revoked_experience_ids": list(self.revoked_experience_ids),
            "quarantined_experience_ids": list(self.quarantined_experience_ids),
            "invalidated_artifact_ids": list(self.invalidated_artifact_ids),
            "reason_digest": self.reason_digest,
            "rebuild_required": bool(self.invalidated_artifact_ids),
        }


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _tokenize_license(expression: str) -> list[str]:
    expression = expression.strip()
    if not expression:
        raise LicenseExpressionError("license expression is empty")
    tokens: list[str] = []
    cursor = 0
    for match in _TOKEN.finditer(expression):
        if expression[cursor : match.start()].strip():
            raise LicenseExpressionError("license expression contains unsupported syntax")
        tokens.append(match.group(0))
        cursor = match.end()
    if expression[cursor:].strip() or not tokens:
        raise LicenseExpressionError("license expression contains unsupported syntax")
    return tokens


class _LicenseParser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.identifiers: list[str] = []
        self.exceptions: list[str] = []
        self.operators: list[str] = []

    def parse(self) -> None:
        self._or_expr()
        if self.pos != len(self.tokens):
            raise LicenseExpressionError("unexpected trailing license token")

    def _or_expr(self) -> None:
        self._and_expr()
        while self._peek("OR"):
            self.operators.append(self._take())
            self._and_expr()

    def _and_expr(self) -> None:
        self._with_expr()
        while self._peek("AND"):
            self.operators.append(self._take())
            self._with_expr()

    def _with_expr(self) -> None:
        simple = self._primary()
        if self._peek("WITH"):
            if not simple:
                raise LicenseExpressionError("WITH requires a simple left expression")
            self.operators.append(self._take())
            token = self._take_identifier()
            self.exceptions.append(token)

    def _primary(self) -> bool:
        if self._peek("("):
            self._take()
            self._or_expr()
            if not self._peek(")"):
                raise LicenseExpressionError("unclosed license parenthesis")
            self._take()
            return False
        token = self._take_identifier()
        self.identifiers.append(token)
        return True

    def _take_identifier(self) -> str:
        if self.pos >= len(self.tokens):
            raise LicenseExpressionError("license identifier expected")
        token = self.tokens[self.pos]
        if token in {"(", ")", "AND", "OR", "WITH"}:
            raise LicenseExpressionError("license identifier expected")
        self.pos += 1
        return token

    def _peek(self, value: str) -> bool:
        return self.pos < len(self.tokens) and self.tokens[self.pos] == value

    def _take(self) -> str:
        if self.pos >= len(self.tokens):
            raise LicenseExpressionError("unexpected end of license expression")
        token = self.tokens[self.pos]
        self.pos += 1
        return token


def assess_license(expression: str | None, policy: GovernancePolicy) -> LicenseAssessment:
    if expression is None:
        return LicenseAssessment(None, PolicyDecision.UNKNOWN, reason="license_missing")
    try:
        parser = _LicenseParser(_tokenize_license(expression))
        parser.parse()
    except LicenseExpressionError:
        return LicenseAssessment(expression, PolicyDecision.REVIEW, reason="license_syntax_review")

    ids = tuple(parser.identifiers + parser.exceptions)
    operators = tuple(parser.operators)
    if any(identifier in policy.denied_licenses for identifier in parser.identifiers):
        return LicenseAssessment(expression, PolicyDecision.DENY, ids, operators, "license_denied")
    if any(identifier.startswith(("LicenseRef-", "DocumentRef-")) for identifier in parser.identifiers):
        if not policy.allow_license_refs:
            return LicenseAssessment(expression, PolicyDecision.REVIEW, ids, operators, "license_ref_review")
    unknown_ids = [identifier for identifier in parser.identifiers if identifier not in policy.allowed_licenses]
    unknown_exceptions = [item for item in parser.exceptions if item not in policy.allowed_exceptions]
    if unknown_ids or unknown_exceptions:
        return LicenseAssessment(expression, PolicyDecision.REVIEW, ids, operators, "license_unknown")
    return LicenseAssessment(expression, PolicyDecision.ALLOW, ids, operators, "license_allowed")


def _redact(text: str, rules: Iterable[RedactionRule]) -> tuple[str, tuple[str, ...], int]:
    output = text
    counts: dict[str, int] = {}
    for rule in rules:
        pattern = rule.compiled()

        def replacement(match: re.Match[str]) -> str:
            counts[rule.category] = counts.get(rule.category, 0) + 1
            prefix = match.groupdict().get("prefix")
            return (prefix or "") + f"<redacted:{rule.category}>"

        output = pattern.sub(replacement, output)
    categories = tuple(sorted(counts))
    return output, categories, sum(counts.values())


def sanitize_experience(
    record: ExperienceRecord,
    raw_text: str,
    *,
    policy: GovernancePolicy,
    consent: PolicyDecision = PolicyDecision.UNKNOWN,
    actor: str = "experience-governance",
) -> SanitizationResult:
    """Sanitize one observed record and fail closed on independent authorization axes."""
    if record.state is not ExperienceState.OBSERVED:
        raise GovernanceError("R15.3 sanitization requires an OBSERVED record")
    if not isinstance(raw_text, str):
        raise GovernanceError("raw_text must be text")

    policy_digest = policy.digest()
    sanitized, categories, finding_count = _redact(
        raw_text, (*_BUILTIN_RULES, *policy.extra_redaction_rules)
    )
    input_digest = _digest_text(raw_text)
    output_digest = _digest_text(sanitized)
    sanitizer_digest = hashlib.sha256(
        f"{SANITIZER_VERSION}\0{policy_digest}".encode()
    ).hexdigest()

    source_type = record.provenance.source_type
    if source_type in policy.denied_source_types:
        source_scope = PolicyDecision.DENY
    elif source_type in policy.allowed_source_types:
        source_scope = PolicyDecision.ALLOW
    else:
        source_scope = PolicyDecision.REVIEW

    provenance = (
        PolicyDecision.ALLOW
        if source_type in policy.trusted_provenance_source_types
        else PolicyDecision.REVIEW
    )
    license_result = assess_license(record.provenance.license_expression, policy)
    privacy = policy.privacy_after_redaction
    if set(categories) & policy.deny_categories:
        privacy = PolicyDecision.DENY

    authorization = TrainingAuthorization(
        source_scope=source_scope,
        consent=consent,
        provenance=provenance,
        license=license_result.decision,
        privacy=privacy,
    )
    evidence = SanitizationEvidence(
        status=SanitizationStatus.PASSED,
        sanitizer_digest=sanitizer_digest,
        categories=categories,
        finding_count=finding_count,
    )
    sanitized_ref = ContentRef(
        workspace_id=record.workspace_id,
        storage_key=(
            f"experience/sanitized/{record.project_id}/{record.experience_id.value}/{output_digest}.txt"
        ),
        sha256=output_digest,
        byte_length=len(sanitized.encode()),
        media_type="text/plain",
    )
    transform = TransformationRef(
        transformation_id="r15.3-sanitize-v1",
        input_digest=input_digest,
        output_digest=output_digest,
        policy_digest=policy_digest,
    )
    governed = replace(
        record,
        content=sanitized_ref,
        authorization=authorization,
        sanitization=evidence,
        transformations=(*record.transformations, transform),
    )

    if authorization.is_allowed() and not record.benchmark_protected:
        eligible = transition_experience(
            governed,
            ExperienceState.ELIGIBLE,
            actor=actor,
            reason="R15.3 authorization axes are explicitly allowed",
        ).record
        final_record = transition_experience(
            eligible,
            ExperienceState.SANITIZED,
            actor=actor,
            reason="R15.3 deterministic sanitizer passed",
        ).record
        disposition = "sanitized"
    else:
        final_record = transition_experience(
            governed,
            ExperienceState.QUARANTINED,
            actor=actor,
            reason="R15.3 authorization unresolved/denied or benchmark protected",
        ).record
        disposition = "quarantined"

    report = SanitizationReport(
        input_digest=input_digest,
        output_digest=output_digest,
        policy_digest=policy_digest,
        sanitizer_digest=sanitizer_digest,
        categories=categories,
        finding_count=finding_count,
        authorization=authorization,
        license_summary=license_result.safe_summary(),
        disposition=disposition,
        blockers=authorization.blockers(),
    )
    return SanitizationResult(final_record, sanitized, report)


@dataclass(slots=True)
class RevocationIndex:
    """Tracks derived artifact dependencies without storing experience payloads."""

    dependencies: dict[str, frozenset[str]] = field(default_factory=dict)

    def register(self, artifact_id: str, parents: Iterable[str]) -> None:
        artifact_id = artifact_id.strip()
        parent_set = frozenset(item.strip() for item in parents if item.strip())
        if not artifact_id or not parent_set:
            raise GovernanceError("artifact_id and at least one parent are required")
        self.dependencies[artifact_id] = parent_set

    def affected(self, roots: Iterable[str]) -> tuple[str, ...]:
        affected = set(item for item in roots if item)
        changed = True
        while changed:
            changed = False
            for artifact_id, parents in self.dependencies.items():
                if artifact_id not in affected and parents & affected:
                    affected.add(artifact_id)
                    changed = True
        root_set = set(roots)
        return tuple(sorted(affected - root_set))

    def revoke_source(
        self,
        source_id: str,
        records: Iterable[ExperienceRecord],
        *,
        actor: str,
        reason: str,
    ) -> tuple[tuple[ExperienceRecord, ...], RevocationReport]:
        source_id = source_id.strip()
        reason = reason.strip()
        if not source_id or not actor.strip() or not reason:
            raise GovernanceError("source_id, actor and reason are required")
        updated: list[ExperienceRecord] = []
        revoked: list[str] = []
        quarantined: list[str] = []
        roots: list[str] = []
        for record in records:
            if record.provenance.source_id != source_id:
                updated.append(record)
                continue
            roots.append(record.experience_id.value)
            if record.state in {
                ExperienceState.ELIGIBLE,
                ExperienceState.SANITIZED,
                ExperienceState.CURATED,
                ExperienceState.DATASET_INCLUDED,
            }:
                changed = transition_experience(
                    record,
                    ExperienceState.REVOKED,
                    actor=actor,
                    reason=reason,
                ).record
                revoked.append(record.experience_id.value)
            elif record.state is ExperienceState.OBSERVED:
                changed = transition_experience(
                    record,
                    ExperienceState.QUARANTINED,
                    actor=actor,
                    reason=reason,
                ).record
                quarantined.append(record.experience_id.value)
            else:
                changed = record
            updated.append(changed)
        invalidated = self.affected(roots)
        report = RevocationReport(
            source_id=source_id,
            revoked_experience_ids=tuple(sorted(revoked)),
            quarantined_experience_ids=tuple(sorted(quarantined)),
            invalidated_artifact_ids=invalidated,
            reason_digest=_digest_text(reason),
        )
        return tuple(updated), report
