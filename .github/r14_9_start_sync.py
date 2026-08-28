from pathlib import Path

path = Path("docs/roadmap/R14_PLAN.md")
text = path.read_text(encoding="utf-8")
old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.7 are COMPLETE + NORMALIZED. R14.7 implementation/evidence PR #269 merged as `763ce96c4f82da2eaec167b56ffb62d9e548b300`; its single continuity-only normalization PR #270 merged as normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after R0 #1810, Python Core #1784 and UI #1751, all SUCCESS. R14.8 technical source `8132c4029983f693a32e0d26903d05e347313bf6` is accepted after R0 #1822, Python Core #1796, UI #1763 and R14 Cloud Save Acceptance #6, all SUCCESS. R14.8 is COMPLETE at END-sync; final exact-head re-gates, protected merge and the single continuity-only normalization remain required. R14.9–R14.17 remain PLANNED. R14.8 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.8 are COMPLETE + NORMALIZED. R14.8 immutable technical source `8132c4029983f693a32e0d26903d05e347313bf6`; accepted END-head `954991537fc8c076169993ea106303421b8edd60`; PR #271 merged with expected-head as `5b51967c63ad5ae5ccc2df89f76aa48831ee2762`; single continuity-only normalization PR #272 passed R0 #1834, Python Core #1808 and UI #1775 and merged as normalized `main` `433c86cc5d43bfea41adb529451367e10c75a30b`. R14.9 is IN_PROGRESS on `r14/09-progression-leaderboards`; R14.10–R14.17 remain PLANNED. R14.9 manual state is NONE."
assert text.count(old_checkpoint) == 1, text.count(old_checkpoint)
text = text.replace(old_checkpoint, new_checkpoint)
old_row = "| R14.9 | Achievements, stats, leaderboards + authoritative progression | PLANNED | NONE | R14.5–R14.6 |"
new_row = "| R14.9 | Achievements, stats, leaderboards + authoritative progression | IN_PROGRESS | NONE | R14.5–R14.6 |"
assert text.count(old_row) == 1, text.count(old_row)
text = text.replace(old_row, new_row)
path.write_text(text, encoding="utf-8")
