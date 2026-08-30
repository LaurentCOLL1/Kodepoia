from pathlib import Path

path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = path.read_text(encoding="utf-8")
lines = text.splitlines()

start_sha = "097e99db28508cd1c53eadfe00b2b33576a445af"
technical_sha = "ae856396faa964fee19ee39e461bc7de4e775cd9"
final_sha = "5f832be8ffc996514736dc7e0567555930f53d85"
merge_sha = "ae7bbe7ee81221e788c6ed996c547e4c11272932"

lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. "
    "R15 planning ACCEPTED + NORMALIZED. R15.1–R15.6 COMPLETE + NORMALIZED; "
    "R15.7–R15.17 PLANNED.** R15.6 clean START `" + start_sha + "`; immutable technical source `"
    + technical_sha + "`; final sealed END-head `" + final_sha
    + "` passed R15.6 #13 / `33298371733` SUCCESS Ubuntu + Windows, R0 #2130 / `33298371714` "
    "SUCCESS Ubuntu + Windows, Python Core #2105 / `33298371667` SUCCESS 5/5 and UI #2070 / "
    "`33298371724` SUCCESS; PR #307 merged only with `expected_head_sha=" + final_sha + "` as `"
    + merge_sha + "`. This branch is the unique continuity-only R15.6 post-merge normalization candidate; "
    "only fresh exact-head R0/Python/UI SUCCESS and expected-head merge authorize R15.7. Manual NONE."
)

r15_6_entry = (
    "- R15.6 : **COMPLETE + NORMALIZED** — clean START / branch point `" + start_sha
    + "`; immutable technical source `" + technical_sha + "`; technical R15.6 #2 / `33295649414` SUCCESS "
    "Ubuntu + Windows, R0 #2124 / `33295649494` SUCCESS Ubuntu + Windows, Python #2099 / `33295649527` "
    "SUCCESS 5/5 and UI #2064 / `33295649458` SUCCESS; END authority truthfully records the START-plan "
    "checkpoint repair; final sealed END-head `" + final_sha + "` passed fresh R15.6 #13 / `33298371733` "
    "SUCCESS Ubuntu + Windows, R0 #2130 / `33298371714` SUCCESS Ubuntu + Windows, Python Core #2105 / "
    "`33298371667` SUCCESS 5/5 and UI #2070 / `33298371724` SUCCESS; PR #307 merged with exact expected "
    "head as `" + merge_sha + "`; manual NONE. This record is the unique post-merge continuity-only R15.6 "
    "normalization candidate; R15.7 START-sync is authorized only after fresh exact-head R0/Python/UI on "
    "this branch and expected-head merge to `main`."
)

entry_count = 0
row_count = 0
next_count = 0
for index, line in enumerate(lines):
    if line.startswith("- R15.6 :"):
        lines[index] = r15_6_entry
        entry_count += 1
    if line.startswith("| R15.6 |"):
        lines[index] = "| R15.6 | COMPLETE + NORMALIZED | NONE |"
        row_count += 1
    if line == "## Next authorized action":
        for candidate in range(index + 1, min(index + 6, len(lines))):
            if lines[candidate].startswith("**"):
                lines[candidate] = (
                    "**R15.6 implementation/evidence is merged as `" + merge_sha
                    + "`. This branch is the unique continuity-only post-merge normalization: require fresh exact-head "
                    "R0 Repository Guard + full Python Core + KodeStudio UI Smoke, then merge only with "
                    "`expected_head_sha`. Only the resulting normalized `main` authorizes R15.7 START-sync; "
                    "`docs/roadmap/R15_PLAN.md` must not change.**"
                )
                next_count += 1
                break

if entry_count != 1 or row_count != 1 or next_count != 1:
    raise SystemExit(
        f"normalization marker mismatch: entry={entry_count} row={row_count} next={next_count}"
    )

path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
