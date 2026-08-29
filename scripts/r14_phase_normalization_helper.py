from pathlib import Path

path = Path('docs/continuity/KODEPOIA_CONTINUITY.md')
text = path.read_text(encoding='utf-8')

first, sep, rest = text.partition('\n')
if not first.startswith('> Kodepoia, architecture v1.0 gelée.'):
    raise SystemExit('continuity banner anchor mismatch')
first = (
    '> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. '
    'R14 planning ACCEPTED + NORMALIZED. R14.1–R14.17 COMPLETE + NORMALIZED. '
    'R14 COMPLETE + NORMALIZED. R15 planning AUTHORIZED on the normalized main produced by this unique phase normalization.** '
    'R14.17 immutable technical source `11fb0e1a28fd5cbb607e2b302a36314f151ee170`; final END-head '
    '`4f4ab856c233e3a0fd4298e1e26d8ea389c7e750`; canonical integrated digest '
    '`06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`; '
    'fresh exact-END gates R0 #2042 / `33267376108`, Python #2017 / `33267376130`, UI #1982 / `33267376112`, '
    'Integrated #15 / `33267376114` all SUCCESS; PR #290 required R0 #2043 / `33267483582` SUCCESS Ubuntu + Windows '
    'and merged exact head as `3327913047625ca26a70b5c96beb3f1608ff7720`. '
    'Manual state CONDITIONAL / NOT TRIGGERED; no provider-live, production-publish, Internet-scale or multi-region claim.'
)
text = first + sep + rest

old_bullet = (
    '- R14.17 : **COMPLETE / IMPLEMENTATION MERGE PENDING** — immutable source '
    '`11fb0e1a28fd5cbb607e2b302a36314f151ee170`; integrated digest '
    '`06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`; manual **CONDITIONAL / NOT TRIGGERED**.'
)
new_bullet = (
    '- R14.17 : **COMPLETE + NORMALIZED** — immutable source '
    '`11fb0e1a28fd5cbb607e2b302a36314f151ee170`; final END-head '
    '`4f4ab856c233e3a0fd4298e1e26d8ea389c7e750`; exact-END R0 #2042 / `33267376108`, Python #2017 / '
    '`33267376130`, UI #1982 / `33267376112`, Integrated #15 / `33267376114` SUCCESS; PR #290 required R0 #2043 / '
    '`33267483582` SUCCESS Ubuntu + Windows and merged with exact expected head as '
    '`3327913047625ca26a70b5c96beb3f1608ff7720`; integrated digest '
    '`06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`; manual **CONDITIONAL / NOT TRIGGERED**.'
)
if text.count(old_bullet) != 1:
    raise SystemExit('R14.17 global bullet anchor mismatch')
text = text.replace(old_bullet, new_bullet, 1)

planning_anchor = '- R14 planning : **ACCEPTED + NORMALIZED**.\n'
phase_bullet = (
    '- R14 : **COMPLETE + NORMALIZED** — canonical integrated digest '
    '`06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`; '
    'implementation/evidence merge `3327913047625ca26a70b5c96beb3f1608ff7720`; this record is the unique '
    'post-merge continuity-only phase normalization authority. R15 planning is the next authorized phase action after this normalization PR merges.\n'
)
if text.count(planning_anchor) != 1:
    raise SystemExit('R14 planning bullet anchor mismatch')
text = text.replace(planning_anchor, planning_anchor + phase_bullet, 1)

old_table = '| R14.17 | COMPLETE / MERGE PENDING | CONDITIONAL / NOT TRIGGERED |'
new_table = '| R14.17 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |'
if text.count(old_table) != 1:
    raise SystemExit('R14.17 status table anchor mismatch')
text = text.replace(old_table, new_table, 1)

heading = '## R14.17 technical / END closure authority\n'
prefix, marker, tail = text.partition(heading)
if not marker:
    raise SystemExit('R14.17 tail heading anchor mismatch')
if '## Next authorized action' not in tail:
    raise SystemExit('R14.17 next-action anchor mismatch')
