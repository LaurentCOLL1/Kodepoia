from __future__ import annotations

import base64
import hashlib
import html
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import unquote

from kodepoia.core.research_guard import ResearchGuard
from kodepoia.core.trust import AuthorityEffect, TrustBoundary, TrustMetadata, TrustOrigin
from kodepoia.quality.redteam import (
    CasePolarity,
    ExpectedDecision,
    RedTeamCase,
    RedTeamCorpus,
)


_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_SUPPLEMENTAL_BYTES = 262_144
_TARGET_BOUNDARIES = frozenset(
    {
        "boundary.prompt-context",
        "boundary.research-web",
        "boundary.repository-workspace",
        "boundary.memory-context",
        "boundary.tool-plugin-mcp",
    }
)
_BOUNDARY_DENIAL = {
    "boundary.prompt-context": ExpectedDecision.DENY,
    "boundary.research-web": ExpectedDecision.DENY,
    "boundary.repository-workspace": ExpectedDecision.QUARANTINE,
    "boundary.memory-context": ExpectedDecision.QUARANTINE,
    "boundary.tool-plugin-mcp": ExpectedDecision.DENY,
}
_EXTRA_PATTERNS = {
    "automatic-execution": re.compile(r"post[_ -]?open|automatic execution|hidden setup", re.I),
    "memory-policy-poison": re.compile(r"permanently disabled|outranks? (?:repository )?policy", re.I),
    "implicit-approval": re.compile(r"approval (?:is|=) implicit|approval\s*=\s*true", re.I),
    "security-gate-spoof": re.compile(r"mark (?:all|every) security gate(?:s)? pass", re.I),
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


class PromptInjectionStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class SupplementalInjectionCase:
    id: str
    origin: TrustOrigin
    payload: str
    effect: AuthorityEffect
    expected_decision: ExpectedDecision
    critical: bool
    benign: bool = False

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SupplementalInjectionCase:
        case_id = str(payload["id"]).strip().lower()
        if not re.fullmatch(r"r16\.2\.[a-z0-9_.:-]+", case_id):
            raise ValueError("supplemental prompt-injection case id is invalid")
        expected = ExpectedDecision(str(payload["expected_decision"]))
        benign = bool(payload.get("benign", False))
        if benign and expected is not ExpectedDecision.ALLOW:
            raise ValueError("benign supplemental cases must expect allow")
        if not benign and expected is ExpectedDecision.ALLOW:
            raise ValueError("adversarial supplemental cases cannot expect allow")
        origin = TrustOrigin(str(payload["origin"]))
        if origin in {TrustOrigin.SYSTEM, TrustOrigin.USER, TrustOrigin.UNKNOWN}:
            raise ValueError("supplemental cases must use an explicit external origin")
        text = str(payload["payload"])
        if not text.strip() or "\x00" in text:
            raise ValueError("supplemental prompt-injection payload is invalid")
        return cls(
            id=case_id,
            origin=origin,
            payload=text,
            effect=AuthorityEffect(str(payload["effect"])),
            expected_decision=expected,
            critical=bool(payload.get("critical", True)),
            benign=benign,
        )

    @property
    def payload_sha256(self) -> str:
        return _sha256(self.payload)

    def evidence_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "origin": self.origin.value,
            "effect": self.effect.value,
            "expected_decision": self.expected_decision.value,
            "critical": self.critical,
            "benign": self.benign,
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True, slots=True)
class PromptInjectionCaseResult:
    id: str
    expected_decision: ExpectedDecision
    actual_decision: ExpectedDecision
    passed: bool
    critical: bool
    payload_sha256: str
    indicators: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "expected_decision": self.expected_decision.value,
            "actual_decision": self.actual_decision.value,
            "passed": self.passed,
            "critical": self.critical,
            "payload_sha256": self.payload_sha256,
            "indicators": list(self.indicators),
        }


