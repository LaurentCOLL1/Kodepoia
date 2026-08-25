from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Sequence

from kodepoia.mobile.contracts import canonical_json_bytes

_SERIAL_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_APP_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_COMPONENT_RE = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+/"
    r"(?:[A-Za-z_][A-Za-z0-9_$]*)(?:\.[A-Za-z_][A-Za-z0-9_$]*)+$"
)
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")
_ALLOWED_GETPROPS = frozenset(
    {
        "sys.boot_completed",
        "ro.build.version.release",
        "ro.product.model",
        "ro.product.cpu.abi",
        "ro.product.locale",
        "persist.sys.locale",
    }
)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha(value: str, field: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256")
    return value


def _serial(value: str) -> str:
    if _SERIAL_RE.fullmatch(value) is None:
        raise ValueError("ADB serial is invalid or unbounded")
    return value


def _adb_tool(value: str | Path) -> str:
    path = Path(value)
    if path.name.casefold() not in {"adb", "adb.exe"}:
        raise ValueError("ADB executable identity is not allowlisted")
    return str(path)


def _apk_path(value: Path) -> str:
    path = Path(value)
    if path.suffix.casefold() != ".apk" or "\x00" in str(path):
        raise ValueError("ADB install target must be an APK")
    return str(path)


def _application_id(value: str) -> str:
    if _APP_ID_RE.fullmatch(value) is None:
        raise ValueError("invalid Android application id")
    return value


class AndroidAdbState(StrEnum):
    DEVICE = "device"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    NO_PERMISSIONS = "no_permissions"
    UNKNOWN = "unknown"


class AndroidOrientation(StrEnum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class AndroidNetworkProfile(StrEnum):
    DEFAULT = "default"
    OFFLINE = "offline"
    WIFI = "wifi"


@dataclass(frozen=True, slots=True)
class AndroidDeviceObservation:
    serial: str
    state: AndroidAdbState
    product: str | None = None
    model: str | None = None
    device: str | None = None
    transport_id: str | None = None

    def __post_init__(self) -> None:
        _serial(self.serial)
        for field_name in ("product", "model", "device", "transport_id"):
            value = getattr(self, field_name)
            if value is not None and (
                not value
                or len(value) > 128
                or "\x00" in value
                or any(ch.isspace() for ch in value)
            ):
                raise ValueError(f"{field_name} must be bounded ADB metadata")

    @property
    def device_sha256(self) -> str:
        return _sha_bytes(("adb-device-v1:" + self.serial).encode("utf-8"))

    @property
    def virtual(self) -> bool:
        return self.serial.startswith("emulator-")

    def public_dict(self) -> dict[str, object]:
        return {
            "device_sha256": self.device_sha256,
            "state": self.state.value,
            "product": self.product,
            "model": self.model,
            "device": self.device,
            "virtual": self.virtual,
        }


@dataclass(frozen=True, slots=True)
class AndroidDeviceCapabilitySnapshot:
    device_sha256: str
    state: AndroidAdbState
    virtual: bool
    boot_completed: bool
    os_version: str
    model: str
    abi: str
    locale: str
    density_dpi: int

    def __post_init__(self) -> None:
        _require_sha(self.device_sha256, "device_sha256")
        if self.state is not AndroidAdbState.DEVICE:
            raise ValueError("capability snapshot requires an online ADB device")
        for field_name in ("os_version", "model", "abi", "locale"):
            value = getattr(self, field_name)
            if not value or len(value) > 128 or "\x00" in value:
                raise ValueError(f"{field_name} must be bounded")
        if not 72 <= self.density_dpi <= 1000:
            raise ValueError("density_dpi outside bounded Android range")

    def to_dict(self) -> dict[str, object]:
        return {
            "device_sha256": self.device_sha256,
            "state": self.state.value,
            "virtual": self.virtual,
            "boot_completed": self.boot_completed,
            "os_version": self.os_version,
            "model": self.model,
            "abi": self.abi,
            "locale": self.locale,
            "density_dpi": self.density_dpi,
        }

    def digest(self) -> str:
        return _sha_bytes(canonical_json_bytes(self.to_dict()))


@dataclass(frozen=True, slots=True)
class AndroidDeviceLease:
    lease_id: str
    device_sha256: str
    artifact_sha256: str
    timeout_seconds: int = 300

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.lease_id):
            raise ValueError("lease_id must be a stable identifier")
        _require_sha(self.device_sha256, "device_sha256")
        _require_sha(self.artifact_sha256, "artifact_sha256")
        if not 1 <= self.timeout_seconds <= 1800:
            raise ValueError("lease timeout outside bounded range")

    def assert_matches(self, observation: AndroidDeviceObservation, artifact_sha256: str) -> None:
        _require_sha(artifact_sha256, "artifact_sha256")
        if observation.state is not AndroidAdbState.DEVICE:
            raise ValueError("device lease cannot target stale/offline device")
        if observation.device_sha256 != self.device_sha256:
            raise ValueError("wrong-device substitution rejected")
        if artifact_sha256 != self.artifact_sha256:
            raise ValueError("artifact substitution rejected")

    def to_dict(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "device_sha256": self.device_sha256,
            "artifact_sha256": self.artifact_sha256,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True, slots=True)
class AndroidDeviceMatrixEntry:
    locale: str
    orientation: AndroidOrientation
    density_dpi: int
    network: AndroidNetworkProfile = AndroidNetworkProfile.DEFAULT

    def __post_init__(self) -> None:
        if _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("invalid Android test locale")
        if not 72 <= self.density_dpi <= 1000:
            raise ValueError("density_dpi outside bounded Android range")

    def to_dict(self) -> dict[str, object]:
        return {
            "locale": self.locale,
            "orientation": self.orientation.value,
            "density_dpi": self.density_dpi,
            "network": self.network.value,
        }


@dataclass(frozen=True, slots=True)
class AndroidInstrumentationResult:
    passed: bool
    tests_run: int
    output_sha256: str

    def __post_init__(self) -> None:
        _require_sha(self.output_sha256, "output_sha256")
        if not 0 <= self.tests_run <= 100_000:
            raise ValueError("tests_run outside bounded range")
        if self.passed and self.tests_run < 1:
            raise ValueError("passing instrumentation requires at least one test")

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "tests_run": self.tests_run,
            "output_sha256": self.output_sha256,
        }


