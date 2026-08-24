from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .animation_bootstrap import ANIMATION_BOOTSTRAP_SOURCE
from .animation_contracts import RetargetRecipe
from .animation_validator import evaluate_animation_measurements
from .errors import BlenderBoundaryError, BlenderProtocolError
from .runner import BlenderRunner, _atomic_write, _is_within, _sha256_file
from .serialization import canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_POLICY_VERSION = "r10.7-v1"
_OUTPUT_NAME = "animation_output.blend"


class AnimationRunner:
    """Governed R10.7 animation/NLA/retarget executor."""

    def __init__(self, blender_runner: BlenderRunner, *, input_root: Path) -> None:
        self.blender_runner = blender_runner
        self.input_root = input_root.resolve(strict=False)

    def _confined_blend(self, path: Path) -> Path:
        candidate = path.resolve(strict=True)
        if not _is_within(candidate, self.input_root) or not candidate.is_file() or candidate.suffix.lower() != ".blend":
            raise BlenderBoundaryError("Animation input must be a .blend file inside its governed root")
        return candidate

    def _prepare(self, recipe: RetargetRecipe, *, source_sha: str, input_blend: Path) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.7 animation staging workspace must be empty")
        source = self._confined_blend(input_blend)
        if _sha256_file(source) != recipe.input_blend_sha256:
            raise BlenderBoundaryError("Animation input digest does not match recipe lineage")
        shutil.copyfile(source, workspace / "input.blend")
        job = {"schema": "kodepoia.blender.animation_job", "version": 1, "source_sha": source_sha, "policy_version": _POLICY_VERSION, "recipe_digest": recipe.digest, "recipe": recipe.to_dict()}
        _atomic_write(workspace / "animation_job.json", canonical_json_bytes(job))
        _atomic_write(workspace / "animation_bootstrap.py", ANIMATION_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def _load_result(self, workspace: Path) -> dict[str, Any]:
        path = (workspace / "animation_result.json").resolve(strict=False)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("Animation result is missing or escaped staging")
        if path.stat().st_size > self.blender_runner.limits.max_result_bytes:
            raise BlenderProtocolError("Animation result exceeds size limit")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlenderProtocolError("Animation result is not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict) or payload.get("schema") != "kodepoia.blender.animation_measurements" or payload.get("version") != 1:
            raise BlenderProtocolError("Unexpected animation result schema/version")
        if payload.get("status") not in {"pass", "fail"} or not isinstance(payload.get("blockers"), list):
            raise BlenderProtocolError("Malformed animation result status/blockers")
        return payload

    def _verify_output(self, workspace: Path, record: Any) -> dict[str, Any]:
        if not isinstance(record, dict) or record.get("filename") != _OUTPUT_NAME:
            raise BlenderProtocolError("Animation output must be animation_output.blend")
        path = (workspace / _OUTPUT_NAME).resolve(strict=True)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("Animation output escapes staging")
        size = path.stat().st_size
        digest = _sha256_file(path)
        if record.get("bytes") != size or record.get("sha256") != digest:
            raise BlenderProtocolError("Animation output identity mismatch")
        return {"filename": _OUTPUT_NAME, "bytes": size, "sha256": digest}

    def run(self, executable: Path, recipe_payload: dict[str, Any], *, source_sha: str, input_blend: Path) -> dict[str, Any]:
        recipe = RetargetRecipe.from_dict(recipe_payload)
        workspace = self._prepare(recipe, source_sha=source_sha, input_blend=input_blend)
        blender = self.blender_runner.boundary.validate_candidate(executable)
        argv = self.blender_runner.boundary.build_job_argv(blender, workspace / "animation_bootstrap.py")
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
        staged = workspace / "input.blend"
        if not staged.is_file() or _sha256_file(staged) != recipe.input_blend_sha256:
            blockers.append("input_mutated")

        result: dict[str, Any] | None = None
        try:
            result = self._load_result(workspace)
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")

        report: dict[str, Any] | None = None
        artifact: dict[str, Any] | None = None
        if result is not None:
            if result.get("recipe_digest") != recipe.digest:
                blockers.append("recipe_digest_mismatch")
            if result.get("input_blend_sha256") != recipe.input_blend_sha256:
                blockers.append("input_lineage_mismatch")
            if result.get("input_file_sha256") != recipe.input_blend_sha256:
                blockers.append("staged_input_digest_mismatch")
            if result.get("status") != "pass":
                blockers.extend(str(item) for item in result.get("blockers", []))
                blockers.append("animation_execution_failed")
            else:
                try:
                    report = evaluate_animation_measurements(recipe, result)
                    artifact = self._verify_output(workspace, result.get("artifact"))
                except (BlenderProtocolError, OSError):
                    blockers.append("report_or_artifact_invalid")
        if report is not None:
            blockers.extend(str(rule["rule_id"]) for rule in report["rules"] if rule["state"] == "BLOCK")
        unique = sorted(set(blockers))
        status = "block" if unique else (str(report["status"]) if report is not None else "block")
        return {"schema": "kodepoia.blender.animation_manifest", "version": 1, "source_sha": source_sha, "policy_version": _POLICY_VERSION, "recipe_id": recipe.recipe_id, "recipe_digest": recipe.digest, "input_blend_sha256": recipe.input_blend_sha256, "status": status, "blockers": unique, "report": report, "report_digest": report.get("report_digest") if report else None, "artifact": artifact, "lineage": {"parent_sha256": recipe.input_blend_sha256, "derived_sha256": artifact.get("sha256") if artifact else None}, "process": {"returncode": process.returncode, "timed_out": process.timed_out, "cancelled": process.cancelled, "stdout_truncated": process.stdout_truncated, "stderr_truncated": process.stderr_truncated}}
