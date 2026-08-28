from __future__ import annotations

import json
import socket
import time
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.backend.contracts import BackendEnvironmentIdentity, BackendEnvironmentKind, BackendServiceKind
from kodepoia.backend.health import BackendHealthSnapshot, BackendHealthState
from kodepoia.backend.intent import BackendProjectProfile
from kodepoia.backend.local_config import (
    BackendConfigOverlay,
    BackendLocalConfig,
    BackendLogLevel,
    local_config_from_runtime_intents,
)
from kodepoia.backend.runtime import BackendLocalRuntime
from kodepoia.backend.scaffold import BackendScaffoldEngine
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "r14"


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _profile() -> BackendProjectProfile:
    return BackendProjectProfile(enabled=True, services=(BackendServiceKind.AUTH,))


def _config(*, port: int = 0, secret_refs=()) -> BackendLocalConfig:
    return local_config_from_runtime_intents(
        "r14_3_fixture",
        _profile().runtime_intents(),
        port=port,
        secret_refs=tuple(secret_refs),
    )


def test_r14_2_runtime_intents_bridge_to_deterministic_local_config() -> None:
    first = _config()
    second = _config()
    assert first == second
    assert first.digest() == second.digest()
    assert first.services == (BackendServiceKind.AUTH,)
    assert first.host == "127.0.0.1"
    assert first.port == 0


def test_empty_runtime_intents_do_not_manufacture_backend_workspace() -> None:
    with pytest.raises(ValueError, match="at least one R14.2 runtime intent"):
        local_config_from_runtime_intents("offline", ())


def test_non_loopback_and_privileged_bind_are_rejected() -> None:
    environment = BackendEnvironmentIdentity("local", BackendEnvironmentKind.LOCAL)
    with pytest.raises(ValueError, match="loopback"):
        BackendLocalConfig("demo", environment, (BackendServiceKind.AUTH,), host="0.0.0.0")
    with pytest.raises(ValueError, match="port"):
        BackendLocalConfig("demo", environment, (BackendServiceKind.AUTH,), port=80)


def test_environment_overlay_is_typed_and_cannot_widen_host() -> None:
    base = _config()
    test_environment = BackendEnvironmentIdentity("test", BackendEnvironmentKind.TEST)
    overlaid = BackendConfigOverlay(
        environment=test_environment,
        port=23456,
        log_level=BackendLogLevel.DEBUG,
    ).apply(base)
    assert overlaid.environment.kind is BackendEnvironmentKind.TEST
    assert overlaid.port == 23456
    assert overlaid.host == "127.0.0.1"
    assert overlaid.services == base.services


def test_config_roundtrip_is_strict_and_secret_ref_only() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    secrets.store("kodepoia.backend.test", "fixture-token", "VERY-SECRET-R14-3-VALUE")
    ref = secrets.ref("kodepoia.backend.test", "fixture-token")
    config = _config(secret_refs=(ref,))
    payload = config.canonical()
    config.assert_secret_boundary(secrets)
    serialized = json.dumps(payload, sort_keys=True)
    assert "VERY-SECRET-R14-3-VALUE" not in serialized
    assert "fixture-token" in serialized
    assert BackendLocalConfig.from_dict(payload) == config
    contaminated = dict(payload)
    contaminated["provider"] = "forbidden"
    with pytest.raises(ValueError, match="unknown or missing"):
        BackendLocalConfig.from_dict(contaminated)


def test_scaffold_generate_twice_is_byte_identical(tmp_path: Path) -> None:
    engine = BackendScaffoldEngine()
    config = _config()
    first = engine.generate(tmp_path, config)
    snapshot = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*"))
        if path.is_file()
    }
    second = engine.generate(tmp_path, config)
    snapshot2 = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*"))
        if path.is_file()
    }
    assert first == second
    assert first.digest() == second.digest()
    assert snapshot == snapshot2
    assert engine.load_config(tmp_path) == config
    assert engine.load_manifest(tmp_path) == first


