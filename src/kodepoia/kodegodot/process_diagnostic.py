from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping

from kodepoia.core.sandbox import ProcessSandbox, _BASE_ENVIRONMENT_KEYS


@dataclass(frozen=True, slots=True)
class ProcessCaseResult:
    name: str
    cwd_kind: str
    environment: str
    capture: str
    returncode: int | None
    elapsed_seconds: float
    timed_out: bool
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return not self.timed_out and self.returncode == 0 and bool((self.stdout or self.stderr).strip())


def _bounded_text(value: str, limit: int = 2048) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[:limit] + "...<truncated>"


def _sanitized_env() -> dict[str, str]:
    return {key: os.environ[key] for key in _BASE_ENVIRONMENT_KEYS if key in os.environ}


def _run_case(
    executable: str,
    *,
    name: str,
    cwd: Path,
    cwd_kind: str,
    environment_name: str,
    env: Mapping[str, str] | None,
    capture: str,
    timeout: float,
) -> ProcessCaseResult:
    started = time.monotonic()
    timed_out = False
    returncode: int | None = None
    stdout = ""
    stderr = ""

    if capture == "pipe":
        process = subprocess.Popen(
            [executable, "--version"],
            cwd=cwd,
            env=None if env is None else dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            stdout, stderr = process.communicate()
        returncode = process.returncode
    elif capture == "file":
        with tempfile.TemporaryFile(mode="w+b") as out_file, tempfile.TemporaryFile(mode="w+b") as err_file:
            process = subprocess.Popen(
                [executable, "--version"],
                cwd=cwd,
                env=None if env is None else dict(env),
                stdout=out_file,
                stderr=err_file,
                shell=False,
            )
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                returncode = process.wait()
            out_file.seek(0)
            err_file.seek(0)
            stdout = out_file.read().decode("utf-8", errors="replace")
            stderr = err_file.read().decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported capture mode: {capture}")

    return ProcessCaseResult(
        name=name,
        cwd_kind=cwd_kind,
        environment=environment_name,
        capture=capture,
        returncode=returncode,
        elapsed_seconds=time.monotonic() - started,
        timed_out=timed_out,
        stdout=_bounded_text(stdout),
        stderr=_bounded_text(stderr),
    )


def run_diagnostic(
    repo_root: Path,
    executable: str,
    *,
    output: Path | None = None,
    timeout: float = 8.0,
) -> dict[str, object]:
    repo_root = repo_root.resolve(strict=True)
    executable_path = Path(executable).resolve(strict=True)
    if not executable_path.is_file():
        raise FileNotFoundError(f"Godot executable is not a file: {executable_path}")
    if not 2.0 <= timeout <= 30.0:
        raise ValueError("Diagnostic timeout must be between 2 and 30 seconds")

    project_dir = repo_root / ".kodepoia" / "r5-acceptance" / "project"
    if not (project_dir / "project.godot").is_file():
        raise FileNotFoundError(
            "R5 acceptance fixture not found. Run r5_accept_local.ps1 -ProbeOnly once before this diagnostic."
        )

    empty_dir = repo_root / ".kodepoia" / "r5-process-diagnostic" / "empty"
    empty_dir.mkdir(parents=True, exist_ok=True)
    for marker in (empty_dir / "project.godot", empty_dir / "project.binary"):
        if marker.exists():
            raise RuntimeError(f"Diagnostic empty directory unexpectedly contains a Godot project marker: {marker}")

    sanitized = _sanitized_env()
    cases = [
        _run_case(
            str(executable_path),
            name="inherited_repo_pipe",
            cwd=repo_root,
            cwd_kind="repo",
            environment_name="inherited",
            env=None,
            capture="pipe",
            timeout=timeout,
        ),
        _run_case(
            str(executable_path),
            name="inherited_project_pipe",
            cwd=project_dir,
            cwd_kind="project",
            environment_name="inherited",
            env=None,
            capture="pipe",
            timeout=timeout,
        ),
        _run_case(
            str(executable_path),
            name="sanitized_empty_pipe",
            cwd=empty_dir,
            cwd_kind="empty",
            environment_name="sanitized",
            env=sanitized,
            capture="pipe",
            timeout=timeout,
        ),
        _run_case(
            str(executable_path),
            name="sanitized_project_pipe",
            cwd=project_dir,
            cwd_kind="project",
            environment_name="sanitized",
            env=sanitized,
            capture="pipe",
            timeout=timeout,
        ),
        _run_case(
            str(executable_path),
            name="sanitized_project_file",
            cwd=project_dir,
            cwd_kind="project",
            environment_name="sanitized",
            env=sanitized,
            capture="file",
            timeout=timeout,
        ),
    ]

    sandbox = ProcessSandbox(project_dir, {executable_path.name})
    started = time.monotonic()
    sandbox_result = sandbox.run([str(executable_path), "--version"], cwd=project_dir, timeout=timeout)
    cases.append(
        ProcessCaseResult(
            name="process_sandbox_project",
            cwd_kind="project",
            environment="sanitized",
            capture="sandbox-pipe",
            returncode=sandbox_result.returncode,
            elapsed_seconds=time.monotonic() - started,
            timed_out=sandbox_result.timed_out,
            stdout=_bounded_text(sandbox_result.stdout),
            stderr=_bounded_text(sandbox_result.stderr),
        )
    )

    payload: dict[str, object] = {
        "metadata": {
            "phase": "R5-godot-process-diagnostic",
            "generated_at": datetime.now(UTC).isoformat(),
            "executable_name": executable_path.name,
            "timeout_seconds": timeout,
            "environment_keys_recorded": False,
            "environment_values_recorded": False,
        },
        "cases": [{**asdict(case), "passed": case.passed} for case in cases],
        "summary": {
            "passed": sum(case.passed for case in cases),
            "failed": sum(not case.passed for case in cases),
            "total": len(cases),
        },
    }

    destination = (output or repo_root / ".kodepoia" / "benchmarks" / "r5-godot-process-diagnostic.json").resolve(strict=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded R5 Windows Godot process-launch diagnostic")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    payload = run_diagnostic(args.repo_root, args.godot, output=args.output, timeout=args.timeout)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
