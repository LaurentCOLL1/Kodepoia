from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

_SCHEMA_VERSION = 1
_MAX_CORPUS_BYTES = 1_048_576
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{1,127}$")
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LIVE_SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", re.IGNORECASE),
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _ID_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a stable lowercase identifier")
    return normalized


def _ensure_no_live_secret(text: str, *, field_name: str) -> None:
    if "\x00" in text:
        raise ValueError(f"{field_name} contains a NUL byte")
    for pattern in _LIVE_SECRET_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"{field_name} contains a live-secret-shaped value")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


class CasePolarity(StrEnum):
    BENIGN = "benign"
    ADVERSARIAL = "adversarial"


class ExpectedDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    QUARANTINE = "quarantine"
    RECOVERY_REQUIRED = "recovery_required"


class HarnessStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class RedTeamBoundary:
    id: str
    name: str
    critical: bool
    security_goals: tuple[str, ...]
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="boundary id"))
        goals = tuple(sorted({item.strip().lower() for item in self.security_goals if item.strip()}))
        if not self.name.strip() or not self.description.strip():
            raise ValueError("boundary name/description cannot be empty")
        if not goals or not set(goals) <= {"confidentiality", "integrity", "availability"}:
            raise ValueError("boundary security_goals must use confidentiality/integrity/availability")
        object.__setattr__(self, "security_goals", goals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "critical": self.critical,
            "security_goals": list(self.security_goals),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RedTeamBoundary:
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            critical=bool(payload.get("critical", False)),
            security_goals=tuple(str(item) for item in payload.get("security_goals", [])),
            description=str(payload.get("description", "")),
        )


@dataclass(frozen=True, slots=True)
class RedTeamCase:
    id: str
    boundary_id: str
    polarity: CasePolarity
    expected_decision: ExpectedDecision
    payload: str
    invariant: str
    severity: str
    attacker_goal: str
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="case id"))
        object.__setattr__(
            self,
            "boundary_id",
            _stable_id(self.boundary_id, field_name="case boundary id"),
        )
        invariant = self.invariant.strip().lower()
        severity = self.severity.strip().lower()
        attacker_goal = self.attacker_goal.strip().lower()
        tags = tuple(sorted({_stable_id(item, field_name="case tag") for item in self.tags}))
        if not invariant:
            raise ValueError("case invariant cannot be empty")
        if severity not in {"info", "low", "medium", "high", "critical"}:
            raise ValueError("unsupported case severity")
        if attacker_goal not in {"confidentiality", "integrity", "availability"}:
            raise ValueError("unsupported attacker goal")
        if not self.payload.strip():
            raise ValueError("case payload cannot be empty")
        _ensure_no_live_secret(self.payload, field_name=f"case {self.id} payload")
        if self.polarity is CasePolarity.BENIGN and self.expected_decision is not ExpectedDecision.ALLOW:
            raise ValueError("benign cases must expect ALLOW")
        if self.polarity is CasePolarity.ADVERSARIAL and self.expected_decision is ExpectedDecision.ALLOW:
            raise ValueError("adversarial cases cannot expect ALLOW")
        object.__setattr__(self, "invariant", invariant)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "attacker_goal", attacker_goal)
        object.__setattr__(self, "tags", tags)

    @property
    def payload_sha256(self) -> str:
        return _sha256_text(self.payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "boundary_id": self.boundary_id,
            "polarity": self.polarity.value,
            "expected_decision": self.expected_decision.value,
            "payload": self.payload,
            "invariant": self.invariant,
            "severity": self.severity,
            "attacker_goal": self.attacker_goal,
            "tags": list(self.tags),
        }

    def evidence_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("payload")
        payload["payload_sha256"] = self.payload_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RedTeamCase:
        return cls(
            id=str(payload["id"]),
            boundary_id=str(payload["boundary_id"]),
            polarity=CasePolarity(str(payload["polarity"])),
            expected_decision=ExpectedDecision(str(payload["expected_decision"])),
            payload=str(payload["payload"]),
            invariant=str(payload["invariant"]),
            severity=str(payload["severity"]),
            attacker_goal=str(payload["attacker_goal"]),
            tags=tuple(str(item) for item in payload.get("tags", [])),
        )


