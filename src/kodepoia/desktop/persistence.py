from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterator, Sequence

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_META_TABLE = "_kodepoia_schema"
_MAX_MIGRATIONS = 64
_MAX_QUERY_LIMIT = 10_000
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _require_identifier(value: str, label: str = "identifier") -> None:
    if _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"invalid {label}: {value!r}")
    if value.startswith("sqlite_"):
        raise ValueError(f"reserved SQLite {label}: {value!r}")


def _quote_identifier(value: str) -> str:
    _require_identifier(value)
    return f'"{value}"'


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SQLiteValueType(StrEnum):
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"


@dataclass(frozen=True, slots=True)
class ColumnDefinition:
    name: str
    value_type: SQLiteValueType
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False

    def validate(self) -> None:
        _require_identifier(self.name, "column")
        if self.primary_key and self.nullable:
            raise ValueError("primary-key columns must be non-nullable")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "name": self.name,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "value_type": self.value_type.value,
        }

    def sql(self) -> str:
        self.validate()
        parts = [_quote_identifier(self.name), self.value_type.value]
        if not self.nullable:
            parts.append("NOT NULL")
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if self.unique:
            parts.append("UNIQUE")
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class ForeignKeyDefinition:
    columns: tuple[str, ...]
    referenced_table: str
    referenced_columns: tuple[str, ...]
    on_delete: str = "NO ACTION"

    def validate(self) -> None:
        if not self.columns or len(self.columns) != len(self.referenced_columns):
            raise ValueError("foreign key columns must be non-empty and aligned")
        for name in self.columns:
            _require_identifier(name, "foreign-key column")
        _require_identifier(self.referenced_table, "referenced table")
        for name in self.referenced_columns:
            _require_identifier(name, "referenced column")
        if self.on_delete not in {"NO ACTION", "RESTRICT", "CASCADE", "SET NULL"}:
            raise ValueError("unsupported foreign-key delete action")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "columns": list(self.columns),
            "on_delete": self.on_delete,
            "referenced_columns": list(self.referenced_columns),
            "referenced_table": self.referenced_table,
        }

    def sql(self) -> str:
        self.validate()
        left = ", ".join(_quote_identifier(name) for name in self.columns)
        right = ", ".join(_quote_identifier(name) for name in self.referenced_columns)
        return (
            f"FOREIGN KEY ({left}) REFERENCES {_quote_identifier(self.referenced_table)} "
            f"({right}) ON DELETE {self.on_delete}"
        )


@dataclass(frozen=True, slots=True)
class TableDefinition:
    name: str
    columns: tuple[ColumnDefinition, ...]
    foreign_keys: tuple[ForeignKeyDefinition, ...] = ()

    def validate(self) -> None:
        _require_identifier(self.name, "table")
        if self.name == _META_TABLE:
            raise ValueError("reserved Kodepoia metadata table")
        if not self.columns:
            raise ValueError("table requires at least one column")
        names = [item.name for item in self.columns]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate column in table {self.name}")
        for column in self.columns:
            column.validate()
        if sum(item.primary_key for item in self.columns) > 1:
            raise ValueError("only one single-column primary key is supported")
        known = set(names)
        for foreign_key in self.foreign_keys:
            foreign_key.validate()
            if not set(foreign_key.columns) <= known:
                raise ValueError("foreign key references a missing local column")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "columns": [
                item.to_dict() for item in sorted(self.columns, key=lambda item: item.name)
            ],
            "foreign_keys": [
                item.to_dict()
                for item in sorted(
                    self.foreign_keys,
                    key=lambda item: (item.columns, item.referenced_table),
                )
            ],
            "name": self.name,
        }

    def create_sql(self) -> str:
        self.validate()
        clauses = [column.sql() for column in self.columns]
        clauses.extend(item.sql() for item in self.foreign_keys)
        return f"CREATE TABLE {_quote_identifier(self.name)} ({', '.join(clauses)})"


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    version: int
    tables: tuple[TableDefinition, ...]

    def validate(self) -> None:
        if self.version < 1:
            raise ValueError("schema version must be positive")
        names = [table.name for table in self.tables]
        if len(names) != len(set(names)):
            raise ValueError("duplicate table")
        by_name = {table.name: table for table in self.tables}
        for table in self.tables:
            table.validate()
            for foreign_key in table.foreign_keys:
                target = by_name.get(foreign_key.referenced_table)
                if target is None:
                    raise ValueError("foreign key references a missing table")
                target_columns = {item.name for item in target.columns}
                if not set(foreign_key.referenced_columns) <= target_columns:
                    raise ValueError("foreign key references a missing target column")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "tables": [
                table.to_dict() for table in sorted(self.tables, key=lambda item: item.name)
            ],
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict())).hexdigest()


