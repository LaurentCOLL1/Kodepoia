from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.release.corrective_rc import build_corrective_rc_handoff


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the repository-safe R19.5 corrective RC release/TUF handoff"
    )
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--production-signed",
        action="store_true",
        help="claim production Authenticode only when independently verified evidence exists",
    )
    args = parser.parse_args()

    handoff = build_corrective_rc_handoff(
        args.installer,
        source_sha=args.source_sha,
        production_signed=args.production_signed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(handoff.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(handoff.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
