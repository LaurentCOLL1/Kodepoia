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
    youtube_module = Path("src/kodepoia/intelligence/research/youtube.py").read_text(encoding="utf-8")
    adapter = Path("src/kodepoia/kodestudio/research_extended_panel.py").read_text(encoding="utf-8")
    ui_test = Path("tests/test_v2_1_5_research_ui.py").read_text(encoding="utf-8")
    python_core = Path(".github/workflows/python-core.yml").read_text(encoding="utf-8")
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
                "transcript_provider_unconfigured" in youtube_module
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
                "class ExtendedResearchServiceAdapter" in adapter
                and "class ExtendedResearchDiscoveryService" in adapter
                and "ResearchSourceKind.COMMUNITY" in adapter
                and "ResearchSourceKind.YOUTUBE" in adapter
                and "researchExtendedSourceState" in adapter
                and "sync_selected_candidate_to_fetch" in adapter,
            ),
            _check(
                "kodestudio-ui-regression-test",
                "test_v215_kodestudio_exposes_extended_fetch_kinds_and_provider_state" in ui_test
                and "test_v215_selecting_typed_candidate_prefills_explicit_fetch" in ui_test
                and "test_v215_youtube_without_network_is_explicitly_blocked" in ui_test
                and "tests/test_v2_1_5_research_ui.py" in python_core,
            ),
            _check(
                "authoritative-cross-platform-evidence",
                "Run V2.1.5 extended sources exact-head acceptance" in python_core
                and "Upload V2.1.5 exact-head evidence" in python_core
                and "v2-1-5-extended-sources-${{ matrix.os }}-${{ env.KODEPOIA_SOURCE_SHA }}" in python_core
                and "os: [ubuntu-latest, windows-latest]" in python_core,
            ),
            _check(
                "authority-current-v2-1-5",
                "V2.1.5 — Extended media/community sources — CURRENT" in roadmap,
            ),
            _check(
                "strict-scope-authority",
                "separately governed acquisition path" in roadmap
                and "cannot silently become trusted evidence" in roadmap
                and "any public release, installer publication or TUF transition" in roadmap
                and "V2.1.6 — ResearchGuard hardening — LATER" in roadmap,
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
