from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .errors import BlenderBoundaryError, BlenderProtocolError
from .qa_bootstrap import MESH_QA_BOOTSTRAP_SOURCE
from .qa_contracts import MeshQAProfile
from .qa_engine import evaluate_mesh_qa
from .runner import BlenderRunner, _atomic_write, _is_within, _sha256_file
from .serialization import canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_POLICY_VERSION = "r10.5-v1"


class MeshQARunner:
    """Read-only R10.5 source/evaluated mesh QA through the governed Blender boundary."""

    def __init__(self, blender_runner: BlenderRunner, *, input_root: Path) -> None:
        self.blender_runner = blender_runner
        self.input_root = input_root.resolve(strict=False)

    def _confined_blend(self, path: Path) -> Path:
        candidate = path.resolve(strict=True)
        if not _is_within(candidate, self.input_root) or not candidate.is_file() or candidate.suffix.lower() != ".blend":
            raise BlenderBoundaryError("Mesh QA input must be a .blend file inside its governed root")
        return candidate

    def _prepare(self, profile: MeshQAProfile, *, source_sha: str, input_blend: Path) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.5 staging workspace must be empty")
        source = self._confined_blend(input_blend)
        if _sha256_file(source) != profile.input_blend_sha256:
            raise BlenderBoundaryError("Mesh QA input digest does not match profile lineage")
        shutil.copyfile(source, workspace / "input.blend")
        job = {
            "schema": "kodepoia.blender.mesh_qa_job", "version": 1, "source_sha": source_sha,
            "policy_version": _POLICY_VERSION, "profile_digest": profile.digest,
            "input_blend_sha256": profile.input_blend_sha256, "profile": profile.to_dict(),
        }
        _atomic_write(workspace / "mesh_qa_job.json", canonical_json_bytes(job))
        _atomic_write(workspace / "mesh_qa_bootstrap.py", MESH_QA_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def _load_measurements(self, workspace: Path) -> dict[str, Any]:
        path = (workspace / "mesh_qa_result.json").resolve(strict=False)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("Mesh QA measurements are missing or escaped staging")
        if path.stat().st_size > self.blender_runner.limits.max_result_bytes:
            raise BlenderProtocolError("Mesh QA measurements exceed the result-size limit")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlenderProtocolError("Mesh QA measurements are not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict) or payload.get("schema") != "kodepoia.blender.mesh_qa_measurements" or payload.get("version") != 1:
            raise BlenderProtocolError("Unexpected Mesh QA measurement schema/version")
        if payload.get("status") not in {"pass", "fail"} or not isinstance(payload.get("blockers"), list):
            raise BlenderProtocolError("Malformed Mesh QA measurement status/blockers")
        if not isinstance(payload.get("objects"), dict):
            raise BlenderProtocolError("Mesh QA measurements must contain an objects mapping")
        return payload

    def run(self, executable: Path, profile_payload: dict[str, Any], *, source_sha: str, input_blend: Path) -> dict[str, Any]:
        profile = MeshQAProfile.from_dict(profile_payload)
        workspace = self._prepare(profile, source_sha=source_sha, input_blend=input_blend)
        blender = self.blender_runner.boundary.validate_candidate(executable)
        argv = self.blender_runner.boundary.build_job_argv(blender, workspace / "mesh_qa_bootstrap.py")
        process = self.blender_runner._run_process(argv, workspace)
        blockers: list[str] = []
        if process.timed_out: blockers.append("process_timed_out")
        if process.cancelled: blockers.append("process_cancelled")
        if process.stdout_truncated: blockers.append("stdout_limit_exceeded")
        if process.stderr_truncated: blockers.append("stderr_limit_exceeded")
        if process.returncode != 0 and not (process.timed_out or process.cancelled): blockers.append("process_nonzero")

        staged = workspace / "input.blend"
        if not staged.is_file() or _sha256_file(staged) != profile.input_blend_sha256: blockers.append("input_mutated")
        if any(path.name != "input.blend" for path in workspace.glob("*.blend")): blockers.append("unexpected_blend_output")

        measurements: dict[str, Any] | None = None
        try:
            measurements = self._load_measurements(workspace)
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")
        report: dict[str, Any] | None = None
        if measurements is not None:
            if measurements.get("profile_digest") != profile.digest: blockers.append("profile_digest_mismatch")
            if measurements.get("input_blend_sha256") != profile.input_blend_sha256: blockers.append("input_lineage_mismatch")
            if measurements.get("input_file_sha256") != profile.input_blend_sha256: blockers.append("staged_input_digest_mismatch")
            if measurements.get("status") != "pass":
                blockers.extend(str(item) for item in measurements.get("blockers", []))
                blockers.append("measurement_failed")
            if not blockers:
                try:
                    report = evaluate_mesh_qa(profile, measurements)
                except BlenderProtocolError:
                    blockers.append("qa_report_invalid")
        if report is not None:
            blockers.extend(str(rule["rule_id"]) for rule in report["rules"] if rule["state"] == "BLOCK")
        unique = sorted(set(blockers))
        status = "block" if unique else (str(report["status"]) if report is not None else "block")
        return {
            "schema": "kodepoia.blender.mesh_qa_manifest", "version": 1, "source_sha": source_sha,
            "policy_version": _POLICY_VERSION, "profile_id": profile.profile_id, "profile_digest": profile.digest,
            "input_blend_sha256": profile.input_blend_sha256, "status": status, "blockers": unique,
            "report": report, "report_digest": report.get("report_digest") if report is not None else None,
            "read_only": True,
            "process": {"returncode": process.returncode, "timed_out": process.timed_out, "cancelled": process.cancelled, "stdout_truncated": process.stdout_truncated, "stderr_truncated": process.stderr_truncated},
        }