@dataclass(frozen=True, slots=True)
class RedTeamCorpus:
    metadata: Mapping[str, Any]
    boundaries: tuple[RedTeamBoundary, ...]
    cases: tuple[RedTeamCase, ...]
    declared_sha256: str
    schema_version: int = _SCHEMA_VERSION

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
            "boundaries": [item.to_dict() for item in self.boundaries],
            "cases": [item.to_dict() for item in self.cases],
        }

    @property
    def corpus_sha256(self) -> str:
        return _sha256_text(_canonical_json(self.canonical_payload()))

    @property
    def case_set_sha256(self) -> str:
        payload = [item.evidence_dict() for item in self.cases]
        return _sha256_text(_canonical_json(payload))

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported red-team corpus schema version")
        metadata = dict(self.metadata)
        if metadata.get("synthetic_only") is not True or metadata.get("immutable") is not True:
            raise ValueError("red-team corpus must be declared synthetic_only and immutable")
        corpus_id = str(metadata.get("id", ""))
        _stable_id(corpus_id, field_name="corpus id")
        _ensure_no_live_secret(_canonical_json(metadata), field_name="corpus metadata")
        if not _SHA256_RE.fullmatch(self.declared_sha256):
            raise ValueError("corpus_sha256 must be a lowercase SHA-256 digest")
        if self.declared_sha256 != self.corpus_sha256:
            raise ValueError("red-team corpus digest mismatch")
        boundary_ids = [item.id for item in self.boundaries]
        case_ids = [item.id for item in self.cases]
        if not self.boundaries or not self.cases:
            raise ValueError("red-team corpus cannot be empty")
        if len(boundary_ids) != len(set(boundary_ids)):
            raise ValueError("red-team boundary ids must be unique")
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("red-team case ids must be unique")
        boundary_set = set(boundary_ids)
        for case in self.cases:
            if case.boundary_id not in boundary_set:
                raise ValueError(f"case references unknown boundary: {case.id}")
        for boundary in self.boundaries:
            if not boundary.critical:
                continue
            polarities = {
                case.polarity
                for case in self.cases
                if case.boundary_id == boundary.id
            }
            if polarities != {CasePolarity.BENIGN, CasePolarity.ADVERSARIAL}:
                raise ValueError(
                    f"critical boundary requires benign and adversarial coverage: {boundary.id}"
                )
        if tuple(sorted(case_ids)) != tuple(case_ids):
            raise ValueError("red-team cases must be stored in deterministic id order")
        if tuple(sorted(boundary_ids)) != tuple(boundary_ids):
            raise ValueError("red-team boundaries must be stored in deterministic id order")

    def coverage(self) -> dict[str, dict[str, int | bool]]:
        self.validate()
        return {
            boundary.id: {
                "critical": boundary.critical,
                "benign": sum(
                    case.boundary_id == boundary.id and case.polarity is CasePolarity.BENIGN
                    for case in self.cases
                ),
                "adversarial": sum(
                    case.boundary_id == boundary.id
                    and case.polarity is CasePolarity.ADVERSARIAL
                    for case in self.cases
                ),
            }
            for boundary in self.boundaries
        }


@dataclass(frozen=True, slots=True)
class RedTeamCaseResult:
    id: str
    boundary_id: str
    expected_decision: ExpectedDecision
    actual_decision: ExpectedDecision | None
    passed: bool | None
    critical: bool
    payload_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "boundary_id": self.boundary_id,
            "expected_decision": self.expected_decision.value,
            "actual_decision": (
                self.actual_decision.value if self.actual_decision is not None else "not_exercised"
            ),
            "passed": self.passed,
            "critical": self.critical,
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True, slots=True)
class RedTeamReport:
    source_sha: str
    corpus_sha256: str
    case_set_sha256: str
    policy_sha256: str
    mode: str
    status: HarnessStatus
    security_claim: bool
    critical_veto: bool
    results: tuple[RedTeamCaseResult, ...]
    coverage: Mapping[str, Mapping[str, int | bool]]
    schema_version: int = _SCHEMA_VERSION

    def semantic_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "corpus_sha256": self.corpus_sha256,
            "case_set_sha256": self.case_set_sha256,
            "policy_sha256": self.policy_sha256,
            "mode": self.mode,
            "status": self.status.value,
            "security_claim": self.security_claim,
            "critical_veto": self.critical_veto,
            "coverage": {key: dict(value) for key, value in sorted(self.coverage.items())},
            "results": [item.to_dict() for item in self.results],
        }

    @property
    def semantic_sha256(self) -> str:
        return _sha256_text(_canonical_json(self.semantic_payload()))

    def to_dict(self) -> dict[str, Any]:
        payload = self.semantic_payload()
        payload["semantic_sha256"] = self.semantic_sha256
        return payload


