from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Mapping

from .errors import BlenderBoundaryError, BlenderProtocolError
from .pbr_bootstrap import PBR_BOOTSTRAP_SOURCE
from .pbr_contracts import PBRRecipe
from .runner import BlenderRunner, _atomic_write, _is_within, _sha256_file
from .serialization import canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_TEXTURE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})
_POLICY_VERSION = "r10.4-v1"


class PBRRunner:
    """Governed R10.4 UV/PBR executor; recipe data never carries filesystem paths."""

    def __init__(self, blender_runner: BlenderRunner, *, input_root: Path, texture_root: Path) -> None:
        self.blender_runner = blender_runner
        self.input_root = input_root.resolve(strict=False)
        self.texture_root = texture_root.resolve(strict=False)

    def _confined_file(self, path: Path, root: Path, *, label: str) -> Path:
        candidate = path.resolve(strict=True)
        if not _is_within(candidate, root) or not candidate.is_file():
            raise BlenderBoundaryError(f"{label} must resolve to a regular file inside its governed root")
        return candidate

    def _prepare(
        self,
        recipe: PBRRecipe,
        *,
        source_sha: str,
        input_blend: Path,
        texture_bindings: Mapping[str, Path],
    ) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.4 staging workspace must be empty")

        blend = self._confined_file(input_blend, self.input_root, label="input blend")
        if blend.suffix.lower() != ".blend" or _sha256_file(blend) != recipe.input_blend_sha256:
            raise BlenderBoundaryError("Input blend extension/digest does not match the declared recipe lineage")
        shutil.copyfile(blend, workspace / "input.blend")

        expected = recipe.texture_sources
        if set(texture_bindings) != set(expected):
            raise BlenderBoundaryError("Texture bindings must exactly match declared source IDs")
        texture_dir = workspace / "textures"
        texture_dir.mkdir()
        staged: dict[str, dict[str, object]] = {}
        for source_id, digest in sorted(expected.items()):
            source = self._confined_file(texture_bindings[source_id], self.texture_root, label="texture")
            suffix = source.suffix.lower()
            if suffix not in _ALLOWED_TEXTURE_SUFFIXES or _sha256_file(source) != digest:
                raise BlenderBoundaryError("Texture extension/digest does not match declared lineage")
            destination = texture_dir / f"{source_id}{suffix}"
            shutil.copyfile(source, destination)
            staged[source_id] = {"filename": destination.name, "sha256": digest, "bytes": destination.stat().st_size}

        job = {
            "schema": "kodepoia.blender.pbr_job",
            "version": 1,
            "source_sha": source_sha,
            "policy_version": _POLICY_VERSION,
            "recipe_digest": recipe.digest,
            "input_blend_sha256": recipe.input_blend_sha256,
            "textures": staged,
            "recipe": recipe.to_dict(),
        }
        _atomic_write(workspace / "pbr_job.json", canonical_json_bytes(job))
        _atomic_write(workspace / "pbr_bootstrap.py", PBR_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def _load_result(self, workspace: Path) -> dict[str, Any]:
        path = (workspace / "pbr_result.json").resolve(strict=False)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("PBR result is missing or escaped staging")
        if path.stat().st_size > self.blender_runner.limits.max_result_bytes:
            raise BlenderProtocolError("PBR result exceeds the result-size limit")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlenderProtocolError("PBR result is not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict) or payload.get("schema") != "kodepoia.blender.pbr_result" or payload.get("version") != 1:
            raise BlenderProtocolError("Unexpected PBR result schema/version")
        if payload.get("status") not in {"pass", "fail"} or not isinstance(payload.get("blockers"), list):
            raise BlenderProtocolError("Malformed PBR result status/blockers")
        if not isinstance(payload.get("objects"), dict) or not isinstance(payload.get("materials"), dict):
            raise BlenderProtocolError("Malformed PBR object/material evidence")
        return payload

    def _verify_artifact(self, workspace: Path, record: Any) -> dict[str, object]:
        if not isinstance(record, dict) or record.get("filename") != "pbr_output.blend":
            raise BlenderProtocolError("PBR output must be pbr_output.blend")
        path = (workspace / "pbr_output.blend").resolve(strict=True)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("PBR output escapes staging")
        digest = _sha256_file(path)
        size = path.stat().st_size
        if record.get("sha256") != digest or record.get("bytes") != size:
            raise BlenderProtocolError("PBR output artifact identity mismatch")
        return {"filename": path.name, "sha256": digest, "bytes": size}

    def run(
        self,
        executable: Path,
        recipe_payload: dict[str, Any],
        *,
        source_sha: str,
        input_blend: Path,
        texture_bindings: Mapping[str, Path],
    ) -> dict[str, Any]:
        recipe = PBRRecipe.from_dict(recipe_payload)
        workspace = self._prepare(recipe, source_sha=source_sha, input_blend=input_blend, texture_bindings=texture_bindings)
        blender = self.blender_runner.boundary.validate_candidate(executable)
        argv = self.blender_runner.boundary.build_job_argv(blender, workspace / "pbr_bootstrap.py")
        process = self.blender_runner._run_process(argv, workspace)
        blockers: list[str] = []
        if process.timed_out: blockers.append("process_timed_out")
        if process.cancelled: blockers.append("process_cancelled")
        if process.stdout_truncated: blockers.append("stdout_limit_exceeded")
        if process.stderr_truncated: blockers.append("stderr_limit_exceeded")
        if process.returncode != 0 and not (process.timed_out or process.cancelled): blockers.append("process_nonzero")

        result: dict[str, Any] | None = None
        try:
            result = self._load_result(workspace)
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")

        artifact = None
        objects: dict[str, Any] = {}
        materials: dict[str, Any] = {}
        if result is not None:
            if result.get("recipe_digest") != recipe.digest: blockers.append("recipe_digest_mismatch")
            if result.get("input_blend_sha256") != recipe.input_blend_sha256: blockers.append("input_lineage_mismatch")
            if result.get("status") != "pass":
                blockers.extend(str(item) for item in result.get("blockers", []))
                blockers.append("pbr_failed")
            else:
                objects = dict(result.get("objects", {}))
                materials = dict(result.get("materials", {}))
                try:
                    artifact = self._verify_artifact(workspace, result.get("artifact"))
                except (BlenderProtocolError, OSError):
                    blockers.append("artifact_invalid_or_missing")

        unique = sorted(set(blockers))
        return {
            "schema": "kodepoia.blender.pbr_manifest",
            "version": 1,
            "source_sha": source_sha,
            "policy_version": _POLICY_VERSION,
            "recipe_id": recipe.recipe_id,
            "recipe_digest": recipe.digest,
            "input_blend_sha256": recipe.input_blend_sha256,
            "status": "pass" if not unique else "fail",
            "blockers": unique,
            "objects": objects,
            "materials": materials,
            "artifact": artifact,
            "bake": {"requested": False, "executed": False},
            "process": {"returncode": process.returncode, "timed_out": process.timed_out, "cancelled": process.cancelled, "stdout_truncated": process.stdout_truncated, "stderr_truncated": process.stderr_truncated},
        }
