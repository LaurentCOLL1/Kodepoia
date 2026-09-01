from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Mapping

from kodepoia.core.governance import GovernancePolicy

MEMORY_SCHEMA_VERSION = 2
_MAX_AUDIT_DETAIL = 240
_SAFE_TRUST_CLASSES = frozenset(
    {"user", "project", "derived", "untrusted", "authoritative_source"}
)
_SAFE_RECORD_CLASSES = frozenset(
    {"user_fact", "project_fact", "derived_summary", "action_suggestion"}
)

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:api[_ -]?key|token|secret|password|passwd)\s*[:=]\s*['\"]?[^\s,'\"]{8,}"),
    re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+\S+"),
)
_AUTHORITY_PATTERNS = (
    re.compile(
        r"(?i)\b(?:grant|give|allow|authorize|approve|enable)\b.{0,80}"
        r"\b(?:permission|capability|privilege|authority|access)\b"
    ),
    re.compile(
        r"(?i)\b(?:disable|bypass|ignore|override|replace|change)\b.{0,80}"
        r"\b(?:security|policy|guardrail|approval|architecture|permission)\b"
    ),
    re.compile(
        r"(?i)\b(?:permission|approval|policy|architecture|security)\b.{0,80}"
        r"\b(?:is|are|has been|was)\s+(?:granted|approved|disabled|overridden|changed)\b"
    ),
)
_PRIVILEGED_METADATA_KEYS = frozenset(
    {
        "approval",
        "approved",
        "authority",
        "authorization",
        "capability",
        "capabilities",
        "permission",
        "permissions",
        "policy",
        "security_override",
        "architecture_override",
    }
)


class MemoryRejectedError(ValueError):
    """Raised when untrusted memory fails the durable-memory write boundary."""


class RebuildState(StrEnum):
    REBUILT = "REBUILT"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    id: int
    scope: str
    kind: str
    content: str
    importance: float
    created_at: str
    embedding: tuple[float, ...] | None
    metadata: dict[str, object]
    schema_version: int = MEMORY_SCHEMA_VERSION
    origin: str = ""
    project_scope: str = ""
    trust_class: str = "untrusted"
    record_class: str = "project_fact"
    version: int = 1
    integrity_digest: str = ""
    expires_at: str | None = None


@dataclass(frozen=True, slots=True)
class AuthoritativeMemory:
    """Known-good rebuild input supplied by an explicit authoritative source adapter."""

    project_scope: str
    kind: str
    content: str
    origin: str
    version: int
    record_class: str = "project_fact"
    importance: float = 0.5
    embedding: tuple[float, ...] | None = None
    metadata: Mapping[str, object] | None = None
    expires_at: str | None = None
    created_at: str = "1970-01-01T00:00:00+00:00"


