from __future__ import annotations

import contextlib
import ctypes
import json
import os
import platform
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult

from .contracts import (
    CapabilityReport,
    CapabilityState,
    ResourcePreflight,
    RuntimeDisposition,
    RuntimeRequest,
    TrainingBackend,
)

_MAX_CAPTURE_CHARS = 8192
_SECRET_PATTERNS = (
    re.compile(
        r"(?i)(?P<prefix>\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
        r"\s*[:=]\s*['\"]?)(?P<value>[^\s'\"]{4,})"
    ),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?"
        r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?i)\b[A-Z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]*"),
    re.compile(r"(?<![A-Za-z0-9])/(?:home|Users)/[^\s'\"`]+"),
)


class SandboxRunner(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult: ...


@dataclass(frozen=True, slots=True)
class HostResources:
    disk_free_bytes: int | None
    ram_free_bytes: int | None


class HostResourceProbe:
    def sample(self, root: Path) -> HostResources:
        disk_free: int | None
        try:
            disk_free = int(shutil.disk_usage(root).free)
        except OSError:
            disk_free = None
        return HostResources(disk_free, _available_ram_bytes())


def _available_ram_bytes() -> int | None:
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        try:
            ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        except (AttributeError, OSError):
            return None
        return int(status.ullAvailPhys) if ok else None
    try:
        pages = int(os.sysconf("SC_AVPHYS_PAGES"))
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError):
        return None
    return pages * page_size if pages >= 0 and page_size > 0 else None


def redact_runtime_text(text: str) -> str:
    text = str(text)[:_MAX_CAPTURE_CHARS]
    home = str(Path.home())
    if home and len(home) > 2:
        text = text.replace(home, "<redacted:user-home>")
    for pattern in _SECRET_PATTERNS:
        def replacement(match: re.Match[str]) -> str:
            prefix = match.groupdict().get("prefix") if match.groupdict() else None
            return (prefix or "") + "<redacted>"

        text = pattern.sub(replacement, text)
    return text


