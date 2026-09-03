from __future__ import annotations

import re
import subprocess
from pathlib import Path

BASE = "f9303eaa58902849953338e3400df34094fad0c6"
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != BASE:
        raise SystemExit(f"wrong normalization base: {head}")
    subprocess.run(
        ["git", "diff", "--exit-code", BASE, "--", CONTINUITY.as_posix()], check=True
    )

    text = CONTINUITY.read_text(encoding="utf-8")

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.13 COMPLETE + NORMALIZED. R16.14 implementation/evidence is merged and its unique post-merge "
        "continuity-only normalization is the only remaining R16.14 action. R16.15–R16.18 remain PLANNED and unauthorized.** "
        "Final exact-END `4e2e165bf23406e287ceded177325b19ed5ccb81` passed R16.14 #4 / `33710294616`, "
        "R16.9 #49 / `33710294572`, R0 #2367 / `33710294495`, Python Core #2339 / `33710294574` 5/5 and "
        "KodeStudio UI Smoke #2304 / `33710294606`, then PR #361 merged with exact expected head as implementation/evidence "
        "`main` `f9303eaa58902849953338e3400df34094fad0c6`. Core manual NONE; optional human listening/device-quality "
        "qualification remains CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`. This single continuity-only normalization "
        "must pass fresh R0/Python/UI and merge before R16.15 START is authorized.\n\n"
    )
    text, count = top_re.subn(top, text, count=1)
    if count != 1:
        raise SystemExit("top continuity anchor mismatch")

    global_re = re.compile(
        r"^- R16\.14 : \*\*COMPLETE at END-sync\*\* — .*?$", re.M
    )
    global_line = (
        "- R16.14 : **COMPLETE + NORMALIZED** — normalized R16.13 `main` `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; "
        "clean START `7ed6f09262fc259bd875fc76c4583b758474090b`; immutable technical source "
        "`92505a002a77c29c5621cdfaa332d43385307b31`; final exact-END `4e2e165bf23406e287ceded177325b19ed5ccb81` "
        "passed fresh R16.14 #4 / `33710294616` SUCCESS Ubuntu + Windows, R16.9 #49 / `33710294572` SUCCESS Ubuntu + Windows, "
        "R0 #2367 / `33710294495` SUCCESS Ubuntu + Windows, Python Core #2339 / `33710294574` SUCCESS 5/5 and UI #2304 / "
        "`33710294606` SUCCESS. PR #361 merged with `expected_head_sha=4e2e165bf23406e287ceded177325b19ed5ccb81` as "
        "implementation/evidence `main` `f9303eaa58902849953338e3400df34094fad0c6`. Exact-END R16.14 artifacts: Linux "
        "`9876741282 / sha256:8d70c25c28f3132af4dc10d72d26d6e34e3e8ab0f5590f65e30ccb05cdbb87c4`; Windows "
        "`9876723999 / sha256:fd47a11c953706ac3a35b33b693c682982c9fda78150bf7fdd379dd997e01d56`. Representative acceptance remains "
        "16/16 PASS with `security_claim=true`, `critical_veto=false`, `secret_free=true`, zero live credentials, zero destructive "
        "host actions and zero external network calls; fixture is synthetic and real TTS/human-device listening remain `NOT_EXERCISED`. "
        "This record is the unique post-merge continuity-only R16.14 normalization authority once this candidate passes fresh "
        "R0/Python/UI and merges; no second R16.14 normalization is permitted. R16.15 START is authorized only from the resulting normalized `main`."
    )
    text, count = global_re.subn(global_line, text, count=1)
    if count != 1:
        raise SystemExit("R16.14 global line anchor mismatch")

    old_end_tail = (
        "- This END-sync is documentation-only relative to `92505a002a77c29c5621cdfaa332d43385307b31`. "
        "Its exact resulting head must pass fresh R16.14/R16.9/R0/Python/UI before PR #361 merges with exact `expected_head_sha`. "
        "Exactly one post-merge continuity-only normalization is then required; only that normalized `main` may authorize R16.15 START."
    )
    new_end_tail = (
        "- Final exact-END `4e2e165bf23406e287ceded177325b19ed5ccb81` is exactly one docs-only commit above the immutable technical source and passed fresh "
        "R16.14 #4 / `33710294616` Ubuntu + Windows, R16.9 #49 / `33710294572` Ubuntu + Windows, R0 #2367 / `33710294495` Ubuntu + Windows, "
        "Python Core #2339 / `33710294574` 5/5 and UI #2304 / `33710294606`. PR #361 then merged with exact expected-head protection as implementation/evidence "
        "`main` `f9303eaa58902849953338e3400df34094fad0c6`. Exact-END artifacts: Linux `9876741282 / sha256:8d70c25c28f3132af4dc10d72d26d6e34e3e8ab0f5590f65e30ccb05cdbb87c4`; "
        "Windows `9876723999 / sha256:fd47a11c953706ac3a35b33b693c682982c9fda78150bf7fdd379dd997e01d56`. Exactly one post-merge continuity-only normalization remains required; only its normalized `main` may authorize R16.15 START."
    )
    text = replace_once(text, old_end_tail, new_end_tail, "R16.14 END tail")

    normalization = """## R16.14 post-merge normalization authority

- Implementation/evidence merge base: `f9303eaa58902849953338e3400df34094fad0c6`, produced only after final exact-END `4e2e165bf23406e287ceded177325b19ed5ccb81` passed R16.14 #4 / `33710294616` Ubuntu + Windows, R16.9 #49 / `33710294572` Ubuntu + Windows, R0 #2367 / `33710294495` Ubuntu + Windows, Python Core #2339 / `33710294574` 5/5 and KodeStudio UI Smoke #2304 / `33710294606`.
- Dedicated normalization branch: `r16/14-continuity-normalization`, created exactly from that implementation/evidence merge.
- The authoritative normalization tree changes only `docs/continuity/KODEPOIA_CONTINUITY.md`; `docs/roadmap/R16_PLAN.md`, all implementation/evidence bytes and all R16.14 workflow/runtime/test bytes remain identical to the implementation merge. Any temporary helper is absent from the decision head.
- Exact-END media artifacts are Linux `9876741282 / sha256:8d70c25c28f3132af4dc10d72d26d6e34e3e8ab0f5590f65e30ccb05cdbb87c4` and Windows `9876723999 / sha256:fd47a11c953706ac3a35b33b693c682982c9fda78150bf7fdd379dd997e01d56`, both bound by GitHub to `4e2e165bf23406e287ceded177325b19ed5ccb81`.
- This is the single authorized post-merge normalization for R16.14. Its exact candidate head must pass fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke before an exact-head merge. No second R16.14 normalization is permitted.
- Core manual state remains **NONE**. Optional human listening/device-quality qualification remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`; it is not inferred from synthetic CI.
- Only the normalized `main` produced by this exact gated normalization merge may authorize R16.15 START; R16.15 implementation must still begin with its own START-sync before any implementation bytes.
"""
    text = replace_once(
        text,
        "\n## R16 status index\n",
        "\n" + normalization + "\n## R16 status index\n",
        "R16 status index insertion",
    )

    text = replace_once(
        text,
        "| R16.14 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "| R16.14 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
        "R16.14 status row",
    )

    next_re = re.compile(
        r"## Next authorized action\n\nR16\.14 — \*\*Representative audio/voice/cinematic beta workflow\*\* — .*?\n\n## Permanent R-phase execution rule",
        re.S,
    )
    next_text = (
        "## Next authorized action\n\n"
        "R16.14 implementation/evidence is merged as `main` `f9303eaa58902849953338e3400df34094fad0c6`; this file is the single authorized "
        "post-merge continuity-only normalization candidate. The immediate action is fresh exact-head R0/Python/UI qualification and exact-head merge of this "
        "normalization. Only the resulting normalized `main` authorizes R16.15 START. If this text is read from `main` after that exact gated normalization merge, "
        "R16.15 START is authorized from that `main`, but R16.15 remains forbidden to implement anything before its own START-sync. Core manual **NONE**; optional "
        "human listening/device-quality qualification remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`.\n\n"
        "## Permanent R-phase execution rule"
    )
    text, count = next_re.subn(next_text, text, count=1)
    if count != 1:
        raise SystemExit("Next authorized action anchor mismatch")

    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE, "--", CONTINUITY.as_posix()], text=True
    ).splitlines()
    if changed != [CONTINUITY.as_posix()]:
        raise SystemExit(f"unexpected normalization diff: {changed}")
    subprocess.run(["git", "diff", "--check", BASE, "--", CONTINUITY.as_posix()], check=True)


if __name__ == "__main__":
    main()
