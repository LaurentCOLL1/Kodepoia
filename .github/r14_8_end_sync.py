from pathlib import Path
import re

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.7 are COMPLETE + NORMALIZED. R14.7 implementation/evidence PR #269 merged as `763ce96c4f82da2eaec167b56ffb62d9e548b300`; its single continuity-only normalization PR #270 merged as normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after R0 #1810, Python Core #1784 and UI #1751, all SUCCESS. R14.8 is IN_PROGRESS on `r14/08-cloud-saves`; R14.9–R14.17 remain PLANNED. R14.8 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.7 are COMPLETE + NORMALIZED. R14.7 implementation/evidence PR #269 merged as `763ce96c4f82da2eaec167b56ffb62d9e548b300`; its single continuity-only normalization PR #270 merged as normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after R0 #1810, Python Core #1784 and UI #1751, all SUCCESS. R14.8 technical source `8132c4029983f693a32e0d26903d05e347313bf6` is accepted after R0 #1822, Python Core #1796, UI #1763 and R14 Cloud Save Acceptance #6, all SUCCESS. R14.8 is COMPLETE at END-sync; final exact-head re-gates, protected merge and the single continuity-only normalization remain required. R14.9–R14.17 remain PLANNED. R14.8 manual state is NONE."
assert plan.count(old_checkpoint) == 1, f"checkpoint count={plan.count(old_checkpoint)}"
plan = plan.replace(old_checkpoint, new_checkpoint)

old_row = "| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | IN_PROGRESS | NONE | R14.5–R14.6 |"
new_row = "| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | COMPLETE | NONE | R14.5–R14.6 |"
assert plan.count(old_row) == 1, f"row count={plan.count(old_row)}"
plan = plan.replace(old_row, new_row)

record = """## Completion record

- Dedicated branch: `r14/08-cloud-saves`.
- Exact branch point: normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after the single accepted R14.7 continuity normalization.
- START state: R14.1–R14.7 COMPLETE + NORMALIZED; R14.8 IN_PROGRESS; R14.9–R14.17 PLANNED.
- Frozen R14.8 scope: server-authoritative save slots, immutable append-only revisions, payload/schema/content digests, explicit client base revision / compare-and-swap semantics, duplicate-safe idempotency, first-class conflict objects, deterministic resolution, quotas/retention bounds, integrity validation and append-only rollback/recovery. No silent last-write-wins, no provider lock-in and no production cloud account requirement.
- Immutable technical source: `8132c4029983f693a32e0d26903d05e347313bf6`.
- Exact-source gates: R0 Repository Guard #1822 / `33206330276`, Python Core #1796 / `33206330171`, KodeStudio UI Smoke #1763 / `33206330345`, R14 Cloud Save Acceptance #6 / `33206330291` — all SUCCESS.
- Python Core Ubuntu: **1564 passed / 13 skipped / 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS; internal KodeStudio smoke SUCCESS.
- Focused R14.8/R14.7/R14.6/R14.5 regression: **70 passed Ubuntu + 70 passed Windows**.
- Fourteen dedicated checks PASS on both OS: immutable revision, idempotent replay, idempotency rebind rejection, explicit conflict, conflict replay, deterministic resolution, double-resolution rejection, explicit migration, silent schema-change rejection, append-only rollback, object authorization, function authorization, integrity guard and bounded quota.
- Cross-platform semantic evidence: state `984bf5fc88d5ca537cd3a4d938c0aa6d890e8f1794f5485467726331331ce345`; trace `f071636d1c5c99614b91817d328bab43ec406daaf315621affecd45af42df5e8`; slot `24c423bfc661d2f8d207364c9d7058cb45413b7e15347beb78b50ca10c7345d1`; current revision `4603e4e2a7d7d708cf689eb6cd4502b9809993b7245fc3ac64bf05eee1f34d7e`; resolved conflict `be2d6808b13bd40aa4a04d003d8d47df315a4461a67647746b87b26d1e6c0eca`.
- Evidence state: `revision_count=5`, `retained_bytes=145`; budgets `max_payload_bytes=1024`, `max_revisions_per_slot=12`, `max_retained_bytes_per_slot=8192`, `max_open_conflicts_per_slot=3`.
- Artifacts: Ubuntu `9699802370` / `sha256:bfd9d7cadb002a822f5c0f399f32dc7410b62318a1dee7a0c3d480bd1c8398d8`; Windows `9699818533` / `sha256:748f1b5572d679e619d82aeda314a1fa1f4c688d7edfe6f84e41fe54424c5a0d`.
- Evidence schema: `schemas/r14/backend-cloud-save-evidence.schema.json`; `provider_live_claim=false`; `secrets_exposed=false`.
- External evidence baseline: RFC 9110 conditional-request semantics are informative lost-update/CAS evidence; Google Play Games Saved Games explicitly exposes conflict states/resolution policies; OWASP API1:2023 remains the object-authorization baseline. None is a provider dependency.
- Manual intervention: NONE.
- END state: R14.8 COMPLETE; R14.9–R14.17 remain PLANNED. R14.9 is not authorized until this END-sync head passes fresh exact-head R0 + full Python Core + KodeStudio UI Smoke + R14 Cloud Save Acceptance, PR #271 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.
"""
pat = r"## Completion record\n.*?\n---\n\n# R14\.9 — Achievements, stats, leaderboards \+ authoritative progression"
plan, n = re.subn(pat, record + "\n---\n\n# R14.9 — Achievements, stats, leaderboards + authoritative progression", plan, count=1, flags=re.S)
assert n == 1, f"completion replacements={n}"
plan_path.write_text(plan, encoding="utf-8")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
prompt_old = "**R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.7 COMPLETE + NORMALIZED. R14.8 IN_PROGRESS. R14.9–R14.17 PLANNED.** R14.8 démarre exactement du `main` normalisé `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` sur `r14/08-cloud-saves`. Le START-sync plan + continuité doit être complet avant toute implémentation. Frozen scope : immutable save revisions, base-revision/CAS, explicit conflicts, idempotency, integrity/schema checks, quotas/retention and append-only rollback/recovery. Manual intervention : NONE."
prompt_new = "**R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.7 COMPLETE + NORMALIZED. R14.8 COMPLETE (END-SYNCED; normalization pending). R14.9–R14.17 PLANNED.** R14.8 source technique immuable `8132c4029983f693a32e0d26903d05e347313bf6` sur `r14/08-cloud-saves`; R0 #1822, Python Core #1796, UI #1763 et Cloud Save Acceptance #6 sont SUCCESS. Re-gater l’END-head exact, merger PR #271 avec expected-head, puis effectuer exactement une normalisation continuity-only avant toute R14.9. Manual intervention : NONE."
assert cont.count(prompt_old) == 1, f"prompt count={cont.count(prompt_old)}"
cont = cont.replace(prompt_old, prompt_new)
global_old = "- R14.8 : **IN_PROGRESS** sur `r14/08-cloud-saves`, base exacte `24e40db2781db8e42591c6ffa8fbdb8f0bf84108`."
global_new = "- R14.8 : **COMPLETE (END-SYNCED; normalization pending)** sur `r14/08-cloud-saves`; source technique immuable `8132c4029983f693a32e0d26903d05e347313bf6`, base exacte `24e40db2781db8e42591c6ffa8fbdb8f0bf84108`."
assert cont.count(global_old) == 1, f"global count={cont.count(global_old)}"
cont = cont.replace(global_old, global_new)
assert cont.count("| R14.8 | IN_PROGRESS | NONE |") == 1
cont = cont.replace("| R14.8 | IN_PROGRESS | NONE |", "| R14.8 | COMPLETE | NONE |")

