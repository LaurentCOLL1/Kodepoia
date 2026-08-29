from pathlib import Path

MERGE = "a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1"
END = "ef39e7898abbca5466073bb78a95df829a33d836"
SOURCE = "a58a0cf48a5e2311b5f6e671655f107e92c4645e"

path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = path.read_text(encoding="utf-8")

old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.10 COMPLETE + NORMALIZED. R14.11 COMPLETE (END-SYNCED; merge/normalization pending). R14.12–R14.17 PLANNED.** R14.11 source technique immuable `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; R14 Remote Config Acceptance `33234881304` SUCCESS Ubuntu + Windows. Re-gater l’END-head exact avec R0 + full Python Core + UI + R14 Remote Config, merger avec expected-head, puis effectuer exactement une normalisation continuity-only avant R14.12. Manual state : NONE."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.11 COMPLETE + NORMALIZED. R14.12–R14.17 PLANNED.** R14.11 source technique immuable `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; END-head `ef39e7898abbca5466073bb78a95df829a33d836`; PR #277 fusionnée par merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1` après R0 #1863, Python Core #1837, UI #1804 et R14 Remote Config #27 tous SUCCESS. Cette branche porte l’unique normalisation continuity-only R14.11; elle doit encore passer R0 + full Python Core + UI et être mergée avec expected-head avant d’autoriser R14.12. Manual state : NONE."
assert text.count(old_prompt) == 1, text.count(old_prompt)
text = text.replace(old_prompt, new_prompt)

old_global = "- R14.11 : **COMPLETE (END-SYNCED; merge/normalization pending)** sur `r14/11-remote-config-feature-flags`; source technique immuable `a58a0cf48a5e2311b5f6e671655f107e92c4645e`."
new_global = "- R14.11 : **COMPLETE + NORMALIZED** — source technique `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; END-head `ef39e7898abbca5466073bb78a95df829a33d836`; PR #277 merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`; unique normalization branch `r14/11-normalization`."
assert text.count(old_global) == 1, text.count(old_global)
text = text.replace(old_global, new_global)

old_row = "| R14.11 | COMPLETE | NONE |"
new_row = "| R14.11 | COMPLETE + NORMALIZED | NONE |"
assert text.count(old_row) == 1, text.count(old_row)
text = text.replace(old_row, new_row)

old_tail = "- Final END-head must differ from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_11_ACCEPTANCE.md` and this continuity file, then pass fresh exact-head R0/Python/UI/R14 Remote Config before expected-head merge.\n- After merge, exactly one continuity-only normalization with fresh R0/Python/UI is mandatory before R14.12. R14.12–R14.17 remain PLANNED."
new_tail = "- Final accepted END-head `ef39e7898abbca5466073bb78a95df829a33d836` differs from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_11_ACCEPTANCE.md` and this continuity file.\n- Fresh END-head gates on exact `ef39e7898abbca5466073bb78a95df829a33d836`: R0 Repository Guard #1863 / `33235110200` SUCCESS; Python Core #1837 / `33235110228` SUCCESS including Ubuntu + Windows core, package builds and UI-in-core; KodeStudio UI Smoke #1804 / `33235110215` SUCCESS; R14 Remote Config Acceptance #27 / `33235110216` SUCCESS Ubuntu + Windows.\n- The earlier bot-triggered runs #1862/#1836/#1803/#26 on the same tree had no executable jobs and are NON-AUTHORITATIVE; the reopened user-triggered runs above are the accepted fresh evidence.\n- PR #277 merged only with `expected_head_sha=ef39e7898abbca5466073bb78a95df829a33d836` as implementation/evidence merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`.\n- Unique post-merge normalization branch: `r14/11-normalization`, created exactly from merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`. Its final tree delta must contain only this continuity file and must pass fresh exact-head R0/Python/UI before expected-head merge.\n- R14.11 final state is COMPLETE + NORMALIZED once that unique normalization PR merges; R14.12–R14.17 remain PLANNED until then."
assert text.count(old_tail) == 1, text.count(old_tail)
text = text.replace(old_tail, new_tail)

old_next = "Treat `a58a0cf48a5e2311b5f6e671655f107e92c4645e` as the only immutable R14.11 technical source. Verify the exact END-head diff from that source is limited to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_11_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Remote Config Acceptance. If all are SUCCESS, merge only with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Do not start R14.12 before normalized `main` exists. Manual state remains NONE."
new_next = "If this file is read from `r14/11-normalization`, verify its exact diff from merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1` contains only this continuity file, run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, and merge the single normalization PR only with `expected_head_sha` equal to that exact normalization head. If this file is read from `main` after that protected merge, R14.11 is COMPLETE + NORMALIZED and R14.12 becomes the next authorized subdivision; start R14.12 only from that normalized `main` with a dedicated branch and START-sync. Manual state for R14.11 remains NONE."
assert text.count(old_next) == 1, text.count(old_next)
text = text.replace(old_next, new_next)

path.write_text(text, encoding="utf-8")
