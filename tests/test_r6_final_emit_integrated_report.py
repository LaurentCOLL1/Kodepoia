from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kodepoia.quality.patch_gate import (
    IntegrationEvidenceStatus,
    R6IntegrationReport,
    R6SubdivisionEvidence,
)


SOURCE_SHA = "f57d1c43cfa12a8f9918b80065f4ffa3502046de"
GENERATED_AT = "2026-08-22T15:36:00Z"
ACCEPTED_HEADS = {
    "R6.1": "802de4ba3110ace657c4e16306a0ca29850ce2bd",
    "R6.2": "8ac3772e98c70260c320519a214bb25b6cedbb38",
    "R6.3": "7150237c263dd3ac96af4662d74909e05f3cf991",
    "R6.4": "72f8a13f68eb8c2e11069fe8e489858cbf2edd41",
    "R6.5": "06fd66af4b3a85da24b98ea2a5fbb2685358c540",
    "R6.6": "6890b9d37722c74703e8b86f7de11dbfe66821ed",
    "R6.7": "0da49c7526b54f562827d63477b7ce8f1865de43",
    "R6.8": "d632669b93fda7b8397b9c3de43d78ca8726323f",
    "R6.9": "1f24b0160cc28a03efdcbbc0aeb841125a1c5351",
    "R6.10": "e9363e0e00f592b39a7a094b7520b3d515fb02f0",
    "R6.11": "d0590ed3eda663ad713fc36d962c8dac1df109eb",
    "R6.12": SOURCE_SHA,
}


def test_emit_exact_r6_integrated_report_for_normalization() -> None:
    root = Path(__file__).resolve().parents[1]
    subdivisions: list[R6SubdivisionEvidence] = []
    for index in range(1, 13):
        subdivision = f"R6.{index}"
        source = f"docs/roadmap/R6_{index}_ACCEPTANCE.md"
        payload = (root / source).read_bytes()
        subdivisions.append(
            R6SubdivisionEvidence(
                subdivision=subdivision,
                status=IntegrationEvidenceStatus.PASS,
                source=source,
                evidence_sha256=hashlib.sha256(payload).hexdigest(),
                accepted_head=ACCEPTED_HEADS[subdivision],
                manual_satisfied=True,
            )
        )

    report = R6IntegrationReport.build(
        SOURCE_SHA,
        tuple(subdivisions),
        generated_at=GENERATED_AT,
    )
    raise AssertionError(
        "R6_FINAL_INTEGRATED_REPORT_BEGIN\n"
        + json.dumps(report.to_dict(), indent=2, sort_keys=True)
        + "\nR6_FINAL_INTEGRATED_REPORT_END"
    )