def _safe_worker_evidence(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("worker output must be an object")
    expected = {
        "backend",
        "backend_capability",
        "device",
        "dtype_supported",
        "four_bit_supported",
        "model_load",
        "packages",
        "python_version",
        "seed_applied",
        "torch_backend_version",
        "vram_free_bytes",
        "vram_total_bytes",
    }
    unknown = set(payload) - expected
    if unknown:
        raise ValueError("worker output contains unsupported fields")
    packages = payload.get("packages", {})
    if not isinstance(packages, dict) or not all(
        isinstance(key, str) and (value is None or isinstance(value, str))
        for key, value in packages.items()
    ):
        raise ValueError("worker packages evidence is invalid")
    device = payload.get("device")
    if device is not None:
        if not isinstance(device, dict):
            raise ValueError("worker device evidence is invalid")
        allowed_device = {"index", "name", "backend_type"}
        if set(device) - allowed_device:
            raise ValueError("worker device contains unsupported fields")
        device = {
            str(key): redact_runtime_text(str(value)) if key == "name" else value
            for key, value in device.items()
        }
    return {
        **payload,
        "device": device,
        "packages": packages,
        "python_version": redact_runtime_text(str(payload.get("python_version", "unknown"))),
        "torch_backend_version": (
            None
            if payload.get("torch_backend_version") is None
            else redact_runtime_text(str(payload["torch_backend_version"]))
        ),
    }


def _host_preflight(request: RuntimeRequest, host: HostResources) -> ResourcePreflight:
    blockers: list[str] = []
    disk_required = request.resources.disk_required_bytes
    ram_required = request.resources.ram_required_bytes

    if disk_required > 0 and host.disk_free_bytes is None:
        blockers.append("storage_budget_unknown")
    elif host.disk_free_bytes is not None and host.disk_free_bytes < disk_required:
        blockers.append("storage_budget_exceeded")

    if ram_required > 0 and host.ram_free_bytes is None:
        blockers.append("ram_budget_unknown")
    elif host.ram_free_bytes is not None and host.ram_free_bytes < ram_required:
        blockers.append("ram_budget_exceeded")

    return ResourcePreflight(
        host.disk_free_bytes,
        host.ram_free_bytes,
        None,
        None,
        tuple(sorted(blockers)),
    )


def _vram_preflight(
    request: RuntimeRequest,
    previous: ResourcePreflight,
    *,
    free_bytes: int | None,
    total_bytes: int | None,
) -> ResourcePreflight:
    blockers = list(previous.blockers)
    if request.backend is TrainingBackend.CPU:
        return ResourcePreflight(
            previous.disk_free_bytes,
            previous.ram_free_bytes,
            None,
            None,
            tuple(blockers),
        )
    required = request.resources.vram_required_free_bytes
    if free_bytes is None or total_bytes is None:
        blockers.append("vram_budget_unknown")
    else:
        policy_total = (
            total_bytes
            if request.resources.vram_total_limit_bytes is None
            else min(total_bytes, request.resources.vram_total_limit_bytes)
        )
        if required > policy_total:
            blockers.append("vram_budget_exceeded")
        elif min(free_bytes, policy_total) < required:
            blockers.append("vram_current_free_insufficient")
    return ResourcePreflight(
        previous.disk_free_bytes,
        previous.ram_free_bytes,
        free_bytes,
        total_bytes,
        tuple(sorted(set(blockers))),
    )


class TrainingRuntime:
    """Bounded R15.8 probe launcher. It never accepts arbitrary command/argv/env input."""

    def __init__(
        self,
        root: Path,
        *,
        kill_switch: KillSwitch | None = None,
        sandbox: SandboxRunner | None = None,
        resource_probe: HostResourceProbe | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.root.mkdir(parents=True, exist_ok=True)
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH
        self.sandbox = sandbox or ProcessSandbox(
            self.root,
            allowed_executables={Path(sys.executable).name},
            kill_switch=self.kill_switch,
        )
        self.resource_probe = resource_probe or HostResourceProbe()

    def probe(self, request: RuntimeRequest) -> CapabilityReport:
        host = self.resource_probe.sample(self.root)
        preflight = _host_preflight(request, host)
        if preflight.blockers:
            return self._budget_blocked(request, preflight)

        first = self._run_worker(request, "probe")
        if isinstance(first, CapabilityReport):
            return first
        evidence, stderr = first
        capability = CapabilityState(str(evidence.get("backend_capability", "unknown")))
        vram_preflight = _vram_preflight(
            request,
            preflight,
            free_bytes=_optional_nonnegative_int(evidence.get("vram_free_bytes")),
            total_bytes=_optional_nonnegative_int(evidence.get("vram_total_bytes")),
        )
        if capability is not CapabilityState.SUPPORTED:
            disposition = (
                RuntimeDisposition.UNSUPPORTED
                if capability is CapabilityState.UNSUPPORTED
                else RuntimeDisposition.FAILED
            )
            return self._report(
                request,
                disposition,
                capability,
                evidence,
                vram_preflight,
                stderr,
                blockers=("backend_unavailable",),
            )
        if vram_preflight.blockers:
            return self._report(
                request,
                RuntimeDisposition.BUDGET_BLOCKED,
                capability,
                evidence,
                vram_preflight,
                stderr,
                blockers=vram_preflight.blockers,
            )
        if request.quantization.value != "none" and evidence.get("four_bit_supported") is not True:
            return self._report(
                request,
                RuntimeDisposition.UNSUPPORTED,
                capability,
                evidence,
                vram_preflight,
                stderr,
                blockers=("four_bit_operation_unsupported",),
            )
        if evidence.get("dtype_supported") is not True:
            return self._report(
                request,
                RuntimeDisposition.UNSUPPORTED,
                capability,
                evidence,
                vram_preflight,
                stderr,
                blockers=("dtype_operation_unsupported",),
            )

        model_state: CapabilityState | None = None
        final_stderr = stderr
        if request.model_load_dry_run:
            second = self._run_worker(request, "model_load")
            if isinstance(second, CapabilityReport):
                return second
            model_evidence, model_stderr = second
            final_stderr = redact_runtime_text("\n".join(filter(None, (stderr, model_stderr))))
            model_raw = model_evidence.get("model_load")
            model_state = CapabilityState(str(model_raw or "unknown"))
            if model_state is not CapabilityState.SUPPORTED:
                return self._report(
                    request,
                    RuntimeDisposition.UNSUPPORTED,
                    capability,
                    {**evidence, "model_load": model_state.value},
                    vram_preflight,
                    final_stderr,
                    blockers=("model_load_dry_run_failed",),
                )

        return self._report(
            request,
            RuntimeDisposition.READY,
            capability,
            {**evidence, "model_load": None if model_state is None else model_state.value},
            vram_preflight,
            final_stderr,
            blockers=(),
        )

    def _run_worker(
        self,
        request: RuntimeRequest,
        action: str,
    ) -> tuple[dict[str, object], str] | CapabilityReport:
        payload = request.worker_payload(action)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="r15_8_",
            dir=self.root,
            delete=False,
        ) as handle:
            config_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        try:
            with contextlib.suppress(OSError):
                config_path.chmod(0o600)
            argv = [sys.executable, "-m", "kodepoia.tuning.probe_worker", config_path.name]
            try:
                result = self.sandbox.run(
                    argv,
                    cwd=self.root,
                    timeout=float(request.timeout_seconds),
                    env={},
                )
            except RuntimeError as exc:
                stderr = redact_runtime_text(str(exc))
                return self._terminal_report(
                    request,
                    RuntimeDisposition.CANCELLED if self.kill_switch.triggered else RuntimeDisposition.FAILED,
                    stderr,
                )
        finally:
            config_path.unlink(missing_ok=True)

        stderr = redact_runtime_text(result.stderr)
        if result.timed_out:
            return self._terminal_report(request, RuntimeDisposition.TIMED_OUT, stderr)
        if result.cancelled:
            return self._terminal_report(request, RuntimeDisposition.CANCELLED, stderr)
        if result.returncode != 0:
            return self._terminal_report(request, RuntimeDisposition.FAILED, stderr)
        try:
            raw = json.loads(result.stdout)
            return _safe_worker_evidence(raw), stderr
        except (json.JSONDecodeError, ValueError, TypeError):
            combined = redact_runtime_text("\n".join(filter(None, (stderr, result.stdout))))
            return self._terminal_report(request, RuntimeDisposition.FAILED, combined)

    def _budget_blocked(self, request: RuntimeRequest, preflight: ResourcePreflight) -> CapabilityReport:
        return CapabilityReport(
            disposition=RuntimeDisposition.BUDGET_BLOCKED,
            request_digest=request.digest,
            backend=request.backend,
            backend_capability=CapabilityState.UNKNOWN,
            dtype_supported=None,
            four_bit_supported=None,
            packages=(),
            python_version=platform.python_version(),
            torch_backend_version=None,
            device=None,
            resources=preflight,
            seed_applied=None,
            model_load=None,
            blockers=preflight.blockers,
        )

    def _terminal_report(
        self,
        request: RuntimeRequest,
        disposition: RuntimeDisposition,
        stderr: str,
    ) -> CapabilityReport:
        return CapabilityReport(
            disposition=disposition,
            request_digest=request.digest,
            backend=request.backend,
            backend_capability=CapabilityState.UNKNOWN,
            dtype_supported=None,
            four_bit_supported=None,
            packages=(),
            python_version=platform.python_version(),
            torch_backend_version=None,
            device=None,
            resources=ResourcePreflight(None, None, None, None),
            seed_applied=None,
            model_load=None,
            blockers=(disposition.value,),
            stderr=stderr,
        )

    def _report(
        self,
        request: RuntimeRequest,
        disposition: RuntimeDisposition,
        capability: CapabilityState,
        evidence: Mapping[str, object],
        resources: ResourcePreflight,
        stderr: str,
        *,
        blockers: tuple[str, ...],
    ) -> CapabilityReport:
        packages_raw = evidence.get("packages", {})
        packages = tuple(
            sorted(
                (str(name), None if version is None else str(version))
                for name, version in dict(packages_raw).items()
            )
        )
        model_raw = evidence.get("model_load")
        return CapabilityReport(
            disposition=disposition,
            request_digest=request.digest,
            backend=request.backend,
            backend_capability=capability,
            dtype_supported=_optional_bool(evidence.get("dtype_supported")),
            four_bit_supported=_optional_bool(evidence.get("four_bit_supported")),
            packages=packages,
            python_version=str(evidence.get("python_version", platform.python_version())),
            torch_backend_version=(
                None
                if evidence.get("torch_backend_version") is None
                else str(evidence["torch_backend_version"])
            ),
            device=None if evidence.get("device") is None else dict(evidence["device"]),
            resources=resources,
            seed_applied=_optional_bool(evidence.get("seed_applied")),
            model_load=None if model_raw is None else CapabilityState(str(model_raw)),
            blockers=tuple(sorted(set(blockers))),
            stderr=redact_runtime_text(stderr),
        )


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _optional_nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
