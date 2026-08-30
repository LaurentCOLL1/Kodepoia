from __future__ import annotations

from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = PATH.read_text(encoding="utf-8")
lines = text.splitlines()

header = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.7 COMPLETE + NORMALIZED; R15.8–R15.17 PLANNED.** R15.7 clean START `9ef6f704d54332203e820cd2bd85e3b4ac86910a`; START-sync `07593e95380df6fb43bda299b7de7295c614d17f`; immutable technical source `a9a967289bbede1ffd155567f3caaa201d1af772`; final sealed END-head `01dd690161305c73630677c3c3ca38b6cd85bbd9` passed R15.7 #9 / `33300637528` SUCCESS Ubuntu + Windows, R0 #2138 / `33300637472` SUCCESS Ubuntu + Windows, Python Core #2113 / `33300637478` SUCCESS 5/5 and UI #2078 / `33300637477` SUCCESS; PR #309 merged only with `expected_head_sha=01dd690161305c73630677c3c3ca38b6cd85bbd9` as `c30d4295ab01230f59fbca561fcfd69e576ccb3f`. This branch is the unique continuity-only R15.7 post-merge normalization candidate; only fresh exact-head R0/Python/UI SUCCESS and expected-head merge authorize R15.8. Manual NONE."

entry = "- R15.7 : **COMPLETE + NORMALIZED** — clean START / normalized R15.6 main `9ef6f704d54332203e820cd2bd85e3b4ac86910a`; START-sync `07593e95380df6fb43bda299b7de7295c614d17f` preceded implementation; immutable technical source `a9a967289bbede1ffd155567f3caaa201d1af772`; technical R15.7 #2 / `33299136312` SUCCESS Ubuntu + Windows, R0 #2134 / `33299136336` SUCCESS Ubuntu + Windows, Python Core #2109 / `33299136316` SUCCESS 5/5 and UI #2074 / `33299136461` SUCCESS; final sealed END-head `01dd690161305c73630677c3c3ca38b6cd85bbd9` passed fresh R15.7 #9 / `33300637528` SUCCESS Ubuntu + Windows, R0 #2138 / `33300637472` SUCCESS Ubuntu + Windows, Python Core #2113 / `33300637478` SUCCESS 5/5 and UI #2078 / `33300637477` SUCCESS; PR #309 merged with exact expected head as `c30d4295ab01230f59fbca561fcfd69e576ccb3f`; deterministic ordered gap-decision authority implements TRAIN/NO_TRAIN/FIX_SYSTEM_FIRST/INSUFFICIENT_DATA/UNSUPPORTED/LICENSE_BLOCKED/BUDGET_BLOCKED/INCONCLUSIVE, requires immutable benchmark/base/dataset evidence, diagnoses tool/retrieval/router/context before training, and executes no training. Manual NONE. This record is the unique post-merge continuity-only R15.7 normalization candidate; R15.8 START-sync is authorized only after fresh exact-head R0/Python/UI on this branch and expected-head merge to `main`."

row = "| R15.7 | COMPLETE + NORMALIZED | NONE |"
next_action = "**R15.7 implementation/evidence is merged as `c30d4295ab01230f59fbca561fcfd69e576ccb3f`. This branch is the unique continuity-only post-merge normalization: require fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, then merge only with `expected_head_sha`. Only the resulting normalized `main` authorizes R15.8 START-sync; `docs/roadmap/R15_PLAN.md` must not change. Manual NONE.**"

if not lines or not lines[0].startswith("> Kodepoia, architecture v1.0 gelée."):
    raise SystemExit("unexpected continuity header")
lines[0] = header

entry_matches = [i for i, line in enumerate(lines) if line.startswith("- R15.7 :")]
if len(entry_matches) != 1:
    raise SystemExit(f"expected one R15.7 global entry, found {len(entry_matches)}")
lines[entry_matches[0]] = entry

row_matches = [i for i, line in enumerate(lines) if line.startswith("| R15.7 |")]
if len(row_matches) != 1:
    raise SystemExit(f"expected one R15.7 status row, found {len(row_matches)}")
lines[row_matches[0]] = row

heading_matches = [i for i, line in enumerate(lines) if line == "## Next authorized action"]
if not heading_matches:
    raise SystemExit("missing Next authorized action heading")
# The first one is the active R15 authority section; later historical R14 sections are immutable.
heading = heading_matches[0]
next_index = heading + 1
while next_index < len(lines) and not lines[next_index].strip():
    next_index += 1
if next_index >= len(lines) or not lines[next_index].startswith("**R15.7"):
    raise SystemExit("unexpected active Next authorized action payload")
lines[next_index] = next_action

PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