@dataclass(frozen=True, slots=True)
class PromptInjectionReport:
    source_sha: str
    r16_corpus_sha256: str
    r16_case_set_sha256: str
    targeted_case_set_sha256: str
    supplemental_case_set_sha256: str
    policy_sha256: str
    status: PromptInjectionStatus
    critical_veto: bool
    results: tuple[PromptInjectionCaseResult, ...]
    security_claim: bool = True
    schema_version: int = 1

    def semantic_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "r16_corpus_sha256": self.r16_corpus_sha256,
            "r16_case_set_sha256": self.r16_case_set_sha256,
            "targeted_case_set_sha256": self.targeted_case_set_sha256,
            "supplemental_case_set_sha256": self.supplemental_case_set_sha256,
            "policy_sha256": self.policy_sha256,
            "status": self.status.value,
            "critical_veto": self.critical_veto,
            "security_claim": self.security_claim,
            "results": [item.to_dict() for item in self.results],
        }

    @property
    def semantic_sha256(self) -> str:
        return _sha256(_canonical_json(self.semantic_payload()))

    def to_dict(self) -> dict[str, Any]:
        payload = self.semantic_payload()
        payload["semantic_sha256"] = self.semantic_sha256
        return payload


class PromptInjectionPolicy:
    """Deterministic content/authority policy; model compliance is never an authorization signal."""

    VERSION = 1

    @property
    def policy_sha256(self) -> str:
        payload = {
            "version": self.VERSION,
            "target_boundaries": sorted(_TARGET_BOUNDARIES),
            "boundary_denial": {key: value.value for key, value in sorted(_BOUNDARY_DENIAL.items())},
            "system_only": sorted(effect.value for effect in TrustBoundary._SYSTEM_ONLY),
            "user_or_system": sorted(effect.value for effect in TrustBoundary._USER_OR_SYSTEM),
        }
        return _sha256(_canonical_json(payload))

    @staticmethod
    def _decoded_variants(payload: str) -> tuple[str, ...]:
        variants = [payload, html.unescape(payload), unquote(payload)]
        stripped = payload.strip()
        encoded = stripped[7:] if stripped.lower().startswith("base64:") else ""
        if encoded:
            try:
                decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                decoded = ""
            if decoded:
                variants.append(decoded)
        return tuple(dict.fromkeys(variants))

    def indicators(self, payload: str, *, origin: TrustOrigin) -> tuple[str, ...]:
        indicators: set[str] = set()
        for variant in self._decoded_variants(payload):
            guarded = ResearchGuard().wrap(variant, origin=origin, source="r16.2-evaluation")
            indicators.update(guarded.indicators)
            indicators.update(name for name, pattern in _EXTRA_PATTERNS.items() if pattern.search(variant))
        return tuple(sorted(indicators))

    def evaluate_redteam_case(self, case: RedTeamCase) -> tuple[ExpectedDecision, tuple[str, ...]]:
        if case.boundary_id not in _TARGET_BOUNDARIES:
            raise ValueError(f"R16.2 does not own red-team boundary: {case.boundary_id}")
        origin = {
            "boundary.prompt-context": TrustOrigin.DOCUMENT,
            "boundary.research-web": TrustOrigin.WEB,
            "boundary.repository-workspace": TrustOrigin.REPOSITORY,
            "boundary.memory-context": TrustOrigin.MEMORY,
            "boundary.tool-plugin-mcp": TrustOrigin.TOOL_OUTPUT,
        }[case.boundary_id]
        indicators = self.indicators(case.payload, origin=origin)
        if case.polarity is CasePolarity.BENIGN:
            return ExpectedDecision.ALLOW, indicators
        if not indicators:
            return ExpectedDecision.ALLOW, indicators
        return _BOUNDARY_DENIAL[case.boundary_id], indicators

    def evaluate_supplemental_case(
        self, case: SupplementalInjectionCase
    ) -> tuple[ExpectedDecision, tuple[str, ...]]:
        indicators = self.indicators(case.payload, origin=case.origin)
        trust = TrustMetadata.untrusted(case.origin, source=case.id, content=case.payload)
        decision = TrustBoundary().evaluate(trust, case.effect)
        actual = ExpectedDecision.ALLOW if decision.allowed else ExpectedDecision.DENY
        return actual, indicators


