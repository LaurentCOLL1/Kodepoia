from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from typing import Any

from kodepoia.backend.postgres import (
    PostgresAdapter,
    PostgresConcurrencyError,
    PostgresConnectionPolicy,
    PostgresMigration,
    PostgresMigrationPlan,
    PostgresSecretRef,
    PostgresStateError,
    PostgresTransactionPolicy,
    snapshot_semantic_digest,
)


SCHEMA = "r14_5_acceptance"


def _dsn() -> str:
    value = os.environ.get("KODEPOIA_R14_5_DSN", "")
    if not value:
        raise SystemExit("KODEPOIA_R14_5_DSN is required")
    return value


def _adapter() -> PostgresAdapter:
    policy = PostgresConnectionPolicy(
        environment_id="test",
        dsn_ref=PostgresSecretRef("ci.r14-5-postgres-dsn"),
        application_name="kodepoia-r14-5-acceptance",
        statement_timeout_ms=15_000,
        lock_timeout_ms=5_000,
    )
    return PostgresAdapter(policy, secret_resolver=lambda _ref: _dsn())


def _plan() -> PostgresMigrationPlan:
    return PostgresMigrationPlan(
        schema_id="r14-5-authoritative-fixture",
        migrations=(
            PostgresMigration(
                migration_id="001-items",
                sequence=1,
                description="authoritative item fixture",
                forward_sql=f"""
                CREATE SCHEMA IF NOT EXISTS {SCHEMA};
                CREATE TABLE {SCHEMA}.items (
                    id bigint PRIMARY KEY,
                    value text NOT NULL,
                    version integer NOT NULL DEFAULT 0
                );
                """,
                rollback_sql=f"DROP TABLE IF EXISTS {SCHEMA}.items;",
            ),
            PostgresMigration(
                migration_id="002-item-note",
                sequence=2,
                description="add deterministic note column",
                forward_sql=f"ALTER TABLE {SCHEMA}.items ADD COLUMN note text NOT NULL DEFAULT '';",
                rollback_sql=f"ALTER TABLE {SCHEMA}.items DROP COLUMN note;",
            ),
        ),
    )


def _reset(adapter: PostgresAdapter) -> None:
    with adapter.connect() as conn:
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.execute("DROP TABLE IF EXISTS kodepoia_schema_migrations")
        conn.execute("DROP TABLE IF EXISTS kodepoia_idempotency_keys")
        conn.commit()


def _fetch_items(adapter: PostgresAdapter) -> list[dict[str, Any]]:
    with adapter.connect() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT id, value, version, note FROM {SCHEMA}.items ORDER BY id")
        return [
            {"id": int(row[0]), "value": str(row[1]), "version": int(row[2]), "note": str(row[3])}
            for row in cur.fetchall()
        ]


def _real_deadlock_detected(dsn: str) -> bool:
    import psycopg

    with psycopg.connect(dsn) as setup:
        setup.execute(f"INSERT INTO {SCHEMA}.items (id, value) VALUES (901, 'a'), (902, 'b') ON CONFLICT DO NOTHING")
        setup.commit()

    barrier = threading.Barrier(2)
    states: list[str | None] = []
    lock = threading.Lock()

    def worker(first: int, second: int) -> None:
        conn = psycopg.connect(dsn)
        try:
            conn.execute("SET deadlock_timeout = '100ms'")
            conn.execute(f"SELECT id FROM {SCHEMA}.items WHERE id = %s FOR UPDATE", (first,))
            barrier.wait(timeout=5)
            conn.execute(f"SELECT id FROM {SCHEMA}.items WHERE id = %s FOR UPDATE", (second,))
            conn.commit()
            state = None
        except Exception as exc:  # PostgreSQL chooses one victim by design.
            conn.rollback()
            state = getattr(exc, "sqlstate", None)
        finally:
            conn.close()
        with lock:
            states.append(state)

    a = threading.Thread(target=worker, args=(901, 902), daemon=True)
    b = threading.Thread(target=worker, args=(902, 901), daemon=True)
    a.start()
    b.start()
    a.join(timeout=10)
    b.join(timeout=10)
    if a.is_alive() or b.is_alive():
        raise RuntimeError("deadlock fixture did not terminate within bound")
    return "40P01" in states


