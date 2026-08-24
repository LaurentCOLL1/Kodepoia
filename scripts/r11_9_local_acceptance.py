from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import tempfile
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.media.cinematic.godot_capture import (
    CapturePolicy,
    resolve_executable,
    run_local_capture,
    synthetic_capture_fixture_intent,
    validate_source_sha,
    write_trusted_capture_fixture,
)

FFPROBE_NAMES = frozenset({"ffprobe", "ffprobe.exe"})


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evidence_digest(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _git_head(repo: Path) -> str:
    head_file = repo / ".git" / "HEAD"
    if not head_file.is_file():
        raise RuntimeError("git_metadata_unavailable")
    raw = head_file.read_text(encoding="utf-8").strip()
    if not raw.startswith("ref: "):
        return validate_source_sha(raw)
    ref = raw[5:].strip()
    loose = repo / ".git" / ref
    if loose.is_file():
        return validate_source_sha(loose.read_text(encoding="utf-8").strip())
    packed = repo / ".git" / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or line.startswith("^"):
                continue
            sha, _, name = line.partition(" ")
            if name == ref:
                return validate_source_sha(sha)
    raise RuntimeError("git_head_ref_unresolved")


def _resolve_godot(value: str) -> Path:
    raw = str(value).strip()
    candidate = Path(raw)
    if candidate.exists():
        resolved = candidate.resolve(strict=True)
    else:
        found = shutil.which(raw)
        if not found:
            raise FileNotFoundError("godot_runtime_not_found")
        resolved = Path(found).resolve(strict=True)
    name = resolved.name.casefold()
    if not resolved.is_file() or not name.startswith("godot") or resolved.suffix.casefold() not in {"", ".exe"}:
        raise ValueError("godot_runtime_name_not_allowed")
    return resolved


def _ffprobe_identity(ffprobe: Path, root: Path) -> dict[str, object]:
    runner = ProcessSandbox(root, allowed_executables={ffprobe.name.lower()})
    result = runner.run([str(ffprobe), "-version"], cwd=root, timeout=30.0)
    if result.returncode != 0 or result.timed_out or result.cancelled:
        raise RuntimeError("ffprobe_version_probe_failed")
    first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not first_line.lower().startswith("ffprobe version "):
        raise RuntimeError("ffprobe_version_unrecognized")
    version_token = first_line.split()[2] if len(first_line.split()) >= 3 else "unknown"
    return {"name": ffprobe.name, "version": version_token, "sha256": _sha256_file(ffprobe)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Required local Godot 4.7 cinematic movie-capture acceptance for Kodepoia R11.9")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--ffprobe", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()

    source_sha = validate_source_sha(str(args.source_sha))
    if not 30.0 <= float(args.timeout) <= 900.0:
        raise SystemExit("--timeout must be between 30 and 900 seconds")

    repo = Path(__file__).resolve().parents[1]
    actual_head = _git_head(repo)
    if actual_head != source_sha:
        raise SystemExit(f"Exact-head mismatch: checkout {source_sha} before running the R11.9 collector")

    output = Path(args.output).resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    runtime: dict[str, object] = {}
    fixture_hashes: dict[str, str] = {}
    result: dict[str, object] = {}
    error_type: str | None = None

    try:
        godot = _resolve_godot(str(args.godot))
        ffprobe = resolve_executable(str(args.ffprobe), allowed_names=FFPROBE_NAMES)
        policy = CapturePolicy(width=640, height=360, fps=30, frames=90, max_output_bytes=64 * 1024 * 1024, video_tolerance_frames=1, av_sync_tolerance_frames=2)
        intent = synthetic_capture_fixture_intent(fps=policy.fps, frames=policy.frames)
        runtime = {
            "platform": platform.system(),
            "godot_name": godot.name,
            "godot_sha256": _sha256_file(godot),
            "ffprobe": _ffprobe_identity(ffprobe, repo),
        }
        with tempfile.TemporaryDirectory(prefix="kodepoia-r11-9-") as temp:
            project_root = Path(temp) / "project"
            fixture_hashes = write_trusted_capture_fixture(project_root, policy, intent)
            result = run_local_capture(
                project_root=project_root,
                godot=godot,
                ffprobe=ffprobe,
                policy=policy,
                intent=intent,
                timeout=float(args.timeout),
            )
            runtime["godot_version"] = dict(result.get("godot", {})).get("version")
            runtime["godot_compatible_47"] = dict(result.get("godot", {})).get("compatible_47")
            if runtime["godot_compatible_47"] is not True:
                blockers.append("godot_47_not_confirmed")
            capture = result.get("capture")
            if not isinstance(capture, dict) or capture.get("status") != "pass":
                blockers.append("capture_verification_failed")
    except Exception as exc:  # local evidence must fail closed and remain privacy-minimized
        error_type = type(exc).__name__
        blockers.append("local_capture_exception")

    evidence: dict[str, object] = {
        "schema": "kodepoia.r11_9_local_acceptance",
        "version": 1,
        "source_sha": source_sha,
        "status": "pass" if not blockers else "fail",
        "blockers": sorted(set(blockers)),
        "error_type": error_type,
        "runtime": runtime,
        "fixture": {
            "kind": "repository_synthetic",
            "file_sha256": {key: fixture_hashes[key] for key in sorted(fixture_hashes)},
        },
        "assembly": {
            "sequence_id": result.get("assembly_id"),
            "digest": result.get("assembly_digest"),
            "command_policy_id": result.get("command_policy_id"),
        },
        "capture": result.get("capture"),
    }
    evidence["evidence_digest"] = _evidence_digest(evidence)
    output.write_text(json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if not blockers else 17


if __name__ == "__main__":
    raise SystemExit(main())
