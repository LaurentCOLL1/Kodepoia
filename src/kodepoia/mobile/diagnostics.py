from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping

from .contracts import MobilePlatform, canonical_json_bytes

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_CAPTURED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_METRIC_NAME_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_MAX_SOURCE_BYTES = 2 * 1024 * 1024
_MAX_REDACTED_BYTES = 2 * 1024 * 1024
_MAX_BUNDLE_BYTES = 16 * 1024 * 1024
_MAX_ENTRIES = 256
_MAX_FINGERPRINTS = 256
_MAX_PERFORMANCE_SNAPSHOTS = 256
_MAX_METRICS = 64
_MAX_SENSITIVE_VALUES = 32
_MAX_RETENTION_DAYS = 90
_MAX_SIGNATURE_COMPONENTS = 64
_MAX_SIGNATURE_COMPONENT_LENGTH = 512


class DiagnosticSourceKind(StrEnum):
    ANDROID_LOGCAT = "ANDROID_LOGCAT"
    ANDROID_CRASH = "ANDROID_CRASH"
    ANDROID_ANR = "ANDROID_ANR"
    ANDROID_TEST = "ANDROID_TEST"
    ANDROID_PERFORMANCE = "ANDROID_PERFORMANCE"
    APPLE_CRASH = "APPLE_CRASH"
    APPLE_JETSAM = "APPLE_JETSAM"
    APPLE_CONSOLE = "APPLE_CONSOLE"
    APPLE_XCTEST = "APPLE_XCTEST"
    APPLE_PERFORMANCE = "APPLE_PERFORMANCE"


class DiagnosticProvider(StrEnum):
    LOCAL_FILE = "LOCAL_FILE"
    ADB = "ADB"
    ANDROID_RUNTIME = "ANDROID_RUNTIME"
    GOOGLE_PLAY = "GOOGLE_PLAY"
    FIREBASE_CRASHLYTICS = "FIREBASE_CRASHLYTICS"
    XCODE = "XCODE"
    APP_STORE = "APP_STORE"
    TESTFLIGHT = "TESTFLIGHT"
    DEVICE_EXPORT = "DEVICE_EXPORT"


