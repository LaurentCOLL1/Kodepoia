from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.contracts import DesktopCapabilityReport, DesktopCapabilityState
from kodepoia.desktop.wpf import WpfAcceptanceResult, WpfAdapter, write_wpf_acceptance_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/roadmap/R12_5_WPF_ACCEPTANCE.json")
    parser.add_argument("--work", default=".kodepoia/r12_5_wpf")
    args = parser.parse_args()
    work = (ROOT / args.work).resolve()
    staging = work / "staging"
    work.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    result = WpfAdapter(ROOT, staging).run_acceptance(canonical_sample_app())
    if isinstance(result, DesktopCapabilityReport):
        print(json.dumps(result.canonical(), indent=2, sort_keys=True))
        return 2 if result.state in {DesktopCapabilityState.UNAVAILABLE, DesktopCapabilityState.UNSUPPORTED} else 1
    assert isinstance(result, WpfAcceptanceResult)
    write_wpf_acceptance_report(result, ROOT / args.output)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
