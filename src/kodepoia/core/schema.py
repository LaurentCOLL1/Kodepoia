from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

Validator = Callable[[dict[str, Any]], None]
Migrator = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class SchemaSpec:
    name: str
    version: int
    validator: Validator


class SchemaError(ValueError):
    pass


class KodeSchema:
    """Versioned schema registry with deterministic one-step migrations."""

    def __init__(self) -> None:
        self._schemas: dict[tuple[str, int], SchemaSpec] = {}
        self._migrations: dict[tuple[str, int, int], Migrator] = {}

    def register(self, spec: SchemaSpec) -> None:
        key = (spec.name, spec.version)
        if key in self._schemas:
            raise SchemaError(f"schema already registered: {key}")
        self._schemas[key] = spec

    def register_migration(self, name: str, from_version: int, to_version: int, migrator: Migrator) -> None:
        if to_version != from_version + 1:
            raise SchemaError("R1 migrations must advance exactly one version")
        key = (name, from_version, to_version)
        if key in self._migrations:
            raise SchemaError(f"migration already registered: {key}")
        self._migrations[key] = migrator

    def validate(self, name: str, version: int, payload: dict[str, Any]) -> None:
        spec = self._schemas.get((name, version))
        if spec is None:
            raise SchemaError(f"unknown schema: {name}@{version}")
        spec.validator(payload)

    def migrate(self, name: str, payload: dict[str, Any], from_version: int, to_version: int) -> dict[str, Any]:
        if to_version < from_version:
            raise SchemaError("downgrades are not supported")
        current = dict(payload)
        version = from_version
        while version < to_version:
            migrator = self._migrations.get((name, version, version + 1))
            if migrator is None:
                raise SchemaError(f"missing migration: {name} {version}->{version + 1}")
            current = migrator(dict(current))
            version += 1
        self.validate(name, to_version, current)
        return current
