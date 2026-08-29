from pathlib import Path

SOURCE = "a58a0cf48a5e2311b5f6e671655f107e92c4645e"
BASE = "a9db57de1c1cc550604edbe6fec095e0a8e13c40"

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.10 are COMPLETE + NORMALIZED on normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`. R14.10 immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391`; END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`; single continuity-only normalization head `d56246f65f834c87ef32a0ba645ca3a76ba898ab` passed R0 #1854, Python Core #1828 and UI #1795 and merged by PR #276 as normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`. R14.11 is IN_PROGRESS on `r14/11-remote-config-feature-flags`; R14.12–R14.17 remain PLANNED. R14.11 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.10 are COMPLETE + NORMALIZED on normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`. R14.11 is COMPLETE at technical/evidence + END-sync level on `r14/11-remote-config-feature-flags`; immutable technical source `a58a0cf48a5e2311b5f6e671655f107e92c4645e` passed R14 Remote Config Acceptance run `33234881304` on Ubuntu and Windows. Final END-head still requires fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Remote Config Acceptance, protected merge and exactly one continuity-only normalization before R14.12. R14.12–R14.17 remain PLANNED. R14.11 manual state is NONE."
assert plan.count(old_checkpoint) == 1, plan.count(old_checkpoint)
plan = plan.replace(old_checkpoint, new_checkpoint)
old_row = "| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | IN_PROGRESS | NONE | R14.5–R14.6 |"
new_row = "| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | COMPLETE | NONE | R14.5–R14.6 |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)
section_start = plan.index("# R14.11 — Remote config, feature flags, targeting + safe rollout/rollback")
section_end = plan.index("# R14.12 — Content delivery: immutable manifests/bundles, channels, cache + rollback")
section = plan[section_start:section_end]
old_completion = "## Completion record\n\nTo be appended when accepted."
completion = """## Completion record

- Dedicated branch: `r14/11-remote-config-feature-flags`; exact normalized branch point `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- Rejected candidate `b43acf2a0f870587a85141cbdb91a3cf352bf2c7` is NON-AUTHORITATIVE and its evidence must never be reused. Its first R14 Remote Config Acceptance run `33234680565` exposed an invalid test/acceptance fixture assumption: object authorization IDs cannot use the permission wildcard `*`.
- The correction enumerated explicit authorized snapshot/flag/environment object IDs and did not weaken historical R14.6 authority semantics.
- Intermediate green source `2a97caac8e2ac19615f7ce2c64585ae8080bd2fe` proved the corrected core but was not frozen because public backend exports were still incomplete.
- Accepted immutable technical source: `a58a0cf48a5e2311b5f6e671655f107e92c4645e`, including public `kodepoia.backend` exports and their dedicated regression.
- Dedicated exact-source R14 Remote Config Acceptance run `33234881304`: Ubuntu job `99053992967` SUCCESS; Windows job `99053993105` SUCCESS.
- Focused regression spans R14.5 PostgreSQL persistence, R14.6 authoritative server, R14.11 remote-config semantics and R14.11 public backend exports.
- Nineteen checks PASS cross-platform: typed schema, immutable snapshots, targeting precedence, stable fractional assignment, bounded rollout distribution, targeting-key fail-closed, prerequisite-cycle rejection, prerequisite enforcement, server-clock expiry, kill-switch override, preview/dry-run, production approval + SafeChange, rollback, environment isolation, object/function authorization, typed OpenFeature-style fallback, redacted evidence, bounded capacity and remote-code type rejection.
- Cross-platform decoded evidence is identical. Digests: snapshot `70397539d8e0fd41102387f32a29f947f29b629cbbfddbd9b20b660b40ca27c4`; state `5343df1b58f0f595133261cdff705d720dc2e2c561e6d01cd69263060680a0c9`; trace `4f45743cdc5af05bbdb795026d2e15a76c502c37d46c649a5ba08347efd00509`; audit `4ec2eb54f751b49c6f43388fc7fcc76f16b7cc9e76eeffe703a638c941b46aa7`; rollout assignment `24df98a3b2058d746bbbec24af41299acc9d84ea2b3d102cee4efbb56de69a98`; rollback preview `d34ad885b9bb733120616e14c96c3e82418d1e3bdbc05099538c9c00022a176a`.
- Fractional fixture: 2,000 subjects -> `off=980`, `on=1020`; same targeting key remains assigned despite unrelated context changes.
- Rollback fixture: `test-v2 → test-v1`, final active `test-v1`; immutable snapshots remain registered.
- Budgets: `max_snapshots=32`, `max_flags_per_snapshot=32`, `max_evaluations=5000`, `max_audit_records=128`.
- Artifacts: Ubuntu `9709604569` / `sha256:25026a76c041d780cb75aeb0cc6cf06143c4a6a5430dc1c1c3a3c82725c6ef63`; Windows `9709607701` / `sha256:1db48d5162f36132568ec8d223c036c7267831f471f068d4140e6ef9360eee24`.
- Evidence schema: `schemas/r14/backend-remote-config-evidence.schema.json`; state is `manual_state=none`, `provider_live_claim=false`, `secrets_exposed=false`, `pii_exposed=false`, `arbitrary_code_execution=false`.
- Stable OpenFeature concepts are informative/provider-boundary evidence only: optional targeting key for subject identity/fractional evaluation, typed evaluation/default fallback, typed context, privacy caution and standard error vocabulary. No full OpenFeature conformance is claimed.
- END state: R14.11 COMPLETE; R14.12–R14.17 remain PLANNED. R14.12 is not authorized until the exact R14.11 END-head passes fresh R0/Python/UI/R14 Remote Config gates, the implementation PR merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.
""".rstrip()
assert section.count(old_completion) == 1, section.count(old_completion)
section = section.replace(old_completion, completion)
plan = plan[:section_start] + section + plan[section_end:]
plan_path.write_text(plan, encoding="utf-8")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.10 COMPLETE + NORMALIZED. R14.11 IN_PROGRESS. R14.12–R14.17 PLANNED.** Normalized `main` d’autorité `a9db57de1c1cc550604edbe6fec095e0a8e13c40`; branche active `r14/11-remote-config-feature-flags`. R14.11 doit conserver des snapshots/définitions immuables, évaluation typée/canonique, targeting déterministe, rollout fractionnel stable, prérequis/expiry/kill-switch, preview, approval/audit/SafeChange pour prod et rollback vers snapshot antérieur. Aucun code/script distant arbitraire. Manual state : NONE."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.10 COMPLETE + NORMALIZED. R14.11 COMPLETE (END-SYNCED; merge/normalization pending). R14.12–R14.17 PLANNED.** R14.11 source technique immuable `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; R14 Remote Config Acceptance `33234881304` SUCCESS Ubuntu + Windows. Re-gater l’END-head exact avec R0 + full Python Core + UI + R14 Remote Config, merger avec expected-head, puis effectuer exactement une normalisation continuity-only avant R14.12. Manual state : NONE."
assert cont.count(old_prompt) == 1, cont.count(old_prompt)
cont = cont.replace(old_prompt, new_prompt)
old_global = "- R14.11 : **IN_PROGRESS** sur `r14/11-remote-config-feature-flags`, branch point exact `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.\n- R14.12–R14.17 : **PLANNED**."
new_global = "- R14.11 : **COMPLETE (END-SYNCED; merge/normalization pending)** sur `r14/11-remote-config-feature-flags`; source technique immuable `a58a0cf48a5e2311b5f6e671655f107e92c4645e`.\n- R14.12–R14.17 : **PLANNED**."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)
old_status = "| R14.11 | IN_PROGRESS | NONE |"
assert cont.count(old_status) == 1, cont.count(old_status)
cont = cont.replace(old_status, "| R14.11 | COMPLETE | NONE |")
closure = """
## R14.11 technical closure authority

