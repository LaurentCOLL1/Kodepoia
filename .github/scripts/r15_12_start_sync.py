from pathlib import Path

plan_path = Path("docs/roadmap/R15_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

normalized_main = "3f931e4f5baa664fcea53c445846200bcf3b5bfd"

old_checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.10 are COMPLETE + NORMALIZED. R15.11 is COMPLETE with immutable technical source `6f49a72918d4ddb4ae4d779e85513ae721688c49`; its final documented END-head requires fresh exact-head R15.11/R0/Python/UI gates before protected merge. R15.12–R15.17 remain PLANNED."
new_checkpoint = f"**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.11 are COMPLETE + NORMALIZED. R15.12 is IN_PROGRESS from normalized `main` `{normalized_main}`; R15.13–R15.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit("R15.12 plan checkpoint replacement cardinality mismatch")
plan = plan.replace(old_checkpoint, new_checkpoint)

old_row = "| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | PLANNED | CONDITIONAL | R15.10–R15.11 + R6/R8/R9 |"
new_row = "| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R15.10–R15.11 + R6/R8/R9 |"
if plan.count(old_row) != 1:
    raise SystemExit("R15.12 index replacement cardinality mismatch")
plan = plan.replace(old_row, new_row)

old_status = "R15.1–R15.11 COMPLETE + NORMALIZED; R15.12–R15.17 PLANNED."
new_status = "R15.1–R15.11 COMPLETE + NORMALIZED; R15.12 IN_PROGRESS; R15.13–R15.17 PLANNED."
if continuity.count(old_status) != 1:
    raise SystemExit("R15.12 continuity status replacement cardinality mismatch")
continuity = continuity.replace(old_status, new_status)

old_authority = "This continuity-only record is the unique R15.11 post-merge normalization authority when its fresh R0/Python/UI gates pass and it merges; manual state R15.11: NONE."
new_authority = f"R15.11 normalization head `72fcf65a0a996e3b5456007c47ebedb21ef06f9c` passed R0 #2176 / `33322653395`, Python Core #2151 / `33322653264` and KodeStudio UI Smoke #2116 / `33322653415`; normalization PR #318 merged exact head as normalized `main` `{normalized_main}`. R15.12 START is authorized from that exact normalized main on branch `r15/12-gguf-conversion-quantization`; manual state R15.12: CONDITIONAL / NOT TRIGGERED."
if continuity.count(old_authority) != 1:
    raise SystemExit("R15.12 top authority replacement cardinality mismatch")
continuity = continuity.replace(old_authority, new_authority)

r15_11_bullet = "- R15.11 : **COMPLETE + NORMALIZED** — clean START / normalized R15.10 `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`; immutable technical source `6f49a72918d4ddb4ae4d779e85513ae721688c49`; final exact END-head `9a351386f9cebffb0458c99da3e02705bfefcd7a`; exact-END R15.11 #8 / `33321151927` SUCCESS Ubuntu + Windows, R0 #2174 / `33321151973` SUCCESS Ubuntu + Windows, Python Core #2149 / `33321151901` SUCCESS, KodeStudio UI Smoke #2114 / `33321151869` SUCCESS; PR #317 merged with `expected_head_sha=9a351386f9cebffb0458c99da3e02705bfefcd7a` as implementation/evidence `main` `43c33064935d1323a1993eae64b2c3a4385f1e36`. Export remains restricted to R15.10 `PROMOTE_TO_EXPORT`, exact base/revision/adapter/dataset/training/evaluation lineage, immutable Safetensors/model-card manifests, source-weight immutability and adapter-only fallback when merge is unsupported. Manual NONE. This record is the unique post-merge continuity-only R15.11 normalization authority when merged; R15.12 START is authorized only from the resulting normalized `main` after this branch passes fresh exact-head R0/Python/UI."
r15_12_bullet = f"- R15.12 : **IN_PROGRESS** — clean START / normalized R15.11 `main` `{normalized_main}`; dedicated branch `r15/12-gguf-conversion-quantization`. Scope is llama.cpp capability/revision probing, structured conversion/quantization plans, high-precision-source preference, semantic GGUF validation, immutable hashes/metadata, policy-driven quantization matrix and quality-loss/critical-regression rejection. Requantization is never implicit; Ollama promotion/public distribution remain out of scope. Manual state CONDITIONAL / NOT TRIGGERED: core wrappers, validators and tiny tool fixtures are automated; real large-model conversion is not required unless later evidence explicitly triggers that gate. R15.13–R15.17 remain PLANNED and unauthorized."
if continuity.count(r15_11_bullet) != 1:
    raise SystemExit("R15.12 continuity insertion anchor cardinality mismatch")
continuity = continuity.replace(r15_11_bullet, r15_11_bullet + "\n" + r15_12_bullet)

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