class MigrationOperationKind(StrEnum):
    CREATE_TABLE = "create_table"
    ADD_COLUMN = "add_column"
    RENAME_TABLE = "rename_table"
    DROP_TABLE = "drop_table"
    CREATE_INDEX = "create_index"
    DROP_INDEX = "drop_index"


@dataclass(frozen=True, slots=True)
class MigrationOperation:
    kind: MigrationOperationKind
    table: str | None = None
    table_definition: TableDefinition | None = None
    column_definition: ColumnDefinition | None = None
    new_name: str | None = None
    index_name: str | None = None
    index_columns: tuple[str, ...] = ()
    unique: bool = False

    @property
    def destructive(self) -> bool:
        return self.kind in {MigrationOperationKind.DROP_TABLE, MigrationOperationKind.DROP_INDEX}

    def validate(self) -> None:
        if self.table is not None:
            _require_identifier(self.table, "table")
        if self.new_name is not None:
            _require_identifier(self.new_name, "new table")
        if self.index_name is not None:
            _require_identifier(self.index_name, "index")
        for name in self.index_columns:
            _require_identifier(name, "index column")
        if self.kind is MigrationOperationKind.CREATE_TABLE:
            if self.table_definition is None:
                raise ValueError("create-table operation requires table_definition")
            self.table_definition.validate()
        elif self.kind is MigrationOperationKind.ADD_COLUMN:
            if self.table is None or self.column_definition is None:
                raise ValueError("add-column operation requires table and column_definition")
            self.column_definition.validate()
        elif self.kind is MigrationOperationKind.RENAME_TABLE:
            if self.table is None or self.new_name is None:
                raise ValueError("rename-table operation requires table and new_name")
        elif self.kind is MigrationOperationKind.DROP_TABLE:
            if self.table is None:
                raise ValueError("drop-table operation requires table")
        elif self.kind is MigrationOperationKind.CREATE_INDEX:
            if self.table is None or self.index_name is None or not self.index_columns:
                raise ValueError("create-index operation requires table, index name and columns")
        elif self.kind is MigrationOperationKind.DROP_INDEX and self.index_name is None:
            raise ValueError("drop-index operation requires index name")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "column_definition": (
                self.column_definition.to_dict() if self.column_definition else None
            ),
            "index_columns": list(self.index_columns),
            "index_name": self.index_name,
            "kind": self.kind.value,
            "new_name": self.new_name,
            "table": self.table,
            "table_definition": self.table_definition.to_dict() if self.table_definition else None,
            "unique": self.unique,
        }

    def sql(self) -> str:
        self.validate()
        if self.kind is MigrationOperationKind.CREATE_TABLE:
            assert self.table_definition is not None
            return self.table_definition.create_sql()
        if self.kind is MigrationOperationKind.ADD_COLUMN:
            assert self.table is not None and self.column_definition is not None
            return (
                f"ALTER TABLE {_quote_identifier(self.table)} "
                f"ADD COLUMN {self.column_definition.sql()}"
            )
        if self.kind is MigrationOperationKind.RENAME_TABLE:
            assert self.table is not None and self.new_name is not None
            return (
                f"ALTER TABLE {_quote_identifier(self.table)} "
                f"RENAME TO {_quote_identifier(self.new_name)}"
            )
        if self.kind is MigrationOperationKind.DROP_TABLE:
            assert self.table is not None
            return f"DROP TABLE {_quote_identifier(self.table)}"
        if self.kind is MigrationOperationKind.CREATE_INDEX:
            assert self.table is not None and self.index_name is not None
            prefix = "UNIQUE " if self.unique else ""
            columns = ", ".join(_quote_identifier(name) for name in self.index_columns)
            return (
                f"CREATE {prefix}INDEX {_quote_identifier(self.index_name)} "
                f"ON {_quote_identifier(self.table)} ({columns})"
            )
        assert self.index_name is not None
        return f"DROP INDEX {_quote_identifier(self.index_name)}"


