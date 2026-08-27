from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.mobile.contracts import MobilePlatform
from kodepoia.mobile.diagnostics import (
    DiagnosticBinding,
    DiagnosticCollectionMode,
    DiagnosticCompleteness,
    DiagnosticFingerprintKind,
    DiagnosticProvider,
    DiagnosticRetentionPolicy,
    DiagnosticSourceKind,
    MobileDiagnosticBundle,
    PerformanceMetric,
    PerformanceSnapshot,
    PerformanceUnit,
    build_fingerprint,
    deduplicate_fingerprints,
    ingest_text_diagnostic,
    redact_diagnostic_text,
    verify_bundle_binding,
    verify_source_digest,
)


def _sha(char: str) -> str:
    return char * 64


def _binding(*, release: str = "a", artifact: str = "b", test_run: str | None = "e") -> DiagnosticBinding:
    return DiagnosticBinding(
        release_candidate_sha256=_sha(release),
        artifact_sha256=_sha(artifact),
        device_snapshot_sha256=_sha("c"),
        toolchain_sha256=_sha("d"),
        test_run_sha256=_sha(test_run) if test_run is not None else None,
    )


def _entry(
    text: str = "FATAL EXCEPTION: main\ncom.example.App.run(App.kt:42)\n",
    *,
    entry_id: str = "android-crash-1",
    platform: MobilePlatform = MobilePlatform.ANDROID,
    source_kind: DiagnosticSourceKind = DiagnosticSourceKind.ANDROID_CRASH,
    provider: DiagnosticProvider = DiagnosticProvider.LOCAL_FILE,
    binding: DiagnosticBinding | None = None,
):
    source = text.encode("utf-8")
    return ingest_text_diagnostic(
        entry_id=entry_id,
        platform=platform,
        source_kind=source_kind,
        provider=provider,
        captured_at_utc="2026-08-27T16:00:00Z",
        completeness=DiagnosticCompleteness.COMPLETE,
        binding=binding or _binding(),
        source_bytes=source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
    )


def _bundle(*, entry=None, retention: DiagnosticRetentionPolicy | None = None) -> MobileDiagnosticBundle:
    actual = entry or _entry()
    return MobileDiagnosticBundle(
        bundle_id="bundle-1",
        collection_mode=DiagnosticCollectionMode.ON_DEMAND,
        release_candidate_sha256=_sha("a"),
        artifact_sha256=_sha("b"),
        retention=retention or DiagnosticRetentionPolicy(),
        entries=(actual,),
    )


def test_redaction_removes_common_secret_and_personal_patterns_before_export() -> None:
    raw = (
        "Authorization: Bearer top-secret-token\n"
        "api_key=abc123supersecret\n"
        "email=user@example.com ip=192.168.1.42\n"
        "unix=/home/laurent/private.txt windows=C:\\Users\\Laurent\\secret.txt\n"
        "explicit=private-value\n"
    )
    result = redact_diagnostic_text(raw, sensitive_values=("private-value",))
    assert "top-secret-token" not in result.text
    assert "abc123supersecret" not in result.text
    assert "user@example.com" not in result.text
    assert "192.168.1.42" not in result.text
    assert "/home/laurent" not in result.text
    assert "C:\\Users\\Laurent" not in result.text
    assert "private-value" not in result.text
    assert result.changed
    categories = {item.category for item in result.counts}
    assert {"authorization", "secret_assignment", "email", "ipv4", "unix_home", "windows_home", "explicit"}.issubset(categories)


def test_redaction_is_deterministic_and_normalizes_line_endings() -> None:
    first = redact_diagnostic_text("hello\r\nuser@example.com\r")
    second = redact_diagnostic_text("hello\nuser@example.com\n")
    assert first.text == second.text
    assert first.redacted_sha256 == second.redacted_sha256


def test_source_digest_is_verified_before_ingestion() -> None:
    source = b"safe diagnostic"
    verify_source_digest(source, hashlib.sha256(source).hexdigest())
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_source_digest(source, _sha("f"))


