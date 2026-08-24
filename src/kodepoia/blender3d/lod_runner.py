from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from kodepoia.assets.contracts import AssetRevision

from .errors import BlenderBoundaryError, BlenderProtocolError
from .lod_bootstrap import LOD_BOOTSTRAP_SOURCE
from .lod_contracts import LODProfile, make_lod_variant_revision, validate_lod_source_revision
from .lod_validator import evaluate_lod_measurements
from .runner import BlenderRunner, _atomic_write, _is_within, _sha256_file
from .serialization import canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_POLICY_VERSION = "r10.9-v1"


class LODRunner:
    """Governed R10.9 LOD executor layered on the accepted Blender process boundary."""

    def __init__(self, blender_runner: BlenderRunner, *, input_root: Path) -> None:
        self.blender_runner = blender_runner
        self.input_root = input_root.resolve(strict=False)

    def _confined_blend(self, path: Path) -> Path:
        candidate = path.resolve(strict=True)
        if not _is_within(candidate, self.input_root) or not candidate.is_file() or candidate.suffix.lower() != ".blend":
            raise BlenderBoundaryError("LOD input must be a .blend file inside its governed root")
        return candidate

    def _prepare(self, profile: LODProfile, *, source_sha: str, input_blend: Path, source_revision: AssetRevision) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        validate_lod_source_revision(profile, source_revision)
        source = self._confined_blend(input_blend)
        if _sha256_file(source) != profile.input_blend_sha256:
            raise BlenderBoundaryError("LOD input digest does not match profile lineage")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.9 LOD staging workspace must be empty")
        shutil.copyfile(source, workspace / "input.blend")
        job = {"schema": "kodepoia.blender.lod_job", "version": 1, "source_sha": source_sha, "policy_version": _POLICY_VERSION, "profile_digest": profile.digest, "input_blend_sha256": profile.input_blend_sha256, "profile": profile.to_dict()}
        _atomic_write(workspace / "lod_job.json", canonical_json_bytes(job))
        _atomic_write(workspace / "lod_bootstrap.py", LOD_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def _load_result(self, workspace: Path) -> dict[str, Any]:
        path = (workspace / "lod_result.json").resolve(strict=False)
        if not _is_within(path, workspace) or not path.is_file():
            raise BlenderProtocolError("LOD result is missing or escaped staging")
        if path.stat().st_size > self.blender_runner.limits.max_result_bytes:
            raise BlenderProtocolError("LOD result exceeds size limit")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlenderProtocolError("LOD result is not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict) or payload.get("schema") != "kodepoia.blender.lod_measurements" or payload.get("version") != 1:
            raise BlenderProtocolError("Unexpected LOD result schema/version")
        if payload.get("status") not in {"pass", "fail"} or not isinstance(payload.get("blockers"), list):
            raise BlenderProtocolError("Malformed LOD result status/blockers")
        if not isinstance(payload.get("source"), dict) or not isinstance(payload.get("tiers"), dict) or not isinstance(payload.get("artifacts"), list):
            raise BlenderProtocolError("LOD source/tiers/artifacts are malformed")
        return payload

    def _verify_artifacts(self, workspace: Path, profile: LODProfile, records: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(records, list):
            raise BlenderProtocolError("LOD artifacts must be an array")
        expected = {tier.tier_id: tier for tier in profile.tiers}
        result: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict):
                raise BlenderProtocolError("LOD artifact record must be an object")
            tier_id = record.get("tier_id")
            if tier_id not in expected or tier_id in result:
                raise BlenderProtocolError("LOD artifact tier identity mismatch")
            filename = f"lod_{tier_id}.blend"
            if record.get("filename") != filename:
                raise BlenderProtocolError("LOD artifact filename mismatch")
            path = (workspace / filename).resolve(strict=True)
            if not _is_within(path, workspace) or not path.is_file():
                raise BlenderProtocolError("LOD artifact escapes staging")
            size = path.stat().st_size
            digest = _sha256_file(path)
            if record.get("bytes") != size or record.get("sha256") != digest:
                raise BlenderProtocolError("LOD artifact identity mismatch")
            result[str(tier_id)] = {"filename": filename, "bytes": size, "sha256": digest}
        if set(result) != set(expected):
            raise BlenderProtocolError("LOD artifact set is incomplete")
        return result

    def run(self, executable: Path, profile_payload: dict[str, Any], *, source_sha: str, input_blend: Path, source_revision: AssetRevision) -> dict[str, Any]:
        profile = LODProfile.from_dict(profile_payload)
        workspace = self._prepare(profile, source_sha=source_sha, input_blend=input_blend, source_revision=source_revision)
        blender = self.blender_runner.boundary.validate_candidate(executable)
        argv = self.blender_runner.boundary.build_job_argv(blender, workspace / "lod_bootstrap.py")
        process = self.blender_runner._run_process(argv, workspace)
        blockers: list[str] = []
        if process.timed_out: blockers.append("process_timed_out")
        if process.cancelled: blockers.append("process_cancelled")
        if process.stdout_truncated: blockers.append("stdout_limit_exceeded")
        if process.stderr_truncated: blockers.append("stderr_limit_exceeded")
        if process.returncode != 0 and not (process.timed_out or process.cancelled): blockers.append("process_nonzero")
        staged = workspace / "input.blend"
        if not staged.is_file() or _sha256_file(staged) != profile.input_blend_sha256: blockers.append("input_mutated")
        result: dict[str, Any] | None = None
        try:
            result = self._load_result(workspace)
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")
        report: dict[str, Any] | None = None
        artifacts: dict[str, dict[str, Any]] = {}
        if result is not None:
            if result.get("profile_digest") != profile.digest: blockers.append("profile_digest_mismatch")
            if result.get("input_blend_sha256") != profile.input_blend_sha256: blockers.append("input_lineage_mismatch")
            if result.get("input_file_sha256") != profile.input_blend_sha256: blockers.append("staged_input_digest_mismatch")
            if result.get("status") != "pass":
                blockers.extend(str(item) for item in result.get("blockers", []))
                blockers.append("lod_execution_failed")
            else:
                try:
                    report = evaluate_lod_measurements(profile, result)
                    artifacts = self._verify_artifacts(workspace, profile, result.get("artifacts"))
                except (BlenderProtocolError, OSError):
                    blockers.append("report_or_artifact_invalid")
        if report is not None:
            blockers.extend(str(rule["rule_id"]) for rule in report["rules"] if rule["state"] == "BLOCK")
        unique = sorted(set(blockers))
        variants: dict[str, dict[str, Any]] = {}
        if not unique and report is not None:
            by_tier = {tier.tier_id: tier for tier in profile.tiers}
            for tier_id, artifact in artifacts.items():
                revision = make_lod_variant_revision(profile, by_tier[tier_id], output_sha256=str(artifact["sha256"]), output_length=int(artifact["bytes"]), source_revision=source_revision)
                variants[tier_id] = revision.manifest_payload()
        status = "block" if unique else (str(report["status"]) if report is not None else "block")
        return {"schema": "kodepoia.blender.lod_manifest", "version": 1, "source_sha": source_sha, "policy_version": _POLICY_VERSION, "profile_id": profile.profile_id, "profile_digest": profile.digest, "input_blend_sha256": profile.input_blend_sha256, "status": status, "blockers": unique, "report": report, "report_digest": report.get("report_digest") if report else None, "artifacts": artifacts, "variant_revisions": variants, "lineage": {"source_asset_id": profile.source_asset_id, "source_revision_id": profile.source_revision_id, "source_sha256": profile.source_content_sha256}, "process": {"returncode": process.returncode, "timed_out": process.timed_out, "cancelled": process.cancelled, "stdout_truncated": process.stdout_truncated, "stderr_truncated": process.stderr_truncated}}
