from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.contracts import DesktopCapabilityReport, DesktopCapabilityState
from kodepoia.desktop.qt6 import Qt6Adapter, QtAcceptanceResult


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/roadmap/R12_8_QT_ACCEPTANCE.json")
    parser.add_argument("--work", default=".kodepoia/r12_8_qt")
    args = parser.parse_args()
    source_sha = os.environ.get("KODEPOIA_SOURCE_SHA", "").strip()
    work = (ROOT / args.work).resolve()
    staging = work / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    adapter = Qt6Adapter(ROOT, staging)
    result = adapter.run_acceptance(canonical_sample_app())
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(result, DesktopCapabilityReport):
        payload = {
            "source_sha": source_sha,
            "adapter": result.canonical(),
            "diagnostic": adapter.last_diagnostic,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2 if result.state in {DesktopCapabilityState.UNAVAILABLE, DesktopCapabilityState.UNSUPPORTED} else 1
    assert isinstance(result, QtAcceptanceResult)
    payload = result.to_dict()
    payload["source_sha"] = source_sha
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
