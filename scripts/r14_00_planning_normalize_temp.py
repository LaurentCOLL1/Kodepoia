from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = PATH.read_text(encoding="utf-8")
lines = text.splitlines()

prompt = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED / NORMALIZATION IN_PROGRESS on `r14/00-planning-continuity-normalization`; R14.1 has not started.** "
    "The exhaustive planning head `343b7834d8b5826d5012bf78926102725b66db7f` changed only `docs/roadmap/R14_PLAN.md` and continuity from normalized R13 main, and passed fresh exact-head R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and KodeStudio UI Smoke #1689 / `33136015584`, all SUCCESS. "
    "Planning PR #255 merged with expected-head protection as `808e5215e45a3a90d3037efb1a3749f01b285b9c`. The single allowed planning continuity normalization branch starts exactly from that merge and must change only `docs/continuity/KODEPOIA_CONTINUITY.md`, pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke, then merge with expected-head protection. "
    "Only the resulting normalized main makes R14 planning ACCEPTED + NORMALIZED and authorizes R14.1 on its own dedicated branch. Frozen R14 scope remains Backend / Platform Services / LiveOps with R14.1–R14.17 fixed by `R14_PLAN.md`."
)

for i, line in enumerate(lines):
    if line.startswith("> Kodepoia, architecture v1.0 gelée."):
        lines[i] = prompt
    elif line.startswith("- R14 planning:"):
        lines[i] = (
            "- R14 planning: **ACCEPTED / NORMALIZATION IN_PROGRESS**. Exhaustive head **`343b7834d8b5826d5012bf78926102725b66db7f`** passed R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; PR #255 merged as **`808e5215e45a3a90d3037efb1a3749f01b285b9c`**. "
            "Single continuity-only planning normalization is active on `r14/00-planning-continuity-normalization`; R14.1 remains forbidden until it passes fresh gates and merges."
        )
text = "\n".join(lines)

start = text.index("## R14 planning authority")
end = text.index("## Frozen R13 subdivision index", start)
section = """## R14 planning authority

- Frozen roadmap title: **Backend / Platform Services / LiveOps**.
- Frozen roadmap scope: conditional Auth, DB, authoritative server, matchmaking/lobby, cloud saves, achievements/entitlements/billing, remote config/feature flags/content delivery/events. R15 fine-tuning and R16 final hardening remain outside R14.
- Authorized normalized planning base: **`b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**, the R13.17 normalization merge.
- Dedicated planning branch: **`r14/00-phase-plan`**, created exactly from that normalized main.
- Exhaustive planning head **`343b7834d8b5826d5012bf78926102725b66db7f`** introduced `docs/roadmap/R14_PLAN.md` and START-sync continuity only. The plan freezes R14.1–R14.17; every subdivision remains **PLANNED** and R14.1 has not started.
- Fresh exact-head planning gates on `343b7834d8b5826d5012bf78926102725b66db7f` all completed SUCCESS: R0 Repository Guard #1748 / **`33136015617`**, Python Core #1722 / **`33136015593`**, and KodeStudio UI Smoke #1689 / **`33136015584`**. Python Core passed full Ubuntu/Windows tests plus both package builds and its internal KodeStudio smoke.
- Planning PR #255 merged with **`expected_head_sha=343b7834d8b5826d5012bf78926102725b66db7f`** as planning merge **`808e5215e45a3a90d3037efb1a3749f01b285b9c`**.
- R14 remains provider-neutral/local-first. Paid cloud accounts, production domains/TLS, production IdP tenants, managed databases, app-store billing accounts, CDN accounts and provider production credentials are not global prerequisites. Provider-live claims remain explicit `CONDITIONAL` capability evidence.
- External compatibility facts are dated evidence, not architecture constants: current auth/token/passkey standards, supported stable PostgreSQL, billing-provider server verification and event/feature-flag/observability interoperability remain capability-probed and source-provenanced.
- Single continuity-only planning normalization branch **`r14/00-planning-continuity-normalization`** was created exactly from planning merge `808e5215e45a3a90d3037efb1a3749f01b285b9c`. It is the only allowed post-planning normalization and must change exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; no R14 plan/code/schema/test/workflow bytes may remain changed in its final cumulative diff.
- **Planning normalization acceptance rule:** this exact normalization head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merge with `expected_head_sha`. Only the resulting normalized `main` makes R14 planning **ACCEPTED + NORMALIZED** and authorizes R14.1.

"""
text = text[:start] + section + text[end:]

heading = "## Next authorized action\n\n"
idx = text.index(heading)
after = idx + len(heading)
next_heading_pos = text.find("\n## ", after)
if next_heading_pos == -1:
    next_heading_pos = len(text)
new_action = (
    "Verify that `r14/00-planning-continuity-normalization` differs from planning merge `808e5215e45a3a90d3037efb1a3749f01b285b9c` by exactly `docs/continuity/KODEPOIA_CONTINUITY.md`. "
    "Open the single planning-normalization PR to `main`, require fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke on its exact head, and merge with `expected_head_sha` only if all three are SUCCESS. "
    "**After that normalized planning merge, start R14.1 on its own branch and perform the mandatory subdivision START-sync in `R14_PLAN.md` + continuity before implementation.**\n"
)
text = text[:after] + new_action + text[next_heading_pos:]
PATH.write_text(text, encoding="utf-8")