DecisionEvaluator = Callable[[RedTeamCase], ExpectedDecision]


class RedTeamRunner:
    def __init__(self, corpus: RedTeamCorpus) -> None:
        corpus.validate()
        self.corpus = corpus
        self._critical = {item.id: item.critical for item in corpus.boundaries}

    def run(
        self,
        *,
        source_sha: str,
        policy_sha256: str,
        evaluator: DecisionEvaluator | None = None,
    ) -> RedTeamReport:
        source = source_sha.strip().lower()
        policy = policy_sha256.strip().lower()
        if not _SHA40_RE.fullmatch(source):
            raise ValueError("source_sha must be an exact lowercase 40-hex Git SHA")
        if not _SHA256_RE.fullmatch(policy):
            raise ValueError("policy_sha256 must be a lowercase SHA-256 digest")

        if evaluator is None:
            results = tuple(
                RedTeamCaseResult(
                    id=case.id,
                    boundary_id=case.boundary_id,
                    expected_decision=case.expected_decision,
                    actual_decision=None,
                    passed=None,
                    critical=self._critical[case.boundary_id],
                    payload_sha256=case.payload_sha256,
                )
                for case in self.corpus.cases
            )
            return RedTeamReport(
                source_sha=source,
                corpus_sha256=self.corpus.corpus_sha256,
                case_set_sha256=self.corpus.case_set_sha256,
                policy_sha256=policy,
                mode="mutation-free-contract",
                status=HarnessStatus.PASS,
                security_claim=False,
                critical_veto=False,
                results=results,
                coverage=self.corpus.coverage(),
            )

        evaluated: list[RedTeamCaseResult] = []
        for case in self.corpus.cases:
            actual = evaluator(case)
            if not isinstance(actual, ExpectedDecision):
                raise TypeError("red-team evaluator must return ExpectedDecision")
            passed = actual is case.expected_decision
            evaluated.append(
                RedTeamCaseResult(
                    id=case.id,
                    boundary_id=case.boundary_id,
                    expected_decision=case.expected_decision,
                    actual_decision=actual,
                    passed=passed,
                    critical=self._critical[case.boundary_id],
                    payload_sha256=case.payload_sha256,
                )
            )
        critical_veto = any(item.critical and item.passed is False for item in evaluated)
        status = (
            HarnessStatus.PASS
            if not critical_veto and all(item.passed is True for item in evaluated)
            else HarnessStatus.FAIL
        )
        return RedTeamReport(
            source_sha=source,
            corpus_sha256=self.corpus.corpus_sha256,
            case_set_sha256=self.corpus.case_set_sha256,
            policy_sha256=policy,
            mode="decision-evaluation",
            status=status,
            security_claim=True,
            critical_veto=critical_veto,
            results=tuple(evaluated),
            coverage=self.corpus.coverage(),
        )


def load_redteam_corpus(path: str | Path, *, repository_root: str | Path) -> RedTeamCorpus:
    root = Path(repository_root).resolve(strict=True)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.is_symlink():
        raise ValueError("red-team corpus cannot be a symlink")
    resolved = candidate.resolve(strict=True)
    if not _is_within(resolved, root):
        raise ValueError("red-team corpus must stay inside repository_root")
    if resolved.suffix.lower() != ".json" or not resolved.is_file():
        raise ValueError("red-team corpus must be a JSON file")
    if resolved.stat().st_size > _MAX_CORPUS_BYTES:
        raise ValueError("red-team corpus exceeds the bounded fixture size")
    raw = resolved.read_text(encoding="utf-8")
    _ensure_no_live_secret(raw, field_name="red-team corpus")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("red-team corpus must be a JSON object")
    corpus = RedTeamCorpus(
        metadata=dict(payload.get("metadata") or {}),
        boundaries=tuple(
            RedTeamBoundary.from_dict(item) for item in payload.get("boundaries", [])
        ),
        cases=tuple(RedTeamCase.from_dict(item) for item in payload.get("cases", [])),
        declared_sha256=str(payload.get("corpus_sha256", "")),
        schema_version=int(payload.get("schema_version", 0)),
    )
    corpus.validate()
    return corpus


def policy_sha256(policy: Mapping[str, Any] | Sequence[str]) -> str:
    return _sha256_text(_canonical_json(policy))
