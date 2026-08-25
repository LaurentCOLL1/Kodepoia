from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.desktop.persistence import (
    ColumnDefinition,
    ComparisonOperator,
    DatabaseState,
    ForeignKeyDefinition,
    MigrationGraph,
    MigrationOperation,
    MigrationOperationKind,
    MigrationStep,
    PersistenceGovernance,
    QueryFilter,
    QueryIntent,
    QueryOperation,
    SQLitePersistenceService,
    SQLitePolicy,
    SQLiteValueType,
    SchemaDefinition,
    TableDefinition,
)


def _schema_v1() -> SchemaDefinition:
    return SchemaDefinition(
        1,
        (
            TableDefinition(
                "items",
                (
                    ColumnDefinition(
                        "id",
                        SQLiteValueType.INTEGER,
                        nullable=False,
                        primary_key=True,
                    ),
                    ColumnDefinition("name", SQLiteValueType.TEXT, nullable=False),
                ),
            ),
        ),
    )


def _schema_v2() -> SchemaDefinition:
    return SchemaDefinition(
        2,
        (
            TableDefinition(
                "items",
                (
                    ColumnDefinition(
                        "id",
                        SQLiteValueType.INTEGER,
                        nullable=False,
                        primary_key=True,
                    ),
                    ColumnDefinition("name", SQLiteValueType.TEXT, nullable=False),
                    ColumnDefinition("note", SQLiteValueType.TEXT),
                ),
            ),
        ),
    )


def _step_v1_v2(*, bad: bool = False) -> MigrationStep:
    source = _schema_v1()
    target = _schema_v2()
    column = "name" if bad else "note"
    operation = MigrationOperation(
        MigrationOperationKind.ADD_COLUMN,
        table="items",
        column_definition=ColumnDefinition(column, SQLiteValueType.TEXT),
    )
    return MigrationStep.build(
        from_version=1,
        to_version=2,
        source_digest=source.digest,
        target_digest=target.digest,
        operations=(operation,),
    )


def _insert(service: SQLitePersistenceService, item_id: int, name: str) -> int:
    result = service.execute(
        QueryIntent(
            QueryOperation.INSERT,
            "items",
            values=(("id", item_id), ("name", name)),
        )
    )
    assert isinstance(result, int)
    return result


def test_schema_digest_is_deterministic_and_identifier_injection_fails() -> None:
    left = SchemaDefinition(
        1,
        (
            TableDefinition(
                "b",
                (ColumnDefinition("id", SQLiteValueType.INTEGER, nullable=False),),
            ),
            TableDefinition(
                "a",
                (ColumnDefinition("value", SQLiteValueType.TEXT),),
            ),
        ),
    )
    right = SchemaDefinition(1, tuple(reversed(left.tables)))
    assert left.digest == right.digest

    with pytest.raises(ValueError, match="invalid query table"):
        QueryIntent(QueryOperation.SELECT, 'items"; DROP TABLE items; --').compile()


def test_query_values_are_parameterized_and_transaction_rolls_back(tmp_path: Path) -> None:
    service = SQLitePersistenceService(tmp_path / "db.sqlite3", _schema_v1())
    assert service.initialize().state is DatabaseState.READY
    payload = "x'); DROP TABLE items; --"
    assert _insert(service, 1, payload) == 1

    rows = service.execute(
        QueryIntent(
            QueryOperation.SELECT,
            "items",
            columns=("id", "name"),
            filters=(QueryFilter("id", ComparisonOperator.EQ, 1),),
        )
    )
    assert rows == [(1, payload)]

    with pytest.raises(RuntimeError, match="rollback"):
        with service.connect() as connection, service.transaction(connection):
            connection.execute('INSERT INTO "items" ("id", "name") VALUES (?, ?)', (2, "temp"))
            raise RuntimeError("rollback")

    rows = service.execute(QueryIntent(QueryOperation.SELECT, "items", columns=("id",)))
    assert rows == [(1,)]


