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
from kodepoia.desktop.winui3 import (
    WinUi3Adapter,
    WinUiAcceptanceResult,
    canonical_winui_deployment,
    write_winui_acceptance_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/roadmap/R12_6_WINUI_ACCEPTANCE.json")
    parser.add_argument("--work", default=".kodepoia/r12_6_winui")
    args = parser.parse_args()
    expected_sha = os.environ.get("KODEPOIA_SOURCE_SHA", "").strip()
    work = (ROOT / args.work).resolve()
    staging = work / "staging"
    work.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    adapter = WinUi3Adapter(ROOT, staging)
    result = adapter.run_acceptance(canonical_sample_app(), canonical_winui_deployment())
    output = (ROOT / args.output).resolve()
    if isinstance(result, DesktopCapabilityReport):
        payload = {
            "source_sha": expected_sha,
            "adapter": result.canonical(),
            "diagnostic": adapter.last_diagnostic,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2 if result.state in {DesktopCapabilityState.UNAVAILABLE, DesktopCapabilityState.UNSUPPORTED} else 1
    assert isinstance(result, WinUiAcceptanceResult)
    write_winui_acceptance_report(result, output)
    payload = result.to_dict()
    payload["source_sha"] = expected_sha
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
