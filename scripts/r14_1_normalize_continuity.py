from pathlib import Path

CONT = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = CONT.read_text(encoding="utf-8")

TECH = "84972d283f6f530ae46ebf6c0452188927b178ff"
END = "75e5d68752a56b8a21fa4842e803d86f772f7468"
MERGE = "6059b6d706d1208fdcad102c9fa217abaf31d099"

old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE at technical/evidence level on `r14/01-backend-contracts-boundaries`; final exact-head documentation re-gates and PR #257 merge remain pending. R14.2–R14.17 remain PLANNED.** R14.1 accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 Repository Guard #1752 / `33140670364`, Python Core #1726 / `33140670445`, and KodeStudio UI Smoke #1693 / `33140670391`, all SUCCESS; Ubuntu full suite recorded 1445 passed / 13 skipped and Windows Core also passed. No technical semantics may change during END-sync. After final fresh R0 + Python Core + UI Smoke on the END-synchronized head, merge PR #257 with expected-head protection, then perform exactly one continuity-only post-merge normalization before R14.1 becomes COMPLETE + NORMALIZED and R14.2 is authorized. Manual state is NONE."
new_prompt = f"> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1 COMPLETE + NORMALIZED when this single continuity-only normalization PR merges; R14.2–R14.17 remain PLANNED.** R14.1 accepted immutable technical source `{TECH}` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`, all SUCCESS. Final END-synchronized head `{END}` changed only plan/acceptance/continuity relative to the technical source and passed fresh R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`, all SUCCESS. PR #257 merged with exact-head protection as `{MERGE}`. This branch `r14/01-continuity-normalization` is the single authorized post-merge continuity-only normalization; its COMPLETE + NORMALIZED authority becomes effective only after this exact continuity-only candidate passes fresh R0 + full Python Core + KodeStudio UI Smoke and its PR merges with expected-head protection. R14.2 may start only from the resulting normalized main. Manual state is NONE."
if text.count(old_prompt) != 1:
    raise SystemExit(f"prompt marker count={text.count(old_prompt)}")
text = text.replace(old_prompt, new_prompt, 1)

old_global = "- R14 planning: **ACCEPTED + NORMALIZED**. Normalized planning `main` is **`27af7b80072678f509f7092cf2759683efe1224f`**. R14.1 accepted immutable technical source **`84972d283f6f530ae46ebf6c0452188927b178ff`** passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`, all SUCCESS. R14.1 is **COMPLETE / FINAL_DOCUMENTATION_REGATES_PENDING**; R14.2–R14.17 remain PLANNED."
new_global = f"- R14 planning: **ACCEPTED + NORMALIZED**. Normalized planning base is **`27af7b80072678f509f7092cf2759683efe1224f`**. R14.1 accepted technical source **`{TECH}`** and final END-head **`{END}`**; implementation/evidence PR #257 merged as **`{MERGE}`**. R14.1 is **COMPLETE / POST_MERGE_NORMALIZATION_IN_PROGRESS** on `r14/01-continuity-normalization`; R14.2–R14.17 remain PLANNED and R14.2 is forbidden until this single continuity-only normalization passes fresh gates and merges."
if text.count(old_global) != 1:
    raise SystemExit(f"global marker count={text.count(old_global)}")
text = text.replace(old_global, new_global, 1)

old_start = "- R14.1 dedicated branch `r14/01-backend-contracts-boundaries` starts exactly from `27af7b80072678f509f7092cf2759683efe1224f`; accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 Repository Guard #1752 / `33140670364`, Python Core #1726 / `33140670445`, and KodeStudio UI Smoke #1693 / `33140670391`, all SUCCESS. R14.1 is **COMPLETE / FINAL_DOCUMENTATION_REGATES_PENDING**, R14.2–R14.17 remain **PLANNED**, and manual intervention is **NONE**."
new_start = f"- R14.1 implementation branch `r14/01-backend-contracts-boundaries` started exactly from normalized planning main `27af7b80072678f509f7092cf2759683efe1224f`. Accepted immutable technical source `{TECH}` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`; final END-head `{END}` passed fresh R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`, all SUCCESS. PR #257 merged with expected-head protection as `{MERGE}`. The only remaining R14.1 authority step is this single continuity-only normalization; manual intervention remains **NONE**."
if text.count(old_start) != 1:
    raise SystemExit(f"start bullet marker count={text.count(old_start)}")
text = text.replace(old_start, new_start, 1)

anchor = "## R12 final closure authority"
section = f"## R14.1 post-merge normalization authority\n\n- Accepted immutable technical source: `{TECH}`.\n- Technical gates: R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, KodeStudio UI Smoke #1693 / `33140670391`, all SUCCESS.\n- Final END-synchronized documentation/evidence head: `{END}`; relative to the technical source only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_1_ACCEPTANCE.md`, and continuity changed.\n- Final fresh exact-head gates: R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, UI #1698 / `33140864338`, all SUCCESS.\n- Implementation/evidence PR #257 merged with `expected_head_sha={END}` as `{MERGE}`.\n- Single authorized normalization branch: `r14/01-continuity-normalization`, created exactly from `{MERGE}`. Its final cumulative diff MUST contain exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; no plan/code/schema/test/workflow bytes may remain changed.\n- This normalization candidate declares the resulting main state **R14.1 COMPLETE + NORMALIZED** and keeps R14.2 **PLANNED**. That declaration becomes authoritative only when this exact candidate passes fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and its PR merges with expected-head protection.\n- Manual intervention: **NONE**.\n\n"
if anchor not in text:
    raise SystemExit("normalization insertion anchor missing")
if "## R14.1 post-merge normalization authority" in text:
    raise SystemExit("normalization authority already present")
text = text.replace(anchor, section + anchor, 1)

CONT.write_text(text, encoding="utf-8", newline="\n")
