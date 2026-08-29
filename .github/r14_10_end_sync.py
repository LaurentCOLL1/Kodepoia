from pathlib import Path

SOURCE = "8a102a19512b076a8edb5c561e86b1d0101bc391"
BASE = "1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf"
PR = 275

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.9 are COMPLETE + NORMALIZED on normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`. R14.9 immutable technical source `155119282af7f4bf71840fc45c2d3de8891f73cd`; accepted END-head `2619e190601089ca2d98b22ccb4c0d254f1f11f7`; PR #273 merge `5f55e8b1811c08e8eef310f18aa3801798153018`; single continuity-only normalization head `814fccac4a68e6de19a98b6c0b622c4298ca1a99` passed R0 #1845, Python Core #1819 and UI #1786 and merged by PR #274 as normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`. R14.10 is IN_PROGRESS on `r14/10-entitlements-billing-catalog`; R14.11–R14.17 remain PLANNED. R14.10 manual state is CONDITIONAL / NOT TRIGGERED; provider-live claim is false."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.9 are COMPLETE + NORMALIZED on normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`. R14.10 is COMPLETE at technical/evidence + END-sync level on `r14/10-entitlements-billing-catalog`; immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391` passed R14 Entitlements Acceptance run `33233097442` on Ubuntu and Windows. PR #275 still requires fresh exact END-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Entitlements Acceptance, protected merge and exactly one continuity-only normalization before R14.11. R14.11–R14.17 remain PLANNED. R14.10 manual state is CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert plan.count(old_checkpoint) == 1, plan.count(old_checkpoint)
plan = plan.replace(old_checkpoint, new_checkpoint)

old_row = "| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R14.4–R14.6 + R13 store contracts |"
new_row = "| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | COMPLETE | CONDITIONAL / NOT TRIGGERED | R14.4–R14.6 + R13 store contracts |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)

section_start = plan.index("# R14.10 — Entitlements, billing/catalog + server-side provider verification/notifications")
section_end = plan.index("# R14.11 — Remote config, feature flags, targeting + safe rollout/rollback")
section = plan[section_start:section_end]
old_completion = "## Completion record\n\nTo be appended when accepted."
completion = """## Completion record

- Dedicated branch: `r14/10-entitlements-billing-catalog`; exact normalized branch point: R14.9 `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- Rejected candidate `55fed19c2ccbb63c790aa427a9afd9366cfe9cef` is NON-AUTHORITATIVE and its evidence must never be reused. Its first dedicated acceptance run exposed that the shared canonical JSON helper incorrectly coerced ordered event arrays through `dict(payload)`.
- The canonicalizer was corrected without changing existing mapping serialization semantics: canonical JSON now accepts JSON-compatible payloads directly while preserving key sorting, compact separators, Unicode handling and NaN rejection. No authority boundary was weakened.
- Accepted immutable technical source: `8a102a19512b076a8edb5c561e86b1d0101bc391`.
- Dedicated exact-source R14 Entitlements Acceptance run `33233097442`: Ubuntu job `99049221513` SUCCESS; Windows job `99049221666` SUCCESS.
- Focused regression covers R14.4 auth/identity/sessions, R14.5 PostgreSQL persistence, R14.6 authoritative server, R14.10 entitlements/billing, plus R13.7 Google Play readiness and R13.15 mobile store compliance.
- Nineteen frozen checks PASS cross-platform: client receipt rejection, invalid notification signature/token rejection, pending-no-grant, verified-provider grant, mutation-free duplicate replay, message/purchase account rebind rejection, out-of-order no-regression, reconciliation convergence/idempotency, server-clock expiry, environment isolation, Apple V2 contract, immutable catalog version, object/function authorization, bounded capacity and redacted evidence.
- Cross-platform evidence JSON is byte-for-byte equivalent. Digests: catalog `029829e18972971f3551f3a0a99e3e641e55ab7a2fb6cb374f6b4645b482389c`; state `3a526baa050763c8b5453c7970f750ce205ef57d864a612986b43488ab9f0154`; trace `1333f7f917742d6a0f93028466e0f1c8e771b9442dfe5403c22184764e1edbeb`; provider events `57962e7fddd666146ebb90aa4fed26eb20a287346995bb37f552179780ea447d`; Google entitlement `b0348458e900e79b8eed4237040a6cd33ca329f52920e613a6d8007ea0ae9a88`; Apple entitlement `69bae02f05593d6c73bc0928cb01b8de72cb6afdacbea47d6592a57f6e20d851`.
- Evidence counts/budgets: 5 provider events, 3 purchase records, 2 catalog definitions; `max_catalog_versions=32`, `max_provider_events=128`, `max_purchases=32`, `max_accounts=32`, `max_reconciliations=64`.
- Canonical artifacts: Ubuntu `9709088552` / `sha256:9f768b4423cd6b735dc5be51ce258596f78d7bd722106f889fbad30b69f188f3`; Windows `9709093199` / `sha256:6c8475949e29a7720aea89a583d6f45bdfd3335c04598893fe7d7afe0070c57c`.
- Evidence schema: `schemas/r14/backend-entitlement-evidence.schema.json`; evidence reports `manual_state=conditional_not_triggered`, `provider_live_claim=false`, `secrets_exposed=false`.
- Current official compatibility evidence remains aligned: Google RTDN is a change signal requiring backend status lookup and recommends message-ID dedupe; Apple V2 uses App Store-signed JWS `signedPayload`, duplicate identity `notificationUUID` and signed snapshot time `signedDate`. These are compatibility constraints only, not live-provider proof.
- Manual intervention: CONDITIONAL / NOT TRIGGERED. No production provider account, product, credential, private key, purchase token or real-money transaction was requested or used.
- END state: R14.10 COMPLETE; R14.11–R14.17 remain PLANNED. R14.11 is not authorized until the exact R14.10 END-head passes fresh R0/Python/UI/R14 Entitlements gates, PR #275 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.
""".rstrip()
assert section.count(old_completion) == 1, section.count(old_completion)
section = section.replace(old_completion, completion)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = continuity_path.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.9 COMPLETE + NORMALIZED. R14.10 IN_PROGRESS. R14.11–R14.17 PLANNED.** Normalized `main` d’autorité `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`; branche active `r14/10-entitlements-billing-catalog`. R14.10 doit conserver les entitlements server-authoritative, vérifier/réconcilier l’état provider avant grant, dédupliquer/rejeter replay/out-of-order/cross-environment, et ne jamais exposer de secret/token. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.9 COMPLETE + NORMALIZED. R14.10 COMPLETE (END-SYNCED; merge/normalization pending). R14.11–R14.17 PLANNED.** R14.10 source technique immuable `8a102a19512b076a8edb5c561e86b1d0101bc391`; R14 Entitlements Acceptance `33233097442` est SUCCESS Ubuntu + Windows. Re-gater l’END-head exact avec R0 + full Python Core + UI + R14 Entitlements, merger PR #275 avec expected-head, puis effectuer exactement une normalisation continuity-only avant R14.11. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert cont.count(old_prompt) == 1, cont.count(old_prompt)
cont = cont.replace(old_prompt, new_prompt)

