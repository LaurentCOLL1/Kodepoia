# R15.1 Acceptance — Experience contracts, eligibility state machine + training-data trust boundary

## Decision

**PASS — technical source accepted.**

Immutable technical source: `2da5e5d5aa712462c898270c41c5cafb42e6aeaa`.

R15.1 is technically accepted with manual state **NONE**. R15.2 remains unauthorized until the R15.1 END-head passes fresh exact-head gates, PR #294 merges with exact expected-head protection, and the unique post-merge continuity-only normalization passes fresh R0/Python/UI and merges.

## Scope accepted

The accepted source introduces the immutable R15 experience contract package, deterministic experience identity, governed digest-bound content references, provenance/transformation descriptors, independent fail-closed training-authorization decisions, the explicit experience state machine, benchmark-protection veto, canonical/redacted serialization, repository/storage protocols, JSON Schema 2020-12 validation and focused cross-platform adversarial tests.

Collection, actual sanitization, SPDX license parsing/policy, revocation propagation, deduplication, benchmark near-match scanning, dataset construction and training remain outside R15.1.

## Immutable source and exact-head gates

- normalized R15 planning main: `29ae0ffabb7ffa974c4d544e33bfe54f0fa403f1`;
- R15.1 clean START-head: `a474d0c85d27ca7113a8044b2c29a5e664ebd352`;
- immutable technical source: `2da5e5d5aa712462c898270c41c5cafb42e6aeaa`;
- START-main -> source: 10 commits; net diff is exactly 7 files (2 START-sync documents + 5 R15.1 technical/test/schema/workflow surfaces); no staging helper survives;
- R15.1 Experience Contracts Acceptance #6 / run `33271323481`: **SUCCESS** Ubuntu + Windows, exact source checkout;
- R0 Repository Guard #2057 / run `33271323508`: **SUCCESS**;
- Python Core #2032 / run `33271323458`: **SUCCESS 5/5**;
- KodeStudio UI Smoke #1997 / run `33271323468`: **SUCCESS**;
- full Ubuntu Python Core: **1778 passed / 14 skipped / 46 warnings**; R7/R8/R9 integrated validation PASS;
- dedicated R15.1 focused acceptance: **18 passed** on Ubuntu and **18 passed** on Windows; Ruff and compileall PASS on both.

## Contract/schema identity

- Python schema name: `kodepoia.experience.record`;
- schema version: `1`;
- JSON Schema dialect: `https://json-schema.org/draft/2020-12/schema`;
- schema path: `schemas/experience-record-v1.schema.json`;
- schema Git blob identity at immutable source: `278d0ef40fc41add884729beb6ee9453c153422c`.

The focused tests call `Draft202012Validator.check_schema()` and validate a serialized `ExperienceRecord` against the checked-in schema.

## Frozen training-data trust-boundary conclusions

All of the following are acceptance requirements and pass on the immutable source:

1. training authorization defaults to `UNKNOWN`, therefore non-eligible;
2. source scope, consent, provenance, license and privacy are independent required decisions;
3. every required decision must be `ALLOW` before `ELIGIBLE`;
4. **sanitization/redaction PASS cannot launder a `DENY`, `UNKNOWN` or `REVIEW` source into training eligibility**;
5. benchmark-protected content is a hard veto independently of other authorization decisions;
6. the happy path is `OBSERVED -> ELIGIBLE -> SANITIZED -> CURATED -> DATASET_INCLUDED`;
7. skipping required promotion states is rejected;
8. `SANITIZED`, `CURATED` and `DATASET_INCLUDED` require PASSED sanitization evidence with sanitizer digest;
9. `REJECTED`, `QUARANTINED`, `REVOKED` and `EXPIRED` are terminal in the R15.1 state model;
10. a dataset-included record may only transition to `REVOKED` or `EXPIRED`;
11. deterministic `ExperienceId` is immutable;
12. cross-workspace content reference is rejected;
13. absolute, drive-qualified and traversal storage keys are rejected;
14. audit summary omits governed storage key and raw payload;
15. canonical JSON and contract SHA-256 are stable;
16. JSON Schema 2020-12 accepts the canonical contract;
17. benchmark protection is tested adversarially;
18. the explicit denied-source-plus-sanitizer-PASS laundering fixture is rejected.

## Data-minimization and non-laundering rule

The following rule is normative for all later R15 subdivisions:

> Secret or identifying material may be removed from an example only when the underlying source is otherwise independently authorized for training. Redaction never turns a forbidden, private, out-of-scope, unconsented, unknown-provenance or policy-disallowed source into admissible training data. Such a source is rejected/quarantined/revoked as a whole according to policy.

R15.3 must preserve and strengthen this invariant when implementing real sanitizers and license/provenance policy.

## Rejected / superseded candidates

- `77f3ce9a935ea6c1816f3f6095d0d2b62db527aa`: superseded as evidence authority because the first R15.1 PR workflow checked out GitHub's synthetic pull-request merge ref rather than the PR head. Its functional test result is not reused as exact-head evidence.
- `ea57df89e172d97f91498d758373e13048d7e707`: rejected as decision authority. Exact-head checkout and all 18 focused tests passed, but Ruff correctly failed one `E501` line-length violation. The source was reformatted and all gates were rerun on `2da5e5d5...`; no failed-candidate result is used for acceptance.
- the first R15.1 START-sync attempt is non-authoritative because `git diff --check` rejected Markdown trailing whitespace before implementation; the corrected START-head is `a474d0c85d27...`.

## Manual intervention

**NONE.**

No GPU, model weights, external dataset, external account, credentials, cloud service or production data are required for R15.1.

## END-sync requirement

The immutable technical source must not change. END-sync may add/update only R15.1 decision/design documentation, `docs/roadmap/R15_PLAN.md` status/completion record and `docs/continuity/KODEPOIA_CONTINUITY.md`. The resulting exact END-head must pass fresh R15.1 focused acceptance, R0 Repository Guard, full Python Core and KodeStudio UI Smoke before PR #294 may be made ready and merged with `expected_head_sha`.

**END-head re-gate marker:** the deterministic END-sync has been applied and its temporary helper removed. This documentation-only marker intentionally defines the exact branch head that must now pass the fresh END gates before merge; it does not alter the immutable technical source.