@dataclass(frozen=True, slots=True)
class MigrationStep:
    from_version: int
    to_version: int
    source_digest: str
    target_digest: str
    operations: tuple[MigrationOperation, ...]
    checksum: str

    @classmethod
    def build(
        cls,
        *,
        from_version: int,
        to_version: int,
        source_digest: str,
        target_digest: str,
        operations: Sequence[MigrationOperation],
    ) -> MigrationStep:
        provisional = cls(
            from_version,
            to_version,
            source_digest,
            target_digest,
            tuple(operations),
            "",
        )
        return cls(
            from_version,
            to_version,
            source_digest,
            target_digest,
            tuple(operations),
            provisional.calculated_checksum,
        )

    @property
    def calculated_checksum(self) -> str:
        payload = {
            "from_version": self.from_version,
            "operations": [item.to_dict() for item in self.operations],
            "source_digest": self.source_digest,
            "target_digest": self.target_digest,
            "to_version": self.to_version,
        }
        return hashlib.sha256(_canonical_json(payload)).hexdigest()

    @property
    def destructive(self) -> bool:
        return any(item.destructive for item in self.operations)

    def validate(self) -> None:
        if self.from_version < 1 or self.to_version < 1 or self.from_version == self.to_version:
            raise ValueError("migration versions must be positive and distinct")
        if _SHA256.fullmatch(self.source_digest) is None:
            raise ValueError("invalid migration source digest")
        if _SHA256.fullmatch(self.target_digest) is None:
            raise ValueError("invalid migration target digest")
        if not self.operations:
            raise ValueError("migration requires at least one typed operation")
        for operation in self.operations:
            operation.validate()
        if self.checksum != self.calculated_checksum:
            raise ValueError("migration checksum mismatch")


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    current_version: int
    target_version: int
    step_checksums: tuple[str, ...]
    destructive: bool


class MigrationGraph:
    def __init__(self, steps: Sequence[MigrationStep], *, max_steps: int = _MAX_MIGRATIONS) -> None:
        if not 1 <= max_steps <= _MAX_MIGRATIONS:
            raise ValueError("invalid migration graph bound")
        if len(steps) > max_steps:
            raise ValueError("migration graph exceeds bound")
        self.steps = tuple(steps)
        self.max_steps = max_steps
        self._validate()

    def _validate(self) -> None:
        edges: set[tuple[int, int]] = set()
        outgoing: dict[int, list[MigrationStep]] = {}
        for step in self.steps:
            step.validate()
            edge = (step.from_version, step.to_version)
            if edge in edges:
                raise ValueError("duplicate migration edge")
            edges.add(edge)
            outgoing.setdefault(step.from_version, []).append(step)
        visiting: set[int] = set()
        visited: set[int] = set()

        def visit(version: int) -> None:
            if version in visiting:
                raise ValueError("migration cycle detected")
            if version in visited:
                return
            visiting.add(version)
            for step in outgoing.get(version, []):
                visit(step.to_version)
            visiting.remove(version)
            visited.add(version)

        for version in sorted(outgoing):
            visit(version)

    def path(self, current_version: int, target_version: int) -> tuple[MigrationStep, ...]:
        if current_version == target_version:
            return ()
        outgoing: dict[int, list[MigrationStep]] = {}
        for step in self.steps:
            outgoing.setdefault(step.from_version, []).append(step)
        queue: list[tuple[int, tuple[MigrationStep, ...]]] = [(current_version, ())]
        seen = {current_version}
        while queue:
            version, current_path = queue.pop(0)
            for step in sorted(
                outgoing.get(version, []), key=lambda item: (item.to_version, item.checksum)
            ):
                next_path = (*current_path, step)
                if len(next_path) > self.max_steps:
                    continue
                if step.to_version == target_version:
                    return next_path
                if step.to_version not in seen:
                    seen.add(step.to_version)
                    queue.append((step.to_version, next_path))
        raise ValueError(
            f"missing migration path from version {current_version} to {target_version}"
        )


