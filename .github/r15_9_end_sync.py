from pathlib import Path

TECHNICAL_SOURCE = "a964bff54886cafe640fb583610e81055fbe3907"
NORMALIZED_BASE = "4c1c726301b5a5f798944632336e130ccfb0cbbe"

plan = Path("docs/roadmap/R15_PLAN.md")
text = plan.read_text(encoding="utf-8")
old = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.8 are COMPLETE + NORMALIZED. R15.9 is IN_PROGRESS from normalized `main` `4c1c726301b5a5f798944632336e130ccfb0cbbe`; R15.10–R15.17 remain PLANNED."
new = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.8 are COMPLETE + NORMALIZED. R15.9 is COMPLETE with immutable technical source `a964bff54886cafe640fb583610e81055fbe3907`; its final documented END-head requires fresh exact-head R15.9/R0/Python/UI gates before protected merge. R15.10–R15.17 remain PLANNED."
if text.count(old) != 1:
    raise SystemExit("R15 plan execution checkpoint marker mismatch")
text = text.replace(old, new, 1)

old = "## Completion record\n\nTo be appended when accepted.\n\n---\n\n# R15.10 — Base-vs-adapter evaluation, critical-regression veto + candidate disposition"
new = """## Completion record

**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- clean START / normalized R15.8 `main`: `4c1c726301b5a5f798944632336e130ccfb0cbbe`;
- START synchronization preceded implementation and kept R15.10–R15.17 PLANNED;
- immutable technical source: `a964bff54886cafe640fb583610e81055fbe3907`;
- R15.9 QLoRA SFT Acceptance #4 / `33310588740`: SUCCESS Ubuntu + Windows;
- R0 Repository Guard #2146 / `33310588679`: SUCCESS Ubuntu + Windows;
- Python Core #2121 / `33310588722`: SUCCESS 5/5;
- KodeStudio UI Smoke #2086 / `33310588691`: SUCCESS;
- core acceptance installs only `.[dev]`; heavy ML dependencies remain optional and real target-GPU/backend qualification is not claimed;
- deterministic repository-owned fixture training produces canonical cross-platform Safetensors adapter/checkpoint evidence, validates train-only optimization, resume lineage/integrity, mismatch rejection, cancellation/timeout and fail-closed RAM/disk budgets;
- model and tokenizer revisions/digests are separately bound; dataset/manifest/train+validation export lineage is immutable; assistant-only/completion-only loss modes fail closed when their declared dataset/template capability is incompatible;
- manual state: `CONDITIONAL / NOT TRIGGERED`;
- PR #313 carries this technical source; the exact final documented END-head produced by this synchronization must receive fresh R15.9 + R0 Repository Guard + full Python Core + KodeStudio UI Smoke evidence before protected merge. Technical-source evidence above is not reused for that final merge decision.

---

# R15.10 — Base-vs-adapter evaluation, critical-regression veto + candidate disposition"""
if text.count(old) != 1:
    raise SystemExit("R15.9 completion record marker mismatch")
text = text.replace(old, new, 1)
plan.write_text(text, encoding="utf-8", newline="\n")

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = continuity.read_text(encoding="utf-8")
lines = text.splitlines()
old_first = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.8 COMPLETE + NORMALIZED; R15.9 IN_PROGRESS; R15.10–R15.17 PLANNED.** R15.8 normalization PR #312 merged as normalized `main` `4c1c726301b5a5f798944632336e130ccfb0cbbe`; R15.9 START branch `r15/09-qlora-sft` begins from that exact authority. Manual state R15.9: CONDITIONAL / NOT TRIGGERED; core acceptance uses bounded fixture training and does not claim real target-GPU qualification."
new_first = "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. R15.1–R15.8 COMPLETE + NORMALIZED; R15.9 COMPLETE pending final END-head re-gates/merge/normalization; R15.10–R15.17 PLANNED.** R15.9 immutable technical source `a964bff54886cafe640fb583610e81055fbe3907` passed R15.9 #4 / `33310588740`, R0 #2146 / `33310588679`, Python Core #2121 / `33310588722` and UI #2086 / `33310588691` on exact source. Manual state R15.9: CONDITIONAL / NOT TRIGGERED; no real target-GPU/backend qualification is claimed."
if not lines or lines[0] != old_first:
    raise SystemExit("continuity first-line marker mismatch")
lines[0] = new_first

marker_index = next((i for i, line in enumerate(lines) if line.startswith("- R14.1–R14.9 : **COMPLETE + NORMALIZED**.")), None)
if marker_index is None:
    raise SystemExit("continuity insertion marker not found")
if any(line.startswith("- R15.9 :") for line in lines):
    raise SystemExit("R15.9 continuity record already exists")
record = "- R15.9 : **COMPLETE — final END-head re-gates pending** — clean normalized base `4c1c726301b5a5f798944632336e130ccfb0cbbe`; immutable technical source `a964bff54886cafe640fb583610e81055fbe3907`; exact-source R15.9 #4 / `33310588740` SUCCESS Ubuntu + Windows, R0 #2146 / `33310588679` SUCCESS Ubuntu + Windows, Python Core #2121 / `33310588722` SUCCESS 5/5, UI #2086 / `33310588691` SUCCESS. Core fixture training proves canonical cross-platform Safetensors adapter/checkpoint evidence, train-only optimization, resume integrity/lineage and mismatch rejection, cancellation/timeout and fail-closed resource budgets while keeping heavy ML dependencies optional. Real target-GPU/backend qualification remains CONDITIONAL / NOT TRIGGERED. PR #313 must not merge until this documentary END-sync head receives fresh exact-head R15.9/R0/Python/UI gates; R15.10 remains PLANNED and unauthorized until implementation merge plus unique continuity-only normalization complete."
lines.insert(marker_index, record)
continuity.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
