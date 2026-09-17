from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _check(name: str, passed: bool, detail: str = "") -> dict[str, object]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="V2.1.5 extended media/community acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    expected = args.source_sha.strip()
    actual = _head()
    checks: list[dict[str, object]] = [
        _check("exact-head", actual == expected, f"expected={expected} actual={actual}"),
    ]

    test_run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_v2_1_5_extended_sources.py"],
        text=True,
        capture_output=True,
        check=False,
    )
    checks.append(
        _check(
            "extended-source-tests",
            test_run.returncode == 0,
            (test_run.stdout + "\n" + test_run.stderr).strip()[-6000:],
        )
    )

    module = Path("src/kodepoia/intelligence/research/extended_sources.py").read_text(encoding="utf-8")
    panel = Path("src/kodepoia/kodestudio/research_panel.py").read_text(encoding="utf-8")
    roadmap = Path("docs/roadmap/V2_1_RESEARCH_WORKSPACE.md").read_text(encoding="utf-8")

    checks.extend(
        [
            _check(
                "candidate-only-before-fetch",
                "descriptor_only_not_fetched:" in module and 'trust="candidate-only"' in module,
            ),
            _check(
                "same-store-and-evidence-lifecycle",
                "ResearchStore" in module
                and "EvidenceWorkspace.project" in module
                and "EvidenceSelectionStore" in module,
            ),
            _check(
                "transcript-unavailable-explicit",
                "transcript_provider_unconfigured" in module
                and '"transcript_status"' in module
                and '"transcript_reason"' in module,
            ),
            _check(
                "unsupported-media-not-authoritative",
                '"stt_fallback_trusted": False' in module
                and '"frame_extraction_trusted": False' in module,
            ),
            _check(
                "community-typed-relationships",
                '"typed_relationships": True' in module
                and '"popularity_is_authority": False' in module,
            ),
            _check(
                "kodestudio-structured-lifecycle",
                "ResearchSourceKind" in panel
                and "EvidenceWorkspace" in panel
                and "researchDiscoveryButton" in panel
                and "researchFetchButton" in panel,
            ),
            _check(
                "authority-current-v2-1-5",
                "V2.1.5" in roadmap and "Extended media/community sources" in roadmap,
            ),
            _check(
                "strict-scope",
                "STT fallback" in roadmap
                and "authoritative citations" in roadmap
                and "posting" in roadmap.lower(),
            ),
        ]
    )

    passed = all(bool(item["passed"]) for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.1.5",
        "source_sha": actual,
        "result": "PASS" if passed else "FAIL",
        "checks": checks,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