new_tail = '''## R14.17 implementation merge / R14 phase normalization authority

- Exact normalized R14.16 base: `f6960db290a570e3a0c3c4ff97600014978d45df`; clean R14.17 START-head `e48f8207c92aae1f655fb270e21a2c861036a6fd`.
- Rejected technical candidates `f25cb89f1b54d325ecab6d12c08ec1e9129c1025` and `152f34d217f159d65b10d811d8770ea840b8e05b` are NON-AUTHORITATIVE. Temporary END-sync/helper staging commits `4e7f5d17e5e8356b7e6b1d3bc9331b73aefe496f`, `f509b7c683776e180f56129e5cb43eb0c65b8916`, and `6b3dcd15ca27979f55688b0b535eed1417b95dc2` are also NON-AUTHORITATIVE. No failed or staging decision evidence is reused.
- Immutable technical source `11fb0e1a28fd5cbb607e2b302a36314f151ee170`; source gates R0 #2028 / `33265386264`, Python #2003 / `33265386254`, UI #1968 / `33265386267`, Integrated #5 / `33265386261` all SUCCESS. Ubuntu Python Core: **1760 passed / 14 skipped / 46 warnings**.
- Scenario authority: 14/14 integrated checks PASS over 222 underlying service checks; artifact `9718490610` / `sha256:8ef3c8fd15ab88919918ff9819784e5ed8558d08951bf2e9dc464d7bac9c8bac`; scenario bytes 6313 / SHA-256 `8080d974bec375e822fb04d271671d922460e4d71e5996ce5a2d61377d4b8d47`; CI authority digest `f8e1ea8d274aafc44009bb76c2c2e21e5306673510cc61c47d96de34b9f20a08`.
- Canonical R14 integrated digest `06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`; report `status=pass`, `blockers=[]`, immutable source `11fb0e1a28fd5cbb607e2b302a36314f151ee170`.
- Final clean R14.17 END-head `4f4ab856c233e3a0fd4298e1e26d8ea389c7e750` contains no temporary report-emission or END-sync helper. Fresh exact-END gates: R0 #2042 / `33267376108` SUCCESS Ubuntu + Windows; Python Core #2017 / `33267376130` SUCCESS 5/5; KodeStudio UI Smoke #1982 / `33267376112` SUCCESS; R14 Integrated #15 / `33267376114` SUCCESS Ubuntu 24.04 + PostgreSQL 18 and Windows 2025.
- PR #290 required R0 Repository Guard #2043 / `33267483582` SUCCESS Ubuntu + Windows on exact head `4f4ab856c233e3a0fd4298e1e26d8ea389c7e750`, then merged only with `expected_head_sha=4f4ab856c233e3a0fd4298e1e26d8ea389c7e750` as implementation/evidence merge `3327913047625ca26a70b5c96beb3f1608ff7720`.
- This R14 phase normalization branch was created exactly from implementation merge `3327913047625ca26a70b5c96beb3f1608ff7720`. Its authoritative final tree changes **only** `docs/continuity/KODEPOIA_CONTINUITY.md`; `docs/roadmap/R14_PLAN.md` remains byte-identical to the implementation merge. Temporary normalization helper files are removed before the normalization decision head.
- Manual/provider state remains **CONDITIONAL / NOT TRIGGERED**; `provider_live_claim=false`, `production_publish_claim=false`, `internet_scale_claim=false`, `multi_region_claim=false`; no external IdP/store/CDN/managed-provider account, credential, public domain/TLS state, destructive production load or production publish is required or claimed.
- This continuity record is the single post-merge R14 phase-normalization authority. It becomes authoritative only after its exact normalization head passes fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and the normalization PR merges with exact expected-head protection. No second R14 normalization is permitted.

## Next authorized action

R15 planning is the next authorized action on the normalized `main` produced by this continuity-only normalization PR. Do not begin R15 from the implementation merge or an unmerged normalization candidate; only the successfully re-gated and merged normalized `main` is authoritative.
'''
text = prefix + new_tail
path.write_text(text, encoding='utf-8')
