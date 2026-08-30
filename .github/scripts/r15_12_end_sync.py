from pathlib import Path

plan_path = Path("docs/roadmap/R15_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

technical_source = "3841c6082437693a6b8f8661354451b677867ce8"

old_checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.11 are COMPLETE + NORMALIZED. R15.12 is IN_PROGRESS from normalized `main` `3f931e4f5baa664fcea53c445846200bcf3b5bfd`; R15.13–R15.17 remain PLANNED."
new_checkpoint = f"**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.11 are COMPLETE + NORMALIZED. R15.12 is COMPLETE with immutable technical source `{technical_source}`; its final documented END-head requires fresh exact-head R15.12/R0/Python/UI gates before protected merge. R15.13–R15.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit("R15.12 END plan checkpoint cardinality mismatch")
plan = plan.replace(old_checkpoint, new_checkpoint)

old_row = "| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R15.10–R15.11 + R6/R8/R9 |"
new_row = "| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | COMPLETE | CONDITIONAL / NOT TRIGGERED | R15.10–R15.11 + R6/R8/R9 |"
if plan.count(old_row) != 1:
    raise SystemExit("R15.12 END index cardinality mismatch")
plan = plan.replace(old_row, new_row)

old_status = "R15.1–R15.11 COMPLETE + NORMALIZED; R15.12 IN_PROGRESS; R15.13–R15.17 PLANNED."
new_status = "R15.1–R15.11 COMPLETE + NORMALIZED; R15.12 COMPLETE pending final END-head re-gates/merge/normalization; R15.13–R15.17 PLANNED."
if continuity.count(old_status) != 1:
    raise SystemExit("R15.12 END continuity status cardinality mismatch")
continuity = continuity.replace(old_status, new_status)

old_manual = "R15.12 START is authorized from that exact normalized main on branch `r15/12-gguf-conversion-quantization`; manual state R15.12: CONDITIONAL / NOT TRIGGERED."
new_manual = f"R15.12 immutable technical source `{technical_source}` implements bounded GGUF header validation, exact source/export/evaluation lineage, structured llama.cpp converter/quantizer argv, high-precision-source preference, explicit requantization refusal, artifact budgets/hashes, importance-matrix digest binding and deterministic quality/critical-domain veto evidence. Final END-head exact gates/merge/normalization remain pending; manual state R15.12: CONDITIONAL / NOT TRIGGERED."
if continuity.count(old_manual) != 1:
    raise SystemExit("R15.12 END top authority cardinality mismatch")
continuity = continuity.replace(old_manual, new_manual)

old_bullet = "- R15.12 : **IN_PROGRESS** — clean START / normalized R15.11 `main` `3f931e4f5baa664fcea53c445846200bcf3b5bfd`; dedicated branch `r15/12-gguf-conversion-quantization`. Scope is llama.cpp capability/revision probing, structured conversion/quantization plans, high-precision-source preference, semantic GGUF validation, immutable hashes/metadata, policy-driven quantization matrix and quality-loss/critical-regression rejection. Requantization is never implicit; Ollama promotion/public distribution remain out of scope. Manual state CONDITIONAL / NOT TRIGGERED: core wrappers, validators and tiny tool fixtures are automated; real large-model conversion is not required unless later evidence explicitly triggers that gate. R15.13–R15.17 remain PLANNED and unauthorized."
new_bullet = f"- R15.12 : **COMPLETE — final END-head re-gates pending** — clean START / normalized R15.11 `main` `3f931e4f5baa664fcea53c445846200bcf3b5bfd`; immutable technical source `{technical_source}`. The core validates GGUF magic/version/counts and disk bounds, binds source/export/evaluation hashes, emits only structured converter/quantizer argv, rejects already-quantized authoritative sources, validates optional importance-matrix digests, and evaluates every authorized quantization target with aggregate-loss limits plus an unconditional critical-domain veto. Seven tiny fixture tests cover malformed artifacts, lineage mismatch, requantization refusal, fake conversion/quantization, tool failure/capability absence, importance matrices, deterministic evidence schema and quality rejection. Manual CONDITIONAL / NOT TRIGGERED; a real large-model conversion is not needed for core acceptance. Exact final R15.12/R0/Python/UI gates, protected merge and continuity-only normalization remain pending; R15.13–R15.17 stay PLANNED and unauthorized."
if continuity.count(old_bullet) != 1:
    raise SystemExit("R15.12 END continuity bullet cardinality mismatch")
continuity = continuity.replace(old_bullet, new_bullet)

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
