from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.intelligence.research import (
    ConflictState,
    FreshnessEvidence,
    FreshnessPolicy,
    ResearchArtifact,
    ResearchFindingKind,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    SourceIdentity,
    SourceMutability,
    SupersessionLink,
    TargetVersionConstraint,
    VersionEvidenceKind,
    VersionInterval,
    VersionObservation,
    VersionProvenanceReport,
    VersionRelation,
    VersionScheme,
    VersionedClaim,
    assess_freshness,
    assess_version,
    build_conflict_groups,
    observation_from_artifact,
    rank_claims,
    source_identity_from_artifact,
    target_constraint_from_project_dna,
)
from kodepoia.project.dna import Platform, ProjectDNA, ProjectType


H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64
H5 = "5" * 64
H6 = "6" * 64


def _exact_observation(
    value: str = "4.7.2",
    *,
    product: str = "Godot",
    scheme: VersionScheme = VersionScheme.SEMVER,
    suffix: str = "source.version",
) -> VersionObservation:
    return VersionObservation(
        product=product,
        kind=VersionEvidenceKind.EXACT,
        scheme=scheme,
        value=value,
        observed_at="2026-08-22T12:00:00Z",
        evidence_refs=(f"artifact:{suffix}",),
    )


def _target(
    value: str = "4.7.2",
    *,
    product: str = "Godot",
    scheme: VersionScheme = VersionScheme.SEMVER,
) -> TargetVersionConstraint:
    return TargetVersionConstraint(
        product=product,
        kind=VersionEvidenceKind.EXACT,
        scheme=scheme,
        value=value,
        evidence_refs=("project_dna:engine_version",),
    )


def _identity(
    *,
    locator: str = "https://docs.example.test/page",
    mutability: SourceMutability = SourceMutability.IMMUTABLE,
    revision: str = "rev-1",
) -> SourceIdentity:
    return SourceIdentity(
        locator=locator,
        mutability=mutability,
        revision=revision if mutability is SourceMutability.IMMUTABLE else "",
        snapshot_sha256=H6,
        evidence_refs=("artifact:snapshot",),
    )


def _claim(
    *,
    observation: VersionObservation,
    identity: SourceIdentity,
    value: str,
    finding_id: str,
    citation_id: str,
    freshness: ResearchFreshness = ResearchFreshness.CURRENT,
    relation: VersionRelation = VersionRelation.EXACT_MATCH,
    authority: int | None = 80,
) -> VersionedClaim:
    return VersionedClaim(
        finding_id=finding_id,
        finding_kind=ResearchFindingKind.SOURCE_FACT,
        claim_key="api.behavior",
        claim_value=value,
        observation_id=observation.observation_id,
        identity_id=identity.identity_id,
        citation_ids=(citation_id,),
        freshness=freshness,
        version_relation=relation,
        authority_rank=authority,
    )


def test_version_observation_kinds_remain_distinct_after_roundtrip() -> None:
    exact = _exact_observation()
    inferred = VersionObservation(
        product="Godot",
        kind=VersionEvidenceKind.INFERRED,
        scheme=VersionScheme.SEMVER,
        value="4.7.2",
        observed_at="2026-08-22T12:00:00Z",
        evidence_refs=("artifact:heading",),
        inference_reason="heading mentions the 4.7 branch",
    )
    ranged = VersionObservation(
        product="Godot",
        kind=VersionEvidenceKind.RANGE,
        scheme=VersionScheme.SEMVER,
        interval=VersionInterval(lower="4.7.0", upper="4.8.0"),
        evidence_refs=("artifact:manifest",),
    )
    unknown = VersionObservation(product="Godot", kind=VersionEvidenceKind.UNKNOWN)

    restored = tuple(
        VersionObservation.from_dict(item.to_dict()) for item in (exact, inferred, ranged, unknown)
    )
    assert tuple(item.kind for item in restored) == (
        VersionEvidenceKind.EXACT,
        VersionEvidenceKind.INFERRED,
        VersionEvidenceKind.RANGE,
        VersionEvidenceKind.UNKNOWN,
    )
    assert restored[1].inference_reason == inferred.inference_reason


def test_inferred_observation_requires_evidence_and_reason_and_never_becomes_exact() -> None:
    with pytest.raises(ValueError, match="Version evidence is required"):
        VersionObservation(
            product="Godot",
            kind=VersionEvidenceKind.INFERRED,
            value="4.7.2",
            inference_reason="guess",
        )
    with pytest.raises(ValueError, match="inference reason"):
        VersionObservation(
            product="Godot",
            kind=VersionEvidenceKind.INFERRED,
            value="4.7.2",
            evidence_refs=("artifact:x",),
        )

    inferred = VersionObservation(
        product="Godot",
        kind=VersionEvidenceKind.INFERRED,
        scheme=VersionScheme.SEMVER,
        value="4.7.2",
        evidence_refs=("artifact:x",),
        inference_reason="branch label only",
    )
    assessment = assess_version(inferred, _target())
    assert assessment.relation is VersionRelation.INFERRED_MATCH
    assert "remains_inferred" in assessment.reason


