from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from kodepoia.assets.boundary import VaultBoundary
from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    ProjectAssetReference,
    ProvenanceRef,
)
from kodepoia.assets.godot_bridge import GodotAssetBridge
from kodepoia.assets.store import VaultStore
from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.trust import (
    AuthorityEffect,
    TrustBoundary,
    TrustMetadata,
    TrustOrigin,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation
from kodepoia.kodegodot.api import GodotToolAPI
from kodepoia.kodegodot.executor import KodeGodotExecutor
from kodepoia.kodegodot.runtime import GodotRuntime

FIXTURE_RELATIVE = Path("tests/fixtures/r16_11_godot_3d_beta")
MUTATED_SCENES = ("scenes/main.tscn", "scenes/prop.tscn")
UNTRUSTED_RESOURCE = "resources/untrusted_metadata.tres"
MALICIOUS_MARKER = "UNTRUSTED_3D_SHOULD_NOT_RUN"
MAX_FIXTURE_FILES = 12
MAX_FIXTURE_BYTES = 64 * 1024
MAX_SINGLE_FILE_BYTES = 16 * 1024


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_payload(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project_digest(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {".godot", ".kodepoia"}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\x00")
        digest.update(path.read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def _resolve_godot(preferred: str | None) -> str | None:
    if preferred == "":
        return None
    if preferred:
        candidate = Path(preferred).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        return shutil.which(preferred)
    for candidate in ("godot", "godot4", "godot4.7"):
        located = shutil.which(candidate)
        if located:
            return located
    return None


def _permissions(workspace: Path, executable: str) -> PermissionSet:
    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.FILE_READ, roots=(workspace,)))
    permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(workspace,)))
    permissions.grant(
        PermissionGrant(
            Capability.PROCESS_EXECUTE,
            executables=(Path(executable).name,),
        )
    )
    return permissions


def _invocation_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "operation": str(result.get("operation", "")),
        "returncode": int(result.get("returncode", -1)),
        "timed_out": bool(result.get("timed_out")),
        "cancelled": bool(result.get("cancelled")),
    }


def _invocation_ok(result: dict[str, Any]) -> bool:
    return (
        int(result.get("returncode", -1)) == 0
        and not bool(result.get("timed_out"))
        and not bool(result.get("cancelled"))
    )


def _fixture_budget(fixture: Path) -> dict[str, Any]:
    files = sorted(item for item in fixture.rglob("*") if item.is_file())
    sizes = {item.relative_to(fixture).as_posix(): item.stat().st_size for item in files}
    return {
        "files": len(files),
        "total_bytes": sum(sizes.values()),
        "max_file_bytes": max(sizes.values(), default=0),
        "sizes": sizes,
    }


