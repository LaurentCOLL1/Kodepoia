from pathlib import Path

PATH = Path('docs/continuity/KODEPOIA_CONTINUITY.md')
text = PATH.read_text(encoding='utf-8')


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected exactly one match, got {count}: {old[:120]!r}')
    text = text.replace(old, new, 1)


replace_once(
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.13 COMPLETE + NORMALIZED. R14.14 COMPLETE at technical/evidence level; END-sync pending fresh exact-head gates. R14.15–R14.17 PLANNED and unauthorized.** R14.14 immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; clean START-head `c17356c7d24fb07544d3f58e65d7f4ef2a2f7624`; technical gates R0 #1930 / `33251838461`, Python Core #1905 / `33251838469`, UI #1870 / `33251838453`, R14 LiveOps Acceptance #4 / `33251838460` all SUCCESS, with 21 focused tests on Ubuntu and Windows and 23/23 deterministic checks PASS. Manual state: NONE; `provider_live_claim=false`. The only authorized next action is fresh validation of the three-file END-sync head, expected-head merge, then one continuity-only post-merge normalization before R14.15.",
    "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.13 COMPLETE + NORMALIZED. R14.14 COMPLETE and merged; its unique post-merge continuity normalization is now the only authorized action. R14.15–R14.17 remain PLANNED and unauthorized.** R14.14 immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; final END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; fresh END gates R0 #1938 / `33253609529`, Python Core #1913 / `33253609548`, UI #1878 / `33253609556`, R14 LiveOps Acceptance #5 / `33253609622` all SUCCESS; PR #283 merged with `expected_head_sha=d8debf494f4f096e2a9f8a4093852752242e8b9f` as `29bf8255277fcbfce721408ec0abab660076f99d`. Manual state: NONE; `provider_live_claim=false`. The only authorized next action is fresh R0 + full Python Core + KodeStudio UI Smoke on the continuity-only `r14/14-normalization` head, then expected-head merge before R14.15."
)

replace_once(
    "- R14.14 : **COMPLETE at technical/evidence level / END-sync pending fresh gates** — immutable source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; branch `r14/14-liveops-campaigns-schedules`; normalized base `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`.",
    "- R14.14 : **COMPLETE / post-merge normalization pending** — immutable source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; PR #283 expected-head merge `29bf8255277fcbfce721408ec0abab660076f99d`; unique normalization branch `r14/14-normalization`."
)

replace_once(
    "- Evidence flags: `manual_state=none`, `provider_live_claim=false`, `external_provider_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`.\n- Manual intervention: **NONE**. No external LiveOps SaaS/account/credential/network proof was required.\n- R14.14 is COMPLETE at technical/evidence level only. R14.15 remains unauthorized until the three-file END-sync head passes fresh exact-head R0/Python/UI/R14 LiveOps gates, merges with `expected_head_sha`, then exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.",
    "- Evidence flags: `manual_state=none`, `provider_live_claim=false`, `external_provider_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`.\n- Final accepted END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f` differs from immutable technical source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_14_ACCEPTANCE.md` and this continuity file.\n- Fresh END-head gates on exact `d8debf494f4f096e2a9f8a4093852752242e8b9f`: R0 Repository Guard #1938 / `33253609529` SUCCESS; Python Core #1913 / `33253609548` SUCCESS; KodeStudio UI Smoke #1878 / `33253609556` SUCCESS; R14 LiveOps Acceptance #5 / `33253609622` SUCCESS Ubuntu 24.04 + Windows 2025.\n- PR #283 merged only with `expected_head_sha=d8debf494f4f096e2a9f8a4093852752242e8b9f` as implementation/evidence merge `29bf8255277fcbfce721408ec0abab660076f99d`.\n- Unique post-merge normalization branch `r14/14-normalization` was created exactly from merge `29bf8255277fcbfce721408ec0abab660076f99d`; its final tree delta must contain only this continuity file and pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before expected-head merge.\n- Manual intervention: **NONE**. No external LiveOps SaaS/account/credential/network proof was required.\n- R14.14 is **COMPLETE and merged**. R14.15 remains unauthorized until the unique continuity-only post-merge normalization passes fresh exact-head R0/Python/UI and merges with expected-head protection."
)

replace_once(
    "## Next authorized action\n\nValidate the R14.14 END-sync head only. Its cumulative diff from immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1` must contain exactly `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_14_ACCEPTANCE.md`, and `docs/continuity/KODEPOIA_CONTINUITY.md`. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 LiveOps Acceptance on that same SHA. If all succeed, merge only with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI before authorizing R14.15. If any manual/provider-live gate becomes genuinely required, stop and record it truthfully instead of synthesizing PASS.",
    "## Next authorized action\n\nComplete the unique R14.14 post-merge normalization on `r14/14-normalization`. Its cumulative tree diff from implementation/evidence merge `29bf8255277fcbfce721408ec0abab660076f99d` must contain exactly `docs/continuity/KODEPOIA_CONTINUITY.md`. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that same normalization SHA. If all succeed, merge the normalization PR only with its exact `expected_head_sha`. Only the resulting normalized `main` authorizes the R14.15 START-sync. If any manual/provider-live gate becomes genuinely required, stop and record it truthfully instead of synthesizing PASS."
)

PATH.write_text(text, encoding='utf-8', newline='\n')
