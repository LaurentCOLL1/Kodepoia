from pathlib import Path

PLAN = Path("docs/roadmap/R14_PLAN.md")
CONT = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

plan = PLAN.read_text(encoding="utf-8")
old_status = "**Status:** PLANNING  "
new_status = "**Status:** IN PROGRESS"
if plan.count(old_status) != 1:
    raise SystemExit(f"expected exactly one phase status marker, got {plan.count(old_status)}")
plan = plan.replace(old_status, new_status, 1)

old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED. R14 planning is active on `r14/00-phase-plan`. No R14.1 implementation may begin until this exhaustive plan is accepted, merged, then followed by exactly one continuity-only planning normalization that passes fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merges."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED. R14 planning is ACCEPTED + NORMALIZED on `main` `27af7b80072678f509f7092cf2759683efe1224f` after planning PR #255 and planning-normalization PR #256. R14.1 is IN_PROGRESS on dedicated branch `r14/01-backend-contracts-boundaries`, created exactly from that normalized main; R14.2–R14.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit(f"expected exactly one execution checkpoint, got {plan.count(old_checkpoint)}")
plan = plan.replace(old_checkpoint, new_checkpoint, 1)

old_row = "| R14.1 | Backend contracts, identities, capability model + secure network/runtime boundaries | PLANNED | NONE | R13 COMPLETE + normalized R14 planning |"
new_row = "| R14.1 | Backend contracts, identities, capability model + secure network/runtime boundaries | IN_PROGRESS | NONE | R13 COMPLETE + normalized R14 planning |"
if plan.count(old_row) != 1:
    raise SystemExit(f"expected exactly one R14.1 index row, got {plan.count(old_row)}")
plan = plan.replace(old_row, new_row, 1)
PLAN.write_text(plan, encoding="utf-8", newline="\n")

cont = CONT.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED / NORMALIZATION IN_PROGRESS on `r14/00-planning-continuity-normalization`; R14.1 has not started.** The exhaustive planning head `343b7834d8b5826d5012bf78926102725b66db7f` changed only `docs/roadmap/R14_PLAN.md` and continuity from normalized R13 main, and passed fresh exact-head R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and KodeStudio UI Smoke #1689 / `33136015584`, all SUCCESS. Planning PR #255 merged with expected-head protection as `808e5215e45a3a90d3037efb1a3749f01b285b9c`. The single allowed planning continuity normalization branch starts exactly from that merge and must change only `docs/continuity/KODEPOIA_CONTINUITY.md`, pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke, then merge with expected-head protection. Only the resulting normalized main makes R14 planning ACCEPTED + NORMALIZED and authorizes R14.1 on its own dedicated branch. Frozen R14 scope remains Backend / Platform Services / LiveOps with R14.1–R14.17 fixed by `R14_PLAN.md`."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 IN_PROGRESS on `r14/01-backend-contracts-boundaries`; R14.2–R14.17 remain PLANNED.** Exhaustive planning head `343b7834d8b5826d5012bf78926102725b66db7f` passed fresh R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; planning PR #255 merged as `808e5215e45a3a90d3037efb1a3749f01b285b9c`. Planning-normalization head `150f7f8a127a068eb79f479d0354d25ee1262c64` changed exactly continuity and passed fresh R0 #1750 / `33136198257`, Python Core #1724 / `33136198229`, and UI #1691 / `33136198210`; PR #256 merged with exact-head protection as normalized `main` `27af7b80072678f509f7092cf2759683efe1224f`. R14.1 branch starts exactly from that main. Manual state for R14.1 is NONE."
if cont.count(old_prompt) != 1:
    raise SystemExit(f"expected exactly one continuity prompt marker, got {cont.count(old_prompt)}")
cont = cont.replace(old_prompt, new_prompt, 1)

old_global = "- R14 planning: **ACCEPTED / NORMALIZATION IN_PROGRESS**. Exhaustive head **`343b7834d8b5826d5012bf78926102725b66db7f`** passed R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; PR #255 merged as **`808e5215e45a3a90d3037efb1a3749f01b285b9c`**. Single continuity-only planning normalization is active on `r14/00-planning-continuity-normalization`; R14.1 remains forbidden until it passes fresh gates and merges."
new_global = "- R14 planning: **ACCEPTED + NORMALIZED**. Exhaustive head **`343b7834d8b5826d5012bf78926102725b66db7f`** passed R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; PR #255 merged as **`808e5215e45a3a90d3037efb1a3749f01b285b9c`**. Planning-normalization head **`150f7f8a127a068eb79f479d0354d25ee1262c64`** passed R0 #1750 / `33136198257`, Python Core #1724 / `33136198229`, and UI #1691 / `33136198210`; PR #256 merged as normalized **`main` `27af7b80072678f509f7092cf2759683efe1224f`**. R14.1 is **IN_PROGRESS** on `r14/01-backend-contracts-boundaries`; R14.2–R14.17 remain PLANNED."
if cont.count(old_global) != 1:
    raise SystemExit(f"expected exactly one R14 global marker, got {cont.count(old_global)}")
cont = cont.replace(old_global, new_global, 1)

anchor = "## R12 final closure authority"
start_section = "## R14 planning closure and R14.1 start authority\n\n- Planning candidate `343b7834d8b5826d5012bf78926102725b66db7f` passed R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; PR #255 merged as `808e5215e45a3a90d3037efb1a3749f01b285b9c`.\n- Single planning-normalization candidate `150f7f8a127a068eb79f479d0354d25ee1262c64` changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1750 / `33136198257`, Python Core #1724 / `33136198229`, and UI #1691 / `33136198210`; PR #256 merged with expected-head protection as normalized main `27af7b80072678f509f7092cf2759683efe1224f`.\n- Therefore R14 planning is authoritatively **ACCEPTED + NORMALIZED**.\n- R14.1 dedicated branch `r14/01-backend-contracts-boundaries` starts exactly from `27af7b80072678f509f7092cf2759683efe1224f`; R14.1 is **IN_PROGRESS**, R14.2–R14.17 remain **PLANNED**, and manual intervention is **NONE**.\n- Frozen R14.1 scope: provider-neutral backend contracts/identities/capability snapshots, environment and endpoint semantics, secure network/runtime boundaries, canonical/redacted evidence and adversarial SSRF protections only; no concrete auth/DB/billing/flags/content/events implementation yet.\n\n"
if anchor not in cont:
    raise SystemExit("continuity insertion anchor missing")
if "## R14 planning closure and R14.1 start authority" in cont:
    raise SystemExit("R14 planning closure section already present")
cont = cont.replace(anchor, start_section + anchor, 1)
CONT.write_text(cont, encoding="utf-8", newline="\n")
