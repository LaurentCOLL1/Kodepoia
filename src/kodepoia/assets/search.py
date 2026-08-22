from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRevisionId,
    AssetRole,
    ReuseScope,
)
from kodepoia.assets.serialization import canonical_json, load_asset_record
from kodepoia.assets.store import VaultStore
from kodepoia.brain.ollama import OllamaClient
from kodepoia.exceptions import BrainUnavailable

_TOKEN_RE = re.compile(r"[\w./+-]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class EmbeddingIdentity:
    provider: str
    model: str
    version: str

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.model.strip() or not self.version.strip():
            raise ValueError("Embedding provider, model and version must be non-empty")


class EmbeddingProvider(Protocol):
    @property
    def identity(self) -> EmbeddingIdentity: ...

    def embed(self, texts: tuple[str, ...]) -> list[list[float]]: ...


class OllamaEmbeddingProvider:
    """Bridge R8 search to the already accepted R3 Ollama `/api/embed` client."""

    def __init__(self, client: OllamaClient, model: str, *, contract_version: str = "r3-embed-v1") -> None:
        if not model.strip():
            raise ValueError("Embedding model must be non-empty")
        self.client = client
        self.model = model
        self.contract_version = contract_version

    @property
    def identity(self) -> EmbeddingIdentity:
        return EmbeddingIdentity("ollama", self.model, self.contract_version)

    def embed(self, texts: tuple[str, ...]) -> list[list[float]]:
        if not texts:
            return []
        return self.client.embed(self.model, list(texts))


class EmbeddingState(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"


class SearchMode(StrEnum):
    HYBRID = "hybrid"
    LEXICAL_FALLBACK = "lexical_fallback"


@dataclass(frozen=True, slots=True)
class SearchDocument:
    revision_id: AssetRevisionId
    asset_id: AssetId
    text: str
    kind: AssetKind
    role: AssetRole
    reuse_scope: ReuseScope
    project_ids: tuple[str, ...] = ()
    license_state: str = "unknown"
    tool_lineage: tuple[str, ...] = ()
    technical_metadata: tuple[tuple[str, str], ...] = ()
    blocked: bool = False

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Search document text must be non-empty")
        if not self.license_state.strip():
            raise ValueError("license_state must be non-empty")
        object.__setattr__(self, "project_ids", tuple(sorted(set(self.project_ids))))
        object.__setattr__(self, "tool_lineage", tuple(sorted(set(self.tool_lineage))))
        object.__setattr__(self, "technical_metadata", tuple(sorted(set(self.technical_metadata))))

    def digest_payload(self) -> dict[str, object]:
        return {
            "revision_id": str(self.revision_id),
            "asset_id": str(self.asset_id),
            "text": self.text,
            "kind": self.kind.value,
            "role": self.role.value,
            "reuse_scope": self.reuse_scope.value,
            "project_ids": list(self.project_ids),
            "license_state": self.license_state,
            "tool_lineage": list(self.tool_lineage),
            "technical_metadata": dict(self.technical_metadata),
            "blocked": self.blocked,
        }

    @property
    def document_digest(self) -> str:
        return hashlib.sha256(canonical_json(self.digest_payload()).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SearchFilters:
    kind: AssetKind | None = None
    role: AssetRole | None = None
    reuse_scope: ReuseScope | None = None
    project_id: str | None = None
    license_state: str | None = None
    tool_lineage: str | None = None
    technical_equals: tuple[tuple[str, str], ...] = ()
    include_blocked: bool = False


@dataclass(frozen=True, slots=True)
class HybridRankingPolicy:
    version: int = 1
    lexical_weight: float = 0.40
    semantic_weight: float = 0.60

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("Ranking policy version must be >= 1")
        if self.lexical_weight < 0 or self.semantic_weight < 0:
            raise ValueError("Ranking weights must be non-negative")
        if not math.isclose(self.lexical_weight + self.semantic_weight, 1.0, abs_tol=1e-9):
            raise ValueError("Ranking weights must sum to 1.0")


@dataclass(frozen=True, slots=True)
class SearchHit:
    revision_id: AssetRevisionId
    asset_id: AssetId
    score: float
    lexical_score: float
    semantic_score: float | None
    mode: SearchMode
    embedding_state: EmbeddingState


@dataclass(frozen=True, slots=True)
class ReindexReport:
    indexed: int
    embedded: int
    embedding_unavailable: bool


class SearchDocumentBuilder:
    """Build rebuildable search text from canonical Vault records and explicit metadata."""

    def __init__(self, store: VaultStore) -> None:
        self.store = store

    def build(
        self,
        revision_id: AssetRevisionId,
        *,
        description: str = "",
        technical_metadata: dict[str, str] | None = None,
        license_state: str = "unknown",
        blocked: bool = False,
    ) -> SearchDocument:
        revision = self.store._load_revision_manifest(revision_id)
        record_path = self.store.boundary.resolve(f"manifests/assets/{revision.asset_id}.json", must_exist=True)
        record = load_asset_record(json.loads(record_path.read_text(encoding="utf-8")))
        project_rows = self.store.db.execute(
            "SELECT DISTINCT project_id FROM project_refs WHERE revision_id = ? ORDER BY project_id",
            (str(revision_id),),
        ).fetchall()
        project_ids = tuple(str(row["project_id"]) for row in project_rows)
        tool_lineage = tuple(
            sorted({edge.transform_id for edge in revision.lineage if edge.transform_id is not None})
        )
        technical = tuple(sorted((str(key), str(value)) for key, value in (technical_metadata or {}).items()))
        provenance_text = " ".join(
            f"{item.source_kind} {item.locator}" for item in revision.provenance
        )
        lineage_text = " ".join(
            f"{edge.relation} {edge.transform_id or ''}" for edge in revision.lineage
        )
        technical_text = " ".join(f"{key} {value}" for key, value in technical)
        text = " ".join(
            part
            for part in (
                record.display_name,
                " ".join(record.tags),
                description.strip(),
                revision.kind.value,
                revision.role.value,
                provenance_text,
                lineage_text,
                technical_text,
                license_state,
            )
            if part
        )
        return SearchDocument(
            revision_id=revision.revision_id,
            asset_id=revision.asset_id,
            text=text,
            kind=revision.kind,
            role=revision.role,
            reuse_scope=revision.reuse_scope,
            project_ids=project_ids,
            license_state=license_state,
            tool_lineage=tool_lineage,
            technical_metadata=technical,
            blocked=blocked,
        )


class AssetSearchIndex:
    """Rebuildable hybrid lexical/vector index stored separately from canonical manifests."""

    def __init__(self, store: VaultStore, policy: HybridRankingPolicy | None = None) -> None:
        self.store = store
        self.policy = policy or HybridRankingPolicy()
        root = store.boundary.resolve("search")
        root.mkdir(parents=True, exist_ok=True)
        self.db_path = store.boundary.resolve("search/index.sqlite3")
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS documents (
                revision_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                document_text TEXT NOT NULL,
                document_digest TEXT NOT NULL,
                kind TEXT NOT NULL,
                role TEXT NOT NULL,
                reuse_scope TEXT NOT NULL,
                project_ids_json TEXT NOT NULL,
                license_state TEXT NOT NULL,
                tool_lineage_json TEXT NOT NULL,
                technical_json TEXT NOT NULL,
                blocked INTEGER NOT NULL CHECK(blocked IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS embeddings (
                revision_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                provider_version TEXT NOT NULL,
                document_digest TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                PRIMARY KEY(revision_id, provider, model, provider_version)
            );
            CREATE INDEX IF NOT EXISTS idx_search_facets ON documents(kind, role, reuse_scope, license_state, blocked);
        """)
        self.db.commit()

    @staticmethod
    def _validated_vector(vector: list[float]) -> list[float]:
        values = [float(value) for value in vector]
        if not values or not all(math.isfinite(value) for value in values):
            raise ValueError("Embedding vector must contain finite values")
        return values

    def index_documents(
        self,
        documents: tuple[SearchDocument, ...],
        provider: EmbeddingProvider | None = None,
    ) -> ReindexReport:
        embedded = 0
        unavailable = False
        with self.db:
            for document in documents:
                self.db.execute(
                    """INSERT OR REPLACE INTO documents(
                        revision_id, asset_id, document_text, document_digest, kind, role, reuse_scope,
                        project_ids_json, license_state, tool_lineage_json, technical_json, blocked
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(document.revision_id),
                        str(document.asset_id),
                        document.text,
                        document.document_digest,
                        document.kind.value,
                        document.role.value,
                        document.reuse_scope.value,
                        canonical_json({"values": list(document.project_ids)}),
                        document.license_state,
                        canonical_json({"values": list(document.tool_lineage)}),
                        canonical_json(dict(document.technical_metadata)),
                        int(document.blocked),
                    ),
                )
        if provider is not None and documents:
            try:
                vectors = provider.embed(tuple(document.text for document in documents))
                if len(vectors) != len(documents):
                    raise ValueError("Embedding provider returned an unexpected vector count")
                identity = provider.identity
                with self.db:
                    for document, raw_vector in zip(documents, vectors, strict=True):
                        vector = self._validated_vector(raw_vector)
                        self.db.execute(
                            """INSERT OR REPLACE INTO embeddings(
                                revision_id, provider, model, provider_version, document_digest, vector_json, dimensions
                            ) VALUES(?, ?, ?, ?, ?, ?, ?)""",
                            (
                                str(document.revision_id),
                                identity.provider,
                                identity.model,
                                identity.version,
                                document.document_digest,
                                json.dumps(vector, separators=(",", ":")),
                                len(vector),
                            ),
                        )
                        embedded += 1
            except BrainUnavailable:
                unavailable = True
        return ReindexReport(len(documents), embedded, unavailable)

    def embedding_state(self, revision_id: AssetRevisionId, provider: EmbeddingProvider | None) -> EmbeddingState:
        if provider is None:
            return EmbeddingState.UNAVAILABLE
        document = self.db.execute(
            "SELECT document_digest FROM documents WHERE revision_id = ?",
            (str(revision_id),),
        ).fetchone()
        if document is None:
            return EmbeddingState.MISSING
        identity = provider.identity
        exact = self.db.execute(
            """SELECT document_digest FROM embeddings
               WHERE revision_id = ? AND provider = ? AND model = ? AND provider_version = ?""",
            (str(revision_id), identity.provider, identity.model, identity.version),
        ).fetchone()
        if exact is not None and str(exact["document_digest"]) == str(document["document_digest"]):
            return EmbeddingState.CURRENT
        any_vector = self.db.execute(
            "SELECT 1 FROM embeddings WHERE revision_id = ? LIMIT 1",
            (str(revision_id),),
        ).fetchone()
        return EmbeddingState.STALE if any_vector is not None else EmbeddingState.MISSING

    @staticmethod
    def _tokens(text: str) -> tuple[str, ...]:
        return tuple(token.casefold() for token in _TOKEN_RE.findall(text))

    @classmethod
    def _lexical_score(cls, query: str, document: str) -> float:
        query_tokens = cls._tokens(query)
        if not query_tokens:
            return 0.0
        document_tokens = cls._tokens(document)
        document_set = set(document_tokens)
        overlap = sum(1 for token in query_tokens if token in document_set) / len(query_tokens)
        phrase_bonus = 0.15 if query.casefold().strip() in document.casefold() else 0.0
        return min(1.0, overlap + phrase_bonus)

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or not left:
            raise ValueError("Embedding dimensions do not match")
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return max(-1.0, min(1.0, dot / (left_norm * right_norm)))

    @staticmethod
    def _matches_filters(row: sqlite3.Row, filters: SearchFilters) -> bool:
        if not filters.include_blocked and bool(row["blocked"]):
            return False
        if filters.kind is not None and row["kind"] != filters.kind.value:
            return False
        if filters.role is not None and row["role"] != filters.role.value:
            return False
        if filters.reuse_scope is not None and row["reuse_scope"] != filters.reuse_scope.value:
            return False
        if filters.license_state is not None and row["license_state"] != filters.license_state:
            return False
        projects = set(json.loads(str(row["project_ids_json"])).get("values", []))
        if filters.project_id is not None and filters.project_id not in projects:
            return False
        lineage = set(json.loads(str(row["tool_lineage_json"])).get("values", []))
        if filters.tool_lineage is not None and filters.tool_lineage not in lineage:
            return False
        technical = json.loads(str(row["technical_json"]))
        return all(str(technical.get(key)) == value for key, value in filters.technical_equals)

    def search(
        self,
        query: str,
        *,
        provider: EmbeddingProvider | None = None,
        filters: SearchFilters | None = None,
        limit: int = 20,
    ) -> list[SearchHit]:
        if not query.strip():
            raise ValueError("Search query must be non-empty")
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        active_filters = filters or SearchFilters()
        query_vector: list[float] | None = None
        provider_available = provider is not None
        if provider is not None:
            try:
                vectors = provider.embed((query,))
                if len(vectors) != 1:
                    raise ValueError("Embedding provider returned an unexpected query vector count")
                query_vector = self._validated_vector(vectors[0])
            except BrainUnavailable:
                provider_available = False

        rows = self.db.execute("SELECT * FROM documents ORDER BY revision_id").fetchall()
        hits: list[SearchHit] = []
        for row in rows:
            if not self._matches_filters(row, active_filters):
                continue
            revision_id = AssetRevisionId(str(row["revision_id"]))
            lexical = self._lexical_score(query, str(row["document_text"]))
            state = self.embedding_state(revision_id, provider if provider_available else None)
            semantic: float | None = None
            mode = SearchMode.LEXICAL_FALLBACK
            score = lexical
            if provider_available and provider is not None and query_vector is not None and state is EmbeddingState.CURRENT:
                identity = provider.identity
                vector_row = self.db.execute(
                    """SELECT vector_json, dimensions FROM embeddings
                       WHERE revision_id = ? AND provider = ? AND model = ? AND provider_version = ?""",
                    (str(revision_id), identity.provider, identity.model, identity.version),
                ).fetchone()
                if vector_row is not None:
                    vector = self._validated_vector(json.loads(str(vector_row["vector_json"])))
                    semantic = (self._cosine(query_vector, vector) + 1.0) / 2.0
                    score = self.policy.lexical_weight * lexical + self.policy.semantic_weight * semantic
                    mode = SearchMode.HYBRID
            if score > 0.0:
                hits.append(
                    SearchHit(
                        revision_id=revision_id,
                        asset_id=AssetId(str(row["asset_id"])),
                        score=score,
                        lexical_score=lexical,
                        semantic_score=semantic,
                        mode=mode,
                        embedding_state=state,
                    )
                )
        hits.sort(key=lambda hit: (-hit.score, str(hit.revision_id)))
        return hits[:limit]

    def close(self) -> None:
        self.db.close()
