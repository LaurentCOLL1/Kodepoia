from __future__ import annotations

import re
import subprocess
from pathlib import Path

BASE_SHA = "41706493d974799b7011953e584b887ca6db1996"
NORMALIZATION_CANDIDATE = "12aaecf1c49bf55453797e67e47df4540510305f"
R16_17_END = "add9aa4373933a1d66f3c20f9da1fc9314b7a709"
R16_17_MERGE = "9ccf3415d8090449001dbdd57cec76248a29af00"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

R0_RUN = "33800330466"
PYTHON_RUN = "33800330339"
UI_RUN = "33800330429"


def line_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"{label}: expected one line, got {count}")
    return updated


def block_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected one block, got {count}")
    return updated


def start_authority() -> str:
    return f"""## R16.18 START authority

- State: **IN_PROGRESS**; core integrated acceptance manual state **NONE**. Optional live-capability evidence remains **CONDITIONAL / NOT TRIGGERED** and may become manual only if an optional real GPU/listening/device/production-signing/publication claim is explicitly requested.
- Exact normalized R16.17 base: `main` `{BASE_SHA}`; dedicated branch `r16/18-integrated-adversarial-real-project-rc-acceptance` created directly from that SHA before implementation.
- R16.17 final exact-END `{R16_17_END}` passed R16.17 #16 / `33799259885` Ubuntu + Windows plus `cross-platform-package-determinism`, R16.9 #71 / `33799259616` Ubuntu + Windows, R0 #2392 / `33799259549` Ubuntu + Windows, Python Core #2364 / `33799259554` final 5/5 and KodeStudio UI Smoke #2329 / `33799259784`; PR #367 merged exact head as implementation/evidence `main` `{R16_17_MERGE}`.
- Unique R16.17 normalization candidate `{NORMALIZATION_CANDIDATE}` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #2394 / `{R0_RUN}` Ubuntu + Windows, Python Core #2366 / `{PYTHON_RUN}` 5/5 and KodeStudio UI Smoke #2331 / `{UI_RUN}`, then PR #372 merged with exact expected head as normalized `main` `{BASE_SHA}`. No second R16.17 normalization is authorized.
- Prior state: R16.1–R16.17 **COMPLETE + NORMALIZED**. R16.18 is the sole active subdivision and the frozen subdivision set remains unchanged.
- Frozen R16.18 scope is unchanged: independently freeze the integrated case/project set; re-run critical R16.1–R16.9 adversarial/recovery/security cases from clean state on one exact source; re-run representative Godot 2D/3D, Windows, ComfyUI fixture, media and long-term workflows; include resource-soak and RC package/provenance linkage; fail closed on any critical failure, unauthorized skip, stale/mixed-SHA evidence or unverifiable binding; preserve truthful `UNAVAILABLE` / `NOT_EXERCISED` outcomes for non-core optional capabilities.
- Core R16.18 acceptance remains CI-owned, synthetic/bounded where external live capability is not required, non-destructive, network-independent for core verdicts and free of live production credentials. Earlier subdivision PASS reports are informative only; final critical verdicts must be re-executed or independently verified against the exact R16.18 source according to the frozen plan.
- No R16.18 implementation bytes precede this START-sync. No v1.0 public release, production signing, store/public registry publication or provider/domain cutover is authorized by this START.
"""


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != BASE_SHA:
        raise SystemExit(f"R16.18 START helper must run on {BASE_SHA}, got {head}")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise SystemExit("R16.18 START source must be clean")

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")
    if "## R16.18 START authority" in plan or "## R16.18 START authority" in continuity:
        raise SystemExit("R16.18 START authority already exists")

    checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        f"R16.1–R16.17 are COMPLETE + NORMALIZED on exact normalized `main` `{BASE_SHA}`. R16.18 is IN_PROGRESS "
        "on dedicated branch `r16/18-integrated-adversarial-real-project-rc-acceptance` created directly from that "
        f"SHA before implementation. R16.17 normalization candidate `{NORMALIZATION_CANDIDATE}` passed R0 #2394 / "
        f"`{R0_RUN}` Ubuntu + Windows, Python Core #2366 / `{PYTHON_RUN}` 5/5 and UI #2331 / `{UI_RUN}`, then PR #372 "
        f"merged exact head as normalized `main` `{BASE_SHA}`. R16.18 core acceptance is CI-owned; optional live "
        "capability/manual evidence remains CONDITIONAL / NOT TRIGGERED. No R16.18 implementation bytes precede "
        "this START-sync and no public release is authorized by it."
    )
    plan = line_once(plan, r"^\*\*Execution checkpoint:\*\*.*$", checkpoint, "plan checkpoint")
    plan = line_once(
        plan,
        r"^\| R16\.18 \| Integrated adversarial \+ real-project RC acceptance \| PLANNED \| CONDITIONAL \|$",
        "| R16.18 | Integrated adversarial + real-project RC acceptance | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.18 row",
    )
    plan = plan.replace(
        "\n---\n\n## Planning acceptance and authorization boundary",
        "\n" + start_authority() + "\n---\n\n## Planning acceptance and authorization boundary",
        1,
    )
    if plan.count("## R16.18 START authority") != 1:
        raise SystemExit("plan START insertion failed")
    PLAN.write_text(plan, encoding="utf-8", newline="\n")

    top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + NORMALIZED. "
        f"R16.1–R16.17 COMPLETE + NORMALIZED on `main` `{BASE_SHA}`. R16.18 IN_PROGRESS on its dedicated branch "
        "after a documentation-only START-sync; no implementation precedes START.** R16.17 normalization candidate "
        f"`{NORMALIZATION_CANDIDATE}` passed R0 #2394 / `{R0_RUN}` Ubuntu + Windows, Python Core #2366 / `{PYTHON_RUN}` "
        f"5/5 and UI #2331 / `{UI_RUN}`, then PR #372 merged exact head as normalized `main` `{BASE_SHA}`. R16.18 "
        "core integrated acceptance is CI-owned; optional live-capability/manual evidence remains CONDITIONAL / NOT "
        "TRIGGERED, and no public release/signing/provider cutover is authorized by START."
    )
    continuity = line_once(
        continuity,
        r"^> Kodepoia, architecture v1\.0 gelée\..*$",
        top,
        "continuity top",
    )

    definitive_r16_17 = (
        f"- R16.17 : **COMPLETE + NORMALIZED** — final exact-END `{R16_17_END}` passed R16.17 #16 / `33799259885` "
        "3/3, R16.9 #71 / `33799259616` 2/2, R0 #2392 / `33799259549` 2/2, Python Core #2364 / "
        f"`33799259554` final 5/5 and UI #2329 / `33799259784`; PR #367 merged exact head as `{R16_17_MERGE}`. "
        f"Unique continuity-only normalization `{NORMALIZATION_CANDIDATE}` passed R0 #2394 / `{R0_RUN}` 2/2, Python "
        f"Core #2366 / `{PYTHON_RUN}` 5/5 and UI #2331 / `{UI_RUN}`, then PR #372 merged exact head as normalized "
        f"`main` `{BASE_SHA}`. Canonical RC packages remain byte-identical Linux/Windows: wheel "
        "`b4378b6336d8f92e307e81a540e9698fd261dde2c4411fe5c224b16a8ee413e6`, sdist "
        "`bfa606908d1a2d34f9d46aaa95acb8087970662d72268e3cd7007987e07fab86`. Core manual CONDITIONAL / NOT "
        "TRIGGERED; optional production actions remain NOT_TRIGGERED/NOT_EXERCISED. No second R16.17 normalization "
        "is authorized."
    )
    r16_18_line = (
        f"- R16.18 : **IN_PROGRESS** — exact normalized R16.17 base `main` `{BASE_SHA}`; dedicated branch "
        "`r16/18-integrated-adversarial-real-project-rc-acceptance` created directly from that SHA before implementation; "
        "frozen integrated adversarial + representative-project RC scope unchanged; core CI acceptance requires no "
        "manual action, optional live capability claims remain CONDITIONAL / NOT TRIGGERED; no R16.18 implementation "
        "bytes precede START-sync."
    )
    continuity = line_once(
        continuity,
        r"^- R16\.17 : \*\*COMPLETE \+ NORMALIZED\*\* — .*$",
        definitive_r16_17 + "\n" + r16_18_line,
        "continuity R16.17/R16.18 global lines",
    )
    continuity = line_once(
        continuity,
        r"^\| R16\.18 \| PLANNED \| CONDITIONAL \|$",
        "| R16.18 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "continuity R16.18 row",
    )
    continuity = continuity.replace(
        "\n## R16 status index\n",
        "\n" + start_authority() + "\n## R16 status index\n",
        1,
    )
    if continuity.count("## R16.18 START authority") != 1:
        raise SystemExit("continuity START insertion failed")

    next_action = (
        "## Next authorized action\n\n"
        f"R16.18 is **IN_PROGRESS** from exact normalized R16.17 `main` `{BASE_SHA}` and this documentation-only "
        "START authority. The next authorized action is R16.18 implementation on the dedicated branch: freeze the "
        "independent integrated case/project set, implement the non-circular exact-source runner/report/workflow, and "
        "re-execute the frozen critical adversarial/recovery/security and representative-project claims rather than "
        "importing earlier PASS verdicts. Core acceptance remains CI-owned; optional real GPU/listening/device/signing/"
        "publication claims remain CONDITIONAL / NOT TRIGGERED. Final phase completion still requires exact-technical "
        "and exact-END R16 Integrated/R0/Python/UI authority, exact-head implementation merge, then exactly one "
        "continuity-only R16 phase normalization.\n\n"
        "## Permanent R-phase execution rule"
    )
    continuity = block_once(
        continuity,
        r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
        next_action,
        "continuity next action",
    )
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")

    changed = sorted(subprocess.check_output(["git", "diff", "--name-only", BASE_SHA], text=True).splitlines())
    expected = sorted([str(PLAN), str(CONTINUITY)])
    if changed != expected:
        raise SystemExit(f"unexpected START surface: {changed!r}")
    subprocess.run(["git", "diff", "--check"], check=True)


if __name__ == "__main__":
    main()
