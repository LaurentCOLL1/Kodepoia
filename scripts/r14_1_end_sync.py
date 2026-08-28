from pathlib import Path

PLAN = Path("docs/roadmap/R14_PLAN.md")
CONT = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
ACCEPTANCE = Path("docs/roadmap/R14_1_ACCEPTANCE.md")

TECH = "84972d283f6f530ae46ebf6c0452188927b178ff"
R0 = "R0 Repository Guard #1752 / `33140670364`"
PY = "Python Core #1726 / `33140670445`"
UI = "KodeStudio UI Smoke #1693 / `33140670391`"

plan = PLAN.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED. R14 planning is ACCEPTED + NORMALIZED on `main` `27af7b80072678f509f7092cf2759683efe1224f` after planning PR #255 and planning-normalization PR #256. R14.1 is IN_PROGRESS on dedicated branch `r14/01-backend-contracts-boundaries`, created exactly from that normalized main; R14.2–R14.17 remain PLANNED."
new_checkpoint = f"**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED and R14 planning is ACCEPTED + NORMALIZED on `main` `27af7b80072678f509f7092cf2759683efe1224f`. R14.1 accepted immutable technical source `{TECH}` passed {R0}, {PY}, and {UI}, all SUCCESS; Ubuntu full suite recorded 1445 passed / 13 skipped and Windows Core also passed. R14.1 is COMPLETE at technical/evidence level; final END-synchronized documentation head must pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before PR #257 may merge. R14.2–R14.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit(f"expected one R14 checkpoint, got {plan.count(old_checkpoint)}")
plan = plan.replace(old_checkpoint, new_checkpoint, 1)
old_row = "| R14.1 | Backend contracts, identities, capability model + secure network/runtime boundaries | IN_PROGRESS | NONE | R13 COMPLETE + normalized R14 planning |"
new_row = "| R14.1 | Backend contracts, identities, capability model + secure network/runtime boundaries | COMPLETE | NONE | R13 COMPLETE + normalized R14 planning |"
if plan.count(old_row) != 1:
    raise SystemExit(f"expected one R14.1 row, got {plan.count(old_row)}")
plan = plan.replace(old_row, new_row, 1)
completion_marker = "## Completion record\n\nTo be appended when accepted.\n\n---\n\n# R14.2"
completion = f"## Completion record\n\n- Accepted immutable technical head: `{TECH}`.\n- Technical exact-head gates: {R0} SUCCESS; {PY} SUCCESS; {UI} SUCCESS.\n- Ubuntu full Python suite: 1445 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS.\n- Manual intervention: NONE.\n- Final END-synchronized documentation/evidence re-gates and implementation PR #257 merge remain pending.\n- Current subdivision status: `COMPLETE` at technical/evidence level, not `COMPLETE + NORMALIZED` until post-merge continuity normalization.\n\n---\n\n# R14.2"
if plan.count(completion_marker) != 1:
    raise SystemExit(f"expected one R14.1 completion marker, got {plan.count(completion_marker)}")
plan = plan.replace(completion_marker, completion, 1)
PLAN.write_text(plan, encoding="utf-8", newline="\n")

acc = ACCEPTANCE.read_text(encoding="utf-8")
if acc.count("**Status: TECHNICAL_CANDIDATE_PENDING**") != 1:
    raise SystemExit("acceptance status marker missing")
acc = acc.replace("**Status: TECHNICAL_CANDIDATE_PENDING**", "**Status: TECHNICAL_CANDIDATE_ACCEPTED / FINAL_REGATES_PENDING**", 1)
pending = "No R14.1 technical candidate is accepted until all required exact-head gates below are COMPLETED / SUCCESS on the same immutable implementation head."
accepted = f"Accepted immutable technical candidate `{TECH}` passed all required exact-head technical gates: {R0}, {PY}, and {UI}, all COMPLETED / SUCCESS. Ubuntu full Python Core recorded 1445 passed, 13 skipped and 46 warnings; Windows Core also completed SUCCESS. This technical authority is immutable; later END-sync documentation commits must not alter accepted implementation semantics."
if acc.count(pending) != 1:
    raise SystemExit("acceptance pending statement missing")
acc = acc.replace(pending, accepted, 1)
old_gates = "1. R0 Repository Guard — PENDING.\n2. Full Python Core — PENDING, including Ubuntu/Windows core tests, package builds and internal KodeStudio smoke.\n3. KodeStudio UI Smoke — PENDING."
new_gates = f"1. {R0} — COMPLETED / SUCCESS.\n2. {PY} — COMPLETED / SUCCESS, including Ubuntu/Windows core tests, both package builds and internal KodeStudio smoke.\n3. {UI} — COMPLETED / SUCCESS."
if acc.count(old_gates) != 1:
    raise SystemExit("acceptance gate block missing")
