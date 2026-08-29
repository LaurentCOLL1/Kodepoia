from pathlib import Path

BASE = '0078a75d473524688e6ab76ccf41b509e2146dea'
BRANCH = 'r14/15-service-operations-resilience'
NORM_HEAD = '8b527170d3b79bfacbdac36f638c8c616689bc61'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, got {count}')
    return text.replace(old, new, 1)


def replace_prefixed_line(text: str, prefix: str, new_line: str, label: str) -> str:
    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise SystemExit(f'{label}: expected one prefixed line, got {len(matches)}')
    lines[matches[0]] = new_line
    return '\n'.join(lines) + ('\n' if text.endswith('\n') else '')


plan_path = Path('docs/roadmap/R14_PLAN.md')
plan = plan_path.read_text(encoding='utf-8')
plan = replace_prefixed_line(
    plan,
    '**Execution checkpoint:**',
    '**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.14 are COMPLETE + NORMALIZED on normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`. R14.15 is IN_PROGRESS on dedicated branch `r14/15-service-operations-resilience`, branched exactly from that normalized main; R14.16–R14.17 remain PLANNED. R14.15 manual state is CONDITIONAL / NOT TRIGGERED for core acceptance: bounded local/hosted CI is authoritative, while external provider quota/cost/load proof remains manual/provider-dependent only if explicitly claimed. R14.14 immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; final END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; implementation/evidence merge PR #283 `29bf8255277fcbfce721408ec0abab660076f99d`; unique normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61`; fresh normalization gates R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, UI #1884 / `33254094372` all SUCCESS; normalization PR #284 expected-head merge produced normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.',
    'plan checkpoint',
)
plan = replace_once(
    plan,
    '- END state: **R14.14 COMPLETE at technical/evidence level**; R14.15–R14.17 remain PLANNED. This END synchronization must now pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke + R14 LiveOps Acceptance; merge is allowed only with expected-head protection, followed by exactly one continuity-only post-merge normalization before R14.15 is authorized.',
    '- Unique post-merge normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`; fresh exact-head R0 #1944 / `33254094376`, Python Core #1919 / `33254094466` and KodeStudio UI Smoke #1884 / `33254094372` all SUCCESS. PR #284 merged only with `expected_head_sha=8b527170d3b79bfacbdac36f638c8c616689bc61` as normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.\n- Final state: **R14.14 COMPLETE + NORMALIZED**. R14.15 is authorized only from normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`; R14.16–R14.17 remain PLANNED.',
    'R14.14 final state',
)
plan = replace_once(
    plan,
    '---\n\n# R14.15 — Service operations/resilience: health, limits, retries, backup/restore, DR + load budgets',
    '''---\n\n## R14.15 START authority\n\n- Dedicated branch: `r14/15-service-operations-resilience`.\n- Exact branch point and sole authorized base: normalized R14.14 `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.\n- R14.14 closure authority: immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; final END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; fresh END gates R0 #1938 / `33253609529`, Python Core #1913 / `33253609548`, UI #1878 / `33253609556`, R14 LiveOps Acceptance #5 / `33253609622` SUCCESS; PR #283 expected-head merge `29bf8255277fcbfce721408ec0abab660076f99d`; unique normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61`; fresh normalization gates R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, UI #1884 / `33254094372` SUCCESS; PR #284 expected-head merge produced normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.\n- START state: R14.1–R14.14 COMPLETE + NORMALIZED; R14.15 IN_PROGRESS; R14.16–R14.17 PLANNED.\n- Core execution posture: deterministic/local or hosted-CI health, retry/circuit/rate-limit, backup/restore/DR, failure-injection and bounded-load evidence only. No Internet-scale, multi-region, external-provider quota/cost or production-load claim may be inferred from core CI.\n- Manual state: **CONDITIONAL / NOT TRIGGERED**. External provider quota/cost/load proof becomes manual/provider-dependent only if explicitly claimed; destructive or high-cost production load is forbidden by default.\n\n---\n\n# R14.15 — Service operations/resilience: health, limits, retries, backup/restore, DR + load budgets''',
    'R14.15 START authority',
)
plan_path.write_text(plan, encoding='utf-8', newline='\n')