def test_scaffold_refuses_divergent_owned_file(tmp_path: Path) -> None:
    engine = BackendScaffoldEngine()
    config = _config()
    engine.generate(tmp_path, config)
    readme = tmp_path / engine.README_PATH
    readme.write_text("user drift\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refuses to overwrite"):
        engine.generate(tmp_path, config)


def test_r14_3_schemas_accept_canonical_documents() -> None:
    config = _config()
    engine = BackendScaffoldEngine()
    _rendered, manifest = engine.render(config)
    health = BackendHealthSnapshot(
        service_id="r14_3_fixture.local",
        environment_id="local",
        state=BackendHealthState.READY,
        live=True,
        ready=True,
        host="127.0.0.1",
        port=34567,
    )
    _validator("backend-local-config.schema.json").validate(config.canonical())
    _validator("backend-workspace-manifest.schema.json").validate(manifest.canonical())
    _validator("backend-health-snapshot.schema.json").validate(health.canonical())


def test_local_runtime_start_health_stop_is_bounded_and_killswitch_owned(tmp_path: Path) -> None:
    switch = KillSwitch()
    secrets = KodeSecrets(MemorySecretBackend())
    runtime = BackendLocalRuntime(tmp_path, secrets=secrets, kill_switch=switch)
    started = time.monotonic()
    handle = runtime.start(_config(), startup_timeout=10.0)
    try:
        assert time.monotonic() - started < 10.0
        assert switch.active_count == 1
        health = runtime.probe(handle)
        assert health.state is BackendHealthState.READY
        assert health.live is True
        assert health.ready is True
        assert health.host == "127.0.0.1"
        assert 1 <= health.port <= 65535
    finally:
        stopped = runtime.stop(handle, shutdown_timeout=5.0)
    assert stopped.state is BackendHealthState.STOPPED
    assert stopped.live is False
    assert stopped.ready is False
    assert switch.active_count == 0


def test_runtime_never_persists_or_logs_resolved_secret_value(tmp_path: Path) -> None:
    switch = KillSwitch()
    secrets = KodeSecrets(MemorySecretBackend())
    raw = "R14-3-SUPER-SECRET-MATERIAL"
    secrets.store("kodepoia.backend.test", "api-key", raw)
    ref = secrets.ref("kodepoia.backend.test", "api-key")
    runtime = BackendLocalRuntime(tmp_path, secrets=secrets, kill_switch=switch)
    handle = runtime.start(_config(secret_refs=(ref,)), startup_timeout=10.0)
    try:
        assert raw not in runtime.redacted_log(handle)
        for path in tmp_path.rglob("*"):
            if path.is_file():
                assert raw.encode("utf-8") not in path.read_bytes()
    finally:
        runtime.stop(handle)


def test_production_environment_cannot_start_local_fixture(tmp_path: Path) -> None:
    base = _config()
    production = BackendConfigOverlay(
        environment=BackendEnvironmentIdentity("production", BackendEnvironmentKind.PRODUCTION)
    ).apply(base)
    runtime = BackendLocalRuntime(
        tmp_path,
        secrets=KodeSecrets(MemorySecretBackend()),
        kill_switch=KillSwitch(),
    )
    with pytest.raises(PermissionError, match="LOCAL or TEST"):
        runtime.start(production)


def test_fixed_port_conflict_fails_closed_and_cleans_process(tmp_path: Path) -> None:
    switch = KillSwitch()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        port = int(occupied.getsockname()[1])
        runtime = BackendLocalRuntime(
            tmp_path,
            secrets=KodeSecrets(MemorySecretBackend()),
            kill_switch=switch,
        )
        with pytest.raises(RuntimeError, match="exited before readiness"):
            runtime.start(_config(port=port), startup_timeout=5.0)
    assert switch.active_count == 0
