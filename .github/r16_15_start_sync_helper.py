from __future__ import annotations

import re
import subprocess
from pathlib import Path

BASE = "00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
BRANCH = "r16/15-long-term-project-durability-resume-upgrade-soak"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != BASE:
        raise SystemExit(f"wrong R16.15 START base: {head}")

    subprocess.run(
        ["git", "diff", "--exit-code", BASE, "--", PLAN.as_posix(), CONTINUITY.as_posix()],
        check=True,
    )

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")

    checkpoint_re = re.compile(r"^\*\*Execution checkpoint:\*\*.*$", re.M)
    checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.14 are COMPLETE + NORMALIZED. R16.15 is IN_PROGRESS on dedicated branch "
        f"`{BRANCH}` from exact normalized `main` `{BASE}`; R16.16–R16.18 remain PLANNED and unauthorized. "
        "R16.14 post-merge normalization candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` passed fresh "
        "R0 #2369 / `33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and "
        "KodeStudio UI Smoke #2306 / `33711021031`, then PR #362 merged with exact expected head as normalized "
        f"`main` `{BASE}`. R16.15 core manual state is NONE; optional extended local wall-clock soak is "
        "CONDITIONAL / NOT TRIGGERED. No R16.15 implementation preceded this START-sync."
    )
    plan, count = checkpoint_re.subn(checkpoint, plan, count=1)
    if count != 1:
        raise SystemExit("plan execution checkpoint anchor mismatch")

    plan = replace_once(
        plan,
        "| R16.14 | Representative audio/voice/cinematic beta workflow | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "| R16.14 | Representative audio/voice/cinematic beta workflow | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.14 status",
    )
    plan = replace_once(
        plan,
        "| R16.15 | Long-term project durability, resume and upgrade soak | PLANNED | CONDITIONAL |",
        "| R16.15 | Long-term project durability, resume and upgrade soak | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.15 status",
    )

    start_authority = f"""## R16.15 START authority

- State: **IN_PROGRESS**; core manual **NONE**; optional extended wall-clock/local-environment soak **CONDITIONAL / NOT TRIGGERED** and non-authoritative for core CI unless explicitly requested.
- Exact normalized base: `main` `{BASE}`; dedicated branch `{BRANCH}` created directly from that SHA before implementation.
- R16.14 normalization authority is complete: candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` changed only continuity, passed fresh R0 #2369 / `33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and KodeStudio UI Smoke #2306 / `33711021031`, then PR #362 merged with `expected_head_sha=82e019f49fe82dc2c2e7c98ce8da70f54a06a548` as normalized `main` `{BASE}`.
- Prior state: R16.1–R16.14 **COMPLETE + NORMALIZED**; R16.16–R16.18 remain **PLANNED** and unauthorized.
- Frozen R16.15 scope is unchanged: deterministic long-lived project fixture; repeated clean-process session resume; durable-authority reconstruction; representative cross-domain change history; forward schema/version migration and supported rollback/recovery; injected stale/corrupt memory, interrupted-write and partial-artifact checkpoints; orphan/duplicate-authority, silent-loss and stale permission/secret-state rejection; bounded deterministic CI soak plus separately truthful optional extended local soak.
- No R16.15 implementation preceded this START-sync. Core acceptance must remain deterministic, synthetic/bounded, non-destructive, network-independent and free of live credentials.
"""
    anchor = (
        "## Manual intervention\n\n"
        "**CONDITIONAL.** Only for an optional extended wall-clock/local-environment soak beyond the authoritative bounded CI profile.\n\n"
        "---\n\n# R16.16 — Resource, concurrency, leak and diagnostics soak"
    )
    replacement = (
        "## Manual intervention\n\n"
        "**CONDITIONAL.** Only for an optional extended wall-clock/local-environment soak beyond the authoritative bounded CI profile.\n\n"
        + start_authority
        + "\n---\n\n# R16.16 — Resource, concurrency, leak and diagnostics soak"
    )
    plan = replace_once(plan, anchor, replacement, "plan R16.15 START insertion")

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.14 COMPLETE + NORMALIZED. R16.15 IN_PROGRESS. R16.16–R16.18 remain PLANNED and unauthorized.** "
        "R16.14 unique post-merge normalization candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` passed fresh "
        "R0 #2369 / `33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and KodeStudio UI Smoke "
        f"#2306 / `33711021031`; PR #362 merged exact head as normalized `main` `{BASE}`. R16.15 START-sync is now "
        f"authorized and synchronized on `{BRANCH}` from that exact `main` before implementation. Core manual NONE; optional "
        "extended local wall-clock soak CONDITIONAL / NOT TRIGGERED.\n\n"
    )
    continuity, count = top_re.subn(top, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity top anchor mismatch")

    r14_re = re.compile(r"^- R16\.14 : \*\*COMPLETE \+ NORMALIZED\*\* — .*?$", re.M)
    r14_final = (
        "- R16.14 : **COMPLETE + NORMALIZED** — normalized R16.13 `main` `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; "
        "clean START `7ed6f09262fc259bd875fc76c4583b758474090b`; immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31`; "
        "final exact-END `4e2e165bf23406e287ceded177325b19ed5ccb81` passed R16.14 #4 / `33710294616` Ubuntu + Windows, R16.9 #49 / "
        "`33710294572` Ubuntu + Windows, R0 #2367 / `33710294495` Ubuntu + Windows, Python Core #2339 / `33710294574` 5/5 and UI #2304 / "
        "`33710294606`; PR #361 merged exact head as implementation/evidence `main` `f9303eaa58902849953338e3400df34094fad0c6`. "
        "Unique normalization candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` changed only this continuity file, passed fresh R0 #2369 / "
        "`33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and UI #2306 / `33711021031`, then PR #362 merged with exact expected head as normalized "
        f"`main` `{BASE}`. Exact-END artifacts remain Linux `9876741282 / sha256:8d70c25c28f3132af4dc10d72d26d6e34e3e8ab0f5590f65e30ccb05cdbb87c4`; "
        "Windows `9876723999 / sha256:fd47a11c953706ac3a35b33b693c682982c9fda78150bf7fdd379dd997e01d56`. Acceptance remains 16/16 PASS, synthetic, "
        "no live credentials/destructive actions/network calls; real TTS/human-device listening NOT_EXERCISED. No second R16.14 normalization is permitted. "
        f"R16.15 START is authorized only from `{BASE}` and is now synchronized before implementation."
    )
    continuity, count = r14_re.subn(r14_final, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity R16.14 global line anchor mismatch")

    if "- R16.15 : **IN_PROGRESS**" in continuity:
        raise SystemExit("R16.15 global line already present")
    r14_match = re.search(r"^- R16\.14 : \*\*COMPLETE \+ NORMALIZED\*\* — .*?$", continuity, re.M)
    if r14_match is None:
        raise SystemExit("updated R16.14 line missing")
    r15_line = (
        f"- R16.15 : **IN_PROGRESS** — exact normalized R16.14 `main` `{BASE}`; dedicated branch `{BRANCH}` created directly from that SHA; "
        "START-sync is documentation-only and precedes all implementation. Frozen scope: deterministic long-lived project/session fixture, clean-process resume, durable-authority reconstruction, "
        "cross-domain history continuity, version/schema forward migration plus supported rollback/recovery, stale/corrupt memory and interrupted/partial-state injection, orphan/duplicate/stale-authority rejection, "
        "bounded deterministic CI soak and separate optional extended local wall-clock soak. Core manual NONE; optional extended local soak CONDITIONAL / NOT TRIGGERED. R16.16 remains PLANNED."
    )
    pos = r14_match.end()
    continuity = continuity[:pos] + "\n" + r15_line + continuity[pos:]

    continuity = replace_once(
        continuity,
        "| R16.15 | PLANNED | CONDITIONAL |",
        "| R16.15 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "continuity R16.15 status",
    )

    continuity_start = f"""## R16.15 START authority

- Exact normalized R16.14 base: `main` `{BASE}`; R16.14 is **COMPLETE + NORMALIZED** and no second R16.14 normalization is authorized.
- Dedicated R16.15 branch `{BRANCH}` is created directly from that exact normalized SHA before implementation; this START-sync is documentation-only.
- R16.14 normalization candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` passed R0 #2369 / `33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and UI #2306 / `33711021031`, then PR #362 merged with exact expected head as `{BASE}`.
- R16.15 state is **IN_PROGRESS**. R16.16–R16.18 remain **PLANNED** and unauthorized.
- Frozen R16.15 scope: deterministic long-lived project fixture; repeated session/checkpoint resume from clean processes; durable state reconstruction; cross-domain edits with provenance/history continuity; version/schema forward migration and supported rollback/recovery; stale/corrupt memory, interrupted write and partial-artifact fault injection; rejection/recovery for unresolved orphan, duplicate authority, silent data loss and stale permission/secret state; bounded deterministic hosted-runner soak plus separately truthful optional extended local soak.
- Core manual state **NONE**. Optional extended wall-clock/local-environment soak is **CONDITIONAL / NOT TRIGGERED** and cannot substitute for bounded core CI evidence.
- No R16.15 implementation bytes precede this START-sync.
"""
    continuity = replace_once(
        continuity,
        "\n## R16 status index\n",
        "\n" + continuity_start + "\n## R16 status index\n",
        "continuity R16 status index insertion",
    )

    next_re = re.compile(
        r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
        re.S,
    )
    next_text = (
        "## Next authorized action\n\n"
        f"R16.15 — **Long-term project durability, resume and upgrade soak** — is the active authorized subdivision on `{BRANCH}` from exact normalized `main` `{BASE}`. "
        "START-sync is complete before implementation. Implement only the frozen R16.15 scope: deterministic long-lived project/session fixture, clean-process resume, durable-authority reconstruction, "
        "cross-domain history continuity, version/schema migration and supported rollback/recovery, stale/corrupt/interrupted/partial-state injection, orphan/duplicate/stale-authority rejection, and bounded deterministic CI soak. "
        "Core manual **NONE**; optional extended local wall-clock/environment soak remains **CONDITIONAL / NOT TRIGGERED** and cannot replace core CI. R16.16 remains unauthorized until R16.15 implementation/evidence, END-sync, exact-head gates, merge and unique post-merge normalization complete.\n\n"
        "## Permanent R-phase execution rule"
    )
    continuity, count = next_re.subn(next_text, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity next action anchor mismatch")

    PLAN.write_text(plan, encoding="utf-8", newline="\n")
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")

    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE, "--", PLAN.as_posix(), CONTINUITY.as_posix()],
        text=True,
    ).splitlines()
    expected = sorted([PLAN.as_posix(), CONTINUITY.as_posix()])
    if sorted(changed) != expected:
        raise SystemExit(f"unexpected START-sync diff: {changed}")
    subprocess.run(["git", "diff", "--check", BASE, "--", *expected], check=True)


if __name__ == "__main__":
    main()
