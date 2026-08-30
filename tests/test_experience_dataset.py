from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.experience import (
    ContaminationReport,
    ContentRef,
    DatasetBuilder,
    DatasetFormat,
    DatasetPolicy,
    DatasetPolicyError,
    DatasetSource,
    DatasetSourceError,
    DatasetSplit,
    DedupItem,
    DedupPolicy,
    DedupResult,
    DuplicateHandling,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    PolicyDecision,
    ProtectedHoldout,
    ProtectedHoldoutRegistry,
    ProvenanceDescriptor,
    SanitizationEvidence,
    SanitizationStatus,
    TrainingAuthorization,
    TransformationRef,
    cluster_items,
    fingerprint_text,
    scan_contamination,
)

_SANITIZER = hashlib.sha256(b"r15.5-sanitizer-fixture").hexdigest()
_GOVERNANCE = hashlib.sha256(b"r15.5-governance-fixture").hexdigest()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _record(
    source_id: str,
    text: str,
    *,
    domain: str = "python",
    task: str = "repair",
    license_expression: str | None = "MIT",
    state: ExperienceState = ExperienceState.CURATED,
) -> ExperienceRecord:
    content_digest = _digest(text)
    origin_digest = _digest("origin:" + source_id)
    experience_id = ExperienceId.derive(
        workspace_id="workspace",
        source_id=source_id,
        origin_digest=origin_digest,
    )
    return ExperienceRecord(
        experience_id=experience_id,
        workspace_id="workspace",
        project_id="project",
        task_label=task,
        domain_label=domain,
        state=state,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="workspace",
            storage_key=(
                f"experience/sanitized/project/{experience_id.value}/"
                f"{content_digest}.txt"
            ),
            sha256=content_digest,
            byte_length=len(text.encode()),
        ),
        provenance=ProvenanceDescriptor(
            source_type="repository_fixture",
            source_id=source_id,
            origin_digest=origin_digest,
            project_scope="project",
            license_expression=license_expression,
        ),
        authorization=TrainingAuthorization(
            source_scope=PolicyDecision.ALLOW,
            consent=PolicyDecision.ALLOW,
            provenance=PolicyDecision.ALLOW,
            license=PolicyDecision.ALLOW,
            privacy=PolicyDecision.ALLOW,
        ),
        sanitization=SanitizationEvidence(
            status=SanitizationStatus.PASSED,
            sanitizer_digest=_SANITIZER,
        ),
        transformations=(
            TransformationRef(
                transformation_id="r15.3-sanitize-v1",
                input_digest=origin_digest,
                output_digest=content_digest,
                policy_digest=_GOVERNANCE,
            ),
        ),
    )


def _sources(
    *records_and_text: tuple[ExperienceRecord, str],
) -> list[DatasetSource]:
    return [
        DatasetSource(record, text, language="en")
        for record, text in records_and_text
    ]


def _dedup_and_report(
    sources: list[DatasetSource],
    policy: DedupPolicy,
) -> tuple[DedupResult, ContaminationReport]:
    items = [
        DedupItem(
            item_id=source.item_id,
            content_digest=source.record.content.sha256,
            fingerprint=fingerprint_text(source.text, policy),
        )
        for source in sources
    ]
    dedup = cluster_items(items, policy)
    registry = ProtectedHoldoutRegistry(policy.digest)
    return dedup, scan_contamination(items, dedup, registry, policy)


def _policy(
    dedup_policy: DedupPolicy,
    *,
    seed: int = 17,
    **kwargs: object,
) -> DatasetPolicy:
    return DatasetPolicy(
        seed=seed,
        sanitizer_digest=_SANITIZER,
        governance_policy_digest=_GOVERNANCE,
        dedup_policy_digest=dedup_policy.digest,
        **kwargs,
    )


def test_dataset_policy_digest_is_deterministic_and_sensitive() -> None:
    dedup = DedupPolicy()
    assert _policy(dedup).digest == _policy(dedup).digest
    assert _policy(dedup, seed=18).digest != _policy(dedup, seed=19).digest


def test_dataset_policy_rejects_invalid_split_contract() -> None:
    dedup = DedupPolicy()
    with pytest.raises(DatasetPolicyError):
        _policy(dedup, validation_weight=0)
    with pytest.raises(DatasetPolicyError):
        _policy(dedup, train_weight=-1)
    with pytest.raises(DatasetPolicyError):
        DatasetPolicy(
            seed=1,
            sanitizer_digest="bad",
            governance_policy_digest=_GOVERNANCE,
            dedup_policy_digest=dedup.digest,
        )


