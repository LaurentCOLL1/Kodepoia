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
from kodepoia.desktop.tauri2 import Tauri2Adapter, TauriAcceptanceResult


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/roadmap/R12_9_TAURI_ACCEPTANCE.json")
    parser.add_argument("--work", default=".kodepoia/r12_9_tauri")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    expected_sha = os.environ.get("KODEPOIA_SOURCE_SHA", "").strip()
    work = (ROOT / args.work).resolve()
    staging = work / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    adapter = Tauri2Adapter(ROOT, staging)

    if args.prepare_only:
        cargo, manifest, model_sha = adapter.render_fixture(canonical_sample_app())
        payload = {
            "source_sha": expected_sha,
            "cargo_manifest": cargo.relative_to(ROOT).as_posix(),
            "fixture_root": cargo.parent.relative_to(ROOT).as_posix(),
            "model_sha256": model_sha,
            "project_manifest_sha256": manifest.digest(),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    result = adapter.run_acceptance(canonical_sample_app())
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

    assert isinstance(result, TauriAcceptanceResult)
    payload = result.to_dict()
    payload["source_sha"] = expected_sha
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
