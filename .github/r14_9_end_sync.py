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
- Mandatory START-sync completed before implementation: R14.1–R14.8 COMPLETE + NORMALIZED, R14.9 IN_PROGRESS, R14.10–R14.17 PLANNED; START plan head `5830d5d7fb75ac529c139c1f020e8dfc4423e580` and final clean START head `d221057a91b9c0389346e6eec71044ce57898db1` differed from normalized main by plan + continuity only.
- Initial dedicated candidate `dc3ea916dd5bfbcc5751a7fbe0128532f3a1298f` is **REJECTED** and its evidence is not reusable. The new test fixture attempted wildcard object authorization; the existing R14.6 stable-object authority boundary was preserved and the fixture was corrected instead of weakening production authorization.
- Pre-acceptance audit detected and corrected recurring-leaderboard lifetime-state bleed: a new recurring period now derives period-local score state rather than inheriting a cumulative lifetime `SUM`/`MAX`/`MIN` result.
- Accepted immutable technical source: `155119282af7f4bf71840fc45c2d3de8891f73cd`.
- Technical exact-source gates: R0 Repository Guard #1836 / `33210136515` SUCCESS; Python Core #1810 / `33210136766` SUCCESS; KodeStudio UI Smoke #1777 / `33210136531` SUCCESS; R14 Progression Acceptance #3 / `33210136498` SUCCESS on Ubuntu and Windows.
- Full Ubuntu Python suite: **1590 passed / 13 skipped / 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS; Python internal KodeStudio smoke SUCCESS.
- Focused R14.9→R14.5 progression regression: **96 passed Ubuntu + 96 passed Windows**.
- Fifteen frozen progression checks PASS cross-platform: authoritative event, bounded capacity, direct-client-score rejection, event-ID rebind rejection, function authorization, deterministic higher ordering, idempotency rebind rejection, mutation-free replay, immutable definition version, deterministic lower ordering, object authorization, server-clock period boundary, privacy filtering, recurring rollover without lifetime bleed, terminal/idempotent unlock.
- Cross-platform semantic digests are identical: definition `0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686`; state `a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d`; trace `c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3`; classic snapshot `49a5655892db2649f2f9a926aff2e2cda14f8b51ef3f9901acc4c227c96e306c`; lower snapshot `2869ce012f10c143be8128f356288c21bc028793d18fae5ea2cb79b6f2b18859`; recurring p0 `a3fd0f5b9a06a093b0961626950ef0ddf9c3acb0ebd9f69e67bf4bb0dd6b9380`; recurring p1 `4d22f10134f62e6449fce47bee6e13ef4ed9556d7922889c0749dc3000ffd2fd`.
- Evidence state: `event_count=6`, `unlock_count=2`; budgets `max_events=128`, `max_accounts=32`, `max_definition_versions=32`, `max_entries_per_leaderboard_period=32`, `max_metadata_bytes=1024`.
- Canonical R14 Progression #3 artifacts: Ubuntu `9701251718` / `sha256:fb8be016598d8bf1450047102b2c44e26aa975bf78c78f62e1e7043f4f64e69a`; Windows `9701266161` / `sha256:065fac3a244258b4047f51b229b66b1adfe3ec0714d556b7ba6e42220568b02e`.
- Evidence schema: `schemas/r14/backend-progression-evidence.schema.json`; `provider_live_claim=false`; `secrets_exposed=false`.
- Steamworks trusted-write semantics and Apple Game Center classic/recurring ordering/reset semantics are informative compatibility evidence only; no provider account or publication claim is part of core acceptance.
- Manual intervention: NONE.
- END state: R14.9 COMPLETE; R14.10–R14.17 remain PLANNED. The END-head must differ from the immutable source only by `R14_PLAN.md`, `R14_9_ACCEPTANCE.md` and continuity, pass fresh R0/Python/UI/R14 Progression, then PR #273 must merge with expected-head protection and exactly one continuity-only normalization must pass before R14.10.
""".rstrip()
assert section.count(old_completion) == 1, section.count(old_completion)
section = section.replace(old_completion, completion)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = continuity_path.read_text(encoding="utf-8")

lines = cont.splitlines()
assert lines[5] == "## Prompt de reprise"
assert lines[7].startswith("> Kodepoia, architecture v1.0 gelée.")
lines[7] = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.8 COMPLETE + NORMALIZED. R14.9 COMPLETE (END-SYNCED; merge/normalization pending). R14.10–R14.17 PLANNED.** R14.9 source technique immuable `155119282af7f4bf71840fc45c2d3de8891f73cd`; R0 #1836, Python Core #1810, UI #1777 et R14 Progression Acceptance #3 sont SUCCESS. Le prochain acte autorisé est de re-gater l’END-head exact, puis merger PR #273 avec expected-head et effectuer exactement une normalisation continuity-only avant R14.10. Manual intervention : NONE."
cont = "\n".join(lines) + ("\n" if cont.endswith("\n") else "")

old_global = "- R14.9 : **IN_PROGRESS** sur `r14/09-progression-leaderboards`, base exacte `433c86cc5d43bfea41adb529451367e10c75a30b`.\n- R14.10–R14.17 : **PLANNED**."
new_global = "- R14.9 : **COMPLETE (END-SYNCED; merge/normalization pending)** sur `r14/09-progression-leaderboards`; source technique immuable `155119282af7f4bf71840fc45c2d3de8891f73cd`.\n- R14.10–R14.17 : **PLANNED**."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)

old_status = "| R14.9 | IN_PROGRESS | NONE |"
new_status = "| R14.9 | COMPLETE | NONE |"
assert cont.count(old_status) == 1, cont.count(old_status)
cont = cont.replace(old_status, new_status)

start = cont.index("## R14.9 START authority")
external = cont.index("## External research baseline relevant to R14.9")
closure = """## R14.9 technical closure authority