def test_busy_timeout_and_foreign_key_policy_are_enforced(tmp_path: Path) -> None:
    schema = SchemaDefinition(
        1,
        (
            TableDefinition(
                "parent",
                (
                    ColumnDefinition(
                        "id",
                        SQLiteValueType.INTEGER,
                        nullable=False,
                        primary_key=True,
                    ),
                ),
            ),
            TableDefinition(
                "child",
                (
                    ColumnDefinition(
                        "id",
                        SQLiteValueType.INTEGER,
                        nullable=False,
                        primary_key=True,
                    ),
                    ColumnDefinition("parent_id", SQLiteValueType.INTEGER, nullable=False),
                ),
                foreign_keys=(
                    ForeignKeyDefinition(("parent_id",), "parent", ("id",), "CASCADE"),
                ),
            ),
        ),
    )
    service = SQLitePersistenceService(
        tmp_path / "db.sqlite3",
        schema,
        policy=SQLitePolicy(busy_timeout_ms=3210),
    )
    service.initialize()
    with service.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA busy_timeout").fetchone() == (3210,)
    with pytest.raises(sqlite3.IntegrityError):
        service.execute(
            QueryIntent(
                QueryOperation.INSERT,
                "child",
                values=(("id", 1), ("parent_id", 999)),
            )
        )


def test_migration_graph_rejects_tamper_cycle_and_missing_path() -> None:
    step = _step_v1_v2()
    tampered = MigrationStep(
        step.from_version,
        step.to_version,
        step.source_digest,
        step.target_digest,
        step.operations,
        "0" * 64,
    )
    with pytest.raises(ValueError, match="checksum"):
        MigrationGraph((tampered,))

    one = MigrationStep.build(
        from_version=1,
        to_version=2,
        source_digest="1" * 64,
        target_digest="2" * 64,
        operations=(
            MigrationOperation(
                MigrationOperationKind.RENAME_TABLE,
                table="a",
                new_name="b",
            ),
        ),
    )
    two = MigrationStep.build(
        from_version=2,
        to_version=1,
        source_digest="2" * 64,
        target_digest="1" * 64,
        operations=(
            MigrationOperation(
                MigrationOperationKind.RENAME_TABLE,
                table="b",
                new_name="a",
            ),
        ),
    )
    with pytest.raises(ValueError, match="cycle"):
        MigrationGraph((one, two))
    with pytest.raises(ValueError, match="missing migration path"):
        MigrationGraph((_step_v1_v2(),)).path(3, 4)


def test_migration_dry_run_commit_and_failed_restore(tmp_path: Path) -> None:
    database = tmp_path / "db.sqlite3"
    backup_root = tmp_path / "backups"
    first = SQLitePersistenceService(database, _schema_v1(), backup_root=backup_root)
    first.initialize()
    _insert(first, 1, "preserved")

    target = SQLitePersistenceService(
        database,
        _schema_v2(),
        migrations=(_step_v1_v2(),),
        backup_root=backup_root,
    )
    plan = target.dry_run_migration()
    assert plan.current_version == 1
    assert plan.target_version == 2
    assert plan.step_checksums == (_step_v1_v2().checksum,)
    assert not plan.destructive
    target.migrate()
    assert target.inspect().state is DatabaseState.READY
    assert target.execute(
        QueryIntent(QueryOperation.SELECT, "items", columns=("id", "name", "note"))
    ) == [(1, "preserved", None)]

    failed_db = tmp_path / "failed.sqlite3"
    old = SQLitePersistenceService(failed_db, _schema_v1(), backup_root=backup_root)
    old.initialize()
    _insert(old, 7, "pre-state")
    broken = SQLitePersistenceService(
        failed_db,
        _schema_v2(),
        migrations=(_step_v1_v2(bad=True),),
        backup_root=backup_root,
    )
    with pytest.raises(sqlite3.OperationalError, match="duplicate column"):
        broken.migrate()
    restored = SQLitePersistenceService(failed_db, _schema_v1(), backup_root=backup_root)
    assert restored.inspect().state is DatabaseState.READY
    assert restored.execute(
        QueryIntent(QueryOperation.SELECT, "items", columns=("id", "name"))
    ) == [(7, "pre-state")]


