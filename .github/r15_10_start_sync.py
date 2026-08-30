from pathlib import Path

BASE = 'ba37dbc46393ca64d565ee1122fe545cc1b48c2d'

plan = Path('docs/roadmap/R15_PLAN.md')
text = plan.read_text(encoding='utf-8')
old = '**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.8 are COMPLETE + NORMALIZED. R15.9 is COMPLETE with immutable technical source `a964bff54886cafe640fb583610e81055fbe3907`; its final documented END-head requires fresh exact-head R15.9/R0/Python/UI gates before protected merge. R15.10–R15.17 remain PLANNED.'
new = '**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.9 are COMPLETE + NORMALIZED. R15.10 is IN_PROGRESS from normalized `main` `ba37dbc46393ca64d565ee1122fe545cc1b48c2d`; R15.11–R15.17 remain PLANNED.'
if text.count(old) != 1:
    raise SystemExit('R15 plan START checkpoint marker mismatch')
plan.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')

continuity = Path('docs/continuity/KODEPOIA_CONTINUITY.md')
text = continuity.read_text(encoding='utf-8')
lines = text.splitlines()
old_first = '> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.9 COMPLETE + NORMALIZED; R15.10–R15.17 PLANNED.** R15.9 implementation/evidence PR #313 merged exact final END-head `48ce6b547807eb81cbcd0885f0f8100b54b0f5f3` as `265c92fe0c9827be55dfde9b439dd29d309eecbc`; this continuity-only branch is the unique post-merge R15.9 normalization authority when merged. R15.10 START is authorized only after fresh exact-head R0/Python/UI succeed here and this normalization merges to `main`. Manual state R15.9: CONDITIONAL / NOT TRIGGERED; no real target-GPU/backend qualification is claimed.'
new_first = '> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.9 COMPLETE + NORMALIZED; R15.10 IN_PROGRESS; R15.11–R15.17 PLANNED.** R15.10 branch `r15/10-base-adapter-evaluation` starts from normalized `main` `ba37dbc46393ca64d565ee1122fe545cc1b48c2d`. Scope is base-vs-adapter KodeBench comparison with identical suite/config/repeats, deterministic critical-regression veto and governed `PROMOTE_TO_EXPORT` / `REJECT` / `INCONCLUSIVE` disposition. Manual state R15.10: NONE.'
if not lines or lines[0] != old_first:
    raise SystemExit('R15.10 continuity top marker mismatch')
lines[0] = new_first

if any(line.startswith('- R15.10 :') for line in lines):
    raise SystemExit('R15.10 continuity START record already exists')
index = next((i for i, line in enumerate(lines) if line.startswith('- R14.1–R14.9 : **COMPLETE + NORMALIZED**.')), None)
if index is None:
    raise SystemExit('continuity insertion marker not found')
record = '- R15.10 : **IN_PROGRESS** — clean START / normalized R15.9 base `ba37dbc46393ca64d565ee1122fe545cc1b48c2d`; dedicated branch `r15/10-base-adapter-evaluation`; compare only immutable base/candidate KodeBench runs with identical suite/config/repeats; mixed suite/base/config comparisons fail closed; any critical-domain regression is a hard veto; target-domain gains, error/resource deltas and repeated-run instability determine deterministic `PROMOTE_TO_EXPORT`, `REJECT` or `INCONCLUSIVE`; manual NONE. R15.11–R15.17 remain PLANNED and unauthorized.'
lines.insert(index, record)
continuity.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