def load_supplemental_cases(
    path: str | Path,
    *,
    repository_root: str | Path,
) -> tuple[SupplementalInjectionCase, ...]:
    root = Path(repository_root).resolve(strict=True)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.is_symlink():
        raise ValueError("supplemental prompt-injection fixture cannot be a symlink")
    resolved = candidate.resolve(strict=True)
    if not _within(resolved, root):
        raise ValueError("supplemental prompt-injection fixture must stay inside repository_root")
    if resolved.suffix.lower() != ".json" or not resolved.is_file():
        raise ValueError("supplemental prompt-injection fixture must be JSON")
    if resolved.stat().st_size > _MAX_SUPPLEMENTAL_BYTES:
        raise ValueError("supplemental prompt-injection fixture exceeds bounded size")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("supplemental prompt-injection fixture must be an object")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("synthetic_only") is not True or metadata.get("immutable") is not True:
        raise ValueError("supplemental prompt-injection fixture must be synthetic_only and immutable")
    cases = tuple(SupplementalInjectionCase.from_dict(item) for item in payload.get("cases", []))
    ids = tuple(item.id for item in cases)
    if not cases or ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
        raise ValueError("supplemental prompt-injection cases must be non-empty, unique and sorted")
    return cases


def supplemental_case_set_sha256(cases: Sequence[SupplementalInjectionCase]) -> str:
    return _sha256(_canonical_json([case.evidence_dict() for case in cases]))


def run_prompt_injection_acceptance(
    *,
    source_sha: str,
    corpus: RedTeamCorpus,
    supplemental_cases: Sequence[SupplementalInjectionCase],
) -> PromptInjectionReport:
    source = source_sha.strip().lower()
    if not _SHA40_RE.fullmatch(source):
        raise ValueError("source_sha must be an exact lowercase 40-hex Git SHA")
    policy = PromptInjectionPolicy()
    targeted = tuple(case for case in corpus.cases if case.boundary_id in _TARGET_BOUNDARIES)
    if not targeted:
        raise ValueError("R16.1 corpus contains no R16.2 target cases")
    results: list[PromptInjectionCaseResult] = []
    for case in targeted:
        actual, indicators = policy.evaluate_redteam_case(case)
        results.append(
            PromptInjectionCaseResult(
                id=case.id,
                expected_decision=case.expected_decision,
                actual_decision=actual,
                passed=actual is case.expected_decision,
                critical=True,
                payload_sha256=case.payload_sha256,
                indicators=indicators,
            )
        )
    for case in supplemental_cases:
        actual, indicators = policy.evaluate_supplemental_case(case)
        results.append(
            PromptInjectionCaseResult(
                id=case.id,
                expected_decision=case.expected_decision,
                actual_decision=actual,
                passed=actual is case.expected_decision,
                critical=case.critical,
                payload_sha256=case.payload_sha256,
                indicators=indicators,
            )
        )
    critical_veto = any(item.critical and not item.passed for item in results)
    status = PromptInjectionStatus.PASS if not critical_veto and all(item.passed for item in results) else PromptInjectionStatus.FAIL
    targeted_digest = _sha256(_canonical_json([case.evidence_dict() for case in targeted]))
    return PromptInjectionReport(
        source_sha=source,
        r16_corpus_sha256=corpus.corpus_sha256,
        r16_case_set_sha256=corpus.case_set_sha256,
        targeted_case_set_sha256=targeted_digest,
        supplemental_case_set_sha256=supplemental_case_set_sha256(supplemental_cases),
        policy_sha256=policy.policy_sha256,
        status=status,
        critical_veto=critical_veto,
        results=tuple(results),
    )
