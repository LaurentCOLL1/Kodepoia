from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

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
from kodepoia.kodegodot.api import GodotToolAPI
from kodepoia.kodegodot.executor import KodeGodotExecutor
from kodepoia.kodegodot.runtime import GodotRuntime

FIXTURE_RELATIVE = Path("tests/fixtures/r16_10_godot_2d_beta")
MUTATED_SCENES = ("scenes/main.tscn", "scenes/hud.tscn")
UNTRUSTED_RESOURCE = "resources/untrusted_instructions.tres"
MALICIOUS_MARKER = "UNTRUSTED_SHOULD_NOT_RUN"


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


def build_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str,
    godot_executable: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    fixture = (repo_root / FIXTURE_RELATIVE).resolve(strict=True)
    if not (fixture / "project.godot").is_file():
        raise FileNotFoundError("R16.10 representative project fixture is missing")

    cases: list[dict[str, Any]] = []
    fixture_digest = _project_digest(fixture)
    resolved_godot = _resolve_godot(godot_executable)
    live: dict[str, Any] = {
        "available": resolved_godot is not None,
        "executable": Path(resolved_godot).name if resolved_godot else None,
        "version": None,
        "compatible_47": None,
        "status": "capability_absent" if resolved_godot is None else "probe_pending",
        "invocations": [],
    }

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-10-") as tmp:
        workspace = Path(tmp) / "project"
        shutil.copytree(fixture, workspace)
        executable = resolved_godot or "godot"
        safe_change = SafeChangeManager(
            workspace, workspace / ".kodepoia" / "snapshots"
        )
        audit = AuditLog(workspace / ".kodepoia" / "audit" / "r16-10.jsonl")
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
        hud_document = executor.invoke(
            "kodegodot_document_parse", {"path": "scenes/hud.tscn"}
        ).result
        main_script = executor.invoke(
            "kodegodot_gdscript_inspect", {"path": "scripts/main.gd"}
        ).result
        hud_script = executor.invoke(
            "kodegodot_gdscript_inspect", {"path": "scripts/hud.gd"}
        ).result
        untrusted_document = executor.invoke(
            "kodegodot_document_parse", {"path": UNTRUSTED_RESOURCE}
        ).result

        dependency_paths = set(main_dependencies.get("dependencies", []))
        expected_dependencies = {
            "res://scripts/main.gd",
            "res://scenes/hud.tscn",
            "res://assets/player.svg",
            "res://resources/player_profile.tres",
        }
        cases.extend(
            [
                _case(
                    "representative-project",
                    project.get("name") == "Kodepoia R16.10 Beta 2D"
                    and int(project.get("scenes", 0)) >= 2
                    and int(project.get("scripts", 0)) >= 2
                    and int(project.get("resources", 0)) >= 2,
                    "repository-owned project exposes multi-file Godot 2D structure",
                ),
                _case(
                    "project-dependencies",
                    expected_dependencies.issubset(dependency_paths),
                    "main scene binds scripts, subscene, imported SVG asset and .tres resource",
                ),
                _case(
                    "public-kodegodot-analysis",
                    bool(main_document)
                    and bool(hud_document)
                    and bool(main_domain)
                    and bool(main_script)
                    and bool(hud_script)
                    and bool(untrusted_document),
                    "public KodeGodot parse/analyze/GDScript paths all returned structured data",
                ),
            ]
        )

        untrusted_text = (workspace / UNTRUSTED_RESOURCE).read_text(encoding="utf-8")
        trust = TrustMetadata.untrusted(
            TrustOrigin.REPOSITORY,
            source=UNTRUSTED_RESOURCE,
            content=untrusted_text,
        )
        boundary = TrustBoundary()
        inspect_decision = boundary.evaluate(trust, AuthorityEffect.INSPECT_DATA)
        process_decision = boundary.evaluate(trust, AuthorityEffect.PROCESS_EXECUTION)
        tool_decision = boundary.evaluate(
            trust, AuthorityEffect.PRIVILEGED_TOOL_TRIGGER
        )
        cases.append(
            _case(
                "untrusted-project-data-boundary",
                MALICIOUS_MARKER in untrusted_text
                and inspect_decision.allowed
                and not process_decision.allowed
                and not tool_decision.allowed,
                "repository instructions remain inspectable data and cannot authorize execution/tools",
            )
        )

        before_project = _project_digest(workspace)
        before_bytes = {
            relative: (workspace / relative).read_bytes()
            for relative in MUTATED_SCENES
        }
        aggregate_snapshot = safe_change.snapshot(
            [workspace / relative for relative in MUTATED_SCENES]
        )
        journal = RecoveryJournal(
            workspace / ".kodepoia" / "recovery" / "r16-10.json"
        )
        checkpoint = journal.save(
            "r16.10-beta-edit",
            "prepared",
            {
                "snapshot": aggregate_snapshot.relative_to(workspace).as_posix(),
                "project_sha256": before_project,
                "paths": list(MUTATED_SCENES),
            },
        )
        loaded = journal.load(
            require_integrity=True,
            expected_task_id="r16.10-beta-edit",
        )

        edit_results: list[dict[str, Any]] = []
        for relative, node, raw_value in (
            ("scenes/main.tscn", "BetaWorld", "3"),
            ("scenes/hud.tscn", "HUD", "2"),
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

        restored_paths = safe_change.restore(aggregate_snapshot)
        restored_project = _project_digest(workspace)
        untrusted_after = (workspace / UNTRUSTED_RESOURCE).read_text(encoding="utf-8")
        journal.clear()

        cases.extend(
            [
                _case(
                    "multi-file-governed-edit",
                    changed_project != before_project
                    and len(edit_results) == 2
                    and all(item["snapshot_created"] for item in edit_results)
                    and diff_text.count("process_mode") >= 4,
                    "two TSCN files changed through SHA-preconditioned public KodeGodot edits",
                ),
                _case(
                    "integrity-bound-recovery-checkpoint",
                    loaded is not None
                    and loaded.integrity_sha256 == checkpoint.integrity_sha256
                    and len(str(checkpoint.integrity_sha256)) == 64,
                    "recovery intent is integrity-bound before mutation",
                ),
                _case(
                    "safechange-rollback",
                    len(restored_paths) == 2
                    and restored_project == before_project
                    and all(
                        (workspace / relative).read_bytes() == before_bytes[relative]
                        for relative in MUTATED_SCENES
                    ),
                    "aggregate SafeChange snapshot restores both modified scene bytes",
                ),
                _case(
                    "negative-control-retained",
                    untrusted_after == untrusted_text
                    and MALICIOUS_MARKER in untrusted_after,
                    "malicious project text remains unchanged data throughout edit/recovery",
                ),
                _case(
                    "audit-chain",
                    audit.verify(),
                    "all governed KodeGodot actions preserve the audit hash chain",
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
                        ("kodegodot_check_script", {"path": "scripts/hud.gd"}),
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
                "godot-capability-probe",
                live_ok,
                "Godot availability/version/live invocations are recorded without inferred PASS",
            )
        )

        static_diagnostics = {
            "project": project,
            "main_document": main_document,
            "main_dependencies": main_dependencies,
            "main_domain": main_domain,
            "hud_document": hud_document,
            "main_script": main_script,
            "hud_script": hud_script,
            "untrusted_document": untrusted_document,
        }
        recovery = {
            "snapshot_manifest_sha256": _file_sha256(
                aggregate_snapshot / "MANIFEST.txt"
            ),
            "checkpoint_integrity_sha256": checkpoint.integrity_sha256,
            "restored_project_sha256": restored_project,
        }

    security_claim = all(bool(item["pass"]) for item in cases)
    semantic_payload = {
        "phase": "R16.10",
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
        "phase": "R16.10",
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
        "pre_change_project_sha256": before_project,
        "changed_project_sha256": changed_project,
        "restored_project_sha256": restored_project,
        "diff_sha256": diff_sha256,
        "diagnostic_sha256": _sha256_payload(static_diagnostics),
        "recovery_sha256": _sha256_payload(recovery),
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
