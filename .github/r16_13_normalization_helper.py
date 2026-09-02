from __future__ import annotations

import re
from pathlib import Path

BASE_SHA = "38cd16fb7f99eaa46a11d83994a0fe50ce576f80"
END_HEAD = "d002d359715a9e34690a97800d276e776b0ac4a0"
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = CONTINUITY.read_text(encoding="utf-8")

    top_re = re.compile(r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n", re.S)
    top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        "R16.1–R16.13 COMPLETE + NORMALIZED. R16.14–R16.18 remain PLANNED and unauthorized.** R16.13 final exact-END "
        f"head `{END_HEAD}` is tree-identical to END-sync `67aee82d3ac49224a9d8ebf8f82b2913d254507c` after a net-zero user retrigger "
        "and passed fresh R16.13 #7 / `33686092457` SUCCESS Ubuntu + Windows, R16.9 #45 / `33686091948` SUCCESS Ubuntu + Windows, "
        "R0 #2361 / `33686091989` SUCCESS Ubuntu + Windows, Python Core #2333 / `33686092442` SUCCESS 5/5 and KodeStudio UI Smoke #2298 / "
        "`33686092476` SUCCESS. PR #359 merged with exact expected head as implementation/evidence `main` "
        f"`{BASE_SHA}`. This record is the unique post-merge continuity-only R16.13 normalization authority when its exact candidate passes fresh "
        "R0/Python/UI and merges. Only the resulting normalized `main` authorizes R16.14 START-sync. Core manual NONE; optional real local "
        "ComfyUI/GPU qualification remains CONDITIONAL / NOT TRIGGERED.\n\n"
    )
    text, count = top_re.subn(top, text, count=1)
    if count != 1:
        raise SystemExit("top authority anchor mismatch")

    global_re = re.compile(r"^- R16\.13 : \*\*COMPLETE at END-sync\*\* — .*?$", re.M)
    global_line = (
        "- R16.13 : **COMPLETE + NORMALIZED** — normalized R16.12 `main` `86a174ab5d627ca9da8a5eb3979e05951582335b`; "
        "clean START `6c16f115c35817dc96954d923688b4488bde515c`; immutable technical source `ef48343a0967920776a2c9849949f3203f5379b6`; "
        "documentation END-sync `67aee82d3ac49224a9d8ebf8f82b2913d254507c`; final exact-END head "
        f"`{END_HEAD}` is tree-identical after a net-zero user retrigger and passed fresh R16.13 #7 / `33686092457` SUCCESS Ubuntu + Windows, "
        "R16.9 #45 / `33686091948` SUCCESS Ubuntu + Windows, R0 #2361 / `33686091989` SUCCESS Ubuntu + Windows, Python Core #2333 / "
        "`33686092442` SUCCESS 5/5 and UI #2298 / `33686092476` SUCCESS. PR #359 merged with `expected_head_sha="
        f"{END_HEAD}` as implementation/evidence `main` `{BASE_SHA}`. Focused + supply-chain regression remains 31/31 PASS per OS; representative "
        "acceptance remains 12/12 PASS with `security_claim=true`, `critical_veto=false`, `secret_free=true`, zero live credentials, zero destructive host "
        "actions and zero external network calls. Canonical digests remain fixture `703bdfc4383b7b21da105f59622995708b3126d162ee245862a7fe84a54d74ed`; "
        "workflow `c359e0505cf1809ad21c1b78749c0a4a5ad235545e3c6872fdd613723c7313c4`; prompt `927a95793dc85ed78ab19a831c5a9b6ac126884e2b1a38511f17317ebf68999b`; "
        "budget `68895e08ad203e0aced0b784065ab1fb08a97d7d1cc2a21586b4b165905aa7c3`; output `1a28b874c6e2c8cf8b02a1aede34837bf8ce7576eba1abcc377ee655d459eadb`; "
        "binding `2b67d1c077340e9eae70afe45f70208d38db92f052019adb8bb0b87202f04df5`; semantic `d149b518d08bf16f864a7f940ebca13071ae63a888ff08e7b4719c8d7a2247b5`. "
        "Fixture is synthetic; real ComfyUI/GPU remains `NOT_EXERCISED`; core manual NONE; optional live qualification CONDITIONAL / NOT TRIGGERED. "
        "This record is the unique post-merge continuity-only R16.13 normalization authority when its exact candidate passes fresh R0/Python/UI and "
        "merges. R16.14 START-sync is authorized only from the resulting normalized `main`."
    )
    text, count = global_re.subn(global_line, text, count=1)
    if count != 1:
        raise SystemExit("global R16.13 anchor mismatch")

    normalization_authority = f"""## R16.13 post-merge normalization authority

- Implementation/evidence PR #359 merged final exact-END head `{END_HEAD}` with exact `expected_head_sha` as `main` `{BASE_SHA}`.
- Final exact-END gates were R16.13 #7 / `33686092457` SUCCESS Ubuntu + Windows; R16.9 #45 / `33686091948` SUCCESS Ubuntu + Windows; R0 #2361 / `33686091989` SUCCESS Ubuntu + Windows; Python Core #2333 / `33686092442` SUCCESS 5/5; KodeStudio UI Smoke #2298 / `33686092476` SUCCESS.
- This branch is the one authorized post-merge R16.13 normalization and may change only `docs/continuity/KODEPOIA_CONTINUITY.md` relative to `{BASE_SHA}`.
- Its exact candidate must pass fresh R0 Repository Guard, Python Core and KodeStudio UI Smoke before merge with exact `expected_head_sha`.
- After that exact normalization merge, and only then, the resulting `main` is the normalized R16.13 authority and R16.14 START-sync becomes authorized. No R16.14 implementation may precede its START-sync.
- Core manual state remains **NONE**. Optional true local ComfyUI/GPU qualification remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`.

"""
    text = replace_once(
        text,
        "## R16 status index\n",
        normalization_authority + "## R16 status index\n",
        "R16 status index heading",
    )

    text = replace_once(
        text,
        "| R16.13 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "| R16.13 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
        "R16.13 status row",
    )

    next_re = re.compile(r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule", re.S)
    next_text = (
        "## Next authorized action\n\n"
        f"R16.13 implementation/evidence PR #359 has merged exact END head `{END_HEAD}` as `main` `{BASE_SHA}`. The sole active authority is now "
        "the continuity-only branch `r16/13-continuity-normalization`. Its exact candidate must pass fresh R0 Repository Guard, Python Core and "
        "KodeStudio UI Smoke and merge with exact `expected_head_sha`. Only the resulting normalized `main` authorizes **R16.14 START-sync**; "
        "R16.14 implementation remains unauthorized until that START-sync is committed. Core manual **NONE**; optional real local ComfyUI/GPU "
        "qualification remains **CONDITIONAL / NOT TRIGGERED**.\n\n"
        "## Permanent R-phase execution rule"
    )
    text, count = next_re.subn(next_text, text, count=1)
    if count != 1:
        raise SystemExit("next authorized action anchor mismatch")

    if "R16.13 COMPLETE at END-sync" in text.split("\n\n", 1)[0]:
        raise SystemExit("stale top R16.13 END state remains")
    if "| R16.13 | COMPLETE | CONDITIONAL / NOT TRIGGERED |" in text:
        raise SystemExit("stale R16.13 table row remains")

    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
