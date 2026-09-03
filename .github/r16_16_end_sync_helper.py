from __future__ import annotations

import re
import subprocess
from pathlib import Path

TECHNICAL_SHA = "fb34d4a92131fa5cc51e3211405ac38908246d6c"
BASE_SHA = "d19a8b1fa32fa5e28fa23b036407bc5bd902ef92"
START_SHA = "ff971a012a0066b995d52deb1e4e8b0ac0a413de"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, got {count}")
    return updated


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != TECHNICAL_SHA:
        raise SystemExit(f"R16.16 END helper must run on {TECHNICAL_SHA}, got {head}")

    subprocess.run(
        ["git", "diff", "--exit-code", TECHNICAL_SHA, "--", str(PLAN), str(CONTINUITY)],
        check=True,
    )

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")
    if "## R16.16 END authority" in plan or "## R16.16 END authority" in continuity:
        raise SystemExit("R16.16 END authority already exists")

    plan_checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.15 are COMPLETE + NORMALIZED. R16.16 is COMPLETE at END-sync on dedicated branch "
        "`r16/16-resource-concurrency-leak-diagnostics-soak` from exact normalized `main` "
        f"`{BASE_SHA}`, with clean START `{START_SHA}` and immutable technical source `{TECHNICAL_SHA}`; "
        "R16.17–R16.18 remain PLANNED and unauthorized. Fresh exact-technical-head gates are SUCCESS: "
        "R16.16 #6 / `33777526743` Ubuntu + Windows, R16.9 #58 / `33777526756` Ubuntu + Windows, "
        "R0 #2380 / `33777526844` Ubuntu + Windows, Python Core #2352 / `33777526769` 5/5 and "
        "KodeStudio UI Smoke #2317 / `33777526726`. R16.16 manual state is NONE. Fresh exact-END "
        "R16.16/R16.9/R0/Python/UI re-gates, PR #365 exact-head merge and exactly one continuity-only "
        "post-merge normalization remain mandatory before R16.17 START."
    )
    plan = regex_once(
        plan,
        r"^\*\*Execution checkpoint:\*\*.*$",
        plan_checkpoint,
        "plan execution checkpoint",
    )
    plan = replace_once(
        plan,
        "| R16.16 | Resource, concurrency, leak and diagnostics soak | IN_PROGRESS | NONE |",
        "| R16.16 | Resource, concurrency, leak and diagnostics soak | COMPLETE | NONE |",
        "plan R16.16 status row",
    )

    end_authority = f"""## R16.16 END authority

- R16.16 state: **COMPLETE at END-sync**; manual intervention **NONE**. R16.17–R16.18 remain **PLANNED** and unauthorized.
- Exact normalized base: `main` `{BASE_SHA}`; clean START-sync `{START_SHA}`; immutable technical source `{TECHNICAL_SHA}`.
- Fresh exact-technical-head gates are all SUCCESS: R16.16 #6 / `33777526743` Ubuntu + Windows; R16.9 #58 / `33777526756` Ubuntu + Windows; R0 Repository Guard #2380 / `33777526844` Ubuntu + Windows; Python Core #2352 / `33777526769` 5/5; KodeStudio UI Smoke #2317 / `33777526726`.
- Focused R16.16 plus R16.9 supply-chain regression is **36/36 PASS** on both hosted OS paths. Representative resource/concurrency/leak/diagnostics acceptance is **18/18 PASS** per OS with `resource_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=NONE`, `external_network_calls=0` and `destructive_host_actions=0`.
- Five bounded representative profiles (`code`, `comfyui`, `desktop`, `godot`, `media`) are stable across repeats. Each repetition executes 15 operations and generates 565248 transient bytes before complete cleanup; temporary files/bytes and thread delta are zero after each repetition.
- Four workers reach the governed cancellation boundary; all four are cancelled with `post_cancel_mutations=0` and consistent state. Two ProcessSandbox/KillSwitch child processes are signalled and unregistered with `active_after=0` and complete cleanup.
- Canonical cross-platform material SHA-256 values are identical: fixture `72a344812fbcca004dc3b4047b33e5488c2d7da85007a4568d8148034b9ce74c`; policy `f1222282157aa947b8fbeee223e95ad1604cb65a60889745ba186eb9ca3c75de`; semantic `92e9dad3a2d5e0a02e44f5f6c3d8bb6d1d83a438fe87e5565b3aa669a0638dfc`; authority `7e2f33450b1b4ae3a119435385c99cbcdb8d64138197fb20e869129e69e01001`; representative-profile semantic `749eaf6bcb2b6ea2999baa0a6d43917527e270e827803b3f0b602fce6be60206`.
- CPU measurement and the absolute CPU budget are PASS on both hosted OS paths. Repeat-to-repeat CPU variance is truthfully `INCONCLUSIVE` when samples are below the frozen 50 ms significance floor, while a dedicated significant 22x regression negative control still fails closed. VRAM remains `INCONCLUSIVE` on hosted runners rather than a synthetic PASS; if VRAM becomes required, unknown capacity blocks the claim.
- Runtime evidence remains explicit: Ubuntu CPython 3.12.14 with `posix-maxrss`; Windows CPython 3.12.10 with governed `tracemalloc` fallback where the portable working-set probe is unavailable.
- Exact technical-head R16.16 #6 artifacts: Linux `9902269140 / sha256:0838eb2baedb8aed20630778e784296effbf56f002d9398ddc0f9c3ffb2816cc` with evidence SHA-256 `6ae8dd7efcf4f84fab1957c04b03fac2c65f4ac410d29e2636a5ffd6f7a60afa`; Windows `9902209604 / sha256:38463b81bf4ce262fb8c311e857c02061482c3059584a6ae0ff335e6cf587958` with evidence SHA-256 `ca2779324eae245b3e2669b0c6fb9f98db44b6f372761902a6fd8e733a67320c`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its exact resulting head must pass fresh R16.16/R16.9/R0/Python/UI SUCCESS before PR #365 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.16 normalization is authorized. Only the resulting normalized `main` may mark R16.16 **COMPLETE + NORMALIZED** and authorize R16.17 START.
"""
    plan = replace_once(
        plan,
        "\n---\n\n# R16.17 — v1.0 packaging, migration, rollback and release readiness",
        "\n" + end_authority + "\n---\n\n# R16.17 — v1.0 packaging, migration, rollback and release readiness",
        "plan R16.17 boundary",
    )
    PLAN.write_text(plan, encoding="utf-8", newline="\n")

    continuity_top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + "
        "NORMALIZED. R16.1–R16.15 COMPLETE + NORMALIZED. R16.16 COMPLETE at END-sync. R16.17–R16.18 "
        "remain PLANNED and unauthorized.** R16.16 immutable technical source "
        f"`{TECHNICAL_SHA}` passed fresh exact-head R16.16 #6 / `33777526743`, R16.9 #58 / "
        "`33777526756`, R0 #2380 / `33777526844`, Python Core #2352 / `33777526769` 5/5 and "
        "KodeStudio UI Smoke #2317 / `33777526726`. Acceptance is 18/18 PASS per OS with canonical "
        "cross-platform fixture/policy/semantic/authority digests, zero post-cancel mutation, zero orphan "
        "process and diagnostics redaction; CPU repeatability below 50 ms and hosted-runner VRAM remain "
        "truthfully INCONCLUSIVE while hard budgets remain PASS/fail-closed. Manual NONE. This "
        "documentation-only END-sync must now pass fresh exact-END R16.16/R16.9/R0/Python/UI before PR "
        "#365 exact-head merge; one continuity-only post-merge normalization remains mandatory before "
        "R16.17 START.\n\n"
    )
    continuity = regex_once(
        continuity,
        r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n",
        continuity_top,
        "continuity top checkpoint",
    )

    global_line = (
        f"- R16.16 : **COMPLETE at END-sync** — normalized R16.15 `main` `{BASE_SHA}`; clean START "
        f"`{START_SHA}`; immutable technical source `{TECHNICAL_SHA}`; exact-technical-head R16.16 #6 / "
        "`33777526743` SUCCESS Ubuntu + Windows, R16.9 #58 / `33777526756` SUCCESS Ubuntu + Windows, "
        "R0 #2380 / `33777526844` SUCCESS Ubuntu + Windows, Python Core #2352 / `33777526769` SUCCESS "
        "5/5 and UI #2317 / `33777526726` SUCCESS. Focused plus supply-chain regression is 36/36 PASS "
        "per OS and representative acceptance is 18/18 PASS per OS; canonical fixture `72a344812fbcca004dc3b4047b33e5488c2d7da85007a4568d8148034b9ce74c`, "
        "policy `f1222282157aa947b8fbeee223e95ad1604cb65a60889745ba186eb9ca3c75de`, semantic "
        "`92e9dad3a2d5e0a02e44f5f6c3d8bb6d1d83a438fe87e5565b3aa669a0638dfc` and authority "
        "`7e2f33450b1b4ae3a119435385c99cbcdb8d64138197fb20e869129e69e01001` match cross-platform; four "
        "workers cancel with zero post-cancel mutation, two child processes clean to active_after=0, temp "
        "and thread deltas return to zero. CPU absolute budget is PASS while sub-50 ms repeat variance and "
        "hosted VRAM are truthfully INCONCLUSIVE. Exact technical artifacts: Linux `9902269140 / "
        "sha256:0838eb2baedb8aed20630778e784296effbf56f002d9398ddc0f9c3ffb2816cc`; Windows `9902209604 / "
        "sha256:38463b81bf4ce262fb8c311e857c02061482c3059584a6ae0ff335e6cf587958`. Manual NONE. Fresh "
        "exact-END five-gate qualification, PR #365 exact-head merge and the unique post-merge "
        "continuity-only normalization remain mandatory before R16.17 START."
    )
    r16_15_pattern = r"^(- R16\.15 : \*\*COMPLETE \+ NORMALIZED\*\* — .*?)$"
    match = re.search(r16_15_pattern, continuity, flags=re.MULTILINE)
    if match is None:
        raise SystemExit("continuity R16.15 global authority anchor missing")
    continuity = continuity[: match.end()] + "\n" + global_line + continuity[match.end() :]

    continuity = replace_once(
        continuity,
        "| R16.16 | IN_PROGRESS | NONE |",
        "| R16.16 | COMPLETE | NONE |",
        "continuity R16.16 status row",
    )
    continuity = replace_once(
        continuity,
        "- No R16.16 implementation bytes precede this START-sync.\n\n## R16 status index",
        "- No R16.16 implementation bytes precede this START-sync.\n\n" + end_authority + "\n## R16 status index",
        "continuity R16.16 END insertion",
    )

    next_action = (
        "## Next authorized action\n\n"
        f"R16.16 is **COMPLETE at END-sync** on exact immutable technical source `{TECHNICAL_SHA}` after "
        "fresh technical-head R16.16/R16.9/R0/Python/UI success. The only authorized next action inside "
        "R16.16 is fresh qualification of the exact documentation END head by those same five authorities, "
        "followed by PR #365 merge only with `expected_head_sha` equal to that exact successful END head, "
        "then exactly one continuity-only post-merge normalization with fresh R0 + full Python Core + "
        "KodeStudio UI Smoke. **No R16.17 action is authorized before the normalized main produced by that "
        "single normalization merge.** Manual intervention remains NONE.\n\n"
        "## Permanent R-phase execution rule"
    )
    continuity = regex_once(
        continuity,
        r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
        next_action,
        "continuity next authorized action",
    )
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")

    changed = subprocess.check_output(
        ["git", "diff", "--name-only", TECHNICAL_SHA], text=True
    ).splitlines()
    expected = sorted([str(CONTINUITY), str(PLAN)])
    if sorted(changed) != expected:
        raise SystemExit(f"unexpected END-sync surface: {changed!r}")
    subprocess.run(["git", "diff", "--check", TECHNICAL_SHA], check=True)


if __name__ == "__main__":
    main()
