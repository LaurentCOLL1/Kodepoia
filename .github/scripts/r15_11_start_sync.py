from pathlib import Path

plan_path = Path("docs/roadmap/R15_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

old_checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.9 are COMPLETE + NORMALIZED. R15.10 is COMPLETE with immutable technical source `a4770042509dbba9397c974f2f5f153513f97b24`; its final documented END-head requires fresh exact-head R15.10/R0/Python/UI gates before protected merge. R15.11–R15.17 remain PLANNED."
new_checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.10 are COMPLETE + NORMALIZED. R15.11 is IN_PROGRESS from normalized `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`; R15.12–R15.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit("R15 plan checkpoint replacement cardinality mismatch")
plan = plan.replace(old_checkpoint, new_checkpoint)

rows = {
    "| R15.9 | QLoRA/SFT adapter training, checkpoints, resume/cancel/recovery + budget controls | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED | R15.5/R15.7–R15.8 |":
    "| R15.9 | QLoRA/SFT adapter training, checkpoints, resume/cancel/recovery + budget controls | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED | R15.5/R15.7–R15.8 |",
    "| R15.10 | Base-vs-adapter evaluation, critical-regression veto + candidate disposition | PLANNED | NONE | R15.6/R15.9 |":
    "| R15.10 | Base-vs-adapter evaluation, critical-regression veto + candidate disposition | COMPLETE + NORMALIZED | NONE | R15.6/R15.9 |",
    "| R15.11 | Accepted adapter/model export, merge compatibility, Safetensors/model card + lineage | PLANNED | NONE | R15.9–R15.10 + R8 |":
    "| R15.11 | Accepted adapter/model export, merge compatibility, Safetensors/model card + lineage | IN_PROGRESS | NONE | R15.9–R15.10 + R8 |",
}
for old, new in rows.items():
    if plan.count(old) != 1:
        raise SystemExit(f"R15 index replacement cardinality mismatch: {old}")
    plan = plan.replace(old, new)

old_top = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.10 COMPLETE + NORMALIZED; R15.11–R15.17 PLANNED.** R15.10 final END-head `e29d55fe52cbbb10515225fa5a7af96c902b9ec1` passed R15.10 #15 / `33317403780`, R0 #2163 / `33317403737`, Python Core #2138 / `33317403712` and UI #2103 / `33317403781`; PR #315 merged that exact head as implementation/evidence `main` `90e60d2ce82db12165a7a6092993b214152cb143`. This record is the unique post-merge continuity-only R15.10 normalization authority when merged; R15.11 START is authorized only from the resulting normalized `main`. Manual state R15.10: NONE."
new_top = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.10 COMPLETE + NORMALIZED; R15.11 IN_PROGRESS; R15.12–R15.17 PLANNED.** R15.10 final END-head `e29d55fe52cbbb10515225fa5a7af96c902b9ec1` passed R15.10 #15 / `33317403780`, R0 #2163 / `33317403737`, Python Core #2138 / `33317403712` and UI #2103 / `33317403781`; PR #315 merged exact head as `90e60d2ce82db12165a7a6092993b214152cb143`; normalization head `f862d2cf1bd148abaae3c74a98de2d8e9bc12ee1` passed R0 #2165 / `33317741671`, Python Core #2140 / `33317741716` and UI #2105 / `33317741688`, then PR #316 merged as normalized `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`. R15.11 START is authorized from that exact normalized main on branch `r15/11-model-export-lineage`; manual state R15.11: NONE."
if continuity.count(old_top) != 1:
    raise SystemExit("continuity top replacement cardinality mismatch")
continuity = continuity.replace(old_top, new_top)

old_tail = "Manual NONE. This record is the unique post-merge continuity-only R15.10 normalization authority when merged; R15.11 START is authorized only from the resulting normalized `main`."
new_tail = "Manual NONE. Normalization head `f862d2cf1bd148abaae3c74a98de2d8e9bc12ee1` passed R0 #2165 / `33317741671`, Python Core #2140 / `33317741716` and UI #2105 / `33317741688`; normalization PR #316 merged exact head as normalized `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`. This is the unique post-merge continuity-only R15.10 normalization authority; R15.11 START is authorized from that exact normalized main."
if continuity.count(old_tail) != 1:
    raise SystemExit("continuity R15.10 normalization tail cardinality mismatch")
continuity = continuity.replace(old_tail, new_tail)

marker = "\n- R14.1–R14.9 : **COMPLETE + NORMALIZED**."
new_bullet = "\n- R15.11 : **IN_PROGRESS** — clean START / normalized R15.10 `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`; dedicated branch `r15/11-model-export-lineage`; scope is accepted-adapter Safetensors/config/tokenizer/template validation, immutable export manifest/model card/license-provenance/checksums and optional supported high-precision merge bound to the exact base model. GGUF quantization, Ollama import/public upload and active registry mutation remain out of scope; unsupported merge remains adapter-only. Manual NONE for fixture/core exporter; R15.12–R15.17 remain PLANNED and unauthorized."
if continuity.count(marker) != 1:
    raise SystemExit("continuity R15.11 insertion marker cardinality mismatch")
continuity = continuity.replace(marker, new_bullet + marker)

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
