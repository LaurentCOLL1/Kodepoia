from pathlib import Path
import re

path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = path.read_text(encoding="utf-8")

old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.8 COMPLETE + NORMALIZED (normalization PR pending merge). R14.9–R14.17 PLANNED.** R14.8 source technique immuable `8132c4029983f693a32e0d26903d05e347313bf6`; END-head exact `954991537fc8c076169993ea106303421b8edd60`; R0 #1832, Python Core #1806, UI #1773 et Cloud Save Acceptance #16 sont SUCCESS; PR #271 a fusionné avec expected-head comme merge `5b51967c63ad5ae5ccc2df89f76aa48831ee2762`. La présente branche `r14/08-normalize-continuity` est l’unique normalisation continuity-only autorisée : valider son HEAD exact avec R0 + full Python Core + KodeStudio UI Smoke, puis merger avec expected-head avant toute R14.9. Manual intervention : NONE."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.8 COMPLETE + NORMALIZED. R14.9 IN_PROGRESS. R14.10–R14.17 PLANNED.** R14.8 est définitivement normalisée sur `main` `433c86cc5d43bfea41adb529451367e10c75a30b` après PR #272. R14.9 démarre exactement de ce SHA sur `r14/09-progression-leaderboards`. Frozen scope : définitions achievement/stat/leaderboard immuables et versionnées, progression seulement depuis événements/commandes autoritatifs validés, unlock/progress idempotents, score ordering/tie/period/reset explicites, snapshots de classement déterministes, écritures directes de score client interdites, privacy/display controls et queries provider-neutral. Manual intervention : NONE."
assert text.count(old_prompt) == 1, text.count(old_prompt)
text = text.replace(old_prompt, new_prompt)

text = text.replace(
    "- R14.1–R14.7 : **COMPLETE + NORMALIZED**.\n- R14.8 : **COMPLETE + NORMALIZED (normalization PR pending merge)** ; source technique immuable `8132c4029983f693a32e0d26903d05e347313bf6`, END-head `954991537fc8c076169993ea106303421b8edd60`, implementation/evidence merge `5b51967c63ad5ae5ccc2df89f76aa48831ee2762`.\n- R14.9–R14.17 : **PLANNED**.",
    "- R14.1–R14.8 : **COMPLETE + NORMALIZED**.\n- R14.8 normalized `main` : **`433c86cc5d43bfea41adb529451367e10c75a30b`** après normalization PR #272.\n- R14.9 : **IN_PROGRESS** sur `r14/09-progression-leaderboards`, base exacte `433c86cc5d43bfea41adb529451367e10c75a30b`.\n- R14.10–R14.17 : **PLANNED**."
)
assert "- R14.9 : **IN_PROGRESS**" in text
assert text.count("| R14.9 | PLANNED | NONE |") == 1
text = text.replace("| R14.9 | PLANNED | NONE |", "| R14.9 | IN_PROGRESS | NONE |")

old_norm = "- Post-merge normalization branch: **`r14/08-normalize-continuity`**, created from exact merge `5b51967c63ad5ae5ccc2df89f76aa48831ee2762`; it is required to change only this continuity file.\n- Current state represented by this normalization candidate: R14.8 **COMPLETE + NORMALIZED**; R14.9–R14.17 **PLANNED**."
new_norm = "- Single post-merge normalization head: **`0850580c78f2190199931129e9c1389f6c9977b1`**, changing only this continuity file. Fresh normalization gates: R0 #1834 / `33208563238`, Python Core #1808 / `33208563310`, UI #1775 / `33208563115` — all SUCCESS.\n- Normalization PR #272 merged with `expected_head_sha=0850580c78f2190199931129e9c1389f6c9977b1` as normalized `main` **`433c86cc5d43bfea41adb529451367e10c75a30b`**.\n- R14.8 final state: **COMPLETE + NORMALIZED**; R14.9 is authorized from that exact normalized `main`."
assert text.count(old_norm) == 1, text.count(old_norm)
text = text.replace(old_norm, new_norm)

start_authority = """## R14.9 START authority

- Dedicated branch: **`r14/09-progression-leaderboards`**.
- Exact branch point: normalized R14.8 `main` **`433c86cc5d43bfea41adb529451367e10c75a30b`**.
- START plan head: `5830d5d7fb75ac529c139c1f020e8dfc4423e580`; helper files self-removed before implementation.
- START state: R14.1–R14.8 **COMPLETE + NORMALIZED**; R14.9 **IN_PROGRESS**; R14.10–R14.17 **PLANNED**.
- Frozen scope: immutable/versioned achievement, stat and leaderboard definitions; server-authoritative validated progression events/commands; duplicate-safe idempotency; terminal/idempotent unlocks; explicit score ordering, tie, update and period/reset policies; deterministic ranking snapshots; privacy/display filtering; provider-neutral reads; direct client score writes forbidden.
- Acceptance focus: forged score rejection, duplicate/rebound event handling, duplicate unlock, definition immutability/versioning, deterministic higher/lower ranking and ties, period rollover/reset, privacy filtering, concurrency and bounded capacity.
- Provider posture: Steam/Game Center/Google Play are informative compatibility references only; no provider account, API key or live publication is required for core R14.9 acceptance.
- Manual intervention: **NONE**.

## External research baseline relevant to R14.9

- Steamworks distinguishes trusted backend Web API operations from client operations; its leaderboard API can require trusted writes so client score submission is disabled, and exposes explicit score update policy. R14.9 therefore keeps trusted progression writes server-side without making Steam the canonical model.
- Apple Game Center distinguishes classic leaderboards from recurring leaderboards that reset on configured schedules and exposes score sort order. R14.9 models periods/reset/order explicitly and deterministically rather than inheriting a platform implementation.
- Google Play Games exposes achievements and leaderboards as distinct client capabilities. R14.9 keeps those surfaces distinct while sharing one authoritative progression/event source internally.
- Provider documentation is versioned comparison evidence only; `provider_live_claim=false` remains mandatory unless a later explicit provider-live gate is executed.
"""

text, n = re.subn(
    r"## External research baseline relevant to R14\.8\n.*?\n## Next authorized action",
    start_authority + "\n## Next authorized action",
    text,
    count=1,
    flags=re.S,
)
assert n == 1, n

next_action = """## Next authorized action

Verify that the exact R14.9 START head differs from normalized R14.8 `main` `433c86cc5d43bfea41adb529451367e10c75a30b` by **only** `docs/roadmap/R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`. No implementation file may exist before that comparison passes. Once the START diff is clean, implement R14.9 on the same dedicated branch with immutable/versioned definitions, authoritative/idempotent progression events, deterministic ranking/period semantics, privacy filtering, bounded state and dedicated Ubuntu/Windows acceptance. Manual intervention remains **NONE**.
"""
text, n = re.subn(r"## Next authorized action\n.*\Z", next_action, text, count=1, flags=re.S)
assert n == 1, n

path.write_text(text, encoding="utf-8")
