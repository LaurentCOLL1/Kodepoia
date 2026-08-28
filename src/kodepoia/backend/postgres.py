from __future__ import annotations

import hashlib
import json
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Iterable, Iterator, Mapping, Protocol, Sequence

from .contracts import canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SQLSTATE_DEADLOCK = "40P01"
_SQLSTATE_SERIALIZATION = "40001"


class PostgresPolicyError(ValueError):
    """Raised when PostgreSQL configuration or migration policy is unsafe."""


class PostgresStateError(RuntimeError):
    """Raised when authoritative PostgreSQL state violates an expected invariant."""


class PostgresConcurrencyError(PostgresStateError):
    """Raised when an optimistic/pessimistic concurrency operation cannot commit safely."""


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise PostgresPolicyError(f"{field} must be a stable identifier")
    return value


def _bounded_text(value: str, *, field: str, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not value
        or len(value) > maximum
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise PostgresPolicyError(f"{field} must be non-empty bounded text")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise PostgresPolicyError(f"{field} must be lowercase SHA-256")
    return value


def sql_sha256(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise PostgresPolicyError("migration SQL must be non-empty text")
    normalized = sql.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class PostgresIsolationLevel(StrEnum):
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"

    @property
    def sql(self) -> str:
        return self.value.replace("_", " ").upper()


class PostgresCapabilityState(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PostgresSecretRef:
    """Reference to a DSN secret. The DSN value itself is intentionally absent."""

    secret_id: str

    def __post_init__(self) -> None:
        _stable_id(self.secret_id, field="secret_id")

    def canonical(self) -> dict[str, str]:
        return {"secret_id": self.secret_id}


@dataclass(frozen=True, slots=True)
class PostgresConnectionPolicy:
    environment_id: str
    dsn_ref: PostgresSecretRef
    application_name: str = "kodepoia"
    connect_timeout_s: int = 5
    statement_timeout_ms: int = 10_000
    lock_timeout_ms: int = 2_000
    idle_transaction_timeout_ms: int = 15_000
    max_connections: int = 8
    ssl_required: bool = False

    def __post_init__(self) -> None:
        _stable_id(self.environment_id, field="environment_id")
        _stable_id(self.application_name, field="application_name")
        bounded = {
            "connect_timeout_s": (self.connect_timeout_s, 1, 60),
            "statement_timeout_ms": (self.statement_timeout_ms, 100, 600_000),
            "lock_timeout_ms": (self.lock_timeout_ms, 50, 60_000),
            "idle_transaction_timeout_ms": (self.idle_transaction_timeout_ms, 100, 600_000),
            "max_connections": (self.max_connections, 1, 128),
        }
        for field, (value, minimum, maximum) in bounded.items():
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                raise PostgresPolicyError(f"{field} must be an integer in [{minimum}, {maximum}]")
        if not isinstance(self.ssl_required, bool):
            raise PostgresPolicyError("ssl_required must be boolean")

    def canonical(self) -> dict[str, Any]:
        return {
            "environment_id": self.environment_id,
            "dsn_ref": self.dsn_ref.canonical(),
            "application_name": self.application_name,
            "connect_timeout_s": self.connect_timeout_s,
            "statement_timeout_ms": self.statement_timeout_ms,
            "lock_timeout_ms": self.lock_timeout_ms,
            "idle_transaction_timeout_ms": self.idle_transaction_timeout_ms,
            "max_connections": self.max_connections,
            "ssl_required": self.ssl_required,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class PostgresCapabilitySnapshot:
    snapshot_id: str
    server_version_num: int
    server_version: str
    state: PostgresCapabilityState
    current_major: int = 18
    features: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.snapshot_id, field="snapshot_id")
        if isinstance(self.server_version_num, bool) or not isinstance(self.server_version_num, int):
            raise PostgresPolicyError("server_version_num must be integer")
        _bounded_text(self.server_version, field="server_version", maximum=256)
        if isinstance(self.current_major, bool) or not isinstance(self.current_major, int) or self.current_major < 1:
            raise PostgresPolicyError("current_major must be a positive integer")
        object.__setattr__(self, "features", tuple(sorted({_stable_id(x, field="feature") for x in self.features})))
        object.__setattr__(self, "blockers", tuple(sorted({_bounded_text(x, field="blocker") for x in self.blockers})))

    @property
    def server_major(self) -> int:
        return self.server_version_num // 10_000

    @property
    def stable_supported(self) -> bool:
        return self.state is PostgresCapabilityState.AVAILABLE and self.server_major == self.current_major

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "server_version_num": self.server_version_num,
            "server_version": self.server_version,
            "server_major": self.server_major,
            "current_major": self.current_major,
            "state": self.state.value,
            "stable_supported": self.stable_supported,
            "features": list(self.features),
            "blockers": list(self.blockers),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


def capability_from_server_version(
    *, snapshot_id: str, server_version_num: int, server_version: str, required_major: int = 18
) -> PostgresCapabilitySnapshot:
    major = server_version_num // 10_000
    if major == required_major:
        state = PostgresCapabilityState.AVAILABLE
        blockers: tuple[str, ...] = ()
    elif major < required_major:
        state = PostgresCapabilityState.UNSUPPORTED
        blockers = (f"PostgreSQL {required_major}.x required; server major is {major}",)
    else:
        state = PostgresCapabilityState.DEGRADED
        blockers = (f"PostgreSQL {major} is not the accepted stable production authority",)
    return PostgresCapabilitySnapshot(
        snapshot_id=snapshot_id,
        server_version_num=server_version_num,
        server_version=server_version,
        state=state,
        current_major=required_major,
        features=("transactions", "migrations", "row_locks", "advisory_locks", "jsonb"),
        blockers=blockers,
    )


@dataclass(frozen=True, slots=True)
class PostgresMigration:
    migration_id: str
    sequence: int
    description: str
    forward_sql: str
    rollback_sql: str
    checksum: str = ""

    def __post_init__(self) -> None:
        _stable_id(self.migration_id, field="migration_id")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 1:
            raise PostgresPolicyError("migration sequence must be a positive integer")
        _bounded_text(self.description, field="description", maximum=256)
        if not self.forward_sql.strip() or not self.rollback_sql.strip():
            raise PostgresPolicyError("forward_sql and rollback_sql are required")
        computed = sql_sha256(self.forward_sql)
        if self.checksum:
            _sha256(self.checksum, field="checksum")
            if self.checksum != computed:
                raise PostgresPolicyError("migration checksum does not match forward_sql")
        else:
            object.__setattr__(self, "checksum", computed)

    def canonical(self) -> dict[str, Any]:
        return {
            "migration_id": self.migration_id,
            "sequence": self.sequence,
            "description": self.description,
            "checksum": self.checksum,
            "rollback_checksum": sql_sha256(self.rollback_sql),
        }


@dataclass(frozen=True, slots=True)
class PostgresMigrationPlan:
    schema_id: str
    migrations: tuple[PostgresMigration, ...]

    def __post_init__(self) -> None:
        _stable_id(self.schema_id, field="schema_id")
        ordered = tuple(sorted(self.migrations, key=lambda item: item.sequence))
        if len({item.migration_id for item in ordered}) != len(ordered):
            raise PostgresPolicyError("migration IDs must be unique")
        if len({item.sequence for item in ordered}) != len(ordered):
            raise PostgresPolicyError("migration sequences must be unique")
        expected = tuple(range(1, len(ordered) + 1))
        if tuple(item.sequence for item in ordered) != expected:
            raise PostgresPolicyError("migration sequences must be contiguous starting at 1")
        object.__setattr__(self, "migrations", ordered)

    def canonical(self) -> dict[str, Any]:
        return {"schema_id": self.schema_id, "migrations": [item.canonical() for item in self.migrations]}

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class PostgresMigrationRecord:
    migration_id: str
    sequence: int
    checksum: str
    schema_digest: str

    def __post_init__(self) -> None:
        _stable_id(self.migration_id, field="migration_id")
        _sha256(self.checksum, field="checksum")
        _sha256(self.schema_digest, field="schema_digest")


@dataclass(frozen=True, slots=True)
class PostgresTransactionPolicy:
    isolation: PostgresIsolationLevel = PostgresIsolationLevel.READ_COMMITTED
    max_retries: int = 2
    retry_backoff_ms: int = 50

    def __post_init__(self) -> None:
        if isinstance(self.max_retries, bool) or not isinstance(self.max_retries, int) or not 0 <= self.max_retries <= 8:
            raise PostgresPolicyError("max_retries must be in [0, 8]")
        if (
            isinstance(self.retry_backoff_ms, bool)
            or not isinstance(self.retry_backoff_ms, int)
            or not 0 <= self.retry_backoff_ms <= 10_000
        ):
            raise PostgresPolicyError("retry_backoff_ms must be in [0, 10000]")


@dataclass(frozen=True, slots=True)
class PostgresTransactionEvidence:
    transaction_id: str
    isolation: PostgresIsolationLevel
    attempts: int
    committed: bool
    sqlstate: str | None = None

    def __post_init__(self) -> None:
        _stable_id(self.transaction_id, field="transaction_id")
        if isinstance(self.attempts, bool) or not isinstance(self.attempts, int) or self.attempts < 1:
            raise PostgresPolicyError("attempts must be positive")
        if self.sqlstate is not None:
            _bounded_text(self.sqlstate, field="sqlstate", maximum=16)

    def canonical(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "isolation": self.isolation.value,
            "attempts": self.attempts,
            "committed": self.committed,
            "sqlstate": self.sqlstate,
        }


@dataclass(frozen=True, slots=True)
class PostgresFixtureSnapshot:
    snapshot_id: str
    schema_digest: str
    tables: Mapping[str, tuple[Mapping[str, Any], ...]]
    payload_sha256: str = ""

    def __post_init__(self) -> None:
        _stable_id(self.snapshot_id, field="snapshot_id")
        _sha256(self.schema_digest, field="schema_digest")
        normalized: dict[str, tuple[Mapping[str, Any], ...]] = {}
        for table, rows in sorted(self.tables.items()):
            _stable_id(table, field="table")
            normalized[table] = tuple(dict(row) for row in rows)
        object.__setattr__(self, "tables", normalized)
        digest = canonical_sha256(self.payload())
        if self.payload_sha256:
            _sha256(self.payload_sha256, field="payload_sha256")
            if self.payload_sha256 != digest:
                raise PostgresPolicyError("snapshot payload digest mismatch")
        else:
            object.__setattr__(self, "payload_sha256", digest)

    def payload(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "schema_digest": self.schema_digest,
            "tables": {name: [dict(row) for row in rows] for name, rows in self.tables.items()},
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.payload(), "payload_sha256": self.payload_sha256}


class CursorLike(Protocol):
    rowcount: int

    def execute(self, query: str, params: Sequence[Any] | None = None) -> Any: ...

    def fetchone(self) -> Sequence[Any] | Mapping[str, Any] | None: ...

    def fetchall(self) -> Sequence[Sequence[Any] | Mapping[str, Any]]: ...

    def __enter__(self) -> CursorLike: ...

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...


class ConnectionLike(Protocol):
    def cursor(self, *args: Any, **kwargs: Any) -> CursorLike: ...

    def execute(self, query: str, params: Sequence[Any] | None = None) -> Any: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close(self) -> None: ...


class PostgresAdapter:
    """Small governed psycopg boundary. A DSN is resolved only at connection time."""

    def __init__(
        self,
        policy: PostgresConnectionPolicy,
        *,
        secret_resolver: Callable[[PostgresSecretRef], str],
        connector: Callable[..., ConnectionLike] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.policy = policy
        self._secret_resolver = secret_resolver
        self._connector = connector
        self._sleeper = sleeper

    def __repr__(self) -> str:
        return f"PostgresAdapter(environment_id={self.policy.environment_id!r}, dsn_ref=<redacted>)"

    def _connect_callable(self) -> Callable[..., ConnectionLike]:
        if self._connector is not None:
            return self._connector
        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError as exc:
            raise PostgresStateError(
                "PostgreSQL capability requires the optional 'postgres' dependency"
            ) from exc
        return psycopg.connect

    @contextmanager
    def connect(self) -> Iterator[ConnectionLike]:
        dsn = self._secret_resolver(self.policy.dsn_ref)
        if not isinstance(dsn, str) or not dsn.strip():
            raise PostgresStateError("resolved PostgreSQL DSN is unavailable")
        kwargs: dict[str, Any] = {
            "connect_timeout": self.policy.connect_timeout_s,
            "application_name": self.policy.application_name,
        }
        if self.policy.ssl_required:
            kwargs["sslmode"] = "require"
        conn = self._connect_callable()(dsn, **kwargs)
        try:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = %s", (self.policy.statement_timeout_ms,))
                cur.execute("SET lock_timeout = %s", (self.policy.lock_timeout_ms,))
                cur.execute(
                    "SET idle_in_transaction_session_timeout = %s",
                    (self.policy.idle_transaction_timeout_ms,),
                )
            yield conn
        finally:
            conn.close()

    def probe(self, *, snapshot_id: str = "postgres-probe") -> PostgresCapabilitySnapshot:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SHOW server_version_num")
            row_num = cur.fetchone()
            cur.execute("SELECT version()")
            row_text = cur.fetchone()
        if row_num is None or row_text is None:
            raise PostgresStateError("PostgreSQL capability probe returned no version")
        server_version_num = int(row_num[0] if not isinstance(row_num, Mapping) else row_num["server_version_num"])
        server_version = str(row_text[0] if not isinstance(row_text, Mapping) else next(iter(row_text.values())))
        return capability_from_server_version(
            snapshot_id=snapshot_id,
            server_version_num=server_version_num,
            server_version=server_version,
        )

    def ensure_migration_ledger(self, conn: ConnectionLike) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kodepoia_schema_migrations (
                migration_id text PRIMARY KEY,
                sequence integer NOT NULL UNIQUE,
                checksum char(64) NOT NULL,
                schema_digest char(64) NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )

    def applied_migrations(self, conn: ConnectionLike) -> tuple[PostgresMigrationRecord, ...]:
        self.ensure_migration_ledger(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT migration_id, sequence, checksum, schema_digest "
                "FROM kodepoia_schema_migrations ORDER BY sequence"
            )
            rows = cur.fetchall()
        return tuple(
            PostgresMigrationRecord(
                migration_id=str(row[0]),
                sequence=int(row[1]),
                checksum=str(row[2]),
                schema_digest=str(row[3]),
            )
            for row in rows
        )

    def validate_migration_drift(self, conn: ConnectionLike, plan: PostgresMigrationPlan) -> None:
        records = self.applied_migrations(conn)
        if len(records) > len(plan.migrations):
            raise PostgresStateError("database contains migrations absent from repository plan")
        for record, expected in zip(records, plan.migrations, strict=False):
            if record.migration_id != expected.migration_id or record.sequence != expected.sequence:
                raise PostgresStateError("migration identity drift detected")
            if record.checksum != expected.checksum:
                raise PostgresStateError("migration checksum drift detected")
            if record.schema_digest != plan.digest():
                raise PostgresStateError("migration schema digest drift detected")

    def apply_migrations(self, conn: ConnectionLike, plan: PostgresMigrationPlan) -> int:
        self.validate_migration_drift(conn, plan)
        applied = self.applied_migrations(conn)
        count = 0
        try:
            for migration in plan.migrations[len(applied) :]:
                conn.execute(migration.forward_sql)
                conn.execute(
                    "INSERT INTO kodepoia_schema_migrations "
                    "(migration_id, sequence, checksum, schema_digest) VALUES (%s, %s, %s, %s)",
                    (migration.migration_id, migration.sequence, migration.checksum, plan.digest()),
                )
                count += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return count

    def rollback_last(self, conn: ConnectionLike, plan: PostgresMigrationPlan) -> str | None:
        self.validate_migration_drift(conn, plan)
        applied = self.applied_migrations(conn)
        if not applied:
            return None
        record = applied[-1]
        migration = next(item for item in plan.migrations if item.migration_id == record.migration_id)
        try:
            conn.execute(migration.rollback_sql)
            conn.execute("DELETE FROM kodepoia_schema_migrations WHERE migration_id = %s", (record.migration_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return record.migration_id

    def run_transaction(
        self,
        *,
        transaction_id: str,
        operation: Callable[[ConnectionLike], Any],
        policy: PostgresTransactionPolicy = PostgresTransactionPolicy(),
    ) -> tuple[Any, PostgresTransactionEvidence]:
        _stable_id(transaction_id, field="transaction_id")
        attempts = 0
        last_sqlstate: str | None = None
        while True:
            attempts += 1
            with self.connect() as conn:
                try:
                    conn.execute(f"SET TRANSACTION ISOLATION LEVEL {policy.isolation.sql}")
                    result = operation(conn)
                    conn.commit()
                    return result, PostgresTransactionEvidence(
                        transaction_id=transaction_id,
                        isolation=policy.isolation,
                        attempts=attempts,
                        committed=True,
                    )
                except Exception as exc:
                    conn.rollback()
                    last_sqlstate = getattr(exc, "sqlstate", None)
                    retryable = last_sqlstate in {_SQLSTATE_DEADLOCK, _SQLSTATE_SERIALIZATION}
                    if not retryable or attempts > policy.max_retries + 1:
                        raise
            self._sleeper((policy.retry_backoff_ms * attempts) / 1000.0)

    @staticmethod
    def optimistic_update(
        conn: ConnectionLike,
        *,
        table: str,
        id_column: str,
        id_value: Any,
        version_column: str,
        expected_version: int,
        assignments: Mapping[str, Any],
    ) -> int:
        for identifier in (table, id_column, version_column, *assignments.keys()):
            _stable_id(identifier, field="SQL identifier")
        if not assignments:
            raise PostgresPolicyError("optimistic update requires assignments")
        if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 0:
            raise PostgresPolicyError("expected_version must be a non-negative integer")
        ordered = sorted(assignments.items())
        set_sql = ", ".join(f'"{key}" = %s' for key, _ in ordered)
        params = [value for _, value in ordered]
        params.extend([id_value, expected_version])
        query = (
            f'UPDATE "{table}" SET {set_sql}, "{version_column}" = "{version_column}" + 1 '
            f'WHERE "{id_column}" = %s AND "{version_column}" = %s RETURNING "{version_column}"'
        )
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            row = cur.fetchone()
        if row is None:
            raise PostgresConcurrencyError("optimistic concurrency conflict")
        return int(row[0] if not isinstance(row, Mapping) else next(iter(row.values())))

    @staticmethod
    def lock_row(
        conn: ConnectionLike,
        *,
        table: str,
        id_column: str,
        id_value: Any,
        columns: Sequence[str],
    ) -> Sequence[Any] | Mapping[str, Any]:
        for identifier in (table, id_column, *columns):
            _stable_id(identifier, field="SQL identifier")
        if not columns:
            raise PostgresPolicyError("at least one lock-row column is required")
        projection = ", ".join(f'"{column}"' for column in columns)
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT {projection} FROM "{table}" WHERE "{id_column}" = %s FOR UPDATE',
                (id_value,),
            )
            row = cur.fetchone()
        if row is None:
            raise PostgresStateError("row to lock does not exist")
        return row

    @staticmethod
    def claim_idempotency_key(conn: ConnectionLike, *, scope: str, key: str, request_digest: str) -> bool:
        _stable_id(scope, field="scope")
        _stable_id(key, field="idempotency key")
        _sha256(request_digest, field="request_digest")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kodepoia_idempotency_keys (
                scope text NOT NULL,
                idempotency_key text NOT NULL,
                request_digest char(64) NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (scope, idempotency_key)
            )
            """
        )
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO kodepoia_idempotency_keys (scope, idempotency_key, request_digest) "
                "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING idempotency_key",
                (scope, key, request_digest),
            )
            inserted = cur.fetchone()
        if inserted is not None:
            return True
        with conn.cursor() as cur:
            cur.execute(
                "SELECT request_digest FROM kodepoia_idempotency_keys WHERE scope = %s AND idempotency_key = %s",
                (scope, key),
            )
            existing = cur.fetchone()
        if existing is None:
            raise PostgresStateError("idempotency key disappeared during validation")
        existing_digest = str(existing[0] if not isinstance(existing, Mapping) else next(iter(existing.values())))
        if existing_digest != request_digest:
            raise PostgresStateError("idempotency key reused for a different request")
        return False

    @staticmethod
    def fixture_snapshot(
        *,
        snapshot_id: str,
        schema_digest: str,
        table_rows: Mapping[str, Iterable[Mapping[str, Any]]],
        primary_keys: Mapping[str, str],
    ) -> PostgresFixtureSnapshot:
        normalized: dict[str, tuple[Mapping[str, Any], ...]] = {}
        for table, rows in table_rows.items():
            _stable_id(table, field="table")
            key = primary_keys.get(table)
            if key is None:
                raise PostgresPolicyError(f"primary key is required for snapshot table {table}")
            _stable_id(key, field="primary key")
            normalized[table] = tuple(sorted((dict(row) for row in rows), key=lambda row: json.dumps(row[key], sort_keys=True)))
        return PostgresFixtureSnapshot(
            snapshot_id=snapshot_id,
            schema_digest=schema_digest,
            tables=normalized,
        )


def snapshot_semantic_digest(snapshot: PostgresFixtureSnapshot) -> str:
    """Digest semantic table content while ignoring snapshot identity metadata."""

    payload = {
        "schema_digest": snapshot.schema_digest,
        "tables": {name: [dict(row) for row in rows] for name, rows in snapshot.tables.items()},
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
