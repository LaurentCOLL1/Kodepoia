from pathlib import Path

normalized_main = "9ef6f704d54332203e820cd2bd85e3b4ac86910a"
r15_6_merge = "ae7bbe7ee81221e788c6ed996c547e4c11272932"
r15_6_norm_head = "8757274943eafc901ad6a0ca3776ddfdb94133c7"

plan = Path("docs/roadmap/R15_PLAN.md")
text = plan.read_text(encoding="utf-8")
lines = text.splitlines()
checkpoint_count = 0
r156_count = 0
r157_count = 0
for index, line in enumerate(lines):
    if line.startswith("**Execution checkpoint:**"):
        lines[index] = (
            "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. "
            "R15.1–R15.6 are COMPLETE + NORMALIZED. R15.7 is IN_PROGRESS on dedicated branch "
            "`r15/07-gap-diagnosis-train-decision` from normalized R15.6 `main` `" + normalized_main + "`; "
            "R15.8–R15.17 remain PLANNED."
        )
        checkpoint_count += 1
    if line.startswith("| R15.6 |"):
        parts = line.split("|")
        parts[3] = " COMPLETE + NORMALIZED "
        lines[index] = "|".join(parts)
        r156_count += 1
    if line.startswith("| R15.7 |"):
        parts = line.split("|")
        parts[3] = " IN_PROGRESS "
        lines[index] = "|".join(parts)
        r157_count += 1
if (checkpoint_count, r156_count, r157_count) != (1, 1, 1):
    raise SystemExit(
        f"plan START markers mismatch: checkpoint={checkpoint_count} r15.6={r156_count} r15.7={r157_count}"
    )
plan.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = continuity.read_text(encoding="utf-8")
lines = text.splitlines()
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. "
    "R15.1–R15.6 COMPLETE + NORMALIZED; R15.7 IN_PROGRESS; R15.8–R15.17 PLANNED.** "
    "R15.6 implementation/evidence merge `" + r15_6_merge + "`; unique continuity-only normalization head `"
    + r15_6_norm_head + "` passed R0 #2132 / `33298606947` SUCCESS Ubuntu + Windows, Python Core #2107 / "
    "`33298606982` SUCCESS 5/5 and UI #2072 / `33298606874` SUCCESS, then normalization PR #308 merged "
    "with exact expected head as normalized `main` `" + normalized_main + "`. R15.7 START is authorized from "
    "that exact main. Manual NONE."
)
entry_count = 0
row_count = 0
next_count = 0
for index, line in enumerate(lines):
    if line.startswith("- R15.6 :"):
        lines[index] = (
            "- R15.6 : **COMPLETE + NORMALIZED** — implementation/evidence merge `" + r15_6_merge
            + "`; unique post-merge normalization head `" + r15_6_norm_head
            + "` passed R0 #2132 / `33298606947` SUCCESS Ubuntu + Windows, Python Core #2107 / "
            "`33298606982` SUCCESS 5/5 and UI #2072 / `33298606874` SUCCESS; normalization PR #308 merged "
            "with exact expected head as normalized `main` `" + normalized_main
            + "`; manual NONE. R15.7 START is authorized only from that exact normalized main."
        )
        entry_count += 1
    if line.startswith("| R15.7 |"):
        lines[index] = "| R15.7 | IN_PROGRESS | NONE |"
        row_count += 1
    if line == "## Next authorized action":
        for candidate in range(index + 1, min(index + 6, len(lines))):
            if lines[candidate].startswith("**"):
                lines[candidate] = (
                    "**R15.7 START-sync is the active authority on `r15/07-gap-diagnosis-train-decision`, based "
                    "exactly on normalized R15.6 `main` `" + normalized_main + "`. Implement only the frozen gap "
                    "diagnosis and governed TRAIN/NO_TRAIN decision engine after this START synchronization; no "
                    "training execution is authorized in R15.7. R15.8 remains unauthorized until R15.7 completes, "
                    "merges and receives its unique post-merge continuity-only normalization. Manual NONE.**"
                )
                next_count += 1
                break
if (entry_count, row_count, next_count) != (1, 1, 1):
    raise SystemExit(
        f"continuity START markers mismatch: entry={entry_count} row={row_count} next={next_count}"
    )
continuity.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
