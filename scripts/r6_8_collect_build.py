from __future__ import annotations

import json
import os
import platform as platform_module
import sys
from pathlib import Path

from kodepoia.quality.build import BuildArtifactKind, BuildStatus, BuildStore, KodeBuild
from kodepoia.quality.ci import CICheck, CICheckStatus, CIStore, KodeCI


WORKFLOW_ID = "r6-8-package-build"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def main() -> int:
    project_root = Path.cwd().resolve(strict=False)
    (project_root / ".kodepoia").mkdir(exist_ok=True)

    source_sha = _required_env("KODEPOIA_SOURCE_SHA")
    build_platform = _required_env("KODEPOIA_BUILD_PLATFORM")
    manifest = KodeBuild.collect(
        project_root,
        source_sha=source_sha,
        platform=build_platform,
        python_version=platform_module.python_version(),
        metadata={
            "collector": "scripts/r6_8_collect_build.py",
            "python_implementation": platform_module.python_implementation(),
            "ci": bool(os.environ.get("CI")),
        },
    )
    build_latest, build_snapshot = BuildStore(project_root).save(manifest)

    by_kind = {artifact.kind: artifact for artifact in manifest.artifacts}
    checks = []
    for kind in (BuildArtifactKind.WHEEL, BuildArtifactKind.SDIST):
        artifact = by_kind.get(kind)
        passed = bool(artifact and artifact.validated)
        checks.append(
            CICheck(
                id=f"package-{kind.value}",
                status=CICheckStatus.PASS if passed else CICheckStatus.FAIL,
                required=True,
                source="KodeBuild",
                message=(artifact.validation if artifact else f"missing {kind.value}"),
                details={
                    "artifact": artifact.name if artifact else None,
                    "sha256": artifact.sha256 if artifact else None,
                },
            )
        )
    report = KodeCI.evaluate(checks, workflow_id=WORKFLOW_ID, source_sha=source_sha)
    ci_latest, ci_snapshot = CIStore(project_root).save(report)

    summary = {
        "source_sha": source_sha.lower(),
        "platform": build_platform,
        "python_version": manifest.python_version,
        "build_status": manifest.status.value,
        "ci_status": report.status.value,
        "artifacts": [artifact.to_dict() for artifact in manifest.artifacts],
        "build_manifest": str(build_latest.relative_to(project_root)),
        "build_snapshot": str(build_snapshot.relative_to(project_root)) if build_snapshot else None,
        "ci_report": str(ci_latest.relative_to(project_root)),
        "ci_snapshot": str(ci_snapshot.relative_to(project_root)) if ci_snapshot else None,
        "build_evidence_sha256": manifest.evidence_sha256,
        "ci_evidence_sha256": report.evidence_sha256,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if manifest.status is BuildStatus.PASS and not report.blocking_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
