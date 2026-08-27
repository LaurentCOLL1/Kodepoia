# R13.15 — Store compliance acceptance

**Subdivision:** R13.15  
**Branch:** `r13/15-store-compliance-engine`  
**Authorized normalized base:** `80e9ae84f4c9edd8b2e41eadb93310abae6e442f`  
**Manual:** NONE  
**Status:** technical candidate ACCEPTED; final end-sync exact-head re-gates pending

## Frozen claim under test

R13.15 proves Kodepoia can evaluate current mobile-store readiness from deterministic, provider-sourced, date-scoped evidence without embedding mutable 2026 policy values as architecture constants.

The accepted core must retain source URL/source SHA-256/retrieved-effective-expiry dates; distinguish current/future/expired/stale/unofficial evidence; fail closed when no current official evidence exists; surface overlapping current-source conflicts; evaluate provider/platform/region/category scope; support Google target API/Data Safety/permissions/content-rating-compatible facts; support Apple SDK/privacy-manifest/required-reason/App Privacy/privacy-policy/age-rating-compatible facts; account for third-party SDK practices; support localization/accessibility/store-asset facts; preserve account-only provider forms as `NEEDS_ACCOUNT_CONFIRMATION`; remain advisory with no legal-certification claim and no live account query.

## Official current-evidence baseline

Baseline retrieval date: **2026-08-27**.

### Google Play target API

Source: `https://support.google.com/googleplay/android-developer/answer/11926878`

Acceptance boundary fixture:

- predecessor ordinary-mobile rule: API 35 through 2026-08-30;
- successor ordinary-mobile rule: API 36 effective 2026-08-31.

Expected behavior:

- 2026-08-30 / target 35: predecessor CURRENT, successor FUTURE, readiness may pass;
- 2026-08-31 / target 35: successor CURRENT, readiness BLOCKED;
- 2026-08-31 / target 36: successor passes.

Dates/values are fixture rule data; the evaluator contains no target-API calendar.

### Google sensitive permissions future-effective evidence

Source: `https://support.google.com/googleplay/android-developer/answer/16558241`

The provider describes Location and Contacts Permissions changes effective **2026-10-28**. On 2026-08-27 the future rule must remain `FUTURE`, a valid predecessor remains current, and the future evidence must not silently override it.

### Google SDK/Data Safety responsibility

Sources:

- `https://support.google.com/googleplay/android-developer/answer/10787469`
- `https://support.google.com/googleplay/android-developer/answer/13323374`
- `https://support.google.com/googleplay/android-developer/answer/10144311`

Expected: third-party SDK data practices not reviewed -> blocker; SDK omitted from local Google Data Safety accounting -> blocker.

### Apple toolchain/privacy/rating

Sources:

- `https://developer.apple.com/news/upcoming-requirements/`
- `https://developer.apple.com/documentation/bundleresources/privacy-manifest-files`
- `https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api`
- `https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/`
- `https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating`

Baseline evidence can express Xcode 26+/26-series SDK effective 2026-04-28, required-reason codes as rule data, required App Privacy/privacy-policy evidence, integrated-SDK disclosure and required/region-sensitive age rating. No version/code/category is hard-coded in engine logic.

## Focused adversarial tests

`tests/test_mobile_r13_15_store_compliance.py` covers:

1. current official minimum rule pass;
2. Google API 36 effective-date boundary;
3. stale-only evidence cannot claim current;
4. unofficial-only evidence cannot claim current;
5. simultaneous current official conflict becomes blocker;
6. future policy does not prematurely override current predecessor;
7. missing account-only state becomes `NEEDS_ACCOUNT_CONFIRMATION`;
8. explicit account evidence evaluates normally without live query;
9. Google SDK review/Data Safety omissions block;
10. Apple SDK App Privacy omission blocks;
11. Apple required-reason set evaluation;
12. store localization/assets/accessibility/privacy helper;
13. region/category scope isolation;
14. deterministic rule/input digests under reordering;
15. duplicate rule/fact rejection;
16. malformed date/hash/URL/provider-platform rejection;
17. future retrieval timestamp rejection;
18. durable schema pins advisory/non-live invariants.

Before repository submission, the module was syntax-compiled and these 18 focused tests were run against a minimal local stub of the already accepted `MobilePlatform`/canonical-digest contract: **18 passed**. This is development preflight only; canonical acceptance is GitHub exact-head CI.

