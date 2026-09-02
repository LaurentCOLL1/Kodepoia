from pathlib import Path

base = "75e58ba578d6c5f654be1c3a8e35fae7f86cb72a"
branch = "r16/11-representative-godot-3d-beta-project"
technical = "4be69eef7300c380d125f35d484c57d8df054d72"

plan_path = Path("docs/roadmap/R16_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.10 are COMPLETE + NORMALIZED. R16.11 is IN_PROGRESS from normalized `main` `75e58ba578d6c5f654be1c3a8e35fae7f86cb72a` on dedicated branch `r16/11-representative-godot-3d-beta-project`; R16.12–R16.18 remain PLANNED."
new_checkpoint = "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.10 are COMPLETE + NORMALIZED. R16.11 is COMPLETE at END-sync on immutable technical source `4be69eef7300c380d125f35d484c57d8df054d72`; R16.12–R16.18 remain PLANNED. Fresh exact-END R16.11/R16.9/R0/Python/UI re-gates, exact-head implementation/evidence merge and the unique continuity-only post-merge normalization are still required before R16.12 is authorized."
assert plan.count(old_checkpoint) == 1
plan = plan.replace(old_checkpoint, new_checkpoint, 1)
old_index = "| R16.11 | Representative real Godot 3D beta project | IN_PROGRESS | NONE |"
new_index = "| R16.11 | Representative real Godot 3D beta project | COMPLETE | NONE |"
assert plan.count(old_index) == 1
plan = plan.replace(old_index, new_index, 1)
marker = "\n---\n\n# R16.12 — Representative real Windows desktop application\n"
assert plan.count(marker) == 1
end_evidence = '''
## R16.11 implementation evidence

- Exact normalized base: `main` `75e58ba578d6c5f654be1c3a8e35fae7f86cb72a`; clean START-sync head `58816b94d4823fd51612151a03c56e3dbe2fe117`; dedicated branch `r16/11-representative-godot-3d-beta-project`.
- Immutable technical source: `4be69eef7300c380d125f35d484c57d8df054d72`.
- Exact-source focused acceptance: R16.11 #12 / `33662240625` SUCCESS Ubuntu + Windows. Both jobs passed exact checkout provenance, wheel+sdist build, compile, Ruff, focused R16.10/R16.11 plus R16.9 supply-chain regression tests, machine-readable acceptance emission and artifact upload.
- Exact-source supply-chain qualification: R16.9 #34 / `33662240583` SUCCESS Ubuntu + Windows after registering the R16.11 workflow as immutable v1 authority with full-SHA actions and read-only permissions.
- Exact-source repository qualification: R0 #2346 / `33662240657` SUCCESS; Python Core #2318 / `33662240501` SUCCESS; KodeStudio UI Smoke #2283 / `33662240630` SUCCESS.
- Acceptance summary: 15/15 cases PASS per OS with `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, zero network calls, no live credentials and no destructive host action. Godot is truthfully `capability_absent` on both hosted runners.
- Representative fixture budget: 8 files, 3754 bytes total, maximum single file 1388 bytes; deterministic OBJ mesh, material, scenes, script, provenance and malicious-metadata negative control stay repository-owned and CI-bounded.
- Canonical cross-platform SHA-256: fixture/pre-change/restored/cancel-restored `69f88a9cb0c250e33ce40783bc11de179cf06a86c669feaafcf1419f2234dcb1`; changed `4a59aaa65f06d04c3df3f088b625f5e3fba6b4999267769ab26e7ae82903d7ab`; diff `d701bff2aa3100c3b46d571deea69e7abc7a35068162e6141a9e6d9cd89e9fe6`; diagnostic `d041a7f188fd1ed47caca5753e1322ed1793cbc441930957616e7dc05ffe473e`; recovery `6d4ac38558c776ac3cc74c13f7ba5dce0cbe15d7dd6c4e27edffda8a3b30687d`; asset content `7e1702ec3110d793088cb7f779e5c0e30fdd1826110013b6c85e4062cd9c5f77`; semantic `bc3ee5d201026acd880fab0b06e84e6a335e72e23685935611d8531b9c6ac294`; deterministic asset revision `rev_c14815e60f06b6b3dca5ffdc7dfa5b84`.
- Exact-source artifacts: Linux `9859239402 / archive sha256:0bff3e1437de0f0a04617d8beb9cf10b86deb15a034bd9daec8872781f7c7d3f / payload sha256:382339653ca3b4d00f28fbdc4d31e196b862eee9ff43ddd2b7580a95d46386e1`; Windows `9859245340 / archive sha256:3c195da388272bee3f6f29243ca626554fb568726f76b25c6756f50886207dab / payload sha256:b8cea082e2933ee39c767f09e100e38862bcfb0db86a3c31babce6476207c4af`.
- Accepted boundaries: public KodeGodot 3D inspection/analysis/edit paths; Vault lineage-aware reference; WorkspaceBoundary confinement; external-reference negative control; untrusted metadata remains inspectable data without process/tool authority; bounded cancellation rollback; SHA-precondition failure; integrity-bound checkpoint; aggregate SafeChange exact restore; audit-chain verification; explicit resource budgets.
- R16.11 is COMPLETE at END-sync. R16.12 remains unauthorized until this documentation/evidence END head passes fresh exact-head R16.11/R16.9/R0/Python/UI gates, merges with exact `expected_head_sha`, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.
'''
plan = plan.replace(marker, "\n" + end_evidence + marker, 1)
plan_path.write_text(plan, encoding="utf-8", newline="\n")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
lines = cont.splitlines()
assert lines and "R16.11 IN_PROGRESS" in lines[0] and base in lines[0]
lines[0] = "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. R16.1–R16.10 COMPLETE + NORMALIZED. R16.11 COMPLETE at END-sync on immutable technical source `4be69eef7300c380d125f35d484c57d8df054d72`; R16.12–R16.18 remain PLANNED.** Technical R16.11 #12 / `33662240625`, R16.9 #34 / `33662240583`, R0 #2346 / `33662240657`, Python Core #2318 / `33662240501` and KodeStudio UI Smoke #2283 / `33662240630` are SUCCESS on the exact technical source as applicable. Fresh exact-END re-gates, exact-head implementation/evidence merge and unique post-merge continuity normalization remain required before R16.12. Manual NONE."
cont = "\n".join(lines) + "\n"
old_index = "| R16.11 | IN_PROGRESS | NONE |"
new_index = "| R16.11 | COMPLETE | NONE |"
assert cont.count(old_index) == 1
cont = cont.replace(old_index, new_index, 1)
old_next = "Implement and accept **R16.11 — Representative real Godot 3D beta project** on `r16/11-representative-godot-3d-beta-project` from exact normalized `main` `75e58ba578d6c5f654be1c3a8e35fae7f86cb72a`. Use a bounded repository-owned 3D project with deterministic provenance and manageable CI size; exercise supported public KodeGodot inspection/edit/validation, workspace-bounded lineage-aware asset references, representative multi-file change plus failure/cancel/SafeChange rollback, resource-budget and malformed/external-reference negative controls, exact project/artifact/diff/diagnostic/recovery digests and truthful capability markers for unavailable external Godot/3D tools. Manual NONE. Freeze one immutable technical source, run focused Ubuntu/Windows acceptance plus fresh R16.9 supply-chain regression if workflow authority changes, R0/Python/UI, END-sync and fresh exact-END re-gates before exact-head merge and the unique continuity-only post-merge normalization."
new_next = "Finalize **R16.11** from immutable technical source `4be69eef7300c380d125f35d484c57d8df054d72`: the END-sync tree may change only `docs/roadmap/R16_PLAN.md` and this continuity file relative to that source, then must pass fresh exact-head R16.11, R16.9, R0, full Python Core and KodeStudio UI Smoke. Merge the implementation/evidence PR only with exact `expected_head_sha`; then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI. Only the resulting normalized `main` authorizes **R16.12 — Representative real Windows desktop application**. Manual NONE."
assert cont.count(old_next) == 1
cont = cont.replace(old_next, new_next, 1)
marker = "\n## R16 status index\n"
assert cont.count(marker) == 1
end_record = '''
## R16.11 END authority

- R16.11 state: **COMPLETE at END-sync**, manual **NONE**; R16.12–R16.18 remain PLANNED and R16.12 is not yet authorized.
- Exact normalized base `75e58ba578d6c5f654be1c3a8e35fae7f86cb72a`; clean START-sync `58816b94d4823fd51612151a03c56e3dbe2fe117`; immutable technical source `4be69eef7300c380d125f35d484c57d8df054d72`.
- Technical focused R16.11 #12 / `33662240625`: SUCCESS Ubuntu + Windows; technical artifacts Linux `9859239402 / sha256:0bff3e1437de0f0a04617d8beb9cf10b86deb15a034bd9daec8872781f7c7d3f`, Windows `9859245340 / sha256:3c195da388272bee3f6f29243ca626554fb568726f76b25c6756f50886207dab`.
- Same-source gates: R16.9 #34 / `33662240583` SUCCESS Ubuntu + Windows; R0 #2346 / `33662240657` SUCCESS; Python Core #2318 / `33662240501` SUCCESS; UI #2283 / `33662240630` SUCCESS.
- Acceptance: 15/15 PASS per OS, `security_claim=true`, `critical_veto=false`, manual NONE, zero network calls, no live credentials, no destructive host action; hosted runners truthfully report Godot `capability_absent`.
- Fixture budget: 8 files / 3754 bytes / max 1388 bytes. Canonical digests: fixture/restored/cancel-restored `69f88a9cb0c250e33ce40783bc11de179cf06a86c669feaafcf1419f2234dcb1`; changed `4a59aaa65f06d04c3df3f088b625f5e3fba6b4999267769ab26e7ae82903d7ab`; diff `d701bff2aa3100c3b46d571deea69e7abc7a35068162e6141a9e6d9cd89e9fe6`; diagnostic `d041a7f188fd1ed47caca5753e1322ed1793cbc441930957616e7dc05ffe473e`; recovery `6d4ac38558c776ac3cc74c13f7ba5dce0cbe15d7dd6c4e27edffda8a3b30687d`; semantic `bc3ee5d201026acd880fab0b06e84e6a335e72e23685935611d8531b9c6ac294`; asset content `7e1702ec3110d793088cb7f779e5c0e30fdd1826110013b6c85e4062cd9c5f77`; asset revision `rev_c14815e60f06b6b3dca5ffdc7dfa5b84`.
- Security/workflow scope is bounded to repository-owned synthetic 3D data and public KodeGodot/Vault/Workspace/SafeChange/Audit surfaces; malicious metadata and external references remain negative controls, not executable authority.
- The final END head must differ from `4be69eef...` only in `docs/roadmap/R16_PLAN.md` and this continuity file, then pass fresh R16.11/R16.9/R0/Python/UI before exact-head implementation/evidence merge.
- Exactly one post-merge continuity-only normalization is authorized; only its normalized `main` may authorize R16.12 START.
'''
cont = cont.replace(marker, end_record + marker, 1)
cont_path.write_text(cont, encoding="utf-8", newline="\n")
