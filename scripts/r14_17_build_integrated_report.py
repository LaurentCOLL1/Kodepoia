from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from kodepoia.backend.integrated_acceptance import build_repository_report, validate_repository_evidence


def _read_repository_bytes(root: Path, source: str) -> bytes:
    candidate = (root / source).resolve()
    root_resolved = root.resolve()
    if candidate == root_resolved or root_resolved not in candidate.parents:
        raise ValueError(f"repository source escapes root: {source}")
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError(f"repository source is missing or not a regular file: {source}")
    return candidate.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the canonical anti-circular R14 integrated acceptance report.")
    parser.add_argument("--source-sha", required=True, help="Immutable accepted R14.17 technical source SHA")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output", default="docs/roadmap/R14_INTEGRATED_ACCEPTANCE.json")
    args = parser.parse_args()

    root = Path(args.repository_root).resolve()
    read_bytes = lambda source: _read_repository_bytes(root, source)
    report = build_repository_report(
        source_sha=args.source_sha,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        read_bytes=read_bytes,
    )
    validate_repository_evidence(report, read_bytes)

    output = (root / args.output).resolve()
    if output == root or root not in output.parents:
        raise ValueError("output escapes repository root")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.relative_to(root).as_posix(), "evidence_sha256": report.evidence_sha256}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