@dataclass(frozen=True, slots=True)
class AndroidDeviceAcceptanceEvidence:
    schema_version: int
    source_sha: str
    runner_os: str
    snapshot: AndroidDeviceCapabilitySnapshot
    lease: AndroidDeviceLease
    test_apk_sha256: str
    test_overlay_sha256: str
    matrix: tuple[AndroidDeviceMatrixEntry, ...]
    instrumentation: AndroidInstrumentationResult
    logcat_sha256: str
    logcat_lines: int
    cleanup_complete: bool
    physical_device_claim: bool = False
    status: str = "pass"

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("R13.6 device evidence schema version must be 1")
        if re.fullmatch(r"[0-9a-f]{40}", self.source_sha) is None:
            raise ValueError("source_sha must be exact lowercase Git SHA")
        if self.runner_os not in {"Linux", "Windows"}:
            raise ValueError("runner_os must be Linux or Windows")
        _require_sha(self.test_apk_sha256, "test_apk_sha256")
        _require_sha(self.test_overlay_sha256, "test_overlay_sha256")
        _require_sha(self.logcat_sha256, "logcat_sha256")
        entries = tuple(self.matrix)
        if not entries or len(entries) > 64:
            raise ValueError("device matrix requires 1..64 entries")
        object.__setattr__(self, "matrix", entries)
        if not 0 <= self.logcat_lines <= 20_000:
            raise ValueError("logcat_lines outside bounded range")
        if self.status != "pass":
            raise ValueError("this evidence type represents accepted device evidence only")
        if self.physical_device_claim:
            raise ValueError("hosted emulator evidence cannot manufacture a physical-device claim")
        if not self.snapshot.virtual or not self.snapshot.boot_completed:
            raise ValueError("R13.6 hosted PASS requires a fully booted virtual device")
        if self.snapshot.device_sha256 != self.lease.device_sha256:
            raise ValueError("lease/snapshot device identity mismatch")
        if not self.instrumentation.passed:
            raise ValueError("R13.6 PASS requires successful instrumentation")
        if not self.cleanup_complete:
            raise ValueError("R13.6 PASS requires owned install cleanup")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "runner_os": self.runner_os,
            "snapshot": self.snapshot.to_dict(),
            "lease": self.lease.to_dict(),
            "test_apk_sha256": self.test_apk_sha256,
            "test_overlay_sha256": self.test_overlay_sha256,
            "matrix": [item.to_dict() for item in self.matrix],
            "instrumentation": self.instrumentation.to_dict(),
            "logcat_sha256": self.logcat_sha256,
            "logcat_lines": self.logcat_lines,
            "cleanup_complete": self.cleanup_complete,
            "physical_device_claim": self.physical_device_claim,
            "status": self.status,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return _sha_bytes(self.canonical_bytes())


