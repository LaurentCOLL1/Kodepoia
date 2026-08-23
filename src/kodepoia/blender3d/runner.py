from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Any

from kodepoia.core.sandbox import ProcessSandbox

from .boundary import BlenderExecutableBoundary, validate_environment_overrides
from .contracts import BlenderProcessLimits, BlenderRuntimePolicy, BlenderVersion
from .errors import BlenderBoundaryError, BlenderProtocolError
from .probe_bootstrap import PROBE_BOOTSTRAP_SOURCE
from .serialization import canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMAND_POLICY_VERSION = "r10.2-v1"
_PROBE_RESULT_NAME = "probe_result.json"
_BLEND_NAME = "probe.blend"
_GLB_NAME = "probe.glb"
_SCRIPT_NAME = "probe_bootstrap.py"
_JOB_NAME = "probe_job.json"


@dataclass(frozen=True, slots=True)
class RunnerProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    stdout_truncated: bool = False
    stderr_truncated: bool = False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _drain_stream(stream: BinaryIO, limit: int, result: dict[str, object], key: str) -> None:
    stored = bytearray()
    total = 0
    try:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            total += len(chunk)
            room = max(0, limit - len(stored))
            if room:
                stored.extend(chunk[:room])
    except (OSError, ValueError):
        pass
    result[key] = bytes(stored)
    result[key + "_bytes"] = total
    result[key + "_truncated"] = total > limit


