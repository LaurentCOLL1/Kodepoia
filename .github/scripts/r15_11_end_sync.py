from pathlib import Path

plan_path = Path("docs/roadmap/R15_PLAN.md")
continuity_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
plan = plan_path.read_text(encoding="utf-8")
continuity = continuity_path.read_text(encoding="utf-8")

technical_source = "527b498e79306425574dc724d00f5edd4a8d14e3"
old_checkpoint = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.10 are COMPLETE + NORMALIZED. R15.11 is IN_PROGRESS from normalized `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`; R15.12–R15.17 remain PLANNED."
new_checkpoint = f"**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.10 are COMPLETE + NORMALIZED. R15.11 is COMPLETE with immutable technical source `{technical_source}`; its final documented END-head requires fresh exact-head R15.11/R0/Python/UI gates before protected merge. R15.12–R15.17 remain PLANNED."
if plan.count(old_checkpoint) != 1:
    raise SystemExit("R15.11 plan checkpoint replacement cardinality mismatch")
plan = plan.replace(old_checkpoint, new_checkpoint)

old_row = "| R15.11 | Accepted adapter/model export, merge compatibility, Safetensors/model card + lineage | IN_PROGRESS | NONE | R15.9–R15.10 + R8 |"
new_row = "| R15.11 | Accepted adapter/model export, merge compatibility, Safetensors/model card + lineage | COMPLETE | NONE | R15.9–R15.10 + R8 |"
if plan.count(old_row) != 1:
    raise SystemExit("R15.11 index replacement cardinality mismatch")
plan = plan.replace(old_row, new_row)

old_top_fragment = "R15.1–R15.10 COMPLETE + NORMALIZED; R15.11 IN_PROGRESS; R15.12–R15.17 PLANNED."
new_top_fragment = "R15.1–R15.10 COMPLETE + NORMALIZED; R15.11 COMPLETE pending final END-head re-gates/merge/normalization; R15.12–R15.17 PLANNED."
if continuity.count(old_top_fragment) != 1:
    raise SystemExit("R15.11 continuity top replacement cardinality mismatch")
continuity = continuity.replace(old_top_fragment, new_top_fragment)

old_manual = "R15.11 START is authorized from that exact normalized main on branch `r15/11-model-export-lineage`; manual state R15.11: NONE."
new_manual = f"R15.11 immutable technical source `{technical_source}` implements deterministic accepted-candidate export, exact base/adaptor binding, adapter-only fallback for unsupported merge, immutable manifest/model card lineage, source immutability and load-smoke injection. Final END-head exact gates/merge/normalization remain pending; manual state R15.11: NONE."
if continuity.count(old_manual) != 1:
    raise SystemExit("R15.11 continuity authority replacement cardinality mismatch")
continuity = continuity.replace(old_manual, new_manual)

old_bullet = "- R15.11 : **IN_PROGRESS** — clean START / normalized R15.10 `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`; dedicated branch `r15/11-model-export-lineage`; scope is accepted-adapter Safetensors/config/tokenizer/template validation, immutable export manifest/model card/license-provenance/checksums and optional supported high-precision merge bound to the exact base model. GGUF quantization, Ollama import/public upload and active registry mutation remain out of scope; unsupported merge remains adapter-only. Manual NONE for fixture/core exporter; R15.12–R15.17 remain PLANNED and unauthorized."
new_bullet = f"- R15.11 : **COMPLETE — final END-head re-gates pending** — clean START / normalized R15.10 `main` `76b1a2b98676376bf917b7fac4cb68bb3d34b2fb`; immutable technical source `{technical_source}`. Export accepts only R15.10 `PROMOTE_TO_EXPORT`, binds adapter config/revision and tree digest to the immutable base/training/dataset/evaluation lineage, emits deterministic adapter/model-card manifests without raw/private source contents, never overwrites source weights, and keeps unsupported merge adapter-only. Tiny fixture tests cover mismatch/rejection, deterministic export, merge capability injection, load smoke, card secrecy and Draft 2020-12 schema validation. Manual NONE; exact final R15.11/R0/Python/UI gates, protected merge and unique continuity-only normalization remain pending; R15.12–R15.17 stay PLANNED and unauthorized."
if continuity.count(old_bullet) != 1:
    raise SystemExit("R15.11 continuity bullet replacement cardinality mismatch")
continuity = continuity.replace(old_bullet, new_bullet)

plan_path.write_text(plan, encoding="utf-8")
continuity_path.write_text(continuity, encoding="utf-8")
