from pathlib import Path

BASE = "75e58ba578d6c5f654be1c3a8e35fae7f86cb72a"
BRANCH = "r16/11-representative-godot-3d-beta-project"
NORMALIZATION_HEAD = "0cd2ecf320b48c13bd81c662e328fee3373f38ee"

plan_path = Path("docs/roadmap/R16_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.9 are COMPLETE + NORMALIZED. R16.10 is COMPLETE on dedicated branch `r16/10-representative-godot-2d-beta-project` from normalized `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; R16.11–R16.18 remain PLANNED. R16.10 still requires fresh exact-END re-gates, exact-head merge, and the unique continuity-only post-merge normalization before R16.11 is authorized."
new_checkpoint = f"**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.10 are COMPLETE + NORMALIZED. R16.11 is IN_PROGRESS from normalized `main` `{BASE}` on dedicated branch `{BRANCH}`; R16.12–R16.18 remain PLANNED."
assert plan.count(old_checkpoint) == 1, "unexpected R16 plan checkpoint"
plan = plan.replace(old_checkpoint, new_checkpoint, 1)

old_r10 = "| R16.10 | Representative real Godot 2D beta project | COMPLETE | NONE |"
new_r10 = "| R16.10 | Representative real Godot 2D beta project | COMPLETE + NORMALIZED | NONE |"
assert plan.count(old_r10) == 1, "unexpected R16.10 plan status"
plan = plan.replace(old_r10, new_r10, 1)
old_r11 = "| R16.11 | Representative real Godot 3D beta project | PLANNED | NONE |"
new_r11 = "| R16.11 | Representative real Godot 3D beta project | IN_PROGRESS | NONE |"
assert plan.count(old_r11) == 1, "unexpected R16.11 plan status"
plan = plan.replace(old_r11, new_r11, 1)
plan_path.write_text(plan, encoding="utf-8", newline="\n")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
old_top = "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.10 COMPLETE + NORMALIZED. R16.11–R16.18 remain PLANNED.** R16.10 immutable technical source `499292dd553460bb48f3092112d5bcb81544242b`; final exact-END head `162abd7b9050bd9f9e35d0b2bf8049b1ed86984c` passed fresh R16.10 #27 / `33641853721` SUCCESS Ubuntu + Windows, R16.9 #26 / `33641853768` SUCCESS Ubuntu + Windows, R0 #2337 / `33641909778` attempt 2 SUCCESS Ubuntu + Windows, Python Core #2308 / `33641853756` SUCCESS 5/5 and KodeStudio UI Smoke #2273 / `33641853653` SUCCESS; implementation/evidence PR #353 merged with `expected_head_sha=162abd7b9050bd9f9e35d0b2bf8049b1ed86984c` as `main` `e6c11e986ad2e0ee5b1cdd50c0ae2061117ca974`. This continuity record is the unique post-merge R16.10 normalization authority and becomes authoritative only after its own fresh exact-head R0/Python/UI gates and exact-head normalization merge. R16.11 is authorized only from the resulting normalized `main`. Manual NONE."
new_top = f"> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.10 COMPLETE + NORMALIZED. R16.11 IN_PROGRESS on `{BRANCH}` from normalized `main` `{BASE}`; R16.12–R16.18 remain PLANNED.** R16.10 immutable technical source `499292dd553460bb48f3092112d5bcb81544242b`; final exact-END head `162abd7b9050bd9f9e35d0b2bf8049b1ed86984c` passed fresh R16.10 #27 / `33641853721`, R16.9 #26 / `33641853768`, R0 #2337 / `33641909778` attempt 2, Python Core #2308 / `33641853756` 5/5 and UI #2273 / `33641853653`; PR #353 merged as implementation/evidence `main` `e6c11e986ad2e0ee5b1cdd50c0ae2061117ca974`; unique normalization head `{NORMALIZATION_HEAD}` passed R0 #2339 / `33653846366` Ubuntu + Windows, Python Core #2311 / `33653846604` 5/5 and KodeStudio UI Smoke #2276 / `33653846942`, then PR #354 merged exact head as normalized `main` `{BASE}`. R16.11 START is synchronized before implementation; manual NONE."
assert cont.count(old_top) == 1, "unexpected continuity header"
cont = cont.replace(old_top, new_top, 1)

old_global = "- R16.10 : **COMPLETE + NORMALIZED** — normalized R16.9 `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; immutable technical source `499292dd553460bb48f3092112d5bcb81544242b`; technical R16.10 #20 / `33638816914` SUCCESS Ubuntu + Windows; final exact-END head `162abd7b9050bd9f9e35d0b2bf8049b1ed86984c` passed fresh R16.10 #27 / `33641853721` SUCCESS Ubuntu + Windows, R16.9 #26 / `33641853768` SUCCESS Ubuntu + Windows, R0 #2337 / `33641909778` attempt 2 SUCCESS Ubuntu + Windows, Python Core #2308 / `33641853756` SUCCESS 5/5 and UI #2273 / `33641853653` SUCCESS; PR #353 merged with exact expected head as implementation/evidence `main` `e6c11e986ad2e0ee5b1cdd50c0ae2061117ca974`. Acceptance remains 10/10 PASS per OS, `security_claim=true`, `critical_veto=false`, Godot `capability_absent` on hosted runners, zero network calls, no live credentials and no destructive host action. This record is the unique post-merge continuity-only R16.10 normalization authority when its exact candidate passes fresh R0/Python/UI and merges; manual NONE. R16.11 is authorized only from the resulting normalized `main`."
new_global = f"- R16.10 : **COMPLETE + NORMALIZED** — normalized R16.9 `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; immutable technical source `499292dd553460bb48f3092112d5bcb81544242b`; technical R16.10 #20 / `33638816914` SUCCESS Ubuntu + Windows; final exact-END head `162abd7b9050bd9f9e35d0b2bf8049b1ed86984c` passed fresh R16.10 #27 / `33641853721` SUCCESS Ubuntu + Windows, R16.9 #26 / `33641853768` SUCCESS Ubuntu + Windows, R0 #2337 / `33641909778` attempt 2 SUCCESS Ubuntu + Windows, Python Core #2308 / `33641853756` SUCCESS 5/5 and UI #2273 / `33641853653` SUCCESS; PR #353 merged with exact expected head as implementation/evidence `main` `e6c11e986ad2e0ee5b1cdd50c0ae2061117ca974`; normalization candidate `{NORMALIZATION_HEAD}` passed fresh R0 #2339 / `33653846366` Ubuntu + Windows, Python Core #2311 / `33653846604` SUCCESS 5/5 and UI #2276 / `33653846942` SUCCESS, then PR #354 merged exact expected head as normalized `main` `{BASE}`. Acceptance remains 10/10 PASS per OS, `security_claim=true`, `critical_veto=false`, Godot `capability_absent` on hosted runners, zero network calls, no live credentials and no destructive host action. Manual NONE. R16.11 START is authorized only from `{BASE}` and is now synchronized on `{BRANCH}` before implementation."
assert cont.count(old_global) == 1, "unexpected R16.10 global record"
cont = cont.replace(old_global, new_global, 1)

old_norm_a = "- This is the single authorized post-merge normalization for R16.10. This continuity record becomes authoritative only after its exact normalization candidate passes fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and the normalization PR merges with exact expected-head protection. No second R16.10 normalization is permitted."
new_norm_a = f"- This is the single authorized post-merge normalization for R16.10: candidate `{NORMALIZATION_HEAD}` passed fresh R0 #2339 / `33653846366` Ubuntu + Windows, Python Core #2311 / `33653846604` SUCCESS 5/5 and KodeStudio UI Smoke #2276 / `33653846942` SUCCESS, then PR #354 merged with exact expected-head protection as normalized `main` `{BASE}`. No second R16.10 normalization is permitted."
assert cont.count(old_norm_a) == 1, "unexpected R16.10 normalization authority"
cont = cont.replace(old_norm_a, new_norm_a, 1)
old_norm_b = "- Manual state remains **NONE**. R16.11 START-sync is authorized only from the resulting normalized `main`; it remains unauthorized from the implementation merge or from any unmerged normalization candidate."
new_norm_b = f"- Manual state remains **NONE**. R16.11 START is authorized only from normalized `main` `{BASE}` and is now synchronized on `{BRANCH}` before implementation."
assert cont.count(old_norm_b) == 1, "unexpected R16.10 normalization manual record"
cont = cont.replace(old_norm_b, new_norm_b, 1)

old_index = "| R16.11 | PLANNED | NONE |"
new_index = "| R16.11 | IN_PROGRESS | NONE |"
assert cont.count(old_index) == 1, "unexpected R16.11 continuity index"
cont = cont.replace(old_index, new_index, 1)

old_next = "R16.11 — **Representative real Godot 3D beta project** — is the next authorized subdivision only on the normalized `main` produced when this unique R16.10 continuity-only normalization PR passes fresh exact-head R0/Python/UI and merges. Do not begin R16.11 from implementation merge `e6c11e986ad2e0ee5b1cdd50c0ae2061117ca974` or from an unmerged normalization candidate. After normalization merge, create the dedicated R16.11 branch from that exact normalized `main` and perform START-sync before implementation. Frozen scope: representative repository-owned Godot 3D scenes/resources, meshes/materials/animation references where already supported, KodeGodot execution/diagnostics, asset lineage, edits/rollback, resource budgets and malicious metadata/text controls. Manual NONE."
new_next = f"Implement and accept **R16.11 — Representative real Godot 3D beta project** on `{BRANCH}` from exact normalized `main` `{BASE}`. Use a bounded repository-owned 3D project with deterministic provenance and manageable CI size; exercise supported public KodeGodot inspection/edit/validation, workspace-bounded lineage-aware asset references, representative multi-file change plus failure/cancel/SafeChange rollback, resource-budget and malformed/external-reference negative controls, exact project/artifact/diff/diagnostic/recovery digests and truthful capability markers for unavailable external Godot/3D tools. Manual NONE. Freeze one immutable technical source, run focused Ubuntu/Windows acceptance plus fresh R16.9 supply-chain regression if workflow authority changes, R0/Python/UI, END-sync and fresh exact-END re-gates before exact-head merge and the unique continuity-only post-merge normalization."
assert cont.count(old_next) == 1, "unexpected next authorized action"
cont = cont.replace(old_next, new_next, 1)

marker = "\n## R16 status index\n"
assert cont.count(marker) == 1, "missing R16 status index marker"
start_record = f'''\n## R16.11 START authority\n\n- Dedicated branch: `{BRANCH}`.\n- Exact normalized branch point: `main` `{BASE}` after unique R16.10 continuity normalization PR #354.\n- State at START: R1–R15 COMPLETE + NORMALIZED; R16 planning ACCEPTED + NORMALIZED; R16.1–R16.10 COMPLETE + NORMALIZED; R16.11 IN_PROGRESS; R16.12–R16.18 PLANNED.\n- Frozen scope: bounded representative repository-owned Godot 3D project with deterministic provenance/manageable CI size; 3D scenes/resources; meshes/materials/animation references where already supported; public KodeGodot execution/diagnostics and multi-file inspection/edit/validation; workspace-bounded lineage-aware asset references; representative failure/cancel/SafeChange rollback; resource budgets; malformed/external-reference and malicious metadata/text negative controls; exact project/artifact/diff/diagnostic/recovery digests.\n- R8/R10 3D asset/Blender/Godot bridge capabilities are dependencies, not permission to invent unsupported engine functionality. External Godot/GPU/renderer/tool availability remains capability-probed and any live claim must record actual executable/version/invocation.\n- Core acceptance remains CI-owned and cross-platform; no external project, live secret, network dependency, dedicated GPU or destructive host action is required.\n- Manual state: **NONE**.\n- No R16.11 implementation preceded this START-sync.\n'''
cont = cont.replace(marker, start_record + marker, 1)
cont_path.write_text(cont, encoding="utf-8", newline="\n")