def test_corrupt_and_oversized_sources_fail_closed() -> None:
    corrupt = b"valid-prefix\xff"
    with pytest.raises(ValueError, match="valid UTF-8"):
        ingest_text_diagnostic(
            entry_id="corrupt",
            platform=MobilePlatform.ANDROID,
            source_kind=DiagnosticSourceKind.ANDROID_LOGCAT,
            provider=DiagnosticProvider.ADB,
            captured_at_utc="2026-08-27T16:00:00Z",
            completeness=DiagnosticCompleteness.PARTIAL,
            binding=_binding(),
            source_bytes=corrupt,
            expected_source_sha256=hashlib.sha256(corrupt).hexdigest(),
        )
    with pytest.raises(ValueError, match="contains NUL"):
        redact_diagnostic_text("prefix\x00suffix")
    oversized = b"x" * (2 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="bounded size"):
        verify_source_digest(oversized, hashlib.sha256(oversized).hexdigest())


def test_platform_source_and_provider_substitution_is_rejected() -> None:
    with pytest.raises(ValueError, match="Android diagnostic source"):
        _entry(platform=MobilePlatform.IOS, source_kind=DiagnosticSourceKind.ANDROID_ANR)
    with pytest.raises(ValueError, match="Android diagnostic provider"):
        _entry(
            platform=MobilePlatform.IOS,
            source_kind=DiagnosticSourceKind.APPLE_CRASH,
            provider=DiagnosticProvider.ADB,
        )
    with pytest.raises(ValueError, match="Apple diagnostic provider"):
        _entry(provider=DiagnosticProvider.XCODE)


def test_apple_crash_jetsam_console_and_xctest_remain_distinct_sources() -> None:
    for index, source_kind in enumerate(
        (
            DiagnosticSourceKind.APPLE_CRASH,
            DiagnosticSourceKind.APPLE_JETSAM,
            DiagnosticSourceKind.APPLE_CONSOLE,
            DiagnosticSourceKind.APPLE_XCTEST,
        ),
        start=1,
    ):
        entry = _entry(
            text=f"apple source {source_kind.value}",
            entry_id=f"apple-{index}",
            platform=MobilePlatform.IOS,
            source_kind=source_kind,
            provider=DiagnosticProvider.LOCAL_FILE,
        )
        assert entry.source_kind is source_kind


def test_ingested_entry_contains_only_redacted_text_for_serialization() -> None:
    secret = "customer-secret-9876"
    source = f"token={secret}\nuser@example.com".encode()
    entry = ingest_text_diagnostic(
        entry_id="redacted-entry",
        platform=MobilePlatform.ANDROID,
        source_kind=DiagnosticSourceKind.ANDROID_LOGCAT,
        provider=DiagnosticProvider.ADB,
        captured_at_utc="2026-08-27T16:00:00Z",
        completeness=DiagnosticCompleteness.COMPLETE,
        binding=_binding(),
        source_bytes=source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
    )
    payload = json.dumps(entry.to_dict(), sort_keys=True)
    assert secret not in payload
    assert "user@example.com" not in payload
    assert entry.source_digest_verified is True
    assert entry.source_sha256 == hashlib.sha256(source).hexdigest()


def test_cross_release_and_cross_artifact_bundle_substitution_is_rejected() -> None:
    entry = _entry()
    with pytest.raises(ValueError, match="cross-release"):
        MobileDiagnosticBundle(
            bundle_id="wrong-release",
            collection_mode=DiagnosticCollectionMode.ON_DEMAND,
            release_candidate_sha256=_sha("9"),
            artifact_sha256=_sha("b"),
            retention=DiagnosticRetentionPolicy(),
            entries=(entry,),
        )
    with pytest.raises(ValueError, match="cross-artifact"):
        MobileDiagnosticBundle(
            bundle_id="wrong-artifact",
            collection_mode=DiagnosticCollectionMode.ON_DEMAND,
            release_candidate_sha256=_sha("a"),
            artifact_sha256=_sha("9"),
            retention=DiagnosticRetentionPolicy(),
            entries=(entry,),
        )