def parse_adb_devices(output: str) -> tuple[AndroidDeviceObservation, ...]:
    if "\x00" in output or len(output) > 1_000_000:
        raise ValueError("ADB device listing is invalid or unbounded")
    observations: list[AndroidDeviceObservation] = []
    for raw_line in output.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*") or line == "List of devices attached":
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ValueError("malformed adb devices line")
        serial = _serial(parts[0])
        raw_state = parts[1]
        state = {
            "device": AndroidAdbState.DEVICE,
            "offline": AndroidAdbState.OFFLINE,
            "unauthorized": AndroidAdbState.UNAUTHORIZED,
            "no": AndroidAdbState.NO_PERMISSIONS,
        }.get(raw_state, AndroidAdbState.UNKNOWN)
        metadata: dict[str, str] = {}
        for token in parts[2:]:
            if ":" not in token:
                continue
            key, value = token.split(":", 1)
            if key in {"product", "model", "device", "transport_id"}:
                metadata[key] = value
        observations.append(
            AndroidDeviceObservation(
                serial=serial,
                state=state,
                product=metadata.get("product"),
                model=metadata.get("model"),
                device=metadata.get("device"),
                transport_id=metadata.get("transport_id"),
            )
        )
    observations.sort(key=lambda item: item.device_sha256)
    return tuple(observations)


def select_single_online_emulator(
    observations: Sequence[AndroidDeviceObservation],
) -> AndroidDeviceObservation:
    online = [item for item in observations if item.state is AndroidAdbState.DEVICE and item.virtual]
    if len(online) != 1:
        raise ValueError("expected exactly one online Android emulator")
    return online[0]


def parse_instrumentation_output(output: bytes) -> AndroidInstrumentationResult:
    if len(output) > 4 * 1024 * 1024:
        raise ValueError("instrumentation output exceeds bounded limit")
    text = output.decode("utf-8", errors="replace")
    matches = re.findall(r"OK \((\d+) tests?\)", text)
    failures = "FAILURES!!!" in text or "INSTRUMENTATION_FAILED" in text
    passed = bool(matches) and not failures
    tests_run = int(matches[-1]) if matches else 0
    return AndroidInstrumentationResult(
        passed=passed,
        tests_run=tests_run,
        output_sha256=_sha_bytes(output),
    )


def build_adb_devices_argv(adb: str | Path) -> tuple[str, ...]:
    return (_adb_tool(adb), "devices", "-l")


def build_adb_wait_argv(adb: str | Path, serial: str) -> tuple[str, ...]:
    return (_adb_tool(adb), "-s", _serial(serial), "wait-for-device")


def build_adb_getprop_argv(adb: str | Path, serial: str, prop: str) -> tuple[str, ...]:
    if prop not in _ALLOWED_GETPROPS:
        raise ValueError("Android property is not allowlisted")
    return (_adb_tool(adb), "-s", _serial(serial), "shell", "getprop", prop)


def build_adb_density_argv(adb: str | Path, serial: str) -> tuple[str, ...]:
    return (_adb_tool(adb), "-s", _serial(serial), "shell", "wm", "density")


def build_adb_install_argv(adb: str | Path, serial: str, apk: Path) -> tuple[str, ...]:
    return (_adb_tool(adb), "-s", _serial(serial), "install", "-r", _apk_path(apk))


def build_adb_uninstall_argv(adb: str | Path, serial: str, application_id: str) -> tuple[str, ...]:
    return (_adb_tool(adb), "-s", _serial(serial), "uninstall", _application_id(application_id))


def build_adb_instrument_argv(adb: str | Path, serial: str, component: str) -> tuple[str, ...]:
    if _COMPONENT_RE.fullmatch(component) is None:
        raise ValueError("instrumentation component is invalid")
    return (
        _adb_tool(adb),
        "-s",
        _serial(serial),
        "shell",
        "am",
        "instrument",
        "-w",
        "-r",
        component,
    )


def build_adb_logcat_argv(adb: str | Path, serial: str, *, line_limit: int = 500) -> tuple[str, ...]:
    if not 1 <= line_limit <= 20_000:
        raise ValueError("logcat line limit outside bounded range")
    return (
        _adb_tool(adb),
        "-s",
        _serial(serial),
        "logcat",
        "-d",
        "-t",
        str(line_limit),
    )


def build_adb_emulator_kill_argv(adb: str | Path, serial: str) -> tuple[str, ...]:
    selected = _serial(serial)
    if not selected.startswith("emulator-"):
        raise ValueError("emulator cleanup cannot target a physical device")
    return (_adb_tool(adb), "-s", selected, "emu", "kill")