old_global = "- R14.10 : **IN_PROGRESS** sur `r14/10-entitlements-billing-catalog`, branch point exact `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.\n- R14.11–R14.17 : **PLANNED**."
new_global = "- R14.10 : **COMPLETE (END-SYNCED; merge/normalization pending)** sur `r14/10-entitlements-billing-catalog`; source technique immuable `8a102a19512b076a8edb5c561e86b1d0101bc391`; PR #275 ouverte.\n- R14.11–R14.17 : **PLANNED**."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)

old_status = "| R14.10 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |"
assert cont.count(old_status) == 1, cont.count(old_status)
cont = cont.replace(old_status, "| R14.10 | COMPLETE | CONDITIONAL / NOT TRIGGERED |")

closure = """
## R14.10 technical closure authority

- Dedicated branch `r14/10-entitlements-billing-catalog`; exact normalized base `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- Rejected candidate `55fed19c2ccbb63c790aa427a9afd9366cfe9cef`: NON-AUTHORITATIVE. Dedicated run `33233002948` detected the canonical JSON array digest defect; no evidence from that SHA is reusable.
- Immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391` after the mapping-compatible canonicalizer correction.
- Dedicated technical gate: R14 Entitlements Acceptance `33233097442` — Ubuntu `99049221513` SUCCESS, Windows `99049221666` SUCCESS.
- Focused regression spans R14.10 plus R14.4–R14.6 authority/auth/persistence and R13.7/R13.15 store compliance. Nineteen entitlement/billing checks PASS on both OS.
- Cross-platform evidence JSON is identical. Digests: catalog `029829e18972971f3551f3a0a99e3e641e55ab7a2fb6cb374f6b4645b482389c`; state `3a526baa050763c8b5453c7970f750ce205ef57d864a612986b43488ab9f0154`; trace `1333f7f917742d6a0f93028466e0f1c8e771b9442dfe5403c22184764e1edbeb`; provider event `57962e7fddd666146ebb90aa4fed26eb20a287346995bb37f552179780ea447d`; Google entitlement `b0348458e900e79b8eed4237040a6cd33ca329f52920e613a6d8007ea0ae9a88`; Apple entitlement `69bae02f05593d6c73bc0928cb01b8de72cb6afdacbea47d6592a57f6e20d851`.
- Artifacts: Ubuntu `9709088552` / `sha256:9f768b4423cd6b735dc5be51ce258596f78d7bd722106f889fbad30b69f188f3`; Windows `9709093199` / `sha256:6c8475949e29a7720aea89a583d6f45bdfd3335c04598893fe7d7afe0070c57c`.
- `manual_state=conditional_not_triggered`; `provider_live_claim=false`; `secrets_exposed=false`. No live store proof is claimed.
- PR #275 carries R14.10. Final END-head must differ from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_10_ACCEPTANCE.md` and this continuity file, then pass fresh exact-head R0/Python/UI/R14 Entitlements before expected-head merge.
- After merge, exactly one continuity-only normalization with fresh R0/Python/UI is mandatory before R14.11. R14.11–R14.17 remain PLANNED.

"""
next_heading = "## Next authorized action\n\n"
assert cont.count(next_heading) == 1, cont.count(next_heading)
pos = cont.index(next_heading)
cont = cont[:pos] + closure + cont[pos:]
old_next = "Verify the final R14.10 START head differs from normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf` only by `docs/roadmap/R14_PLAN.md` and this continuity file. Only after that clean compare may R14.10 implementation begin. Implement provider-neutral catalog/purchase/entitlement/event/reconciliation contracts with authoritative verification, immutable event identity, dedupe/replay/out-of-order/environment isolation, privacy/redaction and bounded state; add adversarial tests and deterministic evidence. Do not claim provider-live success or request credentials. Manual state remains CONDITIONAL / NOT TRIGGERED."
new_next = "Treat `8a102a19512b076a8edb5c561e86b1d0101bc391` as the only immutable R14.10 technical source. Verify the exact END-head diff from that source is limited to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_10_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Entitlements Acceptance. If all are SUCCESS, merge PR #275 only with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Do not start R14.11 before normalized `main` exists. Manual state remains CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert cont.count(old_next) == 1, cont.count(old_next)
cont = cont.replace(old_next, new_next)
continuity_path.write_text(cont, encoding="utf-8")
