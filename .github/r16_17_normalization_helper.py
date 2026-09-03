from __future__ import annotations

import re
import subprocess
from pathlib import Path

MERGE_SHA = "9ccf3415d8090449001dbdd57cec76248a29af00"
END_SHA = "add9aa4373933a1d66f3c20f9da1fc9314b7a709"
TECHNICAL_SHA = "496d43bf48d23dd9ffe8283e910aa4bcaa1a2cf0"
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

R16_17_RUN = "33799259885"
R16_9_RUN = "33799259616"
R0_RUN = "33799259549"
PYTHON_RUN = "33799259554"
UI_RUN = "33799259784"


def regex_line_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one line match, got {count}")
    return updated


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, got {count}")
    return updated


def normalization_authority() -> str:
    return f"""## R16.17 post-merge normalization authority

- Implementation/evidence merge base: `main` `{MERGE_SHA}`, produced only after final exact-END `{END_SHA}` passed fresh R16.17 #16 / `{R16_17_RUN}` SUCCESS Ubuntu + Windows plus `cross-platform-package-determinism`, R16.9 #71 / `{R16_9_RUN}` SUCCESS Ubuntu + Windows, R0 Repository Guard #2392 / `{R0_RUN}` SUCCESS Ubuntu + Windows, Python Core #2364 / `{PYTHON_RUN}` final SUCCESS 5/5 and KodeStudio UI Smoke #2329 / `{UI_RUN}` SUCCESS. The first Python Core Windows attempt hit one transient R16.16 cleanup `WinError 32`; the isolated exact-head rerun passed without changing source bytes or weakening any gate.
- PR #367 merged with `expected_head_sha={END_SHA}` as implementation/evidence `main` `{MERGE_SHA}`. The final END tree is documentation-only relative to immutable technical source `{TECHNICAL_SHA}`, while the merged R16.17 implementation/evidence bytes are exactly those accepted before END-sync.
- Dedicated normalization branch: `r16/17-continuity-normalization`, created exactly from `{MERGE_SHA}`. The authoritative normalization tree changes only `docs/continuity/KODEPOIA_CONTINUITY.md`; `docs/roadmap/R16_PLAN.md`, all implementation/evidence bytes, workflows, runtime/test bytes and RC package logic remain identical to the implementation/evidence merge. No helper file or helper workflow is present in the normalization decision head.
- Exact-END R16.17 #16 artifacts are Linux `9910534495 / sha256:bb061b4ed29e1e07136e0ce1c9a3765b0a550ee69e0ebf6178c45880699f3992` and Windows `9910560589 / sha256:ec9babd8769063c605a8e415e6b14821374c29a21a6c6eda6f60db281f6dffc8`, both source-bound by GitHub to `{END_SHA}`. Canonical package SHA-256 remains wheel `b4378b6336d8f92e307e81a540e9698fd261dde2c4411fe5c224b16a8ee413e6` and sdist `bfa606908d1a2d34f9d46aaa95acb8087970662d72268e3cd7007987e07fab86`, byte-identical across Linux and Windows.
- This is the single authorized post-merge normalization for R16.17. Its exact candidate head must pass fresh R0 Repository Guard Ubuntu + Windows, Python Core 5/5 and KodeStudio UI Smoke before an exact-head merge. No second R16.17 normalization is permitted.
- Core manual state remains **CONDITIONAL / NOT TRIGGERED**. Production signing, public/store registry publication, production credentials and provider/domain cutover remain `NOT_TRIGGERED` / `NOT_EXERCISED`; no public release occurs through normalization.
- Only the normalized `main` produced by this exact gated normalization merge may authorize R16.18 START. R16.18 remains **PLANNED** until its own documentation-only START-sync is committed from that normalized main before any R16.18 implementation bytes.
"""


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != MERGE_SHA:
        raise SystemExit(f"R16.17 normalization helper must run on {MERGE_SHA}, got {head}")

    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise SystemExit("normalization source tree must be clean")

    text = CONTINUITY.read_text(encoding="utf-8")
    if "## R16.17 post-merge normalization authority" in text:
        raise SystemExit("R16.17 post-merge normalization authority already exists")

    top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + "
        "NORMALIZED. R16.1–R16.17 COMPLETE + NORMALIZED. R16.18 remains PLANNED and unauthorized until this "
        "unique normalization candidate passes fresh R0/Python/UI and merges exact-head.** Final R16.17 END "
        f"`{END_SHA}` passed R16.17 #16 / `{R16_17_RUN}` Ubuntu + Windows plus cross-platform package determinism, "
        f"R16.9 #71 / `{R16_9_RUN}` Ubuntu + Windows, R0 #2392 / `{R0_RUN}` Ubuntu + Windows, Python Core #2364 / "
        f"`{PYTHON_RUN}` final 5/5 and UI #2329 / `{UI_RUN}` before PR #367 merged exact head as implementation/evidence "
        f"`main` `{MERGE_SHA}`. This normalization changes only continuity; its fresh R0 + full Python Core + UI Smoke "
        "and exact-head merge are the sole remaining R16.17 authority before R16.18 START. Core manual state remains "
        "CONDITIONAL / NOT TRIGGERED and no production publication/signing/provider cutover is claimed."
    )
    text = regex_line_once(
        text,
        r"^> Kodepoia, architecture v1\.0 gelée\..*$",
        top,
        "continuity top authority",
    )

    global_line = (
        f"- R16.17 : **COMPLETE + NORMALIZED** — normalized R16.16 base `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; "
        f"clean START `5cbae3c525467c3230d7156649b008e418c3d604`; immutable technical source `{TECHNICAL_SHA}`; final exact-END "
        f"`{END_SHA}` passed fresh R16.17 #16 / `{R16_17_RUN}` SUCCESS Ubuntu + Windows plus cross-platform package "
        f"determinism, R16.9 #71 / `{R16_9_RUN}` SUCCESS Ubuntu + Windows, R0 #2392 / `{R0_RUN}` SUCCESS Ubuntu + "
        f"Windows, Python Core #2364 / `{PYTHON_RUN}` final SUCCESS 5/5 and UI #2329 / `{UI_RUN}` SUCCESS; PR #367 "
        f"merged exact expected head as implementation/evidence `main` `{MERGE_SHA}`. Canonical package SHA-256 remains "
        "wheel `b4378b6336d8f92e307e81a540e9698fd261dde2c4411fe5c224b16a8ee413e6` and sdist "
        "`bfa606908d1a2d34f9d46aaa95acb8087970662d72268e3cd7007987e07fab86`, byte-identical Linux/Windows. "
        "Core manual CONDITIONAL / NOT TRIGGERED; no public release or production credential use occurred. This record "
        "is the unique post-merge continuity-only R16.17 normalization authority when its fresh R0/Python/UI-gated "
        "exact head merges; no second normalization is permitted and R16.18 START is authorized only from that "
        "resulting normalized `main`."
    )
    text = regex_line_once(
        text,
        r"^- R16\.17 : \*\*COMPLETE at END-sync\*\* — .*$",
        global_line,
        "R16.17 global status line",
    )

    text = text.replace(
        "| R16.17 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "| R16.17 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
        1,
    )
    if "| R16.17 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |" not in text:
        raise SystemExit("R16.17 normalized status row missing")

    text = text.replace(
        "\n## R16 status index\n",
        "\n" + normalization_authority() + "\n## R16 status index\n",
        1,
    )
    if text.count("## R16.17 post-merge normalization authority") != 1:
        raise SystemExit("normalization authority insertion failed")

    next_action = (
        "## Next authorized action\n\n"
        f"R16.17 is **COMPLETE + NORMALIZED** in this unique continuity-only normalization record, based on "
        f"implementation/evidence merge `{MERGE_SHA}` from final exact-END `{END_SHA}`. This exact normalization "
        "candidate must now pass fresh R0 Repository Guard Ubuntu + Windows, full Python Core 5/5 and standalone "
        "KodeStudio UI Smoke, then merge only with `expected_head_sha` equal to that successful candidate. **No R16.18 "
        "implementation action is authorized before that normalization merge lands on `main`.** Once it lands, the "
        "resulting normalized `main` is the sole authorized base for an R16.18 documentation-only START-sync; R16.18 "
        "remains PLANNED until that START-sync. Core manual state remains CONDITIONAL / NOT TRIGGERED; production "
        "signing, public/store publication, production credentials and provider/domain cutover remain unexercised.\n\n"
        "## Permanent R-phase execution rule"
    )
    text = regex_once(
        text,
        r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
        next_action,
        "next authorized action",
    )

    CONTINUITY.write_text(text, encoding="utf-8", newline="\n")
    changed = subprocess.check_output(["git", "diff", "--name-only", MERGE_SHA], text=True).splitlines()
    if changed != [str(CONTINUITY)]:
        raise SystemExit(f"unexpected normalization surface: {changed!r}")
    subprocess.run(["git", "diff", "--check"], check=True)


if __name__ == "__main__":
    main()
