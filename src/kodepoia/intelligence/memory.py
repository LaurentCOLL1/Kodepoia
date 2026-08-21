from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from kodepoia.core.governance import GovernancePolicy


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


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.db.executescript("""
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
        """)
        self.db.commit()

    def add(self, scope: str, kind: str, content: str, *, importance: float = 0.5, embedding: Iterable[float] | None = None, metadata: dict[str, object] | None = None, governance: GovernancePolicy | None = None) -> int:
        governance = governance or GovernancePolicy()
        vector = json.dumps(list(embedding)) if embedding is not None else None
        cursor = self.db.execute("""INSERT INTO memories(scope, kind, content, importance, created_at, embedding, metadata,
               allow_global, allow_training, confidential) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (scope, kind, content, float(importance), datetime.now(UTC).isoformat(), vector, json.dumps(metadata or {}, ensure_ascii=False), int(governance.allow_global_memory), int(governance.allow_training_dataset), int(governance.confidential)))
        self.db.commit()
        return int(cursor.lastrowid)

    def list(self, *, scope: str | None = None, kind: str | None = None, limit: int = 100) -> list[MemoryRecord]:
        clauses: list[str] = []
        params: list[object] = []
        if scope:
            clauses.append("scope = ?")
            params.append(scope)
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.execute(f"SELECT * FROM memories {where} ORDER BY importance DESC, id DESC LIMIT ?", (*params, limit)).fetchall()
        return [self._record(row) for row in rows]

    def semantic_search(self, query_embedding: Iterable[float], *, scope: str | None = None, limit: int = 8) -> list[MemoryRecord]:
        query = tuple(float(value) for value in query_embedding)
        candidates = self.list(scope=scope, limit=1000)
        scored: list[tuple[float, MemoryRecord]] = []
        for record in candidates:
            if record.embedding and len(record.embedding) == len(query):
                scored.append((self._cosine(query, record.embedding), record))
        scored.sort(key=lambda item: (item[0], item[1].importance), reverse=True)
        return [record for _, record in scored[:limit]]

    @staticmethod
    def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def _record(row: sqlite3.Row) -> MemoryRecord:
        vector = tuple(json.loads(row["embedding"])) if row["embedding"] else None
        return MemoryRecord(id=row["id"], scope=row["scope"], kind=row["kind"], content=row["content"], importance=row["importance"], created_at=row["created_at"], embedding=vector, metadata=json.loads(row["metadata"]))

    def close(self) -> None:
        self.db.close()
