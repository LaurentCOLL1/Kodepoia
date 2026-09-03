from __future__ import annotations

import re
from pathlib import Path

BASE = "429a018192bcb00221f9fc4e6ae64d0fdbc40cfd"
BRANCH = "r16/14-representative-audio-voice-cinematic-beta-workflow"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def sub_once(text: str, pattern: str, replacement: str, *, flags: int = 0, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return updated


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


plan = PLAN.read_text(encoding="utf-8")
continuity = CONTINUITY.read_text(encoding="utf-8")

plan_checkpoint = (
    "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
    "R16.1–R16.13 are COMPLETE + NORMALIZED. R16.14 is IN_PROGRESS on dedicated branch "
    f"`{BRANCH}` from exact normalized `main` `{BASE}`; R16.15–R16.18 remain PLANNED. "
    "Core manual state is NONE; optional human listening/device-quality qualification is CONDITIONAL / NOT TRIGGERED. "
    "No R16.14 implementation preceded this START-sync."
)
plan = sub_once(
    plan,
    r"(?m)^\*\*Execution checkpoint:\*\*.*$",
    plan_checkpoint,
    label="plan execution checkpoint",
)
plan = replace_once(
    plan,
    "| R16.13 | Representative ComfyUI beta workflow | COMPLETE | CONDITIONAL |\n"
    "| R16.14 | Representative audio/voice/cinematic beta workflow | PLANNED | CONDITIONAL |",
    "| R16.13 | Representative ComfyUI beta workflow | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |\n"
    "| R16.14 | Representative audio/voice/cinematic beta workflow | IN_PROGRESS | CONDITIONAL |",
    label="plan frozen index",
)
plan_manual_anchor = (
    "**CONDITIONAL.** Only for an explicitly requested human listening/device-quality claim; core acceptance is automated.\n\n---"
)
plan_start = f"""**CONDITIONAL.** Only for an explicitly requested human listening/device-quality claim; core acceptance is automated.

## R16.14 START authority

- State: **IN_PROGRESS**; core manual **NONE**; optional human listening/device-quality qualification **CONDITIONAL / NOT TRIGGERED** and only if explicitly requested.
- Exact normalized base: `main` `{BASE}`; dedicated branch `{BRANCH}` created directly from that SHA before implementation.
- Prior state: R16.1–R16.13 **COMPLETE + NORMALIZED**; R16.15–R16.18 remain **PLANNED**.
- Frozen scope is unchanged: one repository-owned short media scenario using synthetic/public-domain text/audio fixtures; audio inspection/QA; supported TTS path; voice-governance/profile checks; alignment/viseme generation; cinematic timing/metadata flow; workspace-bounded generated media/output paths with source/provenance linkage; malformed/unsafe markup and external-reference rejection; resource limits; cancellation/failure with partial-output non-promotion.
- No R16.14 implementation preceded this START-sync. Core acceptance requires no microphone, speakers, device playback, live provider credentials, external service, or destructive host action.

---"""
plan = replace_once(plan, plan_manual_anchor, plan_start, label="plan R16.14 START insertion")

continuity_header = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
    "R16.1–R16.13 COMPLETE + NORMALIZED. R16.14 IN_PROGRESS. R16.15–R16.18 remain PLANNED and unauthorized.** "
    "R16.13 normalization candidate `e1951afa5785a823090500a9a039a4ed8385fce8` passed fresh R0 #2363 / `33706746273` SUCCESS Ubuntu + Windows, "
    "Python Core #2335 / `33706746284` SUCCESS 5/5 and KodeStudio UI Smoke #2300 / `33706746134` SUCCESS, then PR #360 merged with exact expected head as normalized "
    f"`main` `{BASE}`. R16.14 START-sync is authoritative only on `{BRANCH}` created directly from that exact normalized main; no R16.14 implementation preceded the sync. "
    "Core manual NONE; optional human listening/device-quality qualification CONDITIONAL / NOT TRIGGERED."
)
continuity = sub_once(
    continuity,
    r"(?m)^> Kodepoia, architecture v1\.0 gelée\..*$",
    continuity_header,
    label="continuity header",
)

