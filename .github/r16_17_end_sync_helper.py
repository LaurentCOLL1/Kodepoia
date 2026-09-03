from __future__ import annotations

import re
import subprocess
from pathlib import Path

TECHNICAL_SHA = "496d43bf48d23dd9ffe8283e910aa4bcaa1a2cf0"
BASE_SHA = "68cc2bb761329b3f1b4932319302db3dcc01cd2b"
START_SHA = "5cbae3c525467c3230d7156649b008e418c3d604"
PLAN = Path("docs/roadmap/R16_PLAN.md")
CONTINUITY = Path("docs/continuity/KODEPOIA_CONTINUITY.md")

R16_17_RUN = "33796341834"
R16_9_RUN = "33796341820"
R0_RUN = "33796341818"
PYTHON_RUN = "33796341864"
UI_RUN = "33796341904"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, got {count}")
    return updated


def regex_line_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one line match, got {count}")
    return updated


def end_authority() -> str:
    return f"""## R16.17 END authority

- R16.17 state: **COMPLETE at END-sync**; core manual state **CONDITIONAL / NOT TRIGGERED**. Production signing, store/public-registry publication, production credentials and provider/domain cutover remain `NOT_TRIGGERED` / `NOT_EXERCISED`; R16.18 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `{BASE_SHA}`; clean START-sync `{START_SHA}`; immutable technical source `{TECHNICAL_SHA}`.
- Fresh exact-technical-head gates are all SUCCESS: R16.17 #13 / `{R16_17_RUN}` Ubuntu + Windows plus `cross-platform-package-determinism`; R16.9 #69 / `{R16_9_RUN}` Ubuntu + Windows; R0 Repository Guard #2390 / `{R0_RUN}` Ubuntu + Windows; Python Core #2362 / `{PYTHON_RUN}` 5/5; KodeStudio UI Smoke #2327 / `{UI_RUN}`.
- Exact-source release-readiness acceptance is **13/13 PASS per OS** with `release_claim=true`, `critical_veto=false`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, `production_credentials_used=false`, `public_release_performed=false` and `network_publication_calls=0`.
- RC identity is `kodepoia-v1.0.0rc1` / version `1.0.0rc1`. Hosted installation is offline from `kodepoia-1.0.0rc1-py3-none-any.whl` with no dependency installation and imports the exact RC version.
- Canonical package bytes are identical across Linux and Windows after repository-owned archive-metadata canonicalization. SHA-256: wheel `b4378b6336d8f92e307e81a540e9698fd261dde2c4411fe5c224b16a8ee413e6`; sdist `bfa606908d1a2d34f9d46aaa95acb8087970662d72268e3cd7007987e07fab86`. Same-OS rebuild identity and the dedicated cross-platform comparison both PASS.
- Declared migration from prior fixture version `0.1.0a4` to `1.0.0rc1` passes backup verification, migration and exact rollback/recovery. The representative fixture set proves three migrated, three round-trip and three rollback paths without a critical failure.
- Exact-source build manifest/provenance, dependency/BOM/license evidence, secure defaults, known limitations, release notes and security/privacy/incident/recovery guidance all satisfy the frozen R16.17 acceptance contract. Release notes SHA-256 are `d9d0e9ed60c5ee25df2a58307162b65f595fa07c9606d49ef9a22c95582d5375`; security/operations guidance SHA-256 is `2a2bb5e8932c45ed055386f6ab550c92f8c449ba0be0cbac0fee67ac2e302525`.
- Optional production actions remain truthful: external artifact attestation `NOT_EXERCISED`; production credentials `NOT_USED`; production signing, provider/domain cutover, public-registry publication and store submission `NOT_TRIGGERED`. No public release occurred automatically.
- Exact technical-head R16.17 #13 artifacts: Linux `9909316760 / sha256:2375f2796c4300f691055969d06d643604fc83e241d2f859d1c99bd2488a9614`, acceptance evidence SHA-256 `42bcf021a2de790cf376b2f889ce8ef2f058e5b5d4dafbb7b286e8b40bc99873`, report-file SHA-256 `b605c8bd9640edf998e5f35cd6e1881b00f2845474dce537eb30912e06133f2d`; Windows `9909428110 / sha256:3f515dabe3cf38edfbcaebda38d6cfecf364424cff489159ffc609741502de10`, acceptance evidence SHA-256 `9eef0f27bf9234281f8ea4b7cfb59048fc15c851745872b5639a4fd7c6d4621c`, report-file SHA-256 `b645727f0c8b96fa2592650b4fcdbb85515c72180cdaed636259ab4bd41d25e9`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its exact resulting head must pass fresh R16.17/R16.9/R0/Python/UI SUCCESS before PR #367 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.17 normalization is authorized. Only the resulting normalized `main` may mark R16.17 **COMPLETE + NORMALIZED** and authorize R16.18 START.
"""


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != TECHNICAL_SHA:
        raise SystemExit(f"R16.17 END helper must run on {TECHNICAL_SHA}, got {head}")

    subprocess.run(
        ["git", "diff", "--exit-code", TECHNICAL_SHA, "--", str(PLAN), str(CONTINUITY)],
        check=True,
    )

    plan = PLAN.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")
    if "## R16.17 END authority" in plan or "## R16.17 END authority" in continuity:
        raise SystemExit("R16.17 END authority already exists")

    plan_checkpoint = (
        "**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. "
        "R16.1–R16.16 are COMPLETE + NORMALIZED. R16.17 is COMPLETE at END-sync on dedicated branch "
        "`r16/17-v1-packaging-migration-rollback-release-readiness` from exact normalized R16.16 `main` "
        f"`{BASE_SHA}`, with clean START `{START_SHA}` and immutable technical source `{TECHNICAL_SHA}`; "
        "R16.18 remains PLANNED and unauthorized. Fresh exact-technical-head gates are SUCCESS: "
        f"R16.17 #13 / `{R16_17_RUN}` Ubuntu + Windows plus cross-platform package determinism, "
        f"R16.9 #69 / `{R16_9_RUN}` Ubuntu + Windows, R0 #2390 / `{R0_RUN}` Ubuntu + Windows, "
        f"Python Core #2362 / `{PYTHON_RUN}` 5/5 and KodeStudio UI Smoke #2327 / `{UI_RUN}`. "
        "R16.17 acceptance is 13/13 PASS per OS and canonical wheel/sdist bytes are identical across Linux/Windows. "
        "Core manual state is CONDITIONAL / NOT TRIGGERED; no public release or production credential use occurred. "
        "Fresh exact-END five-gate qualification, PR #367 exact-head merge and exactly one continuity-only "
        "post-merge normalization remain mandatory before R16.18 START."
    )
    plan = regex_line_once(
        plan,
        r"^\*\*Execution checkpoint:\*\*[^\n]*$",
        plan_checkpoint,
        "plan execution checkpoint",
    )
    plan = replace_once(
        plan,
        "| R16.15 | Long-term project durability, resume and upgrade soak | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "| R16.15 | Long-term project durability, resume and upgrade soak | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.15 normalized status",
    )
    plan = replace_once(
        plan,
        "| R16.16 | Resource, concurrency, leak and diagnostics soak | COMPLETE | NONE |",
        "| R16.16 | Resource, concurrency, leak and diagnostics soak | COMPLETE + NORMALIZED | NONE |",
        "plan R16.16 normalized status",
    )
    plan = replace_once(
        plan,
        "| R16.17 | v1.0 packaging, migration, rollback & release readiness | PLANNED | CONDITIONAL |",
        "| R16.17 | v1.0 packaging, migration, rollback & release readiness | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "plan R16.17 status",
    )
    plan = replace_once(
        plan,
        "\n---\n\n# R16.18 — Integrated adversarial + real-project RC acceptance",
        "\n" + end_authority() + "\n---\n\n# R16.18 — Integrated adversarial + real-project RC acceptance",
        "plan R16.18 boundary",
    )
    PLAN.write_text(plan, encoding="utf-8", newline="\n")

    continuity_top = (
        "> Kodepoia, architecture v1.0 gelée. **R1–R15 COMPLETE + NORMALIZED. R16 planning ACCEPTED + "
        "NORMALIZED. R16.1–R16.16 COMPLETE + NORMALIZED. R16.17 COMPLETE at END-sync. R16.18 remains "
        f"PLANNED and unauthorized.** R16.17 immutable technical source `{TECHNICAL_SHA}` passed fresh exact-head "
        f"R16.17 #13 / `{R16_17_RUN}` Ubuntu + Windows plus cross-platform package determinism, R16.9 #69 / "
        f"`{R16_9_RUN}`, R0 #2390 / `{R0_RUN}`, Python Core #2362 / `{PYTHON_RUN}` 5/5 and KodeStudio UI "
        f"Smoke #2327 / `{UI_RUN}`. Release-readiness is 13/13 PASS per OS; canonical wheel/sdist bytes are "
        "identical across Linux/Windows; no public release or production credential use occurred; core manual state "
        "is CONDITIONAL / NOT TRIGGERED. This documentation-only END-sync must now pass fresh exact-END "
        "R16.17/R16.9/R0/Python/UI before PR #367 exact-head merge; one continuity-only post-merge normalization "
        "remains mandatory before R16.18 START.\n\n"
    )
    continuity = regex_once(
        continuity,
        r"\A> Kodepoia, architecture v1\.0 gelée\..*?\n\n",
        continuity_top,
        "continuity top checkpoint",
    )

    global_line = (
        f"- R16.17 : **COMPLETE at END-sync** — normalized R16.16 `main` `{BASE_SHA}`; clean START `{START_SHA}`; "
        f"immutable technical source `{TECHNICAL_SHA}`; exact-head R16.17 #13 / `{R16_17_RUN}` SUCCESS Ubuntu + "
        "Windows plus cross-platform-package-determinism, "
        f"R16.9 #69 / `{R16_9_RUN}` SUCCESS Ubuntu + Windows, R0 #2390 / `{R0_RUN}` SUCCESS Ubuntu + Windows, "
        f"Python Core #2362 / `{PYTHON_RUN}` SUCCESS 5/5 and UI #2327 / `{UI_RUN}` SUCCESS. Acceptance is 13/13 "
        "PASS per OS with `release_claim=true`, `critical_veto=false`, offline wheel install and exact migration/rollback "
        "coverage. Canonical packages are byte-identical cross-platform: wheel "
        "`b4378b6336d8f92e307e81a540e9698fd261dde2c4411fe5c224b16a8ee413e6`, sdist "
        "`bfa606908d1a2d34f9d46aaa95acb8087970662d72268e3cd7007987e07fab86`. No public release or production "
        "credential use occurred; optional signing/publication/provider cutover remain NOT_TRIGGERED/NOT_EXERCISED. "
        "Core manual CONDITIONAL / NOT TRIGGERED. Fresh exact-END five-gate qualification, PR #367 exact-head merge "
        "and the unique post-merge continuity-only normalization remain mandatory before R16.18 START."
    )
    continuity = regex_line_once(
        continuity,
        r"^- R16\.17 : \*\*IN_PROGRESS\*\* — [^\n]*$",
        global_line,
        "continuity R16.17 global authority",
    )
    continuity = replace_once(
        continuity,
        "| R16.17 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |",
        "| R16.17 | COMPLETE | CONDITIONAL / NOT TRIGGERED |",
        "continuity R16.17 status row",
    )
    continuity = replace_once(
        continuity,
        "- No R16.17 implementation bytes precede this START-sync; no public release occurs automatically.\n\n## R16 status index",
        "- No R16.17 implementation bytes precede this START-sync; no public release occurs automatically.\n\n"
        + end_authority()
        + "\n## R16 status index",
        "continuity R16.17 END insertion",
    )

    next_action = (
        "## Next authorized action\n\n"
        f"R16.17 is **COMPLETE at END-sync** on exact immutable technical source `{TECHNICAL_SHA}` after fresh "
        "technical-head R16.17/R16.9/R0/Python/UI success and explicit cross-platform package byte identity. "
        "The only authorized next action inside R16.17 is fresh qualification of the exact documentation END head "
        "by those same five authorities, followed by PR #367 merge only with `expected_head_sha` equal to that exact "
        "successful END head, then exactly one continuity-only post-merge normalization with fresh R0 + full Python "
        "Core + KodeStudio UI Smoke. **No R16.18 action is authorized before the normalized main produced by that "
        "single normalization merge.** Core manual state remains CONDITIONAL / NOT TRIGGERED; production signing, "
        "public/store publication, production credentials and provider/domain cutover remain unexercised.\n\n"
        "## Permanent R-phase execution rule"
    )
    continuity = regex_once(
        continuity,
        r"## Next authorized action\n\n.*?\n\n## Permanent R-phase execution rule",
        next_action,
        "continuity next authorized action",
    )
    CONTINUITY.write_text(continuity, encoding="utf-8", newline="\n")

    changed = subprocess.check_output(
        ["git", "diff", "--name-only", TECHNICAL_SHA], text=True
    ).splitlines()
    expected = sorted([str(CONTINUITY), str(PLAN)])
    if sorted(changed) != expected:
        raise SystemExit(f"unexpected END-sync surface: {changed!r}")
    subprocess.run(["git", "diff", "--check", TECHNICAL_SHA], check=True)


if __name__ == "__main__":
    main()
