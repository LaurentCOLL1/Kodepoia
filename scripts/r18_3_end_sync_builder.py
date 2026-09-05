from __future__ import annotations

import argparse
import re
from pathlib import Path

ROADMAP = Path("docs/roadmap/R18_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def _replace_next_action(text: str, body: str) -> str:
    pattern = re.compile(r"(## Next authorized action\n\n)(.*?)(?=\n## |\Z)", re.DOTALL)
    match = pattern.search(text)
    if match is None:
        raise SystemExit("continuity: Next authorized action section missing")
    return text[: match.start()] + match.group(1) + body.rstrip() + "\n" + text[match.end() :]


def _technical_evidence(args: argparse.Namespace) -> str:
    return (
        f"Immutable technical source `{args.technical_sha}` passed R18.3 specialized run "
        f"`{args.specialized_run}` with Ubuntu + Windows contract acceptance and the actual "
        "Windows release-candidate path: exact-source installer build, deterministic SPDX 2.3 "
        "SBOM, release provenance, evidence-bound bundle, GitHub build-provenance attestation, "
        "GitHub SPDX SBOM attestation, successful `gh attestation verify` for both predicates, "
        "and rejection of a modified subject. "
        f"Final technical bundle SHA-256 `{args.bundle_sha256}`; SBOM SHA-256 "
        f"`{args.sbom_sha256}`; provenance SHA-256 `{args.provenance_sha256}`; Actions artifact "
        f"`{args.artifact_id}` / `{args.artifact_name}`, artifact ZIP digest "
        f"`sha256:{args.artifact_digest}`. Broad exact-source gate run `{args.broad_run}` is "
        "SUCCESS for all 7 jobs: R0 Ubuntu/Windows, full Python Core Ubuntu/Windows, "
        "KodeStudio UI Smoke Windows and R16.9 Ubuntu/Windows. Manual intervention NONE; "
        "production signing, public GitHub Release and public WinGet submission remain NOT "
        "TRIGGERED. Because this END-sync changes documentation bytes, fresh specialized R18.3 "
        "+ R16.9 + R0 + full Python Core + KodeStudio UI gates on the resulting exact END-head "
        "remain mandatory before exact-head PR merge."
    )


def update_roadmap(args: argparse.Namespace) -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "R18.3 SBOM, provenance and artifact attestations is **IN_PROGRESS** from that exact "
        "normalized main on `r18/03-sbom-provenance-attestations`. R18.4 remains PLANNED and "
        "is not authorized until R18.3 implementation/evidence merge plus unique post-merge "
        "normalization complete.",
        "R18.3 SBOM, provenance and artifact attestations is **COMPLETE at END-sync** on "
        f"immutable technical source `{args.technical_sha}`; fresh exact-END gates, "
        "implementation/evidence merge and the unique post-merge normalization remain required. "
        "R18.4 remains PLANNED and is not authorized until that normalization completes.",
        label="roadmap status",
    )
    text = _replace_once(
        text,
        "| R18.3 | SBOM, provenance and artifact attestations | IN_PROGRESS | NONE | R18.2 |",
        "| R18.3 | SBOM, provenance and artifact attestations | COMPLETE | NONE | R18.2 |",
        label="roadmap index",
    )
    marker = (
        "## Validation and evidence\n\n"
        "SBOM digest, attestation subject digest, verification output, run/workflow IDs and exact head."
    )
    replacement = marker + "\n\nEND-sync technical acceptance: " + _technical_evidence(args)
    start = text.index("# R18.3 — SBOM, provenance and artifact attestations")
    end = text.index("# R18.4 — Windows Authenticode signing and verification boundary")
    before, section, after = text[:start], text[start:end], text[end:]
    section = _replace_once(section, marker, replacement, label="R18.3 validation evidence")
    ROADMAP.write_text(before + section + after, encoding="utf-8", newline="\n")


def update_continuity(args: argparse.Namespace) -> None:
    text = CONTINUITY.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "R18.3 SBOM, provenance and artifact attestations is STARTED / IN_PROGRESS from that "
        "exact normalized main on `r18/03-sbom-provenance-attestations`; R18.4 remains PLANNED "
        "until R18.3 implementation/evidence merge and unique post-merge normalization complete.",
        "R18.3 SBOM, provenance and artifact attestations is COMPLETE at END-sync on immutable "
        f"technical source `{args.technical_sha}`; fresh exact-END gates, implementation/evidence "
        "merge and the unique post-merge normalization remain required. R18.4 remains PLANNED "
        "and unauthorized until that normalization completes.",
        label="continuity headline",
    )
    line_pattern = re.compile(r"^- R18\.3 : \*\*STARTED / IN_PROGRESS\*\* — .*?$", re.MULTILINE)
    match = line_pattern.search(text)
    if match is None:
        raise SystemExit("continuity: R18.3 state line missing")
    current = match.group(0)
    updated = current.replace("**STARTED / IN_PROGRESS**", "**COMPLETE at END-sync**", 1)
    evidence = _technical_evidence(args)
    updated = _replace_once(
        updated,
        "Manual NONE.",
        evidence + " Manual NONE.",
        label="continuity R18.3 evidence insertion",
    )
    text = text[: match.start()] + updated + text[match.end() :]
    text = _replace_next_action(
        text,
        "R18.3 technical implementation is accepted only on immutable source "
        f"`{args.technical_sha}`. The next authorized action is to validate the documentation-only "
        "R18.3 END-head with fresh exact-source R18.3 specialized attestation, R16.9, R0, full "
        "Python Core and KodeStudio UI Smoke gates; only then may the implementation/evidence PR "
        "merge with exact expected-head protection. R18.4 remains unauthorized until the unique "
        "post-merge R18.3 continuity normalization is itself freshly gated and merged. Production "
        "signing, public GitHub Release publication and public WinGet submission remain NOT TRIGGERED.",
    )
    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--technical-sha", required=True)
    parser.add_argument("--specialized-run", required=True)
    parser.add_argument("--broad-run", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--sbom-sha256", required=True)
    parser.add_argument("--provenance-sha256", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    args = parser.parse_args()
    update_roadmap(args)
    update_continuity(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