def test_target_constraint_cannot_be_inferred() -> None:
    with pytest.raises(ValueError, match="cannot silently be inferred"):
        TargetVersionConstraint(
            product="Godot",
            kind=VersionEvidenceKind.INFERRED,
            value="4.7.2",
            evidence_refs=("guess",),
        )


def test_project_dna_target_is_consumed_without_rewriting_dna() -> None:
    dna = ProjectDNA(
        schema_version=1,
        name="Fixture",
        project_type=ProjectType.TOOL,
        platforms=[Platform.WINDOWS],
        engine="Godot",
        engine_version="4.7.2",
    )
    before = dna.to_dict()
    constraint = target_constraint_from_project_dna(dna, scheme=VersionScheme.SEMVER)
    assert constraint is not None
    assert constraint.kind is VersionEvidenceKind.EXACT
    assert constraint.value == "4.7.2"
    assert constraint.evidence_refs == ("project_dna:engine", "project_dna:engine_version")
    assert dna.to_dict() == before

    dna.engine_version = None
    unknown = target_constraint_from_project_dna(dna, scheme=VersionScheme.SEMVER)
    assert unknown is not None
    assert unknown.kind is VersionEvidenceKind.UNKNOWN
    assert unknown.value == ""


def test_semver_exact_identity_keeps_build_metadata_but_range_uses_precedence() -> None:
    exact_with_build = _exact_observation("1.2.3+build.1")
    exact_other_build = _target("1.2.3+build.2")
    assert assess_version(exact_with_build, exact_other_build).relation is VersionRelation.MISMATCH

    ranged = VersionObservation(
        product="Godot",
        kind=VersionEvidenceKind.RANGE,
        scheme=VersionScheme.SEMVER,
        interval=VersionInterval(lower="1.2.3", upper="2.0.0"),
        evidence_refs=("artifact:range",),
    )
    target = _target("1.2.3+build.99")
    assert assess_version(ranged, target).relation is VersionRelation.RANGE_MATCH


def test_semver_prerelease_precedence_and_invalid_shape_are_conservative() -> None:
    ranged = VersionObservation(
        product="Godot",
        kind=VersionEvidenceKind.RANGE,
        scheme=VersionScheme.SEMVER,
        interval=VersionInterval(lower="1.0.0-rc.1", upper="1.0.0", include_upper=False),
        evidence_refs=("artifact:range",),
    )
    assert assess_version(ranged, _target("1.0.0-rc.2")).relation is VersionRelation.RANGE_MATCH
    assert assess_version(ranged, _target("1.0.0")).relation is VersionRelation.MISMATCH

    malformed = _exact_observation("Godot-4.7", scheme=VersionScheme.SEMVER)
    assert assess_version(malformed, _target()).relation is VersionRelation.UNKNOWN


def test_pep440_simple_release_padding_matches_without_assuming_full_parser() -> None:
    observation = _exact_observation("1.0", product="PythonPkg", scheme=VersionScheme.PEP440)
    target = _target("1.0.0", product="PythonPkg", scheme=VersionScheme.PEP440)
    assert assess_version(observation, target).relation is VersionRelation.EXACT_MATCH

    unsupported = _exact_observation("1.0rc1", product="PythonPkg", scheme=VersionScheme.PEP440)
    different = _target("1.0", product="PythonPkg", scheme=VersionScheme.PEP440)
    assert assess_version(unsupported, different).relation is VersionRelation.UNKNOWN


def test_opaque_versions_support_exact_identity_but_not_ordering() -> None:
    same = _exact_observation("vendor-r42", product="Tool", scheme=VersionScheme.OPAQUE)
    assert assess_version(same, _target("vendor-r42", product="Tool", scheme=VersionScheme.OPAQUE)).relation is VersionRelation.EXACT_MATCH
    assert assess_version(same, _target("vendor-r43", product="Tool", scheme=VersionScheme.OPAQUE)).relation is VersionRelation.MISMATCH

    ranged = VersionObservation(
        product="Tool",
        kind=VersionEvidenceKind.RANGE,
        scheme=VersionScheme.OPAQUE,
        interval=VersionInterval(lower="r40", upper="r50"),
        evidence_refs=("artifact:range",),
    )
    assert assess_version(ranged, _target("r42", product="Tool", scheme=VersionScheme.OPAQUE)).relation is VersionRelation.UNKNOWN


