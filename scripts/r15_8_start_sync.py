from __future__ import annotations

from pathlib import Path

PLAN = Path("docs/roadmap/R15_PLAN.md")
CONT = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

plan_lines = PLAN.read_text(encoding="utf-8").splitlines()
cont_lines = CONT.read_text(encoding="utf-8").splitlines()

checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.7 are COMPLETE + NORMALIZED. R15.7 normalization head `d07ca7b2ab550e0fcaf09897d51d72b2dd94d590` passed R0 #2140 / `33300956787` SUCCESS Ubuntu + Windows, Python Core #2115 / `33300956780` SUCCESS 5/5 and KodeStudio UI Smoke #2080 / `33300956762` SUCCESS; normalization PR #310 merged with exact expected head as normalized `main` `5de1cabd3e861e75204595de1819564c782a217d`. R15.8 is IN_PROGRESS; R15.9–R15.17 remain PLANNED."

matches = [i for i, line in enumerate(plan_lines) if line.startswith("**Execution checkpoint:**")]
if len(matches) != 1:
    raise SystemExit(f"expected one execution checkpoint, found {len(matches)}")
plan_lines[matches[0]] = checkpoint

for rid, status in (("R15.7", "COMPLETE + NORMALIZED"), ("R15.8", "IN_PROGRESS")):
    matches = [i for i, line in enumerate(plan_lines) if line.startswith(f"| {rid} |")]
    if len(matches) != 1:
        raise SystemExit(f"expected one plan row for {rid}, found {len(matches)}")
    manual = "NONE" if rid == "R15.7" else "CONDITIONAL"
    plan_lines[matches[0]] = f"| {rid} | {status} | {manual} |" + (" R15.5–R15.6 + R3/R4/R7 |" if rid == "R15.7" else " R15.7 + R1/R6/R9 |")

r157_start = next(i for i, line in enumerate(plan_lines) if line.startswith("# R15.7 —"))
r158_start = next(i for i, line in enumerate(plan_lines) if line.startswith("# R15.8 —"))
record = next(i for i in range(r157_start, r158_start) if plan_lines[i] == "## Completion record")
insert = record + 1
while insert < r158_start and not plan_lines[insert].strip():
    insert += 1
normalization_line = "- Post-merge normalization head `d07ca7b2ab550e0fcaf09897d51d72b2dd94d590`: R0 #2140 / `33300956787`, Python Core #2115 / `33300956780` (5/5), UI #2080 / `33300956762` SUCCESS; PR #310 merged with exact expected head as normalized `main` `5de1cabd3e861e75204595de1819564c782a217d`. R15.7 is COMPLETE + NORMALIZED; manual NONE."
if normalization_line not in plan_lines[record:r158_start]:
    plan_lines.insert(insert, normalization_line)

PLAN.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

header = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.7 COMPLETE + NORMALIZED; R15.8 IN_PROGRESS; R15.9–R15.17 PLANNED.** R15.7 normalization head `d07ca7b2ab550e0fcaf09897d51d72b2dd94d590` passed R0 #2140 / `33300956787`, Python Core #2115 / `33300956780` 5/5 and UI #2080 / `33300956762` SUCCESS; PR #310 merged with exact expected head as normalized `main` `5de1cabd3e861e75204595de1819564c782a217d`. R15.8 START-sync is active from that exact normalized main. Manual state R15.8: CONDITIONAL / NOT TRIGGERED for core fixture/CI acceptance."
if not cont_lines or not cont_lines[0].startswith("> Kodepoia, architecture v1.0 gelée."):
    raise SystemExit("unexpected continuity header")
cont_lines[0] = header

r157 = [i for i, line in enumerate(cont_lines) if line.startswith("- R15.7 :")]
if len(r157) != 1:
    raise SystemExit(f"expected one R15.7 continuity entry, found {len(r157)}")
cont_lines[r157[0]] = "- R15.7 : **COMPLETE + NORMALIZED** — clean START `9ef6f704d54332203e820cd2bd85e3b4ac86910a`; immutable technical source `a9a967289bbede1ffd155567f3caaa201d1af772`; final sealed END-head `01dd690161305c73630677c3c3ca38b6cd85bbd9` passed R15.7 #9 / `33300637528`, R0 #2138 / `33300637472`, Python Core #2113 / `33300637478` 5/5 and UI #2078 / `33300637477` SUCCESS; PR #309 merged exact head as `c30d4295ab01230f59fbca561fcfd69e576ccb3f`; unique normalization head `d07ca7b2ab550e0fcaf09897d51d72b2dd94d590` passed R0 #2140 / `33300956787`, Python Core #2115 / `33300956780` 5/5 and UI #2080 / `33300956762` SUCCESS; normalization PR #310 merged exact head as normalized `main` `5de1cabd3e861e75204595de1819564c782a217d`; manual NONE."

r158_entry = "- R15.8 : **IN_PROGRESS** — clean START / exact normalized R15.7 base `5de1cabd3e861e75204595de1819564c782a217d`; scope is optional training runtime, backend capability probes, dependency isolation and reproducibility. Core acceptance must work without heavy ML extras and uses fake/isolated capabilities; real local GPU/backend qualification remains CONDITIONAL and is NOT TRIGGERED unless explicitly required."
if not any(line.startswith("- R15.8 :") for line in cont_lines):
    cont_lines.insert(r157[0] + 1, r158_entry)
else:
    idx = next(i for i, line in enumerate(cont_lines) if line.startswith("- R15.8 :"))
    cont_lines[idx] = r158_entry

for rid, status, manual in (("R15.7", "COMPLETE + NORMALIZED", "NONE"), ("R15.8", "IN_PROGRESS", "CONDITIONAL")):
    matches = [i for i, line in enumerate(cont_lines) if line.startswith(f"| {rid} |")]
    if len(matches) != 1:
        raise SystemExit(f"expected one continuity row for {rid}, found {len(matches)}")
    cont_lines[matches[0]] = f"| {rid} | {status} | {manual} |"

headings = [i for i, line in enumerate(cont_lines) if line == "## Next authorized action"]
if not headings:
    raise SystemExit("missing Next authorized action")
i = headings[0] + 1
while i < len(cont_lines) and not cont_lines[i].strip():
    i += 1
cont_lines[i] = "**R15.8 START-sync is authorized from normalized `main` `5de1cabd3e861e75204595de1819564c782a217d` and is now active. Implement only the frozen optional training-runtime/capability-probe scope, preserve the core install without heavy ML extras, and use isolated/fake capability acceptance. If authoritative acceptance of a specific real local GPU/backend becomes required, stop before later subdivisions and request only the bounded user-side capability JSON.**"

CONT.write_text("\n".join(cont_lines) + "\n", encoding="utf-8")
