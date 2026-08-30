from pathlib import Path

plan_path = Path("docs/roadmap/R15_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

normalized_main = "ca625d51808de6c1f9c950faecc2aa785e7a757d"

old_checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.11 are COMPLETE + NORMALIZED. R15.12 is COMPLETE with immutable technical source `3841c6082437693a6b8f8661354451b677867ce8`; its final documented END-head requires fresh exact-head R15.12/R0/Python/UI gates before protected merge. R15.13–R15.17 remain PLANNED."
new_checkpoint = f"**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.12 are COMPLETE + NORMALIZED. R15.13 is IN_PROGRESS from normalized `main` `{normalized_main}`; R15.14–R15.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit("R15.13 plan checkpoint replacement cardinality mismatch")
plan = plan.replace(old_checkpoint, new_checkpoint)

old_r15_12_row = "| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | COMPLETE | CONDITIONAL / NOT TRIGGERED | R15.10–R15.11 + R6/R8/R9 |"
new_r15_12_row = "| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED | R15.10–R15.11 + R6/R8/R9 |"
if plan.count(old_r15_12_row) != 1:
    raise SystemExit("R15.12 normalized row replacement cardinality mismatch")
plan = plan.replace(old_r15_12_row, new_r15_12_row)

old_r15_13_row = "| R15.13 | Ollama import/Modelfile packaging, base-binding + local runtime verification | PLANNED | CONDITIONAL | R15.10–R15.12 + R3 |"
new_r15_13_row = "| R15.13 | Ollama import/Modelfile packaging, base-binding + local runtime verification | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R15.10–R15.12 + R3 |"
if plan.count(old_r15_13_row) != 1:
    raise SystemExit("R15.13 index replacement cardinality mismatch")
plan = plan.replace(old_r15_13_row, new_r15_13_row)

old_top = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.12 COMPLETE + NORMALIZED; R15.13–R15.17 PLANNED.** R15.12 immutable technical source `3841c6082437693a6b8f8661354451b677867ce8`; final exact END-head `3319089a1298f3e7d26e67073102d913d4d07f47` passed R15.12 #10 / `33323150172` Ubuntu + Windows, R0 #2178 / `33323150197` Ubuntu + Windows, Python Core #2153 / `33323150120` and KodeStudio UI Smoke #2118 / `33323150243`; PR #319 merged that exact head as implementation/evidence `main` `6c2b3b2c2c4943e3425601c92edd2dd05a7e4412`. This continuity-only record is the unique R15.12 post-merge normalization authority when its fresh R0/Python/UI gates pass and it merges; manual state R15.12: CONDITIONAL / NOT TRIGGERED."
new_top = f"> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.12 COMPLETE + NORMALIZED; R15.13 IN_PROGRESS; R15.14–R15.17 PLANNED.** R15.12 immutable technical source `3841c6082437693a6b8f8661354451b677867ce8`; final exact END-head `3319089a1298f3e7d26e67073102d913d4d07f47` passed R15.12 #10 / `33323150172` Ubuntu + Windows, R0 #2178 / `33323150197` Ubuntu + Windows, Python Core #2153 / `33323150120` and KodeStudio UI Smoke #2118 / `33323150243`; PR #319 merged that exact head as implementation/evidence `main` `6c2b3b2c2c4943e3425601c92edd2dd05a7e4412`. R15.12 normalization head `cdb18f2e78650a997e4b996b5b19242ccc6424e5` passed R0 #2180 / `33324594986`, Python Core #2155 / `33324595025` and KodeStudio UI Smoke #2120 / `33324594974`; normalization PR #320 merged exact head as normalized `main` `{normalized_main}`. R15.13 START is authorized from that exact normalized main on branch `r15/13-ollama-import-packaging`; manual state R15.13: CONDITIONAL / NOT TRIGGERED."
if continuity.count(old_top) != 1:
    raise SystemExit("R15.13 continuity top replacement cardinality mismatch")
continuity = continuity.replace(old_top, new_top)

r15_12_bullet = "- R15.12 : **COMPLETE + NORMALIZED** — clean START / normalized R15.11 `main` `3f931e4f5baa664fcea53c445846200bcf3b5bfd`; immutable technical source `3841c6082437693a6b8f8661354451b677867ce8`; final exact END-head `3319089a1298f3e7d26e67073102d913d4d07f47`; exact-END R15.12 #10 / `33323150172` SUCCESS Ubuntu + Windows, R0 #2178 / `33323150197` SUCCESS Ubuntu + Windows, Python Core #2153 / `33323150120` SUCCESS and KodeStudio UI Smoke #2118 / `33323150243` SUCCESS; PR #319 merged with `expected_head_sha=3319089a1298f3e7d26e67073102d913d4d07f47` as implementation/evidence `main` `6c2b3b2c2c4943e3425601c92edd2dd05a7e4412`. GGUF validation, exact source/export/evaluation lineage, structured converter/quantizer argv, high-precision-source preference, explicit requantization refusal, artifact budgets/hashes, optional importance-matrix binding and aggregate/critical quality veto remain authoritative. Manual CONDITIONAL / NOT TRIGGERED; real large-model conversion was not required for core acceptance. This record is the unique post-merge continuity-only R15.12 normalization authority when merged; R15.13 START is authorized only from the resulting normalized `main` after this branch passes fresh exact-head R0/Python/UI."
r15_13_bullet = f"- R15.13 : **IN_PROGRESS** — clean START / normalized R15.12 `main` `{normalized_main}`; dedicated branch `r15/13-ollama-import-packaging`. Scope is deterministic Ollama Modelfile/API packaging, exact FROM/ADAPTER base binding, namespaced candidate tags, license/metadata and runtime-parameter capture, create/show/digest lifecycle, loopback-only smoke, structured-output/tool capability probes and KodeBench comparison. Public push, remote authoritative Ollama and silent active-tag replacement remain forbidden. Manual state CONDITIONAL / NOT TRIGGERED: core packaging/lifecycle acceptance uses fakes/fixtures; real local model creation is not required unless later evidence explicitly triggers that gate. R15.14–R15.17 remain PLANNED and unauthorized."
if continuity.count(r15_12_bullet) != 1:
    raise SystemExit("R15.13 continuity insertion anchor cardinality mismatch")
continuity = continuity.replace(r15_12_bullet, r15_12_bullet + "\n" + r15_13_bullet)

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