def test_split_assignment_is_stable_and_supports_internal_test() -> None:
    dedup = DedupPolicy()
    builder = DatasetBuilder(
        _policy(dedup, train_weight=1, validation_weight=1, test_weight=1)
    )
    group_ids = [
        "grp_" + hashlib.sha256(str(index).encode()).hexdigest()
        for index in range(200)
    ]
    first = [builder.assign_split(group_id) for group_id in group_ids]
    reverse = [builder.assign_split(group_id) for group_id in reversed(group_ids)]
    assert first == list(reversed(reverse))
    assert set(first) == {
        DatasetSplit.TRAIN,
        DatasetSplit.VALIDATION,
        DatasetSplit.TEST,
    }


def test_rebuild_is_byte_deterministic_and_group_safe() -> None:
    dedup_policy = DedupPolicy(lowercase_comparison=False)
    first = _record("source-a", "alpha beta gamma")
    second = _record("source-b", "alpha   beta gamma")
    third = _record("source-c", "different delta epsilon")
    sources = _sources(
        (first, "alpha beta gamma"),
        (second, "alpha   beta gamma"),
        (third, "different delta epsilon"),
    )
    dedup, report = _dedup_and_report(sources, dedup_policy)
    builder = DatasetBuilder(
        _policy(
            dedup_policy,
            duplicate_handling=DuplicateHandling.KEEP_GROUP,
        )
    )
    forward = builder.build(sources, dedup=dedup, contamination=report)
    reverse = builder.build(
        list(reversed(sources)), dedup=dedup, contamination=report
    )
    assert forward.manifest.canonical_json() == reverse.manifest.canonical_json()
    assert forward.card.canonical_json() == reverse.card.canonical_json()
    for split in DatasetSplit:
        assert forward.export_bytes(split) == reverse.export_bytes(split)
    grouped: dict[str, set[DatasetSplit]] = {}
    for entry in forward.manifest.entries:
        grouped.setdefault(entry.group_id, set()).add(entry.split)
    assert all(len(splits) == 1 for splits in grouped.values())


def test_representative_only_uses_r15_4_authority() -> None:
    dedup_policy = DedupPolicy(lowercase_comparison=True)
    first = _record("source-a", "SAME")
    second = _record("source-b", "same")
    sources = _sources((first, "SAME"), (second, "same"))
    dedup, report = _dedup_and_report(sources, dedup_policy)
    build = DatasetBuilder(_policy(dedup_policy)).build(
        sources, dedup=dedup, contamination=report
    )
    assert [entry.experience_id for entry in build.manifest.entries] == [
        dedup.clusters[0].representative_id
    ]
    assert build.manifest.selection_summary["excluded_by_reason"] == {
        "duplicate_member": 1
    }


def test_contaminated_group_is_excluded_whole_and_all_contaminated_fails() -> None:
    dedup_policy = DedupPolicy(lowercase_comparison=False)
    first = _record("source-a", "protected alpha beta")
    second = _record("source-b", "protected   alpha beta")
    safe = _record("source-safe", "ordinary gamma delta")
    sources = _sources(
        (first, "protected alpha beta"),
        (second, "protected   alpha beta"),
        (safe, "ordinary gamma delta"),
    )
    items = [
        DedupItem(
            item_id=source.item_id,
            content_digest=source.record.content.sha256,
            fingerprint=fingerprint_text(source.text, dedup_policy),
        )
        for source in sources
    ]
    dedup = cluster_items(items, dedup_policy)
    registry = ProtectedHoldoutRegistry(dedup_policy.digest)
    registry.register(
        ProtectedHoldout.from_text(
            "holdout-a", "protected alpha beta", dedup_policy
        )
    )
    report = scan_contamination(items, dedup, registry, dedup_policy)
    builder = DatasetBuilder(
        _policy(
            dedup_policy,
            duplicate_handling=DuplicateHandling.KEEP_GROUP,
        )
    )
    build = builder.build(sources, dedup=dedup, contamination=report)
    assert [entry.experience_id for entry in build.manifest.entries] == [
        safe.experience_id.value
    ]
    assert build.manifest.selection_summary["excluded_by_reason"] == {
        "benchmark_contamination": 2
    }
    with pytest.raises(DatasetSourceError, match="no eligible"):
        builder.build(sources[:2], dedup=dedup, contamination=report)


def test_source_policy_and_payload_mismatches_fail_closed() -> None:
    dedup_policy = DedupPolicy()
    record = _record("source-a", "alpha beta")
    sources = _sources((record, "alpha beta"))
    dedup, report = _dedup_and_report(sources, dedup_policy)
    wrong_sanitizer = replace(
        _policy(dedup_policy), sanitizer_digest=_digest("other-sanitizer")
    )
    with pytest.raises(DatasetPolicyError, match="sanitizer"):
        DatasetBuilder(wrong_sanitizer).build(
            sources, dedup=dedup, contamination=report
        )
    wrong_governance = replace(
        _policy(dedup_policy),
        governance_policy_digest=_digest("other-governance"),
    )
    with pytest.raises(DatasetPolicyError, match="governance"):
        DatasetBuilder(wrong_governance).build(
            sources, dedup=dedup, contamination=report
        )
    other_dedup = DedupPolicy(near_threshold=0.91)
    with pytest.raises(DatasetPolicyError, match="dedup"):
        DatasetBuilder(_policy(other_dedup)).build(
            sources, dedup=dedup, contamination=report
        )
    with pytest.raises(DatasetSourceError, match="digest"):
        DatasetSource(record, "tampered", language="en")


