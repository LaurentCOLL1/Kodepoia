from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.core.secret_guard import (
    ArtifactLeakScanner,
    EphemeralSecretResolver,
    SecretAwareProcessSandbox,
    SecretDestinationPolicy,
    SecretTaintGuard,
)
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend
from kodepoia.exceptions import PolicyDenied


def _secrets() -> tuple[KodeSecrets, SecretTaintGuard, str]:
    secrets = KodeSecrets(MemorySecretBackend())
    canary = "KODEPOIA_SYNTHETIC_SECRET_R16_4_ALPHA_7f83b1657ff1"
    secrets.store("r16.4", "alpha", canary)
    return secrets, SecretTaintGuard(secrets), canary


def test_raw_and_encoded_secret_variants_are_redacted() -> None:
    _secrets_store, guard, canary = _secrets()
    encoded = base64.b64encode(canary.encode()).decode()
    double_encoded = base64.b64encode(encoded.encode()).decode()

    redacted = guard.redact_text(f"raw={canary} b64={encoded} double={double_encoded}")

    assert canary not in redacted
    assert encoded not in redacted
    assert double_encoded not in redacted
    assert redacted.count("<redacted-secret>") >= 3


def test_sensitive_named_fields_are_redacted_without_known_value() -> None:
    _secrets_store, guard, _canary = _secrets()
    payload = {"nested": {"api_key": "unknown-but-sensitive", "safe": "visible"}}

    sanitized = guard.sanitize_payload(payload)
    leaks = guard.find_leaks(payload)

    assert sanitized["nested"]["api_key"] == "<redacted-secret>"
    assert sanitized["nested"]["safe"] == "visible"
    assert any(item.encoding == "sensitive-field" for item in leaks)


def test_secret_refs_are_durable_without_materializing_values() -> None:
    secrets, guard, canary = _secrets()
    ref = secrets.ref("r16.4", "alpha")
    payload = {"credential_ref": ref}

    sanitized = guard.sanitize_payload(payload)

    assert sanitized == {"credential_ref": {"namespace": "r16.4", "key": "alpha"}}
    assert canary not in guard.sanitize_json(payload)
    assert not guard.contains_taint(payload)


def test_raw_secret_is_denied_in_argv_and_ordinary_env() -> None:
    _secrets_store, guard, canary = _secrets()

    with pytest.raises(PolicyDenied, match="argv"):
        guard.assert_safe_argv(["tool", "--token", canary])
    with pytest.raises(PolicyDenied, match="environment"):
        guard.assert_safe_environment({"TOKEN": canary})


def test_ephemeral_resolver_observes_rotation_without_durable_cache() -> None:
    secrets, guard, old_value = _secrets()
    backend = secrets.backend
    ref = secrets.ref("r16.4", "alpha")
    resolver = EphemeralSecretResolver(secrets, guard)

    assert resolver.resolve(ref) == old_value
    new_value = "KODEPOIA_SYNTHETIC_SECRET_R16_4_ROTATED_9e107d9d372b"
    backend.set("r16.4", "alpha", new_value)
    assert resolver.resolve(ref) == new_value

    redacted = guard.redact_text(f"old={old_value} new={new_value}")
    assert old_value not in redacted
    assert new_value not in redacted


def test_secret_destination_policy_requires_explicit_host_and_payload_authority() -> None:
    _secrets_store, guard, canary = _secrets()
    policy = SecretDestinationPolicy(approved_hosts=["api.example.test"])

    with pytest.raises(PolicyDenied, match="egress denied"):
        policy.authorize("https://evil.example.test/upload", {"token": canary}, guard)
    with pytest.raises(PolicyDenied, match="egress denied"):
        policy.authorize("https://api.example.test/upload", {"token": canary}, guard)

    policy.authorize(
        "https://api.example.test/upload",
        {"token": canary},
        guard,
        allow_secret_payload=True,
    )

    with pytest.raises(PolicyDenied, match="destination URLs"):
        policy.authorize(
            f"https://api.example.test/upload?token={canary}",
            {"safe": True},
            guard,
        )


def test_secret_aware_process_resolves_env_only_at_launch_and_redacts_output(tmp_path: Path) -> None:
    secrets, guard, canary = _secrets()
    executable = Path(sys.executable).name.lower()
    sandbox = ProcessSandbox(tmp_path, allowed_executables={executable})
    protected = SecretAwareProcessSandbox(sandbox, secrets, guard)

    result = protected.run(
        [
            sys.executable,
            "-c",
            "import os,sys; v=os.environ['R16_SECRET']; print(v); print(v, file=sys.stderr)",
        ],
        secret_env={"R16_SECRET": secrets.ref("r16.4", "alpha")},
    )

    assert result.returncode == 0
    assert canary not in result.stdout
    assert canary not in result.stderr
    assert "<redacted-secret>" in result.stdout
    assert "<redacted-secret>" in result.stderr


def test_exception_sanitization_preserves_type_without_secret() -> None:
    _secrets_store, guard, canary = _secrets()
    exc = RuntimeError(f"request failed with credential {canary}")

    sanitized = guard.sanitize_exception(exc)

    assert sanitized.startswith("RuntimeError:")
    assert canary not in sanitized
    assert "<redacted-secret>" in sanitized


def test_artifact_scanner_reports_location_without_secret_contents(tmp_path: Path) -> None:
    _secrets_store, guard, canary = _secrets()
    encoded = base64.b64encode(canary.encode()).decode()
    (tmp_path / "clean.json").write_text('{"status":"ok"}\n', encoding="utf-8")
    (tmp_path / "leaky.log").write_text(f"debug={encoded}\n", encoding="utf-8")
    scanner = ArtifactLeakScanner(guard)

    report = scanner.scan(tmp_path)
    serialized = str(report.to_dict())

    assert report.clean is False
    assert any(item.location == "leaky.log" for item in report.leaks)
    assert canary not in serialized
    assert encoded not in serialized
    with pytest.raises(PolicyDenied, match="leaky.log"):
        scanner.require_clean(tmp_path)


def test_artifact_scan_bounds_fail_closed(tmp_path: Path) -> None:
    _secrets_store, guard, _canary = _secrets()
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    scanner = ArtifactLeakScanner(guard, max_files=1)

    report = scanner.scan(tmp_path)

    assert report.bounded is False
    assert report.clean is False
    with pytest.raises(PolicyDenied, match="bounds"):
        scanner.require_clean(tmp_path)
