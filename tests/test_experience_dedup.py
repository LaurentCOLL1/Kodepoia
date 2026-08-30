from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.experience import (
    DedupError,
    DedupItem,
    DedupPolicy,
    MatchType,
    PolicyMismatch,
    ProtectedHoldout,
    ProtectedHoldoutRegistry,
    cluster_items,
    fingerprint_text,
    jaccard_similarity,
    normalize_for_comparison,
    scan_contamination,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _item(item_id: str, text: str, policy: DedupPolicy) -> DedupItem:
    return DedupItem(
        item_id=item_id,
        content_digest=_digest(text),
        fingerprint=fingerprint_text(text, policy),
    )


def test_normalization_is_platform_stable_and_comparison_only() -> None:
    policy = DedupPolicy(lowercase_comparison=True)
    left = "  Café\r\nVALUE\t =  1  "
    right = "cafe\u0301\nvalue = 1"
    assert normalize_for_comparison(left, policy) == normalize_for_comparison(right, policy)
    assert left.startswith("  Café")


def test_policy_digest_is_deterministic_and_policy_sensitive() -> None:
    assert DedupPolicy().digest == DedupPolicy().digest
    assert DedupPolicy(near_threshold=0.81).digest != DedupPolicy(near_threshold=0.82).digest


def test_invalid_policy_fails_closed() -> None:
    with pytest.raises(DedupError):
        DedupPolicy(shingle_size=0)
    with pytest.raises(DedupError):
        DedupPolicy(near_threshold=float("nan"))
    with pytest.raises(DedupError):
        DedupPolicy(near_threshold=1.1)


def test_exact_duplicates_cluster_independent_of_row_order() -> None:
    policy = DedupPolicy(lowercase_comparison=False)
    first = _item("item-a", "alpha beta\ngamma", policy)
    second = _item("item-b", "alpha   beta\r\ngamma", policy)
    third = _item("item-c", "different content", policy)
    forward = cluster_items([first, second, third], policy)
    reverse = cluster_items([third, second, first], policy)
    assert forward.group_by_item == reverse.group_by_item
    assert forward.clusters == reverse.clusters
    assert forward.group_for("item-a") == forward.group_for("item-b")
    assert forward.group_for("item-a") != forward.group_for("item-c")


def test_near_duplicate_threshold_is_inclusive() -> None:
    policy = DedupPolicy(shingle_size=2, near_threshold=0.60, lowercase_comparison=False)
    left = _item("left", "alpha beta gamma delta epsilon", policy)
    right = _item("right", "alpha beta gamma delta zeta", policy)
    similarity = jaccard_similarity(left.fingerprint, right.fingerprint)
    assert similarity == pytest.approx(0.60)
    result = cluster_items([left, right], policy)
    assert result.group_for("left") == result.group_for("right")


def test_below_threshold_items_remain_separate() -> None:
    policy = DedupPolicy(shingle_size=2, near_threshold=0.61, lowercase_comparison=False)
    left = _item("left", "alpha beta gamma delta epsilon", policy)
    right = _item("right", "alpha beta gamma delta zeta", policy)
    result = cluster_items([left, right], policy)
    assert result.group_for("left") != result.group_for("right")


def test_duplicate_cluster_is_transitive_and_has_one_split_group() -> None:
    policy = DedupPolicy(shingle_size=1, near_threshold=0.50, lowercase_comparison=False)
    first = _item("a", "one two", policy)
    middle = _item("b", "one two three", policy)
    last = _item("c", "two three", policy)
    result = cluster_items([last, first, middle], policy)
    groups = {result.group_for(item_id) for item_id in ("a", "b", "c")}
    assert len(groups) == 1
    assert result.clusters[0].member_ids == ("a", "b", "c")


def test_representative_selection_is_deterministic() -> None:
    policy = DedupPolicy(lowercase_comparison=True)
    first = _item("z-item", "SAME", policy)
    second = _item("a-item", "same", policy)
    result = cluster_items([first, second], policy)
    assert result.clusters[0].representative_id == "a-item"


def test_duplicate_item_ids_are_rejected() -> None:
    policy = DedupPolicy()
    item = _item("duplicate", "hello", policy)
    with pytest.raises(DedupError):
        cluster_items([item, item], policy)


def test_fingerprint_policy_mismatch_is_rejected() -> None:
    first_policy = DedupPolicy(near_threshold=0.80)
    second_policy = DedupPolicy(near_threshold=0.90)
    item = _item("item", "hello world", first_policy)
    with pytest.raises(PolicyMismatch):
        cluster_items([item], second_policy)
    with pytest.raises(PolicyMismatch):
        jaccard_similarity(item.fingerprint, fingerprint_text("hello world", second_policy))


def test_exact_holdout_match_quarantines_entire_duplicate_group() -> None:
    policy = DedupPolicy(lowercase_comparison=False)
    first = _item("item-a", "protected alpha beta", policy)
    second = _item("item-b", "protected   alpha beta", policy)
    safe = _item("item-safe", "ordinary gamma delta", policy)
    dedup = cluster_items([first, second, safe], policy)
    registry = ProtectedHoldoutRegistry(policy.digest)
    registry.register(ProtectedHoldout.from_text("holdout-1", "protected alpha beta", policy))
    report = scan_contamination([safe, second, first], dedup, registry, policy)
    assert report.quarantined_item_ids == ("item-a", "item-b")
    assert report.findings
    assert all(finding.match_type is MatchType.EXACT for finding in report.findings)
    assert report.contaminated_group_ids == (dedup.group_for("item-a"),)


def test_near_holdout_match_requires_review_and_quarantines_group() -> None:
    policy = DedupPolicy(shingle_size=2, near_threshold=0.60, lowercase_comparison=False)
    item = _item("candidate", "alpha beta gamma delta zeta", policy)
    dedup = cluster_items([item], policy)
    registry = ProtectedHoldoutRegistry(policy.digest)
    registry.register(
        ProtectedHoldout.from_text("holdout-near", "alpha beta gamma delta epsilon", policy)
    )
    report = scan_contamination([item], dedup, registry, policy)
    assert report.quarantined_item_ids == ("candidate",)
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.match_type is MatchType.NEAR
    assert finding.review_required is True
    assert finding.similarity == pytest.approx(0.60)


def test_below_threshold_holdout_does_not_quarantine() -> None:
    policy = DedupPolicy(shingle_size=2, near_threshold=0.61, lowercase_comparison=False)
    item = _item("candidate", "alpha beta gamma delta zeta", policy)
    dedup = cluster_items([item], policy)
    registry = ProtectedHoldoutRegistry(policy.digest)
    registry.register(
        ProtectedHoldout.from_text("holdout-near", "alpha beta gamma delta epsilon", policy)
    )
    report = scan_contamination([item], dedup, registry, policy)
    assert report.quarantined_item_ids == ()
    assert report.findings == ()


def test_safe_reports_never_include_raw_holdout_or_candidate_content() -> None:
    policy = DedupPolicy(shingle_size=2, near_threshold=0.50, lowercase_comparison=False)
    raw_holdout = "benchmark secret-marker-7812 alpha beta gamma"
    raw_candidate = "benchmark secret-marker-7812 alpha beta delta"
    item = _item("candidate", raw_candidate, policy)
    dedup = cluster_items([item], policy)
    registry = ProtectedHoldoutRegistry(policy.digest)
    registry.register(ProtectedHoldout.from_text("holdout-secret", raw_holdout, policy))
    report = scan_contamination([item], dedup, registry, policy)
    serialized = json.dumps(report.safe_descriptor(), sort_keys=True)
    manifest = json.dumps(registry.safe_manifest(), sort_keys=True)
    assert "secret-marker-7812" not in serialized
    assert "secret-marker-7812" not in manifest
    assert raw_holdout not in serialized
    assert raw_candidate not in serialized


def test_registry_is_idempotent_but_rejects_conflicting_identity() -> None:
    policy = DedupPolicy()
    registry = ProtectedHoldoutRegistry(policy.digest)
    first = ProtectedHoldout.from_text("holdout", "alpha beta", policy)
    registry.register(first)
    registry.register(first)
    with pytest.raises(DedupError):
        registry.register(ProtectedHoldout.from_text("holdout", "other text", policy))


def test_registry_rejects_policy_mismatch() -> None:
    first = DedupPolicy(near_threshold=0.8)
    second = DedupPolicy(near_threshold=0.9)
    registry = ProtectedHoldoutRegistry(first.digest)
    with pytest.raises(PolicyMismatch):
        registry.register(ProtectedHoldout.from_text("holdout", "text", second))


def test_safe_holdout_manifest_validates_against_repository_schema() -> None:
    policy = DedupPolicy()
    registry = ProtectedHoldoutRegistry(policy.digest)
    registry.register(ProtectedHoldout.from_text("holdout-a", "alpha beta", policy))
    schema_path = Path("schemas/experience-holdout-registry-v1.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(registry.safe_manifest())


def test_group_identity_changes_when_policy_changes() -> None:
    first_policy = DedupPolicy(lowercase_comparison=False, near_threshold=0.8)
    second_policy = DedupPolicy(lowercase_comparison=False, near_threshold=0.9)
    first_group = cluster_items([_item("item", "alpha beta", first_policy)], first_policy)
    second_group = cluster_items([_item("item", "alpha beta", second_policy)], second_policy)
    assert first_group.clusters[0].group_id != second_group.clusters[0].group_id


def test_scan_requires_consistent_policy_authority() -> None:
    first = DedupPolicy(near_threshold=0.8)
    second = DedupPolicy(near_threshold=0.9)
    item = _item("item", "alpha beta", first)
    dedup = cluster_items([item], first)
    registry = ProtectedHoldoutRegistry(first.digest)
    with pytest.raises(PolicyMismatch):
        scan_contamination([item], dedup, registry, second)
