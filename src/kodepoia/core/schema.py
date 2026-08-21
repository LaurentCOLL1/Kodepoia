from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from kodepoia.exceptions import SchemaError

Migration = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class VersionedDocument:
    schema: str
    version: int
    payload: dict[str, Any]


class SchemaRegistry:
    def __init__(self) -> None:
        self._latest: dict[str, int] = {}
        self._migrations: dict[tuple[str, int], Migration] = {}

    def register(self, schema: str, latest_version: int) -> None:
        if latest_version < 1:
            raise SchemaError("Schema versions start at 1")
        self._latest[schema] = latest_version

    def add_migration(self, schema: str, from_version: int, migration: Migration) -> None:
        self._migrations[(schema, from_version)] = migration

    def migrate(self, document: VersionedDocument) -> VersionedDocument:
        latest = self._latest.get(document.schema)
        if latest is None:
            raise SchemaError(f"Unknown schema: {document.schema}")
        if document.version > latest:
            raise SchemaError("Document is newer than this Kodepoia build")
        payload = dict(document.payload)
        version = document.version
        while version < latest:
            migration = self._migrations.get((document.schema, version))
            if migration is None:
                raise SchemaError(f"Missing migration {document.schema} v{version}->v{version + 1}")
            payload = migration(payload)
            version += 1
        return VersionedDocument(document.schema, version, payload)
