from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable, Mapping

DEDUP_VERSION = "r15.4-dedup-v1"
HOLDOUT_SCHEMA = "kodepoia.experience.protected-holdout-registry"
HOLDOUT_SCHEMA_VERSION = 1
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
_SPACE = re.compile(r"[ \t]+")


class DedupError(ValueError):
    """Base error for deterministic deduplication/contamination failures."""


class PolicyMismatch(DedupError):
    """Raised when fingerprints from different policies are combined."""


class MatchType(StrEnum):
    EXACT = "exact"
    NEAR = "near"


@dataclass(frozen=True, slots=True)
class DedupPolicy:
    shingle_size: int = 3
    near_threshold: float = 0.80
    lowercase_comparison: bool = True
    unicode_form: str = "NFKC"
    version: str = DEDUP_VERSION

    def __post_init__(self) -> None:
        if not 1 <= self.shingle_size <= 16:
            raise DedupError("shingle_size must be between 1 and 16")
        if not math.isfinite(self.near_threshold) or not 0.0 <= self.near_threshold <= 1.0:
            raise DedupError("near_threshold must be finite and between 0 and 1")
        if self.unicode_form not in {"NFC", "NFKC"}:
            raise DedupError("unicode_form must be NFC or NFKC")
        _require_safe_id("version", self.version)

    def descriptor(self) -> dict[str, object]:
        return {
            "lowercase_comparison": self.lowercase_comparison,
            "near_threshold": self.near_threshold,
            "shingle_size": self.shingle_size,
            "unicode_form": self.unicode_form,
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        payload = json.dumps(self.descriptor(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ComparisonFingerprint:
    exact_digest: str
    shingle_hashes: tuple[str, ...]
    token_count: int
    policy_digest: str

    def __post_init__(self) -> None:
        _require_digest("exact_digest", self.exact_digest)
        _require_digest("policy_digest", self.policy_digest)
        if self.token_count < 0:
            raise DedupError("token_count must be >= 0")
        if tuple(sorted(set(self.shingle_hashes))) != self.shingle_hashes:
            raise DedupError("shingle_hashes must be unique and sorted")
        for value in self.shingle_hashes:
            _require_digest("shingle hash", value)

    def safe_descriptor(self) -> dict[str, object]:
        return {
            "exact_digest": self.exact_digest,
            "policy_digest": self.policy_digest,
            "shingle_count": len(self.shingle_hashes),
            "token_count": self.token_count,
        }


@dataclass(frozen=True, slots=True)
class DedupItem:
    item_id: str
    content_digest: str
    fingerprint: ComparisonFingerprint

    def __post_init__(self) -> None:
        _require_safe_id("item_id", self.item_id)
        _require_digest("content_digest", self.content_digest)


@dataclass(frozen=True, slots=True)
class DuplicateCluster:
    group_id: str
    member_ids: tuple[str, ...]
    representative_id: str
    policy_digest: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"grp_[0-9a-f]{64}", self.group_id):
            raise DedupError("group_id must be grp_<64 lowercase hex chars>")
        if not self.member_ids or tuple(sorted(set(self.member_ids))) != self.member_ids:
            raise DedupError("member_ids must be non-empty, unique and sorted")
        if self.representative_id not in self.member_ids:
            raise DedupError("representative_id must belong to member_ids")
        _require_digest("policy_digest", self.policy_digest)


@dataclass(frozen=True, slots=True)
class DedupResult:
    policy_digest: str
    clusters: tuple[DuplicateCluster, ...]
    group_by_item: Mapping[str, str] = field(repr=False)

    def __post_init__(self) -> None:
        _require_digest("policy_digest", self.policy_digest)
        cluster_groups = {cluster.group_id for cluster in self.clusters}
        if any(group_id not in cluster_groups for group_id in self.group_by_item.values()):
            raise DedupError("group_by_item references an unknown cluster")

    def group_for(self, item_id: str) -> str:
        try:
            return self.group_by_item[item_id]
        except KeyError as exc:
            raise DedupError(f"unknown dedup item: {item_id}") from exc


@dataclass(frozen=True, slots=True)
class ProtectedHoldout:
    holdout_id: str
    fingerprint: ComparisonFingerprint

    def __post_init__(self) -> None:
        _require_safe_id("holdout_id", self.holdout_id)

    @classmethod
    def from_text(cls, holdout_id: str, text: str, policy: DedupPolicy) -> ProtectedHoldout:
        return cls(holdout_id=holdout_id, fingerprint=fingerprint_text(text, policy))

    def safe_descriptor(self) -> dict[str, object]:
        return {"holdout_id": self.holdout_id, "fingerprint": self.fingerprint.safe_descriptor()}


@dataclass(slots=True)
class ProtectedHoldoutRegistry:
    policy_digest: str
    _entries: dict[str, ProtectedHoldout] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        _require_digest("policy_digest", self.policy_digest)

    def register(self, holdout: ProtectedHoldout) -> None:
        if holdout.fingerprint.policy_digest != self.policy_digest:
            raise PolicyMismatch("holdout fingerprint policy does not match registry policy")
        existing = self._entries.get(holdout.holdout_id)
        if existing is not None and existing != holdout:
            raise DedupError(f"holdout_id already registered with different fingerprint: {holdout.holdout_id}")
        self._entries[holdout.holdout_id] = holdout

    def entries(self) -> tuple[ProtectedHoldout, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))

    def safe_manifest(self) -> dict[str, object]:
        return {
            "schema": HOLDOUT_SCHEMA,
            "schema_version": HOLDOUT_SCHEMA_VERSION,
            "policy_digest": self.policy_digest,
            "holdouts": [entry.safe_descriptor() for entry in self.entries()],
        }


@dataclass(frozen=True, slots=True)
class ContaminationFinding:
    item_id: str
    holdout_id: str
    group_id: str
    match_type: MatchType
    similarity: float
    threshold: float
    item_exact_digest: str
    holdout_exact_digest: str
    policy_digest: str
    review_required: bool

    def safe_descriptor(self) -> dict[str, object]:
        return {
            "group_id": self.group_id,
            "holdout_exact_digest": self.holdout_exact_digest,
            "holdout_id": self.holdout_id,
            "item_exact_digest": self.item_exact_digest,
            "item_id": self.item_id,
            "match_type": self.match_type.value,
            "policy_digest": self.policy_digest,
            "review_required": self.review_required,
            "similarity": self.similarity,
            "threshold": self.threshold,
        }


@dataclass(frozen=True, slots=True)
class ContaminationReport:
    policy_digest: str
    findings: tuple[ContaminationFinding, ...]
    quarantined_item_ids: tuple[str, ...]
    contaminated_group_ids: tuple[str, ...]

    def safe_descriptor(self) -> dict[str, object]:
        return {
            "contaminated_group_ids": list(self.contaminated_group_ids),
            "finding_count": len(self.findings),
            "findings": [finding.safe_descriptor() for finding in self.findings],
            "policy_digest": self.policy_digest,
            "quarantined_item_ids": list(self.quarantined_item_ids),
        }


def normalize_for_comparison(text: str, policy: DedupPolicy) -> str:
    if not isinstance(text, str):
        raise DedupError("comparison content must be text")
    normalized = unicodedata.normalize(policy.unicode_form, text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [_SPACE.sub(" ", line).strip() for line in normalized.split("\n")]
    normalized = "\n".join(lines).strip()
    if policy.lowercase_comparison:
        normalized = normalized.casefold()
    return normalized


def fingerprint_text(text: str, policy: DedupPolicy) -> ComparisonFingerprint:
    normalized = normalize_for_comparison(text, policy)
    exact_digest = hashlib.sha256(normalized.encode()).hexdigest()
    tokens = _TOKEN.findall(normalized)
    shingles = _shingles(tokens, policy.shingle_size)
    return ComparisonFingerprint(
        exact_digest=exact_digest,
        shingle_hashes=tuple(sorted(hashlib.sha256(value.encode()).hexdigest() for value in shingles)),
        token_count=len(tokens),
        policy_digest=policy.digest,
    )


def jaccard_similarity(left: ComparisonFingerprint, right: ComparisonFingerprint) -> float:
    if left.policy_digest != right.policy_digest:
        raise PolicyMismatch("cannot compare fingerprints created under different policies")
    left_set = set(left.shingle_hashes)
    right_set = set(right.shingle_hashes)
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 1.0


def cluster_items(items: Iterable[DedupItem], policy: DedupPolicy) -> DedupResult:
    ordered = tuple(sorted(items, key=lambda item: item.item_id))
    ids = [item.item_id for item in ordered]
    if len(ids) != len(set(ids)):
        raise DedupError("item_id values must be unique")
    for item in ordered:
        if item.fingerprint.policy_digest != policy.digest:
            raise PolicyMismatch("item fingerprint policy does not match dedup policy")

    parent = {item.item_id: item.item_id for item in ordered}

    def find(item_id: str) -> str:
        while parent[item_id] != item_id:
            parent[item_id] = parent[parent[item_id]]
            item_id = parent[item_id]
        return item_id

    def union(left_id: str, right_id: str) -> None:
        left_root = find(left_id)
        right_root = find(right_id)
        if left_root == right_root:
            return
        first, second = sorted((left_root, right_root))
        parent[second] = first

    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            exact = left.fingerprint.exact_digest == right.fingerprint.exact_digest
            if exact or jaccard_similarity(left.fingerprint, right.fingerprint) >= policy.near_threshold:
                union(left.item_id, right.item_id)

    grouped: dict[str, list[DedupItem]] = {}
    for item in ordered:
        grouped.setdefault(find(item.item_id), []).append(item)

    clusters: list[DuplicateCluster] = []
    group_by_item: dict[str, str] = {}
    for members in sorted(grouped.values(), key=lambda values: tuple(item.item_id for item in values)):
        member_ids = tuple(sorted(item.item_id for item in members))
        identity = "\n".join(
            f"{item.item_id}:{item.content_digest}:{item.fingerprint.exact_digest}"
            for item in sorted(members, key=lambda value: value.item_id)
        )
        group_id = "grp_" + hashlib.sha256(f"{policy.digest}\n{identity}".encode()).hexdigest()
        representative = min(members, key=lambda item: (item.fingerprint.exact_digest, item.item_id)).item_id
        cluster = DuplicateCluster(
            group_id=group_id,
            member_ids=member_ids,
            representative_id=representative,
            policy_digest=policy.digest,
        )
        clusters.append(cluster)
        for item_id in member_ids:
            group_by_item[item_id] = group_id

    clusters.sort(key=lambda cluster: cluster.group_id)
    return DedupResult(policy_digest=policy.digest, clusters=tuple(clusters), group_by_item=group_by_item)


def scan_contamination(
    items: Iterable[DedupItem],
    dedup: DedupResult,
    registry: ProtectedHoldoutRegistry,
    policy: DedupPolicy,
) -> ContaminationReport:
    ordered = tuple(sorted(items, key=lambda item: item.item_id))
    if dedup.policy_digest != policy.digest or registry.policy_digest != policy.digest:
        raise PolicyMismatch("dedup result/holdout registry must use the active policy")

    findings: list[ContaminationFinding] = []
    contaminated_groups: set[str] = set()
    for item in ordered:
        if item.fingerprint.policy_digest != policy.digest:
            raise PolicyMismatch("item fingerprint policy does not match contamination policy")
        group_id = dedup.group_for(item.item_id)
        for holdout in registry.entries():
            exact = item.fingerprint.exact_digest == holdout.fingerprint.exact_digest
            similarity = 1.0 if exact else jaccard_similarity(item.fingerprint, holdout.fingerprint)
            if exact or similarity >= policy.near_threshold:
                match_type = MatchType.EXACT if exact else MatchType.NEAR
                findings.append(
                    ContaminationFinding(
                        item_id=item.item_id,
                        holdout_id=holdout.holdout_id,
                        group_id=group_id,
                        match_type=match_type,
                        similarity=round(similarity, 12),
                        threshold=policy.near_threshold,
                        item_exact_digest=item.fingerprint.exact_digest,
                        holdout_exact_digest=holdout.fingerprint.exact_digest,
                        policy_digest=policy.digest,
                        review_required=match_type is MatchType.NEAR,
                    )
                )
                contaminated_groups.add(group_id)

    quarantined = sorted(
        item_id for item_id, group_id in dedup.group_by_item.items() if group_id in contaminated_groups
    )
    findings.sort(key=lambda finding: (finding.group_id, finding.item_id, finding.holdout_id))
    return ContaminationReport(
        policy_digest=policy.digest,
        findings=tuple(findings),
        quarantined_item_ids=tuple(quarantined),
        contaminated_group_ids=tuple(sorted(contaminated_groups)),
    )


def _shingles(tokens: list[str], size: int) -> set[str]:
    if not tokens:
        return {"<empty>"}
    if len(tokens) <= size:
        return {"\x1f".join(tokens)}
    return {"\x1f".join(tokens[index : index + size]) for index in range(len(tokens) - size + 1)}


def _require_digest(name: str, value: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise DedupError(f"{name} must be 64 lowercase hex chars")


def _require_safe_id(name: str, value: str) -> None:
    if not _SAFE_ID.fullmatch(value):
        raise DedupError(f"{name} must be a stable safe identifier")