authority = """## R14.8 END-sync authority

- Dedicated branch: **`r14/08-cloud-saves`**.
- Exact branch point: normalized R14.7 `main` **`24e40db2781db8e42591c6ffa8fbdb8f0bf84108`**.
- Immutable technical source: **`8132c4029983f693a32e0d26903d05e347313bf6`**.
- Technical gates: R0 #1822 / `33206330276`, Python Core #1796 / `33206330171`, UI #1763 / `33206330345`, Cloud Save Acceptance #6 / `33206330291` — all SUCCESS.
- Python Core Ubuntu: **1564 passed / 13 skipped / 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS.
- Focused R14.8→R14.5: **70 passed Ubuntu + 70 passed Windows**; fourteen cloud-save checks PASS cross-platform.
- Semantic digests: state `984bf5fc88d5ca537cd3a4d938c0aa6d890e8f1794f5485467726331331ce345`; trace `f071636d1c5c99614b91817d328bab43ec406daaf315621affecd45af42df5e8`; slot `24c423bfc661d2f8d207364c9d7058cb45413b7e15347beb78b50ca10c7345d1`; current revision `4603e4e2a7d7d708cf689eb6cd4502b9809993b7245fc3ac64bf05eee1f34d7e`; resolved conflict `be2d6808b13bd40aa4a04d003d8d47df315a4461a67647746b87b26d1e6c0eca`.
- Artifacts: Ubuntu `9699802370` / `sha256:bfd9d7cadb002a822f5c0f399f32dc7410b62318a1dee7a0c3d480bd1c8398d8`; Windows `9699818533` / `sha256:748f1b5572d679e619d82aeda314a1fa1f4c688d7edfe6f84e41fe54424c5a0d`.
- Provider posture: `provider_live_claim=false`, `secrets_exposed=false`; RFC 9110 / Google Play Games / OWASP are informative evidence only.
- Current state: R14.8 **COMPLETE** at END-sync; R14.9–R14.17 **PLANNED**.
- Manual intervention: **NONE**.
"""
cont, n = re.subn(r"## R14\.8 start authority\n.*?\n## External research baseline relevant to R14\.8", authority + "\n## External research baseline relevant to R14.8", cont, count=1, flags=re.S)
assert n == 1, f"authority replacements={n}"
next_text = """## Next authorized action

Treat `8132c4029983f693a32e0d26903d05e347313bf6` as the only immutable R14.8 technical source. The END-sync head may differ only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_8_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Cloud Save Acceptance. If all are SUCCESS, merge PR #271 only with `expected_head_sha` equal to that exact END-head. Then perform exactly one continuity-only post-merge normalization, fresh R0/Python/UI, and protected merge. Do not start R14.9 until normalized `main` exists. Manual intervention remains **NONE**.
"""
cont, n = re.subn(r"## Next authorized action\n.*\Z", next_text, cont, count=1, flags=re.S)
assert n == 1, f"next replacements={n}"
cont_path.write_text(cont, encoding="utf-8")

assert Path("docs/roadmap/R14_8_ACCEPTANCE.md").exists()
Path(".github/workflows/r14-8-end-sync-helper.yml").unlink()
Path(".github/r14_8_end_sync.py").unlink()
