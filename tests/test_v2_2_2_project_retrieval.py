from __future__ import annotations

import hashlib

import pytest

from kodepoia.exceptions import BrainUnavailable
from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeCatalog,
    ProjectKnowledgeItem,
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
)
from kodepoia.intelligence.project_retrieval import (
    ProjectEmbeddingIdentity,
    ProjectRetrievalRequest,
    ProjectRetrievalState,
    ProjectSemanticRetriever,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _item(
    seed: str,
    text: str,
    *,
    project_scope: str = "project:fixture",
    kind: ProjectKnowledgeSourceKind = ProjectKnowledgeSourceKind.PROJECT_FILE,
    state: ProjectKnowledgeState = ProjectKnowledgeState.ACTIVE,
) -> ProjectKnowledgeItem:
    return ProjectKnowledgeItem(
        project_scope=project_scope,
        source_kind=kind,
        source_identity=_digest(f"identity:{seed}"),
        source_digest_sha256=_digest(f"source:{seed}"),
        content_sha256=_digest(text),
        text=text,
        trust_class="project_untrusted",
        freshness="current",
        locator=f"project:///{seed}",
        state=state,
        provenance={"seed": seed},
    )


class FixtureEmbeddingProvider:
    def __init__(
        self,
        mapping: dict[str, list[float]],
        *,
        unavailable: bool = False,
    ) -> None:
        self.mapping = mapping
        self.unavailable = unavailable
        self.calls: list[tuple[str, ...]] = []
        self.identity_reads = 0

    @property
    def identity(self) -> ProjectEmbeddingIdentity:
        self.identity_reads += 1
        return ProjectEmbeddingIdentity("fixture", "deterministic", "1")

    def embed(self, texts: tuple[str, ...]) -> list[list[float]]:
        self.calls.append(texts)
        if self.unavailable:
            raise BrainUnavailable("fixture unavailable")
        return [list(self.mapping[text]) for text in texts]


def test_semantic_retrieval_ranks_without_lexical_overlap() -> None:
    crate = _item("crate", "weathered wooden cargo box")
    car = _item("car", "red sports automobile")
    catalog = ProjectKnowledgeCatalog("project:fixture", (crate, car))
    provider = FixtureEmbeddingProvider(
        {
            "crate": [1.0, 0.0],
            crate.text: [1.0, 0.0],
            car.text: [0.0, 1.0],
        }
    )

    result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest("project:fixture", "crate", limit=2),
        provider=provider,
    )

    assert result.state is ProjectRetrievalState.READY
    assert [hit.primary_knowledge_id for hit in result.hits] == [
        crate.knowledge_id,
        car.knowledge_id,
    ]
    assert result.hits[0].score == pytest.approx(1.0)
    assert result.hits[1].score == pytest.approx(0.5)
    assert provider.calls == [("crate", crate.text, car.text)] or provider.calls == [
        ("crate", car.text, crate.text)
    ]


def test_project_scope_is_rejected_before_provider_access() -> None:
    catalog = ProjectKnowledgeCatalog(
        "project:fixture",
        (_item("a", "alpha"),),
    )
    provider = FixtureEmbeddingProvider({"query": [1.0], "alpha": [1.0]})

    with pytest.raises(ValueError, match="project scope"):
        ProjectSemanticRetriever().retrieve(
            catalog,
            ProjectRetrievalRequest("project:other", "query"),
            provider=provider,
        )

    assert provider.identity_reads == 0
    assert provider.calls == []


def test_provider_unavailable_is_not_reported_as_empty() -> None:
    item = _item("a", "alpha")
    catalog = ProjectKnowledgeCatalog("project:fixture", (item,))
    request = ProjectRetrievalRequest("project:fixture", "query")

    no_provider = ProjectSemanticRetriever().retrieve(
        catalog,
        request,
        provider=None,
    )
    assert no_provider.state is ProjectRetrievalState.EMBEDDING_UNAVAILABLE
    assert no_provider.hits == ()

    unavailable = FixtureEmbeddingProvider({}, unavailable=True)
    unavailable_result = ProjectSemanticRetriever().retrieve(
        catalog,
        request,
        provider=unavailable,
    )
    assert unavailable_result.state is ProjectRetrievalState.EMBEDDING_UNAVAILABLE
    assert unavailable_result.provider_identity is not None
    assert "fixture unavailable" in unavailable_result.diagnostic


def test_valid_zero_result_is_distinct_from_unavailable() -> None:
    item = _item("a", "alpha")
    catalog = ProjectKnowledgeCatalog("project:fixture", (item,))
    provider = FixtureEmbeddingProvider(
        {
            "query": [1.0, 0.0],
            "alpha": [0.0, 1.0],
        }
    )

    result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest(
            "project:fixture",
            "query",
            min_score=0.9,
        ),
        provider=provider,
    )

    assert result.state is ProjectRetrievalState.EMPTY
    assert result.provider_identity == ProjectEmbeddingIdentity(
        "fixture",
        "deterministic",
        "1",
    )
    assert result.eligible_candidates == 1
    assert result.normalized_candidates == 1
    assert result.hits == ()
    assert "no candidate met min_score" in result.diagnostic


