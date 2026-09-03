from __future__ import annotations

import re
import subprocess
from pathlib import Path

TECHNICAL_SHA = "92505a002a77c29c5621cdfaa332d43385307b31"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != TECHNICAL_SHA:
        raise SystemExit("R16.14 END-sync helper is not running on the immutable technical source")

    subprocess.run(
        ["git", "diff", "--exit-code", TECHNICAL_SHA, "--", PLAN.as_posix(), CONTINUITY.as_posix()],
        check=True,
    )

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")

    old_checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.13 are COMPLETE + NORMALIZED. R16.14 is IN_PROGRESS on dedicated branch "
        "`r16/14-representative-audio-voice-cinematic-beta-workflow` from exact normalized `main` "
        "`429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; R16.15–R16.18 remain PLANNED. Core manual state is NONE; "
        "optional human listening/device-quality qualification is CONDITIONAL / NOT TRIGGERED. No R16.14 implementation preceded this START-sync."
    )
    new_checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.13 are COMPLETE + NORMALIZED. R16.14 is COMPLETE at END-sync on dedicated branch "
        "`r16/14-representative-audio-voice-cinematic-beta-workflow` from exact normalized `main` "
        "`429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`, with clean START `7ed6f09262fc259bd875fc76c4583b758474090b` "
        "and immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31`; R16.15–R16.18 remain PLANNED and unauthorized. "
        "Core manual state is NONE; optional human listening/device-quality qualification is CONDITIONAL / NOT TRIGGERED. "
        "Fresh exact-END R16.14/R16.9/R0/Python/UI re-gates are mandatory before PR #361 may merge, followed by exactly one "
        "post-merge continuity-only normalization before R16.15 START."
    )
    plan = replace_once(plan, old_checkpoint, new_checkpoint, "plan execution checkpoint")
    plan = replace_once(
        plan,
        "| R16.14 | Representative audio/voice/cinematic beta workflow | IN_PROGRESS | CONDITIONAL |",
        "| R16.14 | Representative audio/voice/cinematic beta workflow | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.14 status row",
    )

    plan_end = """## R16.14 END authority

- State: **COMPLETE at END-sync**; core manual **NONE**; optional human listening/device-quality qualification **CONDITIONAL / NOT TRIGGERED**. R16.15 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; clean START-sync `7ed6f09262fc259bd875fc76c4583b758474090b`; immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31`.
- Fresh exact-technical-head gates on that immutable source are all SUCCESS: R16.14 #2 / `33709267769` Ubuntu + Windows; R16.9 #47 / `33709267732` Ubuntu + Windows; R0 Repository Guard #2365 / `33709267690` Ubuntu + Windows; Python Core #2337 / `33709267539` 5/5; KodeStudio UI Smoke #2302 / `33709267641`.
- Representative media acceptance is **16/16 PASS** on both hosted OS paths with `security_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, `live_credentials_used=false`, `destructive_host_actions=false` and `external_network_calls=0`. Focused R16.14 plus R16.9 supply-chain regression tests also pass on both OS paths.
- The authoritative CI fixture is explicit synthetic media: `fixture_is_synthetic_audio=true`, `fixture_is_real_tts_runtime=false`, `fixture_is_human_listened=false`; optional human/device listening remains `NOT_EXERCISED`, so no real TTS engine, microphone, speaker, playback-device or subjective-quality claim is inferred.
- Accepted audio facts are deterministic and cross-platform: mono 16-bit PCM WAV, 16000 Hz, 16000 frames, 1.0 second, zero clipped samples. Workspace escape, unsafe external reference, unapproved voice identity/profile use, malformed/unsafe markup, resource-boundary and cancellation/partial-output promotion controls fail closed as required.
- Canonical cross-platform SHA-256 values are identical for material semantics: fixture `bee1f3459d97bc059de630c49afd75aa8156ba14ae3367151660d791f5f5a452`; text `7ac74b671415b23c03a7a044514cf3e5560a9b5b760b31e2c46c857c804ff2d7`; profile `5b3c28c2afd1ac53f1a4e7834bf5e0adc1bde8cb5227250deda853e6f0446dd3`; voice binding `904865b55a531339d527b16be0d3acfc429aa7fa4a322c5ba9550070e6e9f68b`; TTS request `4f2cd932ac4a1e02c78b614eb39226b05909a774925c6abb5ee210be6a5403db`; audio `4d4a7b63ec4e6c9765e5451ec36b4c2c9d28f5fb3a69cba1886d67b9bd29966f`; alignment `e7bf2de62066cfdd2c0c56f9f46e375fdc135cde16821b2047470f1b591da478`; viseme `9bb00001a32380616488ac85b91d8480e1d8e923fed486811af299a354927349`; cinematic `55e4a9044e8cfb8e8cd14cbf0ed574f7f3581061c88cd590ad52670e22bde6d9`; binding `210a9a6cc10890ff4d5467b9783373d45417358181a144d8d060f7b0726a703d`; semantic `62db8be0c807002d2a04549db58a509b613cf6ba18d9493af82e98f3c1bdc3fd`.
- Exact technical-head artifacts from R16.14 #2: Linux `9876404530 / sha256:144502ee168b12fd8e8018da236e7c109fdaf79f17bd98bd0ddeb1c27dc78ee9`; Windows `9876415748 / sha256:20f3669edd24624dd43ca3313c5a8197d7e66104b8861dbd79074cfc4a1d3506`. Report file SHA-256 is Linux `3c5f9b7f857855061b4a473dc643baaacdd4eb4dfd9943ec96837a790919fa9e` and Windows `1a572d3986f653a6de23bf8f61223828f25d859ddc1a362fc507ab9d8ecf55a6`; platform-specific evidence SHA-256 is Linux `4f4419fc01410e68acf3d6fb20a6e4655e4a0ed8149d361bfdbbb0a4fab1c55f` and Windows `9096479309bd95a7f788cdf718a7a6a9fad8845ac5dee05e325a4b901a8690ad`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its resulting exact END head must receive fresh R16.14/R16.9/R0/Python/UI SUCCESS before PR #361 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.14 normalization is authorized after the implementation/evidence merge. Only the resulting normalized `main` may mark R16.14 **COMPLETE + NORMALIZED** and authorize R16.15 START.
"""
    plan_anchor = "\n---\n\n# R16.15 — Long-term project durability, resume and upgrade soak"
    plan = replace_once(
        plan,
        plan_anchor,
        "\n" + plan_end + "\n---\n\n# R16.15 — Long-term project durability, resume and upgrade soak",
        "plan R16.15 anchor",
    )

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    new_top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.13 COMPLETE + NORMALIZED. R16.14 COMPLETE at END-sync. R16.15–R16.18 remain PLANNED and unauthorized.** "
        "R16.14 immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31` passed fresh exact-head R16.14 #2 / "
        "`33709267769`, R16.9 #47 / `33709267732`, R0 #2365 / `33709267690`, Python Core #2337 / `33709267539` 5/5 "
        "and KodeStudio UI Smoke #2302 / `33709267641`. Core manual NONE; optional human listening/device-quality qualification "
        "CONDITIONAL / NOT TRIGGERED and `NOT_EXERCISED`. This documentation-only END-sync must now pass fresh exact-END "
        "R16.14/R16.9/R0/Python/UI before PR #361 exact-head merge; one continuity-only post-merge normalization remains mandatory "
        "before R16.15 START.\n\n"
    )
    continuity, count = top_re.subn(new_top, continuity, count=1)
    if count != 1:
        raise SystemExit("continuity top paragraph anchor mismatch")

    global_re = re.compile(r"^- R16\.13 : \*\*COMPLETE \+ NORMALIZED\*\* — .*?$", re.M)
    global_match = global_re.search(continuity)
    if global_match is None:
        raise SystemExit("continuity global R16.13 bullet anchor mismatch")
    global_line = (
        "- R16.14 : **COMPLETE at END-sync** — normalized R16.13 `main` `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; "
        "clean START `7ed6f09262fc259bd875fc76c4583b758474090b`; immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31`; "
        "exact-technical-head R16.14 #2 / `33709267769` SUCCESS Ubuntu + Windows, R16.9 #47 / `33709267732` SUCCESS Ubuntu + Windows, "
        "R0 #2365 / `33709267690` SUCCESS Ubuntu + Windows, Python Core #2337 / `33709267539` SUCCESS 5/5 and UI #2302 / `33709267641` SUCCESS. "
        "Representative acceptance 16/16 PASS with `security_claim=true`, `critical_veto=false`, `secret_free=true`, zero live credentials, "
        "zero destructive host actions and zero external network calls. Canonical digests: fixture `bee1f3459d97bc059de630c49afd75aa8156ba14ae3367151660d791f5f5a452`; "
        "audio `4d4a7b63ec4e6c9765e5451ec36b4c2c9d28f5fb3a69cba1886d67b9bd29966f`; alignment `e7bf2de62066cfdd2c0c56f9f46e375fdc135cde16821b2047470f1b591da478`; "
        "viseme `9bb00001a32380616488ac85b91d8480e1d8e923fed486811af299a354927349`; cinematic `55e4a9044e8cfb8e8cd14cbf0ed574f7f3581061c88cd590ad52670e22bde6d9`; "
        "binding `210a9a6cc10890ff4d5467b9783373d45417358181a144d8d060f7b0726a703d`; semantic `62db8be0c807002d2a04549db58a509b613cf6ba18d9493af82e98f3c1bdc3fd`. "
        "Technical-head artifacts: Linux `9876404530 / sha256:144502ee168b12fd8e8018da236e7c109fdaf79f17bd98bd0ddeb1c27dc78ee9`; Windows "
        "`9876415748 / sha256:20f3669edd24624dd43ca3313c5a8197d7e66104b8861dbd79074cfc4a1d3506`. Fixture is synthetic; real TTS runtime and human/device "
        "listening remain `NOT_EXERCISED`; core manual NONE; optional listening qualification CONDITIONAL / NOT TRIGGERED. Fresh exact-END five-gate qualification, "
        "PR #361 expected-head merge and the unique post-merge continuity-only normalization remain mandatory before R16.15 START."
    )
    insert_at = global_match.end()
    continuity = continuity[:insert_at] + "\n" + global_line + continuity[insert_at:]

    continuity = replace_once(
        continuity,
        "| R16.14 | IN_PROGRESS | CONDITIONAL |",
        "| R16.14 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "continuity R16.14 status index",
    )

    continuity_end = """## R16.14 END authority

- R16.14 state: **COMPLETE at END-sync**; core manual **NONE**; optional human listening/device-quality qualification **CONDITIONAL / NOT TRIGGERED**. R16.15 remains PLANNED and unauthorized.
- Exact normalized base `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; clean START-sync `7ed6f09262fc259bd875fc76c4583b758474090b`; immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31`.
- Exact-technical-head gates are all SUCCESS: R16.14 #2 / `33709267769` Ubuntu + Windows; R16.9 #47 / `33709267732` Ubuntu + Windows; R0 #2365 / `33709267690` Ubuntu + Windows; Python Core #2337 / `33709267539` 5/5; KodeStudio UI Smoke #2302 / `33709267641`.
- Representative media acceptance is 16/16 PASS, `security_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, no live credentials, no destructive host actions and zero external network calls. Focused R16.14 plus R16.9 regression tests pass on both hosted OS paths.
- CI is repository-owned synthetic media: `fixture_is_synthetic_audio=true`, `fixture_is_real_tts_runtime=false`, `fixture_is_human_listened=false`; optional human/device listening is `NOT_EXERCISED`. No real TTS runtime, microphone, speakers, device playback or subjective listening-quality claim is inferred.
- Accepted deterministic audio is mono 16-bit PCM WAV at 16000 Hz for 1.0 second / 16000 frames with zero clipped samples. Voice governance, markup rejection, path/external-reference confinement, resource bounds, cancellation and partial-output non-promotion remain fail-closed.
- Cross-platform canonical digests: fixture `bee1f3459d97bc059de630c49afd75aa8156ba14ae3367151660d791f5f5a452`; text `7ac74b671415b23c03a7a044514cf3e5560a9b5b760b31e2c46c857c804ff2d7`; profile `5b3c28c2afd1ac53f1a4e7834bf5e0adc1bde8cb5227250deda853e6f0446dd3`; voice binding `904865b55a531339d527b16be0d3acfc429aa7fa4a322c5ba9550070e6e9f68b`; TTS request `4f2cd932ac4a1e02c78b614eb39226b05909a774925c6abb5ee210be6a5403db`; audio `4d4a7b63ec4e6c9765e5451ec36b4c2c9d28f5fb3a69cba1886d67b9bd29966f`; alignment `e7bf2de62066cfdd2c0c56f9f46e375fdc135cde16821b2047470f1b591da478`; viseme `9bb00001a32380616488ac85b91d8480e1d8e923fed486811af299a354927349`; cinematic `55e4a9044e8cfb8e8cd14cbf0ed574f7f3581061c88cd590ad52670e22bde6d9`; binding `210a9a6cc10890ff4d5467b9783373d45417358181a144d8d060f7b0726a703d`; semantic `62db8be0c807002d2a04549db58a509b613cf6ba18d9493af82e98f3c1bdc3fd`.
- R16.14 #2 artifacts: Linux `9876404530 / sha256:144502ee168b12fd8e8018da236e7c109fdaf79f17bd98bd0ddeb1c27dc78ee9`; Windows `9876415748 / sha256:20f3669edd24624dd43ca3313c5a8197d7e66104b8861dbd79074cfc4a1d3506`. Report SHA-256: Linux `3c5f9b7f857855061b4a473dc643baaacdd4eb4dfd9943ec96837a790919fa9e`; Windows `1a572d3986f653a6de23bf8f61223828f25d859ddc1a362fc507ab9d8ecf55a6`.
- This END-sync is documentation-only relative to `92505a002a77c29c5621cdfaa332d43385307b31`. Its exact resulting head must pass fresh R16.14/R16.9/R0/Python/UI before PR #361 merges with exact `expected_head_sha`. Exactly one post-merge continuity-only normalization is then required; only that normalized `main` may authorize R16.15 START.
"""
    continuity = replace_once(
        continuity,
        "\n## R16 status index\n",
        "\n" + continuity_end + "\n## R16 status index\n",
        "continuity R16 status index anchor",
    )

    old_next = (
        "R16.14 — **Representative audio/voice/cinematic beta workflow** — is the active authorized subdivision on "
        "`r16/14-representative-audio-voice-cinematic-beta-workflow` from exact normalized `main` "
        "`429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`. START-sync is complete before implementation. Implement only the frozen R16.14 scope: "
        "repository-owned synthetic/public-domain media fixture, audio QA, supported TTS path, voice governance, alignment/visemes, cinematic timing/metadata, "
        "workspace/provenance boundaries, malformed markup/external-reference negatives, resource budgets, cancellation/failure and partial-output non-promotion. "
        "Core manual **NONE**; optional human listening/device-quality qualification remains **CONDITIONAL / NOT TRIGGERED** and does not affect core CI unless explicitly requested."
    )
    new_next = (
        "R16.14 — **Representative audio/voice/cinematic beta workflow** — is COMPLETE at END-sync on immutable technical source "
        "`92505a002a77c29c5621cdfaa332d43385307b31`. The next authorized action is fresh exact-END R16.14/R16.9/R0/Python/UI qualification "
        "of this documentation-only END head, followed only if all five authorities are SUCCESS by PR #361 merge with exact `expected_head_sha` and exactly one "
        "post-merge continuity-only normalization with fresh R0/Python/UI. R16.15 remains PLANNED and unauthorized until that normalized `main` exists. "
        "Core manual **NONE**; optional human listening/device-quality qualification remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`."
    )
    continuity = replace_once(continuity, old_next, new_next, "continuity next authorized action")

    PLAN.write_text(plan, encoding="utf-8", newline="\n")
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")

    changed = subprocess.check_output(
        ["git", "diff", "--name-only", TECHNICAL_SHA, "--"], text=True
    ).splitlines()
    expected = sorted([PLAN.as_posix(), CONTINUITY.as_posix()])
    if sorted(changed) != expected:
        raise SystemExit(f"unexpected END-sync diff: {changed}")

    subprocess.run(["git", "diff", "--check", TECHNICAL_SHA, "--", *expected], check=True)


if __name__ == "__main__":
    main()
