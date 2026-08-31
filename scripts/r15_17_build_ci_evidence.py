from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from kodepoia.tuning.integrated_evidence import (
    REQUIRED_ARTIFACT_KINDS,
    REQUIRED_RUNS,
    WorkflowArtifactBinding,
    WorkflowRunBinding,
    build_ci_evidence,
)


def _parse_run(value: str) -> WorkflowRunBinding:
    parts = value.split("|")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("run must be NAME|RUN_ID|RUN_NUMBER")
    name, run_id, run_number = parts
    try:
        return WorkflowRunBinding(name, int(run_id), int(run_number), "success")
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_artifact(value: str) -> WorkflowArtifactBinding:
    parts = value.split("|")
    if len(parts) != 5:
        raise argparse.ArgumentTypeError(
            "artifact must be KIND|RUN_NAME|ARTIFACT_ID|NAME|SHA256"
        )
    kind, run_name, artifact_id, name, sha256 = parts
    try:
        return WorkflowArtifactBinding(kind, run_name, int(artifact_id), name, sha256)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build exact-head R15.17 CI authority after independent gates pass."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run", action="append", type=_parse_run, required=True)
    parser.add_argument("--artifact", action="append", type=_parse_artifact, required=True)
    parser.add_argument("--output", default="docs/roadmap/R15_17_CI_ACCEPTANCE.json")
    args = parser.parse_args()

    runs = tuple(args.run)
    artifacts = tuple(args.artifact)
    if tuple(item.name for item in runs) != REQUIRED_RUNS:
        parser.error("--run values must appear once each in REQUIRED_RUNS order")
    if tuple(item.kind for item in artifacts) != REQUIRED_ARTIFACT_KINDS:
        parser.error(
            "--artifact values must appear once each in REQUIRED_ARTIFACT_KINDS order"
        )

    evidence = build_ci_evidence(
        source_sha=args.source_sha,
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        runs=runs,
        artifacts=artifacts,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": output.as_posix(),
                "evidence_sha256": evidence.evidence_sha256,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