def test_corrupt_incompatible_and_newer_schema_states(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not a sqlite database")
    assert (
        SQLitePersistenceService(corrupt, _schema_v1()).inspect().state
        is DatabaseState.CORRUPT
    )

    incompatible = tmp_path / "incompatible.sqlite3"
    service = SQLitePersistenceService(incompatible, _schema_v1())
    service.initialize()
    with service.connect() as connection:
        connection.execute(
            'UPDATE "_kodepoia_schema" SET "digest" = ? WHERE "singleton" = 1',
            ("f" * 64,),
        )
    assert service.inspect().state is DatabaseState.INCOMPATIBLE

    newer = tmp_path / "newer.sqlite3"
    current = SQLitePersistenceService(newer, _schema_v2())
    current.initialize()
    assert (
        SQLitePersistenceService(newer, _schema_v1()).inspect().state
        is DatabaseState.NEWER_SCHEMA
    )


def test_crash_recovery_restores_checksum_bound_pre_state(tmp_path: Path) -> None:
    database = tmp_path / "project" / "db.sqlite3"
    backup_root = tmp_path / "backups"
    journal = RecoveryJournal(tmp_path / "recovery.json")
    governance = PersistenceGovernance(recovery_journal=journal)
    service = SQLitePersistenceService(
        database,
        _schema_v1(),
        backup_root=backup_root,
        governance=governance,
    )
    service.initialize()
    _insert(service, 1, "before-crash")
    backup = service.create_online_backup("pre-migration")
    from kodepoia.desktop import persistence as persistence_module

    journal.save(
        "simulated-crash",
        "sqlite_migration",
        {
            "database_path": str(database.resolve()),
            "backup_path": str(backup.resolve()),
            "backup_sha256": persistence_module._sha256(backup),
            "pre_version": 1,
            "pre_digest": _schema_v1().digest,
        },
    )
    service.execute(
        QueryIntent(
            QueryOperation.UPDATE,
            "items",
            values=(("name", "partial-change"),),
            filters=(QueryFilter("id", ComparisonOperator.EQ, 1),),
        )
    )
    assert service.recover_interrupted_migration()
    assert service.execute(
        QueryIntent(QueryOperation.SELECT, "items", columns=("name",))
    ) == [("before-crash",)]
    assert journal.load() is None


def test_destructive_migration_integrates_safechange_backup_recovery_audit(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    database = project / "db.sqlite3"
    online_backups = tmp_path / "online"
    audit = AuditLog(tmp_path / "audit.jsonl")
    recovery = RecoveryJournal(tmp_path / "recovery.json")
    safe_change = SafeChangeManager(project, tmp_path / "snapshots")
    backup_manager = BackupManager(tmp_path / "archives")

    source = _schema_v1()
    target = SchemaDefinition(2, ())
    step = MigrationStep.build(
        from_version=1,
        to_version=2,
        source_digest=source.digest,
        target_digest=target.digest,
        operations=(
            MigrationOperation(MigrationOperationKind.DROP_TABLE, table="items"),
        ),
    )
    initial = SQLitePersistenceService(database, source, backup_root=online_backups)
    initial.initialize()
    _insert(initial, 1, "before-drop")

    governance = PersistenceGovernance(
        safe_change=safe_change,
        backup_manager=backup_manager,
        recovery_journal=recovery,
        audit_log=audit,
        project_root=project,
    )
    migrated = SQLitePersistenceService(
        database,
        target,
        migrations=(step,),
        backup_root=online_backups,
        governance=governance,
    )
    assert migrated.dry_run_migration().destructive
    migrated.migrate()
    assert migrated.inspect().state is DatabaseState.READY
    assert any((tmp_path / "snapshots").iterdir())
    assert any((tmp_path / "archives").glob("*.zip"))
    assert recovery.load() is None
    assert audit.verify()


def test_import_requires_integrity_and_exact_schema(tmp_path: Path) -> None:
    destination = SQLitePersistenceService(tmp_path / "dst.sqlite3", _schema_v1())
    destination.initialize()
    _insert(destination, 1, "old")

    source = SQLitePersistenceService(tmp_path / "src.sqlite3", _schema_v1())
    source.initialize()
    _insert(source, 2, "new")
    destination.import_database(tmp_path / "src.sqlite3")
    assert destination.execute(
        QueryIntent(QueryOperation.SELECT, "items", columns=("id", "name"))
    ) == [(2, "new")]

    incompatible = SQLitePersistenceService(tmp_path / "wrong.sqlite3", _schema_v2())
    incompatible.initialize()
    with pytest.raises(ValueError, match="incompatible"):
        destination.import_database(tmp_path / "wrong.sqlite3")
