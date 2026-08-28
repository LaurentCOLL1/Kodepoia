from pathlib import Path

path = Path("docs/roadmap/R14_PLAN.md")
text = path.read_text(encoding="utf-8")

old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.7 are COMPLETE + NORMALIZED. R14.7 implementation/evidence PR #269 merged as `763ce96c4f82da2eaec167b56ffb62d9e548b300`; its single continuity-only normalization PR #270 merged as normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after R0 #1810, Python Core #1784 and UI #1751, all SUCCESS. R14.8 is IN_PROGRESS on `r14/08-cloud-saves`; R14.9–R14.17 remain PLANNED. R14.8 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.7 are COMPLETE + NORMALIZED. R14.7 implementation/evidence PR #269 merged as `763ce96c4f82da2eaec167b56ffb62d9e548b300`; its single continuity-only normalization PR #270 merged as normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after R0 #1810, Python Core #1784 and UI #1751, all SUCCESS. R14.8 technical source `8132c4029983f693a32e0d26903d05e347313bf6` is accepted after R0 #1822, Python Core #1796, UI #1763 and R14 Cloud Save Acceptance #6, all SUCCESS. R14.8 is COMPLETE at END-sync; final exact-head re-gates, protected merge and the single continuity-only normalization remain required. R14.9–R14.17 remain PLANNED. R14.8 manual state is NONE."
assert text.count(old_checkpoint) == 1
text = text.replace(old_checkpoint, new_checkpoint)

old_row = "| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | IN_PROGRESS | NONE | R14.5–R14.6 |"
new_row = "| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | COMPLETE | NONE | R14.5–R14.6 |"
assert text.count(old_row) == 1
text = text.replace(old_row, new_row)

h8 = "# R14.8 — Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery"
h9 = "# R14.9 — Achievements, stats, leaderboards + authoritative progression"
assert text.count(h8) == 1 and text.count(h9) == 1
pre, tail = text.split(h8, 1)
section, post = tail.split(h9, 1)
assert section.count("## Completion record") == 1
section_pre = section.split("## Completion record", 1)[0]
record = '''## Completion record

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

---

'''
text = pre + h8 + section_pre + record + h9 + post
path.write_text(text, encoding="utf-8")