- Dedicated branch `r14/11-remote-config-feature-flags`; exact normalized base `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- Rejected candidate `b43acf2a0f870587a85141cbdb91a3cf352bf2c7`: NON-AUTHORITATIVE. Its dedicated run `33234680565` detected invalid wildcard object IDs in R14.11 fixtures; no evidence from that SHA is reusable.
- Historical authority was not weakened. Fixtures now enumerate explicit authorized objects while wildcard permissions retain existing R14.6 semantics.
- Intermediate `2a97caac8e2ac19615f7ce2c64585ae8080bd2fe` passed the corrected core but is not the final source because the public backend export surface was completed afterward.
- Immutable technical source `a58a0cf48a5e2311b5f6e671655f107e92c4645e` includes remote-config implementation, tests, schema, deterministic acceptance gate, public backend exports and export regression.
- Dedicated technical gate `33234881304`: Ubuntu `99053992967` SUCCESS; Windows `99053993105` SUCCESS.
- All nineteen remote-config checks PASS on both OS. Decoded evidence objects are identical; fractional fixture is `980/1020` across 2,000 subjects; rollback converges `test-v2 → test-v1`.
- Digests: snapshot `70397539d8e0fd41102387f32a29f947f29b629cbbfddbd9b20b660b40ca27c4`; state `5343df1b58f0f595133261cdff705d720dc2e2c561e6d01cd69263060680a0c9`; trace `4f45743cdc5af05bbdb795026d2e15a76c502c37d46c649a5ba08347efd00509`; audit `4ec2eb54f751b49c6f43388fc7fcc76f16b7cc9e76eeffe703a638c941b46aa7`; rollout `24df98a3b2058d746bbbec24af41299acc9d84ea2b3d102cee4efbb56de69a98`; rollback preview `d34ad885b9bb733120616e14c96c3e82418d1e3bdbc05099538c9c00022a176a`.
- Artifacts: Ubuntu `9709604569` / `sha256:25026a76c041d780cb75aeb0cc6cf06143c4a6a5430dc1c1c3a3c82725c6ef63`; Windows `9709607701` / `sha256:1db48d5162f36132568ec8d223c036c7267831f471f068d4140e6ef9360eee24`.
- `manual_state=none`; `provider_live_claim=false`; `secrets_exposed=false`; `pii_exposed=false`; `arbitrary_code_execution=false`.
- Stable OpenFeature concepts are compatibility evidence only, not architecture authority or full conformance proof.
- Final END-head must differ from immutable source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_11_ACCEPTANCE.md` and this continuity file, then pass fresh exact-head R0/Python/UI/R14 Remote Config before expected-head merge.
- After merge, exactly one continuity-only normalization with fresh R0/Python/UI is mandatory before R14.12. R14.12–R14.17 remain PLANNED.

"""
marker = "## Next authorized action\n\n"
assert cont.count(marker) == 1, cont.count(marker)
pos = cont.index(marker)
cont = cont[:pos] + closure + cont[pos:]
old_next = "Verify the final R14.11 START head differs from normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40` only by `docs/roadmap/R14_PLAN.md` and this continuity file. Only after that clean compare may R14.11 implementation begin. Implement immutable typed config/flag snapshots, canonical privacy-bounded evaluation context, deterministic targeting/fractional rollout, prerequisites/cycle rejection, expiry, kill-switch, preview, production permission/audit/SafeChange activation and immutable rollback. Manual state remains NONE."
new_next = "Treat `a58a0cf48a5e2311b5f6e671655f107e92c4645e` as the only immutable R14.11 technical source. Verify the exact END-head diff from that source is limited to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_11_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Remote Config Acceptance. If all are SUCCESS, merge only with `expected_head_sha` equal to that exact END-head, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Do not start R14.12 before normalized `main` exists. Manual state remains NONE."
assert cont.count(old_next) == 1, cont.count(old_next)
cont = cont.replace(old_next, new_next)
cont_path.write_text(cont, encoding="utf-8")
