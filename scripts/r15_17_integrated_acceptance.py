from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from kodepoia.tuning.integrated_acceptance import (
    canonical_json_bytes,
    run_integrated_scenario,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the exact-source R15.17 adversarial integrated scenario."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="kodepoia-r15-17-") as temporary:
        evidence = run_integrated_scenario(args.source_sha, Path(temporary))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(evidence) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
