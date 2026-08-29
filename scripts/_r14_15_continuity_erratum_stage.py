from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = PATH.read_text(encoding="utf-8")

replacements = [
    (
        "R14.15 implementation MERGED; the unique post-merge continuity-only normalization is pending. R14.16–R14.17 remain PLANNED and unauthorized.",
        "R14.15 COMPLETE + NORMALIZED. R14.16–R14.17 remain PLANNED; R14.16 START-sync is authorized from normalized main `1f10d7a13f49cb6e931e5e0694f083228ed24070`.",
    ),
    (
        "The only authorized next action is the unique continuity-only normalization with fresh exact-head R0/Python/UI; R14.16 remains unauthorized until that normalization merges.",
        "The unique continuity-only normalization is complete: head `68a6f106484ab60d9925dfcc60189b509d995393` passed fresh exact-head R0 #1973 / `33257784369`, Python Core #1948 / `33257784390`, and UI #1913 / `33257784370`; PR #286 merged with exact expected-head protection as normalized main `1f10d7a13f49cb6e931e5e0694f083228ed24070`. The next authorized action is R14.16 START-sync from that exact normalized main.",
    ),
    (
        "- R14.15 : **IMPLEMENTATION MERGED / NORMALIZATION PENDING** — immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; END-head `80bd6853664ab9f41fd41fb83f43b43980bef394`; PR #285 merge `53373e78c60d4a338e9313496a822c93ab334e68`; manual `CONDITIONAL / NOT TRIGGERED`.",
        "- R14.15 : **COMPLETE + NORMALIZED** — immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; END-head `80bd6853664ab9f41fd41fb83f43b43980bef394`; PR #285 merge `53373e78c60d4a338e9313496a822c93ab334e68`; unique normalization head `68a6f106484ab60d9925dfcc60189b509d995393`; normalized `main` `1f10d7a13f49cb6e931e5e0694f083228ed24070` via PR #286 after fresh R0 #1973 / `33257784369`, Python Core #1948 / `33257784390`, and UI #1913 / `33257784370` SUCCESS; manual `CONDITIONAL / NOT TRIGGERED`.",
    ),
    (
        "| R14.15 | IMPLEMENTATION MERGED / NORMALIZATION PENDING | CONDITIONAL / NOT TRIGGERED |",
        "| R14.15 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
    ),
    (
        "- R14.15 is **technically COMPLETE and implementation-merged**. Clean END-head `80bd6853664ab9f41fd41fb83f43b43980bef394` passed fresh exact-head R0/Python/UI/R14 Resilience gates and PR #285 merged with exact expected-head protection as `53373e78c60d4a338e9313496a822c93ab334e68`. R14.15 remains unnormalized and R14.16 remains unauthorized until the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.",
        "- R14.15 is **COMPLETE + NORMALIZED**. Clean END-head `80bd6853664ab9f41fd41fb83f43b43980bef394` passed fresh exact-head R0/Python/UI/R14 Resilience gates and PR #285 merged with exact expected-head protection as `53373e78c60d4a338e9313496a822c93ab334e68`. The unique continuity-only normalization head `68a6f106484ab60d9925dfcc60189b509d995393` passed fresh exact-head R0/Python/UI and PR #286 merged with exact expected-head protection as normalized `main` `1f10d7a13f49cb6e931e5e0694f083228ed24070`. R14.16 START-sync is authorized from that exact normalized main.",
    ),
    (
        "- The sole remaining R14.15 action is exactly one continuity-only normalization commit from implementation merge `53373e78c60d4a338e9313496a822c93ab334e68`, followed by fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke, then an `expected_head_sha` merge. No plan or technical file may change during normalization.",
        "- Unique post-merge normalization head `68a6f106484ab60d9925dfcc60189b509d995393` changed only this continuity file; fresh exact-head R0 Repository Guard #1973 / `33257784369`, Python Core #1948 / `33257784390` (5/5), and KodeStudio UI Smoke #1913 / `33257784370` all SUCCESS. PR #286 merged with `expected_head_sha=68a6f106484ab60d9925dfcc60189b509d995393` as normalized `main` `1f10d7a13f49cb6e931e5e0694f083228ed24070`. Normalization cardinality is exactly one; this post-merge erratum only corrects stale continuity wording and is not a second normalization.",
    ),
    (
        "Validate and merge the unique R14.15 continuity-only normalization candidate. Its diff from implementation merge `53373e78c60d4a338e9313496a822c93ab334e68` must contain only `docs/continuity/KODEPOIA_CONTINUITY.md`; fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke must all succeed before merge. Only the resulting normalized `main` authorizes R14.16 START-sync. R14.16–R14.17 remain PLANNED until then.",
        "Start R14.16 from exact normalized `main` `1f10d7a13f49cb6e931e5e0694f083228ed24070`: create its dedicated branch, perform the mandatory START-sync with R14.1–R14.15 COMPLETE + NORMALIZED, R14.16 IN_PROGRESS and R14.17 PLANNED, then implement and gate R14.16 according to `docs/roadmap/R14_PLAN.md`. R14.17 remains PLANNED and unauthorized until R14.16 completes and normalizes.",
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one match, found {count}: {old[:120]!r}")
    text = text.replace(old, new)

stale = [
    "normalization is pending",
    "IMPLEMENTATION MERGED / NORMALIZATION PENDING",
    "remains unnormalized",
    "sole remaining R14.15 action",
    "Validate and merge the unique R14.15 continuity-only normalization candidate",
]
for marker in stale:
    if marker in text:
        raise SystemExit(f"Stale continuity marker survives: {marker!r}")

if text.count("68a6f106484ab60d9925dfcc60189b509d995393") < 3:
    raise SystemExit("Normalization head not recorded consistently")
if text.count("1f10d7a13f49cb6e931e5e0694f083228ed24070") < 4:
    raise SystemExit("Normalized main not recorded consistently")

PATH.write_text(text, encoding="utf-8", newline="\n")
