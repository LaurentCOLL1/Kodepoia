from pathlib import Path

PATH = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = PATH.read_text(encoding="utf-8")
lines = text.splitlines()

prompt = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning IN_PROGRESS on `r14/00-phase-plan`; no R14.1 implementation is authorized yet.** "
    "R13.17 final documentation/evidence head `cb0c63bcdcbaf2b58b3066d311780843c2598575` passed the complete fresh 12-workflow exact-head family; implementation/evidence PR #253 merged as `f56c61dbc82efd93c08e2b29ad1acff33219689f`. "
    "The single continuity-only R13.17 normalization head `1bc52616e5e527dadfe8feafdc0d137433b37a48` changed exactly continuity, passed fresh R0 #1746 / `33135420877`, Python Core #1720 / `33135420870`, and KodeStudio UI Smoke #1687 / `33135420823`, all SUCCESS; PR #254 merged with exact-head protection as normalized main `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`. "
    "Therefore R13 is authoritatively COMPLETE + NORMALIZED. R14 frozen scope is Backend / Platform Services / LiveOps: conditional Auth, DB, authoritative server, matchmaking/lobby, cloud saves, achievements/entitlements/billing, remote config/feature flags/content delivery/events. "
    "The exhaustive `docs/roadmap/R14_PLAN.md` is being created from normalized main on `r14/00-phase-plan`; all R14.1–R14.17 subdivisions remain PLANNED. Merge the planning PR only after fresh exact-head R0 + full Python Core + KodeStudio UI Smoke, then perform exactly one continuity-only planning normalization with the same three fresh gates before R14.1 may start."
)

for i, line in enumerate(lines):
    if line.startswith("> Kodepoia, architecture v1.0 gelée."):
        lines[i] = prompt
    elif line.startswith("- R13 phase status:"):
        lines[i] = "- R13 phase status: **COMPLETE + NORMALIZED**."
    elif line.startswith("- R13.17:"):
        lines[i] = (
            "- R13.17: **COMPLETE + NORMALIZED**. Final documentation/evidence head **`cb0c63bcdcbaf2b58b3066d311780843c2598575`** passed all 12 fresh exact-head final gates; PR #253 merged as **`f56c61dbc82efd93c08e2b29ad1acff33219689f`**. "
            "Single continuity-only normalization head **`1bc52616e5e527dadfe8feafdc0d137433b37a48`** passed R0 #1746 / `33135420877`, Python Core #1720 / `33135420870`, and UI #1687 / `33135420823`; PR #254 merged as normalized **`main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**. Manual **CONDITIONAL / NOT TRIGGERED**."
        )
    elif line.startswith("- R14 planning:"):
        lines[i] = (
            "- R14 planning: **IN_PROGRESS** on `r14/00-phase-plan`, created exactly from normalized `main` **`b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**. "
            "Exhaustive `R14_PLAN.md` covers frozen R14.1–R14.17; implementation remains forbidden until planning merge + single planning continuity normalization."
        )
text = "\n".join(lines)

start = text.index("## R13.17 normalization authority")
end = text.index("## Frozen R13 subdivision index", start)
old = text[start:end]
anchor = "- Single continuity-only normalization branch"
cut = old.index(anchor)
prefix = old[:cut]
replacement_tail = """- Single continuity-only normalization head **`1bc52616e5e527dadfe8feafdc0d137433b37a48`** changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md` relative to implementation/evidence merge `f56c61dbc82efd93c08e2b29ad1acff33219689f`, with no plan/code/schema/test/workflow bytes in the cumulative final diff.
- Fresh exact-head normalization gates on `1bc52616e5e527dadfe8feafdc0d137433b37a48` all completed SUCCESS: R0 Repository Guard #1746 / **`33135420877`**, Python Core #1720 / **`33135420870`**, and KodeStudio UI Smoke #1687 / **`33135420823`**.
- Normalization PR #254 merged with **`expected_head_sha=1bc52616e5e527dadfe8feafdc0d137433b37a48`** as normalized **`main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**.
- Frozen core boundaries remain unchanged: Android proof is **VIRTUAL / API 36**, Apple proof is **SIMULATOR**; physical devices, live Play/App Store/TestFlight state, production signing/provisioning credentials and automatic public publication remain outside the frozen core PASS claim.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No physical device, live store account, production signing secret, Apple Developer/App Store Connect credential, paid provider quota or user-machine Android SDK/Xcode installation was required.
- Therefore R13.17 and Phase R13 are authoritatively **COMPLETE + NORMALIZED**.

## R14 planning authority

- Frozen roadmap title: **Backend / Platform Services / LiveOps**.
- Frozen roadmap scope: conditional Auth, DB, authoritative server, matchmaking/lobby, cloud saves, achievements/entitlements/billing, remote config/feature flags/content delivery/events. R15 fine-tuning and R16 final hardening remain outside R14.
- Authorized normalized planning base: **`b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**, the R13.17 normalization merge.
- Dedicated planning branch: **`r14/00-phase-plan`**, created exactly from that normalized main.
- `docs/roadmap/R14_PLAN.md` is the exhaustive planning authority under construction. Its frozen candidate subdivision index is R14.1–R14.17, all **PLANNED**; R14.1 has **not started**.
- R14 is provider-neutral/local-first. Paid cloud accounts, production domains/TLS, production IdP tenants, managed databases, app-store billing accounts, CDN accounts and provider production credentials are not global prerequisites. Provider-live claims remain explicit `CONDITIONAL` capability evidence.
- Planning external compatibility facts are dated evidence, not architecture constants: current auth/token/passkey standards, supported stable PostgreSQL, billing-provider server verification, event/feature-flag/observability interoperability are capability-probed and source-provenanced.
- **Planning acceptance rule:** no R14.1 implementation before the exhaustive planning PR passes fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merges with `expected_head_sha`, followed by exactly one continuity-only planning normalization from that merge with the same three fresh gates and exact-head merge.

"""
text = text[:start] + prefix + replacement_tail + text[end:]

heading = "## Next authorized action\n\n"
idx = text.index(heading)
after = idx + len(heading)
next_heading_pos = text.find("\n## ", after)
if next_heading_pos == -1:
    next_heading_pos = len(text)
new_action = (
    "Finish and verify the exhaustive `docs/roadmap/R14_PLAN.md` plus this START-sync continuity on `r14/00-phase-plan`. "
    "Freeze the exact planning head, require fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, and merge the planning PR with `expected_head_sha` only if all three are SUCCESS. "
    "Then create exactly one continuity-only R14 planning-normalization branch from that planning merge; it must change only continuity, pass fresh R0 + Python Core + UI Smoke and merge with expected-head protection. "
    "**Only after that normalized planning merge may R14.1 start on its own dedicated branch.** If any conditional manual seam unexpectedly becomes necessary during planning, stop and document it rather than starting implementation.\n"
)
text = text[:after] + new_action + text[next_heading_pos:]
PATH.write_text(text, encoding="utf-8")
