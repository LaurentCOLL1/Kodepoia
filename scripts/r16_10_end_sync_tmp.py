from pathlib import Path

PLAN = Path('docs/roadmap/R16_PLAN.md')
CONT = Path('docs/continuity/KODEPOIA_CONTINUITY.md')

plan = PLAN.read_text(encoding='utf-8')
old = "R16.1–R16.9 are COMPLETE + NORMALIZED. R16.10 is IN_PROGRESS from normalized `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6` on dedicated branch `r16/10-representative-godot-2d-beta-project`; R16.11–R16.18 remain PLANNED."
new = "R16.1–R16.9 are COMPLETE + NORMALIZED. R16.10 is COMPLETE on dedicated branch `r16/10-representative-godot-2d-beta-project` from normalized `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; R16.11–R16.18 remain PLANNED. R16.10 still requires fresh exact-END re-gates, exact-head merge, and the unique continuity-only post-merge normalization before R16.11 is authorized."
assert plan.count(old) == 1
plan = plan.replace(old, new)
old = "| R16.10 | Representative real Godot 2D beta project | IN_PROGRESS | NONE |"
new = "| R16.10 | Representative real Godot 2D beta project | COMPLETE | NONE |"
assert plan.count(old) == 1
plan = plan.replace(old, new)
marker = "## Manual intervention\n\n**NONE** for core acceptance.\n\n---\n\n# R16.11 — Representative real Godot 3D beta project"
evidence = '''## Manual intervention

**NONE** for core acceptance.

## R16.10 implementation evidence

- Exact normalized base: `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; dedicated branch `r16/10-representative-godot-2d-beta-project`; final immutable technical candidate before END-sync: `499292dd553460bb48f3092112d5bcb81544242b` (tree-identical retrigger of clean source `ee433680428fd525970456d740980e432d38bea5`).
- Exact-source focused acceptance: R16.10 #20 / `33638816914` SUCCESS on Ubuntu + Windows. Both jobs passed exact checkout/provenance, wheel+sdist build, compile, Ruff, focused tests, machine-readable acceptance emission and artifact upload.
- Exact-source supply-chain regression qualification: R16.9 #23 / `33638824052` SUCCESS Ubuntu + Windows after registering the R16.10 focused workflow as the 13th immutable authority while preserving strict `all(item.authoritative)` enforcement and full-SHA action pins.
- Exact-source repository qualification: R0 #2333 / `33638823984` SUCCESS Ubuntu + Windows; Python Core #2305 / `33638824758` SUCCESS 5/5; standalone KodeStudio UI Smoke #2270 / `33638824596` SUCCESS.
- Acceptance summary: 10/10 cases PASS on each OS; `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, no live credentials, zero network calls, no destructive host action. Untrusted repository/project text remains data-only.
- Godot live capability is truthfully `capability_absent` on both hosted runners; no executable/version/invocation is claimed.
- Canonical cross-platform SHA-256: fixture/restored `e87b912f36b960e724b4d2eb6367794c6933ae0255353b5cbcbb400294c66b95`; changed `0312025cdbfef593ba21a4280d9d897c4ef8aa37ec8201ceeec9c9b9b96f054e`; diff `4226629a0be5da2ba2dfb3f344d56b973d9893462ef8cba64c7bc8b37a450542`; diagnostic `f61d0af7376d7deda7ad2ac65b5debdf47154f432403d41c150d351a59fc6b07`; recovery `6f107c6ff1c683ad31597e400512fb247ed56b6e4d035c1a9f0e4dce5ab5a7d5`; semantic `25b95aa0ae5ccd909a1b93e9e0d3540482a2f6c6c01491c6fd7845fd80bbe095`.
- Exact-source artifacts: Linux `9850084807 / sha256:09eede99ef70a5b9faefdde5965001e1c3d33de8ad55d34242fa97582f2e5c28`; Windows `9850065450 / sha256:f0d2da48b853f1d27d8cc14e61884c32357438ed85a9d1616cd86ffdd6c252da`.
- SafeChange rollback uses canonical LF manifest serialization and restores the original project digest exactly.
- R16.10 is COMPLETE at END-sync. R16.11 remains unauthorized until fresh exact-END R16.10/R16.9/R0/Python/UI gates, PR #353 exact-head merge, and the unique continuity-only post-merge normalization all succeed.

---

# R16.11 — Representative real Godot 3D beta project'''
assert plan.count(marker) == 1
PLAN.write_text(plan.replace(marker, evidence), encoding='utf-8', newline='\n')