def test_artifact_without_version_remains_unknown_and_is_not_promoted_current() -> None:
    source = ResearchSource(
        kind=ResearchSourceKind.WEB,
        locator="https://docs.example.test/current",
        product="Godot",
        version="",
    )
    artifact = ResearchArtifact.from_content(
        source=source,
        content="Version not stated.",
        retrieved_at="2026-08-22T12:00:00Z",
        freshness=ResearchFreshness.CURRENT,
    )
    observation = observation_from_artifact(artifact, scheme=VersionScheme.SEMVER)
    assert observation.kind is VersionEvidenceKind.UNKNOWN
    assert assess_version(observation, _target()).relation is VersionRelation.UNKNOWN


def test_mutable_freshness_requires_revalidation_not_cache_retrieval_time() -> None:
    policy = FreshnessPolicy(mutable_revalidate_days=30, immutable_max_age_days=3650)
    missing = assess_freshness(
        FreshnessEvidence(
            mutability=SourceMutability.MUTABLE,
            observed_or_updated_at="2026-08-22T10:00:00Z",
            validated_at=None,
        ),
        as_of="2026-08-22T12:00:00Z",
        policy=policy,
    )
    assert missing.freshness is ResearchFreshness.UNKNOWN
    assert missing.reason == "mutable_source_has_no_revalidation_evidence"

    current = assess_freshness(
        FreshnessEvidence(
            mutability=SourceMutability.MUTABLE,
            validated_at="2026-08-01T00:00:00Z",
        ),
        as_of="2026-08-22T12:00:00Z",
        policy=policy,
    )
    assert current.freshness is ResearchFreshness.CURRENT

    stale = assess_freshness(
        FreshnessEvidence(
            mutability=SourceMutability.MUTABLE,
            validated_at="2026-06-01T00:00:00Z",
        ),
        as_of="2026-08-22T12:00:00Z",
        policy=policy,
    )
    assert stale.freshness is ResearchFreshness.STALE

    future = assess_freshness(
        FreshnessEvidence(
            mutability=SourceMutability.MUTABLE,
            validated_at="2026-08-23T00:00:00Z",
        ),
        as_of="2026-08-22T12:00:00Z",
        policy=policy,
    )
    assert future.freshness is ResearchFreshness.UNKNOWN
    assert future.reason == "freshness_basis_is_in_the_future"


def test_source_identity_requires_immutable_evidence_and_artifact_adapter_hash_binds_snapshot() -> None:
    with pytest.raises(ValueError, match="Immutable source identity requires"):
        SourceIdentity(
            locator="https://github.com/example/repo/blob/sha/file.md",
            mutability=SourceMutability.IMMUTABLE,
        )

    source = ResearchSource(
        kind=ResearchSourceKind.GITHUB,
        locator="https://github.com/example/repo/blob/abc/file.md",
        product="Tool",
        version="1.0.0",
    )
    artifact = ResearchArtifact.from_content(
        source=source,
        content="immutable snapshot",
        retrieved_at="2026-08-22T12:00:00Z",
    )
    identity = source_identity_from_artifact(
        artifact,
        mutability=SourceMutability.IMMUTABLE,
        revision="abc",
        evidence_refs=("github:commit_sha",),
    )
    assert identity.snapshot_sha256 == artifact.content_sha256
    assert identity.revision == "abc"


def test_conflicting_old_and_new_claims_remain_visible_with_supersession_link() -> None:
    old_observation = _exact_observation("4.6.2", suffix="old")
    new_observation = _exact_observation("4.7.2", suffix="new")
    old_identity = _identity(locator="https://docs.example.test/4.6", revision="rev-old")
    new_identity = _identity(locator="https://docs.example.test/4.7", revision="rev-new")
    old_claim = _claim(
        observation=old_observation,
        identity=old_identity,
        value="legacy",
        finding_id=H1,
        citation_id=H2,
        freshness=ResearchFreshness.STALE,
        relation=VersionRelation.MISMATCH,
    )
    new_claim = _claim(
        observation=new_observation,
        identity=new_identity,
        value="current",
        finding_id=H3,
        citation_id=H4,
        relation=VersionRelation.EXACT_MATCH,
    )
    link = SupersessionLink(
        older_claim_id=old_claim.claim_id,
        newer_claim_id=new_claim.claim_id,
        reason="official 4.7 documentation supersedes the 4.6 behavior for the target version",
        evidence_refs=("citation:release-notes",),
    )

    groups = build_conflict_groups((old_claim, new_claim), (link,))
    assert len(groups) == 1
    assert groups[0].state is ConflictState.CONFLICT
    assert set(groups[0].claim_ids) == {old_claim.claim_id, new_claim.claim_id}
    assert groups[0].supersession_link_ids == (link.link_id,)


