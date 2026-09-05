from __future__ import annotations

import argparse
import re
from pathlib import Path

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge-sha", required=True)
    parser.add_argument("--end-head", required=True)
    parser.add_argument("--exact-end-specialized-run", required=True)
    parser.add_argument("--exact-end-broad-run", required=True)
    parser.add_argument("--pr-number", required=True)
    args = parser.parse_args()

    text = CONTINUITY.read_text(encoding="utf-8")

    old_headline = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. "
        "R18 planning ACCEPTED + NORMALIZED. R18.1 Canonical release identity, versions and "
        "channels is COMPLETE + NORMALIZED on canonical `main` "
        "`c611131268041b06f53de66eaadd45120e2b750d`. R18.2 Deterministic release bundle and "
        "manifest contract is COMPLETE + NORMALIZED on canonical `main` "
        "`c376d0af789e584e1ef307f43e42a62ce024b052` after exact-head implementation/evidence "
        "PR #384 and unique continuity-only normalization PR #385. R18.3 SBOM, provenance and "
        "artifact attestations is COMPLETE at END-sync on immutable technical source "
        "`ceeb1c790e7bc67755b986f29d7244d42dbb3c7a`; fresh exact-END gates, "
        "implementation/evidence merge and the unique post-merge normalization remain required. "
        "R18.4 remains PLANNED and unauthorized until that normalization completes.** Production "
        "signing, public GitHub Release publication and public WinGet submission remain "
        "CONDITIONAL / NOT TRIGGERED."
    )
    new_headline = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. "
        "R18 planning ACCEPTED + NORMALIZED. R18.1 Canonical release identity, versions and "
        "channels is COMPLETE + NORMALIZED on canonical `main` "
        "`c611131268041b06f53de66eaadd45120e2b750d`. R18.2 Deterministic release bundle and "
        "manifest contract is COMPLETE + NORMALIZED on canonical `main` "
        "`c376d0af789e584e1ef307f43e42a62ce024b052` after exact-head implementation/evidence "
        "PR #384 and unique continuity-only normalization PR #385. R18.3 SBOM, provenance and "
        "artifact attestations is COMPLETE + NORMALIZED effective when this unique "
        "continuity-only normalization record enters `main` through fresh exact-head R0/Python/UI "
        f"gates and exact expected-head merge; implementation/evidence PR #{args.pr_number} merged "
        f"exact END head `{args.end_head}` as `main` `{args.merge_sha}`. R18.4 remains PLANNED and "
        "is authorized only from the normalized `main` produced by this record.** Production "
        "signing, public GitHub Release publication and public WinGet submission remain "
        "CONDITIONAL / NOT TRIGGERED."
    )
    text = _replace_once(text, old_headline, new_headline, label="headline")

    pattern = re.compile(r"^- R18\.3 : .*?$", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        raise SystemExit("continuity: R18.3 state line missing")
    line = match.group(0)
    if "**COMPLETE at END-sync**" not in line:
        raise SystemExit("continuity: R18.3 is not at END-sync")
    if args.end_head not in text:
        # END head is normally referenced in Next authorized action, not necessarily state line.
        pass
    line = line.replace(
        "**COMPLETE at END-sync**",
        "**COMPLETE + NORMALIZED effective when this unique continuity-only normalization record "
        "enters `main` through fresh exact-head R0/Python/UI gates and exact expected-head merge**",
        1,
    )
    old_tail = (
        "Because this END-sync changes documentation bytes, fresh specialized R18.3 + R16.9 + R0 + "
        "full Python Core + KodeStudio UI gates on the resulting exact END-head remain mandatory "
        "before exact-head PR merge. Manual NONE. Production signing/public GitHub Release/public "
        "WinGet submission remain NOT TRIGGERED. R18.4 remains PLANNED and unauthorized until "
        "R18.3 implementation/evidence merge plus exactly one post-merge continuity normalization complete."
    )
    new_tail = (
        f"Final exact-END head `{args.end_head}` passed specialized R18.3 run "
        f"`{args.exact_end_specialized_run}` SUCCESS for Ubuntu + Windows contract jobs and the "
        "actual Windows release-candidate attestation path; broad exact-END gate run "
        f"`{args.exact_end_broad_run}` passed all 7 jobs: R0 Ubuntu/Windows, full Python Core "
        "Ubuntu/Windows, KodeStudio UI Smoke Windows and R16.9 Ubuntu/Windows. "
        f"Implementation/evidence PR #{args.pr_number} merged with `expected_head_sha={args.end_head}` "
        f"as `main` `{args.merge_sha}`. Manual NONE. Production signing/public GitHub Release/public "
        "WinGet submission remain NOT TRIGGERED. This continuity-only record is the single authorized "
        "post-merge R18.3 normalization authority; no second R18.3 normalization is authorized. "
        "R18.4 remains PLANNED and is authorized only from the normalized `main` produced when this "
        "exact record passes fresh R0/Python/UI and merges with exact expected-head protection."
    )
    line = _replace_once(line, old_tail, new_tail, label="R18.3 evidence tail")
    text = text[: match.start()] + line + text[match.end() :]

    text = _replace_next_action(
        text,
        "R18.3 implementation/evidence is merged and this file is the single authorized "
        "continuity-only R18.3 normalization record. This normalization head must pass fresh "
        "exact-head R0 Repository Guard Ubuntu + Windows, full Python Core and KodeStudio UI Smoke "
        "before exact expected-head protected merge. R18.4 START-sync is the next authorized action "
        "only from the canonical normalized `main` produced by that merge. Production signing, "
        "public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.",
    )

    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
