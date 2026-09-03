from __future__ import annotations

import re
import subprocess
from pathlib import Path

BASE_SHA = "d19a8b1fa32fa5e28fa23b036407bc5bd902ef92"
NORMALIZATION_CANDIDATE = "86eb24e3e8e42fa6ca46bd1731a42a1877188d80"
IMPLEMENTATION_MERGE = "f1a57893f136e5b5b058aa420adcd4f24bf81c9e"
FINAL_END = "46dc20e7bd734c2902e0c2ac2deb2ef909cf43b3"
BRANCH = "r16/16-resource-concurrency-leak-diagnostics-soak"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != BASE_SHA:
        raise SystemExit("R16.16 START helper is not on the exact normalized R16.15 main")

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")

    plan, count = re.subn(
        r"^\*\*Execution checkpoint:\*\*.*$",
        (
            "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
            "R16.1–R16.15 are COMPLETE + NORMALIZED. R16.16 is IN_PROGRESS on dedicated branch "
            f"`{BRANCH}` created directly from exact normalized `main` `{BASE_SHA}` before implementation; "
            "R16.17–R16.18 remain PLANNED and unauthorized. R16.15 final exact-END "
            f"`{FINAL_END}` passed R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / `33773493833` "
            "Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / `33773494099` 5/5 "
            f"and KodeStudio UI Smoke #2313 / `33773493773`; PR #363 merged as `{IMPLEMENTATION_MERGE}`. "
            f"The unique continuity-only normalization candidate `{NORMALIZATION_CANDIDATE}` then passed fresh R0 #2378 / "
            "`33774559173` Ubuntu + Windows, Python Core #2350 / `33774558881` 5/5 and UI #2315 / `33774559462`, "
            f"and PR #364 merged with exact expected head as normalized `main` `{BASE_SHA}`. R16.16 manual state is NONE. "
            "No R16.16 implementation precedes this START-sync."
        ),
        plan,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise SystemExit("plan execution checkpoint anchor mismatch")

    plan, count = re.subn(
        r"^\| R16\.16 \|([^\n]*?)\| PLANNED \| NONE \|$",
        r"| R16.16 |\1| IN_PROGRESS | NONE |",
        plan,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise SystemExit("plan R16.16 status row anchor mismatch")

    start_authority = f"""## R16.16 START authority

- State: **IN_PROGRESS**; manual intervention **NONE**.
- Exact normalized R16.15 base: `main` `{BASE_SHA}`; dedicated branch `{BRANCH}` created directly from that SHA before implementation.
- R16.15 final exact-END `{FINAL_END}` passed R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / `33773493833` Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / `33773494099` 5/5 and KodeStudio UI Smoke #2313 / `33773493773`; PR #363 merged with exact expected head as implementation/evidence `main` `{IMPLEMENTATION_MERGE}`.
- The unique R16.15 post-merge continuity-only normalization candidate `{NORMALIZATION_CANDIDATE}` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #2378 / `33774559173` Ubuntu + Windows, Python Core #2350 / `33774558881` 5/5 and KodeStudio UI Smoke #2315 / `33774559462`, then PR #364 merged with exact expected head as normalized `main` `{BASE_SHA}`. No second R16.15 normalization is authorized.
- Prior state: R16.1–R16.15 **COMPLETE + NORMALIZED**; R16.17–R16.18 remain **PLANNED** and unauthorized.
- Frozen R16.16 scope: deterministic bounded load profiles for representative code/Godot/ComfyUI/media/desktop fixtures; CPU/RAM/VRAM/disk/process/time budgets; repeated/concurrent workloads; supported cancellation races; worker/process/file-handle/temp-artifact cleanup; privacy-safe diagnostics; frozen regression thresholds/baselines; explicit environment variance and `INCONCLUSIVE` handling.
- Core acceptance remains bounded, deterministic, network-independent, non-destructive and free of live credentials. Unknown capacity or ambiguous resource state fails closed where the frozen scope requires it.
- No R16.16 implementation bytes precede this START-sync.

"""
    plan_anchor = "## Manual intervention\n\n**NONE.**\n\n---\n\n# R16.17 — v1.0 packaging, migration, rollback and release readiness"
    plan = replace_once(
        plan,
        plan_anchor,
        "## Manual intervention\n\n**NONE.**\n\n" + start_authority + "---\n\n# R16.17 — v1.0 packaging, migration, rollback and release readiness",
        "plan R16.16 manual/R16.17 anchor",
    )

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    new_top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.15 COMPLETE + NORMALIZED. R16.16 IN_PROGRESS. R16.17–R16.18 remain PLANNED and unauthorized.** "
        f"R16.15 unique normalization candidate `{NORMALIZATION_CANDIDATE}` passed fresh R0 #2378 / `33774559173` "
        "Ubuntu + Windows, Python Core #2350 / `33774558881` 5/5 and KodeStudio UI Smoke #2315 / `33774559462`, "
        f"then PR #364 merged with exact expected head as normalized `main` `{BASE_SHA}`. R16.16 dedicated branch "
        f"`{BRANCH}` is created directly from that exact normalized main before implementation. Manual state NONE. "
        "This START-sync is documentation-only; no R16.16 implementation bytes precede it.\n\n"
    )
    continuity, count = top_re.subn(new_top, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity top anchor mismatch")

    global_re = re.compile(r"^- R16\.15 : \*\*COMPLETE \+ NORMALIZED\*\* — .*?$", re.M)
    match = global_re.search(continuity)
    if match is None:
        raise SystemExit("continuity R16.15 normalized bullet anchor mismatch")
    r1615 = (
        f"- R16.15 : **COMPLETE + NORMALIZED** — normalized R16.14 base `00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f`; "
        "clean START `cf29886a7f48f1d43e2f57e34a9c3483f4ada519`; immutable technical source "
        "`377040f326d2cf87eec4d68b0f90ca2ed615cc04`; final exact-END "
        f"`{FINAL_END}` passed R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / `33773493833` "
        "Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / `33773494099` 5/5 and "
        f"UI #2313 / `33773493773`; PR #363 merged exact head as implementation/evidence `main` `{IMPLEMENTATION_MERGE}`. "
        f"Unique normalization candidate `{NORMALIZATION_CANDIDATE}` changed only continuity, passed R0 #2378 / `33774559173` "
        "Ubuntu + Windows, Python Core #2350 / `33774558881` 5/5 and UI #2315 / `33774559462`; PR #364 merged with "
        f"exact expected head as normalized `main` `{BASE_SHA}`. Exact-END acceptance remains 31/31 focused + supply-chain "
        "tests and 20/20 durability cases per OS; canonical fixture `9bd8b2e63b1c17b351744e9552da7927c911e7da78ddcd8b25e4dc19a0e899b5`, "
        "semantic `1f128da121ebb957b7a1f29dc96007d381ef6ad4f2e340e3c59c10eb0f56dd7c`, policy "
        "`f921f368f516523f6a803fd01320a825cc8086189c1ebc77165fd9cd6f77dc05`, authority "
        "`be7bf480b34a47175bd4cf8c492ecd3b4d11a097cbe09ee2ba8f132ddda6d5b7`. Core manual NONE; optional extended "
        f"local soak remains CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`. R16.16 START-sync is authorized only from `{BASE_SHA}`."
    )
    continuity = continuity[: match.start()] + r1615 + continuity[match.end():]

    continuity_start = f"""## R16.16 START authority

- R16.16 state: **IN_PROGRESS**; manual intervention **NONE**. R16.17–R16.18 remain PLANNED and unauthorized.
- Exact normalized R16.15 base: `main` `{BASE_SHA}`; dedicated branch `{BRANCH}` created directly from that SHA before implementation.
- R16.15 implementation/evidence merge `{IMPLEMENTATION_MERGE}` followed final exact-END `{FINAL_END}` and the five mandatory exact-END authorities. The single post-merge normalization candidate `{NORMALIZATION_CANDIDATE}` changed only continuity, passed fresh R0 #2378 / `33774559173` Ubuntu + Windows, Python Core #2350 / `33774558881` 5/5 and UI #2315 / `33774559462`, then PR #364 merged with exact expected head as normalized `main` `{BASE_SHA}`.
- Frozen scope: deterministic bounded representative load profiles; CPU/RAM/VRAM/disk/process/time budgets; concurrency/cancellation races; worker/process/handle/temp cleanup; repeatability and bounded-growth checks; privacy-safe aggregate diagnostics; explicit thresholds/baselines and source-bound evidence; normalized environment variance with truthful `INCONCLUSIVE` handling.
- Core execution must be synthetic/fixture-based where needed, bounded, non-destructive, network-independent, free of live credentials and diagnostically redacted. Unknown capacity fails closed when budget safety cannot be proven.
- No R16.16 implementation bytes precede this START-sync.

"""
    continuity = replace_once(
        continuity,
        "\n## R16 status index\n",
        "\n" + continuity_start + "## R16 status index\n",
        "continuity status index anchor",
    )
    continuity = replace_once(
        continuity,
        "| R16.16 | PLANNED | NONE |",
        "| R16.16 | IN_PROGRESS | NONE |",
        "continuity R16.16 status row",
    )

    next_re = re.compile(r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule", re.S)
    next_block = (
        "## Next authorized action\n\n"
        f"R16.16 is **IN_PROGRESS** on `{BRANCH}` from exact normalized `main` `{BASE_SHA}` after this documentation-only "
        "START-sync. The next authorized action is R16.16 implementation and focused/adversarial bounded acceptance for resource, "
        "concurrency, cancellation, cleanup/leak detection and privacy-safe diagnostics. No R16.17 action is authorized. Manual "
        "intervention is NONE. After an immutable technical source is selected, fresh exact-head R16.16 plus R16.9/R0/Python/UI "
        "qualification is required before any END-sync or merge.\n\n"
        "## Permanent R-phase execution rule"
    )
    continuity, count = next_re.subn(next_block, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity next action anchor mismatch")

    PLAN.write_text(plan, encoding="utf-8", newline="\n")
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
