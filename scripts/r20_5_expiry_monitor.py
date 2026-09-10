from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kodepoia.update.operations_health import build_operations_health_report


def _now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("reference time must include a timezone")
    return parsed.astimezone(UTC).replace(microsecond=0)


def _load_metadata(metadata_dir: Path) -> dict[str, bytes]:
    names = ("root.json", "targets.json", "snapshot.json", "timestamp.json")
    payload: dict[str, bytes] = {}
    for name in names:
        path = metadata_dir / name
        if not path.is_file():
            raise ValueError(f"required metadata file is missing: {path}")
        payload[name] = path.read_bytes()
    return payload


def _load_runs(path: Path) -> Any:
    if not path.is_file():
        raise ValueError(f"workflow run evidence is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _remaining(value: object) -> str:
    if not isinstance(value, int):
        return "n/a"
    sign = "-" if value < 0 else ""
    seconds = abs(value)
    days, seconds = divmod(seconds, 24 * 60 * 60)
    hours, seconds = divmod(seconds, 60 * 60)
    minutes = seconds // 60
    return f"{sign}{days}d {hours}h {minutes}m"


def _summary(report: dict[str, object]) -> str:
    metadata = report.get("metadata")
    workflow = report.get("refresh_workflow")
    lines = [
        "# R20.5 update operations health",
        "",
        f"Overall state: **{str(report.get('state', 'unknown')).upper()}**",
        "",
    ]
    if isinstance(metadata, dict):
        roles = metadata.get("roles")
        if isinstance(roles, dict):
            lines.extend(
                [
                    "| Role | State | Expires | Remaining |",
                    "| --- | --- | --- | ---: |",
                ]
            )
            for role in ("root", "targets", "snapshot", "timestamp"):
                item = roles.get(role)
                if isinstance(item, dict):
                    lines.append(
                        "| {role} | {state} | {expires} | {remaining} |".format(
                            role=role,
                            state=item.get("state", "unknown"),
                            expires=item.get("expires_at", "n/a"),
                            remaining=_remaining(item.get("remaining_seconds")),
                        )
                    )
            lines.append("")
        error = metadata.get("verification_error")
        if error:
            lines.extend([f"Metadata verification: **FAILED** — {error}", ""])
    if isinstance(workflow, dict):
        lines.extend(
            [
                f"R20.4 refresh workflow state: **{str(workflow.get('state', 'unknown')).upper()}**",
                f"Last successful refresh: `{workflow.get('last_success_at') or 'none visible'}`",
                f"Consecutive completed failures: `{workflow.get('consecutive_failures', 0)}`",
                f"Reason: {workflow.get('reason', 'n/a')}",
                "",
            ]
        )
    lines.append(
        "Safety invariant: Kodepoia startup/local work remain available; expired or unverifiable update metadata are never accepted."
    )
    return "\n".join(lines) + "\n"


def _emit_github_feedback(report: dict[str, object]) -> None:
    state = str(report.get("state", "critical"))
    message = "R20.5 update operations health is " + state
    if state == "critical":
        print(f"::error title=R20.5 update operations health::{message}")
    elif state == "warning":
        print(f"::warning title=R20.5 update operations health::{message}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(_summary(report))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R20.5 monitor for TUF metadata lifetime and R20.4 refresh health."
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("update-repository/metadata"),
    )
    parser.add_argument("--workflow-runs", type=Path, required=True)
    parser.add_argument(
        "--reference-time",
        help="UTC/offset ISO-8601 time for deterministic acceptance; defaults to current UTC time.",
    )
    parser.add_argument("--source-sha")
    parser.add_argument(
        "--fail-on",
        choices=("critical", "warning", "never"),
        default="critical",
        help="Exit non-zero at this severity. Production uses critical.",
    )
    args = parser.parse_args()

    try:
        metadata = _load_metadata(args.metadata_dir.resolve())
        report = build_operations_health_report(
            root_bytes=metadata["root.json"],
            targets_bytes=metadata["targets.json"],
            snapshot_bytes=metadata["snapshot.json"],
            timestamp_bytes=metadata["timestamp.json"],
            workflow_runs=_load_runs(args.workflow_runs.resolve()),
            reference_time=_now(args.reference_time),
            source_sha=args.source_sha,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        _emit_github_feedback(report)
        state = str(report["state"])
        if args.fail_on == "critical" and state == "critical":
            return 2
        if args.fail_on == "warning" and state in {"warning", "critical"}:
            return 2
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        print(f"::error title=R20.5 monitor error::{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