class BlenderRunner:
    """Governed R10.2 headless Blender runner backed by ProcessSandbox only."""

    def __init__(
        self,
        boundary: BlenderExecutableBoundary,
        sandbox: ProcessSandbox,
        *,
        limits: BlenderProcessLimits | None = None,
        runtime_policy: BlenderRuntimePolicy | None = None,
    ) -> None:
        self.boundary = boundary
        self.sandbox = sandbox
        self.limits = limits or BlenderProcessLimits()
        self.runtime_policy = runtime_policy or BlenderRuntimePolicy()

    def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
        managed = self.sandbox.spawn_piped(argv, cwd=cwd, env=validate_environment_overrides(None))
        try:
            managed.stdin.close()
            capture: dict[str, object] = {}
            stdout_thread = threading.Thread(
                target=_drain_stream,
                args=(managed.stdout, self.limits.max_stdout_bytes, capture, "stdout"),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=_drain_stream,
                args=(managed.stderr, self.limits.max_stderr_bytes, capture, "stderr"),
                daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()
            deadline = time.monotonic() + self.limits.wall_time_seconds
            timed_out = False
            cancelled = False
            while managed.returncode is None:
                if self.sandbox.kill_switch.triggered:
                    cancelled = True
                    managed.close()
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    managed.close()
                    break
                time.sleep(0.05)
            if managed.returncode is None and not (timed_out or cancelled):
                managed.process.wait(timeout=2.0)
            stdout_thread.join(timeout=2.0)
            stderr_thread.join(timeout=2.0)
            return RunnerProcessResult(
                returncode=managed.returncode if managed.returncode is not None else -1,
                stdout=bytes(capture.get("stdout", b"")).decode("utf-8", errors="replace"),
                stderr=bytes(capture.get("stderr", b"")).decode("utf-8", errors="replace"),
                timed_out=timed_out,
                cancelled=cancelled,
                stdout_bytes=int(capture.get("stdout_bytes", 0)),
                stderr_bytes=int(capture.get("stderr_bytes", 0)),
                stdout_truncated=bool(capture.get("stdout_truncated", False)),
                stderr_truncated=bool(capture.get("stderr_truncated", False)),
            )
        finally:
            managed.close()

    def _prepare_workspace(self, source_sha: str) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        workspace = self.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        existing = [item.name for item in workspace.iterdir()]
        if existing:
            raise BlenderBoundaryError(
                "R10.2 acceptance workspace must be empty; clean only the documented R10.2 workspace first"
            )
        job = {
            "schema": "kodepoia.blender.probe_job",
            "version": 1,
            "source_sha": source_sha,
            "operation": "capability_probe",
            "command_policy_version": _COMMAND_POLICY_VERSION,
        }
        _atomic_write(workspace / _JOB_NAME, canonical_json_bytes(job))
        _atomic_write(workspace / _SCRIPT_NAME, PROBE_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def _load_result(self, workspace: Path) -> dict[str, Any]:
        result_path = (workspace / _PROBE_RESULT_NAME).resolve(strict=False)
        if not _is_within(result_path, workspace):
            raise BlenderProtocolError("Probe result path escapes the workspace")
        if not result_path.is_file():
            raise BlenderProtocolError("Probe result is missing")
        if result_path.stat().st_size > self.limits.max_result_bytes:
            raise BlenderProtocolError("Probe result exceeds the R10.2 result size limit")
        try:
            document = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlenderProtocolError("Probe result is not valid UTF-8 JSON") from exc
        if not isinstance(document, dict):
            raise BlenderProtocolError("Probe result must be a JSON object")
        if document.get("schema") != "kodepoia.blender.probe_result" or document.get("version") != 1:
            raise BlenderProtocolError("Unexpected probe-result schema/version")
        if document.get("status") not in {"pass", "fail"}:
            raise BlenderProtocolError("Probe result status must be pass or fail")
        blockers = document.get("blockers")
        if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
            raise BlenderProtocolError("Probe blockers must be a string array")
        if not isinstance(document.get("facts"), dict) or not isinstance(document.get("artifacts"), dict):
            raise BlenderProtocolError("Probe result facts/artifacts must be objects")
        return document

    def _verify_artifact(self, workspace: Path, record: Any, expected_name: str) -> dict[str, object]:
        if not isinstance(record, dict) or record.get("filename") != expected_name:
            raise BlenderProtocolError(f"Probe artifact must be exactly {expected_name}")
        path = (workspace / expected_name).resolve(strict=True)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError(f"Probe artifact escapes workspace: {expected_name}")
        size = path.stat().st_size
        digest = _sha256_file(path)
        if record.get("bytes") != size or record.get("sha256") != digest:
            raise BlenderProtocolError(f"Probe artifact identity mismatch: {expected_name}")
        return {"sha256": digest, "bytes": size}

    def run_capability_probe(self, executable: Path, *, source_sha: str) -> dict[str, Any]:
        workspace = self._prepare_workspace(source_sha)
        blender = self.boundary.validate_candidate(executable)
        argv = self.boundary.build_job_argv(blender, workspace / _SCRIPT_NAME)
        process = self._run_process(argv, workspace)
        blockers: list[str] = []
        if process.timed_out:
            blockers.append("process_timed_out")
        if process.cancelled:
            blockers.append("process_cancelled")
        if process.stdout_truncated:
            blockers.append("stdout_limit_exceeded")
        if process.stderr_truncated:
            blockers.append("stderr_limit_exceeded")
        if process.returncode != 0 and not (process.timed_out or process.cancelled):
            blockers.append("process_nonzero")

        document: dict[str, Any] | None = None
        try:
            document = self._load_result(workspace)
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")

        facts: dict[str, Any] = document.get("facts", {}) if document else {}
        artifacts: dict[str, object] = {}
        if document is not None:
            for blocker in document.get("blockers", []):
                if blocker not in blockers:
                    blockers.append(blocker)
            if document.get("status") != "pass":
                blockers.append("probe_failed")
            try:
                artifact_records = document.get("artifacts", {})
                artifacts = {
                    "blend": self._verify_artifact(workspace, artifact_records.get("blend"), _BLEND_NAME),
                    "glb": self._verify_artifact(workspace, artifact_records.get("glb"), _GLB_NAME),
                }
            except (BlenderProtocolError, OSError):
                blockers.append("artifact_invalid_or_missing")
                artifacts = {}

        version_text = facts.get("blender_version")
        version: BlenderVersion | None = None
        if isinstance(version_text, str):
            try:
                version = BlenderVersion.parse(version_text)
            except ValueError:
                blockers.append("blender_version_invalid")
        else:
            blockers.append("blender_version_missing")
        if version is not None and not self.runtime_policy.supports(version):
            blockers.append("blender_version_unsupported")
        if facts.get("background") is not True:
            blockers.append("background_false")
        if facts.get("gltf_exporter_available") is not True:
            blockers.append("gltf_exporter_unavailable")
        if facts.get("bmesh_available") is not True:
            blockers.append("bmesh_unavailable")
        if facts.get("online_access") is not False:
            blockers.append("offline_mode_not_confirmed")

        lower_output = (process.stdout + "\n" + process.stderr).lower()
        oom = "out of memory" in lower_output or "std::bad_alloc" in lower_output
        if oom:
            blockers.append("resource_exhausted")
        unique_blockers = sorted(set(blockers))
        runtime = {
            "version": version.canonical() if version is not None else None,
            "python_version": facts.get("python_version") if isinstance(facts.get("python_version"), str) else None,
            "platform": platform.system().lower(),
            "machine": platform.machine(),
            "executable_sha256": _sha256_file(blender),
        }
        return {
            "schema": "kodepoia.r10.local_blender_evidence",
            "version": 1,
            "source_sha": source_sha,
            "status": "pass" if not unique_blockers else "fail",
            "blockers": unique_blockers,
            "runtime": runtime,
            "command_policy": {
                "version": _COMMAND_POLICY_VERSION,
                "background": True,
                "factory_startup": True,
                "autoexec_disabled": True,
                "offline_mode": True,
                "python_exit_code": 17,
                "bootstrap_sha256": hashlib.sha256(PROBE_BOOTSTRAP_SOURCE.encode("utf-8")).hexdigest(),
            },
            "probe": {
                "background": facts.get("background"),
                "online_access": facts.get("online_access"),
                "gltf_exporter_available": facts.get("gltf_exporter_available"),
                "bmesh_available": facts.get("bmesh_available"),
                "object_count": facts.get("object_count"),
                "mesh_count": facts.get("mesh_count"),
                "vertex_count": facts.get("vertex_count"),
                "face_count": facts.get("face_count"),
                "bmesh_vertex_count": facts.get("bmesh_vertex_count"),
            },
            "artifacts": artifacts,
            "process": {
                "returncode": process.returncode,
                "timed_out": process.timed_out,
                "cancelled": process.cancelled,
                "crash": process.returncode not in {0, 17} and not process.timed_out and not process.cancelled,
                "oom": oom,
                "stdout_bytes": process.stdout_bytes,
                "stderr_bytes": process.stderr_bytes,
                "stdout_truncated": process.stdout_truncated,
                "stderr_truncated": process.stderr_truncated,
            },
        }


def write_local_evidence(path: Path, evidence: dict[str, Any], *, root: Path) -> Path:
    root = root.resolve(strict=False)
    destination = path if path.is_absolute() else root / path
    destination = destination.resolve(strict=False)
    if not _is_within(destination, root):
        raise BlenderBoundaryError("R10.2 evidence output must remain inside the project root")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(destination, canonical_json_bytes(evidence))
    return destination