def test_verify_bundle_binding_rejects_replay_against_other_release() -> None:
    bundle = _bundle()
    verify_bundle_binding(
        bundle,
        expected_release_candidate_sha256=_sha("a"),
        expected_artifact_sha256=_sha("b"),
    )
    with pytest.raises(ValueError, match="cross-release"):
        verify_bundle_binding(
            bundle,
            expected_release_candidate_sha256=_sha("f"),
            expected_artifact_sha256=_sha("b"),
        )


def test_fingerprint_kinds_are_source_specific_and_deterministic() -> None:
    first = build_fingerprint(
        kind=DiagnosticFingerprintKind.CRASH,
        platform=MobilePlatform.ANDROID,
        source_kind=DiagnosticSourceKind.ANDROID_CRASH,
        signature_components=("java.lang.IllegalStateException", "com.example.App.run(App.kt:42)"),
    )
    second = build_fingerprint(
        kind=DiagnosticFingerprintKind.CRASH,
        platform=MobilePlatform.ANDROID,
        source_kind=DiagnosticSourceKind.ANDROID_CRASH,
        signature_components=("java.lang.IllegalStateException", "com.example.App.run(App.kt:42)"),
    )
    assert first == second
    assert len(deduplicate_fingerprints((second, first))) == 1
    with pytest.raises(ValueError, match="incompatible"):
        build_fingerprint(
            kind=DiagnosticFingerprintKind.ANR,
            platform=MobilePlatform.IOS,
            source_kind=DiagnosticSourceKind.APPLE_CRASH,
            signature_components=("main",),
        )


def test_apple_jetsam_has_memory_termination_fingerprint_not_crash_fingerprint() -> None:
    fingerprint = build_fingerprint(
        kind=DiagnosticFingerprintKind.MEMORY_TERMINATION,
        platform=MobilePlatform.IOS,
        source_kind=DiagnosticSourceKind.APPLE_JETSAM,
        signature_components=("memory-pressure", "frontmost"),
    )
    assert fingerprint.kind is DiagnosticFingerprintKind.MEMORY_TERMINATION
    with pytest.raises(ValueError, match="incompatible"):
        build_fingerprint(
            kind=DiagnosticFingerprintKind.CRASH,
            platform=MobilePlatform.IOS,
            source_kind=DiagnosticSourceKind.APPLE_JETSAM,
            signature_components=("memory-pressure",),
        )


def test_performance_metrics_are_bounded_observations_not_provider_thresholds() -> None:
    metric = PerformanceMetric(name="startup.ms", unit=PerformanceUnit.MILLISECONDS, value=123.4)
    assert metric.value == 123.4
    with pytest.raises(ValueError, match="0..100"):
        PerformanceMetric(name="cpu.percent", unit=PerformanceUnit.PERCENT, value=100.01)
    with pytest.raises(ValueError, match="finite"):
        PerformanceMetric(name="startup.ms", unit=PerformanceUnit.MILLISECONDS, value=float("inf"))


def test_performance_snapshot_must_bind_an_entry_in_same_bundle() -> None:
    entry = _entry(
        text="startup_ms=123",
        entry_id="perf-entry",
        source_kind=DiagnosticSourceKind.ANDROID_PERFORMANCE,
    )
    snapshot = PerformanceSnapshot(
        snapshot_id="perf-1",
        platform=MobilePlatform.ANDROID,
        captured_at_utc="2026-08-27T16:00:00Z",
        binding=_binding(),
        source_entry_sha256=entry.digest(),
        metrics=(PerformanceMetric(name="startup.ms", unit=PerformanceUnit.MILLISECONDS, value=123),),
    )
    bundle = MobileDiagnosticBundle(
        bundle_id="perf-bundle",
        collection_mode=DiagnosticCollectionMode.TEST_RUN,
        release_candidate_sha256=_sha("a"),
        artifact_sha256=_sha("b"),
        retention=DiagnosticRetentionPolicy(),
        entries=(entry,),
        performance_snapshots=(snapshot,),
    )
    assert bundle.performance_snapshots == (snapshot,)

    wrong = PerformanceSnapshot(
        snapshot_id="perf-wrong",
        platform=MobilePlatform.ANDROID,
        captured_at_utc="2026-08-27T16:00:00Z",
        binding=_binding(),
        source_entry_sha256=_sha("9"),
        metrics=(PerformanceMetric(name="startup.ms", unit=PerformanceUnit.MILLISECONDS, value=123),),
    )
    with pytest.raises(ValueError, match="must bind a diagnostic entry"):
        MobileDiagnosticBundle(
            bundle_id="perf-wrong-bundle",
            collection_mode=DiagnosticCollectionMode.TEST_RUN,
            release_candidate_sha256=_sha("a"),
            artifact_sha256=_sha("b"),
            retention=DiagnosticRetentionPolicy(),
            entries=(entry,),
            performance_snapshots=(wrong,),
        )