continuity_path = Path('docs/continuity/KODEPOIA_CONTINUITY.md')
cont = continuity_path.read_text(encoding='utf-8')
cont = replace_prefixed_line(
    cont,
    '> Kodepoia, architecture v1.0 gelée.',
    '> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.14 COMPLETE + NORMALIZED. R14.15 IN_PROGRESS on `r14/15-service-operations-resilience`; R14.16–R14.17 PLANNED.** Normalized R14.14 `main` and exact R14.15 branch point: `0078a75d473524688e6ab76ccf41b509e2146dea`. R14.14 immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; implementation merge PR #283 `29bf8255277fcbfce721408ec0abab660076f99d`; unique normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61`; normalization gates R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, UI #1884 / `33254094372` SUCCESS; PR #284 expected-head merge -> normalized main `0078a75d473524688e6ab76ccf41b509e2146dea`. R14.15 manual state: CONDITIONAL / NOT TRIGGERED for core; no external quota/cost/load or production-scale claim is authorized without explicit manual evidence. The only authorized action is R14.15 implementation/testing on its dedicated branch.',
    'continuity prompt',
)
cont = replace_prefixed_line(
    cont,
    '- R14.14 :',
    '- R14.14 : **COMPLETE + NORMALIZED** — immutable source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; PR #283 merge `29bf8255277fcbfce721408ec0abab660076f99d`; normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61`; normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea` via PR #284 after fresh R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, UI #1884 / `33254094372` SUCCESS.',
    'continuity R14.14 global',
)
cont = replace_once(
    cont,
    '- R14.15–R14.17 : **PLANNED**.',
    '- R14.15 : **IN_PROGRESS** — branch `r14/15-service-operations-resilience`; exact normalized base `0078a75d473524688e6ab76ccf41b509e2146dea`; manual `CONDITIONAL / NOT TRIGGERED` for core.\n- R14.16–R14.17 : **PLANNED**.',
    'continuity global R14.15 status',
)
cont = replace_prefixed_line(
    cont,
    '- Manual state actuel R14.14 :',
    '- Manual state actuel R14.15 : **CONDITIONAL / NOT TRIGGERED**. Core uses bounded local/hosted CI; external provider quota/cost/load evidence is manual only if explicitly claimed, and no destructive/high-cost production load is authorized by default.',
    'continuity manual state',
)
cont = replace_once(cont, '| R14.14 | COMPLETE | NONE |', '| R14.14 | COMPLETE + NORMALIZED | NONE |', 'status R14.14')
cont = replace_once(cont, '| R14.15 | PLANNED | CONDITIONAL |', '| R14.15 | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |', 'status R14.15')
cont = replace_once(
    cont,
    '- Unique post-merge normalization branch `r14/14-normalization` was created exactly from merge `29bf8255277fcbfce721408ec0abab660076f99d`; its final tree delta must contain only this continuity file and pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before expected-head merge.',
    '- Unique post-merge normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61` changed only this continuity file; fresh exact-head R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, and UI #1884 / `33254094372` all SUCCESS. PR #284 merged with `expected_head_sha=8b527170d3b79bfacbdac36f638c8c616689bc61` as normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.',
    'R14.14 normalization closure',
)
cont = replace_once(
    cont,
    '- R14.14 is **COMPLETE and merged**. R14.15 remains unauthorized until the unique continuity-only post-merge normalization passes fresh exact-head R0/Python/UI and merges with expected-head protection.',
    '- R14.14 final state: **COMPLETE + NORMALIZED** on `main` `0078a75d473524688e6ab76ccf41b509e2146dea`. R14.15 START-sync is authorized from that exact normalized main.',
    'R14.14 final closure state',
)
cont = replace_once(
    cont,
    '## Next authorized action\n\nComplete the unique R14.14 post-merge normalization on `r14/14-normalization`. Its cumulative tree diff from implementation/evidence merge `29bf8255277fcbfce721408ec0abab660076f99d` must contain exactly `docs/continuity/KODEPOIA_CONTINUITY.md`. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that same normalization SHA. If all succeed, merge the normalization PR only with its exact `expected_head_sha`. Only the resulting normalized `main` authorizes the R14.15 START-sync. If any manual/provider-live gate becomes genuinely required, stop and record it truthfully instead of synthesizing PASS.',
    '''## R14.15 START authority\n\n- Dedicated branch: `r14/15-service-operations-resilience`.\n- Exact branch point and sole authorized base: normalized R14.14 `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.\n- START state: R14.1–R14.14 COMPLETE + NORMALIZED; R14.15 IN_PROGRESS; R14.16–R14.17 PLANNED.\n- Scope authority: health/readiness/dependency graph; timeout/retry/backoff/jitter; circuit breaker/bulkhead/rate limits; connection/queue budgets; graceful degradation; backup scheduling + isolated restore; bounded RPO/RTO evidence; deterministic dependency failure injection; bounded load profiles; OTel-derived service health; bounded log/event retention.\n- Acceptance posture: dependency outage, timeout/retry/circuit/rate-limit, graceful shutdown, backup+restore hash, bounded RPO/RTO and load-budget evidence plus R0/Python/UI. Local/hosted CI never implies Internet-scale or multi-region production capability.\n- Manual state: **CONDITIONAL / NOT TRIGGERED**. External provider quota/cost/load proof is manual/provider-dependent only when explicitly claimed; destructive/high-cost production load remains forbidden by default.\n\n## Next authorized action\n\nImplement and test R14.15 only on `r14/15-service-operations-resilience`, preserving the exact normalized base `0078a75d473524688e6ab76ccf41b509e2146dea` and the frozen R14.15 scope. Build deterministic provider-neutral resilience, health, backup/restore/DR, failure-injection and bounded-load evidence; do not infer external-provider, Internet-scale, multi-region or production-load capability from local/hosted CI. If an external quota/cost/load claim becomes genuinely required, stop and record the manual/provider-dependent gate truthfully before any R14.16 work.''',
    'R14.15 next action',
)
continuity_path.write_text(cont, encoding='utf-8', newline='\n')
