from pathlib import Path

BASE = "1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf"
BRANCH = "r14/10-entitlements-billing-catalog"

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.8 are COMPLETE + NORMALIZED. R14.9 is COMPLETE at technical/evidence + END-sync level on `r14/09-progression-leaderboards`; immutable technical source `155119282af7f4bf71840fc45c2d3de8891f73cd` passed R0 #1836, Python Core #1810, UI #1777 and R14 Progression Acceptance #3. R14.10–R14.17 remain PLANNED. PR #273 still requires fresh exact END-head re-gates, protected merge and exactly one continuity-only normalization before R14.10. R14.9 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.9 are COMPLETE + NORMALIZED on normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`. R14.9 immutable technical source `155119282af7f4bf71840fc45c2d3de8891f73cd`; accepted END-head `2619e190601089ca2d98b22ccb4c0d254f1f11f7`; PR #273 merge `5f55e8b1811c08e8eef310f18aa3801798153018`; single continuity-only normalization head `814fccac4a68e6de19a98b6c0b622c4298ca1a99` passed R0 #1845, Python Core #1819 and UI #1786 and merged by PR #274 as normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`. R14.10 is IN_PROGRESS on `r14/10-entitlements-billing-catalog`; R14.11–R14.17 remain PLANNED. R14.10 manual state is CONDITIONAL / NOT TRIGGERED; provider-live claim is false."
assert plan.count(old_checkpoint) == 1, plan.count(old_checkpoint)
plan = plan.replace(old_checkpoint, new_checkpoint)
old_row = "| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | PLANNED | CONDITIONAL | R14.4–R14.6 + R13 store contracts |"
new_row = "| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R14.4–R14.6 + R13 store contracts |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)
section_start = plan.index("# R14.10 — Entitlements, billing/catalog + server-side provider verification/notifications")
section_end = plan.index("# R14.11 — Remote config, feature flags, targeting + safe rollout/rollback")
section = plan[section_start:section_end]
old_manual_completion = "## Manual intervention\n\n**CONDITIONAL.** Core acceptance uses synthetic/sandbox contracts. Real Apple/Google production account, product and transaction verification is required only for a provider-live claim; user must never send secrets/private keys/tokens.\n\n## Completion record\n\nTo be appended when accepted."
new_manual_completion = """## Manual intervention

**CONDITIONAL / NOT TRIGGERED.** Core acceptance uses synthetic/provider-contract fixtures with `provider_live_claim=false`. Real Apple/Google production account, product and transaction verification is required only for a later explicit provider-live claim; user must never send secrets/private keys/tokens.

## START authority

- Dedicated branch: `r14/10-entitlements-billing-catalog`.
- Exact branch point: normalized R14.9 `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- R14.9 closure authority: technical source `155119282af7f4bf71840fc45c2d3de8891f73cd`; accepted END-head `2619e190601089ca2d98b22ccb4c0d254f1f11f7`; exact END gates R0 #1843 / `33211148134`, Python Core #1817 / `33211148235`, UI #1784 / `33211148160`, R14 Progression #10 / `33211148184` all SUCCESS; PR #273 merged with expected-head as `5f55e8b1811c08e8eef310f18aa3801798153018`.
- Single R14.9 post-merge normalization head `814fccac4a68e6de19a98b6c0b622c4298ca1a99` changed only continuity, passed R0 #1845 / `33223835030`, Python Core #1819 / `33223835012`, UI #1786 / `33223835008`, and PR #274 merged with expected-head as normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- START state: R14.1–R14.9 COMPLETE + NORMALIZED; R14.10 IN_PROGRESS; R14.11–R14.17 PLANNED.
- Core trust invariants: notification arrival/client receipt never grants entitlement by itself; provider identity/environment/message identity are explicit; provider events are immutable and deduplicated; authoritative provider state is verified/reconciled before entitlement transitions; transitions are transactional/idempotent; raw provider credentials/tokens are never model-visible evidence.
- Current official compatibility baseline: Google RTDN requires a subsequent Google Play Developer API query for complete purchase status and recommends deduplication by RTDN `messageId`; Google purchase verification belongs on the backend before granting entitlement. Apple App Store Server Notifications V2 uses App Store-signed JWS `signedPayload`, `notificationUUID` for duplicate suppression, and `signedDate` to prefer the most recent transaction-state snapshot. These are compatibility constraints, not provider-live proof.
- Manual state: CONDITIONAL / NOT TRIGGERED. `provider_live_claim=false`; no production account, product, purchase, credential, private key or token is required for core acceptance.

## Completion record

To be appended when accepted."""
assert section.count(old_manual_completion) == 1, section.count(old_manual_completion)
section = section.replace(old_manual_completion, new_manual_completion)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.9 COMPLETE + NORMALIZED (normalization PR pending merge). R14.10–R14.17 PLANNED.** R14.9 source technique immuable `155119282af7f4bf71840fc45c2d3de8891f73cd`; END-head exact `2619e190601089ca2d98b22ccb4c0d254f1f11f7`; fresh END gates R0 #1843, Python Core #1817, UI #1784 et R14 Progression Acceptance #10 sont SUCCESS; PR #273 a fusionné avec expected-head comme merge `5f55e8b1811c08e8eef310f18aa3801798153018`. La présente branche `r14/09-normalize-continuity` est l’unique normalisation continuity-only autorisée : valider son HEAD exact avec R0 + full Python Core + KodeStudio UI Smoke, puis merger avec expected-head avant toute R14.10. Manual intervention : NONE."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.9 COMPLETE + NORMALIZED. R14.10 IN_PROGRESS. R14.11–R14.17 PLANNED.** Normalized `main` d’autorité `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`; branche active `r14/10-entitlements-billing-catalog`. R14.10 doit conserver les entitlements server-authoritative, vérifier/réconcilier l’état provider avant grant, dédupliquer/rejeter replay/out-of-order/cross-environment, et ne jamais exposer de secret/token. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
assert cont.count(old_prompt) == 1, cont.count(old_prompt)
cont = cont.replace(old_prompt, new_prompt)
old_global = "- R14.1–R14.8 : **COMPLETE + NORMALIZED**.\n- R14.8 normalized `main` : **`433c86cc5d43bfea41adb529451367e10c75a30b`** après normalization PR #272.\n- R14.9 : **COMPLETE + NORMALIZED (normalization PR pending merge)** ; source technique immuable `155119282af7f4bf71840fc45c2d3de8891f73cd`, END-head `2619e190601089ca2d98b22ccb4c0d254f1f11f7`, implementation/evidence merge `5f55e8b1811c08e8eef310f18aa3801798153018`.\n- R14.10–R14.17 : **PLANNED**.\n- Manual state actuel : **NONE**."
new_global = "- R14.1–R14.9 : **COMPLETE + NORMALIZED**.\n- R14.9 normalized `main` : **`1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`** après normalization PR #274.\n- R14.10 : **IN_PROGRESS** sur `r14/10-entitlements-billing-catalog`, branch point exact `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.\n- R14.11–R14.17 : **PLANNED**.\n- Manual state actuel : **CONDITIONAL / NOT TRIGGERED** (`provider_live_claim=false`)."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)
old_status = "| R14.9 | COMPLETE + NORMALIZED | NONE |\n| R14.10 | PLANNED | CONDITIONAL |"
new_status = "| R14.9 | COMPLETE + NORMALIZED | NONE |\n| R14.10 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |"
assert cont.count(old_status) == 1, cont.count(old_status)
cont = cont.replace(old_status, new_status)
old_r149_tail = "- Single post-merge normalization branch: **`r14/09-normalize-continuity`**, created from exact merge `5f55e8b1811c08e8eef310f18aa3801798153018`; it is required to change only this continuity file.\n- Current state represented by this normalization candidate: R14.9 **COMPLETE + NORMALIZED**; R14.10–R14.17 **PLANNED**. R14.10 remains unauthorized until this exact normalization head passes fresh R0/Python/UI and is merged with expected-head.\n- Manual intervention: **NONE**."
new_r149_tail = "- Single post-merge normalization head: **`814fccac4a68e6de19a98b6c0b622c4298ca1a99`**, changing only this continuity file. Fresh normalization gates: R0 #1845 / `33223835030`, Python Core #1819 / `33223835012`, UI #1786 / `33223835008` — all SUCCESS.\n- Normalization PR #274 merged with `expected_head_sha=814fccac4a68e6de19a98b6c0b622c4298ca1a99` as normalized `main` **`1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`**.\n- R14.9 final state: **COMPLETE + NORMALIZED**; R14.10 is authorized from that exact normalized `main`.\n- Manual intervention: **NONE**."
assert cont.count(old_r149_tail) == 1, cont.count(old_r149_tail)
cont = cont.replace(old_r149_tail, new_r149_tail)
next_heading = "## Next authorized action\n\n"
assert cont.count(next_heading) == 1, cont.count(next_heading)
next_pos = cont.index(next_heading)
start_authority = """## R14.10 START authority

- Dedicated branch: **`r14/10-entitlements-billing-catalog`**.
- Exact branch point: normalized R14.9 `main` **`1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`**.
- State at START: R14.1–R14.9 **COMPLETE + NORMALIZED**; R14.10 **IN_PROGRESS**; R14.11–R14.17 **PLANNED**.
- Google compatibility invariant: RTDN is a change signal, not complete authoritative purchase state; backend re-queries Google Play Developer API and deduplicates RTDN `messageId` before converging entitlements.
- Apple compatibility invariant: App Store Server Notifications V2 `signedPayload` is App Store-signed JWS; `notificationUUID` is the duplicate key and most recent `signedDate` wins for repeated transaction snapshots.
- Core acceptance remains provider-neutral/synthetic. Manual state **CONDITIONAL / NOT TRIGGERED**; `provider_live_claim=false`; secrets/private keys/purchase tokens are never requested from the user or written to evidence.

"""
cont = cont[:next_pos] + start_authority + next_heading + "Verify the final R14.10 START head differs from normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf` only by `docs/roadmap/R14_PLAN.md` and this continuity file. Only after that clean compare may R14.10 implementation begin. Implement provider-neutral catalog/purchase/entitlement/event/reconciliation contracts with authoritative verification, immutable event identity, dedupe/replay/out-of-order/environment isolation, privacy/redaction and bounded state; add adversarial tests and deterministic evidence. Do not claim provider-live success or request credentials. Manual state remains CONDITIONAL / NOT TRIGGERED.\n"
cont_path.write_text(cont, encoding="utf-8")