## Fail-closed acceptance table

| Condition | Required result |
| --- | --- |
| No applicable provider rule | `BLOCKED` |
| Applicable requirement has stale-only evidence | `BLOCKED`, no current policy claim |
| Applicable requirement has unofficial-only evidence | `BLOCKED`, no current policy claim |
| Future successor + valid current predecessor | predecessor remains governing current rule |
| Current official rules conflict | explicit `CONFLICT` blocker |
| Current local requirement missing/false | rule severity applied |
| Account-only rule, no account evidence | `NEEDS_ACCOUNT_CONFIRMATION`, no live query |
| SDK data practices not reviewed | blocker |
| Google SDK omitted from Data Safety | blocker |
| Apple SDK omitted from App Privacy | blocker |
| Invalid source hash/date/HTTPS/scoping | reject |
| Retrieval date after evaluation | reject |
| Attempted legal-certification flag | reject |
| Attempted live-account-query flag | reject |

## Determinism

Deterministic order is enforced for rules, facts, SDK inventory, scope sets, set-valued facts, findings, current/non-current rule IDs and account confirmations. Rule-set, input and snapshot digests use the existing canonical mobile JSON hashing contract. Equivalent inputs in different iteration order must produce identical durable digests.

## Currentness/conflict truthfulness

HTTPS alone is insufficient for `CURRENT`. Provider authority is `support.google.com`/`developer.android.com` for Google Play and `developer.apple.com` for Apple. Nonofficial HTTPS evidence may be retained as `UNOFFICIAL` but cannot satisfy current official requirements. Future rules remain future until `effective_from`; stale evidence exceeds `freshness_days`; expiration occurs after explicit `expires_on`; no conflict heuristic guesses a winner.

## Account boundary

R13.15 has no provider-account client. `ComplianceContext.account_connected` means explicit account-derived evidence was supplied by a caller; it does not authorize network I/O. Missing account-only evidence remains `NEEDS_ACCOUNT_CONFIRMATION` and `live_account_query_attempted=false`.

## Legal/readiness boundary

Every durable snapshot enforces `legal_certification=false` and `live_account_query_attempted=false`. `READY` means supplied current provider evidence and local facts satisfy deterministic readiness checks. It does not mean legal certification, Play/App Review approval, publication success, account-form submission or future continued compliance.

## Required exact-head CI

A candidate is accepted only when the **same exact Git SHA** has R0 Repository Guard SUCCESS, full Python Core SUCCESS and KodeStudio UI Smoke SUCCESS. If end-sync changes bytes, all three must rerun on the final end-synchronized SHA before merge.

## Accepted technical candidate

Exact Git SHA **`dc9e04b1d0170b889ae02231a68304e7b7a11c60`** passed R0 Repository Guard #1715 / `33097922318`, full Python Core #1689 / `33097922338`, and KodeStudio UI Smoke #1656 / `33097922322`, all SUCCESS on that exact SHA. Full Python Core includes Ubuntu/Windows tests, Ubuntu/Windows package builds and the internal KodeStudio smoke; focused R13.15 tests are part of the repository suite. Directly relevant existing regressions also passed: Google Play Readiness #179 / `33097922247` on Ubuntu+Windows and Apple Xcode Acceptance #162 / `33097922206` on hosted macOS. No live account/device/publication evidence is claimed.

Because this acceptance/end-sync documentation changes bytes after the technical candidate, these records are not themselves merge authority. Fresh R0 + full Python Core + KodeStudio UI Smoke must pass on the final end-synchronized SHA before PR #249 merges with `expected_head_sha`. Manual remains **NONE**.

## Merge/normalization rule

After final exact-head success: merge implementation PR with `expected_head_sha`; create exactly one normalization branch from that merge; modify only `docs/continuity/KODEPOIA_CONTINUITY.md`; verify one-file diff; run fresh exact-head R0 + Python + UI; merge with `expected_head_sha`; only the resulting normalized `main` authorizes R13.16.

## Manual state

**NONE.** No Play Console/App Store Connect account, credential/token, production signing key, physical device, live form, upload or publication is required for frozen R13.15 core. Account-only live facts remain explicit confirmations rather than fabricated acceptance evidence.
