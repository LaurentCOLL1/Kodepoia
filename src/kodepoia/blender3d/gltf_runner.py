from __future__ import annotations

import json
import platform
import re
import shutil
from pathlib import Path
from typing import Any

from kodepoia.assets.contracts import AssetRevision
from kodepoia.kodegodot.runtime import GodotRuntime

from .errors import BlenderBoundaryError, BlenderProtocolError
from .gltf_bootstrap import GLTF_ACCEPTANCE_BOOTSTRAP_SOURCE, GLTF_EXPORT_BOOTSTRAP_SOURCE
from .gltf_contracts import GltfContainer, GltfExportProfile, make_gltf_export_revision, validate_gltf_source_revision
from .gltf_godot_fixture import GODOT_PROJECT_SOURCE, GODOT_VALIDATOR_SCENE_SOURCE, GODOT_VALIDATOR_SCRIPT_SOURCE
from .gltf_validator import evaluate_roundtrip, validate_gltf_file
from .runner import BlenderRunner, _atomic_write, _is_within, _sha256_file
from .serialization import canonical_json_bytes, canonical_sha256

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPORT_POLICY_VERSION = "r10.10-export-v1"
_ACCEPTANCE_POLICY_VERSION = "r10.10-local-v1"


def _bounded_json(path: Path, *, root: Path, max_bytes: int, schema: str) -> dict[str, Any]:
    candidate = path.resolve(strict=False)
    if not _is_within(candidate, root) or not candidate.is_file() or candidate.stat().st_size > max_bytes:
        raise BlenderProtocolError("R10.10 result is missing, escaped or oversized")
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BlenderProtocolError("R10.10 result is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("schema") != schema or payload.get("version") != 1:
        raise BlenderProtocolError("Unexpected R10.10 result schema/version")
    if payload.get("status") not in {"pass", "fail"} or not isinstance(payload.get("blockers"), list):
        raise BlenderProtocolError("Malformed R10.10 status/blockers")
    return payload


def _process_blockers(process: Any) -> list[str]:
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
    return blockers


def _verify_record(root: Path, record: Any, *, expected: str | None = None) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BlenderProtocolError("artifact record must be an object")
    rel = record.get("path", record.get("filename"))
    if not isinstance(rel, str) or not rel or len(rel) > 4096:
        raise BlenderProtocolError("artifact path is invalid")
    normalized = rel.replace("\\", "/")
    if expected is not None and normalized != expected:
        raise BlenderProtocolError("artifact path does not match fixed R10.10 name")
    relative = Path(normalized)
    if relative.is_absolute() or ".." in relative.parts:
        raise BlenderProtocolError("artifact path escapes staging")
    candidate = (root / relative).resolve(strict=True)
    if not _is_within(candidate, root) or not candidate.is_file() or candidate.is_symlink():
        raise BlenderProtocolError("artifact escapes staging or is not a regular file")
    size = candidate.stat().st_size
    digest = _sha256_file(candidate)
    if record.get("bytes") != size or record.get("sha256") != digest:
        raise BlenderProtocolError("artifact identity mismatch")
    return {"path": normalized, "sha256": digest, "bytes": size, "absolute": candidate}


def _runtime(blender_runner: BlenderRunner, payload: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        blockers.append("runtime_missing")
        return {}
    text = runtime.get("blender_version")
    if not isinstance(text, str):
        blockers.append("blender_version_missing")
    else:
        try:
            from .contracts import BlenderVersion
            if not blender_runner.runtime_policy.supports(BlenderVersion.parse(text)):
                blockers.append("blender_version_unsupported")
        except ValueError:
            blockers.append("blender_version_invalid")
    if runtime.get("background") is not True:
        blockers.append("background_false")
    if runtime.get("online_access") is not False:
        blockers.append("offline_mode_not_confirmed")
    return runtime


class GltfExportRunner:
    """R10.10 governed GLB/glTF export + Blender round-trip runner."""

    def __init__(self, blender_runner: BlenderRunner, *, input_root: Path) -> None:
        self.blender_runner = blender_runner
        self.input_root = input_root.resolve(strict=False)

    def _prepare(self, profile: GltfExportProfile, *, source_sha: str, input_blend: Path) -> Path:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        source = input_blend.resolve(strict=True)
        if not _is_within(source, self.input_root) or not source.is_file() or source.suffix.lower() != ".blend":
            raise BlenderBoundaryError("R10.10 input must be a .blend inside its governed root")
        if _sha256_file(source) != profile.input_blend_sha256:
            raise BlenderBoundaryError("R10.10 input digest does not match profile lineage")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        workspace.mkdir(parents=True, exist_ok=True)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.10 export staging workspace must be empty")
        shutil.copyfile(source, workspace / "input.blend")
        _atomic_write(workspace / "gltf_job.json", canonical_json_bytes({
            "schema": "kodepoia.blender.gltf_job", "version": 1, "source_sha": source_sha,
            "policy_version": _EXPORT_POLICY_VERSION, "profile_digest": profile.digest, "profile": profile.to_dict(),
        }))
        _atomic_write(workspace / "gltf_bootstrap.py", GLTF_EXPORT_BOOTSTRAP_SOURCE.encode("utf-8"))
        return workspace

    def run(self, executable: Path, profile_payload: dict[str, Any], *, source_sha: str, input_blend: Path, source_revision: AssetRevision) -> dict[str, Any]:
        profile = GltfExportProfile.from_dict(profile_payload)
        validate_gltf_source_revision(profile, source_revision)
        workspace = self._prepare(profile, source_sha=source_sha, input_blend=input_blend)
        blender = self.blender_runner.boundary.validate_candidate(executable)
        process = self.blender_runner._run_process(self.blender_runner.boundary.build_job_argv(blender, workspace / "gltf_bootstrap.py"), workspace)
        blockers = _process_blockers(process)
        result: dict[str, Any] | None = None
        try:
            result = _bounded_json(workspace / "gltf_result.json", root=workspace, max_bytes=self.blender_runner.limits.max_result_bytes, schema="kodepoia.blender.gltf_result")
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")
        runtime: dict[str, Any] = {}
        artifact: dict[str, Any] | None = None
        facts: dict[str, Any] | None = None
        report: dict[str, Any] | None = None
        promotion: dict[str, Any] | None = None
        if result is not None:
            runtime = _runtime(self.blender_runner, result, blockers)
            if result.get("profile_digest") != profile.digest:
                blockers.append("profile_digest_mismatch")
            if result.get("input_blend_sha256") != profile.input_blend_sha256:
                blockers.append("input_lineage_mismatch")
            if result.get("status") != "pass":
                blockers.extend(str(item) for item in result.get("blockers", []))
                blockers.append("gltf_execution_failed")
            try:
                output_root = (workspace / "export").resolve(strict=True)
                records = result.get("artifacts")
                if not isinstance(records, list) or not records or len(records) > 128:
                    raise BlenderProtocolError("glTF artifact inventory is malformed")
                verified = [_verify_record(output_root, item) for item in records]
                if sum(int(item["bytes"]) for item in verified) > profile.max_output_bytes:
                    raise BlenderProtocolError("glTF output budget exceeded")
                primary_name = "asset.glb" if profile.container is GltfContainer.GLB else "asset.gltf"
                matching = [item for item in verified if item["path"] == primary_name]
                if result.get("primary") != primary_name or len(matching) != 1:
                    raise BlenderProtocolError("glTF primary artifact mismatch")
                primary = matching[0]
                document, parsed = validate_gltf_file(primary["absolute"], max_bytes=profile.max_output_bytes)
                facts = parsed.to_dict()
                if profile.container is GltfContainer.GLTF_SEPARATE:
                    declared = []
                    for collection in (document.get("buffers", []), document.get("images", [])):
                        if isinstance(collection, list):
                            for item in collection:
                                if isinstance(item, dict) and isinstance(item.get("uri"), str) and not item["uri"].startswith("data:"):
                                    declared.append(item["uri"].replace("\\", "/"))
                    present = {str(item["path"]) for item in verified}
                    if any(uri not in present for uri in declared):
                        raise BlenderProtocolError("separate glTF dependency missing from verified inventory")
                source_facts = result.get("source") if isinstance(result.get("source"), dict) else {}
                imported_facts = result.get("roundtrip") if isinstance(result.get("roundtrip"), dict) else {}
                report = evaluate_roundtrip(profile, source_facts, imported_facts, document)
                if report["status"] != "pass":
                    blockers.extend(str(item) for item in report["blockers"])
                artifact = {key: primary[key] for key in ("path", "sha256", "bytes")}
            except (BlenderProtocolError, OSError, KeyError, TypeError):
                blockers.append("export_validation_failed")
        unique = sorted(set(blockers))
        manifest_base = {
            "schema": "kodepoia.blender.gltf_export_manifest", "version": 1, "source_sha": source_sha,
            "policy_version": _EXPORT_POLICY_VERSION, "profile_digest": profile.digest,
            "input_revision_id": profile.source_revision_id, "status": "pass" if not unique else "block",
            "blockers": unique, "runtime": runtime, "artifact": artifact, "gltf": facts, "roundtrip": report,
            "process": {"returncode": process.returncode, "timed_out": process.timed_out, "cancelled": process.cancelled,
                        "stdout_truncated": process.stdout_truncated, "stderr_truncated": process.stderr_truncated},
        }
        evidence_digest = canonical_sha256(manifest_base)
        if not unique and artifact is not None and profile.container is GltfContainer.GLB:
            revision = make_gltf_export_revision(profile, output_sha256=str(artifact["sha256"]), output_length=int(artifact["bytes"]), source_revision=source_revision, manifest_digest=evidence_digest)
            promotion = revision.manifest_payload()
        return {**manifest_base, "evidence_digest": evidence_digest, "promotion": promotion}


class GltfLocalAcceptanceRunner:
    """REQUIRED real Blender 5.2 + Godot 4.7 interoperability acceptance."""

    def __init__(self, blender_runner: BlenderRunner, *, acceptance_root: Path, godot_timeout: float = 300.0) -> None:
        self.blender_runner = blender_runner
        self.acceptance_root = acceptance_root.resolve(strict=False)
        self.godot_timeout = float(godot_timeout)
        if not 1.0 <= self.godot_timeout <= 900.0:
            raise ValueError("Godot timeout must be between 1 and 900 seconds")

    def _godot_project(self, static_glb: Path, rigged_glb: Path) -> Path:
        root = (self.acceptance_root / "godot").resolve(strict=False)
        if root.exists() and any(root.iterdir()):
            raise BlenderBoundaryError("R10.10 Godot acceptance workspace must be empty")
        (root / "assets").mkdir(parents=True, exist_ok=True)
        _atomic_write(root / "project.godot", GODOT_PROJECT_SOURCE.encode("utf-8"))
        _atomic_write(root / "validator.tscn", GODOT_VALIDATOR_SCENE_SOURCE.encode("utf-8"))
        _atomic_write(root / "validator.gd", GODOT_VALIDATOR_SCRIPT_SOURCE.encode("utf-8"))
        shutil.copyfile(static_glb, root / "assets/static.glb")
        shutil.copyfile(rigged_glb, root / "assets/rigged.glb")
        return root

    def run(self, blender_executable: Path, godot_executable: Path, *, source_sha: str) -> dict[str, Any]:
        if not _SOURCE_SHA_RE.fullmatch(source_sha):
            raise BlenderBoundaryError("source_sha must be a lowercase 40-character Git SHA")
        workspace = self.blender_runner.boundary.staging_root.resolve(strict=False)
        if any(workspace.iterdir()):
            raise BlenderBoundaryError("R10.10 Blender acceptance workspace must be empty")
        _atomic_write(workspace / "gltf_acceptance_bootstrap.py", GLTF_ACCEPTANCE_BOOTSTRAP_SOURCE.encode("utf-8"))
        blender = self.blender_runner.boundary.validate_candidate(blender_executable)
        process = self.blender_runner._run_process(self.blender_runner.boundary.build_job_argv(blender, workspace / "gltf_acceptance_bootstrap.py"), workspace)
        blockers = _process_blockers(process)
        result: dict[str, Any] | None = None
        try:
            result = _bounded_json(workspace / "gltf_acceptance_result.json", root=workspace, max_bytes=self.blender_runner.limits.max_result_bytes, schema="kodepoia.blender.gltf_acceptance_result")
        except BlenderProtocolError:
            blockers.append("result_invalid_or_missing")
        runtime: dict[str, Any] = {}
        static_artifact: dict[str, Any] | None = None
        rigged_artifact: dict[str, Any] | None = None
        static_facts: dict[str, Any] | None = None
        rigged_facts: dict[str, Any] | None = None
        if result is not None:
            runtime = _runtime(self.blender_runner, result, blockers)
            if result.get("status") != "pass":
                blockers.extend(str(item) for item in result.get("blockers", []))
                blockers.append("blender_acceptance_failed")
            try:
                records = result.get("artifacts")
                if not isinstance(records, dict):
                    raise BlenderProtocolError("acceptance artifacts missing")
                static_artifact = _verify_record(workspace, records.get("static"), expected="static.glb")
                rigged_artifact = _verify_record(workspace, records.get("rigged"), expected="rigged.glb")
                static_doc, static_parsed = validate_gltf_file(static_artifact["absolute"], max_bytes=64 * 1024 * 1024)
                rigged_doc, rigged_parsed = validate_gltf_file(rigged_artifact["absolute"], max_bytes=64 * 1024 * 1024)
                static_facts = static_parsed.to_dict(); rigged_facts = rigged_parsed.to_dict()
                if static_parsed.mesh_count < 1 or static_parsed.material_count < 1 or static_parsed.skin_count != 0:
                    blockers.append("static_glb_semantics")
                if rigged_parsed.mesh_count < 1 or rigged_parsed.material_count < 1 or rigged_parsed.skin_count < 1 or rigged_parsed.animation_count < 1 or rigged_parsed.morph_target_count < 1:
                    blockers.append("rigged_glb_semantics")
                if static_doc.get("asset", {}).get("version") != "2.0" or rigged_doc.get("asset", {}).get("version") != "2.0":
                    blockers.append("gltf_version_mismatch")
            except (BlenderProtocolError, OSError, KeyError, TypeError):
                blockers.append("acceptance_glb_validation_failed")

        godot_version: dict[str, Any] | None = None
        godot_import: dict[str, Any] | None = None
        godot_smoke: dict[str, Any] | None = None
        godot_hash: str | None = None
        if static_artifact is not None and rigged_artifact is not None and not blockers:
            try:
                godot = godot_executable.resolve(strict=True)
                if not godot.is_file():
                    raise BlenderBoundaryError("Godot executable must be a regular file")
                godot_hash = _sha256_file(godot)
                project = self._godot_project(static_artifact["absolute"], rigged_artifact["absolute"])
                runtime47 = GodotRuntime(project, executable=str(godot))
                version = runtime47.require_47()
                godot_version = {"raw": version.raw, "major": version.major, "minor": version.minor, "patch": version.patch, "compatible_47": version.compatible_47}
                imported = runtime47.import_project(timeout=self.godot_timeout)
                godot_import = {"returncode": imported.returncode, "timed_out": imported.timed_out, "cancelled": imported.cancelled,
                                "stdout_bytes": len(imported.stdout.encode("utf-8", errors="replace")), "stderr_bytes": len(imported.stderr.encode("utf-8", errors="replace"))}
                if not imported.ok:
                    blockers.append("godot_import_failed")
                else:
                    smoke = runtime47.smoke_project(scene="validator.tscn", quit_after=120, timeout=self.godot_timeout)
                    marker = "KODEPOIA_R10_10_GODOT_PASS" in (smoke.stdout + "\n" + smoke.stderr)
                    godot_smoke = {"returncode": smoke.returncode, "timed_out": smoke.timed_out, "cancelled": smoke.cancelled, "pass_marker": marker,
                                   "stdout_bytes": len(smoke.stdout.encode("utf-8", errors="replace")), "stderr_bytes": len(smoke.stderr.encode("utf-8", errors="replace"))}
                    if not smoke.ok or not marker:
                        blockers.append("godot_semantic_smoke_failed")
            except (OSError, RuntimeError, ValueError, BlenderBoundaryError) as exc:
                blockers.append("godot_acceptance_boundary_error")
                godot_smoke = {"error_type": type(exc).__name__}

        unique = sorted(set(blockers))
        def public(item: dict[str, Any] | None) -> dict[str, Any] | None:
            return None if item is None else {key: item[key] for key in ("path", "sha256", "bytes")}
        evidence: dict[str, Any] = {
            "schema": "kodepoia.r10.gltf_local_acceptance", "version": 1, "source_sha": source_sha,
            "status": "pass" if not unique else "fail", "blockers": unique, "policy_version": _ACCEPTANCE_POLICY_VERSION,
            "platform": {"system": platform.system().lower(), "machine": platform.machine()},
            "blender": {"version": runtime.get("blender_version"), "background": runtime.get("background"), "online_access": runtime.get("online_access"),
                        "executable_sha256": _sha256_file(blender), "process": {"returncode": process.returncode, "timed_out": process.timed_out, "cancelled": process.cancelled,
                        "stdout_bytes": process.stdout_bytes, "stderr_bytes": process.stderr_bytes, "stdout_truncated": process.stdout_truncated, "stderr_truncated": process.stderr_truncated}},
            "fixtures": {"static": {"artifact": public(static_artifact), "gltf": static_facts, "roundtrip": None if result is None else result.get("fixtures", {}).get("static")},
                         "rigged": {"artifact": public(rigged_artifact), "gltf": rigged_facts, "roundtrip": None if result is None else result.get("fixtures", {}).get("rigged")}},
            "godot": {"version": godot_version, "executable_sha256": godot_hash, "import": godot_import, "semantic_smoke": godot_smoke},
        }
        evidence["evidence_digest"] = canonical_sha256(evidence)
        return evidence


def validate_local_acceptance_evidence(payload: dict[str, Any], *, expected_source_sha: str) -> None:
    if payload.get("schema") != "kodepoia.r10.gltf_local_acceptance" or payload.get("version") != 1:
        raise BlenderProtocolError("Unexpected R10.10 local evidence schema/version")
    if payload.get("source_sha") != expected_source_sha or not _SOURCE_SHA_RE.fullmatch(expected_source_sha):
        raise BlenderProtocolError("R10.10 evidence source SHA mismatch")
    if payload.get("status") != "pass" or payload.get("blockers") != []:
        raise BlenderProtocolError("R10.10 evidence is not a clean PASS")
    digest = payload.get("evidence_digest")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise BlenderProtocolError("R10.10 evidence digest is missing")
    basis = dict(payload); basis.pop("evidence_digest", None)
    if canonical_sha256(basis) != digest:
        raise BlenderProtocolError("R10.10 evidence digest mismatch")
    blender = payload.get("blender"); godot = payload.get("godot")
    if not isinstance(blender, dict) or not isinstance(godot, dict):
        raise BlenderProtocolError("R10.10 runtime evidence is malformed")
    if blender.get("background") is not True or blender.get("online_access") is not False:
        raise BlenderProtocolError("R10.10 Blender runtime is not background/offline")
    version = blender.get("version")
    if not isinstance(version, str) or not version.startswith("5.2"):
        raise BlenderProtocolError("R10.10 evidence is not Blender 5.2.x")
    godot_version = godot.get("version")
    if not isinstance(godot_version, dict) or godot_version.get("compatible_47") is not True:
        raise BlenderProtocolError("R10.10 evidence is not Godot 4.7.x")
    if not isinstance(godot.get("import"), dict) or godot["import"].get("returncode") != 0:
        raise BlenderProtocolError("R10.10 Godot import did not pass")
    smoke = godot.get("semantic_smoke")
    if not isinstance(smoke, dict) or smoke.get("returncode") != 0 or smoke.get("pass_marker") is not True:
        raise BlenderProtocolError("R10.10 Godot semantic smoke did not pass")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, dict):
        raise BlenderProtocolError("R10.10 fixture evidence is missing")
    for name in ("static", "rigged"):
        fixture = fixtures.get(name)
        if not isinstance(fixture, dict) or not isinstance(fixture.get("artifact"), dict) or not isinstance(fixture.get("gltf"), dict):
            raise BlenderProtocolError(f"R10.10 {name} fixture evidence is malformed")
        artifact = fixture["artifact"]
        if not isinstance(artifact.get("sha256"), str) or not _SHA256_RE.fullmatch(artifact["sha256"]) or not isinstance(artifact.get("bytes"), int) or artifact["bytes"] < 1:
            raise BlenderProtocolError(f"R10.10 {name} artifact identity is malformed")


def write_gltf_local_evidence(path: Path, evidence: dict[str, Any], *, root: Path) -> Path:
    root = root.resolve(strict=False)
    destination = path if path.is_absolute() else root / path
    destination = destination.resolve(strict=False)
    if not _is_within(destination, root):
        raise BlenderBoundaryError("R10.10 evidence output must remain inside the project root")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(destination, canonical_json_bytes(evidence))
    return destination
