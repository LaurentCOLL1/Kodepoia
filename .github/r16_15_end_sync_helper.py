from __future__ import annotations

import re
import subprocess
from pathlib import Path

TECHNICAL_SHA = "377040f326d2cf87eec4d68b0f90ca2ed615cc04"
START_SHA = "cf29886a7f48f1d43e2f57e34a9c3483f4ada519"
BASE_SHA = "00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != TECHNICAL_SHA:
        raise SystemExit("R16.15 END-sync helper is not running on the immutable technical source")

    subprocess.run(
        ["git", "diff", "--exit-code", TECHNICAL_SHA, "--", PLAN.as_posix(), CONTINUITY.as_posix()],
        check=True,
    )

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")

    old_checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.14 are COMPLETE + NORMALIZED. R16.15 is IN_PROGRESS on dedicated branch "
        "`r16/15-long-term-project-durability-resume-upgrade-soak` from exact normalized `main` "
        "`00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f`; R16.16–R16.18 remain PLANNED and unauthorized. "
        "R16.14 post-merge normalization candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` passed fresh R0 #2369 / "
        "`33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and KodeStudio UI Smoke #2306 / "
        "`33711021031`, then PR #362 merged with exact expected head as normalized `main` "
        "`00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f`. R16.15 core manual state is NONE; optional extended local "
        "wall-clock soak is CONDITIONAL / NOT TRIGGERED. No R16.15 implementation preceded this START-sync."
    )
    new_checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.14 are COMPLETE + NORMALIZED. R16.15 is COMPLETE at END-sync on dedicated branch "
        "`r16/15-long-term-project-durability-resume-upgrade-soak` from exact normalized `main` "
        f"`{BASE_SHA}`, with clean START `{START_SHA}` and immutable technical source `{TECHNICAL_SHA}`; "
        "R16.16–R16.18 remain PLANNED and unauthorized. Fresh exact-technical-head gates are SUCCESS: "
        "R16.15 #13 / `33771718895` Ubuntu + Windows, R16.9 #54 / `33771719752` Ubuntu + Windows, "
        "R0 #2374 / `33771719659` Ubuntu + Windows, Python Core #2346 / `33771718602` 5/5 and "
        "KodeStudio UI Smoke #2311 / `33771718965`. Core manual state is NONE; optional extended local wall-clock "
        "soak is CONDITIONAL / NOT TRIGGERED and NOT_EXERCISED. Fresh exact-END R16.15/R16.9/R0/Python/UI "
        "re-gates, PR #363 exact-head merge and exactly one continuity-only post-merge normalization remain mandatory "
        "before R16.16 START."
    )
    plan = replace_once(plan, old_checkpoint, new_checkpoint, "plan execution checkpoint")
    plan = replace_once(
        plan,
        "| R16.15 | Long-term project durability, resume and upgrade soak | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "| R16.15 | Long-term project durability, resume and upgrade soak | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.15 status row",
    )

    plan_end = f"""## R16.15 END authority

- State: **COMPLETE at END-sync**; core manual **NONE**; optional extended wall-clock/local-environment soak **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`. R16.16 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `{BASE_SHA}`; clean START-sync `{START_SHA}`; immutable technical source `{TECHNICAL_SHA}`.
- Fresh exact-technical-head gates on that immutable source are all SUCCESS: R16.15 #13 / `33771718895` Ubuntu + Windows; R16.9 #54 / `33771719752` Ubuntu + Windows; R0 Repository Guard #2374 / `33771719659` Ubuntu + Windows; Python Core #2346 / `33771718602` 5/5; KodeStudio UI Smoke #2311 / `33771718965`.
- Focused R16.15 plus R16.9 supply-chain regression is **31/31 PASS** on both hosted OS paths. Representative durability acceptance is **20/20 PASS** per OS with `durability_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, `external_network_calls=0` and `destructive_host_actions=0`.
- The authoritative bounded profile performs 3 clean-process resume sessions and 8 deterministic soak cycles. Final durable database version is 2 with schema SHA-256 `a489ab34411a5f0ce00b02e09fde1be0a45b3935df6fa696267c3b15ebd91ff5`; failed migration rollback, memory tamper quarantine/recovery and artifact-registry recovery all succeed without promoting corrupt/partial state.
- Canonical cross-platform material SHA-256 values are identical: fixture `9bd8b2e63b1c17b351744e9552da7927c911e7da78ddcd8b25e4dc19a0e899b5`; semantic `1f128da121ebb957b7a1f29dc96007d381ef6ad4f2e340e3c59c10eb0f56dd7c`; policy `f921f368f516523f6a803fd01320a825cc8086189c1ebc77165fd9cd6f77dc05`; authority `be7bf480b34a47175bd4cf8c492ecd3b4d11a097cbe09ee2ba8f132ddda6d5b7`. The earlier raw-checkout-byte fixture digest was rejected as non-authoritative because LF/CRLF checkout differences changed it; the accepted source hashes canonical parsed JSON and includes an explicit LF/CRLF regression.
- Runtime evidence is truthful rather than normalized away: Ubuntu uses CPython 3.12.14 / SQLite 3.45.1; Windows uses CPython 3.12.10 / SQLite 3.49.1. Platform-specific project byte counts and evidence digests are allowed while material semantic/config/fixture authority digests remain identical.
- Exact technical-head artifacts from R16.15 #13 are Linux `9900010682 / sha256:2fee659600eb57e5e58a5988c08c238aeed9538d17e01b8dacff3eab01af96d7` with evidence SHA-256 `333b8a6a4c4caf76444c8800d3243182dcc21906d713c77418bdef810234c8ab`, and Windows `9900045779 / sha256:39fae32fc3e65bb004796a46c7391bea3f82f4bd7d04664f123aa0f918f90f3a` with evidence SHA-256 `653544c4d7555afa64529d53456618819d807ecf7bb720e85cd0abf1e3bbc1f4`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its resulting exact END head must receive fresh R16.15/R16.9/R0/Python/UI SUCCESS before PR #363 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.15 normalization is authorized after the implementation/evidence merge. Only the resulting normalized `main` may mark R16.15 **COMPLETE + NORMALIZED** and authorize R16.16 START.
"""
    plan_anchor = "\n---\n\n# R16.16 — Resource, concurrency, leak and diagnostics soak"
    plan = replace_once(
        plan,
        plan_anchor,
        "\n" + plan_end + "\n---\n\n# R16.16 — Resource, concurrency, leak and diagnostics soak",
        "plan R16.16 anchor",
    )

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    new_top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.14 COMPLETE + NORMALIZED. R16.15 COMPLETE at END-sync. R16.16–R16.18 remain PLANNED and unauthorized.** "
        f"R16.15 immutable technical source `{TECHNICAL_SHA}` passed fresh exact-head R16.15 #13 / `33771718895`, "
        "R16.9 #54 / `33771719752`, R0 #2374 / `33771719659`, Python Core #2346 / `33771718602` 5/5 and "
        "KodeStudio UI Smoke #2311 / `33771718965`. Acceptance is 20/20 PASS per OS with canonical cross-platform fixture, "
        "semantic, policy and authority digests; core manual NONE; optional extended local wall-clock soak CONDITIONAL / NOT TRIGGERED "
        "and `NOT_EXERCISED`. This documentation-only END-sync must now pass fresh exact-END R16.15/R16.9/R0/Python/UI before "
        "PR #363 exact-head merge; one continuity-only post-merge normalization remains mandatory before R16.16 START.\n\n"
    )
    continuity, count = top_re.subn(new_top, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity top paragraph anchor mismatch")

    global_re = re.compile(r"^- R16\.15 : \*\*IN_PROGRESS\*\* — .*?$", re.M)
    global_match = global_re.search(continuity)
    if global_match is None:
        raise SystemExit("continuity global R16.15 bullet anchor mismatch")
    global_line = (
        f"- R16.15 : **COMPLETE at END-sync** — normalized R16.14 `main` `{BASE_SHA}`; clean START `{START_SHA}`; "
        f"immutable technical source `{TECHNICAL_SHA}`; exact-technical-head R16.15 #13 / `33771718895` SUCCESS Ubuntu + Windows, "
        "R16.9 #54 / `33771719752` SUCCESS Ubuntu + Windows, R0 #2374 / `33771719659` SUCCESS Ubuntu + Windows, "
        "Python Core #2346 / `33771718602` SUCCESS 5/5 and UI #2311 / `33771718965` SUCCESS. Focused + supply-chain regression "
        "is 31/31 PASS per OS and durability acceptance is 20/20 PASS per OS with `durability_claim=true`, `critical_veto=false`, "
        "`secret_free=true`, zero external network calls and zero destructive host actions. Canonical cross-platform digests: fixture "
        "`9bd8b2e63b1c17b351744e9552da7927c911e7da78ddcd8b25e4dc19a0e899b5`; semantic "
        "`1f128da121ebb957b7a1f29dc96007d381ef6ad4f2e340e3c59c10eb0f56dd7c`; policy "
        "`f921f368f516523f6a803fd01320a825cc8086189c1ebc77165fd9cd6f77dc05`; authority "
        "`be7bf480b34a47175bd4cf8c492ecd3b4d11a097cbe09ee2ba8f132ddda6d5b7`. Three clean-process resumes and eight bounded soak cycles "
        "complete; final DB version 2 / schema `a489ab34411a5f0ce00b02e09fde1be0a45b3935df6fa696267c3b15ebd91ff5`; migration rollback, "
        "memory-tamper recovery and registry recovery succeed. Technical artifacts: Linux `9900010682 / sha256:2fee659600eb57e5e58a5988c08c238aeed9538d17e01b8dacff3eab01af96d7`; "
        "Windows `9900045779 / sha256:39fae32fc3e65bb004796a46c7391bea3f82f4bd7d04664f123aa0f918f90f3a`. Core manual NONE; optional extended local soak "
        "CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`. Fresh exact-END five-gate qualification, PR #363 expected-head merge and the unique "
        "post-merge continuity-only normalization remain mandatory before R16.16 START."
    )
    continuity = continuity[: global_match.start()] + global_line + continuity[global_match.end() :]

    continuity_end = f"""## R16.15 END authority

- R16.15 state: **COMPLETE at END-sync**; core manual **NONE**; optional extended wall-clock/local-environment soak **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`. R16.16 remains PLANNED and unauthorized.
- Exact normalized base `{BASE_SHA}`; clean START-sync `{START_SHA}`; immutable technical source `{TECHNICAL_SHA}`.
- Exact-technical-head gates are all SUCCESS: R16.15 #13 / `33771718895` Ubuntu + Windows; R16.9 #54 / `33771719752` Ubuntu + Windows; R0 #2374 / `33771719659` Ubuntu + Windows; Python Core #2346 / `33771718602` 5/5; KodeStudio UI Smoke #2311 / `33771718965`.
- Focused R16.15 plus R16.9 supply-chain regression is 31/31 PASS on each hosted OS; representative durability acceptance is 20/20 PASS per OS with `durability_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, no live credentials, zero external network calls and zero destructive host actions.
- Bounded authoritative soak performs 3 clean-process resumes and 8 cycles. Final durable DB version is 2 with schema SHA-256 `a489ab34411a5f0ce00b02e09fde1be0a45b3935df6fa696267c3b15ebd91ff5`; failed migration rollback, memory tamper quarantine/recovery and artifact-registry recovery succeed while corrupt/partial state remains non-authoritative.
- Accepted canonical cross-platform SHA-256 values are fixture `9bd8b2e63b1c17b351744e9552da7927c911e7da78ddcd8b25e4dc19a0e899b5`, semantic `1f128da121ebb957b7a1f29dc96007d381ef6ad4f2e340e3c59c10eb0f56dd7c`, policy `f921f368f516523f6a803fd01320a825cc8086189c1ebc77165fd9cd6f77dc05` and authority `be7bf480b34a47175bd4cf8c492ecd3b4d11a097cbe09ee2ba8f132ddda6d5b7`. The earlier raw-checkout-byte fixture digest is explicitly non-authoritative because LF/CRLF changed it; canonical parsed-JSON hashing plus a dedicated LF/CRLF regression closes that portability defect.
- Runtime differences remain explicit: Ubuntu CPython 3.12.14 / SQLite 3.45.1; Windows CPython 3.12.10 / SQLite 3.49.1. Platform-specific evidence SHA-256 is Linux `333b8a6a4c4caf76444c8800d3243182dcc21906d713c77418bdef810234c8ab` and Windows `653544c4d7555afa64529d53456618819d807ecf7bb720e85cd0abf1e3bbc1f4`.
- R16.15 #13 artifacts are Linux `9900010682 / sha256:2fee659600eb57e5e58a5988c08c238aeed9538d17e01b8dacff3eab01af96d7` and Windows `9900045779 / sha256:39fae32fc3e65bb004796a46c7391bea3f82f4bd7d04664f123aa0f918f90f3a`, both source-bound to `{TECHNICAL_SHA}`.
- This END-sync is restricted to `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`. The resulting exact END head must pass fresh R16.15/R16.9/R0/Python/UI before PR #363 may merge with exact expected-head protection.
- Exactly one post-merge continuity-only R16.15 normalization is authorized. Only its gated merge may mark R16.15 **COMPLETE + NORMALIZED** and authorize R16.16 START.

"""
    continuity = replace_once(
        continuity,
        "\n## R16 status index\n",
        "\n" + continuity_end + "## R16 status index\n",
        "continuity R16 status anchor",
    )
    continuity = replace_once(
        continuity,
        "| R16.15 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "| R16.15 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "continuity R16.15 status row",
    )

    next_re = re.compile(
        r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
        re.S,
    )
    next_block = (
        "## Next authorized action\n\n"
        "R16.15 is **COMPLETE at END-sync** on its documentation-only exact END candidate derived from immutable technical "
        f"source `{TECHNICAL_SHA}`. The next authorized action is fresh exact-END qualification by R16.15, R16.9, R0, "
        "Python Core and KodeStudio UI Smoke on that one exact head, followed only on full SUCCESS by PR #363 merge with "
        "`expected_head_sha` equal to the qualified head. Exactly one post-merge continuity-only R16.15 normalization must then "
        "pass fresh R0/Python/UI and merge with exact-head protection. R16.16 remains unauthorized until that normalized `main` "
        "exists; optional extended local wall-clock/environment soak remains CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`.\n\n"
        "## Permanent R-phase execution rule"
    )
    continuity, count = next_re.subn(next_block, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity next authorized action anchor mismatch")

    PLAN.write_text(plan, encoding="utf-8", newline="\n")
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
