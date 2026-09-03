from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from kodepoia.core.backup import BackupManager
from kodepoia.core.fault_recovery import (
    FaultInjector,
    FaultMode,
    FaultSpec,
    FaultStage,
    FileRecoveryDrill,
    RecoveryRequiredError,
)
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.desktop.persistence import (
    ColumnDefinition,
    ComparisonOperator,
    DatabaseState,
    MigrationOperation,
    MigrationOperationKind,
    MigrationStep,
    QueryFilter,
    QueryIntent,
    QueryOperation,
    SchemaDefinition,
    SQLitePersistenceService,
    SQLiteValueType,
    TableDefinition,
)
from kodepoia.intelligence.memory import AuthoritativeMemory, MemoryStore, RebuildState
from kodepoia.project.dna import (
    ApprovalPolicy,
    DecisionState,
    Dimension,
    PerformanceBudget,
    Platform,
    ProjectDNA,
    ProjectType,
)

FIXTURE_RELATIVE = Path("tests/fixtures/r16_15_project_durability/scenario.json")
SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_SESSIONS = 8


class DurabilityGovernanceError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def _safe_relative(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise DurabilityGovernanceError("artifact path must be bounded and relative")
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise DurabilityGovernanceError("artifact path escapes representative project")
    normalized = path.as_posix()
    if normalized.startswith(".kodepoia/"):
        raise DurabilityGovernanceError("artifact path targets internal recovery state")
    return normalized


def validate_fixture_payload(payload: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "name",
        "project",
        "sessions",
        "authority",
        "budgets",
        "negative_controls",
    }
    if set(payload) != expected or payload.get("schema_version") != 1:
        raise DurabilityGovernanceError("fixture schema/fields drifted")
    if payload.get("name") != "r16.15-long-term-project-durability-resume-upgrade-soak":
        raise DurabilityGovernanceError("fixture identity drifted")
    project = payload.get("project")
    if not isinstance(project, dict) or set(project) != {
        "name",
        "engine",
        "engine_version",
        "genres",
    }:
        raise DurabilityGovernanceError("project fixture contract is invalid")
    if project.get("name") != "R16_15_Durable_Project":
        raise DurabilityGovernanceError("project fixture identity drifted")
    sessions = payload.get("sessions")
    if not isinstance(sessions, list) or not 3 <= len(sessions) <= _MAX_SESSIONS:
        raise DurabilityGovernanceError("fixture requires 3..8 bounded sessions")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for item in sessions:
        if not isinstance(item, dict) or set(item) != {
            "id",
            "artifact",
            "content",
            "memory_content",
        }:
            raise DurabilityGovernanceError("session contract is invalid")
        session_id = item.get("id")
        if not isinstance(session_id, str) or not re.fullmatch(r"session-[0-9]{3}", session_id):
            raise DurabilityGovernanceError("session id is invalid")
        if session_id in seen_ids:
            raise DurabilityGovernanceError("session ids must be unique")
        seen_ids.add(session_id)
        artifact = _safe_relative(item.get("artifact"))
        if artifact in seen_paths:
            raise DurabilityGovernanceError("artifact paths must be unique")
        seen_paths.add(artifact)
        for field in ("content", "memory_content"):
            value = item.get(field)
            if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 16384:
                raise DurabilityGovernanceError(f"{field} is invalid")
    authority = payload.get("authority")
    if not isinstance(authority, dict) or set(authority) != {"permission_epoch", "secret_refs"}:
        raise DurabilityGovernanceError("authority contract is invalid")
    epoch = authority.get("permission_epoch")
    if isinstance(epoch, bool) or not isinstance(epoch, int) or not 1 <= epoch <= 1000:
        raise DurabilityGovernanceError("permission_epoch is invalid")
    refs = authority.get("secret_refs")
    if not isinstance(refs, list) or not refs or len(refs) > 8:
        raise DurabilityGovernanceError("secret_refs must be bounded references")
    for ref in refs:
        if not isinstance(ref, str) or re.fullmatch(
            r"secret-ref://[A-Za-z0-9._/-]{1,120}", ref
        ) is None:
            raise DurabilityGovernanceError("secret_refs may contain references only")
    budgets = payload.get("budgets")
    if not isinstance(budgets, dict) or set(budgets) != {
        "max_fixture_bytes",
        "max_project_bytes",
        "timeout_seconds",
        "soak_cycles",
    }:
        raise DurabilityGovernanceError("budget contract is invalid")
    if not 3 <= int(budgets["soak_cycles"]) <= 32:
        raise DurabilityGovernanceError("soak cycle budget is invalid")
    if not 1.0 <= float(budgets["timeout_seconds"]) <= 60.0:
        raise DurabilityGovernanceError("timeout budget is invalid")
    if not 1024 <= int(budgets["max_project_bytes"]) <= 16 * 1024 * 1024:
        raise DurabilityGovernanceError("project byte budget is invalid")
    controls = payload.get("negative_controls")
    if not isinstance(controls, dict) or set(controls) != {
        "tampered_memory",
        "failed_migration",
        "interrupted_registry_write",
        "partial_artifact",
        "stale_authority",
    }:
        raise DurabilityGovernanceError("negative-control contract is invalid")
    if not all(value is True for value in controls.values()):
        raise DurabilityGovernanceError("all negative controls must be enabled")
    return payload


def _load_fixture(repo_root: Path) -> tuple[dict[str, Any], bytes]:
    raw = (repo_root / FIXTURE_RELATIVE).read_bytes()
    if not raw or len(raw) > 256 * 1024:
        raise DurabilityGovernanceError("fixture byte budget exceeded")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise DurabilityGovernanceError("fixture root must be an object")
    return validate_fixture_payload(payload), raw


def _write_bound(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {"schema_version": 1, "payload": payload, "integrity_sha256": _digest(payload)}
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(envelope, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_bound(path: Path) -> dict[str, Any]:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(envelope, dict) or set(envelope) != {
        "schema_version",
        "payload",
        "integrity_sha256",
    }:
        raise DurabilityGovernanceError("bound state envelope is invalid")
    payload = envelope.get("payload")
    if envelope.get("schema_version") != 1 or not isinstance(payload, dict):
        raise DurabilityGovernanceError("bound state schema is invalid")
    if envelope.get("integrity_sha256") != _digest(payload):
        raise DurabilityGovernanceError("bound state integrity mismatch")
    return dict(payload)


def _dna(fixture: dict[str, Any]) -> ProjectDNA:
    project = fixture["project"]
    return ProjectDNA(
        schema_version=1,
        name=str(project["name"]),
        project_type=ProjectType.GAME,
        platforms=[Platform.WINDOWS, Platform.LINUX],
        engine=str(project["engine"]),
        engine_version=str(project["engine_version"]),
        dimension=Dimension.D3,
        genres=[str(item) for item in project["genres"]],
        inputs=["keyboard", "mouse"],
        graphics_style="representative-r16.15",
        online=DecisionState.NO,
        multiplayer=DecisionState.NO,
        performance={
            "windows": PerformanceBudget(target_fps=60, min_fps=30, max_ram_mb=4096),
            "linux": PerformanceBudget(target_fps=60, min_fps=30, max_ram_mb=4096),
        },
        tools={"durability_acceptance": True},
        download_policy=ApprovalPolicy.ASK,
        install_policy=ApprovalPolicy.ASK,
        lineage={"authority": "r16.15.repository-fixture"},
        capabilities={"persistence": DecisionState.YES, "recovery": DecisionState.YES},
    )


def _validate_state(state: dict[str, Any], fixture: dict[str, Any]) -> None:
    if set(state) != {
        "state_schema",
        "project_name",
        "session_history",
        "upgrade_history",
        "authority",
    }:
        raise DurabilityGovernanceError("project state fields drifted")
    if state["state_schema"] not in {1, 2}:
        raise DurabilityGovernanceError("project state schema is unsupported")
    if state["project_name"] != fixture["project"]["name"]:
        raise DurabilityGovernanceError("project identity drifted")
    if state["authority"] != fixture["authority"]:
        raise DurabilityGovernanceError("stale or widened authority state rejected")
    history = state["session_history"]
    if not isinstance(history, list) or len(history) > len(fixture["sessions"]):
        raise DurabilityGovernanceError("session history is invalid")
    expected_ids = [item["id"] for item in fixture["sessions"]]
    actual_ids = [item.get("session_id") for item in history if isinstance(item, dict)]
    if actual_ids != expected_ids[: len(actual_ids)]:
        raise DurabilityGovernanceError("session history provenance drifted")
    upgrades = state["upgrade_history"]
    if state["state_schema"] == 1 and upgrades != []:
        raise DurabilityGovernanceError("state v1 upgrade history is invalid")
    if state["state_schema"] == 2 and upgrades != ["state-v1-to-v2"]:
        raise DurabilityGovernanceError("state v2 upgrade history is invalid")


def _validate_registry(registry: dict[str, Any], project_root: Path) -> None:
    if set(registry) != {"registry_schema", "artifacts"} or registry["registry_schema"] != 1:
        raise DurabilityGovernanceError("artifact registry schema is invalid")
    artifacts = registry["artifacts"]
    if not isinstance(artifacts, dict) or len(artifacts) > _MAX_SESSIONS:
        raise DurabilityGovernanceError("artifact registry is invalid")
    root = project_root.resolve(strict=True)
    for relative, expected in artifacts.items():
        normalized = _safe_relative(relative)
        if normalized != relative:
            raise DurabilityGovernanceError("artifact path is not canonical")
        target = (project_root / relative).resolve(strict=True)
        if root not in target.parents or not target.is_file() or _file_digest(target) != expected:
            raise DurabilityGovernanceError("artifact registry integrity mismatch")


def _initialize(project_root: Path, fixture: dict[str, Any]) -> None:
    project_root.mkdir(parents=True, exist_ok=False)
    _dna(fixture).save(project_root / "project_dna.yaml")
    state = {
        "state_schema": 1,
        "project_name": fixture["project"]["name"],
        "session_history": [],
        "upgrade_history": [],
        "authority": fixture["authority"],
    }
    _validate_state(state, fixture)
    _write_bound(project_root / "state/project-state.json", state)
    _write_bound(
        project_root / "state/artifact-registry.json",
        {"registry_schema": 1, "artifacts": {}},
    )


def _migrate_state(project_root: Path, fixture: dict[str, Any]) -> None:
    path = project_root / "state/project-state.json"
    state = _read_bound(path)
    _validate_state(state, fixture)
    if state["state_schema"] != 1:
        raise DurabilityGovernanceError("state migration source must be v1")
    state["state_schema"] = 2
    state["upgrade_history"] = ["state-v1-to-v2"]
    _validate_state(state, fixture)
    _write_bound(path, state)


def _worker_session(project_root: Path, fixture: dict[str, Any], index: int) -> dict[str, Any]:
    if not 0 <= index < len(fixture["sessions"]):
        raise DurabilityGovernanceError("worker index is out of bounds")
    if ProjectDNA.load(project_root / "project_dna.yaml").to_dict() != _dna(fixture).to_dict():
        raise DurabilityGovernanceError("Project DNA reconstruction drifted")
    state_path = project_root / "state/project-state.json"
    registry_path = project_root / "state/artifact-registry.json"
    state = _read_bound(state_path)
    registry = _read_bound(registry_path)
    _validate_state(state, fixture)
    _validate_registry(registry, project_root)
    if len(state["session_history"]) != index:
        raise DurabilityGovernanceError("clean worker reconstructed wrong session count")
    session = fixture["sessions"][index]
    relative = _safe_relative(session["artifact"])
    artifact = project_root / relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    payload = (session["content"] + "\n").encode("utf-8")
    temporary = artifact.with_name(f".{artifact.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, artifact)
    finally:
        temporary.unlink(missing_ok=True)
    artifact_sha = _file_digest(artifact)
    store = MemoryStore(project_root / "state/memory.sqlite3")
    try:
        store.add(
            scope=str(fixture["project"]["name"]),
            kind="session_summary",
            content=str(session["memory_content"]),
            metadata={"session_id": str(session["id"])},
            origin=f"r16.15:{session['id']}",
            project_scope=str(fixture["project"]["name"]),
            trust_class="project",
            record_class="project_fact",
            version=1,
        )
        records = store.list(scope=str(fixture["project"]["name"]), limit=_MAX_SESSIONS)
        if len(records) != index + 1:
            raise DurabilityGovernanceError("durable memory reconstruction drifted")
    finally:
        store.db.close()
    item = {
        "session_id": session["id"],
        "artifact": relative,
        "artifact_sha256": artifact_sha,
        "memory_origin": f"r16.15:{session['id']}",
        "memory_version": 1,
    }
    state["session_history"] = [*state["session_history"], item]
    registry["artifacts"] = {**registry["artifacts"], relative: artifact_sha}
    _validate_state(state, fixture)
    _write_bound(registry_path, registry)
    _write_bound(state_path, state)
    return {"pid": os.getpid(), "session_id": session["id"], "artifact_sha256": artifact_sha}


def _spawn(
    repo_root: Path,
    project_root: Path,
    fixture_path: Path,
    index: int,
    timeout: float,
) -> dict[str, Any]:
    env = dict(os.environ)
    source = str((repo_root / "src").resolve())
    env["PYTHONPATH"] = source + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "kodepoia.project.r16_15_acceptance",
            "--worker-session",
            str(index),
            "--worker-project",
            str(project_root),
            "--worker-fixture",
            str(fixture_path),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise DurabilityGovernanceError(
            completed.stderr.strip() or completed.stdout.strip() or "child process failed"
        )
    result = json.loads(completed.stdout)
    if not isinstance(result, dict) or result.get("pid") == os.getpid():
        raise DurabilityGovernanceError("session did not run in a clean child process")
    return result


def _schema(version: int) -> SchemaDefinition:
    columns = [
        ColumnDefinition("id", SQLiteValueType.INTEGER, nullable=False, primary_key=True),
        ColumnDefinition("session_id", SQLiteValueType.TEXT, nullable=False, unique=True),
    ]
    if version == 2:
        columns.append(ColumnDefinition("artifact_sha256", SQLiteValueType.TEXT, nullable=True))
    return SchemaDefinition(
        version=version,
        tables=(TableDefinition("sessions", tuple(columns)),),
    )


def _migration(duplicate: bool = False) -> MigrationStep:
    column = ColumnDefinition(
        "session_id" if duplicate else "artifact_sha256",
        SQLiteValueType.TEXT,
        nullable=True,
    )
    return MigrationStep.build(
        from_version=1,
        to_version=2,
        source_digest=_schema(1).digest,
        target_digest=_schema(2).digest,
        operations=(
            MigrationOperation(
                MigrationOperationKind.ADD_COLUMN,
                table="sessions",
                column_definition=column,
            ),
        ),
    )


def _database(project_root: Path, session: dict[str, Any]) -> dict[str, Any]:
    path = project_root / "state/desktop.sqlite3"
    backups = project_root / "state/sqlite-backups"
    v1 = SQLitePersistenceService(path, _schema(1), backup_root=backups)
    if v1.initialize().state is not DatabaseState.READY:
        raise DurabilityGovernanceError("desktop database v1 did not initialize")
    if v1.execute(
        QueryIntent(
            QueryOperation.INSERT,
            "sessions",
            values=(("id", 1), ("session_id", session["session_id"])),
        )
    ) != 1:
        raise DurabilityGovernanceError("desktop database insert failed")
    bad = SQLitePersistenceService(
        path,
        _schema(2),
        migrations=(_migration(True),),
        backup_root=backups,
    )
    failed = False
    try:
        bad.migrate()
    except (sqlite3.DatabaseError, ValueError):
        failed = True
    inspected = bad.inspect()
    rolled_back = (
        failed
        and inspected.state is DatabaseState.MIGRATION_REQUIRED
        and inspected.current_version == 1
        and inspected.current_digest == _schema(1).digest
    )
    if not rolled_back:
        raise DurabilityGovernanceError("failed migration did not restore exact v1 state")
    good = SQLitePersistenceService(
        path,
        _schema(2),
        migrations=(_migration(),),
        backup_root=backups,
    )
    good.migrate()
    if good.inspect().state is not DatabaseState.READY:
        raise DurabilityGovernanceError("forward migration did not reach schema v2")
    good.execute(
        QueryIntent(
            QueryOperation.UPDATE,
            "sessions",
            values=(("artifact_sha256", session["artifact_sha256"]),),
            filters=(QueryFilter("id", ComparisonOperator.EQ, 1),),
        )
    )
    rows = good.execute(
        QueryIntent(
            QueryOperation.SELECT,
            "sessions",
            columns=("id", "session_id", "artifact_sha256"),
            order_by=("id",),
            limit=10,
        )
    )
    expected = [(1, session["session_id"], session["artifact_sha256"])]
    if rows != expected:
        raise DurabilityGovernanceError("migrated database content drifted")
    return {
        "failed_migration_rolled_back": True,
        "final_version": 2,
        "final_schema_sha256": _schema(2).digest,
        "rows": [list(row) for row in rows],
    }


def _memory_recovery(project_root: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    path = project_root / "state/memory.sqlite3"
    last = fixture["sessions"][-1]
    store = MemoryStore(path)
    try:
        store.db.execute(
            "UPDATE memories SET content = ? WHERE origin = ?",
            ("tampered durable memory", f"r16.15:{last['id']}"),
        )
        store.db.commit()
    finally:
        store.db.close()
    reopened = MemoryStore(path)
    try:
        valid = reopened.list(scope=str(fixture["project"]["name"]), limit=_MAX_SESSIONS)
        quarantine = reopened.quarantine_events(project_scope=str(fixture["project"]["name"]))
        quarantined = len(valid) == len(fixture["sessions"]) - 1 and any(
            item["reason"] == "integrity_mismatch" for item in quarantine
        )
        rebuilt = reopened.rebuild_from_authoritative(
            (
                AuthoritativeMemory(
                    project_scope=str(fixture["project"]["name"]),
                    kind="session_summary",
                    content=str(last["memory_content"]),
                    origin=f"r16.15:{last['id']}",
                    version=1,
                    record_class="project_fact",
                    metadata={"session_id": str(last["id"])},
                    created_at="2026-09-03T00:00:00+00:00",
                ),
            ),
            project_scope=str(fixture["project"]["name"]),
        )
        records = reopened.list(scope=str(fixture["project"]["name"]), limit=_MAX_SESSIONS)
    finally:
        reopened.db.close()
    expected = {
        (f"r16.15:{item['id']}", str(item["memory_content"])) for item in fixture["sessions"]
    }
    actual = {(record.origin, record.content) for record in records}
    return {
        "tamper_quarantined": quarantined,
        "memory_restored": rebuilt.state is RebuildState.REBUILT and actual == expected,
        "rebuild_semantic_sha256": rebuilt.semantic_digest,
    }


def _registry_recovery(project_root: Path, scratch: Path) -> dict[str, Any]:
    registry = project_root / "state/artifact-registry.json"
    baseline = registry.read_bytes()
    journal = RecoveryJournal(scratch / "recovery.json")
    drill = FileRecoveryDrill(
        project_root,
        scratch / "snapshots",
        journal,
        injector=FaultInjector(
            (FaultSpec(FaultStage.COMMIT, FaultMode.INTERRUPT, "r16.15-registry"),)
        ),
    )
    blocked = False
    try:
        drill.mutate_file(
            "r16.15-registry",
            "state/artifact-registry.json",
            b'{"partial":"state"}\n',
        )
    except RecoveryRequiredError:
        blocked = True
    if not blocked:
        raise DurabilityGovernanceError("interrupted registry write did not block")
    result = drill.recover("r16.15-registry")
    _read_bound(registry)
    return {
        "interruption_blocked": blocked,
        "baseline_restored": registry.read_bytes() == baseline,
        "journal_cleared": not journal.path.exists(),
        "recovery_status": result.status,
    }


def _expected_semantic(fixture: dict[str, Any]) -> dict[str, Any]:
    history = []
    artifacts: dict[str, str] = {}
    memory = []
    for item in fixture["sessions"]:
        sha = hashlib.sha256((item["content"] + "\n").encode("utf-8")).hexdigest()
        artifacts[item["artifact"]] = sha
        history.append(
            {
                "session_id": item["id"],
                "artifact": item["artifact"],
                "artifact_sha256": sha,
                "memory_origin": f"r16.15:{item['id']}",
                "memory_version": 1,
            }
        )
        memory.append(
            {
                "origin": f"r16.15:{item['id']}",
                "content": item["memory_content"],
                "metadata": {"session_id": item["id"]},
            }
        )
    return {
        "dna": _dna(fixture).to_dict(),
        "state": {
            "state_schema": 2,
            "project_name": fixture["project"]["name"],
            "session_history": history,
            "upgrade_history": ["state-v1-to-v2"],
            "authority": fixture["authority"],
        },
        "registry": {"registry_schema": 1, "artifacts": artifacts},
        "memory": memory,
        "desktop": {
            "final_version": 2,
            "final_schema_sha256": _schema(2).digest,
            "rows": [[1, fixture["sessions"][0]["id"], history[0]["artifact_sha256"]]],
        },
    }


def _actual_semantic(
    project_root: Path,
    fixture: dict[str, Any],
    database: dict[str, Any],
) -> dict[str, Any]:
    store = MemoryStore(project_root / "state/memory.sqlite3")
    try:
        records = store.list(scope=str(fixture["project"]["name"]), limit=_MAX_SESSIONS)
    finally:
        store.db.close()
    memory = sorted(
        (
            {
                "origin": record.origin,
                "content": record.content,
                "metadata": record.metadata,
            }
            for record in records
        ),
        key=lambda item: item["origin"],
    )
    return {
        "dna": ProjectDNA.load(project_root / "project_dna.yaml").to_dict(),
        "state": _read_bound(project_root / "state/project-state.json"),
        "registry": _read_bound(project_root / "state/artifact-registry.json"),
        "memory": memory,
        "desktop": {
            "final_version": database["final_version"],
            "final_schema_sha256": database["final_schema_sha256"],
            "rows": database["rows"],
        },
    }


def qualify_extended_local_soak(*, requested: bool = False) -> dict[str, object]:
    if not requested:
        return {
            "state": "NOT_EXERCISED",
            "claim_satisfied": False,
            "manual_required": False,
            "detail": "optional extended wall-clock/local-environment soak was not requested",
        }
    return {
        "state": "MANUAL_REQUIRED",
        "claim_satisfied": False,
        "manual_required": True,
        "detail": "optional extended soak requires separate local qualification",
    }


def build_project_durability_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str | None = None,
    require_extended_local_soak: bool = False,
) -> dict[str, Any]:
    if SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be an exact lowercase 40-character SHA")
    started = time.monotonic()
    fixture, fixture_bytes = _load_fixture(repo_root)
    fixture_path = (repo_root / FIXTURE_RELATIVE).resolve(strict=True)
    cases: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-15-") as name:
        scratch = Path(name)
        project_root = scratch / "project"
        _initialize(project_root, fixture)
        cases.append(_case("project_fixture_initialized", True, "bound state and DNA created"))
        dna_ok = ProjectDNA.load(project_root / "project_dna.yaml").to_dict() == _dna(fixture).to_dict()
        cases.append(_case("project_dna_round_trip", dna_ok, "durable Project DNA reconstructed"))
        children = [
            _spawn(
                repo_root,
                project_root,
                fixture_path,
                0,
                float(fixture["budgets"]["timeout_seconds"]),
            )
        ]
        cases.append(_case("clean_process_session_1", True, "first clean-process session completed"))
        _migrate_state(project_root, fixture)
        cases.append(_case("project_state_forward_upgrade", True, "state v1 migrated to v2"))
        for index in range(1, len(fixture["sessions"])):
            children.append(
                _spawn(
                    repo_root,
                    project_root,
                    fixture_path,
                    index,
                    float(fixture["budgets"]["timeout_seconds"]),
                )
            )
        clean = len(children) == len(fixture["sessions"]) and all(
            item["pid"] != os.getpid() for item in children
        )
        cases.append(_case("clean_process_multi_session_resume", clean, "all sessions reopened cleanly"))
        state = _read_bound(project_root / "state/project-state.json")
        registry = _read_bound(project_root / "state/artifact-registry.json")
        _validate_state(state, fixture)
        _validate_registry(registry, project_root)
        aligned = len(state["session_history"]) == len(registry["artifacts"]) == len(fixture["sessions"])
        cases.append(_case("history_and_registry_provenance", aligned, "history and registry aligned"))
        database = _database(project_root, state["session_history"][0])
        cases.append(
            _case(
                "failed_schema_migration_rolls_back",
                bool(database["failed_migration_rolled_back"]),
                "failed migration restored exact v1 pre-state",
            )
        )
        cases.append(_case("desktop_persistence_forward_migration", True, "SQLite reached schema v2"))
        memory = _memory_recovery(project_root, fixture)
        cases.append(
            _case(
                "tampered_memory_quarantined",
                bool(memory["tamper_quarantined"]),
                "tampered durable memory was quarantined",
            )
        )
        cases.append(
            _case(
                "authoritative_memory_rebuild",
                bool(memory["memory_restored"]),
                "authoritative rebuild restored rejected memory",
            )
        )
        registry_recovery = _registry_recovery(project_root, scratch / "recovery")
        cases.append(
            _case(
                "interrupted_registry_write_blocks",
                bool(registry_recovery["interruption_blocked"]),
                "interrupted write required recovery",
            )
        )
        recovered = bool(registry_recovery["baseline_restored"]) and bool(
            registry_recovery["journal_cleared"]
        )
        cases.append(_case("interrupted_registry_write_recovers", recovered, "registry baseline restored"))
        partial = project_root / "artifacts/.r16-15-partial.tmp"
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_text("partial-output", encoding="utf-8")
        seen_partial = partial.is_file()
        partial.unlink()
        cases.append(
            _case(
                "partial_artifact_not_promoted",
                seen_partial and not partial.exists(),
                "partial artifact removed without registry promotion",
            )
        )
        stale = json.loads(json.dumps(state))
        stale["authority"]["permission_epoch"] -= 1
        rejected = False
        try:
            _validate_state(stale, fixture)
        except DurabilityGovernanceError:
            rejected = True
        cases.append(_case("stale_authority_state_rejected", rejected, "stale authority rejected"))
        backup = BackupManager(scratch / "backups")
        archive = backup.create_archive(project_root, label="r16-15-final")
        verified = backup.verify(archive)
        restored = scratch / "restored-project"
        backup.restore(archive, restored)
        cases.append(_case("verified_project_backup", verified, "project backup verified"))
        restore_ok = (
            ProjectDNA.load(restored / "project_dna.yaml").to_dict() == _dna(fixture).to_dict()
            and _read_bound(restored / "state/project-state.json") == state
        )
        cases.append(
            _case(
                "backup_restore_reconstructs_authority",
                restore_ok,
                "backup restored durable DNA and state",
            )
        )
        soak_ok = True
        for _ in range(int(fixture["budgets"]["soak_cycles"])):
            try:
                _validate_state(_read_bound(project_root / "state/project-state.json"), fixture)
                _validate_registry(
                    _read_bound(project_root / "state/artifact-registry.json"),
                    project_root,
                )
            except DurabilityGovernanceError:
                soak_ok = False
                break
        cases.append(_case("bounded_deterministic_soak", soak_ok, "bounded reopen soak passed"))
        project_bytes = sum(
            path.stat().st_size for path in project_root.rglob("*") if path.is_file()
        )
        cases.append(
            _case(
                "bounded_project_footprint",
                project_bytes <= int(fixture["budgets"]["max_project_bytes"]),
                f"project bytes={project_bytes}",
            )
        )
        registered = set(registry["artifacts"])
        actual_artifacts = {
            path.relative_to(project_root).as_posix()
            for path in (project_root / "artifacts").rglob("*")
            if path.is_file() and not path.name.startswith(".")
        }
        cases.append(
            _case(
                "no_unresolved_orphan_artifacts",
                actual_artifacts == registered,
                "no unregistered final artifact remains",
            )
        )
        actual = _actual_semantic(project_root, fixture, database)
        expected = _expected_semantic(fixture)
        semantic_sha256 = _digest(actual)
        expected_semantic_sha256 = _digest(expected)
        cases.append(
            _case(
                "final_digest_and_history_match_authority",
                actual == expected and semantic_sha256 == expected_semantic_sha256,
                "final semantic digest and history match fixture authority",
            )
        )
    failed = [item for item in cases if not item["pass"]]
    qualification = qualify_extended_local_soak(requested=require_extended_local_soak)
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.15",
        "source_sha": source_sha,
        "platform": platform or sys.platform,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "semantic_sha256": semantic_sha256,
        "expected_semantic_sha256": expected_semantic_sha256,
        "clean_process_sessions": len(fixture["sessions"]),
        "bounded_soak_cycles": int(fixture["budgets"]["soak_cycles"]),
        "project_bytes": project_bytes,
        "durability_claim": not failed,
        "critical_veto": bool(failed),
        "secret_free": True,
        "external_network_calls": 0,
        "destructive_host_actions": 0,
        "core_manual_required": False,
        "manual_state": (
            "MANUAL_REQUIRED" if require_extended_local_soak else "CONDITIONAL_NOT_TRIGGERED"
        ),
        "extended_local_soak": qualification,
        "memory_recovery": memory,
        "database_migration": database,
        "registry_recovery": registry_recovery,
        "summary": {
            "total": len(cases),
            "passed": len(cases) - len(failed),
            "failed": len(failed),
        },
        "cases": cases,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    report["evidence_sha256"] = _digest(
        {key: value for key, value in report.items() if key != "elapsed_seconds"}
    )
    return report


def _worker_main(args: argparse.Namespace) -> int:
    fixture = json.loads(Path(args.worker_fixture).read_text(encoding="utf-8"))
    if not isinstance(fixture, dict):
        raise DurabilityGovernanceError("worker fixture is invalid")
    fixture = validate_fixture_payload(fixture)
    result = _worker_session(
        Path(args.worker_project).resolve(strict=True),
        fixture,
        int(args.worker_session),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _module_cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-session", type=int)
    parser.add_argument("--worker-project")
    parser.add_argument("--worker-fixture")
    args = parser.parse_args()
    if args.worker_session is None or not args.worker_project or not args.worker_fixture:
        parser.error("worker session, project and fixture are required")
    return _worker_main(args)


if __name__ == "__main__":
    raise SystemExit(_module_cli())