old_tail = (
    "This record is the unique post-merge continuity-only R16.13 normalization authority when its exact candidate passes fresh R0/Python/UI and merges. "
    "R16.14 START-sync is authorized only from the resulting normalized `main`."
)
new_tail = (
    "Post-merge normalization candidate `e1951afa5785a823090500a9a039a4ed8385fce8` passed fresh R0 #2363 / `33706746273` SUCCESS Ubuntu + Windows, "
    "Python Core #2335 / `33706746284` SUCCESS 5/5 and UI #2300 / `33706746134` SUCCESS; PR #360 merged with "
    f"`expected_head_sha=e1951afa5785a823090500a9a039a4ed8385fce8` as normalized `main` `{BASE}`. "
    f"R16.14 START-sync is authorized only from this exact normalized main and is now synchronized on `{BRANCH}` before implementation."
)
continuity = replace_once(continuity, old_tail, new_tail, label="continuity R16.13 global closure")

normalization_and_start = f"""## R16.13 post-merge normalization authority

- Implementation/evidence PR #359 merged final exact-END head `d002d359715a9e34690a97800d276e776b0ac4a0` with exact `expected_head_sha` as `main` `38cd16fb7f99eaa46a11d83994a0fe50ce576f80`.
- Final exact-END gates were R16.13 #7 / `33686092457` SUCCESS Ubuntu + Windows; R16.9 #45 / `33686091948` SUCCESS Ubuntu + Windows; R0 #2361 / `33686091989` SUCCESS Ubuntu + Windows; Python Core #2333 / `33686092442` SUCCESS 5/5; KodeStudio UI Smoke #2298 / `33686092476` SUCCESS.
- Unique continuity-only normalization candidate `e1951afa5785a823090500a9a039a4ed8385fce8` changed only `docs/continuity/KODEPOIA_CONTINUITY.md` relative to `38cd16fb7f99eaa46a11d83994a0fe50ce576f80` and passed fresh R0 #2363 / `33706746273` SUCCESS Ubuntu + Windows, Python Core #2335 / `33706746284` SUCCESS 5/5 and KodeStudio UI Smoke #2300 / `33706746134` SUCCESS.
- PR #360 merged with exact `expected_head_sha=e1951afa5785a823090500a9a039a4ed8385fce8` as normalized `main` `{BASE}`.
- R16.13 final state is **COMPLETE + NORMALIZED**. Core manual state remains **NONE**; optional true local ComfyUI/GPU qualification remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`.
- Only normalized `main` `{BASE}` authorizes R16.14 START-sync.

## R16.14 START authority

- R16.14 state: **IN_PROGRESS**; core manual **NONE**; optional human listening/device-quality qualification **CONDITIONAL / NOT TRIGGERED** and only if explicitly requested.
- Exact normalized base: `main` `{BASE}`; dedicated branch `{BRANCH}` created directly from that SHA before implementation.
- R16.1–R16.13 are **COMPLETE + NORMALIZED**; R16.15–R16.18 remain **PLANNED**.
- Frozen scope: repository-owned short media scenario using synthetic/public-domain text/audio fixtures; audio inspection/QA; supported TTS; voice governance/profiles; alignment/visemes; cinematic timing/metadata; workspace-bound outputs and provenance; unsafe markup/external-reference rejection; bounded resources; cancellation/failure with partial-output non-promotion.
- No R16.14 implementation preceded this START-sync. Core CI requires no microphone, speakers, device playback, live provider credentials, external service, or destructive host action.

## R16 status index"""
continuity = sub_once(
    continuity,
    r"(?s)## R16\.13 post-merge normalization authority\n\n.*?\n\n## R16 status index",
    normalization_and_start,
    label="continuity normalization closure and R16.14 START",
)
continuity = replace_once(
    continuity,
    "| R16.14 | PLANNED | CONDITIONAL |",
    "| R16.14 | IN_PROGRESS | CONDITIONAL |",
    label="continuity R16.14 status index",
)

next_action = f"""## Next authorized action

R16.14 — **Representative audio/voice/cinematic beta workflow** — is the active authorized subdivision on `{BRANCH}` from exact normalized `main` `{BASE}`. START-sync is complete before implementation. Implement only the frozen R16.14 scope: repository-owned synthetic/public-domain media fixture, audio QA, supported TTS path, voice governance, alignment/visemes, cinematic timing/metadata, workspace/provenance boundaries, malformed markup/external-reference negatives, resource budgets, cancellation/failure and partial-output non-promotion. Core manual **NONE**; optional human listening/device-quality qualification remains **CONDITIONAL / NOT TRIGGERED** and does not affect core CI unless explicitly requested.

## Permanent R-phase execution rule"""
continuity = sub_once(
    continuity,
    r"(?s)## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
    next_action,
    label="continuity next action",
)

PLAN.write_text(plan, encoding="utf-8", newline="\n")
CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")
