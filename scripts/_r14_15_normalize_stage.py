from pathlib import Path

path = Path('docs/continuity/KODEPOIA_CONTINUITY.md')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        '> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.14 COMPLETE + NORMALIZED. R14.15 technically COMPLETE on its immutable source; END-sync/re-gates/merge/normalization pending. R14.16–R14.17 remain PLANNED and unauthorized.** R14.15 base `0078a75d473524688e6ab76ccf41b509e2146dea`; START-head `c3dd8aa5f3a7ec7d5f866ead207cf3a023fedbf0`; immutable technical source `232bae747e91fd97f4cf3110a019639217d7914b`; technical gates R0 #1959 / `33255887218`, Python Core #1934 / `33255887265`, UI #1899 / `33255887175`, R14 Resilience Acceptance #1 / `33255887252` all SUCCESS. Manual state: CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`; `external_load_required=false`; no Internet-scale, multi-region or PostgreSQL PITR claim. The only authorized next action is the three-file R14.15 END-sync followed by fresh exact-head re-gates.',
        '> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.14 COMPLETE + NORMALIZED. R14.15 implementation MERGED; the unique post-merge continuity-only normalization is pending. R14.16–R14.17 remain PLANNED and unauthorized.** R14.15 normalized base `0078a75d473524688e6ab76ccf41b509e2146dea`; START-head `c3dd8aa5f3a7ec7d5f866ead207cf3a023fedbf0`; immutable technical source `232bae747e91fd97f4cf3110a019639217d7914b`; clean END-head `80bd6853664ab9f41fd41fb83f43b43980bef394`; implementation merge PR #285 -> `53373e78c60d4a338e9313496a822c93ab334e68`. Fresh END gates R0 #1966 / `33257412850`, Python Core #1941 / `33257412849`, UI #1906 / `33257412847`, R14 Resilience Acceptance #3 / `33257412881` all SUCCESS. Manual state: CONDITIONAL / NOT TRIGGERED; `provider_live_claim=false`; `external_load_required=false`; no Internet-scale, multi-region or PostgreSQL PITR claim. The only authorized next action is the unique continuity-only normalization with fresh exact-head R0/Python/UI; R14.16 remains unauthorized until that normalization merges.'
    ),
    (
        '- R14.15 : **TECHNICALLY COMPLETE / END-SYNC PENDING** — immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; manual `CONDITIONAL / NOT TRIGGERED`.',
        '- R14.15 : **IMPLEMENTATION MERGED / NORMALIZATION PENDING** — immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; END-head `80bd6853664ab9f41fd41fb83f43b43980bef394`; PR #285 merge `53373e78c60d4a338e9313496a822c93ab334e68`; manual `CONDITIONAL / NOT TRIGGERED`.'
    ),
    (
        '| R14.15 | TECHNICALLY COMPLETE / END-SYNC PENDING | CONDITIONAL / NOT TRIGGERED |',
        '| R14.15 | IMPLEMENTATION MERGED / NORMALIZATION PENDING | CONDITIONAL / NOT TRIGGERED |'
    ),
    (
        '- R14.15 is **technically COMPLETE**. It remains unnormalized and R14.16 remains unauthorized until the three-file END-sync passes fresh exact-head R0/Python/UI/R14 Resilience gates, merges with expected-head protection, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.',
        '- R14.15 is **technically COMPLETE and implementation-merged**. Clean END-head `80bd6853664ab9f41fd41fb83f43b43980bef394` passed fresh exact-head R0/Python/UI/R14 Resilience gates and PR #285 merged with exact expected-head protection as `53373e78c60d4a338e9313496a822c93ab334e68`. R14.15 remains unnormalized and R14.16 remains unauthorized until the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.'
    ),
]

for old, new in replacements:
    count = text.count(old)
    assert count == 1, (count, old[:120])
    text = text.replace(old, new, 1)

old_tail = '''## Next authorized action

Complete the R14.15 END-sync from immutable technical source `232bae747e91fd97f4cf3110a019639217d7914b`. Its cumulative diff must contain exactly `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_15_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Service Operations Resilience Acceptance on that same END SHA. If all succeed, merge only with exact `expected_head_sha`, then perform exactly one continuity-only post-merge normalization with fresh R0/Python/UI before any R14.16 START-sync. If an external quota/cost/load or production DR claim becomes genuinely required, stop and record the manual/provider-dependent gate truthfully instead of synthesizing PASS.'''
new_tail = '''## R14.15 implementation merge / normalization authority

- Immutable technical source: `232bae747e91fd97f4cf3110a019639217d7914b`.
- Clean END-head: `80bd6853664ab9f41fd41fb83f43b43980bef394`, direct child of the immutable source; source→END changed exactly `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_15_ACCEPTANCE.md` and this continuity file.
- Fresh exact-END gates: R0 Repository Guard #1966 / `33257412850` SUCCESS; Python Core #1941 / `33257412849` SUCCESS 5/5 with Ubuntu **1731 passed / 13 skipped / 46 warnings** and R7/R8/R9 PASS; KodeStudio UI Smoke #1906 / `33257412847` SUCCESS; R14 Service Operations Resilience Acceptance #3 / `33257412881` SUCCESS Ubuntu 24.04 + Windows 2025 with 24/24 deterministic checks.
- Fresh END artifacts: Ubuntu `9716228073` / `sha256:97f82c4203d6d8987883849069c3bd8f47345b90d6078c2fcedf236c5c237bec`; Windows `9716231809` / `sha256:87fa03305606e02cc7758cdbd334e1f545023792859cc825323afa096eec1573`.
- PR #285 merged only with `expected_head_sha=80bd6853664ab9f41fd41fb83f43b43980bef394` as implementation merge `53373e78c60d4a338e9313496a822c93ab334e68`.
- Manual/provider state remains **CONDITIONAL / NOT TRIGGERED**. No external-provider quota/cost/load, Internet-scale, multi-region or PostgreSQL PITR capability is claimed.
- The sole remaining R14.15 action is exactly one continuity-only normalization commit from implementation merge `53373e78c60d4a338e9313496a822c93ab334e68`, followed by fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke, then an `expected_head_sha` merge. No plan or technical file may change during normalization.

## Next authorized action

Validate and merge the unique R14.15 continuity-only normalization candidate. Its diff from implementation merge `53373e78c60d4a338e9313496a822c93ab334e68` must contain only `docs/continuity/KODEPOIA_CONTINUITY.md`; fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke must all succeed before merge. Only the resulting normalized `main` authorizes R14.16 START-sync. R14.16–R14.17 remain PLANNED until then.'''
assert text.count(old_tail) == 1, text.count(old_tail)
text = text.replace(old_tail, new_tail, 1)

assert 'END-SYNC PENDING' not in text
assert 'three-file R14.15 END-sync' not in text
assert '53373e78c60d4a338e9313496a822c93ab334e68' in text
assert '80bd6853664ab9f41fd41fb83f43b43980bef394' in text
path.write_text(text, encoding='utf-8', newline='\n')