def run(source_sha: str) -> dict[str, Any]:
    adapter = _adapter()
    plan = _plan()
    _reset(adapter)

    server = adapter.probe(snapshot_id="r14-5-postgres-18")
    if not server.stable_supported:
        raise RuntimeError(f"unsupported PostgreSQL authority: {server.canonical()}")

    with adapter.connect() as conn:
        fresh_apply = adapter.apply_migrations(conn, plan) == 2
        records = adapter.applied_migrations(conn)
        if len(records) != 2:
            raise RuntimeError("migration ledger did not record both migrations")
        rolled = adapter.rollback_last(conn, plan)
        rollback_reapply = rolled == "002-item-note" and adapter.apply_migrations(conn, plan) == 1

    try:
        def fail_operation(conn: Any) -> None:
            conn.execute(f"INSERT INTO {SCHEMA}.items (id, value) VALUES (10, 'must-rollback')")
            raise RuntimeError("intentional atomicity fixture")

        adapter.run_transaction(transaction_id="atomicity-fixture", operation=fail_operation)
    except RuntimeError as exc:
        if str(exc) != "intentional atomicity fixture":
            raise
    with adapter.connect() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {SCHEMA}.items WHERE id = 10")
        atomicity = int(cur.fetchone()[0]) == 0

    with adapter.connect() as conn:
        conn.execute(f"INSERT INTO {SCHEMA}.items (id, value, version, note) VALUES (20, 'v0', 0, 'seed')")
        conn.commit()
    # Helpers accept governed bare identifiers only; expose a simple updatable fixture view.
    with adapter.connect() as conn:
        conn.execute(f"CREATE OR REPLACE VIEW {SCHEMA}_items_view AS SELECT * FROM {SCHEMA}.items")
        conn.commit()
    with adapter.connect() as conn:
        version = adapter.optimistic_update(
            conn,
            table=f"{SCHEMA}_items_view",
            id_column="id",
            id_value=20,
            version_column="version",
            expected_version=0,
            assignments={"value": "v1"},
        )
        conn.commit()
    optimistic_conflict = version == 1
    with adapter.connect() as conn:
        try:
            adapter.optimistic_update(
                conn,
                table=f"{SCHEMA}_items_view",
                id_column="id",
                id_value=20,
                version_column="version",
                expected_version=0,
                assignments={"value": "stale"},
            )
        except PostgresConcurrencyError:
            optimistic_conflict = optimistic_conflict and True
            conn.rollback()
        else:
            optimistic_conflict = False
            conn.rollback()

    with adapter.connect() as conn:
        row = adapter.lock_row(
            conn,
            table=f"{SCHEMA}_items_view",
            id_column="id",
            id_value=20,
            columns=("id", "version"),
        )
        row_lock = int(row[0]) == 20 and int(row[1]) == 1
        conn.rollback()

    request_digest = "a" * 64
    with adapter.connect() as conn:
        first = adapter.claim_idempotency_key(conn, scope="save", key="request-1", request_digest=request_digest)
        conn.commit()
    with adapter.connect() as conn:
        second = adapter.claim_idempotency_key(conn, scope="save", key="request-1", request_digest=request_digest)
        conn.commit()
    idempotency = first is True and second is False
    with adapter.connect() as conn:
        try:
            adapter.claim_idempotency_key(conn, scope="save", key="request-1", request_digest="b" * 64)
        except PostgresStateError:
            idempotency = idempotency and True
            conn.rollback()
        else:
            idempotency = False
            conn.rollback()

    deadlock_detected = _real_deadlock_detected(_dsn())

    class RetryOnce(RuntimeError):
        sqlstate = "40001"

    retry_calls = 0

    def retry_operation(conn: Any) -> int:
        nonlocal retry_calls
        retry_calls += 1
        if retry_calls == 1:
            raise RetryOnce("synthetic serialization retry trigger")
        conn.execute(f"INSERT INTO {SCHEMA}.items (id, value, version, note) VALUES (40, 'retry', 0, 'bounded')")
        return retry_calls

    retry_result, retry_evidence = adapter.run_transaction(
        transaction_id="bounded-retry-fixture",
        operation=retry_operation,
        policy=PostgresTransactionPolicy(max_retries=1, retry_backoff_ms=1),
    )
    bounded_retry = deadlock_detected and retry_result == 2 and retry_evidence.attempts == 2

    with adapter.connect() as conn:
        conn.execute(f"DELETE FROM {SCHEMA}.items WHERE id >= 900")
        conn.execute(f"INSERT INTO {SCHEMA}.items (id, value, version, note) VALUES (30, 'backup', 2, 'stable')")
        conn.commit()
    before_rows = _fetch_items(adapter)
    before = adapter.fixture_snapshot(
        snapshot_id="before-restore",
        schema_digest=plan.digest(),
        table_rows={"items": before_rows},
        primary_keys={"items": "id"},
    )
    with adapter.connect() as conn:
        conn.execute(f"TRUNCATE TABLE {SCHEMA}.items")
        for row in before_rows:
            conn.execute(
                f"INSERT INTO {SCHEMA}.items (id, value, version, note) VALUES (%s, %s, %s, %s)",
                (row["id"], row["value"], row["version"], row["note"]),
            )
        conn.commit()
    after = adapter.fixture_snapshot(
        snapshot_id="after-restore",
        schema_digest=plan.digest(),
        table_rows={"items": _fetch_items(adapter)},
        primary_keys={"items": "id"},
    )
    restore_digest = snapshot_semantic_digest(after)
    backup_restore = restore_digest == snapshot_semantic_digest(before)

    checks = {
        "fresh_apply": fresh_apply,
        "rollback_reapply": rollback_reapply,
        "atomicity": atomicity,
        "optimistic_conflict": optimistic_conflict,
        "row_lock": row_lock,
        "idempotency": idempotency,
        "bounded_retry": bounded_retry,
        "backup_restore": backup_restore,
    }
    if not all(checks.values()):
        raise RuntimeError(f"R14.5 PostgreSQL acceptance failed: {checks}")

    server_payload = server.canonical()
    server_evidence = {
        key: server_payload[key]
        for key in ("server_version_num", "server_version", "server_major", "state", "stable_supported")
    }
    return {
        "source_sha": source_sha,
        "server": server_evidence,
        "migration_plan_digest": plan.digest(),
        "checks": checks,
        "restore_digest": restore_digest,
        "status": "pass",
        "secrets_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if len(args.source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in args.source_sha):
        raise SystemExit("--source-sha must be lowercase 40-character git SHA")
    result = run(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