@dataclass(frozen=True, slots=True)
class RebuildReport:
    state: RebuildState
    project_scope: str
    restored: int
    quarantined: int
    semantic_digest: str | None
    reason: str


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.db.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                embedding TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                allow_global INTEGER NOT NULL DEFAULT 0,
                allow_training INTEGER NOT NULL DEFAULT 0,
                confidential INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_memories_scope_kind ON memories(scope, kind);
            CREATE TABLE IF NOT EXISTS memory_quarantine (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER,
                quarantined_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                scope TEXT,
                project_scope TEXT,
                kind TEXT,
                origin TEXT,
                record_version INTEGER,
                content_sha256 TEXT NOT NULL,
                integrity_digest TEXT,
                metadata_sha256 TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_memory_quarantine_scope
                ON memory_quarantine(project_scope, reason);
            """
        )
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(memories)")}
        additions = {
            "schema_version": "INTEGER",
            "origin": "TEXT",
            "project_scope": "TEXT",
            "trust_class": "TEXT",
            "record_class": "TEXT",
            "record_version": "INTEGER",
            "integrity_digest": "TEXT",
            "expires_at": "TEXT",
        }
        for name, sql_type in additions.items():
            if name not in columns:
                self.db.execute(f"ALTER TABLE memories ADD COLUMN {name} {sql_type}")
        self._migrate_legacy_rows()
        self.db.commit()

    def _migrate_legacy_rows(self) -> None:
        rows = self.db.execute(
            """
            SELECT * FROM memories
            WHERE schema_version IS NULL OR origin IS NULL OR project_scope IS NULL
               OR trust_class IS NULL OR record_class IS NULL OR record_version IS NULL
               OR integrity_digest IS NULL
            ORDER BY id
            """
        ).fetchall()
        for row in rows:
            metadata = self._safe_metadata(row["metadata"])
            vector = self._safe_embedding(row["embedding"])
            origin = row["origin"] or f"legacy:{row['id']}"
            project_scope = row["project_scope"] or row["scope"]
            trust_class = row["trust_class"] or "untrusted"
            record_class = row["record_class"] or "project_fact"
            record_version = int(row["record_version"] or 1)
            schema_version = int(row["schema_version"] or MEMORY_SCHEMA_VERSION)
            digest = self._digest(
                scope=row["scope"],
                kind=row["kind"],
                content=row["content"],
                importance=float(row["importance"]),
                created_at=row["created_at"],
                embedding=vector,
                metadata=metadata,
                allow_global=int(row["allow_global"]),
                allow_training=int(row["allow_training"]),
                confidential=int(row["confidential"]),
                schema_version=schema_version,
                origin=origin,
                project_scope=project_scope,
                trust_class=trust_class,
                record_class=record_class,
                version=record_version,
                expires_at=row["expires_at"],
            )
            self.db.execute(
                """
                UPDATE memories
                SET schema_version = ?, origin = ?, project_scope = ?, trust_class = ?,
                    record_class = ?, record_version = ?, integrity_digest = ?
                WHERE id = ?
                """,
                (
                    schema_version,
                    origin,
                    project_scope,
                    trust_class,
                    record_class,
                    record_version,
                    digest,
                    row["id"],
                ),
            )

    def add(
        self,
        scope: str,
        kind: str,
        content: str,
        *,
        importance: float = 0.5,
        embedding: Iterable[float] | None = None,
        metadata: dict[str, object] | None = None,
        governance: GovernancePolicy | None = None,
        origin: str | None = None,
        project_scope: str | None = None,
        trust_class: str = "user",
        record_class: str = "project_fact",
        version: int = 1,
        expires_at: str | None = None,
    ) -> int:
        governance = governance or GovernancePolicy()
        created_at = datetime.now(UTC).isoformat()
        vector = self._normalize_embedding(embedding)
        metadata_obj = dict(metadata or {})
        scope = self._required_text(scope, "scope")
        kind = self._required_text(kind, "kind")
        project_scope = self._required_text(project_scope or scope, "project_scope")
        trust_class = self._validate_trust_class(trust_class)
        record_class = self._validate_record_class(record_class)
        version = self._validate_version(version)
        expires_at = self._normalize_timestamp(expires_at, "expires_at")
        importance_value = self._finite_float(importance, "importance")
        self._validate_payload_for_persistence(
            content=content,
            metadata=metadata_obj,
            scope=scope,
            project_scope=project_scope,
            kind=kind,
            origin=origin or "pending",
            version=version,
        )
        if origin is None:
            seed = self._canonical_json(
                {
                    "scope": scope,
                    "kind": kind,
                    "content": content,
                    "created_at": created_at,
                    "record_class": record_class,
                }
            )
            origin = f"local:{hashlib.sha256(seed.encode()).hexdigest()[:24]}"
        origin = self._required_text(origin, "origin")

        allow_global = int(governance.allow_global_memory)
        allow_training = int(governance.allow_training_dataset)
        confidential = int(governance.confidential)
        digest = self._digest(
            scope=scope,
            kind=kind,
            content=content,
            importance=importance_value,
            created_at=created_at,
            embedding=vector,
            metadata=metadata_obj,
            allow_global=allow_global,
            allow_training=allow_training,
            confidential=confidential,
            schema_version=MEMORY_SCHEMA_VERSION,
            origin=origin,
            project_scope=project_scope,
            trust_class=trust_class,
            record_class=record_class,
            version=version,
            expires_at=expires_at,
        )
        existing = self.db.execute(
            """
            SELECT * FROM memories
            WHERE origin = ? AND project_scope = ? AND kind = ?
            ORDER BY record_version DESC, id ASC
            """,
            (origin, project_scope, kind),
        ).fetchall()
        for row in existing:
            existing_version = int(row["record_version"])
            if existing_version == version:
                reason = (
                    "replay"
                    if self._same_semantic_payload(
                        row,
                        scope=scope,
                        content=content,
                        importance=importance_value,
                        embedding=vector,
                        metadata=metadata_obj,
                        trust_class=trust_class,
                        record_class=record_class,
                        expires_at=expires_at,
                    )
                    else "version_conflict"
                )
                self._audit_rejected(
                    reason=reason,
                    scope=scope,
                    project_scope=project_scope,
                    kind=kind,
                    origin=origin,
                    version=version,
                    content=content,
                    metadata=metadata_obj,
                    integrity_digest=digest,
                    detail="incoming record rejected before persistence",
                )
                self.db.commit()
                raise MemoryRejectedError(reason)
            if existing_version > version:
                self._audit_rejected(
                    reason="stale_version",
                    scope=scope,
                    project_scope=project_scope,
                    kind=kind,
                    origin=origin,
                    version=version,
                    content=content,
                    metadata=metadata_obj,
                    integrity_digest=digest,
                    detail=f"newer version {existing_version} already exists",
                )
                self.db.commit()
                raise MemoryRejectedError("stale_version")

        for row in existing:
            self._quarantine_row(row, "superseded_by_newer_version", detail=f"superseded by v{version}")

        cursor = self.db.execute(
            """
            INSERT INTO memories(
                scope, kind, content, importance, created_at, embedding, metadata,
                allow_global, allow_training, confidential, schema_version, origin,
                project_scope, trust_class, record_class, record_version,
                integrity_digest, expires_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scope,
                kind,
                content,
                importance_value,
                created_at,
                self._encode_embedding(vector),
                self._canonical_json(metadata_obj),
                allow_global,
                allow_training,
                confidential,
                MEMORY_SCHEMA_VERSION,
                origin,
                project_scope,
                trust_class,
                record_class,
                version,
                digest,
                expires_at,
            ),
        )
        self.db.commit()
        return int(cursor.lastrowid)

    def list(
        self,
        *,
        scope: str | None = None,
        kind: str | None = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        if limit < 0:
            raise ValueError("limit must be >= 0")
        rows = self.db.execute("SELECT * FROM memories ORDER BY id ASC").fetchall()
        verified = self._verify_and_quarantine(rows, requested_scope=scope)
        if kind is not None:
            verified = [row for row in verified if row["kind"] == kind]
        records = [self._record(row) for row in verified]
        records.sort(key=lambda record: (record.importance, record.id), reverse=True)
        return records[:limit]

    def semantic_search(
        self,
        query_embedding: Iterable[float],
        *,
        scope: str | None = None,
        limit: int = 8,
    ) -> list[MemoryRecord]:
        query = self._normalize_embedding(query_embedding) or ()
        candidates = self.list(scope=scope, limit=1000)
        scored: list[tuple[float, MemoryRecord]] = []
        for record in candidates:
            if record.embedding and len(record.embedding) == len(query):
                scored.append((self._cosine(query, record.embedding), record))
        scored.sort(key=lambda item: (item[0], item[1].importance), reverse=True)
        return [record for _, record in scored[:limit]]

    def invalidate(
        self,
        *,
        scope: str,
        origin: str | None = None,
        kind: str | None = None,
        reason: str = "explicit_invalidation",
    ) -> int:
        scope = self._required_text(scope, "scope")
        if origin is None and kind is None:
            raise ValueError("bounded invalidation requires origin or kind")
        clauses = ["project_scope = ?"]
        params: list[object] = [scope]
        if origin is not None:
            clauses.append("origin = ?")
            params.append(origin)
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        rows = self.db.execute(
            f"SELECT * FROM memories WHERE {' AND '.join(clauses)} ORDER BY id", params
        ).fetchall()
        for row in rows:
            self._quarantine_row(row, reason, detail="bounded explicit invalidation")
        self.db.commit()
        return len(rows)

    def rebuild_from_authoritative(
        self,
        sources: Iterable[AuthoritativeMemory],
        *,
        project_scope: str,
    ) -> RebuildReport:
        project_scope = self._required_text(project_scope, "project_scope")
        items = list(sources)
        if not items:
            return RebuildReport(
                RebuildState.INCONCLUSIVE,
                project_scope,
                0,
                0,
                None,
                "no authoritative sources supplied",
            )

        normalized: list[AuthoritativeMemory] = []
        semantic_items: list[dict[str, object]] = []
        try:
            for item in items:
                if item.project_scope != project_scope:
                    raise MemoryRejectedError("authoritative source is out of project scope")
                origin = self._required_text(item.origin, "origin")
                kind = self._required_text(item.kind, "kind")
                version = self._validate_version(item.version)
                record_class = self._validate_record_class(item.record_class)
                if record_class == "action_suggestion":
                    raise MemoryRejectedError("authoritative rebuild cannot create action authority")
                metadata = dict(item.metadata or {})
                vector = self._normalize_embedding(item.embedding)
                expires_at = self._normalize_timestamp(item.expires_at, "expires_at")
                created_at = self._normalize_timestamp(item.created_at, "created_at")
                self._validate_payload_for_persistence(
                    content=item.content,
                    metadata=metadata,
                    scope=project_scope,
                    project_scope=project_scope,
                    kind=kind,
                    origin=origin,
                    version=version,
                )
                importance = self._finite_float(item.importance, "importance")
                normalized_item = AuthoritativeMemory(
                    project_scope=project_scope,
                    kind=kind,
                    content=item.content,
                    origin=origin,
                    version=version,
                    record_class=record_class,
                    importance=importance,
                    embedding=vector,
                    metadata=metadata,
                    expires_at=expires_at,
                    created_at=created_at or item.created_at,
                )
                normalized.append(normalized_item)
                semantic_items.append(
                    {
                        "project_scope": project_scope,
                        "kind": kind,
                        "content_sha256": self._content_hash(item.content),
                        "origin": origin,
                        "version": version,
                        "record_class": record_class,
                        "importance": importance,
                        "embedding": list(vector) if vector is not None else None,
                        "metadata": metadata,
                        "expires_at": expires_at,
                        "created_at": created_at,
                    }
                )
        except (TypeError, ValueError) as exc:
            return RebuildReport(
                RebuildState.INCONCLUSIVE,
                project_scope,
                0,
                0,
                None,
                str(exc),
            )

        key_counts: dict[tuple[str, str, int], int] = {}
        for item in normalized:
            key = (item.origin, item.kind, item.version)
            key_counts[key] = key_counts.get(key, 0) + 1
        if any(count > 1 for count in key_counts.values()):
            return RebuildReport(
                RebuildState.INCONCLUSIVE,
                project_scope,
                0,
                0,
                None,
                "authoritative source set contains duplicate logical versions",
            )

        order = sorted(
            range(len(normalized)),
            key=lambda index: (
                normalized[index].origin,
                normalized[index].kind,
                normalized[index].version,
                self._content_hash(normalized[index].content),
            ),
        )
        normalized = [normalized[index] for index in order]
        semantic_items = [semantic_items[index] for index in order]
        semantic_digest = hashlib.sha256(
            self._canonical_json(semantic_items).encode()
        ).hexdigest()

        targets = {(item.origin, item.kind) for item in normalized}
        rows = self.db.execute(
            "SELECT * FROM memories WHERE project_scope = ? ORDER BY id", (project_scope,)
        ).fetchall()
        to_replace = [row for row in rows if (row["origin"], row["kind"]) in targets]
        try:
            self.db.execute("BEGIN")
            for row in to_replace:
                self._quarantine_row(
                    row,
                    "authoritative_rebuild_replaced",
                    detail=f"rebuild set {semantic_digest}",
                )
            for item in normalized:
                metadata = dict(item.metadata or {})
                vector = item.embedding
                digest = self._digest(
                    scope=project_scope,
                    kind=item.kind,
                    content=item.content,
                    importance=item.importance,
                    created_at=item.created_at,
                    embedding=vector,
                    metadata=metadata,
                    allow_global=0,
                    allow_training=0,
                    confidential=0,
                    schema_version=MEMORY_SCHEMA_VERSION,
                    origin=item.origin,
                    project_scope=project_scope,
                    trust_class="authoritative_source",
                    record_class=item.record_class,
                    version=item.version,
                    expires_at=item.expires_at,
                )
                self.db.execute(
                    """
                    INSERT INTO memories(
                        scope, kind, content, importance, created_at, embedding, metadata,
                        allow_global, allow_training, confidential, schema_version, origin,
                        project_scope, trust_class, record_class, record_version,
                        integrity_digest, expires_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_scope,
                        item.kind,
                        item.content,
                        item.importance,
                        item.created_at,
                        self._encode_embedding(vector),
                        self._canonical_json(metadata),
                        MEMORY_SCHEMA_VERSION,
                        item.origin,
                        project_scope,
                        "authoritative_source",
                        item.record_class,
                        item.version,
                        digest,
                        item.expires_at,
                    ),
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return RebuildReport(
            RebuildState.REBUILT,
            project_scope,
            len(normalized),
            len(to_replace),
            semantic_digest,
            "deterministic authoritative rebuild completed",
        )

    def quarantine_events(self, *, project_scope: str | None = None) -> list[dict[str, object]]:
        if project_scope is None:
            rows = self.db.execute("SELECT * FROM memory_quarantine ORDER BY id").fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM memory_quarantine WHERE project_scope = ? ORDER BY id",
                (project_scope,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _verify_and_quarantine(
        self,
        rows: list[sqlite3.Row],
        *,
        requested_scope: str | None,
    ) -> list[sqlite3.Row]:
        individually_valid: list[sqlite3.Row] = []
        for row in rows:
            reason = self._row_rejection_reason(row, requested_scope=requested_scope)
            if reason is None:
                if requested_scope is None or row["project_scope"] == requested_scope:
                    individually_valid.append(row)
            else:
                self._quarantine_row(row, reason, detail="read-time fail-closed validation")

        grouped: dict[tuple[str, str, str, int], list[sqlite3.Row]] = {}
        for row in individually_valid:
            key = (
                row["origin"],
                row["project_scope"],
                row["kind"],
                int(row["record_version"]),
            )
            grouped.setdefault(key, []).append(row)

        candidate_rows: list[sqlite3.Row] = []
        for group in grouped.values():
            if len(group) == 1:
                candidate_rows.extend(group)
                continue
            digests = {row["integrity_digest"] for row in group}
            if len(digests) == 1:
                group.sort(key=lambda row: int(row["id"]))
                candidate_rows.append(group[0])
                for row in group[1:]:
                    self._quarantine_row(row, "replay", detail="duplicate durable-memory record")
            else:
                for row in group:
                    self._quarantine_row(
                        row,
                        "version_conflict",
                        detail="conflicting records share origin/scope/kind/version",
                    )

        by_lineage: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
        for row in candidate_rows:
            key = (row["origin"], row["project_scope"], row["kind"])
            by_lineage.setdefault(key, []).append(row)

        final_rows: list[sqlite3.Row] = []
        for group in by_lineage.values():
            highest = max(int(row["record_version"]) for row in group)
            for row in group:
                if int(row["record_version"]) == highest:
                    final_rows.append(row)
                else:
                    self._quarantine_row(
                        row,
                        "stale_version",
                        detail=f"newer version {highest} exists",
                    )
        self.db.commit()
        return final_rows

    def _row_rejection_reason(
        self,
        row: sqlite3.Row,
        *,
        requested_scope: str | None,
    ) -> str | None:
        try:
            if int(row["schema_version"]) != MEMORY_SCHEMA_VERSION:
                return "unsupported_schema"
            if row["trust_class"] not in _SAFE_TRUST_CLASSES:
                return "invalid_trust_class"
            if row["record_class"] not in _SAFE_RECORD_CLASSES:
                return "invalid_record_class"
            if int(row["record_version"]) < 1:
                return "invalid_version"
            if not row["origin"] or not row["project_scope"]:
                return "missing_provenance"
            if row["scope"] != row["project_scope"]:
                return "scope_mismatch"
            if requested_scope is not None and row["project_scope"] != requested_scope:
                return "cross_project_scope"
            metadata = self._safe_metadata(row["metadata"])
            vector = self._safe_embedding(row["embedding"])
            if self._contains_secret(row["content"]) or self._contains_secret(
                self._canonical_json(metadata)
            ):
                return "secret_embedding"
            if self._authority_spoof_reason(row["content"], metadata) is not None:
                return "authority_spoofing"
            expires_at = self._normalize_timestamp(row["expires_at"], "expires_at")
            if expires_at is not None and datetime.fromisoformat(expires_at) <= datetime.now(UTC):
                return "expired"
            expected = self._digest(
                scope=row["scope"],
                kind=row["kind"],
                content=row["content"],
                importance=float(row["importance"]),
                created_at=row["created_at"],
                embedding=vector,
                metadata=metadata,
                allow_global=int(row["allow_global"]),
                allow_training=int(row["allow_training"]),
                confidential=int(row["confidential"]),
                schema_version=int(row["schema_version"]),
                origin=row["origin"],
                project_scope=row["project_scope"],
                trust_class=row["trust_class"],
                record_class=row["record_class"],
                version=int(row["record_version"]),
                expires_at=expires_at,
            )
            if not row["integrity_digest"] or not hmac.compare_digest(
                expected, row["integrity_digest"]
            ):
                return "integrity_mismatch"
        except (TypeError, ValueError, json.JSONDecodeError, OverflowError):
            return "malformed"
        return None

    def _validate_payload_for_persistence(
        self,
        *,
        content: str,
        metadata: Mapping[str, object],
        scope: str,
        project_scope: str,
        kind: str,
        origin: str,
        version: int,
    ) -> None:
        if not isinstance(content, str) or not content.strip():
            raise MemoryRejectedError("content must be a non-empty string")
        metadata_json = self._canonical_json(metadata)
        if self._contains_secret(content) or self._contains_secret(metadata_json):
            self._audit_rejected(
                reason="secret_embedding",
                scope=scope,
                project_scope=project_scope,
                kind=kind,
                origin=origin,
                version=version,
                content=content,
                metadata=metadata,
                integrity_digest=None,
                detail="secret-like payload rejected; raw value not persisted",
            )
            self.db.commit()
            raise MemoryRejectedError("secret_embedding")
        authority_reason = self._authority_spoof_reason(content, metadata)
        if authority_reason is not None:
            self._audit_rejected(
                reason="authority_spoofing",
                scope=scope,
                project_scope=project_scope,
                kind=kind,
                origin=origin,
                version=version,
                content=content,
                metadata=metadata,
                integrity_digest=None,
                detail=authority_reason,
            )
            self.db.commit()
            raise MemoryRejectedError("authority_spoofing")

    @staticmethod
    def _authority_spoof_reason(
        content: str,
        metadata: Mapping[str, object],
    ) -> str | None:
        for key in metadata:
            if str(key).strip().lower() in _PRIVILEGED_METADATA_KEYS:
                return f"privileged metadata key rejected: {key}"
        for pattern in _AUTHORITY_PATTERNS:
            if pattern.search(content):
                return "memory content attempts to create or override authority"
        return None

    @staticmethod
    def _contains_secret(value: str) -> bool:
        return any(pattern.search(value) for pattern in _SECRET_PATTERNS)

    def _quarantine_row(self, row: sqlite3.Row, reason: str, *, detail: str) -> None:
        self._audit_rejected(
            reason=reason,
            scope=row["scope"],
            project_scope=row["project_scope"],
            kind=row["kind"],
            origin=row["origin"],
            version=int(row["record_version"]) if row["record_version"] is not None else None,
            content=row["content"],
            metadata=self._safe_metadata(row["metadata"]),
            integrity_digest=row["integrity_digest"],
            detail=detail,
            memory_id=int(row["id"]),
        )
        self.db.execute("DELETE FROM memories WHERE id = ?", (row["id"],))

    def _audit_rejected(
        self,
        *,
        reason: str,
        scope: str | None,
        project_scope: str | None,
        kind: str | None,
        origin: str | None,
        version: int | None,
        content: str,
        metadata: Mapping[str, object],
        integrity_digest: str | None,
        detail: str,
        memory_id: int | None = None,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO memory_quarantine(
                memory_id, quarantined_at, reason, scope, project_scope, kind, origin,
                record_version, content_sha256, integrity_digest, metadata_sha256, detail
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                datetime.now(UTC).isoformat(),
                reason,
                scope,
                project_scope,
                kind,
                origin,
                version,
                self._content_hash(content),
                integrity_digest,
                hashlib.sha256(self._canonical_json(metadata).encode()).hexdigest(),
                detail[:_MAX_AUDIT_DETAIL],
            ),
        )

    @staticmethod
    def _same_semantic_payload(
        row: sqlite3.Row,
        *,
        scope: str,
        content: str,
        importance: float,
        embedding: tuple[float, ...] | None,
        metadata: Mapping[str, object],
        trust_class: str,
        record_class: str,
        expires_at: str | None,
    ) -> bool:
        try:
            return (
                row["scope"] == scope
                and row["content"] == content
                and float(row["importance"]) == importance
                and MemoryStore._safe_embedding(row["embedding"]) == embedding
                and MemoryStore._safe_metadata(row["metadata"]) == dict(metadata)
                and row["trust_class"] == trust_class
                and row["record_class"] == record_class
                and row["expires_at"] == expires_at
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return False

    @staticmethod
    def _digest(
        *,
        scope: str,
        kind: str,
        content: str,
        importance: float,
        created_at: str,
        embedding: tuple[float, ...] | None,
        metadata: Mapping[str, object],
        allow_global: int,
        allow_training: int,
        confidential: int,
        schema_version: int,
        origin: str,
        project_scope: str,
        trust_class: str,
        record_class: str,
        version: int,
        expires_at: str | None,
    ) -> str:
        payload = {
            "allow_global": allow_global,
            "allow_training": allow_training,
            "confidential": confidential,
            "content": content,
            "created_at": created_at,
            "embedding": list(embedding) if embedding is not None else None,
            "expires_at": expires_at,
            "importance": importance,
            "kind": kind,
            "metadata": dict(metadata),
            "origin": origin,
            "project_scope": project_scope,
            "record_class": record_class,
            "schema_version": schema_version,
            "scope": scope,
            "trust_class": trust_class,
            "version": version,
        }
        return hashlib.sha256(MemoryStore._canonical_json(payload).encode()).hexdigest()

    @staticmethod
    def _canonical_json(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def _normalize_embedding(embedding: Iterable[float] | None) -> tuple[float, ...] | None:
        if embedding is None:
            return None
        vector = tuple(float(value) for value in embedding)
        if any(not math.isfinite(value) for value in vector):
            raise ValueError("embedding values must be finite")
        return vector

    @staticmethod
    def _encode_embedding(embedding: tuple[float, ...] | None) -> str | None:
        return json.dumps(list(embedding)) if embedding is not None else None

    @staticmethod
    def _safe_embedding(value: str | None) -> tuple[float, ...] | None:
        if value is None:
            return None
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            raise ValueError("embedding must be a JSON list")
        vector = tuple(float(item) for item in parsed)
        if any(not math.isfinite(item) for item in vector):
            raise ValueError("embedding values must be finite")
        return vector

    @staticmethod
    def _safe_metadata(value: str) -> dict[str, object]:
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError("metadata must be a JSON object")
        return parsed

    @staticmethod
    def _required_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _validate_trust_class(value: str) -> str:
        if value not in _SAFE_TRUST_CLASSES:
            raise ValueError(f"unsupported trust_class: {value}")
        return value

    @staticmethod
    def _validate_record_class(value: str) -> str:
        if value not in _SAFE_RECORD_CLASSES:
            raise ValueError(f"unsupported record_class: {value}")
        return value

    @staticmethod
    def _validate_version(value: int) -> int:
        version = int(value)
        if version < 1:
            raise ValueError("version must be >= 1")
        return version

    @staticmethod
    def _finite_float(value: float, field: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("f{field} must be finite")
        return result

    @staticmethod
    def _normalize_timestamp(value: str | None, field: str) -> str | None:
        if value is None:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError(f"{field} must include a timezone")
        return parsed.astimezone(UTC).isoformat()

    @staticmethod
    def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def _record(row: sqlite3.Row) -> MemoryRecord:
        vector = MemoryStore._safe_embedding(row["embedding"])
        return MemoryRecord(
            id=row["id"],
            scope=row["scope"],
            kind=row["kind"],
            content=row["content"],
            importance=row["importance"],
            created_at=row["created_at"],
            embedding=vector,
            metadata=MemoryStore._safe_metadata(row["metadata"]),
            schema_version=int(row["schema_version"]),
            origin=row["origin"],
            project_scope=row["project_scope"],
            trust_class=row["trust_class"],
            record_class=row["record_class"],
            version=int(row["record_version"]),
            integrity_digest=row["integrity_digest"],
            expires_at=row["expires_at"],
        )

    def close(self) -> None:
        self.db.close()