acc = acc.replace(old_gates, new_gates, 1)
append_anchor = "## End synchronization and final gates"
record = f"## Accepted technical candidate record\n\n- Immutable source SHA: `{TECH}`.\n- {R0}: SUCCESS.\n- {PY}: SUCCESS; Ubuntu `pytest` = **1445 passed, 13 skipped, 46 warnings**; Windows Core test step = SUCCESS; both package builds and Python internal UI smoke = SUCCESS.\n- {UI}: SUCCESS.\n- Rejected predecessor technical candidates: NONE. The earlier START-sync workflow failure occurred before implementation and was solely a Markdown trailing-whitespace guard failure; it is not technical acceptance evidence.\n- Manual intervention: NONE.\n- Next authority: END-synchronized documentation/evidence head with fresh exact-head R0/Python/UI.\n\n"
if append_anchor not in acc or "## Accepted technical candidate record" in acc:
    raise SystemExit("acceptance record insertion state invalid")
acc = acc.replace(append_anchor, record + append_anchor, 1)
ACCEPTANCE.write_text(acc, encoding="utf-8", newline="\n")

cont = CONT.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 IN_PROGRESS on `r14/01-backend-contracts-boundaries`; R14.2–R14.17 remain PLANNED.** Exhaustive planning head `343b7834d8b5826d5012bf78926102725b66db7f` passed fresh R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; planning PR #255 merged as `808e5215e45a3a90d3037efb1a3749f01b285b9c`. Planning-normalization head `150f7f8a127a068eb79f479d0354d25ee1262c64` changed exactly continuity and passed fresh R0 #1750 / `33136198257`, Python Core #1724 / `33136198229`, and UI #1691 / `33136198210`; PR #256 merged with exact-head protection as normalized `main` `27af7b80072678f509f7092cf2759683efe1224f`. R14.1 branch starts exactly from that main. Manual state for R14.1 is NONE."
new_prompt = f"> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE at technical/evidence level on `r14/01-backend-contracts-boundaries`; final exact-head documentation re-gates and PR #257 merge remain pending. R14.2–R14.17 remain PLANNED.** R14.1 accepted immutable technical source `{TECH}` passed {R0}, {PY}, and {UI}, all SUCCESS; Ubuntu full suite recorded 1445 passed / 13 skipped and Windows Core also passed. No technical semantics may change during END-sync. After final fresh R0 + Python Core + UI Smoke on the END-synchronized head, merge PR #257 with expected-head protection, then perform exactly one continuity-only post-merge normalization before R14.1 becomes COMPLETE + NORMALIZED and R14.2 is authorized. Manual state is NONE."
if cont.count(old_prompt) != 1:
    raise SystemExit(f"continuity prompt marker count={cont.count(old_prompt)}")
cont = cont.replace(old_prompt, new_prompt, 1)
old_global = "- R14 planning: **ACCEPTED + NORMALIZED**. Exhaustive head **`343b7834d8b5826d5012bf78926102725b66db7f`** passed R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; PR #255 merged as **`808e5215e45a3a90d3037efb1a3749f01b285b9c`**. Planning-normalization head **`150f7f8a127a068eb79f479d0354d25ee1262c64`** passed R0 #1750 / `33136198257`, Python Core #1724 / `33136198229`, and UI #1691 / `33136198210`; PR #256 merged as normalized **`main` `27af7b80072678f509f7092cf2759683efe1224f`**. R14.1 is **IN_PROGRESS** on `r14/01-backend-contracts-boundaries`; R14.2–R14.17 remain PLANNED."
new_global = f"- R14 planning: **ACCEPTED + NORMALIZED**. Normalized planning `main` is **`27af7b80072678f509f7092cf2759683efe1224f`**. R14.1 accepted immutable technical source **`{TECH}`** passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`, all SUCCESS. R14.1 is **COMPLETE / FINAL_DOCUMENTATION_REGATES_PENDING**; R14.2–R14.17 remain PLANNED."
if cont.count(old_global) != 1:
    raise SystemExit(f"continuity global marker count={cont.count(old_global)}")
cont = cont.replace(old_global, new_global, 1)
old_start = "- R14.1 dedicated branch `r14/01-backend-contracts-boundaries` starts exactly from `27af7b80072678f509f7092cf2759683efe1224f`; R14.1 is **IN_PROGRESS**, R14.2–R14.17 remain **PLANNED**, and manual intervention is **NONE**."
new_start = f"- R14.1 dedicated branch `r14/01-backend-contracts-boundaries` starts exactly from `27af7b80072678f509f7092cf2759683efe1224f`; accepted immutable technical source `{TECH}` passed {R0}, {PY}, and {UI}, all SUCCESS. R14.1 is **COMPLETE / FINAL_DOCUMENTATION_REGATES_PENDING**, R14.2–R14.17 remain **PLANNED**, and manual intervention is **NONE**."
if cont.count(old_start) != 1:
    raise SystemExit(f"continuity start bullet count={cont.count(old_start)}")
cont = cont.replace(old_start, new_start, 1)
CONT.write_text(cont, encoding="utf-8", newline="\n")