class QueryOperation(StrEnum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class ComparisonOperator(StrEnum):
    EQ = "="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="


@dataclass(frozen=True, slots=True)
class QueryFilter:
    column: str
    operator: ComparisonOperator
    value: object

    def validate(self) -> None:
        _require_identifier(self.column, "filter column")


@dataclass(frozen=True, slots=True)
class QueryIntent:
    operation: QueryOperation
    table: str
    columns: tuple[str, ...] = ()
    values: tuple[tuple[str, object], ...] = ()
    filters: tuple[QueryFilter, ...] = ()
    order_by: tuple[str, ...] = ()
    descending: bool = False
    limit: int | None = None

    def validate(self) -> None:
        _require_identifier(self.table, "query table")
        for name in self.columns:
            _require_identifier(name, "query column")
        value_names = [name for name, _ in self.values]
        for name in value_names:
            _require_identifier(name, "value column")
        if len(value_names) != len(set(value_names)):
            raise ValueError("duplicate query value column")
        for item in self.filters:
            item.validate()
        for name in self.order_by:
            _require_identifier(name, "order column")
        if self.limit is not None and not 1 <= self.limit <= _MAX_QUERY_LIMIT:
            raise ValueError("query limit out of bounds")
        if self.operation is QueryOperation.SELECT:
            if self.values:
                raise ValueError("select intent cannot contain values")
        elif self.operation is QueryOperation.INSERT:
            if not self.values or self.filters or self.columns or self.order_by or self.limit:
                raise ValueError("invalid insert intent")
        elif self.operation is QueryOperation.UPDATE:
            if not self.values or self.columns or self.order_by or self.limit:
                raise ValueError("invalid update intent")
        elif self.values or self.columns or self.order_by or self.limit:
            raise ValueError("invalid delete intent")

    def compile(self) -> tuple[str, tuple[object, ...]]:
        self.validate()
        table = _quote_identifier(self.table)
        parameters: list[object]
        if self.operation is QueryOperation.SELECT:
            columns = (
                ", ".join(_quote_identifier(name) for name in self.columns)
                if self.columns
                else "*"
            )
            sql = f"SELECT {columns} FROM {table}"
            parameters = []
        elif self.operation is QueryOperation.INSERT:
            names = [name for name, _ in self.values]
            sql = (
                f"INSERT INTO {table} "
                f"({', '.join(_quote_identifier(name) for name in names)}) "
                f"VALUES ({', '.join('?' for _ in names)})"
            )
            parameters = [value for _, value in self.values]
        elif self.operation is QueryOperation.UPDATE:
            assignments = ", ".join(
                f"{_quote_identifier(name)} = ?" for name, _ in self.values
            )
            sql = f"UPDATE {table} SET {assignments}"
            parameters = [value for _, value in self.values]
        else:
            sql = f"DELETE FROM {table}"
            parameters = []
        if self.filters:
            sql += " WHERE " + " AND ".join(
                f"{_quote_identifier(item.column)} {item.operator.value} ?"
                for item in self.filters
            )
            parameters.extend(item.value for item in self.filters)
        if self.operation is QueryOperation.SELECT and self.order_by:
            direction = " DESC" if self.descending else " ASC"
            sql += " ORDER BY " + ", ".join(
                f"{_quote_identifier(name)}{direction}" for name in self.order_by
            )
        if self.operation is QueryOperation.SELECT and self.limit is not None:
            sql += " LIMIT ?"
            parameters.append(self.limit)
        return sql, tuple(parameters)


class DatabaseState(StrEnum):
    ABSENT = "absent"
    READY = "ready"
    MIGRATION_REQUIRED = "migration_required"
    CORRUPT = "corrupt"
    INCOMPATIBLE = "incompatible"
    NEWER_SCHEMA = "newer_schema"


@dataclass(frozen=True, slots=True)
class DatabaseStatus:
    state: DatabaseState
    current_version: int | None
    target_version: int
    current_digest: str | None
    target_digest: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class SQLitePolicy:
    busy_timeout_ms: int = 5000
    backup_pages: int = 128
    backup_sleep_seconds: float = 0.05

    def validate(self) -> None:
        if not 1 <= self.busy_timeout_ms <= 60_000:
            raise ValueError("busy timeout out of bounds")
        if not 1 <= self.backup_pages <= 4096:
            raise ValueError("backup page batch out of bounds")
        if not 0.0 <= self.backup_sleep_seconds <= 1.0:
            raise ValueError("backup sleep out of bounds")


@dataclass(frozen=True, slots=True)
class PersistenceGovernance:
    safe_change: SafeChangeManager | None = None
    backup_manager: BackupManager | None = None
    recovery_journal: RecoveryJournal | None = None
    audit_log: AuditLog | None = None
    project_root: Path | None = None


class SQLitePersistenceService:
    def __init__(
        self,
        database_path: Path,
        schema: SchemaDefinition,
        *,
        migrations: Sequence[MigrationStep] = (),
        policy: SQLitePolicy | None = None,
        backup_root: Path | None = None,
        governance: PersistenceGovernance | None = None,
    ) -> None:
        schema.validate()
        self.policy = policy or SQLitePolicy()
        self.policy.validate()
        self.database_path = database_path.resolve(strict=False)
        self.schema = schema
        self.graph = MigrationGraph(migrations)
        self.backup_root = (
            backup_root.resolve(strict=False)
            if backup_root is not None
            else self.database_path.parent / ".kodepoia" / "sqlite-backups"
        )
        self.governance = governance or PersistenceGovernance()

    def _connect_path(self, path: Path) -> sqlite3.Connection:
        connection = sqlite3.connect(
            path,
            timeout=self.policy.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.policy.busy_timeout_ms}")
        return connection

    def connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return self._connect_path(self.database_path)

    @contextmanager
    def transaction(self, connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        else:
            connection.commit()

    def initialize(self) -> DatabaseStatus:
        if self.database_path.exists():
            status = self.inspect()
            if status.state is DatabaseState.ABSENT:
                raise AssertionError("existing database cannot be absent")
            return status
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, self.transaction(connection):
            self._create_metadata(connection)
            for table in sorted(self.schema.tables, key=lambda item: item.name):
                connection.execute(table.create_sql())
            self._write_metadata(connection, self.schema.version, self.schema.digest)
        return self.inspect()

    @staticmethod
    def _create_metadata(connection: sqlite3.Connection) -> None:
        connection.execute(
            f'CREATE TABLE "{_META_TABLE}" ('
            '"singleton" INTEGER PRIMARY KEY CHECK ("singleton" = 1), '
            '"version" INTEGER NOT NULL CHECK ("version" >= 1), '
            '"digest" TEXT NOT NULL)'
        )

    @staticmethod
    def _write_metadata(connection: sqlite3.Connection, version: int, digest: str) -> None:
        connection.execute(
            f'INSERT INTO "{_META_TABLE}" ("singleton", "version", "digest") '
            "VALUES (1, ?, ?) "
            'ON CONFLICT("singleton") DO UPDATE SET "version" = excluded."version", '
            '"digest" = excluded."digest"',
            (version, digest),
        )

    @staticmethod
    def _read_metadata(connection: sqlite3.Connection) -> tuple[int, str] | None:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (_META_TABLE,),
        ).fetchone()
        if exists is None:
            return None
        row = connection.execute(
            f'SELECT "version", "digest" FROM "{_META_TABLE}" WHERE "singleton" = 1'
        ).fetchone()
        if row is None:
            return None
        return int(row[0]), str(row[1])

    @staticmethod
    def _integrity_ok(connection: sqlite3.Connection) -> bool:
        row = connection.execute("PRAGMA quick_check").fetchone()
        return row is not None and str(row[0]).lower() == "ok"

    def inspect(self) -> DatabaseStatus:
        if not self.database_path.exists():
            return DatabaseStatus(
                DatabaseState.ABSENT,
                None,
                self.schema.version,
                None,
                self.schema.digest,
            )
        try:
            with closing(self.connect()) as connection:
                if not self._integrity_ok(connection):
                    return DatabaseStatus(
                        DatabaseState.CORRUPT,
                        None,
                        self.schema.version,
                        None,
                        self.schema.digest,
                        "SQLite quick_check failed",
                    )
                metadata = self._read_metadata(connection)
        except sqlite3.DatabaseError as exc:
            return DatabaseStatus(
                DatabaseState.CORRUPT,
                None,
                self.schema.version,
                None,
                self.schema.digest,
                str(exc),
            )
        if metadata is None:
            return DatabaseStatus(
                DatabaseState.INCOMPATIBLE,
                None,
                self.schema.version,
                None,
                self.schema.digest,
                "Kodepoia schema metadata is missing",
            )
        current_version, current_digest = metadata
        if current_version > self.schema.version:
            state = DatabaseState.NEWER_SCHEMA
        elif current_version < self.schema.version:
            state = DatabaseState.MIGRATION_REQUIRED
        elif current_digest != self.schema.digest:
            state = DatabaseState.INCOMPATIBLE
        else:
            state = DatabaseState.READY
        return DatabaseStatus(
            state,
            current_version,
            self.schema.version,
            current_digest,
            self.schema.digest,
        )

    def dry_run_migration(self) -> MigrationPlan:
        status = self.inspect()
        if status.state is DatabaseState.READY:
            return MigrationPlan(self.schema.version, self.schema.version, (), False)
        if status.state is not DatabaseState.MIGRATION_REQUIRED:
            raise ValueError(f"database is not migratable: {status.state.value}")
        assert status.current_version is not None
        path = self.graph.path(status.current_version, self.schema.version)
        current_digest = status.current_digest
        for step in path:
            if step.source_digest != current_digest:
                raise ValueError("migration source schema digest mismatch")
            current_digest = step.target_digest
        if current_digest != self.schema.digest:
            raise ValueError("migration path does not terminate at target schema digest")
        return MigrationPlan(
            status.current_version,
            self.schema.version,
            tuple(step.checksum for step in path),
            any(step.destructive for step in path),
        )

    def execute(self, intent: QueryIntent) -> list[tuple[Any, ...]] | int:
        status = self.inspect()
        if status.state is not DatabaseState.READY:
            raise RuntimeError(f"database not ready: {status.state.value}")
        sql, parameters = intent.compile()
        with closing(self.connect()) as connection, self.transaction(connection):
            cursor = connection.execute(sql, parameters)
            if intent.operation is QueryOperation.SELECT:
                return list(cursor.fetchall())
            return cursor.rowcount

    def create_online_backup(self, label: str = "snapshot") -> Path:
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", label) is None:
            raise ValueError("invalid backup label")
        status = self.inspect()
        if status.state not in {DatabaseState.READY, DatabaseState.MIGRATION_REQUIRED}:
            raise RuntimeError(f"refusing backup for database state {status.state.value}")
        self.backup_root.mkdir(parents=True, exist_ok=True)
        token = hashlib.sha256(
            f"{status.current_version}:{status.current_digest}:{label}".encode()
        ).hexdigest()[:16]
        destination = self.backup_root / f"{label}-{token}.sqlite3"
        temporary = destination.with_suffix(".tmp.sqlite3")
        temporary.unlink(missing_ok=True)
        try:
            with closing(self.connect()) as source, closing(
                self._connect_path(temporary)
            ) as target:
                source.backup(
                    target,
                    pages=self.policy.backup_pages,
                    sleep=self.policy.backup_sleep_seconds,
                )
            with closing(self._connect_path(temporary)) as check:
                if not self._integrity_ok(check):
                    raise OSError("online SQLite backup failed integrity check")
            temporary.replace(destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return destination

    def _restore_online_backup(self, backup_path: Path) -> None:
        backup_path = backup_path.resolve(strict=True)
        if backup_path.parent != self.backup_root:
            raise ValueError("backup path escapes configured backup root")
        for suffix in ("", "-wal", "-shm"):
            Path(f"{self.database_path}{suffix}").unlink(missing_ok=True)
        with closing(self._connect_path(backup_path)) as source, closing(
            self.connect()
        ) as target:
            source.backup(
                target,
                pages=self.policy.backup_pages,
                sleep=self.policy.backup_sleep_seconds,
            )
        if self.inspect().state not in {DatabaseState.READY, DatabaseState.MIGRATION_REQUIRED}:
            raise OSError("restored SQLite backup is not an accepted pre-state")

    def _govern_before_destructive_change(self) -> None:
        governance = self.governance
        if governance.safe_change is not None:
            governance.safe_change.snapshot([self.database_path])
        if governance.backup_manager is not None:
            if governance.project_root is None:
                raise ValueError("project_root required with BackupManager governance")
            governance.backup_manager.create_archive(
                governance.project_root,
                label="r12-10-sqlite",
            )

    def _audit(
        self,
        action: str,
        outcome: str,
        details: dict[str, object] | None = None,
    ) -> None:
        if self.governance.audit_log is not None:
            self.governance.audit_log.append(
                "desktop.persistence",
                action,
                "kodepoia",
                outcome,
                dict(details or {}),
            )

    def migrate(self) -> MigrationPlan:
        plan = self.dry_run_migration()
        if not plan.step_checksums:
            return plan
        status = self.inspect()
        assert status.current_version is not None
        path = self.graph.path(status.current_version, self.schema.version)
        backup = self.create_online_backup("pre-migration")
        backup_digest = _sha256(backup)
        if plan.destructive:
            self._govern_before_destructive_change()
        journal = self.governance.recovery_journal
        task_id = f"sqlite-migration-{status.current_version}-to-{self.schema.version}"
        if journal is not None:
            journal.save(
                task_id,
                "sqlite_migration",
                {
                    "backup_path": str(backup),
                    "backup_sha256": backup_digest,
                    "database_path": str(self.database_path),
                    "pre_digest": status.current_digest,
                    "pre_version": status.current_version,
                },
            )
        self._audit(
            "migrate",
            "started",
            {"from": status.current_version, "to": self.schema.version},
        )
        try:
            with closing(self.connect()) as connection, self.transaction(connection):
                current_version = status.current_version
                current_digest = status.current_digest
                for step in path:
                    step.validate()
                    if step.from_version != current_version:
                        raise ValueError("migration step version discontinuity")
                    if step.source_digest != current_digest:
                        raise ValueError("migration source digest mismatch")
                    for operation in step.operations:
                        connection.execute(operation.sql())
                    self._write_metadata(connection, step.to_version, step.target_digest)
                    current_version = step.to_version
                    current_digest = step.target_digest
                if current_version != self.schema.version or current_digest != self.schema.digest:
                    raise ValueError("migration did not reach target schema")
            final_status = self.inspect()
            if final_status.state is not DatabaseState.READY:
                raise ValueError(f"migration produced {final_status.state.value}")
        except BaseException:
            self._restore_online_backup(backup)
            restored = self.inspect()
            if (
                restored.current_version != status.current_version
                or restored.current_digest != status.current_digest
            ):
                raise OSError("failed migration could not restore accepted pre-state")
            self._audit("migrate", "rolled_back", {"from": status.current_version})
            if journal is not None:
                journal.clear()
            raise
        if journal is not None:
            journal.clear()
        self._audit("migrate", "success", {"to": self.schema.version})
        return plan

    def recover_interrupted_migration(self) -> bool:
        journal = self.governance.recovery_journal
        if journal is None:
            return False
        checkpoint = journal.load()
        if checkpoint is None or checkpoint.phase != "sqlite_migration":
            return False
        state = checkpoint.state
        if Path(str(state.get("database_path", ""))).resolve(strict=False) != self.database_path:
            raise ValueError("recovery checkpoint targets another database")
        backup = Path(str(state.get("backup_path", ""))).resolve(strict=True)
        if backup.parent != self.backup_root:
            raise ValueError("recovery backup escapes configured root")
        if _sha256(backup) != str(state.get("backup_sha256", "")):
            raise ValueError("recovery backup checksum mismatch")
        self._restore_online_backup(backup)
        status = self.inspect()
        if status.current_version != int(state["pre_version"]):
            raise OSError("recovery did not restore pre-migration version")
        if status.current_digest != str(state["pre_digest"]):
            raise OSError("recovery did not restore pre-migration digest")
        journal.clear()
        self._audit("recover_migration", "success", {"version": status.current_version})
        return True

    def import_database(self, source_path: Path) -> None:
        source_path = source_path.resolve(strict=True)
        if source_path == self.database_path:
            raise ValueError("cannot import database from itself")
        with closing(self._connect_path(source_path)) as source:
            if not self._integrity_ok(source):
                raise ValueError("import database failed integrity check")
            metadata = self._read_metadata(source)
        if metadata != (self.schema.version, self.schema.digest):
            raise ValueError("import database schema is incompatible")
        backup = self.create_online_backup("pre-import")
        self._govern_before_destructive_change()
        self._audit("import", "started", {"source_sha256": _sha256(source_path)})
        try:
            for suffix in ("", "-wal", "-shm"):
                Path(f"{self.database_path}{suffix}").unlink(missing_ok=True)
            with closing(self._connect_path(source_path)) as source, closing(
                self.connect()
            ) as target:
                source.backup(
                    target,
                    pages=self.policy.backup_pages,
                    sleep=self.policy.backup_sleep_seconds,
                )
            if self.inspect().state is not DatabaseState.READY:
                raise ValueError("imported database is not ready")
        except BaseException:
            self._restore_online_backup(backup)
            self._audit("import", "rolled_back")
            raise
        self._audit("import", "success")