class DiagnosticCompleteness(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


class DiagnosticCollectionMode(StrEnum):
    ON_DEMAND = "ON_DEMAND"
    TEST_RUN = "TEST_RUN"
    EXPLICIT_USER_EXPORT = "EXPLICIT_USER_EXPORT"


class DiagnosticFingerprintKind(StrEnum):
    CRASH = "CRASH"
    ANR = "ANR"
    MEMORY_TERMINATION = "MEMORY_TERMINATION"
    TEST_FAILURE = "TEST_FAILURE"
    PERFORMANCE = "PERFORMANCE"


class PerformanceUnit(StrEnum):
    MILLISECONDS = "MILLISECONDS"
    BYTES = "BYTES"
    PERCENT = "PERCENT"
    COUNT = "COUNT"
    FPS = "FPS"
    MILLIWATTS = "MILLIWATTS"
    BYTES_PER_SECOND = "BYTES_PER_SECOND"


@dataclass(frozen=True, slots=True)
class RedactionCount:
    category: str
    count: int

    def __post_init__(self) -> None:
        _stable_id(self.category, "redaction category")
        if not 1 <= self.count <= 1_000_000:
            raise ValueError("redaction count is outside bounded range")

    def to_dict(self) -> dict[str, object]:
        return {"category": self.category, "count": self.count}


@dataclass(frozen=True, slots=True)
class RedactionResult:
    text: str
    redacted_sha256: str
    counts: tuple[RedactionCount, ...]

    def __post_init__(self) -> None:
        _sha256(self.redacted_sha256, "redacted_sha256")
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.redacted_sha256:
            raise ValueError("redacted_sha256 does not match redacted text")
        if len(self.text.encode("utf-8")) > _MAX_REDACTED_BYTES:
            raise ValueError("redacted diagnostic text exceeds bounded size")
        counts = tuple(sorted(self.counts, key=lambda item: item.category))
        if len({item.category for item in counts}) != len(counts):
            raise ValueError("redaction categories must be unique")
        object.__setattr__(self, "counts", counts)

    @property
    def changed(self) -> bool:
        return bool(self.counts)

    def to_dict(self) -> dict[str, object]:
        return {
            "redacted_sha256": self.redacted_sha256,
            "counts": [item.to_dict() for item in self.counts],
            "changed": self.changed,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticBinding:
    release_candidate_sha256: str
    artifact_sha256: str
    device_snapshot_sha256: str
    toolchain_sha256: str
    test_run_sha256: str | None = None

    def __post_init__(self) -> None:
        _sha256(self.release_candidate_sha256, "release_candidate_sha256")
        _sha256(self.artifact_sha256, "artifact_sha256")
        _sha256(self.device_snapshot_sha256, "device_snapshot_sha256")
        _sha256(self.toolchain_sha256, "toolchain_sha256")
        if self.test_run_sha256 is not None:
            _sha256(self.test_run_sha256, "test_run_sha256")

    def to_dict(self) -> dict[str, object]:
        return {
            "release_candidate_sha256": self.release_candidate_sha256,
            "artifact_sha256": self.artifact_sha256,
            "device_snapshot_sha256": self.device_snapshot_sha256,
            "toolchain_sha256": self.toolchain_sha256,
            "test_run_sha256": self.test_run_sha256,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticEntry:
    entry_id: str
    platform: MobilePlatform
    source_kind: DiagnosticSourceKind
    provider: DiagnosticProvider
    captured_at_utc: str
    completeness: DiagnosticCompleteness
    binding: DiagnosticBinding
    source_sha256: str
    source_size_bytes: int
    source_digest_verified: bool
    redacted_text: str
    redacted_sha256: str
    redactions: tuple[RedactionCount, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.entry_id, "entry_id")
        _validate_source_platform(self.platform, self.source_kind)
        _validate_provider_platform(self.platform, self.provider)
        if _CAPTURED_AT_RE.fullmatch(self.captured_at_utc) is None:
            raise ValueError("captured_at_utc must be second-precision UTC RFC3339 text")
        _sha256(self.source_sha256, "source_sha256")
        if not 0 <= self.source_size_bytes <= _MAX_SOURCE_BYTES:
            raise ValueError("source_size_bytes is outside bounded range")
        if not self.source_digest_verified:
            raise ValueError("diagnostic source digest must be independently verified")
        if len(self.redacted_text.encode("utf-8")) > _MAX_REDACTED_BYTES:
            raise ValueError("redacted diagnostic text exceeds bounded size")
        _sha256(self.redacted_sha256, "redacted_sha256")
        if hashlib.sha256(self.redacted_text.encode("utf-8")).hexdigest() != self.redacted_sha256:
            raise ValueError("redacted payload digest mismatch")
        redactions = tuple(sorted(self.redactions, key=lambda item: item.category))
        if len({item.category for item in redactions}) != len(redactions):
            raise ValueError("redaction categories must be unique")
        object.__setattr__(self, "redactions", redactions)

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "platform": self.platform.value,
            "source_kind": self.source_kind.value,
            "provider": self.provider.value,
            "captured_at_utc": self.captured_at_utc,
            "completeness": self.completeness.value,
            "binding": self.binding.to_dict(),
            "source_sha256": self.source_sha256,
            "source_size_bytes": self.source_size_bytes,
            "source_digest_verified": self.source_digest_verified,
            "redacted_text": self.redacted_text,
            "redacted_sha256": self.redacted_sha256,
            "redactions": [item.to_dict() for item in self.redactions],
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class DiagnosticFingerprint:
    fingerprint_id: str
    kind: DiagnosticFingerprintKind
    platform: MobilePlatform
    source_kind: DiagnosticSourceKind
    signature_sha256: str
    component_count: int

    def __post_init__(self) -> None:
        _stable_id(self.fingerprint_id, "fingerprint_id")
        _validate_source_platform(self.platform, self.source_kind)
        _validate_fingerprint_source(self.kind, self.source_kind)
        _sha256(self.signature_sha256, "signature_sha256")
        if not 1 <= self.component_count <= _MAX_SIGNATURE_COMPONENTS:
            raise ValueError("fingerprint component count is outside bounded range")

    def to_dict(self) -> dict[str, object]:
        return {
            "fingerprint_id": self.fingerprint_id,
            "kind": self.kind.value,
            "platform": self.platform.value,
            "source_kind": self.source_kind.value,
            "signature_sha256": self.signature_sha256,
            "component_count": self.component_count,
        }


@dataclass(frozen=True, slots=True)
class PerformanceMetric:
    name: str
    unit: PerformanceUnit
    value: float

    def __post_init__(self) -> None:
        if _METRIC_NAME_RE.fullmatch(self.name) is None:
            raise ValueError("performance metric name is invalid")
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise ValueError("performance metric value must be numeric")
        numeric = float(self.value)
        if not math.isfinite(numeric) or numeric < 0 or numeric > 1e18:
            raise ValueError("performance metric value is outside bounded finite range")
        if self.unit is PerformanceUnit.PERCENT and numeric > 100:
            raise ValueError("percentage performance metric must be 0..100")
        object.__setattr__(self, "value", numeric)

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "unit": self.unit.value, "value": self.value}


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    snapshot_id: str
    platform: MobilePlatform
    captured_at_utc: str
    binding: DiagnosticBinding
    source_entry_sha256: str
    metrics: tuple[PerformanceMetric, ...]

    def __post_init__(self) -> None:
        _stable_id(self.snapshot_id, "snapshot_id")
        if _CAPTURED_AT_RE.fullmatch(self.captured_at_utc) is None:
            raise ValueError("captured_at_utc must be second-precision UTC RFC3339 text")
        _sha256(self.source_entry_sha256, "source_entry_sha256")
        metrics = tuple(sorted(self.metrics, key=lambda item: (item.name, item.unit.value)))
        if not metrics or len(metrics) > _MAX_METRICS:
            raise ValueError("performance snapshot requires 1..64 metrics")
        keys = {(item.name, item.unit) for item in metrics}
        if len(keys) != len(metrics):
            raise ValueError("performance snapshot cannot contain duplicate metric identities")
        object.__setattr__(self, "metrics", metrics)

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "platform": self.platform.value,
            "captured_at_utc": self.captured_at_utc,
            "binding": self.binding.to_dict(),
            "source_entry_sha256": self.source_entry_sha256,
            "metrics": [item.to_dict() for item in self.metrics],
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class DiagnosticRetentionPolicy:
    retention_days: int = 30
    max_bundle_bytes: int = 4 * 1024 * 1024
    max_entries: int = 128
    export_allowed: bool = True

    def __post_init__(self) -> None:
        if not 1 <= self.retention_days <= _MAX_RETENTION_DAYS:
            raise ValueError("diagnostic retention must be 1..90 days")
        if not 1 <= self.max_bundle_bytes <= _MAX_BUNDLE_BYTES:
            raise ValueError("diagnostic bundle byte budget is outside bounded range")
        if not 1 <= self.max_entries <= _MAX_ENTRIES:
            raise ValueError("diagnostic entry budget is outside bounded range")

    def to_dict(self) -> dict[str, object]:
        return {
            "retention_days": self.retention_days,
            "max_bundle_bytes": self.max_bundle_bytes,
            "max_entries": self.max_entries,
            "export_allowed": self.export_allowed,
        }


@dataclass(frozen=True, slots=True)
class MobileDiagnosticBundle:
    bundle_id: str
    collection_mode: DiagnosticCollectionMode
    release_candidate_sha256: str
    artifact_sha256: str
    retention: DiagnosticRetentionPolicy
    entries: tuple[DiagnosticEntry, ...]
    fingerprints: tuple[DiagnosticFingerprint, ...] = ()
    performance_snapshots: tuple[PerformanceSnapshot, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.bundle_id, "bundle_id")
        _sha256(self.release_candidate_sha256, "release_candidate_sha256")
        _sha256(self.artifact_sha256, "artifact_sha256")
        entries = tuple(sorted(self.entries, key=lambda item: item.entry_id))
        if not entries or len(entries) > self.retention.max_entries:
            raise ValueError("diagnostic bundle entry count exceeds retention policy")
        if len(entries) > _MAX_ENTRIES:
            raise ValueError("diagnostic bundle exceeds global entry bound")
        if len({item.entry_id for item in entries}) != len(entries):
            raise ValueError("diagnostic bundle cannot contain duplicate entry ids")
        if len({item.digest() for item in entries}) != len(entries):
            raise ValueError("diagnostic bundle cannot contain duplicate diagnostic entries")
        for entry in entries:
            _require_binding(entry.binding, self.release_candidate_sha256, self.artifact_sha256)
        object.__setattr__(self, "entries", entries)

        fingerprints = tuple(sorted(self.fingerprints, key=lambda item: item.fingerprint_id))
        if len(fingerprints) > _MAX_FINGERPRINTS:
            raise ValueError("diagnostic fingerprint count exceeds global bound")
        if len({item.fingerprint_id for item in fingerprints}) != len(fingerprints):
            raise ValueError("diagnostic bundle cannot contain duplicate fingerprint ids")
        object.__setattr__(self, "fingerprints", fingerprints)

        snapshots = tuple(sorted(self.performance_snapshots, key=lambda item: item.snapshot_id))
        if len(snapshots) > _MAX_PERFORMANCE_SNAPSHOTS:
            raise ValueError("performance snapshot count exceeds global bound")
        if len({item.snapshot_id for item in snapshots}) != len(snapshots):
            raise ValueError("diagnostic bundle cannot contain duplicate performance snapshot ids")
        entry_digests = {item.digest() for item in entries}
        for snapshot in snapshots:
            _require_binding(snapshot.binding, self.release_candidate_sha256, self.artifact_sha256)
            if snapshot.source_entry_sha256 not in entry_digests:
                raise ValueError("performance snapshot must bind a diagnostic entry in this bundle")
        object.__setattr__(self, "performance_snapshots", snapshots)

        payload_bytes = canonical_json_bytes(self._payload_without_budget_check())
        if len(payload_bytes) > self.retention.max_bundle_bytes:
            raise ValueError("diagnostic bundle exceeds configured byte budget")
        if len(payload_bytes) > _MAX_BUNDLE_BYTES:
            raise ValueError("diagnostic bundle exceeds global byte bound")

    def _payload_without_budget_check(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "bundle_id": self.bundle_id,
            "collection_mode": self.collection_mode.value,
            "release_candidate_sha256": self.release_candidate_sha256,
            "artifact_sha256": self.artifact_sha256,
            "retention": self.retention.to_dict(),
            "entries": [item.to_dict() for item in self.entries],
            "fingerprints": [item.to_dict() for item in self.fingerprints],
            "performance_snapshots": [item.to_dict() for item in self.performance_snapshots],
            "continuous_hidden_telemetry": False,
        }

    def to_dict(self) -> dict[str, object]:
        return self._payload_without_budget_check()

    def digest(self) -> str:
        return _digest(self.to_dict())

    def export_bytes(self) -> bytes:
        if not self.retention.export_allowed:
            raise ValueError("diagnostic export is disabled by retention policy")
        return canonical_json_bytes(self.to_dict())


def _stable_id(value: str, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _digest(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _validate_source_platform(platform: MobilePlatform, source_kind: DiagnosticSourceKind) -> None:
    if source_kind.value.startswith("ANDROID_") and platform is not MobilePlatform.ANDROID:
        raise ValueError("Android diagnostic source cannot certify an Apple platform")
    if source_kind.value.startswith("APPLE_") and platform not in {MobilePlatform.IOS, MobilePlatform.IPADOS}:
        raise ValueError("Apple diagnostic source cannot certify Android")


def _validate_provider_platform(platform: MobilePlatform, provider: DiagnosticProvider) -> None:
    android_only = {
        DiagnosticProvider.ADB,
        DiagnosticProvider.ANDROID_RUNTIME,
        DiagnosticProvider.GOOGLE_PLAY,
        DiagnosticProvider.FIREBASE_CRASHLYTICS,
    }
    apple_only = {DiagnosticProvider.XCODE, DiagnosticProvider.APP_STORE, DiagnosticProvider.TESTFLIGHT}
    if provider in android_only and platform is not MobilePlatform.ANDROID:
        raise ValueError("Android diagnostic provider cannot certify an Apple platform")
    if provider in apple_only and platform not in {MobilePlatform.IOS, MobilePlatform.IPADOS}:
        raise ValueError("Apple diagnostic provider cannot certify Android")


def _validate_fingerprint_source(kind: DiagnosticFingerprintKind, source_kind: DiagnosticSourceKind) -> None:
    allowed = {
        DiagnosticFingerprintKind.CRASH: {DiagnosticSourceKind.ANDROID_CRASH, DiagnosticSourceKind.APPLE_CRASH},
        DiagnosticFingerprintKind.ANR: {DiagnosticSourceKind.ANDROID_ANR},
        DiagnosticFingerprintKind.MEMORY_TERMINATION: {DiagnosticSourceKind.APPLE_JETSAM},
        DiagnosticFingerprintKind.TEST_FAILURE: {DiagnosticSourceKind.ANDROID_TEST, DiagnosticSourceKind.APPLE_XCTEST},
        DiagnosticFingerprintKind.PERFORMANCE: {DiagnosticSourceKind.ANDROID_PERFORMANCE, DiagnosticSourceKind.APPLE_PERFORMANCE},
    }
    if source_kind not in allowed[kind]:
        raise ValueError("fingerprint kind is incompatible with diagnostic source")


def _require_binding(binding: DiagnosticBinding, release_sha256: str, artifact_sha256: str) -> None:
    if binding.release_candidate_sha256 != release_sha256:
        raise ValueError("cross-release diagnostic substitution rejected")
    if binding.artifact_sha256 != artifact_sha256:
        raise ValueError("cross-artifact diagnostic substitution rejected")


def verify_source_digest(source_bytes: bytes, expected_sha256: str) -> None:
    _sha256(expected_sha256, "expected_source_sha256")
    if not isinstance(source_bytes, bytes):
        raise TypeError("diagnostic source must be bytes")
    if len(source_bytes) > _MAX_SOURCE_BYTES:
        raise ValueError("diagnostic source exceeds bounded size")
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != expected_sha256:
        raise ValueError("diagnostic source digest mismatch")


def redact_diagnostic_text(text: str, *, sensitive_values: Iterable[str] = ()) -> RedactionResult:
    if not isinstance(text, str):
        raise TypeError("diagnostic text must be str")
    encoded = text.encode("utf-8")
    if len(encoded) > _MAX_SOURCE_BYTES:
        raise ValueError("diagnostic text exceeds bounded size")
    if "\x00" in text:
        raise ValueError("diagnostic text contains NUL and is treated as corrupt")

    values = tuple(sensitive_values)
    if len(values) > _MAX_SENSITIVE_VALUES:
        raise ValueError("too many explicit sensitive values")
    normalized_values: list[str] = []
    for value in values:
        if not isinstance(value, str) or not 4 <= len(value) <= 512 or "\x00" in value:
            raise ValueError("explicit sensitive values must be bounded non-NUL strings")
        normalized_values.append(value)

    current = text.replace("\r\n", "\n").replace("\r", "\n")
    counts: dict[str, int] = {}

    for value in sorted(set(normalized_values), key=lambda item: (-len(item), item)):
        occurrences = current.count(value)
        if occurrences:
            current = current.replace(value, "[REDACTED_EXPLICIT]")
            counts["explicit"] = counts.get("explicit", 0) + occurrences

    patterns: tuple[tuple[str, re.Pattern[str], str], ...] = (
        (
            "authorization",
            re.compile(r"(?im)\bAuthorization\s*:\s*(?:Bearer\s+)?[^\s]+"),
            "Authorization: [REDACTED_TOKEN]",
        ),
        (
            "secret_assignment",
            re.compile(
                r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|passwd|secret)"
                r"\s*[:=]\s*[^\s,;]+"
            ),
            r"\1=[REDACTED_SECRET]",
        ),
        (
            "email",
            re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63}\b"),
            "[REDACTED_EMAIL]",
        ),
        (
            "ipv4",
            re.compile(r"(?<![0-9])(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}(?![0-9])"),
            "[REDACTED_IP]",
        ),
        (
            "unix_home",
            re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^/\s]+"),
            "/[REDACTED_HOME]",
        ),
        (
            "windows_home",
            re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+"),
            r"C:\\[REDACTED_HOME]",
        ),
    )
    for category, pattern, replacement in patterns:
        current, count = pattern.subn(replacement, current)
        if count:
            counts[category] = counts.get(category, 0) + count

    if len(current.encode("utf-8")) > _MAX_REDACTED_BYTES:
        raise ValueError("redacted diagnostic text exceeds bounded size")
    digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    return RedactionResult(
        text=current,
        redacted_sha256=digest,
        counts=tuple(RedactionCount(category=key, count=value) for key, value in sorted(counts.items())),
    )


def ingest_text_diagnostic(
    *,
    entry_id: str,
    platform: MobilePlatform,
    source_kind: DiagnosticSourceKind,
    provider: DiagnosticProvider,
    captured_at_utc: str,
    completeness: DiagnosticCompleteness,
    binding: DiagnosticBinding,
    source_bytes: bytes,
    expected_source_sha256: str,
    sensitive_values: Iterable[str] = (),
) -> DiagnosticEntry:
    verify_source_digest(source_bytes, expected_source_sha256)
    try:
        text = source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("diagnostic source is not valid UTF-8 text") from exc
    redacted = redact_diagnostic_text(text, sensitive_values=sensitive_values)
    return DiagnosticEntry(
        entry_id=entry_id,
        platform=platform,
        source_kind=source_kind,
        provider=provider,
        captured_at_utc=captured_at_utc,
        completeness=completeness,
        binding=binding,
        source_sha256=expected_source_sha256,
        source_size_bytes=len(source_bytes),
        source_digest_verified=True,
        redacted_text=redacted.text,
        redacted_sha256=redacted.redacted_sha256,
        redactions=redacted.counts,
    )


def build_fingerprint(
    *,
    kind: DiagnosticFingerprintKind,
    platform: MobilePlatform,
    source_kind: DiagnosticSourceKind,
    signature_components: Iterable[str],
) -> DiagnosticFingerprint:
    _validate_source_platform(platform, source_kind)
    _validate_fingerprint_source(kind, source_kind)
    components = tuple(signature_components)
    if not components or len(components) > _MAX_SIGNATURE_COMPONENTS:
        raise ValueError("fingerprint requires 1..64 signature components")
    normalized: list[str] = []
    for component in components:
        if not isinstance(component, str):
            raise TypeError("fingerprint signature components must be text")
        compact = " ".join(component.split())
        if not compact or len(compact) > _MAX_SIGNATURE_COMPONENT_LENGTH or "\x00" in compact:
            raise ValueError("fingerprint signature component is invalid or unbounded")
        redacted = redact_diagnostic_text(compact)
        normalized.append(redacted.text)
    payload = {
        "kind": kind.value,
        "platform": platform.value,
        "source_kind": source_kind.value,
        "signature_components": normalized,
        "fingerprint_version": 1,
    }
    digest = _digest(payload)
    return DiagnosticFingerprint(
        fingerprint_id=f"{kind.value.lower()}-{digest[:32]}",
        kind=kind,
        platform=platform,
        source_kind=source_kind,
        signature_sha256=digest,
        component_count=len(normalized),
    )


def verify_bundle_binding(
    bundle: MobileDiagnosticBundle,
    *,
    expected_release_candidate_sha256: str,
    expected_artifact_sha256: str,
) -> None:
    _sha256(expected_release_candidate_sha256, "expected_release_candidate_sha256")
    _sha256(expected_artifact_sha256, "expected_artifact_sha256")
    if bundle.release_candidate_sha256 != expected_release_candidate_sha256:
        raise ValueError("cross-release diagnostic substitution rejected")
    if bundle.artifact_sha256 != expected_artifact_sha256:
        raise ValueError("cross-artifact diagnostic substitution rejected")


def deduplicate_fingerprints(
    fingerprints: Iterable[DiagnosticFingerprint],
) -> tuple[DiagnosticFingerprint, ...]:
    by_signature: dict[tuple[DiagnosticFingerprintKind, MobilePlatform, DiagnosticSourceKind, str], DiagnosticFingerprint] = {}
    for fingerprint in fingerprints:
        key = (fingerprint.kind, fingerprint.platform, fingerprint.source_kind, fingerprint.signature_sha256)
        existing = by_signature.get(key)
        if existing is None or fingerprint.fingerprint_id < existing.fingerprint_id:
            by_signature[key] = fingerprint
    return tuple(sorted(by_signature.values(), key=lambda item: item.fingerprint_id))