def test_manifest_card_are_safe_but_jsonl_is_governed_payload() -> None:
    dedup_policy = DedupPolicy()
    marker = "private-marker-r15-5-7812"
    text = f"sanitized training {marker}"
    record = _record("source-a", text)
    source = DatasetSource(record, text, language="en")
    dedup, report = _dedup_and_report([source], dedup_policy)
    build = DatasetBuilder(_policy(dedup_policy)).build(
        [source], dedup=dedup, contamination=report
    )
    manifest = build.manifest.canonical_json()
    card = build.card.canonical_json() + build.card_markdown
    assert marker not in manifest
    assert marker not in card
    assert record.content.storage_key not in manifest
    assert record.content.storage_key not in card
    assert marker.encode() in b"".join(build.exports.values())


def test_prompt_completion_and_conversation_forms_are_tokenizer_independent() -> None:
    dedup_policy = DedupPolicy(near_threshold=1.0)
    prompt_text = json.dumps(
        {"prompt": "Question", "completion": "Answer"},
        sort_keys=True,
        separators=(",", ":"),
    )
    chat_text = json.dumps(
        {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ]
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    prompt = DatasetSource(
        _record("source-prompt", prompt_text),
        prompt_text,
        format=DatasetFormat.PROMPT_COMPLETION,
        language="en",
    )
    chat = DatasetSource(
        _record("source-chat", chat_text),
        chat_text,
        format=DatasetFormat.CONVERSATIONAL,
        language="en",
    )
    sources = [prompt, chat]
    dedup, report = _dedup_and_report(sources, dedup_policy)
    build = DatasetBuilder(
        _policy(
            dedup_policy,
            duplicate_handling=DuplicateHandling.KEEP_GROUP,
        )
    ).build(sources, dedup=dedup, contamination=report)
    exported = b"".join(build.exports.values()).decode()
    assert '"prompt":"Question"' in exported
    assert '"completion":"Answer"' in exported
    assert '"messages":[' in exported
    assert "tokenizer" not in exported.lower()


def test_license_state_filters_and_domain_balancing_are_deterministic() -> None:
    dedup_policy = DedupPolicy(near_threshold=1.0)
    safe_python = _record("python-a", "python alpha", domain="python")
    other_python = _record("python-b", "python beta", domain="python")
    safe_godot = _record("godot-a", "godot alpha", domain="godot")
    no_license = _record(
        "license-a", "license alpha", license_expression=None
    )
    sanitized = _record(
        "state-a", "state alpha", state=ExperienceState.SANITIZED
    )
    sources = _sources(
        (safe_python, "python alpha"),
        (other_python, "python beta"),
        (safe_godot, "godot alpha"),
        (no_license, "license alpha"),
        (sanitized, "state alpha"),
    )
    dedup, report = _dedup_and_report(sources, dedup_policy)
    builder = DatasetBuilder(_policy(dedup_policy, max_groups_per_domain=1))
    first = builder.build(sources, dedup=dedup, contamination=report)
    reverse = builder.build(
        list(reversed(sources)), dedup=dedup, contamination=report
    )
    assert first.manifest.canonical_json() == reverse.manifest.canonical_json()
    assert first.manifest.selection_summary["selected_groups"] == 2
    assert {entry.domain for entry in first.manifest.entries} == {
        "godot",
        "python",
    }
    excluded = first.manifest.selection_summary["excluded_by_reason"]
    assert excluded["license_missing"] == 1
    assert excluded["state:sanitized"] == 1


def test_manifest_and_card_validate_against_repository_schemas() -> None:
    dedup_policy = DedupPolicy()
    record = _record("source-a", "alpha beta")
    source = DatasetSource(record, "alpha beta", language="en")
    dedup, report = _dedup_and_report([source], dedup_policy)
    build = DatasetBuilder(_policy(dedup_policy)).build(
        [source], dedup=dedup, contamination=report
    )
    manifest_schema = json.loads(
        Path("schemas/experience-dataset-manifest-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    card_schema = json.loads(
        Path("schemas/experience-dataset-card-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(manifest_schema).validate(build.manifest.to_dict())
    Draft202012Validator(card_schema).validate(build.card.to_dict())
