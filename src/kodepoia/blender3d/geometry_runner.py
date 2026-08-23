from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .contracts import BlenderProcessLimits
from .errors import BlenderBoundaryError, BlenderProtocolError
from .geometry_bootstrap import GEOMETRY_BOOTSTRAP_SOURCE
from .geometry_contracts import GeometryRecipe
from .runner import BlenderRunner, _atomic_write, _is_within, _sha256_file
from .serialization import canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SCRIPT_NAME = "geometry_bootstrap.py"
_JOB_NAME = "geometry_job.json"
_RESULT_NAME = "geometry_result.json"
_OUTPUT_NAME = "geometry_output.blend"
_POLICY_VERSION = "r10.3-v1"


class GeometryRunner:
    """R10.3 governed geometry executor layered on the accepted BlenderRunner."""

    def __init__(self, blender_runner: BlenderRunner) -> None:
        self.blender_runner = blender_runner

    @property
    def limits(self) -> BlenderProcessLimits:
        return self.blender_runner.limits

    def _prepare(self, recipe: GeometryRecipe, *, source_sha: str) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.3 geometry staging workspace must be empty")
        job = {
            "schema": "kodepoia.blender.geometry_job",
            "version": 1,
            "source_sha": source_sha,
            "policy_version": _POLICY_VERSION,
            "recipe_digest": recipe.digest,
            "recipe": recipe.to_dict(),
        }
        _atomic_write(workspace / _JOB_NAME, canonical_json_bytes(job))
        _atomic_write(workspace / _SCRIPT_NAME, GEOMETRY_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def _load_result(self, workspace: Path) -> dict[str, Any]:
        path = (workspace / _RESULT_NAME).resolve(strict=False)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("Geometry result is missing or escaped staging")
        if path.stat().st_size > self.limits.max_result_bytes:
            raise BlenderProtocolError("Geometry result exceeds size limit")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlenderProtocolError("Geometry result is not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise BlenderProtocolError("Geometry result must be an object")
        if payload.get("schema") != "kodepoia.blender.geometry_result" or payload.get("version") != 1:
            raise BlenderProtocolError("Unexpected geometry result schema/version")
        if payload.get("status") not in {"pass", "fail"}:
            raise BlenderProtocolError("Geometry result status must be pass/fail")
        if not isinstance(payload.get("blockers"), list) or not isinstance(payload.get("objects"), dict):
            raise BlenderProtocolError("Geometry result blockers/objects are malformed")
        return payload

    def _verify_output(self, workspace: Path, record: Any) -> dict[str, object]:
        if not isinstance(record, dict) or record.get("filename") != _OUTPUT_NAME:
            raise BlenderProtocolError("Geometry output artifact must be geometry_output.blend")
        path = (workspace / _OUTPUT_NAME).resolve(strict=True)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("Geometry output artifact escapes staging")
        size = path.stat().st_size
        digest = _sha256_file(path)
        if record.get("bytes") != size or record.get("sha256") != digest:
            raise BlenderProtocolError("Geometry output artifact identity mismatch")
        return {"filename": _OUTPUT_NAME, "bytes": size, "sha256": digest}

    def run(self, executable: Path, recipe_payload: dict[str, Any], *, source_sha: str) -> dict[str, Any]:
        recipe = GeometryRecipe.from_dict(recipe_payload)
        workspace = self._prepare(recipe, source_sha=source_sha)
        blender = self.blender_runner.boundary.validate_candidate(executable)
        argv = self.blender_runner.boundary.build_job_argv(blender, workspace / _SCRIPT_NAME)
        process = self.blender_runner._run_process(argv, workspace)
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

        result: dict[str, Any] | None = None
        try:
            result = self._load_result(workspace)
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")

        objects: dict[str, Any] = {}
        artifact: dict[str, object] | None = None
        if result is not None:
            if result.get("recipe_digest") != recipe.digest:
                blockers.append("recipe_digest_mismatch")
            if result.get("status") != "pass":
                blockers.extend(str(item) for item in result.get("blockers", []))
                blockers.append("geometry_failed")
            else:
                objects = dict(result.get("objects", {}))
                try:
                    artifact = self._verify_output(workspace, result.get("artifact"))
                except (BlenderProtocolError, OSError):
                    blockers.append("artifact_invalid_or_missing")

        unique = sorted(set(blockers))
        return {
            "schema": "kodepoia.blender.geometry_manifest",
            "version": 1,
            "source_sha": source_sha,
            "policy_version": _POLICY_VERSION,
            "recipe_id": recipe.recipe_id,
            "recipe_digest": recipe.digest,
            "status": "pass" if not unique else "fail",
            "blockers": unique,
            "objects": objects,
            "artifact": artifact,
            "process": {
                "returncode": process.returncode,
                "timed_out": process.timed_out,
                "cancelled": process.cancelled,
                "stdout_bytes": process.stdout_bytes,
                "stderr_bytes": process.stderr_bytes,
                "stdout_truncated": process.stdout_truncated,
                "stderr_truncated": process.stderr_truncated,
            },
        }