def test_candidate_limit_fails_explicitly_before_provider_access() -> None:
    catalog = ProjectKnowledgeCatalog(
        "project:fixture",
        (_item("a", "alpha"), _item("b", "beta")),
    )
    provider = FixtureEmbeddingProvider(
        {"query": [1.0], "alpha": [1.0], "beta": [1.0]}
    )

    result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest(
            "project:fixture",
            "query",
            max_candidates=1,
        ),
        provider=provider,
    )

    assert result.state is ProjectRetrievalState.CANDIDATE_LIMIT_EXCEEDED
    assert result.eligible_candidates == 2
    assert result.normalized_candidates == 0
    assert provider.identity_reads == 0
    assert provider.calls == []


def test_duplicate_content_is_normalized_without_losing_provenance() -> None:
    text = "same governed knowledge"
    file_item = _item(
        "file",
        text,
        kind=ProjectKnowledgeSourceKind.PROJECT_FILE,
    )
    memory_item = _item(
        "memory",
        text,
        kind=ProjectKnowledgeSourceKind.MEMORY,
        state=ProjectKnowledgeState.INCLUDED,
    )
    catalog = ProjectKnowledgeCatalog(
        "project:fixture",
        (memory_item, file_item),
    )
    provider = FixtureEmbeddingProvider(
        {
            "query": [1.0, 0.0],
            text: [1.0, 0.0],
        }
    )

    result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest("project:fixture", "query"),
        provider=provider,
    )

    assert result.state is ProjectRetrievalState.READY
    assert result.eligible_candidates == 2
    assert result.normalized_candidates == 1
    assert len(result.hits) == 1
    refs = result.hits[0].source_refs
    assert {ref.knowledge_id for ref in refs} == {
        file_item.knowledge_id,
        memory_item.knowledge_id,
    }
    assert {ref.source_kind for ref in refs} == {
        ProjectKnowledgeSourceKind.PROJECT_FILE,
        ProjectKnowledgeSourceKind.MEMORY,
    }
    assert {ref.provenance["seed"] for ref in refs} == {"file", "memory"}
    assert provider.calls == [("query", text)]


def test_excluded_invalidated_and_unselected_source_kinds_are_not_scored() -> None:
    active_file = _item("file", "file active")
    excluded = _item(
        "excluded",
        "excluded",
        state=ProjectKnowledgeState.EXCLUDED,
    )
    invalidated = _item(
        "invalidated",
        "invalidated",
        state=ProjectKnowledgeState.INVALIDATED,
    )
    memory = _item(
        "memory",
        "memory active",
        kind=ProjectKnowledgeSourceKind.MEMORY,
    )
    catalog = ProjectKnowledgeCatalog(
        "project:fixture",
        (active_file, excluded, invalidated, memory),
    )
    provider = FixtureEmbeddingProvider(
        {
            "query": [1.0],
            "file active": [1.0],
        }
    )

    result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest(
            "project:fixture",
            "query",
            source_kinds=(ProjectKnowledgeSourceKind.PROJECT_FILE,),
        ),
        provider=provider,
    )

    assert result.eligible_candidates == 1
    assert result.hits[0].primary_knowledge_id == active_file.knowledge_id
    assert provider.calls == [("query", "file active")]


def test_empty_catalog_is_valid_empty_without_provider_invocation() -> None:
    catalog = ProjectKnowledgeCatalog("project:fixture", ())
    provider = FixtureEmbeddingProvider({"query": [1.0]})

    result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest("project:fixture", "query"),
        provider=provider,
    )

    assert result.state is ProjectRetrievalState.EMPTY
    assert result.diagnostic == "No eligible project knowledge candidates"
    assert provider.identity_reads == 0
    assert provider.calls == []


def test_tie_break_and_result_digest_are_deterministic() -> None:
    first = _item("first", "first text")
    second = _item("second", "second text")
    catalog = ProjectKnowledgeCatalog("project:fixture", (second, first))
    mapping = {
        "query": [1.0, 0.0],
        first.text: [0.0, 1.0],
        second.text: [0.0, 1.0],
    }

    first_result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest("project:fixture", "query"),
        provider=FixtureEmbeddingProvider(mapping),
    )
    second_result = ProjectSemanticRetriever().retrieve(
        catalog,
        ProjectRetrievalRequest("project:fixture", "query"),
        provider=FixtureEmbeddingProvider(mapping),
    )

    expected = sorted(
        (first, second),
        key=lambda item: (item.content_sha256, item.knowledge_id),
    )
    assert [hit.primary_knowledge_id for hit in first_result.hits] == [
        item.knowledge_id for item in expected
    ]
    assert first_result.digest_sha256 == second_result.digest_sha256
    assert first_result.to_dict() == second_result.to_dict()


def test_embedding_contract_errors_fail_closed() -> None:
    item = _item("a", "alpha")
    catalog = ProjectKnowledgeCatalog("project:fixture", (item,))
    request = ProjectRetrievalRequest("project:fixture", "query")

    wrong_count = FixtureEmbeddingProvider({"query": [1.0], "alpha": [1.0]})
    wrong_count.embed = lambda texts: [[1.0]]  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="vector count"):
        ProjectSemanticRetriever().retrieve(
            catalog,
            request,
            provider=wrong_count,
        )

    mismatched = FixtureEmbeddingProvider(
        {"query": [1.0, 0.0], "alpha": [1.0]}
    )
    with pytest.raises(ValueError, match="dimensions"):
        ProjectSemanticRetriever().retrieve(
            catalog,
            request,
            provider=mismatched,
        )
