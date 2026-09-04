from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from kodepoia.quality import integrated_rc_acceptance as base

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_PREPARATIONS = {"none", "build_dist", "release_package"}


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_path(payload: Any, dotted: str) -> Any:
    current = payload
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise base.IntegratedRCAcceptanceError(f"missing phase evidence path: {dotted}")
        current = current[part]
    return current


def _normalized_equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.casefold() == expected.casefold()
    return actual == expected


def _contains_manual_required(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_manual_required(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_manual_required(item) for item in value)
    return isinstance(value, str) and "MANUAL_REQUIRED" in value.upper()


def _critical_veto_present(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("critical_veto") is True:
        return True
    summary = value.get("summary")
    return isinstance(summary, dict) and summary.get("critical_veto") is True


def load_execution_policy(
    path: str | Path,
    *,
    base_policy: dict[str, Any],
) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "policy_id",
        "base_policy_id",
        "require_phase_acceptance",
        "require_phase_source_binding",
        "reject_manual_required",
        "reject_critical_veto",
        "cases",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise base.IntegratedRCAcceptanceError("execution policy schema drifted")
    if payload["schema_version"] != 1:
        raise base.IntegratedRCAcceptanceError("unsupported execution policy schema")
    if payload["base_policy_id"] != base_policy["policy_id"]:
        raise base.IntegratedRCAcceptanceError("execution/base policy authority mismatch")
    for flag in (
        "require_phase_acceptance",
        "require_phase_source_binding",
        "reject_manual_required",
        "reject_critical_veto",
    ):
        if payload[flag] is not True:
            raise base.IntegratedRCAcceptanceError(f"execution policy must require {flag}")

    expected = {(case["id"], case["phase"]) for case in base_policy["cases"]}
    actual: set[tuple[str, str]] = set()
    for case in payload["cases"]:
        if not isinstance(case, dict) or set(case) != {
            "id",
            "phase",
            "script",
            "platform_arg",
            "preparation",
            "verdict",
        }:
            raise base.IntegratedRCAcceptanceError("execution case schema drifted")
        pair = (case["id"], case["phase"])
        if pair in actual:
            raise base.IntegratedRCAcceptanceError(f"duplicate execution case: {pair}")
        actual.add(pair)
        if not isinstance(case["script"], str) or not case["script"].startswith("scripts/r16_"):
            raise base.IntegratedRCAcceptanceError(f"invalid execution script: {pair}")
        if not isinstance(case["platform_arg"], bool):
            raise base.IntegratedRCAcceptanceError(f"platform_arg must be boolean: {pair}")
        if case["preparation"] not in _ALLOWED_PREPARATIONS:
            raise base.IntegratedRCAcceptanceError(f"unsupported preparation: {pair}")
        verdict = case["verdict"]
        if not isinstance(verdict, dict):
            raise base.IntegratedRCAcceptanceError(f"invalid verdict: {pair}")
        if verdict.get("mode") == "path_equals":
            if set(verdict) != {"mode", "path", "value"} or not isinstance(verdict["path"], str):
                raise base.IntegratedRCAcceptanceError(f"invalid path verdict: {pair}")
        elif verdict.get("mode") == "all_true_mapping":
            if set(verdict) != {"mode", "path"} or not isinstance(verdict["path"], str):
                raise base.IntegratedRCAcceptanceError(f"invalid mapping verdict: {pair}")
        else:
            raise base.IntegratedRCAcceptanceError(f"unsupported verdict mode: {pair}")
    if actual != expected:
        raise base.IntegratedRCAcceptanceError("execution policy does not exactly cover base case set")
    return payload


def _execution_case(policy: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [case for case in policy["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise base.IntegratedRCAcceptanceError(f"unknown execution case: {case_id}")
    return matches[0]


def _run(command: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _artifact_hashes(dist: Path) -> dict[str, str]:
    values = {
        path.name: _file_digest(path)
        for path in sorted(dist.iterdir())
        if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    } if dist.is_dir() else {}
    if len(values) != 2 or any(_SHA256_RE.fullmatch(item) is None for item in values.values()):
        raise base.IntegratedRCAcceptanceError(
            "expected exactly one wheel and one sdist with SHA-256 digests"
        )
    return values


def _build_dist(root: Path) -> dict[str, str]:
    shutil.rmtree(root / "dist", ignore_errors=True)
    result = _run(
        [sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", "dist"],
        cwd=root,
        timeout=600,
    )
    if result.returncode != 0:
        raise base.IntegratedRCAcceptanceError(
            "exact-source package build failed: " + (result.stderr or result.stdout)[-2000:]
        )
    return _artifact_hashes(root / "dist")


def _canonicalize_dist(root: Path) -> None:
    result = _run(
        [
            sys.executable,
            "-m",
            "kodepoia.quality.release_package",
            "--dist",
            "dist",
            "--repo-root",
            ".",
            "--source-date-epoch",
            os.environ.get("SOURCE_DATE_EPOCH", "946684800"),
        ],
        cwd=root,
        timeout=300,
    )
    if result.returncode != 0:
        raise base.IntegratedRCAcceptanceError(
            "package canonicalization failed: " + (result.stderr or result.stdout)[-2000:]
        )


def _prepare(
    root: Path,
    *,
    preparation: str,
    phase_dir: Path,
    case_id: str,
    platform: str,
) -> dict[str, Any]:
    if preparation == "none":
        return {}
    if preparation == "build_dist":
        return {"artifact_hashes": _build_dist(root)}
    if preparation != "release_package":
        raise base.IntegratedRCAcceptanceError(f"unsupported preparation: {preparation}")

    _build_dist(root)
    _canonicalize_dist(root)
    baseline = _artifact_hashes(root / "dist")
    baseline_path = phase_dir / f"{case_id}-{platform}.baseline.json"
    baseline_path.write_text(
        json.dumps({"artifacts": baseline}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(root / "dist", ignore_errors=True)
    _build_dist(root)
    _canonicalize_dist(root)
    rebuilt = _artifact_hashes(root / "dist")
    if baseline != rebuilt:
        raise base.IntegratedRCAcceptanceError("same-source canonical RC rebuild is not byte-identical")
    return {
        "artifact_hashes": baseline,
        "baseline_build": baseline_path.as_posix(),
        "same_source_rebuild_identical": True,
    }


def _evaluate_verdict(payload: dict[str, Any], contract: dict[str, Any]) -> bool:
    if contract["mode"] == "path_equals":
        return _normalized_equal(_json_path(payload, contract["path"]), contract["value"])
    value = _json_path(payload, contract["path"])
    return isinstance(value, dict) and bool(value) and all(item is True for item in value.values())


def run_integrated_case(
    repo_root: str | Path,
    *,
    base_policy_path: str | Path,
    execution_policy_path: str | Path,
    source_sha: str,
    case_id: str,
    platform: str,
    evidence_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve(strict=True)
    base_policy = base.load_policy(base_policy_path)
    execution_policy = load_execution_policy(execution_policy_path, base_policy=base_policy)
    contract = _execution_case(execution_policy, case_id)

    base_report = base.run_fresh_case(
        root,
        policy_path=base_policy_path,
        source_sha=source_sha,
        case_id=case_id,
        platform=platform,
    )

    output_root = Path(evidence_dir)
    if not output_root.is_absolute():
        output_root = root / output_root
    phase_dir = output_root / "phase"
    phase_dir.mkdir(parents=True, exist_ok=True)
    script = root / contract["script"]
    if not script.is_file():
        raise base.IntegratedRCAcceptanceError(f"phase acceptance script missing: {contract['script']}")

    prepared = _prepare(
        root,
        preparation=contract["preparation"],
        phase_dir=phase_dir,
        case_id=case_id,
        platform=platform,
    )
    phase_output = phase_dir / f"{case_id}-{platform}.phase.json"
    command = [sys.executable, contract["script"], "--source-sha", source_sha]
    if contract["platform_arg"]:
        command.extend(["--platform", platform])
    if contract["preparation"] == "release_package":
        command.extend(["--baseline-build", prepared["baseline_build"]])
    command.extend(["--output", str(phase_output)])
    executed = _run(command, cwd=root, timeout=1800)

    phase_payload: dict[str, Any] = {}
    if phase_output.is_file():
        loaded = json.loads(phase_output.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            phase_payload = loaded
    source_bound = str(phase_payload.get("source_sha", "")).strip().lower() == source_sha.lower()
    verdict = bool(phase_payload) and _evaluate_verdict(phase_payload, contract["verdict"])
    manual_required = _contains_manual_required(phase_payload)
    critical_veto = _critical_veto_present(phase_payload)
    phase_pass = (
        executed.returncode == 0
        and source_bound
        and verdict
        and not manual_required
        and not critical_veto
    )

    semantic = {
        **{
            key: value
            for key, value in base_report.items()
            if key not in {"semantic_sha256", "stdout_tail", "stderr_tail", "pass"}
        },
        "base_policy_sha256": _digest(base_policy),
        "execution_policy_sha256": _digest(execution_policy),
        "integrated_contract_sha256": _digest(
            {"base_policy": base_policy, "execution_policy": execution_policy}
        ),
        "phase_acceptance_script": contract["script"],
        "phase_acceptance_returncode": executed.returncode,
        "phase_evidence_source_bound": source_bound,
        "phase_evidence_verdict": verdict,
        "phase_manual_required": manual_required,
        "phase_critical_veto": critical_veto,
        "phase_evidence_sha256": _file_digest(phase_output) if phase_output.is_file() else "",
        "preparation": contract["preparation"],
        "artifact_hashes": prepared.get("artifact_hashes", {}),
        "same_source_rebuild_identical": prepared.get("same_source_rebuild_identical"),
        "pass": base_report["pass"] and phase_pass,
    }
    return {
        **semantic,
        "semantic_sha256": _digest(semantic),
        "pytest_stdout_tail": base_report.get("stdout_tail", ""),
        "pytest_stderr_tail": base_report.get("stderr_tail", ""),
        "acceptance_stdout_tail": executed.stdout[-4000:],
        "acceptance_stderr_tail": executed.stderr[-4000:],
    }


def aggregate_integrated_reports(
    *,
    base_policy_path: str | Path,
    execution_policy_path: str | Path,
    source_sha: str,
    reports_dir: str | Path,
) -> dict[str, Any]:
    base_policy = base.load_policy(base_policy_path)
    execution_policy = load_execution_policy(execution_policy_path, base_policy=base_policy)
    summary = base.aggregate_fresh_reports(
        policy_path=base_policy_path,
        source_sha=source_sha,
        reports_dir=reports_dir,
    )
    execution_digest = _digest(execution_policy)
    integrated_digest = _digest(
        {"base_policy": base_policy, "execution_policy": execution_policy}
    )

    directory = Path(reports_dir)
    reports: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "case_id" in payload and "semantic_sha256" in payload:
            reports.append(payload)

    contract_mismatches = sorted(
        f"{item.get('case_id')}@{item.get('platform')}"
        for item in reports
        if item.get("execution_policy_sha256") != execution_digest
        or item.get("integrated_contract_sha256") != integrated_digest
    )
    phase_failures = sorted(
        f"{item.get('case_id')}@{item.get('platform')}"
        for item in reports
        if item.get("phase_evidence_source_bound") is not True
        or item.get("phase_evidence_verdict") is not True
        or item.get("phase_manual_required") is not False
        or item.get("phase_critical_veto") is not False
        or not item.get("phase_evidence_sha256")
    )
    rc_reports = [
        item for item in reports if item.get("case_id") == "r16.17-release-readiness"
    ]
    rc_sets = [item.get("artifact_hashes") for item in rc_reports]
    packages_identical = (
        len(rc_sets) == 2
        and all(isinstance(item, dict) and len(item) == 2 for item in rc_sets)
        and rc_sets[0] == rc_sets[1]
    )

    blockers = list(summary["blockers"])
    if contract_mismatches:
        blockers.append("phase_execution_contract_binding_mismatch")
    if phase_failures:
        blockers.append("phase_acceptance_missing_stale_failed_or_manual")
    if not packages_identical:
        blockers.append("cross_platform_rc_package_bytes_differ_or_missing")
    blockers = list(dict.fromkeys(blockers))

    summary.update(
        {
            "execution_policy_id": execution_policy["policy_id"],
            "execution_policy_sha256": execution_digest,
            "integrated_contract_sha256": integrated_digest,
            "phase_contract_mismatches": contract_mismatches,
            "phase_failures": phase_failures,
            "cross_platform_rc_packages_identical": packages_identical,
            "rc_package_sha256": rc_sets[0] if packages_identical else {},
            "core_manual_required": False,
            "manual_state": "CONDITIONAL_NOT_TRIGGERED",
            "optional_live_capabilities": "NOT_EXERCISED",
            "public_release_performed": False,
            "production_signing_performed": False,
            "production_credentials_used": False,
            "blockers": blockers,
            "critical_veto": bool(blockers),
            "rc_acceptance_claim": not blockers,
            "phase_evidence_sha256": {
                f"{item.get('case_id')}@{item.get('platform')}": item.get("phase_evidence_sha256")
                for item in sorted(
                    reports,
                    key=lambda report: (
                        str(report.get("case_id", "")),
                        str(report.get("platform", "")),
                    ),
                )
            },
        }
    )
    summary.pop("authority_sha256", None)
    summary["authority_sha256"] = _digest(summary)
    return summary
