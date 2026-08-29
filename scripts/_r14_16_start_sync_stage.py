from pathlib import Path

BASE_MAIN = "8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36"
NORMALIZED_ANCHOR = "1f10d7a13f49cb6e931e5e0694f083228ed24070"
BRANCH = "r14/16-cli-kodestudio-liveops-ux"

plan_path = Path("docs/roadmap/R14_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

old_end = "- END-sync must change only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_15_ACCEPTANCE.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` from immutable source `232bae747e91fd97f4cf3110a019639217d7914b`, then pass fresh exact-head R0/Python/UI/R14 Resilience gates before expected-head merge."
new_end = "\n".join([
    "- Final clean END-head `80bd6853664ab9f41fd41fb83f43b43980bef394` is a direct child of immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; source→END changed exactly `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_15_ACCEPTANCE.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.",
    "- Fresh exact-END gates: R0 Repository Guard #1966 / `33257412850` SUCCESS; Python Core #1941 / `33257412849` SUCCESS 5/5 with Ubuntu **1731 passed / 13 skipped / 46 warnings**; KodeStudio UI Smoke #1906 / `33257412847` SUCCESS; R14 Service Operations Resilience Acceptance #3 / `33257412881` SUCCESS Ubuntu + Windows with 24/24 deterministic checks.",
    "- Fresh END artifacts: Ubuntu `9716228073` / `sha256:97f82c4203d6d8987883849069c3bd8f47345b90d6078c2fcedf236c5c237bec`; Windows `9716231809` / `sha256:87fa03305606e02cc7758cdbd334e1f545023792859cc825323afa096eec1573`.",
    "- PR #285 merged only with `expected_head_sha=80bd6853664ab9f41fd41fb83f43b43980bef394` as implementation merge `53373e78c60d4a338e9313496a822c93ab334e68`.",
    "- The unique post-merge normalization head `68a6f106484ab60d9925dfcc60189b509d995393` changed only continuity, passed fresh exact-head R0 #1973 / `33257784369`, Python Core #1948 / `33257784390` (5/5), and UI #1913 / `33257784370`, then PR #286 merged with `expected_head_sha=68a6f106484ab60d9925dfcc60189b509d995393` as normalized main `1f10d7a13f49cb6e931e5e0694f083228ed24070`.",
    "- Post-normalization continuity erratum head `ff8e24a13ae040956f9eff4ebaa19f02f4a142a1` corrected stale wording only; fresh erratum gates R0 #1979 / `33258615852`, Python Core #1954 / `33258615797`, and UI #1919 / `33258615872` all SUCCESS. PR #287 merged with exact expected-head as current main `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`. This erratum is explicitly **not** a second normalization; normalization cardinality remains exactly one.",
    "- R14.15 final state: **COMPLETE + NORMALIZED**. Manual/provider state remains **CONDITIONAL / NOT TRIGGERED**; no external-provider quota/cost/load, Internet-scale, multi-region or production PostgreSQL PITR claim is made. R14.16 START-sync is authorized from the current main carrying the normalized R14.15 state plus the continuity-only erratum.",
])
if plan.count(old_end) != 1:
    raise SystemExit(f"R14.15 END marker count={plan.count(old_end)}")
plan = plan.replace(old_end, new_end)

marker = "# R14.16 — CLI + KodeStudio Backend/LiveOps UX, local stack control + dry-run/provider status"
pre, sep, r16 = plan.partition(marker)
if not sep:
    raise SystemExit("R14.16 section missing")
old_tail = """## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.
"""
new_tail = f"""## Manual intervention

**NONE.**

## START authority

- Dedicated branch: `{BRANCH}`.
- Effective exact branch point: current `main` `{BASE_MAIN}`. R14.15's unique normalized anchor remains `{NORMALIZED_ANCHOR}`; PR #287 only added the continuity erratum and is not a second normalization.
- START state: R14.1–R14.15 **COMPLETE + NORMALIZED**; R14.16 **IN_PROGRESS**; R14.17 **PLANNED**.
- Scope authority is limited to structured CLI/KodeStudio workflows over existing R14 domain APIs: backend/local-stack status, migration preview/apply, provider capability, lobby/save/progression inspection, entitlement reconciliation preview, config/content/campaign preview/rollout/rollback, event replay preview, and resilience/backup/load reports.
- Trust invariants: no raw shell console; no raw secret values; no ungoverned endpoint/command escape; environment and authority scope remain visible; destructive/live mutations require existing permission/confirmation/SafeChange rules; inspect/preview/dry-run remains the default for migrations, replay, rollout, content and campaign actions; machine-readable CLI JSON must be stable and redacted.
- UX authority includes accessibility and localization regression coverage without weakening server/domain authorization. UI/CLI are adapters, never alternate authority paths.
- Manual intervention: **NONE**. Core R14.16 must remain provider-neutral and testable from local/hosted CI without external account, credential, production deployment or live provider proof.

## Completion record

To be appended when accepted.
"""
if r16.count(old_tail) != 1:
    raise SystemExit(f"R14.16 tail count={r16.count(old_tail)}")
r16 = r16.replace(old_tail, new_tail, 1)
plan = pre + sep + r16

old_top = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.14 COMPLETE + NORMALIZED. R14.15 COMPLETE + NORMALIZED. R14.16–R14.17 remain PLANNED; R14.16 START-sync is authorized from normalized main `1f10d7a13f49cb6e931e5e0694f083228ed24070`.**"
new_top = f"> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.15 COMPLETE + NORMALIZED. R14.16 IN_PROGRESS on `{BRANCH}` from effective branch point `{BASE_MAIN}`; R14.17 remains PLANNED and unauthorized.**"
if continuity.count(old_top) != 1:
    raise SystemExit(f"continuity top count={continuity.count(old_top)}")
continuity = continuity.replace(old_top, new_top)

old_global = "- R14.16–R14.17 : **PLANNED**."
new_global = f"- R14.16 : **IN_PROGRESS** — branch `{BRANCH}`; effective base `{BASE_MAIN}`; normalized R14.15 anchor `{NORMALIZED_ANCHOR}`; manual **NONE**.\n- R14.17 : **PLANNED**."
if continuity.count(old_global) != 1:
    raise SystemExit(f"global status count={continuity.count(old_global)}")
continuity = continuity.replace(old_global, new_global)

old_r15 = "- R14.15 : **COMPLETE + NORMALIZED** — immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; END-head `80bd6853664ab9f41fd41fb83f43b43980bef394`; PR #285 merge `53373e78c60d4a338e9313496a822c93ab334e68`; unique normalization head `68a6f106484ab60d9925dfcc60189b509d995393`; normalized `main` `1f10d7a13f49cb6e931e5e0694f083228ed24070` via PR #286 after fresh R0 #1973 / `33257784369`, Python Core #1948 / `33257784390`, and UI #1913 / `33257784370` SUCCESS; manual `CONDITIONAL / NOT TRIGGERED`."
new_r15 = old_r15[:-1] + "; post-normalization continuity erratum PR #287 -> current `main` `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36` after fresh R0 #1979 / `33258615852`, Python #1954 / `33258615797`, UI #1919 / `33258615872` SUCCESS; erratum is not a second normalization."
if continuity.count(old_r15) != 1:
    raise SystemExit(f"R14.15 global record count={continuity.count(old_r15)}")
continuity = continuity.replace(old_r15, new_r15)

old_row = "| R14.16 | PLANNED | NONE |"
new_row = "| R14.16 | IN_PROGRESS | NONE |"
if continuity.count(old_row) != 1:
    raise SystemExit(f"R14.16 status row count={continuity.count(old_row)}")
continuity = continuity.replace(old_row, new_row)

old_next = "Start R14.16 from exact normalized `main` `1f10d7a13f49cb6e931e5e0694f083228ed24070`: create its dedicated branch, perform the mandatory START-sync with R14.1–R14.15 COMPLETE + NORMALIZED, R14.16 IN_PROGRESS and R14.17 PLANNED, then implement and gate R14.16 according to `docs/roadmap/R14_PLAN.md`. R14.17 remains PLANNED and unauthorized until R14.16 completes and normalizes."
start_authority = f"""## R14.16 START authority

- Dedicated branch: `{BRANCH}`.
- Effective exact branch point: current `main` `{BASE_MAIN}`. The unique R14.15 normalized anchor remains `{NORMALIZED_ANCHOR}`; PR #287 / merge `{BASE_MAIN}` is a continuity-only erratum layered after normalization and does not alter normalization cardinality.
- START state: R14.1–R14.15 **COMPLETE + NORMALIZED**; R14.16 **IN_PROGRESS**; R14.17 **PLANNED**.
- Scope: structured CLI + KodeStudio Backend/LiveOps workflows over existing R14 domain APIs, including local stack status/control, migration preview/apply, provider capability/status, lobby/save/progression inspection, entitlement reconciliation preview, flags/config/content/campaign preview and governed rollout/rollback, event replay preview, health/load/backup reporting.
- Safety: UI/CLI never become an alternate authority path; environment + authority are visible; raw shell, raw secrets, arbitrary endpoint/command input and automatic production publish remain forbidden; mutation paths preserve existing permission/confirmation/SafeChange gates; inspect/preview/dry-run is the default where required.
- Acceptance posture: stable redacted CLI JSON, UI smoke, accessibility/localization regression, forbidden-input tests and fresh exact-head R0/Python/UI. Manual intervention: **NONE**.

## Next authorized action

Implement R14.16 only on `{BRANCH}` after this START-sync, preserving the frozen scope above. Freeze an immutable technical source before decision evidence, run focused/adversarial tests plus fresh exact-head gates, and do not authorize R14.17 until R14.16 implementation/END-sync/merge and its unique continuity-only normalization are complete."
if continuity.count(old_next) != 1:
    raise SystemExit(f"next action count={continuity.count(old_next)}")
continuity = continuity.replace("## Next authorized action\n\n" + old_next, start_authority)

for stale in [
    "R14.16–R14.17 remain PLANNED",
    "| R14.16 | PLANNED | NONE |",
    "Start R14.16 from exact normalized `main`",
]:
    if stale in continuity:
        raise SystemExit(f"stale continuity marker survives: {stale}")

if plan.count(f"Dedicated branch: `{BRANCH}`") != 1:
    raise SystemExit("R14.16 plan START authority not unique")
if continuity.count(f"Dedicated branch: `{BRANCH}`") != 1:
    raise SystemExit("R14.16 continuity START authority not unique")

plan_path.write_text(plan, encoding="utf-8", newline="\n")
continuity_path.write_text(continuity, encoding="utf-8", newline="\n")
