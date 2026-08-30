from pathlib import Path

normalized = "ffb5a830cce35334b3f62e69fae2e2c02c717080"
normalization_head = "db823f11fbc04007b304810fb94aa300fc8ddc48"

plan = Path("docs/roadmap/R15_PLAN.md")
text = plan.read_text(encoding="utf-8")
old = "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.2 are COMPLETE + NORMALIZED. R15.3 is COMPLETE with immutable technical source `e049a8f5c8155accb1d64ca4028deec5f85c4aa8`; implementation merge + unique post-merge continuity-only normalization are pending. R15.4–R15.17 remain PLANNED."
new = f"**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.3 are COMPLETE + NORMALIZED; normalized R15.3 `main` is `{normalized}`. R15.4 is IN_PROGRESS on dedicated branch `r15/04-dedup-contamination`; R15.5–R15.17 remain PLANNED."
assert text.count(old) == 1
text = text.replace(old, new, 1)
old_row = "| R15.4 | Exact/near deduplication, benchmark-contamination firewall + quarantine | PLANNED | NONE | R15.1–R15.3 |"
assert text.count(old_row) == 1
text = text.replace(old_row, old_row.replace(" | PLANNED | ", " | IN_PROGRESS | "), 1)
# Synchronize the R15.3 completion record now that its merge+normalization are authoritative.
marker = "# R15.3 — Sanitization, secret/privacy filtering, license/provenance policy + revocation"
pos = text.index(marker)
next_pos = text.index("# R15.4 — Exact/near deduplication", pos)
section = text[pos:next_pos]
old_completion = "## Completion record\n\nTo be appended when accepted."
assert section.count(old_completion) == 1
new_completion = """## Completion record

**COMPLETE + NORMALIZED.**

- clean START-head: `ba719dd9d556909b08606d6c7ebb4d4ef18dbd37`;
- immutable technical source: `e049a8f5c8155accb1d64ca4028deec5f85c4aa8`;
- final END-head: `3a41e703bdedaf613e88dc672bee1b8ca01b62ff`;
- exact-END R15.3 #19 / `33283462348`: SUCCESS Ubuntu + Windows;
- R0 #2088 / `33283462344`: SUCCESS Ubuntu + Windows;
- Python Core #2063 / `33283462455`: SUCCESS 5/5;
- KodeStudio UI Smoke #2028 / `33283462377`: SUCCESS;
- PR #300 merged with protected exact head as `4b37d7735194e9b4b21899d44ad4224c418979ed`;
- post-merge normalization head `db823f11fbc04007b304810fb94aa300fc8ddc48`: R0 #2090 / `33283698522`, Python #2065 / `33283698570`, UI #2030 / `33283698532` SUCCESS; normalization PR #301 -> normalized `main` `ffb5a830cce35334b3f62e69fae2e2c02c717080`;
- manual state: `NONE`.
"""
section = section.replace(old_completion, new_completion, 1)
text = text[:pos] + section + text[next_pos:]
plan.write_text(text, encoding="utf-8", newline="\n")

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
lines = continuity.read_text(encoding="utf-8").splitlines()
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. "
    "R15.1–R15.3 COMPLETE + NORMALIZED; R15.4 IN_PROGRESS; R15.5–R15.17 PLANNED.** "
    f"R15.4 clean branch point is normalized R15.3 `main` `{normalized}`; dedicated branch "
    "`r15/04-dedup-contamination`; manual NONE. Exact/near dedup and benchmark contamination remain "
    "fail-closed; protected holdout content must never leak into reports."
)
idx = next(i for i, line in enumerate(lines) if line.startswith("- R15.3 : **COMPLETE + NORMALIZED**"))
lines[idx] = (
    "- R15.3 : **COMPLETE + NORMALIZED** — clean START `ba719dd9d556909b08606d6c7ebb4d4ef18dbd37`; "
    "immutable technical source `e049a8f5c8155accb1d64ca4028deec5f85c4aa8`; final END-head "
    "`3a41e703bdedaf613e88dc672bee1b8ca01b62ff`; exact-END R15.3 #19 / `33283462348`, "
    "R0 #2088 / `33283462344`, Python #2063 / `33283462455`, UI #2028 / `33283462377` SUCCESS; "
    "PR #300 merge `4b37d7735194e9b4b21899d44ad4224c418979ed`; normalization head "
    f"`{normalization_head}` passed R0 #2090 / `33283698522`, Python #2065 / `33283698570`, UI #2030 / "
    f"`33283698532`; normalization PR #301 -> normalized `main` `{normalized}`; manual NONE."
)
lines.insert(idx + 1, f"- R15.4 : **IN_PROGRESS** — clean branch point `{normalized}`; branch `r15/04-dedup-contamination`; START-sync only, no implementation precedes this state; manual NONE.")
status = next(i for i, line in enumerate(lines) if line == "| R15.4 | PLANNED | NONE |")
lines[status] = "| R15.4 | IN_PROGRESS | NONE |"
action = next(i for i, line in enumerate(lines) if line.startswith("**R15.3 normalization is staged continuity-only."))
lines[action] = (
    "**R15.4 START-sync is active on `r15/04-dedup-contamination` from normalized `main` "
    f"`{normalized}`. Implement exact/near deduplication, protected-holdout contamination firewall, "
    "quarantine and deterministic group identity; require focused/adversarial tests plus exact-head R0/Python/UI before END-sync.**"
)
continuity.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
