from __future__ import annotations

import re
import subprocess
from pathlib import Path

MERGE_SHA = "f1a57893f136e5b5b058aa420adcd4f24bf81c9e"
FINAL_END_SHA = "46dc20e7bd734c2902e0c2ac2deb2ef909cf43b3"
TECHNICAL_SHA = "377040f326d2cf87eec4d68b0f90ca2ed615cc04"
START_SHA = "cf29886a7f48f1d43e2f57e34a9c3483f4ada519"
BASE_SHA = "00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f"
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != MERGE_SHA:
        raise SystemExit("R16.15 normalization helper is not on the exact implementation/evidence merge")

    text = CONTINUITY.read_text(encoding="utf-8")

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.14 COMPLETE + NORMALIZED. R16.15 implementation/evidence is merged and its unique post-merge "
        "continuity-only normalization is the only remaining R16.15 action. R16.16–R16.18 remain PLANNED and unauthorized.** "
        f"Final exact-END `{FINAL_END_SHA}` passed R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / "
        "`33773493833` Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / "
        f"`33773494099` 5/5 and KodeStudio UI Smoke #2313 / `33773493773`, then PR #363 merged with exact expected "
        f"head as implementation/evidence `main` `{MERGE_SHA}`. Core manual NONE; optional extended local wall-clock/environment "
        "soak remains CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`. This single continuity-only normalization must pass "
        "fresh R0/Python/UI and merge before R16.16 START is authorized.\n\n"
    )
    text, count = top_re.subn(top, text, count=1)
    if count != 1:
        raise SystemExit("continuity top authority anchor mismatch")

    global_re = re.compile(r"^- R16\.15 : \*\*COMPLETE at END-sync\*\* — .*?$", re.M)
    match = global_re.search(text)
    if match is None:
        raise SystemExit("continuity global R16.15 bullet anchor mismatch")
    global_line = (
        f"- R16.15 : **COMPLETE + NORMALIZED** — normalized R16.14 `main` `{BASE_SHA}`; clean START `{START_SHA}`; "
        f"immutable technical source `{TECHNICAL_SHA}`; final exact-END `{FINAL_END_SHA}` passed fresh R16.15 #16 / "
        "`33773493932` SUCCESS Ubuntu + Windows, R16.9 #56 / `33773493833` SUCCESS Ubuntu + Windows, R0 #2376 / "
        "`33773493409` SUCCESS Ubuntu + Windows, Python Core #2348 / `33773494099` SUCCESS 5/5 and UI #2313 / "
        f"`33773493773` SUCCESS; PR #363 merged with exact expected head as implementation/evidence `main` `{MERGE_SHA}`. "
        "Exact-END acceptance remains 31/31 focused + supply-chain tests and 20/20 durability cases per OS with "
        "`durability_claim=true`, `critical_veto=false`, `secret_free=true`, canonical fixture "
        "`9bd8b2e63b1c17b351744e9552da7927c911e7da78ddcd8b25e4dc19a0e899b5`, semantic "
        "`1f128da121ebb957b7a1f29dc96007d381ef6ad4f2e340e3c59c10eb0f56dd7c`, policy "
        "`f921f368f516523f6a803fd01320a825cc8086189c1ebc77165fd9cd6f77dc05` and authority "
        "`be7bf480b34a47175bd4cf8c492ecd3b4d11a097cbe09ee2ba8f132ddda6d5b7`. Exact-END artifacts are Linux "
        "`9900652422 / sha256:1ef0ce6b347a83126020caf8a68926048d7afd0f6ecb5b0541a27a043a927c58` and Windows "
        "`9900708787 / sha256:238e34162c237f5c6bc379dd46193ba6fb0961d6766694bf678be0a3fd83d4e7`. Core manual NONE; "
        "optional extended local soak CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`. This record is the unique post-merge "
        "continuity-only R16.15 normalization authority when its PR merges; R16.16 START is authorized only from the resulting normalized `main`."
    )
    text = text[: match.start()] + global_line + text[match.end() :]

    old_tail = (
        "- This END-sync is restricted to `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`. "
        "The resulting exact END head must pass fresh R16.15/R16.9/R0/Python/UI before PR #363 may merge with exact expected-head protection.\n"
        "- Exactly one post-merge continuity-only R16.15 normalization is authorized. Only its gated merge may mark R16.15 **COMPLETE + NORMALIZED** and authorize R16.16 START.\n"
    )
    new_tail = (
        f"- Final exact-END `{FINAL_END_SHA}` passed fresh R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / "
        "`33773493833` Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / "
        "`33773494099` 5/5 and UI #2313 / `33773493773`. Exact-END artifacts are Linux `9900652422 / "
        "sha256:1ef0ce6b347a83126020caf8a68926048d7afd0f6ecb5b0541a27a043a927c58` with evidence SHA-256 "
        "`2dfe5b0002152e66d63f50dd52390ddf901939e5983f74cbaccf675ebccfec75`, and Windows `9900708787 / "
        "sha256:238e34162c237f5c6bc379dd46193ba6fb0961d6766694bf678be0a3fd83d4e7` with evidence SHA-256 "
        f"`f3334f0cbf2c81eb7f9d43ebb504e17d45fc91c3e460e3ac1bcb960e000f6d90`. PR #363 then merged with "
        f"`expected_head_sha={FINAL_END_SHA}` as implementation/evidence `main` `{MERGE_SHA}`.\n"
        "- Exactly one post-merge continuity-only R16.15 normalization is authorized from that merge. Only its fresh "
        "R0/Python/UI-gated exact-head merge may establish R16.15 **COMPLETE + NORMALIZED** and authorize R16.16 START.\n"
    )
    text = replace_once(text, old_tail, new_tail, "R16.15 END tail")

    normalization = f"""## R16.15 post-merge normalization authority

- Implementation/evidence merge base: `{MERGE_SHA}`, produced only after final exact-END `{FINAL_END_SHA}` passed R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / `33773493833` Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / `33773494099` 5/5 and KodeStudio UI Smoke #2313 / `33773493773`.
- Dedicated normalization branch: `r16/15-continuity-normalization`, created exactly from that implementation/evidence merge.
- The authoritative normalization tree changes only `docs/continuity/KODEPOIA_CONTINUITY.md`; `docs/roadmap/R16_PLAN.md`, all implementation/evidence bytes and all R16.15 workflow/runtime/test bytes remain identical to the implementation merge. Any temporary helper is absent from the decision head.
- Exact-END artifacts are Linux `9900652422 / sha256:1ef0ce6b347a83126020caf8a68926048d7afd0f6ecb5b0541a27a043a927c58` and Windows `9900708787 / sha256:238e34162c237f5c6bc379dd46193ba6fb0961d6766694bf678be0a3fd83d4e7`, both bound by GitHub to `{FINAL_END_SHA}`; evidence SHA-256 values are Linux `2dfe5b0002152e66d63f50dd52390ddf901939e5983f74cbaccf675ebccfec75` and Windows `f3334f0cbf2c81eb7f9d43ebb504e17d45fc91c3e460e3ac1bcb960e000f6d90`.
- This is the single authorized post-merge normalization for R16.15. Its exact candidate head must pass fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke before an exact-head merge. No second R16.15 normalization is permitted.
- Core manual state remains **NONE**. Optional extended wall-clock/local-environment soak remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`; it is not inferred from hosted CI.
- Only the normalized `main` produced by this exact gated normalization merge may authorize R16.16 START; R16.16 implementation must still begin with its own START-sync before any implementation bytes.

"""
    text = replace_once(
        text,
        "\n## R16 status index\n",
        "\n" + normalization + "## R16 status index\n",
        "R16 status index anchor",
    )
    text = replace_once(
        text,
        "| R16.15 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "| R16.15 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
        "R16.15 status row",
    )

    next_re = re.compile(r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule", re.S)
    next_block = (
        "## Next authorized action\n\n"
        f"R16.15 implementation/evidence is merged as `main` `{MERGE_SHA}` after final exact-END `{FINAL_END_SHA}` passed all five "
        "required authorities. This file is the single authorized post-merge continuity-only normalization candidate. The next "
        "authorized action is fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke on this one "
        "exact normalization head, followed only on full SUCCESS by exact-head merge of its normalization PR. R16.16 remains "
        "unauthorized until that normalized `main` exists; once it exists, only R16.16 START-sync is authorized before any R16.16 "
        "implementation. Optional extended local wall-clock/environment soak remains CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`.\n\n"
        "## Permanent R-phase execution rule"
    )
    text, count = next_re.subn(next_block, text, count=1)
    if count != 1:
        raise SystemExit("next authorized action anchor mismatch")

    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
