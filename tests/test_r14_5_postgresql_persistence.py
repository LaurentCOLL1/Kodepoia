from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

import pytest

from kodepoia.backend.postgres import (
    PostgresCapabilityState,
    PostgresConcurrencyError,
    PostgresConnectionPolicy,
    PostgresFixtureSnapshot,
    PostgresIsolationLevel,
    PostgresMigration,
    PostgresMigrationPlan,
    PostgresPolicyError,
    PostgresSecretRef,
    PostgresStateError,
    PostgresTransactionEvidence,
    PostgresTransactionPolicy,
    capability_from_server_version,
    snapshot_semantic_digest,
    sql_sha256,
)


def _migration(sequence: int, name: str) -> PostgresMigration:
    return PostgresMigration(
        migration_id=f"m{sequence}-{name}",
        sequence=sequence,
        description=name,
        forward_sql=f"CREATE TABLE {name} (id bigint PRIMARY KEY);\n",
        rollback_sql=f"DROP TABLE {name};\n",
    )


def test_secret_ref_and_connection_policy_redact_real_secret() -> None:
    policy = PostgresConnectionPolicy(
        environment_id="test",
        dsn_ref=PostgresSecretRef("kode-secrets.pg-test"),
        application_name="kodepoia-r14",
    )
    payload = policy.canonical()
    assert payload["dsn_ref"] == {"secret_id": "kode-secrets.pg-test"}
    assert "postgresql://" not in repr(payload)
    assert len(policy.digest()) == 64


def test_connection_policy_rejects_unbounded_settings() -> None:
    with pytest.raises(PostgresPolicyError):
        PostgresConnectionPolicy(
            environment_id="test",
            dsn_ref=PostgresSecretRef("pg"),
            connect_timeout_s=0,
        )
    with pytest.raises(PostgresPolicyError):
        PostgresConnectionPolicy(
            environment_id="test",
            dsn_ref=PostgresSecretRef("pg"),
            max_connections=999,
        )


def test_sql_checksum_normalizes_line_endings() -> None:
    assert sql_sha256("SELECT 1;\r\n") == sql_sha256("SELECT 1;\n")
    assert sql_sha256("SELECT 1;\r") == sql_sha256("SELECT 1;\n")


def test_migration_checksum_is_derived_and_tampering_is_rejected() -> None:
    migration = _migration(1, "alpha")
    assert migration.checksum == hashlib.sha256(migration.forward_sql.encode()).hexdigest()
    with pytest.raises(PostgresPolicyError, match="checksum"):
        replace(migration, checksum="0" * 64)


def test_migration_plan_orders_and_requires_contiguous_unique_sequences() -> None:
    plan = PostgresMigrationPlan("schema-main", (_migration(2, "beta"), _migration(1, "alpha")))
    assert [item.sequence for item in plan.migrations] == [1, 2]
    assert len(plan.digest()) == 64
    with pytest.raises(PostgresPolicyError, match="contiguous"):
        PostgresMigrationPlan("schema-main", (_migration(2, "beta"),))
    with pytest.raises(PostgresPolicyError, match="unique"):
        PostgresMigrationPlan("schema-main", (_migration(1, "alpha"), _migration(1, "beta")))


def test_server_version_18_is_available_and_future_major_is_not_authoritative() -> None:
    stable = capability_from_server_version(
        snapshot_id="pg18",
        server_version_num=180006,
        server_version="PostgreSQL 18.6",
    )
    assert stable.server_major == 18
    assert stable.state is PostgresCapabilityState.AVAILABLE
    assert stable.stable_supported is True

    prerelease = capability_from_server_version(
        snapshot_id="pg19",
        server_version_num=190000,
        server_version="PostgreSQL 19beta3",
    )
    assert prerelease.state is PostgresCapabilityState.DEGRADED
    assert prerelease.stable_supported is False
    assert "not the accepted stable" in prerelease.blockers[0]


def test_old_server_is_explicitly_unsupported() -> None:
    snapshot = capability_from_server_version(
        snapshot_id="pg17",
        server_version_num=170011,
        server_version="PostgreSQL 17.11",
    )
    assert snapshot.state is PostgresCapabilityState.UNSUPPORTED
    assert snapshot.blockers


def test_transaction_policy_bounds_retry_and_exposes_isolation_sql() -> None:
    policy = PostgresTransactionPolicy(
        isolation=PostgresIsolationLevel.SERIALIZABLE,
        max_retries=3,
        retry_backoff_ms=10,
    )
    assert policy.isolation.sql == "SERIALIZABLE"
    with pytest.raises(PostgresPolicyError):
        PostgresTransactionPolicy(max_retries=9)


def test_transaction_evidence_is_canonical_and_never_contains_dsn() -> None:
    evidence = PostgresTransactionEvidence(
        transaction_id="tx-1",
        isolation=PostgresIsolationLevel.REPEATABLE_READ,
        attempts=2,
        committed=True,
    )
    assert evidence.canonical() == {
        "transaction_id": "tx-1",
        "isolation": "repeatable_read",
        "attempts": 2,
        "committed": True,
        "sqlstate": None,
    }


def test_fixture_snapshot_is_deterministic_and_hash_bound() -> None:
    schema_digest = "1" * 64
    first = PostgresFixtureSnapshot(
        snapshot_id="snap-a",
        schema_digest=schema_digest,
        tables={"items": ({"id": 1, "value": "a"}, {"id": 2, "value": "b"})},
    )
    second = PostgresFixtureSnapshot(
        snapshot_id="snap-b",
        schema_digest=schema_digest,
        tables={"items": ({"id": 1, "value": "a"}, {"id": 2, "value": "b"})},
    )
    assert first.payload_sha256 != second.payload_sha256
    assert snapshot_semantic_digest(first) == snapshot_semantic_digest(second)
    assert len(snapshot_semantic_digest(first)) == 64


def test_fixture_snapshot_rejects_payload_tampering() -> None:
    snapshot = PostgresFixtureSnapshot(
        snapshot_id="snap",
        schema_digest="2" * 64,
        tables={"items": ({"id": 1},)},
    )
    with pytest.raises(PostgresPolicyError, match="digest"):
        replace(snapshot, payload_sha256="0" * 64)


def test_concurrency_errors_are_state_errors() -> None:
    error = PostgresConcurrencyError("conflict")
    assert isinstance(error, PostgresStateError)


def test_migration_plan_serialization_excludes_sql_bodies() -> None:
    plan = PostgresMigrationPlan("schema", (_migration(1, "alpha"),))
    serialized = plan.canonical()
    assert "forward_sql" not in serialized["migrations"][0]
    assert "rollback_sql" not in serialized["migrations"][0]
    assert serialized["migrations"][0]["checksum"] == plan.migrations[0].checksum


def test_invalid_identifiers_are_rejected_before_sql_construction() -> None:
    with pytest.raises(PostgresPolicyError):
        PostgresSecretRef("../../password")
    with pytest.raises(PostgresPolicyError):
        PostgresConnectionPolicy(
            environment_id="prod;DROP TABLE x",
            dsn_ref=PostgresSecretRef("pg"),
        )


def test_evidence_models_reject_boolean_integer_confusion() -> None:
    with pytest.raises(PostgresPolicyError):
        PostgresTransactionEvidence(
            transaction_id="tx",
            isolation=PostgresIsolationLevel.READ_COMMITTED,
            attempts=True,  # type: ignore[arg-type]
            committed=False,
        )
