from pathlib import Path

BASE = "a9db57de1c1cc550604edbe6fec095e0a8e13c40"
R1410_NORM_HEAD = "d56246f65f834c87ef32a0ba645ca3a76ba898ab"
R1410_NORM_MERGE = BASE

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.9 are COMPLETE + NORMALIZED on normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`. R14.10 is COMPLETE at technical/evidence + END-sync level on `r14/10-entitlements-billing-catalog`; immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391` passed R14 Entitlements Acceptance run `33233097442` on Ubuntu and Windows. PR #275 still requires fresh exact END-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Entitlements Acceptance, protected merge and exactly one continuity-only normalization before R14.11. R14.11–R14.17 remain PLANNED. R14.10 manual state is CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.10 are COMPLETE + NORMALIZED on normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`. R14.10 immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`; single continuity-only normalization head `d56246f65f834c87ef32a0ba645ca3a76ba898ab` passed R0 #1854, Python Core #1828 and UI #1795 and merged by PR #276 as normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`. R14.11 is IN_PROGRESS on `r14/11-remote-config-feature-flags`; R14.12–R14.17 remain PLANNED. R14.11 manual state is NONE."
assert plan.count(old_checkpoint) == 1, plan.count(old_checkpoint)
plan = plan.replace(old_checkpoint, new_checkpoint)
old_row = "| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | PLANNED | NONE | R14.5–R14.6 |"
new_row = "| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | IN_PROGRESS | NONE | R14.5–R14.6 |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)
section_start = plan.index("# R14.11 — Remote config, feature flags, targeting + safe rollout/rollback")
section_end = plan.index("# R14.12 — Content delivery: immutable manifests/bundles, channels, cache + rollback")
section = plan[section_start:section_end]
needle = "## Completion record\n\nTo be appended when accepted."
start_record = """## START authority

- Dedicated branch: `r14/11-remote-config-feature-flags`.
- Exact branch point: normalized R14.10 `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- R14.10 closure authority: immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391`; final END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; END gates R0 #1852 / `33233480750`, Python Core #1826 / `33233480761`, UI #1793 / `33233480825`, R14 Entitlements #12 / `33233480782` all SUCCESS; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`.
- Single R14.10 post-merge normalization head `d56246f65f834c87ef32a0ba645ca3a76ba898ab` changed only continuity, passed R0 #1854 / `33233746051`, Python Core #1828 / `33233746018`, UI #1795 / `33233746115`, and PR #276 merged with expected-head as normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- START state: R14.1–R14.10 COMPLETE + NORMALIZED; R14.11 IN_PROGRESS; R14.12–R14.17 PLANNED.
- Trust invariants: immutable/versioned definitions and snapshots; no remote arbitrary code/script execution; unsupported or unknown value/rule types fail closed; evaluation context is canonical, bounded and privacy-governed; fractional rollout uses stable deterministic hashing; prerequisite cycles fail closed; expiry/kill-switch override rollout safely; production activation requires explicit permission + audit + SafeChange; rollback reactivates a prior immutable snapshot rather than mutating history.
- OpenFeature compatibility is conceptual/provider-boundary only. Current stable concepts used as reference: typed flag evaluation, evaluation context with optional targeting key, fractional evaluation, deterministic provider-neutral resolution and privacy caution for context data. Experimental/provider-specific behavior is not architecture authority.
- Manual intervention: NONE for provider-neutral core.

## Completion record

To be appended when accepted."""
assert section.count(needle) == 1, section.count(needle)
section = section.replace(needle, start_record)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.10 COMPLETE + NORMALIZED. R14.11–R14.17 PLANNED.** R14.10 source technique immuable `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 fusionnée par merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715` après R0 #1852, Python Core #1826, UI #1793 et R14 Entitlements #12 tous SUCCESS. Cette continuité est l’unique normalisation post-merge R14.10; sur une branche de normalisation, elle doit encore passer R0 + full Python Core + UI et être mergée avec expected-head avant d’autoriser R14.11. Manual state : CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.10 COMPLETE + NORMALIZED. R14.11 IN_PROGRESS. R14.12–R14.17 PLANNED.** Normalized `main` d’autorité `a9db57de1c1cc550604edbe6fec095e0a8e13c40`; branche active `r14/11-remote-config-feature-flags`. R14.11 doit conserver des snapshots/définitions immuables, évaluation typée/canonique, targeting déterministe, rollout fractionnel stable, prérequis/expiry/kill-switch, preview, approval/audit/SafeChange pour prod et rollback vers snapshot antérieur. Aucun code/script distant arbitraire. Manual state : NONE."
assert cont.count(old_prompt) == 1, cont.count(old_prompt)
cont = cont.replace(old_prompt, new_prompt)
old_global = "- R14.10 : **COMPLETE + NORMALIZED** — source technique `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`; unique normalization branch `r14/10-normalization`.\n- R14.11–R14.17 : **PLANNED**."
new_global = "- R14.10 : **COMPLETE + NORMALIZED** — source technique `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`; normalization head `d56246f65f834c87ef32a0ba645ca3a76ba898ab`; normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40` via PR #276.\n- R14.11 : **IN_PROGRESS** sur `r14/11-remote-config-feature-flags`, branch point exact `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.\n- R14.12–R14.17 : **PLANNED**."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)
old_status = "| R14.11 | PLANNED | NONE |"
assert cont.count(old_status) == 1, cont.count(old_status)
cont = cont.replace(old_status, "| R14.11 | IN_PROGRESS | NONE |")
old_tail = "- Unique post-merge normalization branch: `r14/10-normalization`, created exactly from merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`. Its final tree delta must contain only this continuity file and must pass fresh exact-head R0/Python/UI before expected-head merge.\n- R14.10 final state is COMPLETE + NORMALIZED once that unique normalization PR merges; R14.11–R14.17 remain PLANNED until then."
new_tail = "- Unique post-merge normalization head `d56246f65f834c87ef32a0ba645ca3a76ba898ab` changed only this continuity file; fresh normalization gates R0 #1854 / `33233746051`, Python Core #1828 / `33233746018`, UI #1795 / `33233746115` all SUCCESS.\n- Normalization PR #276 merged with `expected_head_sha=d56246f65f834c87ef32a0ba645ca3a76ba898ab` as normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.\n- R14.10 final state: COMPLETE + NORMALIZED; R14.11 is authorized from that exact normalized `main`."
assert cont.count(old_tail) == 1, cont.count(old_tail)
cont = cont.replace(old_tail, new_tail)
old_next = "If this file is read from `r14/10-normalization`, verify its exact diff from merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715` contains only this continuity file, run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, and merge the single normalization PR only with `expected_head_sha` equal to that exact normalization head. If this file is read from `main` after that protected merge, R14.10 is COMPLETE + NORMALIZED and R14.11 becomes the next authorized subdivision; start R14.11 only from that normalized `main` with a dedicated branch and START-sync. Manual state remains CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`."
new_next = "Verify the final R14.11 START head differs from normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40` only by `docs/roadmap/R14_PLAN.md` and this continuity file. Only after that clean compare may R14.11 implementation begin. Implement immutable typed config/flag snapshots, canonical privacy-bounded evaluation context, deterministic targeting/fractional rollout, prerequisites/cycle rejection, expiry, kill-switch, preview, production permission/audit/SafeChange activation and immutable rollback. Manual state remains NONE."
assert cont.count(old_next) == 1, cont.count(old_next)
cont = cont.replace(old_next, new_next)
start_block = """
## R14.11 START authority

- Dedicated branch: **`r14/11-remote-config-feature-flags`**.
- Exact branch point: normalized R14.10 `main` **`a9db57de1c1cc550604edbe6fec095e0a8e13c40`**.
- R14.10 normalization: `d56246f65f834c87ef32a0ba645ca3a76ba898ab`; R0 #1854 / `33233746051`, Python Core #1828 / `33233746018`, UI #1795 / `33233746115` SUCCESS; PR #276 expected-head merge produced the exact normalized base.
- State at START: R14.1–R14.10 **COMPLETE + NORMALIZED**; R14.11 **IN_PROGRESS**; R14.12–R14.17 **PLANNED**.
- OpenFeature compatibility baseline: evaluation context supports a targeting key used by providers for fractional evaluation; context may contain custom typed fields but must be privacy-governed. R14.11 uses these stable concepts without claiming full SDK conformance.
- Core safety invariant: remote config carries typed data/rules only; no remote arbitrary code or script execution. Unknown types, invalid context, prerequisite cycles and unsafe production activation fail closed.
- Manual intervention: **NONE**.

"""
marker = "## Next authorized action\n\n"
assert cont.count(marker) == 1, cont.count(marker)
pos = cont.index(marker)
cont = cont[:pos] + start_block + cont[pos:]
cont_path.write_text(cont, encoding="utf-8")