cont = CONT.read_text(encoding='utf-8')
old = "**R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.9 COMPLETE + NORMALIZED. R16.10 IN_PROGRESS on `r16/10-representative-godot-2d-beta-project` from normalized `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; R16.11–R16.18 remain PLANNED.**"
new = "**R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.9 COMPLETE + NORMALIZED. R16.10 COMPLETE at END-sync on `r16/10-representative-godot-2d-beta-project` from normalized `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; R16.11–R16.18 remain PLANNED and unauthorized until R16.10 merge + unique post-merge normalization.**"
assert cont.count(old) == 1
cont = cont.replace(old, new)
assert cont.count('| R16.10 | IN_PROGRESS | NONE |') == 1
cont = cont.replace('| R16.10 | IN_PROGRESS | NONE |', '| R16.10 | COMPLETE | NONE |')
anchor = '- No R16.10 implementation preceded this START-sync.\n\n## R16 status index'
block = '''- No R16.10 implementation preceded this START-sync.

## R16.10 END authority

- R16.10 state: **COMPLETE at END-sync**, manual **NONE**; R16.11–R16.18 remain PLANNED and R16.11 is not yet authorized.
- Exact normalized base `3957a30053da791facb2de7fbbbb0614d0fa03d6`; immutable technical candidate `499292dd553460bb48f3092112d5bcb81544242b`, tree-identical to clean source `ee433680428fd525970456d740980e432d38bea5`.
- Technical focused R16.10 #20 / `33638816914`: SUCCESS Ubuntu + Windows; artifacts Linux `9850084807 / sha256:09eede99ef70a5b9faefdde5965001e1c3d33de8ad55d34242fa97582f2e5c28`, Windows `9850065450 / sha256:f0d2da48b853f1d27d8cc14e61884c32357438ed85a9d1616cd86ffdd6c252da`.
- Same-source gates: R16.9 #23 / `33638824052` SUCCESS Ubuntu + Windows; R0 #2333 / `33638823984` SUCCESS Ubuntu + Windows; Python Core #2305 / `33638824758` SUCCESS 5/5; UI #2270 / `33638824596` SUCCESS.
- Acceptance: 10/10 PASS per OS, `security_claim=true`, `critical_veto=false`, manual NONE, no live credentials, zero network calls, no destructive host action; Godot is `capability_absent` on both hosted runners.
- Canonical digests: fixture/restored `e87b912f36b960e724b4d2eb6367794c6933ae0255353b5cbcbb400294c66b95`; changed `0312025cdbfef593ba21a4280d9d897c4ef8aa37ec8201ceeec9c9b9b96f054e`; diff `4226629a0be5da2ba2dfb3f344d56b973d9893462ef8cba64c7bc8b37a450542`; diagnostic `f61d0af7376d7deda7ad2ac65b5debdf47154f432403d41c150d351a59fc6b07`; recovery `6f107c6ff1c683ad31597e400512fb247ed56b6e4d035c1a9f0e4dce5ab5a7d5`; semantic `25b95aa0ae5ccd909a1b93e9e0d3540482a2f6c6c01491c6fd7845fd80bbe095`.
- R16.10 is the 13th immutable R16.9 workflow authority; strict full-SHA action pinning and least privilege remain unchanged.
- The final END head must differ from `499292dd...` only in `docs/roadmap/R16_PLAN.md` and this continuity file, then pass fresh R16.10/R16.9/R0/Python/UI before PR #353 exact-head merge.
- Exactly one post-merge continuity-only normalization is authorized; only its normalized `main` may authorize R16.11 START.

## R16 status index'''
assert cont.count(anchor) == 1
CONT.write_text(cont.replace(anchor, block), encoding='utf-8', newline='\n')