def test_agreement_and_unresolved_groups_are_explicit() -> None:
    observation = _exact_observation()
    identity_a = _identity(locator="https://a.example.test", revision="a")
    identity_b = _identity(locator="https://b.example.test", revision="b")
    first = _claim(
        observation=observation,
        identity=identity_a,
        value="same",
        finding_id=H1,
        citation_id=H2,
    )
    second = _claim(
        observation=observation,
        identity=identity_b,
        value="same",
        finding_id=H3,
        citation_id=H4,
    )
    assert build_conflict_groups((first,))[0].state is ConflictState.UNRESOLVED
    assert build_conflict_groups((first, second))[0].state is ConflictState.AGREEMENT


def test_ranking_is_explicit_deterministic_and_never_drops_contradictory_claims() -> None:
    observation = _exact_observation()
    immutable = _identity(locator="https://immutable.example.test", revision="sha")
    mutable = _identity(
        locator="https://forum.example.test/thread",
        mutability=SourceMutability.MUTABLE,
    )
    preferred = _claim(
        observation=observation,
        identity=immutable,
        value="preferred",
        finding_id=H1,
        citation_id=H2,
        freshness=ResearchFreshness.CURRENT,
        relation=VersionRelation.EXACT_MATCH,
        authority=90,
    )
    contradictory = _claim(
        observation=observation,
        identity=mutable,
        value="contradictory",
        finding_id=H3,
        citation_id=H4,
        freshness=ResearchFreshness.STALE,
        relation=VersionRelation.UNKNOWN,
        authority=20,
    )
    ranked = rank_claims((contradictory, preferred), (mutable, immutable))
    assert ranked == (preferred, contradictory)
    assert {item.claim_id for item in ranked} == {preferred.claim_id, contradictory.claim_id}
    assert "popularity" not in preferred.to_dict()
    assert "source_count" not in preferred.to_dict()


def test_source_fact_claim_requires_citation_evidence() -> None:
    observation = _exact_observation()
    identity = _identity()
    with pytest.raises(ValueError, match="citation evidence"):
        VersionedClaim(
            finding_id=H1,
            finding_kind=ResearchFindingKind.SOURCE_FACT,
            claim_key="api.behavior",
            claim_value="value",
            observation_id=observation.observation_id,
            identity_id=identity.identity_id,
            citation_ids=(),
            freshness=ResearchFreshness.UNKNOWN,
            version_relation=VersionRelation.UNKNOWN,
        )


def test_version_provenance_report_roundtrip_schema_and_tamper_rejection() -> None:
    target = _target()
    old_observation = _exact_observation("4.6.2", suffix="old")
    new_observation = _exact_observation("4.7.2", suffix="new")
    old_identity = _identity(locator="https://docs.example.test/4.6", revision="old")
    new_identity = _identity(locator="https://docs.example.test/4.7", revision="new")
    old_claim = _claim(
        observation=old_observation,
        identity=old_identity,
        value="legacy",
        finding_id=H1,
        citation_id=H2,
        freshness=ResearchFreshness.STALE,
        relation=VersionRelation.MISMATCH,
    )
    new_claim = _claim(
        observation=new_observation,
        identity=new_identity,
        value="current",
        finding_id=H3,
        citation_id=H4,
    )
    link = SupersessionLink(
        older_claim_id=old_claim.claim_id,
        newer_claim_id=new_claim.claim_id,
        reason="new target-version documentation",
        evidence_refs=("artifact:release-notes",),
    )
    report = VersionProvenanceReport.create(
        target=target,
        observations=(old_observation, new_observation),
        identities=(old_identity, new_identity),
        claims=(old_claim, new_claim),
        supersession_links=(link,),
        generated_at="2026-08-22T12:00:00Z",
    )

    payload = report.to_dict()
    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "schemas" / "research-version-provenance-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(payload)
    restored = VersionProvenanceReport.from_dict(payload)
    assert restored.digest_sha256 == report.digest_sha256
    assert restored.groups[0].state is ConflictState.CONFLICT

    tampered = json.loads(json.dumps(payload))
    tampered["claims"][0]["claim_value"] = "silently-rewritten"
    with pytest.raises(ValueError):
        VersionProvenanceReport.from_dict(tampered)


def test_report_rejects_missing_observation_or_identity_references() -> None:
    target = _target()
    observation = _exact_observation()
    identity = _identity()
    claim = _claim(
        observation=observation,
        identity=identity,
        value="value",
        finding_id=H1,
        citation_id=H2,
    )
    with pytest.raises(ValueError, match="absent observation"):
        VersionProvenanceReport.create(
            target=target,
            observations=(),
            identities=(identity,),
            claims=(claim,),
            generated_at="2026-08-22T12:00:00Z",
        )
    with pytest.raises(ValueError, match="absent source identity"):
        VersionProvenanceReport.create(
            target=target,
            observations=(observation,),
            identities=(),
            claims=(claim,),
            generated_at="2026-08-22T12:00:00Z",
        )