def test_duplicate_performance_metric_identity_is_rejected() -> None:
    entry = _entry(source_kind=DiagnosticSourceKind.ANDROID_PERFORMANCE)
    with pytest.raises(ValueError, match="duplicate metric"):
        PerformanceSnapshot(
            snapshot_id="dup",
            platform=MobilePlatform.ANDROID,
            captured_at_utc="2026-08-27T16:00:00Z",
            binding=_binding(),
            source_entry_sha256=entry.digest(),
            metrics=(
                PerformanceMetric(name="fps", unit=PerformanceUnit.FPS, value=60),
                PerformanceMetric(name="fps", unit=PerformanceUnit.FPS, value=59),
            ),
        )


def test_bundle_has_only_explicit_collection_modes_and_no_hidden_telemetry() -> None:
    bundle = _bundle()
    payload = bundle.to_dict()
    assert payload["continuous_hidden_telemetry"] is False
    assert payload["collection_mode"] == "ON_DEMAND"
    assert "background" not in {item.value.lower() for item in DiagnosticCollectionMode}
    assert b'"continuous_hidden_telemetry":false' in bundle.export_bytes()


def test_export_can_be_disabled_and_bundle_size_is_bounded() -> None:
    no_export = _bundle(retention=DiagnosticRetentionPolicy(export_allowed=False))
    with pytest.raises(ValueError, match="export is disabled"):
        no_export.export_bytes()

    with pytest.raises(ValueError, match="configured byte budget"):
        _bundle(retention=DiagnosticRetentionPolicy(max_bundle_bytes=128))


def test_retention_policy_is_bounded() -> None:
    with pytest.raises(ValueError, match="1..90"):
        DiagnosticRetentionPolicy(retention_days=91)
    with pytest.raises(ValueError, match="entry budget"):
        DiagnosticRetentionPolicy(max_entries=257)
    with pytest.raises(ValueError, match="byte budget"):
        DiagnosticRetentionPolicy(max_bundle_bytes=16 * 1024 * 1024 + 1)


def test_schema_is_versioned_bounded_and_forbids_hidden_telemetry() -> None:
    schema_path = Path("schemas/mobile-diagnostics-v1.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["properties"]["continuous_hidden_telemetry"]["const"] is False
    assert schema["properties"]["entries"]["maxItems"] == 256
    assert schema["$defs"]["retention"]["properties"]["retention_days"]["maximum"] == 90
    assert "ANDROID_ANR" in schema["$defs"]["sourceKind"]["enum"]
    assert "APPLE_JETSAM" in schema["$defs"]["sourceKind"]["enum"]


def test_timestamp_and_explicit_sensitive_value_inputs_are_bounded() -> None:
    source = b"hello"
    with pytest.raises(ValueError, match="RFC3339"):
        ingest_text_diagnostic(
            entry_id="bad-time",
            platform=MobilePlatform.ANDROID,
            source_kind=DiagnosticSourceKind.ANDROID_LOGCAT,
            provider=DiagnosticProvider.ADB,
            captured_at_utc="2026-08-27 16:00:00",
            completeness=DiagnosticCompleteness.COMPLETE,
            binding=_binding(),
            source_bytes=source,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
        )
    with pytest.raises(ValueError, match="bounded"):
        redact_diagnostic_text("hello", sensitive_values=("x" * 513,))