def build_3d_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str,
    godot_executable: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    fixture = (repo_root / FIXTURE_RELATIVE).resolve(strict=True)
    if not (fixture / "project.godot").is_file():
        raise FileNotFoundError("R16.11 representative Godot 3D fixture is missing")

    budget = _fixture_budget(fixture)
    fixture_digest = _project_digest(fixture)
    resolved_godot = _resolve_godot(godot_executable)
    cases: list[dict[str, Any]] = []
    live: dict[str, Any] = {
        "available": resolved_godot is not None,
        "executable": Path(resolved_godot).name if resolved_godot else None,
        "version": None,
        "compatible_47": None,
        "status": "capability_absent" if resolved_godot is None else "probe_pending",
        "invocations": [],
    }

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-11-") as tmp:
        temp_root = Path(tmp)
        workspace = temp_root / "project"
        shutil.copytree(fixture, workspace)
        executable = resolved_godot or "godot"
        safe_change = SafeChangeManager(
            workspace, workspace / ".kodepoia" / "snapshots"
        )
        audit = AuditLog(workspace / ".kodepoia" / "audit" / "r16-11.jsonl")
        runtime = GodotRuntime(workspace, executable=executable)
        api = GodotToolAPI(workspace, runtime=runtime)
        executor = KodeGodotExecutor(
            workspace,
            guardian=KodeGuardian(_permissions(workspace, executable)),
            audit=audit,
            safe_change=safe_change,
            api=api,
        )

        project = executor.invoke("kodegodot_project_inspect").result
        main_document = executor.invoke(
            "kodegodot_document_parse", {"path": "scenes/main.tscn"}
        ).result
        main_dependencies = executor.invoke(
            "kodegodot_document_dependencies", {"path": "scenes/main.tscn"}
        ).result
        main_domain = executor.invoke(
            "kodegodot_scene_analyze", {"path": "scenes/main.tscn"}
        ).result
        prop_document = executor.invoke(
            "kodegodot_document_parse", {"path": "scenes/prop.tscn"}
        ).result
        prop_dependencies = executor.invoke(
            "kodegodot_document_dependencies", {"path": "scenes/prop.tscn"}
        ).result
        prop_domain = executor.invoke(
            "kodegodot_scene_analyze", {"path": "scenes/prop.tscn"}
        ).result
        main_script = executor.invoke(
            "kodegodot_gdscript_inspect", {"path": "scripts/main.gd"}
        ).result
        untrusted_document = executor.invoke(
            "kodegodot_document_parse", {"path": UNTRUSTED_RESOURCE}
        ).result

        main_deps = set(main_dependencies.get("dependencies", []))
        prop_deps = set(prop_dependencies.get("dependencies", []))
        prop_subresource_types = {
            str(item.get("resource_type"))
            for item in prop_document.get("sub_resources", [])
        }
        cases.extend(
            [
                _case(
                    "resource-budget",
                    budget["files"] <= MAX_FIXTURE_FILES
                    and budget["total_bytes"] <= MAX_FIXTURE_BYTES
                    and budget["max_file_bytes"] <= MAX_SINGLE_FILE_BYTES,
                    "fixture remains bounded for deterministic hosted-runner acceptance",
                ),
                _case(
                    "representative-3d-project",
                    project.get("name") == "Kodepoia R16.11 Beta 3D"
                    and int(project.get("scenes", 0)) >= 2
                    and int(project.get("scripts", 0)) >= 1
                    and int(project.get("resources", 0)) >= 2,
                    "repository-owned project exposes multi-scene Godot 3D structure",
                ),
                _case(
                    "3d-dependencies",
                    {
                        "res://scripts/main.gd",
                        "res://scenes/prop.tscn",
                        "res://resources/untrusted_metadata.tres",
                    }.issubset(main_deps)
                    and {
                        "res://assets/pillar.obj",
                        "res://materials/pillar_material.tres",
                    }.issubset(prop_deps),
                    "scene dependencies bind script, packed 3D scene, mesh source and material",
                ),
                _case(
                    "public-kodegodot-3d-analysis",
                    main_domain.get("dimension") == "3d"
                    and bool(main_domain.get("cameras"))
                    and bool(main_domain.get("lights"))
                    and prop_domain.get("dimension") == "3d"
                    and bool(prop_domain.get("mesh_nodes"))
                    and bool(prop_domain.get("collision_nodes"))
                    and {"Animation", "AnimationLibrary", "BoxShape3D"}.issubset(
                        prop_subresource_types
                    )
                    and bool(main_script),
                    "public KodeGodot parsing/domain/script surfaces recognize representative 3D composition",
                ),
            ]
        )

        project_boundary = WorkspaceBoundary(workspace)
        vault = VaultStore(VaultBoundary(temp_root / "vault"))
        pillar_path = workspace / "assets" / "pillar.obj"
        asset_id = AssetId.from_seed("r16.11", "assets/pillar.obj")
        revision = vault.ingest(
            project_boundary=project_boundary,
            source_path="assets/pillar.obj",
            asset_id=asset_id,
            kind=AssetKind.MODEL_3D,
            display_name="R16.11 representative pillar mesh",
            provenance=(
                ProvenanceRef(
                    source_kind="repository_fixture",
                    locator=(FIXTURE_RELATIVE / "assets/pillar.obj").as_posix(),
                    evidence_sha256=_file_sha256(pillar_path),
                ),
            ),
        )
        reference = ProjectAssetReference(
            project_id="r16.11-godot-3d-beta",
            asset_id=asset_id,
            revision_id=revision.revision_id,
            target_path="assets/pillar.obj",
            metadata={"role": "representative_3d_mesh"},
        )
        vault.add_project_reference(reference, project_boundary=project_boundary)
        bridge = GodotAssetBridge(workspace, executor)
        captured = bridge.capture_source("assets/pillar.obj", reference=reference)
        positive_portability = bridge.portability_diagnostics((reference,))
        negative_portability = bridge.portability_diagnostics(
            (
                ProjectAssetReference(
                    project_id=reference.project_id,
                    asset_id=reference.asset_id,
                    revision_id=reference.revision_id,
                    target_path="../outside.obj",
                ),
                ProjectAssetReference(
                    project_id=reference.project_id,
                    asset_id=reference.asset_id,
                    revision_id=reference.revision_id,
                    target_path=".godot/imported/pillar.mesh",
                ),
                ProjectAssetReference(
                    project_id=reference.project_id,
                    asset_id=reference.asset_id,
                    revision_id=reference.revision_id,
                ),
            )
        )
        negative_codes = {item.code for item in negative_portability}
        cases.extend(
            [
                _case(
                    "vault-lineage-aware-reference",
                    captured.asset_id == str(asset_id)
                    and captured.revision_id == str(revision.revision_id)
                    and captured.sha256 == revision.content_sha256
                    and bool(revision.provenance)
                    and revision.provenance[0].evidence_sha256 == captured.sha256,
                    "R8 Vault revision identity/provenance stays bound to the materialized Godot mesh source",
                ),
                _case(
                    "workspace-bounded-asset-reference",
                    not positive_portability
                    and {
                        "INVALID_TARGET_PATH",
                        "GENERATED_CACHE_REFERENCE",
                        "MISSING_TARGET_PATH",
                    }.issubset(negative_codes),
                    "valid asset reference stays portable while escape/cache/missing references fail closed",
                ),
            ]
        )
        vault.db.close()

        escaped_dependency_denied = False
        try:
            project_boundary.resolve("../outside/payload.obj")
        except WorkspaceViolation:
            escaped_dependency_denied = True

        untrusted_text = (workspace / UNTRUSTED_RESOURCE).read_text(encoding="utf-8")
        cases.append(
            _case(
                "external-reference-negative-control",
                'metadata/external_reference = "../outside/payload.obj"' in untrusted_text
                and escaped_dependency_denied,
                "external-reference metadata remains project data and cannot cross WorkspaceBoundary",
            )
        )
        trust = TrustMetadata.untrusted(
            TrustOrigin.REPOSITORY,
            source=UNTRUSTED_RESOURCE,
            content=untrusted_text,
        )
        trust_boundary = TrustBoundary()
        inspect_decision = trust_boundary.evaluate(trust, AuthorityEffect.INSPECT_DATA)
        process_decision = trust_boundary.evaluate(
            trust, AuthorityEffect.PROCESS_EXECUTION
        )
        tool_decision = trust_boundary.evaluate(
            trust, AuthorityEffect.PRIVILEGED_TOOL_TRIGGER
        )
        cases.append(
            _case(
                "untrusted-3d-metadata-boundary",
                MALICIOUS_MARKER in untrusted_text
                and bool(untrusted_document)
                and inspect_decision.allowed
                and not process_decision.allowed
                and not tool_decision.allowed,
                "malicious project metadata stays inspectable data and never becomes process/tool authority",
            )
        )

        before_project = _project_digest(workspace)
        before_bytes = {
            relative: (workspace / relative).read_bytes()
            for relative in MUTATED_SCENES
        }

        cancel_snapshot = safe_change.snapshot(
            [workspace / relative for relative in MUTATED_SCENES]
        )
        cancel_edit = executor.invoke(
            "kodegodot_scene_set_existing_property",
            {
                "path": "scenes/main.tscn",
                "node": "Beta3DWorld",
                "property": "process_mode",
                "raw_value": "3",
                "expected_sha256": _file_sha256(workspace / "scenes/main.tscn"),
            },
        )
        cancellation_requested = True
        cancel_restored = safe_change.restore(cancel_snapshot)
        cancel_project = _project_digest(workspace)
        cases.append(
            _case(
                "bounded-cancellation-rollback",
                cancellation_requested
                and bool(cancel_edit.snapshot)
                and len(cancel_restored) == 2
                and cancel_project == before_project
                and all(
                    (workspace / relative).read_bytes() == before_bytes[relative]
                    for relative in MUTATED_SCENES
                ),
                "cancellation between governed 3D edit steps prevents the next mutation "
                "and restores the exact project",
            )
        )

        aggregate_snapshot = safe_change.snapshot(
            [workspace / relative for relative in MUTATED_SCENES]
        )
        journal = RecoveryJournal(
            workspace / ".kodepoia" / "recovery" / "r16-11.json"
        )
        checkpoint = journal.save(
            "r16.11-beta-3d-edit",
            "prepared",
            {
                "snapshot": aggregate_snapshot.relative_to(
                    safe_change.project_root
                ).as_posix(),
                "project_sha256": before_project,
                "paths": list(MUTATED_SCENES),
            },
        )
        loaded = journal.load(
            require_integrity=True,
            expected_task_id="r16.11-beta-3d-edit",
        )

        edit_results: list[dict[str, Any]] = []
        for relative, node, raw_value in (
            ("scenes/main.tscn", "Beta3DWorld", "3"),
            ("scenes/prop.tscn", "RepresentativeProp", "2"),
        ):
            target = workspace / relative
            execution = executor.invoke(
                "kodegodot_scene_set_existing_property",
                {
                    "path": relative,
                    "node": node,
                    "property": "process_mode",
                    "raw_value": raw_value,
                    "expected_sha256": _file_sha256(target),
                },
            )
            edit_results.append(
                {
                    "path": relative,
                    "snapshot_created": bool(execution.snapshot),
                    "result": execution.result,
                }
            )

        changed_project = _project_digest(workspace)
        diff_text_parts: list[str] = []
        for relative in MUTATED_SCENES:
            before = before_bytes[relative].decode("utf-8").splitlines(keepends=True)
            after = (workspace / relative).read_text(encoding="utf-8").splitlines(
                keepends=True
            )
            diff_text_parts.extend(
                difflib.unified_diff(
                    before,
                    after,
                    fromfile=f"a/{relative}",
                    tofile=f"b/{relative}",
                )
            )
        diff_text = "".join(diff_text_parts)
        diff_sha256 = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()

        failure_type: str | None = None
        failure_message = ""
        prop_after_success = (workspace / "scenes/prop.tscn").read_bytes()
        try:
            executor.invoke(
                "kodegodot_scene_set_existing_property",
                {
                    "path": "scenes/prop.tscn",
                    "node": "RepresentativeProp",
                    "property": "process_mode",
                    "raw_value": "1",
                    "expected_sha256": "0" * 64,
                },
            )
        except ValueError as exc:
            failure_type = type(exc).__name__
            failure_message = str(exc)
        prop_after_failure = (workspace / "scenes/prop.tscn").read_bytes()

        restored_paths = safe_change.restore(aggregate_snapshot)
        restored_project = _project_digest(workspace)
        journal.clear()
        cases.extend(
            [
                _case(
                    "multi-file-governed-3d-edit",
                    changed_project != before_project
                    and len(edit_results) == 2
                    and all(item["snapshot_created"] for item in edit_results)
                    and diff_text.count("process_mode") >= 4,
                    "two 3D TSCN files change through SHA-preconditioned public KodeGodot edits",
                ),
                _case(
                    "failed-edit-precondition",
                    failure_type == "ValueError"
                    and "precondition failed" in failure_message
                    and prop_after_failure == prop_after_success,
                    "stale SHA failure is rejected before any second write",
                ),
                _case(
                    "integrity-bound-recovery-checkpoint",
                    loaded is not None
                    and loaded.integrity_sha256 == checkpoint.integrity_sha256
                    and len(str(checkpoint.integrity_sha256)) == 64,
                    "recovery intent is integrity-bound before representative 3D mutation",
                ),
                _case(
                    "safechange-3d-rollback",
                    len(restored_paths) == 2
                    and restored_project == before_project
                    and all(
                        (workspace / relative).read_bytes() == before_bytes[relative]
                        for relative in MUTATED_SCENES
                    ),
                    "aggregate SafeChange restores exact bytes after 3D edit/failure drill",
                ),
                _case(
                    "audit-chain",
                    audit.verify(),
                    "all governed KodeGodot 3D actions preserve the audit hash chain",
                ),
            ]
        )

        if resolved_godot is not None:
            try:
                version = executor.invoke("kodegodot_engine_version").result
                live["version"] = version.get("raw")
                live["compatible_47"] = bool(version.get("compatible_47"))
                if not live["compatible_47"]:
                    live["status"] = "available_incompatible"
                else:
                    live["status"] = "running"
                    for tool_name, arguments in (
                        ("kodegodot_check_script", {"path": "scripts/main.gd"}),
                        ("kodegodot_import_project", {"timeout": 180}),
                        (
                            "kodegodot_smoke_project",
                            {
                                "scene": "scenes/main.tscn",
                                "quit_after": 3,
                                "timeout": 180,
                            },
                        ),
                    ):
                        result = executor.invoke(tool_name, arguments).result
                        live["invocations"].append(_invocation_summary(result))
                    live["status"] = (
                        "pass"
                        if all(_invocation_ok(item) for item in live["invocations"])
                        else "fail"
                    )
            except Exception as exc:
                live["status"] = "probe_failed"
                live["error_type"] = type(exc).__name__

        live_ok = live["status"] in {
            "capability_absent",
            "available_incompatible",
            "pass",
        }
        cases.append(
            _case(
                "godot-3d-capability-probe",
                live_ok,
                "Godot 4.7 availability/version/live 3D invocations are recorded without inferred PASS",
            )
        )

        static_diagnostics = {
            "project": project,
            "main_document": main_document,
            "main_dependencies": main_dependencies,
            "main_domain": main_domain,
            "prop_document": prop_document,
            "prop_dependencies": prop_dependencies,
            "prop_domain": prop_domain,
            "main_script": main_script,
            "untrusted_document": untrusted_document,
            "asset_revision": revision.manifest_payload(),
            "captured_asset": captured.to_dict(),
            "positive_portability": [item.to_dict() for item in positive_portability],
            "negative_portability": [item.to_dict() for item in negative_portability],
            "budget": budget,
        }
        recovery = {
            "cancel_snapshot_manifest_sha256": _file_sha256(
                cancel_snapshot / "MANIFEST.txt"
            ),
            "snapshot_manifest_sha256": _file_sha256(
                aggregate_snapshot / "MANIFEST.txt"
            ),
            "restored_paths": list(MUTATED_SCENES),
            "restored_project_sha256": restored_project,
            "failed_edit_type": failure_type,
        }

    security_claim = all(bool(item["pass"]) for item in cases)
    semantic_payload = {
        "phase": "R16.11",
        "fixture_sha256": fixture_digest,
        "case_results": [
            {"name": item["name"], "pass": item["pass"]} for item in cases
        ],
        "manual_state": "NONE",
        "security_claim": security_claim,
        "critical_veto": not security_claim,
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.11",
        "source_sha": source_sha.lower(),
        "platform": platform,
        "security_claim": security_claim,
        "critical_veto": not security_claim,
        "manual_state": "NONE",
        "network_calls": 0,
        "live_credentials_used": False,
        "destructive_host_actions": False,
        "fixture": FIXTURE_RELATIVE.as_posix(),
        "fixture_sha256": fixture_digest,
        "resource_budget": budget,
        "pre_change_project_sha256": before_project,
        "cancel_restored_project_sha256": cancel_project,
        "changed_project_sha256": changed_project,
        "restored_project_sha256": restored_project,
        "diff_sha256": diff_sha256,
        "diagnostic_sha256": _sha256_payload(static_diagnostics),
        "recovery_sha256": _sha256_payload(recovery),
        "recovery_checkpoint_integrity_sha256": checkpoint.integrity_sha256,
        "asset_revision_id": str(revision.revision_id),
        "asset_content_sha256": revision.content_sha256,
        "trust": {
            "metadata": trust.to_dict(),
            "inspect_data": asdict(inspect_decision),
            "process_execution": asdict(process_decision),
            "privileged_tool_trigger": asdict(tool_decision),
        },
        "live_godot": live,
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(bool(item["pass"]) for item in cases),
            "failed": sum(not bool(item["pass"]) for item in cases),
        },
        "semantic_sha256": _sha256_payload(semantic_payload),
    }
    report["evidence_sha256"] = _sha256_payload(report)
    return report