- Dedicated branch: **`r14/09-progression-leaderboards`**; exact branch point: normalized R14.8 `main` **`433c86cc5d43bfea41adb529451367e10c75a30b`**.
- START plan head `5830d5d7fb75ac529c139c1f020e8dfc4423e580`; final clean START head `d221057a91b9c0389346e6eec71044ce57898db1`; no implementation preceded the clean START compare.
- Rejected candidate `dc3ea916dd5bfbcc5751a7fbe0128532f3a1298f`: **NON-AUTHORITATIVE**. Fixture wildcard object authorization violated the existing stable-object constructor contract; production authorization was not weakened and no evidence from this candidate may be reused.
- Accepted immutable technical source: **`155119282af7f4bf71840fc45c2d3de8891f73cd`**.
- Technical gates: R0 #1836 / `33210136515`, Python Core #1810 / `33210136766`, UI #1777 / `33210136531`, R14 Progression Acceptance #3 / `33210136498` — all SUCCESS.
- Full Ubuntu: **1590 passed / 13 skipped / 46 warnings**. Focused R14.9→R14.5: **96 passed Ubuntu + 96 passed Windows**.
- Fifteen checks PASS on both OS: authoritative event, bounded capacity, direct-client-score rejection, event-ID rebind rejection, function authorization, deterministic higher ordering, idempotency rebind rejection, mutation-free replay, immutable definition version, deterministic lower ordering, object authorization, server-clock period boundary, privacy filter, recurring rollover without lifetime bleed, terminal/idempotent unlock.
- Semantic digests cross-platform: definition `0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686`; state `a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d`; trace `c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3`; classic `49a5655892db2649f2f9a926aff2e2cda14f8b51ef3f9901acc4c227c96e306c`; lower `2869ce012f10c143be8128f356288c21bc028793d18fae5ea2cb79b6f2b18859`; recurring p0 `a3fd0f5b9a06a093b0961626950ef0ddf9c3acb0ebd9f69e67bf4bb0dd6b9380`; recurring p1 `4d22f10134f62e6449fce47bee6e13ef4ed9556d7922889c0749dc3000ffd2fd`.
- Canonical artifacts: Ubuntu `9701251718` / `sha256:fb8be016598d8bf1450047102b2c44e26aa975bf78c78f62e1e7043f4f64e69a`; Windows `9701266161` / `sha256:065fac3a244258b4047f51b229b66b1adfe3ec0714d556b7ba6e42220568b02e`.
- `provider_live_claim=false`; `secrets_exposed=false`; provider documentation is informative compatibility evidence only.
- Current state: R14.9 **COMPLETE at END-sync**; R14.10–R14.17 **PLANNED**. Manual intervention: **NONE**.

"""
cont = cont[:start] + closure + cont[external:]

next_heading = "## Next authorized action\n\n"
assert cont.count(next_heading) == 1, cont.count(next_heading)
next_pos = cont.index(next_heading)
cont = cont[:next_pos] + next_heading + "Treat `155119282af7f4bf71840fc45c2d3de8891f73cd` as the only immutable R14.9 technical source. Verify the END-head diff from that source is limited to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_9_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Progression Acceptance. If all are SUCCESS, merge PR #273 only with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Do not start R14.10 before normalized `main` exists. Manual intervention remains **NONE**.\n"
continuity_path.write_text(cont, encoding="utf-8")
