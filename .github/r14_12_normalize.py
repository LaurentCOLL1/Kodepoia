from pathlib import Path

MERGE = "a088a081276213e7efa7bfb03b7b8adea2f0a75b"
END = "42db6d1fa84f5bd9b6a2c8e399603b9b9e621417"
SOURCE = "9472f9198cdbaeed5c2b4618595480ac65bc4d5e"

path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = path.read_text(encoding="utf-8")

old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.11 COMPLETE + NORMALIZED. R14.12 COMPLETE au niveau technique/END-sync, en attente des re-gates END-head + merge + normalisation. R14.13–R14.17 PLANNED.** Normalized `main` d’autorité avant R14.12 `71ceb529e89b13be343be76527e9b9b0b419ceda`; branche active `r14/12-content-delivery`; source technique immuable R14.12 `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`. Gates techniques sur cette source : R0 #1882 / `33244609227`, Python Core #1857 / `33244609228`, UI #1822 / `33244609244`, R14 Content Delivery #19 / `33244609252`, tous SUCCESS. Full Ubuntu : 1674 passed / 13 skipped / 46 warnings. Manual state CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`. Le prochain geste autorisé est de vérifier que l’END-head ne diffère de la source technique que par `R14_PLAN.md`, `R14_12_ACCEPTANCE.md` et cette continuité, puis d’exécuter des re-gates frais sur cet END-head exact avant toute fusion."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.12 COMPLETE + NORMALIZED. R14.13–R14.17 PLANNED.** R14.12 source technique immuable `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`; END-head `42db6d1fa84f5bd9b6a2c8e399603b9b9e621417`; PR #279 fusionnée par merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b` après R0 #1884, Python Core #1859, UI #1824 et R14 Content Delivery #21 tous SUCCESS. Cette branche porte l’unique normalisation continuity-only R14.12; elle doit encore passer R0 + full Python Core + UI et être mergée avec expected-head avant d’autoriser R14.13. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert text.count(old_prompt) == 1, text.count(old_prompt)
text = text.replace(old_prompt, new_prompt)

old_global = "- R14.12 : **COMPLETE au niveau technique/END-sync** sur `r14/12-content-delivery`; exact branch point `71ceb529e89b13be343be76527e9b9b0b419ceda`; source technique immuable `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`; merge/normalisation encore requis avant `COMPLETE + NORMALIZED`."
new_global = "- R14.12 : **COMPLETE + NORMALIZED** — source technique `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`; END-head `42db6d1fa84f5bd9b6a2c8e399603b9b9e621417`; PR #279 merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b`; unique normalization branch `r14/12-normalization`."
assert text.count(old_global) == 1, text.count(old_global)
text = text.replace(old_global, new_global)

old_row = "| R14.12 | COMPLETE (END candidate; normalization pending) | CONDITIONAL / NOT TRIGGERED |"
new_row = "| R14.12 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |"
assert text.count(old_row) == 1, text.count(old_row)
text = text.replace(old_row, new_row)

old_tail = "- END state: R14.12 COMPLETE at technical/documentation-candidate level; R14.13–R14.17 remain PLANNED. R14.13 is not authorized until the exact R14.12 END-head passes fresh R0/Python/UI/R14 Content Delivery gates, PR #279 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges."
new_tail = "- Final accepted END-head `42db6d1fa84f5bd9b6a2c8e399603b9b9e621417` differs from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_12_ACCEPTANCE.md` and this continuity file.\n- Fresh END-head gates on exact `42db6d1fa84f5bd9b6a2c8e399603b9b9e621417`: R0 Repository Guard #1884 / `33245750516` SUCCESS Ubuntu + Windows; Python Core #1859 / `33245750503` SUCCESS including Ubuntu + Windows core, package builds and UI-in-core, with Ubuntu 1674 passed / 13 skipped / 46 warnings; KodeStudio UI Smoke #1824 / `33245750507` SUCCESS; R14 Content Delivery Acceptance #21 / `33245750553` SUCCESS Ubuntu + Windows.\n- PR #279 merged only with `expected_head_sha=42db6d1fa84f5bd9b6a2c8e399603b9b9e621417` as implementation/evidence merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b`.\n- Unique post-merge normalization branch: `r14/12-normalization`, created exactly from merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b`. Its final tree delta must contain only this continuity file and must pass fresh exact-head R0/Python/UI before expected-head merge.\n- Manual state remains CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`; no external CDN/provider proof or credential was required.\n- R14.12 final state is COMPLETE + NORMALIZED once that unique normalization PR merges; R14.13–R14.17 remain PLANNED until then."
assert text.count(old_tail) == 1, text.count(old_tail)
text = text.replace(old_tail, new_tail)

old_next = "The immutable technical source is `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`. Verify the R14.12 END-head differs from it **only** by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_12_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Content Delivery Acceptance on that END-head. If all are SUCCESS and the PR #279 head still equals the exact accepted END-head, merge only with `expected_head_sha` protection. Then create exactly one `r14/12-normalization` branch from the implementation/evidence merge, change only this continuity file, run fresh exact-head R0 + full Python Core + UI, and merge the normalization with expected-head protection. Only the resulting normalized `main` authorizes R14.13. Manual state remains CONDITIONAL / NOT TRIGGERED; do not request CDN/provider credentials or claim provider-live success."
new_next = "If this file is read from `r14/12-normalization`, verify its exact diff from merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b` contains only this continuity file, run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, and merge the single normalization PR only with `expected_head_sha` equal to that exact normalization head. If this file is read from `main` after that protected merge, R14.12 is COMPLETE + NORMALIZED and R14.13 becomes the next authorized subdivision; start R14.13 only from that normalized `main` with a dedicated branch and mandatory START-sync before implementation. Manual state for R14.12 remains CONDITIONAL / NOT TRIGGERED and `provider_live_claim=false`."
assert text.count(old_next) == 1, text.count(old_next)
text = text.replace(old_next, new_next)

path.write_text(text, encoding="utf-8")
