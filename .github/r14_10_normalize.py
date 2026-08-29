from pathlib import Path

MERGE = "c0059f02c193c4972daaaad851ce0d5a8fdcd715"
END = "37c7418e31e1467032eac0646b731eab1087f4eb"
SOURCE = "8a102a19512b076a8edb5c561e86b1d0101bc391"

path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = path.read_text(encoding="utf-8")

old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.9 COMPLETE + NORMALIZED. R14.10 COMPLETE (END-SYNCED; merge/normalization pending). R14.11–R14.17 PLANNED.** R14.10 source technique immuable `8a102a19512b076a8edb5c561e86b1d0101bc391`; R14 Entitlements Acceptance `33233097442` est SUCCESS Ubuntu + Windows. Re-gater l’END-head exact avec R0 + full Python Core + UI + R14 Entitlements, merger PR #275 avec expected-head, puis effectuer exactement une normalisation continuity-only avant R14.11. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.10 COMPLETE + NORMALIZED. R14.11–R14.17 PLANNED.** R14.10 source technique immuable `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 fusionnée par merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715` après R0 #1852, Python Core #1826, UI #1793 et R14 Entitlements #12 tous SUCCESS. Cette continuité est l’unique normalisation post-merge R14.10; sur une branche de normalisation, elle doit encore passer R0 + full Python Core + UI et être mergée avec expected-head avant d’autoriser R14.11. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert text.count(old_prompt) == 1, text.count(old_prompt)
text = text.replace(old_prompt, new_prompt)

old_global = "- R14.10 : **COMPLETE (END-SYNCED; merge/normalization pending)** sur `r14/10-entitlements-billing-catalog`; source technique immuable `8a102a19512b076a8edb5c561e86b1d0101bc391`; PR #275 ouverte."
new_global = "- R14.10 : **COMPLETE + NORMALIZED** — source technique `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`; unique normalization branch `r14/10-normalization`."
assert text.count(old_global) == 1, text.count(old_global)
text = text.replace(old_global, new_global)

old_row = "| R14.10 | COMPLETE | CONDITIONAL / NOT TRIGGERED |"
new_row = "| R14.10 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |"
assert text.count(old_row) == 1, text.count(old_row)
text = text.replace(old_row, new_row)

old_closure_tail = "- PR #275 carries R14.10. Final END-head must differ from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_10_ACCEPTANCE.md` and this continuity file, then pass fresh exact-head R0/Python/UI/R14 Entitlements before expected-head merge.\n- After merge, exactly one continuity-only normalization with fresh R0/Python/UI is mandatory before R14.11. R14.11–R14.17 remain PLANNED."
new_closure_tail = "- Final END-head `37c7418e31e1467032eac0646b731eab1087f4eb` differs from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_10_ACCEPTANCE.md` and this continuity file.\n- Fresh END-head gates on exact `37c7418e31e1467032eac0646b731eab1087f4eb`: R0 Repository Guard #1852 / `33233480750` SUCCESS; Python Core #1826 / `33233480761` SUCCESS including Ubuntu + Windows core and package builds; KodeStudio UI Smoke #1793 / `33233480825` SUCCESS; R14 Entitlements Acceptance #12 / `33233480782` SUCCESS.\n- PR #275 merged only with `expected_head_sha=37c7418e31e1467032eac0646b731eab1087f4eb` as implementation/evidence merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`.\n- Unique post-merge normalization branch: `r14/10-normalization`, created exactly from merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`. Its final tree delta must contain only this continuity file and must pass fresh exact-head R0/Python/UI before expected-head merge.\n- R14.10 final state is COMPLETE + NORMALIZED once that unique normalization PR merges; R14.11–R14.17 remain PLANNED until then."
assert text.count(old_closure_tail) == 1, text.count(old_closure_tail)
text = text.replace(old_closure_tail, new_closure_tail)

old_next = "Treat `8a102a19512b076a8edb5c561e86b1d0101bc391` as the only immutable R14.10 technical source. Verify the exact END-head diff from that source is limited to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_10_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Entitlements Acceptance. If all are SUCCESS, merge PR #275 only with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Do not start R14.11 before normalized `main` exists. Manual state remains CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
new_next = "If this file is read from `r14/10-normalization`, verify its exact diff from merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715` contains only this continuity file, run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, and merge the single normalization PR only with `expected_head_sha` equal to that exact normalization head. If this file is read from `main` after that protected merge, R14.10 is COMPLETE + NORMALIZED and R14.11 becomes the next authorized subdivision; start R14.11 only from that normalized `main` with a dedicated branch and START-sync. Manual state remains CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert text.count(old_next) == 1, text.count(old_next)
text = text.replace(old_next, new_next)

path.write_text(text, encoding="utf-8")
