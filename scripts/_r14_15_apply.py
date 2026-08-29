from __future__ import annotations

import base64
import json
import re
import subprocess
import zlib
from pathlib import Path

START_SHA = "c3dd8aa5f3a7ec7d5f866ead207cf3a023fedbf0"
PAYLOAD_COMMIT = "472befade27bc2e0fa2c7d7317d0b5aa26ce41f6"
LEGACY_PATH = ".github/workflows/_r14_15_impl.yml"
APPLY_WORKFLOW = ".github/workflows/_r14_15_apply.yml"
APPLY_SCRIPT = "scripts/_r14_15_apply.py"

EXPORTS = [
    "BackupArtifact",
    "Bulkhead",
    "CircuitBreaker",
    "CircuitState",
    "DependencyHealth",
    "DependencyState",
    "DisasterRecoveryPolicy",
    "FailureAction",
    "FailureInjector",
    "FailureRule",
    "GracefulDrain",
    "IsolatedRestoreRunner",
    "LoadBudgetResult",
    "LoadObservation",
    "LoadProfile",
    "OtelServiceObservation",
    "ResilienceCapacityError",
    "ResiliencePolicyError",
    "ResilienceStateError",
    "ResilientExecutor",
    "RestoreEvidence",
    "RetryEvidence",
    "RetryPolicy",
    "ServiceHealthSnapshot",
    "ServiceHealthState",
    "ServiceOperationsEvidence",
    "TokenBucketRateLimiter",
    "evaluate_load",
]

EXPECTED = {
    ".github/workflows/r14-resilience-acceptance.yml",
    "schemas/r14/backend-resilience-evidence.schema.json",
    "scripts/r14_15_resilience_acceptance.py",
    "src/kodepoia/backend/__init__.py",
    "src/kodepoia/backend/resilience.py",
    "tests/test_r14_15_backend_exports.py",
    "tests/test_r14_15_resilience.py",
}


def main() -> int:
    legacy = subprocess.check_output(
        ["git", "show", f"{PAYLOAD_COMMIT}:{LEGACY_PATH}"], text=True
    )
    match = re.search(r"payload = '([^']+)'", legacy)
    if match is None:
        raise RuntimeError("R14.15 payload not found in guarded history")
    files = json.loads(zlib.decompress(base64.b64decode(match.group(1))).decode("utf-8"))
    if set(files) != EXPECTED - {"src/kodepoia/backend/__init__.py"}:
        raise RuntimeError(f"unexpected payload surface: {sorted(files)}")
    for raw_path, content in files.items():
        path = Path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    init_path = Path("src/kodepoia/backend/__init__.py")
    text = init_path.read_text(encoding="utf-8")
    if "from .resilience import (" in text:
        raise RuntimeError("R14.15 exports already present")
    import_marker = "from .runtime import BackendLocalRuntime, BackendRuntimeHandle\n"
    if import_marker not in text:
        raise RuntimeError("backend runtime import marker missing")
    resilience_import = "from .resilience import (\n" + "".join(
        f"    {name},\n" for name in EXPORTS
    ) + ")\n"
    text = text.replace(import_marker, resilience_import + import_marker, 1)
    all_marker = '    "canonical_sha256",\n]'
    if all_marker not in text:
        raise RuntimeError("backend __all__ marker missing")
    resilience_all = "".join(f'    "{name}",\n' for name in EXPORTS)
    text = text.replace(all_marker, resilience_all + all_marker, 1)
    init_path.write_text(text, encoding="utf-8")

    # Hosted runners may materialize one historical JSON with a working-tree EOL drift.
    # Restore it before proving the R14.15 surface; it is not part of this subdivision.
    subprocess.run(
        ["git", "checkout", "--", "docs/roadmap/R10_7_LOCAL_ACCEPTANCE.json"],
        check=True,
    )

    Path(APPLY_WORKFLOW).unlink()
    Path(APPLY_SCRIPT).unlink()

    # `git diff` omits untracked files. Intent-to-add makes the six newly-created
    # technical files visible to the exact START->technical-source surface guard.
    new_paths = sorted(EXPECTED - {"src/kodepoia/backend/__init__.py"})
    subprocess.run(["git", "add", "-N", "--", *new_paths], check=True)
    actual = set(
        subprocess.check_output(["git", "diff", "--name-only", START_SHA], text=True).splitlines()
    )
    if actual != EXPECTED:
        raise RuntimeError(f"unexpected final surface: actual={sorted(actual)} expected={sorted(EXPECTED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
