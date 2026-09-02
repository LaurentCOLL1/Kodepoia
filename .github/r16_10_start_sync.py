from pathlib import Path

base = "3957a30053da791facb2de7fbbbb0614d0fa03d6"
branch = "r16/10-representative-godot-2d-beta-project"

plan_path = Path("docs/roadmap/R16_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.8 are COMPLETE + NORMALIZED. R16.9 is COMPLETE on immutable technical source `026ddc91672c144977453c9852a5288e9533af22` with fresh technical acceptance recorded below; post-merge continuity normalization is still required before R16.10. R16.10–R16.18 remain PLANNED."
new_checkpoint = f"**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.9 are COMPLETE + NORMALIZED. R16.10 is IN_PROGRESS from normalized `main` `{base}` on dedicated branch `{branch}`; R16.11–R16.18 remain PLANNED."
assert plan.count(old_checkpoint) == 1
plan = plan.replace(old_checkpoint, new_checkpoint, 1)

old_r9 = "| R16.9 | Dependency/workflow/release supply-chain provenance hardening | COMPLETE | NONE |"
new_r9 = "| R16.9 | Dependency/workflow/release supply-chain provenance hardening | COMPLETE + NORMALIZED | NONE |"
assert plan.count(old_r9) == 1
plan = plan.replace(old_r9, new_r9, 1)
old_r10 = "| R16.10 | Representative real Godot 2D beta project | PLANNED | NONE |"
new_r10 = "| R16.10 | Representative real Godot 2D beta project | IN_PROGRESS | NONE |"
assert plan.count(old_r10) == 1
plan = plan.replace(old_r10, new_r10, 1)
plan_path.write_text(plan, encoding="utf-8", newline="\n")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
old_top = "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.9 COMPLETE + NORMALIZED. R16.10–R16.18 remain PLANNED.** R16.9 immutable technical source `026ddc91672c144977453c9852a5288e9533af22`; final exact-END head `910e4d166782cc570b98f60470a13be48896a116` passed fresh R16.9 #16 / `33586184972` Ubuntu + Windows, R0 #2324 / `33586185066` Ubuntu + Windows, Python Core #2296 / `33586184754` 5/5 and KodeStudio UI Smoke #2261 / `33586184752`; implementation/evidence PR #351 merged exact expected head as `b81fe4248338ed5cabe6e3034f396cd11202ec39`. This continuity record is the unique post-merge R16.9 normalization authority and becomes authoritative only after its own fresh exact-head R0/Python/UI gates and exact-head normalization merge. R16.10 is authorized only from the resulting normalized `main`. Manual NONE."
new_top = f"> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.9 COMPLETE + NORMALIZED. R16.10 IN_PROGRESS on `{branch}` from normalized `main` `{base}`; R16.11–R16.18 remain PLANNED.** R16.9 immutable technical source `026ddc91672c144977453c9852a5288e9533af22`; final exact-END head `910e4d166782cc570b98f60470a13be48896a116` passed R16.9 #16 / `33586184972`, R0 #2324 / `33586185066`, Python Core #2296 / `33586184754` 5/5 and UI #2261 / `33586184752`; PR #351 merged as `b81fe4248338ed5cabe6e3034f396cd11202ec39`; unique normalization head `661d16e97f5c5d348db0c98e3885420b1b40de14` passed R0 #2326 / `33587183979`, Python Core #2298 / `33587184006` 5/5 and UI #2263 / `33587184031`, then PR #352 merged exact head as normalized `main` `{base}`. R16.10 START is synchronized before implementation; manual NONE."
assert cont.count(old_top) == 1
cont = cont.replace(old_top, new_top, 1)

old_norm_a = "- This is the single authorized post-merge normalization for R16.9. It becomes authoritative only after fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke all succeed and the normalization PR merges with exact expected-head protection."
new_norm_a = f"- This is the single authorized post-merge normalization for R16.9: candidate `661d16e97f5c5d348db0c98e3885420b1b40de14` passed R0 #2326 / `33587183979` Ubuntu + Windows, Python Core #2298 / `33587184006` 5/5 and KodeStudio UI Smoke #2263 / `33587184031`, then PR #352 merged with exact expected-head protection as normalized `main` `{base}`."
assert cont.count(old_norm_a) == 1
cont = cont.replace(old_norm_a, new_norm_a, 1)
old_norm_b = "- Manual state remains **NONE**. R16.10 remains PLANNED until that normalized `main` exists."
new_norm_b = f"- Manual state remains **NONE**. R16.10 START is authorized only from normalized `main` `{base}` and is now synchronized on `{branch}` before implementation."
assert cont.count(old_norm_b) == 1
cont = cont.replace(old_norm_b, new_norm_b, 1)

old_index = "| R16.10 | PLANNED | NONE |"
new_index = "| R16.10 | IN_PROGRESS | NONE |"
assert cont.count(old_index) == 1
cont = cont.replace(old_index, new_index, 1)

old_next = "Complete this **unique R16.9 continuity-only normalization** from implementation/evidence `main` `b81fe4248338ed5cabe6e3034f396cd11202ec39`: its final tree must change only `docs/continuity/KODEPOIA_CONTINUITY.md`, pass fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke, then merge with exact `expected_head_sha`. Only the resulting normalized `main` authorizes **R16.10 — Representative real Godot 2D beta project**; R16.10 must begin with its own dedicated branch and START-sync before implementation."
new_next = f"Implement and accept **R16.10 — Representative real Godot 2D beta project** on `{branch}` from exact normalized `main` `{base}`. Use a bounded repository-owned real Godot 2D project; exercise public KodeGodot create/open/analyze/edit/validate/run-or-headless-check paths, multi-file SafeChange/rollback, deterministic project/diff/diagnostic evidence, benign untrusted project text and a malicious non-executing negative control. Godot engine availability is capability-probed and any live claim must record executable/version/invocation. Manual NONE. Freeze one immutable technical source, run focused Ubuntu/Windows acceptance plus fresh R0/Python/UI, END-sync and re-gate any changed END head before exact-head merge and the unique continuity-only post-merge normalization."
assert cont.count(old_next) == 1
cont = cont.replace(old_next, new_next, 1)

marker = "\n## R16 status index\n"
assert cont.count(marker) == 1
start_record = f'''\n## R16.10 START authority\n\n- Dedicated branch: `{branch}`.\n- Exact normalized branch point: `main` `{base}` after unique R16.9 continuity normalization PR #352.\n- State at START: R1–R15 COMPLETE + NORMALIZED; R16 planning ACCEPTED + NORMALIZED; R16.1–R16.9 COMPLETE + NORMALIZED; R16.10 IN_PROGRESS; R16.11–R16.18 PLANNED.\n- Frozen scope: representative repository-owned Godot 2D beta project; deterministic assets/scenes/scripts and provenance; public KodeGodot create/open/analyze/edit/validate/run-or-supported-headless paths; realistic multi-file change with SafeChange/rollback; benign untrusted project instructions retained as data; malicious negative-control text denied execution authority; project/diff/diagnostic/recovery digests; capability-probed Godot executable/version/invocation when available.\n- Core acceptance remains CI-owned and cross-platform; no external project, live secret, network dependency or destructive host action is required. Godot executable absence is recorded truthfully rather than inferred as PASS.\n- Manual state: **NONE**.\n- No R16.10 implementation preceded this START-sync.\n'''
cont = cont.replace(marker, start_record + marker, 1)
cont_path.write_text(cont, encoding="utf-8", newline="\n")
