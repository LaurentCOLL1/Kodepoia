from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.assets import (
    AssetId,
    AssetKind,
    AssetRole,
    AssetSearchIndex,
    EmbeddingIdentity,
    EmbeddingState,
    OllamaEmbeddingProvider,
    ProvenanceRef,
    ReuseScope,
    SearchDocument,
    SearchDocumentBuilder,
    SearchFilters,
    SearchMode,
    VaultBoundary,
    VaultStore,
)
from kodepoia.exceptions import BrainUnavailable
from kodepoia.kodecode.workspace import WorkspaceBoundary


class FakeEmbeddingProvider:
    def __init__(self, model: str, mapping: dict[str, list[float]], *, unavailable: bool = False) -> None:
        self._identity = EmbeddingIdentity("fixture", model, "1")
        self.mapping = mapping
        self.unavailable = unavailable

    @property
    def identity(self) -> EmbeddingIdentity:
        return self._identity

    def embed(self, texts: tuple[str, ...]) -> list[list[float]]:
        if self.unavailable:
            raise BrainUnavailable("fixture unavailable")
        return [list(self.mapping[text]) for text in texts]


def _store(tmp_path: Path) -> tuple[VaultStore, Path]:
    vault = tmp_path / "vault"; vault.mkdir()
    project = tmp_path / "project"; project.mkdir()
    return VaultStore(VaultBoundary(vault)), project


def _ingest(store: VaultStore, project: Path, name: str, key: str, *, kind: AssetKind = AssetKind.GENERIC, reuse: ReuseScope = ReuseScope.VAULT_LOCAL):
    (project / name).write_text(key, encoding="utf-8")
    return store.ingest(
        project_boundary=WorkspaceBoundary(project), source_path=name,
        asset_id=AssetId.from_seed("search", key), kind=kind, display_name=key,
        provenance=(ProvenanceRef("project", name),), reuse_scope=reuse,
    )


def test_semantic_match_can_retrieve_beyond_keyword_overlap(tmp_path: Path) -> None:
    store, project = _store(tmp_path)
    try:
        wooden = _ingest(store, project, "wood.txt", "wood")
        car = _ingest(store, project, "car.txt", "car")
        documents = (
            SearchDocument(wooden.revision_id, wooden.asset_id, "weathered wooden cargo box", wooden.kind, wooden.role, wooden.reuse_scope),
            SearchDocument(car.revision_id, car.asset_id, "red sports automobile", car.kind, car.role, car.reuse_scope),
        )
        mapping = {
            "weathered wooden cargo box": [1.0, 0.0],
            "red sports automobile": [0.0, 1.0],
            "crate": [1.0, 0.0],
        }
        provider = FakeEmbeddingProvider("fixture-a", mapping)
        index = AssetSearchIndex(store)
        index.index_documents(documents, provider)
        hits = index.search("crate", provider=provider)
        assert hits[0].revision_id == wooden.revision_id
        assert hits[0].lexical_score == 0.0
        assert hits[0].mode is SearchMode.HYBRID
        index.close()
    finally:
        store.close()


def test_lexical_fallback_when_embedding_provider_is_unavailable(tmp_path: Path) -> None:
    store, project = _store(tmp_path)
    try:
        wooden = _ingest(store, project, "wood.txt", "wood")
        document = SearchDocument(wooden.revision_id, wooden.asset_id, "wooden crate prop", wooden.kind, wooden.role, wooden.reuse_scope)
        index = AssetSearchIndex(store)
        index.index_documents((document,))
        unavailable = FakeEmbeddingProvider("missing", {}, unavailable=True)
        hits = index.search("crate", provider=unavailable)
        assert hits[0].revision_id == wooden.revision_id
        assert hits[0].mode is SearchMode.LEXICAL_FALLBACK
        assert hits[0].embedding_state is EmbeddingState.UNAVAILABLE
        index.close()
    finally:
        store.close()


def test_provider_identity_and_metadata_changes_mark_vectors_stale(tmp_path: Path) -> None:
    store, project = _store(tmp_path)
    try:
        revision = _ingest(store, project, "asset.txt", "asset")
        first_doc = SearchDocument(revision.revision_id, revision.asset_id, "old description", revision.kind, revision.role, revision.reuse_scope)
        first = FakeEmbeddingProvider("model-a", {"old description": [1.0, 0.0]})
        second = FakeEmbeddingProvider("model-b", {"old description": [1.0, 0.0]})
        index = AssetSearchIndex(store)
        index.index_documents((first_doc,), first)
        assert index.embedding_state(revision.revision_id, first) is EmbeddingState.CURRENT
        assert index.embedding_state(revision.revision_id, second) is EmbeddingState.STALE
        changed = SearchDocument(revision.revision_id, revision.asset_id, "new description", revision.kind, revision.role, revision.reuse_scope)
        index.index_documents((changed,))
        assert index.embedding_state(revision.revision_id, first) is EmbeddingState.STALE
        index.close()
    finally:
        store.close()


def test_exact_facets_and_blocked_policy_apply_before_ranking(tmp_path: Path) -> None:
    store, project = _store(tmp_path)
    try:
        image = _ingest(store, project, "image.txt", "image", kind=AssetKind.IMAGE, reuse=ReuseScope.EXPORTABLE)
        model = _ingest(store, project, "model.txt", "model", kind=AssetKind.MODEL_3D, reuse=ReuseScope.VAULT_LOCAL)
        documents = (
            SearchDocument(image.revision_id, image.asset_id, "common hero asset", image.kind, AssetRole.SOURCE, image.reuse_scope, license_state="allow"),
            SearchDocument(model.revision_id, model.asset_id, "common hero asset", model.kind, AssetRole.SOURCE, model.reuse_scope, license_state="blocked", blocked=True),
        )
        index = AssetSearchIndex(store)
        index.index_documents(documents)
        hits = index.search("common", filters=SearchFilters(kind=AssetKind.IMAGE, reuse_scope=ReuseScope.EXPORTABLE, license_state="allow"))
        assert [hit.revision_id for hit in hits] == [image.revision_id]
        assert all(hit.revision_id != model.revision_id for hit in index.search("common"))
        index.close()
    finally:
        store.close()


def test_document_builder_uses_canonical_metadata_and_project_refs(tmp_path: Path) -> None:
    store, project = _store(tmp_path)
    try:
        revision = _ingest(store, project, "asset.txt", "builder", kind=AssetKind.DOCUMENT)
        from kodepoia.assets import ProjectAssetReference
        store.add_project_reference(ProjectAssetReference("project-x", revision.asset_id, revision.revision_id))
        document = SearchDocumentBuilder(store).build(
            revision.revision_id,
            description="manual description",
            technical_metadata={"format": "txt"},
            license_state="unknown",
        )
        assert "builder" in document.text
        assert "manual description" in document.text
        assert "asset.txt" in document.text
        assert document.project_ids == ("project-x",)
        assert ("format", "txt") in document.technical_metadata
    finally:
        store.close()


def test_ollama_bridge_reuses_existing_r3_embed_contract() -> None:
    class StubClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []
        def embed(self, model: str, inputs: object):
            self.calls.append((model, inputs))
            return [[1.0, 2.0], [3.0, 4.0]]

    client = StubClient()
    provider = OllamaEmbeddingProvider(client, "embed-model")  # type: ignore[arg-type]
    assert provider.embed(("a", "b")) == [[1.0, 2.0], [3.0, 4.0]]
    assert client.calls == [("embed-model", ["a", "b"])]
    assert provider.identity == EmbeddingIdentity("ollama", "embed-model", "r3-embed-v1")
