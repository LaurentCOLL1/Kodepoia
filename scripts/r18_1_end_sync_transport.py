from pathlib import Path

TECHNICAL = "8fda649829acfd5abae2ea31e9c744f8554b8d06"
RUN = "33928967043"
ACCEPTANCE = "1bf94b74713522149083b608c0664c215ba12304244fb6d6ec04e280291f883d"
IDENTITY = "d0cd93c16846980ac8e633bd23f2930969f2d249040452c5529095de1cd40ef1"
SCHEMA = "0c4dfdd550cd14bccbdcf03a6f3b1403e0bff3c2afed6b61803f7e1ee6612b4f"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def update_plan() -> None:
    path = Path("docs/roadmap/R18_PLAN.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "Status: **PLANNING**", "Status: **IN_PROGRESS**", "phase status")
    text = replace_once(
        text,
        "Roadmap status: this document is the explicit post-R17 roadmap authorization for R18. It does **not** rewrite the frozen v1.0/R1–R16 architecture or history. No R18 implementation is authorized until this complete plan and its planning continuity record are re-gated and merged to `main`.",
        "Roadmap status: planning is **ACCEPTED + NORMALIZED** on `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`. R18.1 is COMPLETE at END-sync on immutable technical source `" + TECHNICAL + "`; its implementation/evidence merge and the unique post-merge continuity-only normalization remain required before R18.2 may start. The frozen v1.0/R1–R16 architecture and history are not rewritten.",
        "roadmap checkpoint",
    )
    text = replace_once(
        text,
        "| R18.1 | Canonical release identity, versions and channels | PLANNED | NONE | R17 normalized main |",
        "| R18.1 | Canonical release identity, versions and channels | COMPLETE | NONE | R17 normalized main |",
        "R18.1 index",
    )
    marker = "## Validation and evidence\n\nPreserve exact head SHA, normalized identity JSON, all derived version strings and CI run IDs. Evidence must demonstrate zero version disagreement."
    replacement = marker + (
        "\n\nEND-sync technical acceptance: immutable source `" + TECHNICAL + "`; R18.1 run `" + RUN + "` SUCCESS on Ubuntu 24.04 and Windows with compile, Ruff, 6/6 focused tests, packaged-wheel identity verification and exact-source evidence emission. Canonical identity is `Kodepoia` / `kodepoia`, channel `beta`, build type `prerelease`, PEP 440 `1.1.0rc1`, public/installer `1.1.0-rc1`, source binding `exact-head`; acceptance SHA-256 `" + ACCEPTANCE + "`, identity SHA-256 `" + IDENTITY + "`, schema SHA-256 `" + SCHEMA + "`. Manual state is `NONE`; production signing, public GitHub Release and public WinGet submission are not triggered. Because this END-sync changes documentation bytes, fresh R18.1 + R0 Repository Guard + full Python Core + KodeStudio UI Smoke gates on the resulting exact END-head are mandatory before exact-head merge."
    )
    text = replace_once(text, marker, replacement, "R18.1 evidence")
    path.write_text(text, encoding="utf-8", newline="\n")


def update_continuity() -> None:
    path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED on canonical `main` `bbffc382d4fb8a7d947345da11b56459d0fec825` after planning PR #379 and the unique exact-head gated planning-normalization PR #380. R18.1 Canonical release identity, versions and channels is STARTED from that exact normalized main on `r18/01-release-identity`.** Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.",
        "> Kodepoia, architecture v1.0 gelée. **R1–R17 COMPLETE + NORMALIZED. R18 planning ACCEPTED + NORMALIZED on canonical `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`. R18.1 Canonical release identity, versions and channels is COMPLETE at END-sync on immutable technical source `" + TECHNICAL + "`; fresh exact-END R18.1/R0/Python/UI gates, exact-head PR #381 merge and the unique post-merge continuity normalization remain required before R18.2.** Production signing, public GitHub Release publication and public WinGet submission remain CONDITIONAL / NOT TRIGGERED.",
        "continuity header",
    )
    old_r181 = "- R18.1 : **IN PROGRESS / START-SYNC** — normalized R18 planning base `bbffc382d4fb8a7d947345da11b56459d0fec825`; dedicated branch `r18/01-release-identity`; scope frozen to canonical release identity, versions and channels from `docs/roadmap/R18_PLAN.md`. Required channels are `stable`, `beta`, `nightly`; Python version output must be PEP 440-normalized; `pyproject.toml`, Inno Setup and CLI/UI version surfaces must be derived or validated against the single machine-readable authority; monotonicity and channel transitions must be tested. No production signing/public release/WinGet submission is authorized by this START."
    new_r181 = "- R18.1 : **COMPLETE at END-sync; merge + normalization pending** — normalized R18 planning base `bbffc382d4fb8a7d947345da11b56459d0fec825`; dedicated branch `r18/01-release-identity`; immutable technical source `" + TECHNICAL + "`. Exact-source R18.1 run `" + RUN + "` SUCCESS Ubuntu + Windows with compile, Ruff, 6/6 focused tests, packaged-wheel canonical identity verification and 21/21 acceptance checks; acceptance `" + ACCEPTANCE + "`; canonical identity `Kodepoia` / `kodepoia`, channel `beta`, build type `prerelease`, PEP 440 `1.1.0rc1`, public/installer `1.1.0-rc1`, identity `" + IDENTITY + "`, schema `" + SCHEMA + "`, `source_binding=exact-head`; manual NONE. Exact technical-head R0 #2428 / `33928967169`, Python Core #2400 / `33928967172` and UI #2365 / `33928967128` also SUCCESS. Historical R16.17/R16.18 release-readiness workflows fail only at their intentionally frozen v1.0 acceptance emitters after the R18.1 version identity changes and are not R18.1 gates. END-sync changes plan/continuity bytes, so fresh R18.1 + R0 + full Python Core + UI gates on the resulting exact END-head are required before PR #381 may merge with exact expected-head protection. After that merge, exactly one continuity-only R18.1 normalization is required; R18.2 remains PLANNED until that normalized main exists. Production signing/public GitHub Release/public WinGet submission remain NOT TRIGGERED."
    text = replace_once(text, old_r181, new_r181, "R18.1 continuity")
    old_next = "R18.1 — Canonical release identity, versions and channels — is the next authorized subdivision **only after this exact planning-normalization record passes fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke and merges to `main` with exact expected-head protection**. Begin R18.1 START-sync from that resulting normalized `main`; do not start it from planning merge `7869f674e8e5b9298b526c2c3c2a9b4295ce798d` or from this unmerged normalization candidate."
    new_next = "R18.1 is COMPLETE at END-sync on immutable technical source `" + TECHNICAL + "`. The next authorized action is to run fresh exact-END R18.1, R0 Repository Guard, full Python Core and KodeStudio UI Smoke gates on the documentation-synchronized head, then merge PR #381 only with that exact expected head. After the implementation/evidence merge, create exactly one continuity-only R18.1 normalization from the resulting `main`, gate it with fresh R0/Python/UI and merge it with exact expected-head protection. **R18.2 is not authorized until that normalized `main` exists.**"
    text = replace_once(text, old_next, new_next, "next authorized action")
    text = replace_once(
        text,
        "- State: **PLANNING ACCEPTED + NORMALIZED effective when this unique planning-normalization record enters `main` through fresh exact-head gates and exact-head merge**.",
        "- State: **PLANNING ACCEPTED + NORMALIZED** — unique planning-normalization PR #380 merged as canonical `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`; R18.1 is COMPLETE at END-sync with merge + subdivision normalization pending.",
        "R18 state",
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def remove_transports() -> None:
    for name in (
        ".github/workflows/r18-1-end-sync-transport.yml",
        ".github/workflows/r18-1-end-sync-transport-v2.yml",
        "scripts/r18_1_end_sync_transport.py",
    ):
        path = Path(name)
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    update_plan()
    update_continuity()
    remove_transports()
