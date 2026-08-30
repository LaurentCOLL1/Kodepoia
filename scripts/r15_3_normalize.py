from pathlib import Path

merge_sha = "4b37d7735194e9b4b21899d44ad4224c418979ed"
end_sha = "3a41e703bdedaf613e88dc672bee1b8ca01b62ff"
technical = "e049a8f5c8155accb1d64ca4028deec5f85c4aa8"
start = "ba719dd9d556909b08606d6c7ebb4d4ef18dbd37"

path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
lines = path.read_text(encoding="utf-8").splitlines()
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. "
    "R15 planning ACCEPTED + NORMALIZED. R15.1–R15.3 COMPLETE + NORMALIZED; "
    "R15.4–R15.17 PLANNED.** R15.3 immutable technical source "
    f"`{technical}`; final END-head `{end_sha}`; exact-END R15.3 #19 / `33283462348`, "
    "R0 #2088 / `33283462344`, Python #2063 / `33283462455`, UI #2028 / "
    f"`33283462377` SUCCESS; PR #300 merged exact head as `{merge_sha}`; manual NONE. "
    "This record is the unique post-merge continuity-only R15.3 normalization authority; "
    "only its merged normalized `main` authorizes R15.4 START-sync."
)
idx = next(i for i, line in enumerate(lines) if line.startswith("- R15.3 : **COMPLETE — IMPLEMENTATION MERGE PENDING**"))
lines[idx] = (
    f"- R15.3 : **COMPLETE + NORMALIZED** — clean START `{start}`; immutable technical source "
    f"`{technical}`; final END-head `{end_sha}`; exact-END R15.3 #19 / `33283462348` "
    "SUCCESS Ubuntu + Windows, R0 #2088 / `33283462344` SUCCESS, Python #2063 / "
    "`33283462455` SUCCESS 5/5, UI #2028 / `33283462377` SUCCESS; PR #300 merged "
    f"with `expected_head_sha={end_sha}` as `{merge_sha}`; manual NONE. Sanitization remains "
    "deterministic/non-laundering, license/provenance/privacy fail closed, and revocation "
    "lineage-aware. This is the unique post-merge continuity-only normalization authority; "
    "R15.4 is authorized only after this normalization branch passes fresh R0/Python/UI and merges."
)
next_idx = next(i for i, line in enumerate(lines) if line.startswith("**R15.3 END-sync is complete"))
lines[next_idx] = (
    "**R15.3 normalization is staged continuity-only. Require fresh exact-head R0 Repository Guard + "
    "full Python Core + KodeStudio UI Smoke, merge with `expected_head_sha`, then start R15.4 from "
    "that normalized `main`. R15.4 remains unauthorized before this merge.**"
)
path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
