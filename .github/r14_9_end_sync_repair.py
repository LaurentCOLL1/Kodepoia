from pathlib import Path

SOURCE = "155119282af7f4bf71840fc45c2d3de8891f73cd"
BASE = "433c86cc5d43bfea41adb529451367e10c75a30b"

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.8 are COMPLETE + NORMALIZED. R14.8 immutable technical source `8132c4029983f693a32e0d26903d05e347313bf6`; accepted END-head `954991537fc8c076169993ea106303421b8edd60`; PR #271 merged with expected-head as `5b51967c63ad5ae5ccc2df89f76aa48831ee2762`; single continuity-only normalization PR #272 passed R0 #1834, Python Core #1808 and UI #1775 and merged as normalized `main` `433c86cc5d43bfea41adb529451367e10c75a30b`. R14.9 is IN_PROGRESS on `r14/09-progression-leaderboards`; R14.10–R14.17 remain PLANNED. R14.9 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.8 are COMPLETE + NORMALIZED. R14.9 is COMPLETE at technical/evidence + END-sync level on `r14/09-progression-leaderboards`; immutable technical source `155119282af7f4bf71840fc45c2d3de8891f73cd` passed R0 #1836, Python Core #1810, UI #1777 and R14 Progression Acceptance #3. R14.10–R14.17 remain PLANNED. PR #273 still requires fresh exact END-head re-gates, protected merge and exactly one continuity-only normalization before R14.10. R14.9 manual state is NONE."
assert plan.count(old_checkpoint) == 1, plan.count(old_checkpoint)
plan = plan.replace(old_checkpoint, new_checkpoint)
old_row = "| R14.9 | Achievements, stats, leaderboards + authoritative progression | IN_PROGRESS | NONE | R14.5–R14.6 |"
new_row = "| R14.9 | Achievements, stats, leaderboards + authoritative progression | COMPLETE | NONE | R14.5–R14.6 |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)
section_start = plan.index("# R14.9 — Achievements, stats, leaderboards + authoritative progression")
section_end = plan.index("# R14.10 — Entitlements, billing/catalog + server-side provider verification/notifications")
section = plan[section_start:section_end]
old_completion = "## Completion record\n\nTo be appended when accepted."
completion = """## Completion record

- Dedicated branch: `r14/09-progression-leaderboards`; exact normalized branch point: R14.8 `main` `433c86cc5d43bfea41adb529451367e10c75a30b`.
- Mandatory START-sync completed before implementation; final clean START head `d221057a91b9c0389346e6eec71044ce57898db1` differed from normalized main by plan + continuity only.
- Candidate `dc3ea916dd5bfbcc5751a7fbe0128532f3a1298f` is REJECTED and its evidence is non-authoritative; the test fixture, not the production authorization boundary, was corrected.
- Pre-acceptance audit detected and corrected recurring-leaderboard lifetime-state bleed; recurring periods now derive period-local score state.
- Accepted immutable technical source: `155119282af7f4bf71840fc45c2d3de8891f73cd`.
- Technical exact-source gates: R0 #1836 / `33210136515`, Python Core #1810 / `33210136766`, UI #1777 / `33210136531`, R14 Progression Acceptance #3 / `33210136498` — all SUCCESS.
- Full Ubuntu: **1590 passed / 13 skipped / 46 warnings**; focused R14.9→R14.5: **96 passed Ubuntu + 96 passed Windows**.
- Fifteen frozen progression checks PASS cross-platform, including authoritative-only score mutation, idempotency/event rebinding rejection, deterministic ordering/ties, server-clock period boundaries, privacy filtering, bounded capacity and recurring rollover without lifetime bleed.
- Cross-platform digests: definition `0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686`; state `a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d`; trace `c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3`; classic `49a5655892db2649f2f9a926aff2e2cda14f8b51ef3f9901acc4c227c96e306c`; lower `2869ce012f10c143be8128f356288c21bc028793d18fae5ea2cb79b6f2b18859`; recurring p0 `a3fd0f5b9a06a093b0961626950ef0ddf9c3acb0ebd9f69e67bf4bb0dd6b9380`; recurring p1 `4d22f10134f62e6449fce47bee6e13ef4ed9556d7922889c0749dc3000ffd2fd`.
- Canonical artifacts: Ubuntu `9701251718` / `sha256:fb8be016598d8bf1450047102b2c44e26aa975bf78c78f62e1e7043f4f64e69a`; Windows `9701266161` / `sha256:065fac3a244258b4047f51b229b66b1adfe3ec0714d556b7ba6e42220568b02e`.
- `provider_live_claim=false`; `secrets_exposed=false`; provider docs are compatibility evidence only. Manual intervention: NONE.
- END state: R14.9 COMPLETE; R14.10–R14.17 remain PLANNED. Fresh exact END-head R0/Python/UI/R14 Progression, expected-head PR #273 merge and one continuity-only normalization remain mandatory before R14.10.
""".rstrip()
assert section.count(old_completion) == 1, section.count(old_completion)
section = section.replace(old_completion, completion)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = continuity_path.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.8 COMPLETE + NORMALIZED. R14.9 IN_PROGRESS. R14.10–R14.17 PLANNED.** R14.8 est définitivement normalisée sur `main` `433c86cc5d43bfea41adb529451367e10c75a30b` après PR #272. R14.9 démarre exactement de ce SHA sur `r14/09-progression-leaderboards`. Frozen scope : définitions achievement/stat/leaderboard immuables et versionnées, progression seulement depuis événements/commandes autoritatifs validés, unlock/progress idempotents, score ordering/tie/period/reset explicites, snapshots de classement déterministes, écritures directes de score client interdites, privacy/display controls et queries provider-neutral. Manual intervention : NONE."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.8 COMPLETE + NORMALIZED. R14.9 COMPLETE (END-SYNCED; merge/normalization pending). R14.10–R14.17 PLANNED.** R14.9 source technique immuable `155119282af7f4bf71840fc45c2d3de8891f73cd`; R0 #1836, Python Core #1810, UI #1777 et R14 Progression Acceptance #3 sont SUCCESS. Re-gater l’END-head exact, merger PR #273 avec expected-head, puis effectuer exactement une normalisation continuity-only avant R14.10. Manual intervention : NONE."
assert cont.count(old_prompt) == 1, cont.count(old_prompt)
cont = cont.replace(old_prompt, new_prompt)
old_global = "- R14.9 : **IN_PROGRESS** sur `r14/09-progression-leaderboards`, base exacte `433c86cc5d43bfea41adb529451367e10c75a30b`.\n- R14.10–R14.17 : **PLANNED**."
new_global = "- R14.9 : **COMPLETE (END-SYNCED; merge/normalization pending)** sur `r14/09-progression-leaderboards`; source technique immuable `155119282af7f4bf71840fc45c2d3de8891f73cd`.\n- R14.10–R14.17 : **PLANNED**."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)
old_status = "| R14.9 | IN_PROGRESS | NONE |"
assert cont.count(old_status) == 1, cont.count(old_status)
cont = cont.replace(old_status, "| R14.9 | COMPLETE | NONE |")
start = cont.index("## R14.9 START authority")
external = cont.index("## External research baseline relevant to R14.9")
closure = """## R14.9 technical closure authority

- Dedicated branch `r14/09-progression-leaderboards`; exact base normalized R14.8 `main` `433c86cc5d43bfea41adb529451367e10c75a30b`.
- Clean START head `d221057a91b9c0389346e6eec71044ce57898db1`; no implementation preceded START acceptance.
- Rejected candidate `dc3ea916dd5bfbcc5751a7fbe0128532f3a1298f`: NON-AUTHORITATIVE; its evidence must never be reused.
- Immutable technical source `155119282af7f4bf71840fc45c2d3de8891f73cd`.
- Technical gates: R0 #1836 / `33210136515`, Python Core #1810 / `33210136766`, UI #1777 / `33210136531`, R14 Progression #3 / `33210136498` — all SUCCESS.
- Full Ubuntu: **1590 passed / 13 skipped / 46 warnings**; focused: **96 passed Ubuntu + 96 passed Windows**; fifteen dedicated checks PASS on both OS.
- Digests: definition `0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686`; state `a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d`; trace `c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3`.
- Artifacts: Ubuntu `9701251718` / `sha256:fb8be016598d8bf1450047102b2c44e26aa975bf78c78f62e1e7043f4f64e69a`; Windows `9701266161` / `sha256:065fac3a244258b4047f51b229b66b1adfe3ec0714d556b7ba6e42220568b02e`.
- `provider_live_claim=false`; `secrets_exposed=false`; manual NONE.
- Current state: R14.9 COMPLETE at END-sync; R14.10–R14.17 PLANNED.

"""
cont = cont[:start] + closure + cont[external:]
next_heading = "## Next authorized action\n\n"
assert cont.count(next_heading) == 1, cont.count(next_heading)
pos = cont.index(next_heading)
cont = cont[:pos] + next_heading + "Treat `155119282af7f4bf71840fc45c2d3de8891f73cd` as the only immutable R14.9 technical source. Verify the END-head diff from that source is limited to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_9_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Progression Acceptance. If all are SUCCESS, merge PR #273 only with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Do not start R14.10 before normalized `main` exists. Manual intervention remains NONE.\n"
continuity_path.write_text(cont, encoding="utf-8")
