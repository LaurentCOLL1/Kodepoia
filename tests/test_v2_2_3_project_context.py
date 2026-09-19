from __future__ import annotations

import hashlib

import pytest

from kodepoia.intelligence.project_context import (
    ExplainableProjectContextBuilder,
    ProjectContextCandidate,
    ProjectContextDecision,
    ProjectContextOverride,
    ProjectContextReason,
)
from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
)
from kodepoia.intelligence.project_retrieval import (
    ProjectEmbeddingIdentity,
    ProjectRetrievalHit,
    ProjectRetrievalRequest,
    ProjectRetrievalResult,
    ProjectRetrievalSourceRef,
    ProjectRetrievalState,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _ref(
    seed: str,
    *,
    kind: ProjectKnowledgeSourceKind,
    trust: str,
    locator: str,
    version: str = "",
    provenance: dict[str, object] | None = None,
) -> ProjectRetrievalSourceRef:
    content_sha = _digest(f"content:{seed}")
    return ProjectRetrievalSourceRef(
        knowledge_id=_digest(f"knowledge:{seed}:{kind.value}"),
        source_kind=kind,
        source_identity=_digest(f"identity:{seed}:{kind.value}"),
        source_digest_sha256=_digest(f"source:{seed}:{kind.value}"),
        content_sha256=content_sha,
        locator=locator,
        trust_class=trust,
        freshness="current",
        version=version,
        state=ProjectKnowledgeState.ACTIVE,
        provenance=provenance or {"seed": seed},
    )


def _hit(
    seed: str,
    text: str,
    score: float,
    *,
    refs: tuple[ProjectRetrievalSourceRef, ...] | None = None,
) -> ProjectRetrievalHit:
    source_refs = refs or (
        _ref(
            seed,
            kind=ProjectKnowledgeSourceKind.PROJECT_FILE,
            trust="project_untrusted",
            locator=f"project:///{seed}.md",
        ),
    )
    content_sha = _digest(f"content:{seed}")
    normalized_refs = tuple(
        ProjectRetrievalSourceRef(
            knowledge_id=ref.knowledge_id,
            source_kind=ref.source_kind,
            source_identity=ref.source_identity,
            source_digest_sha256=ref.source_digest_sha256,
            content_sha256=content_sha,
            locator=ref.locator,
            trust_class=ref.trust_class,
            freshness=ref.freshness,
            version=ref.version,
            state=ref.state,
            provenance=ref.provenance,
        )
        for ref in source_refs
    )
    normalized_refs = tuple(
        sorted(normalized_refs, key=lambda value: value.knowledge_id)
    )
    return ProjectRetrievalHit(
        content_sha256=content_sha,
        score=score,
        primary_knowledge_id=normalized_refs[0].knowledge_id,
        text=text,
        source_refs=normalized_refs,
    )


def _result(*hits: ProjectRetrievalHit) -> ProjectRetrievalResult:
    return ProjectRetrievalResult(
        state=ProjectRetrievalState.READY,
        request=ProjectRetrievalRequest(
            project_scope="project:fixture",
            query="Explain the project",
            limit=max(1, len(hits)),
        ),
        catalog_digest_sha256=_digest("catalog"),
        provider_identity=ProjectEmbeddingIdentity(
            "fixture",
            "deterministic",
            "1",
        ),
        eligible_candidates=len(hits),
        normalized_candidates=len(hits),
        hits=tuple(hits),
        diagnostic="Semantic retrieval completed",
    )


def test_budget_selection_is_explainable_and_preserves_untrusted_boundary() -> None:
    research_ref = _ref(
        "research",
        kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
        trust="external_guarded_untrusted",
        locator="research-pack:///fixture",
        version="4.7",
        provenance={"citation_ids": ["citation-2", "citation-1"]},
    )
    first = _hit(
        "research",
        "Research says this is relevant.",
        0.95,
        refs=(research_ref,),
    )
    second = _hit("file", "Project file also has context.", 0.80)
    first_candidate = ProjectContextCandidate.from_hit(first)

    bundle = ExplainableProjectContextBuilder(
        budget_tokens=first_candidate.estimated_tokens
    ).build(_result(first, second))

    assert [item.candidate.content_sha256 for item in bundle.selected] == [
        first.content_sha256
    ]
    assert bundle.selected[0].decision is ProjectContextDecision.SELECTED
    assert bundle.selected[0].reason is ProjectContextReason.WITHIN_BUDGET
    assert bundle.omitted[0].candidate.content_sha256 == second.content_sha256
    assert bundle.omitted[0].reason is ProjectContextReason.BUDGET_EXCEEDED
    assert bundle.selected_tokens == first_candidate.estimated_tokens
    assert bundle.remaining_tokens == 0

    rendered = bundle.render()
    assert "<UNTRUSTED_DATA>" in rendered
    assert "</UNTRUSTED_DATA>" in rendered
    assert "authority=data_only" in rendered
    assert "SOURCE_TRACE:" in rendered
    assert "citation-1,citation-2" in rendered
    assert "research-pack:///fixture" in rendered


def test_user_include_can_exceed_budget_without_promoting_trust() -> None:
    first = _hit("first", "first optional context", 0.95)
    second = _hit("second", "second explicitly included context", 0.10)
    second_candidate = ProjectContextCandidate.from_hit(second)

    bundle = ExplainableProjectContextBuilder(budget_tokens=1).build(
        _result(first, second),
        overrides={
            second.content_sha256: ProjectContextOverride.INCLUDE,
        },
    )

    selected = {item.candidate.content_sha256: item for item in bundle.selected}
    assert second.content_sha256 in selected
    assert selected[second.content_sha256].reason is ProjectContextReason.USER_INCLUDED
    assert bundle.over_budget_tokens >= second_candidate.estimated_tokens - 1
    assert "authority=data_only" in bundle.render()
    assert "level=untrusted" in bundle.render()


def test_user_exclude_wins_before_final_context_assembly() -> None:
    first = _hit("first", "highest score but excluded", 0.99)
    second = _hit("second", "remaining selected item", 0.50)

    bundle = ExplainableProjectContextBuilder(budget_tokens=10_000).build(
        _result(first, second),
        overrides={first.content_sha256: "exclude"},
    )

    assert [item.candidate.content_sha256 for item in bundle.selected] == [
        second.content_sha256
    ]
    assert bundle.omitted[0].candidate.content_sha256 == first.content_sha256
    assert bundle.omitted[0].reason is ProjectContextReason.USER_EXCLUDED
    assert "highest score but excluded" not in bundle.render()


def test_mandatory_item_is_selected_but_keeps_data_only_trust() -> None:
    item = _hit("mandatory", "must be visible in this context bundle", 0.2)

    bundle = ExplainableProjectContextBuilder(budget_tokens=1).build(
        _result(item),
        mandatory_content_sha256s=(item.content_sha256,),
    )

    assert len(bundle.selected) == 1
    assert bundle.selected[0].mandatory is True
    assert bundle.selected[0].reason is ProjectContextReason.MANDATORY
    assert bundle.over_budget_tokens > 0
    rendered = bundle.render()
    assert "authority=data_only" in rendered
    assert "<UNTRUSTED_DATA>" in rendered


def test_duplicate_source_traceability_survives_context_rendering() -> None:
    file_ref = _ref(
        "shared",
        kind=ProjectKnowledgeSourceKind.PROJECT_FILE,
        trust="project_untrusted",
        locator="project:///docs/shared.md",
    )
    memory_ref = _ref(
        "shared",
        kind=ProjectKnowledgeSourceKind.MEMORY,
        trust="project",
        locator="memory:///shared",
        version="3",
    )
    hit = _hit(
        "shared",
        "same normalized content",
        0.75,
        refs=(file_ref, memory_ref),
    )

    bundle = ExplainableProjectContextBuilder().build(_result(hit))
    rendered = bundle.render()

    assert "project:///docs/shared.md" in rendered
    assert "memory:///shared" in rendered
    assert "project_file,memory" in rendered or "memory,project_file" in rendered
    assert all(
        ref.knowledge_id in rendered
        for ref in bundle.selected[0].candidate.source_refs
    )


def test_non_ready_retrieval_is_rejected_instead_of_fabricating_context() -> None:
    empty = ProjectRetrievalResult(
        state=ProjectRetrievalState.EMPTY,
        request=ProjectRetrievalRequest(
            project_scope="project:fixture",
            query="No match",
        ),
        catalog_digest_sha256=_digest("catalog"),
        provider_identity=ProjectEmbeddingIdentity(
            "fixture",
            "deterministic",
            "1",
        ),
        eligible_candidates=1,
        normalized_candidates=1,
        hits=(),
        diagnostic="Embedding capability is ready; no candidate met min_score",
    )

    with pytest.raises(ValueError, match="READY"):
        ExplainableProjectContextBuilder().build(empty)


def test_unknown_override_or_mandatory_reference_fails_closed() -> None:
    item = _hit("known", "known item", 0.7)
    retrieval = _result(item)

    with pytest.raises(ValueError, match="unknown retrieval hit"):
        ExplainableProjectContextBuilder().build(
            retrieval,
            overrides={_digest("unknown"): "include"},
        )
    with pytest.raises(ValueError, match="unknown retrieval hit"):
        ExplainableProjectContextBuilder().build(
            retrieval,
            mandatory_content_sha256s=(_digest("unknown"),),
        )


def test_bundle_digest_and_selection_order_are_deterministic() -> None:
    first = _hit("first", "alpha", 0.5)
    second = _hit("second", "beta", 0.5)
    retrieval = _result(first, second)

    one = ExplainableProjectContextBuilder().build(retrieval)
    two = ExplainableProjectContextBuilder().build(retrieval)

    assert one.to_dict() == two.to_dict()
    assert one.digest_sha256 == two.digest_sha256
    assert [item.candidate.content_sha256 for item in one.selected] == [
        first.content_sha256,
        second.content_sha256,
    ]
