# R13.15 — Current store compliance engine design

**Subdivision:** R13.15  
**Branch:** `r13/15-store-compliance-engine`  
**Authorized normalized base:** `80e9ae84f4c9edd8b2e41eadb93310abae6e442f`  
**Architecture:** v1.0 frozen  
**Manual:** NONE for deterministic/local evaluation  
**Evidence baseline retrieved:** 2026-08-27

## Purpose

R13.15 turns mutable mobile-store policy into versioned, inspectable evidence instead of hard-coded folklore. The core does **not** decide law, promise store acceptance, query a live provider account, publish an app, or silently fetch policy pages. It deterministically evaluates bounded rule evidence that already carries source provenance, dates and scope.

The durable output binds the exact source Git SHA, rule-set/input digests, applicable rule evidence, current/future/expired/stale/unofficial state, local findings, conflicts, account-only confirmations and third-party SDK declaration findings. Every output fixes `legal_certification=false` and `live_account_query_attempted=false`.

## Existing contracts reused

R13.15 layers above accepted R13 contracts instead of replacing them. `MobilePlatform` and canonical digest helpers remain in `kodepoia.mobile.contracts`; R13.7 `google_play.py` remains the provider-specific dry-run adapter and Play metadata/Data Safety/permissions/SDK model; accepted Apple Xcode/signing/testing evidence remains the source of Apple build/toolchain facts; R13.13 release evidence remains release-candidate authority; R13.14 diagnostics is not repurposed as compliance evidence. R7 ResearchGuard remains the external-research/provenance boundary.

No R1–R12 or earlier R13 architecture boundary changes.

## New durable model

`src/kodepoia/mobile/compliance.py` introduces a provider-neutral layer.

### ComplianceRule

A rule carries stable `rule_id`, provider, fact/requirement key, comparison operator, expected value, HTTPS source URL, SHA-256 of captured source evidence, `retrieved_on`, `effective_from`, optional `expires_on`, bounded freshness window, platform/region/app-category scope, severity/remediation and `account_only`.

Mutable values such as target API 36 or Xcode 26 are therefore **rule data**, not architecture constants.

The bounded v1 operator set is `PRESENT`, `TRUE`, `MIN_INTEGER`, `EQUALS`, `CONTAINS_ALL`; arbitrary executable expressions are not allowed.

### Currentness

For the requested evaluation date, each applicable rule is classified `CURRENT`, `FUTURE`, `EXPIRED`, `STALE` or `UNOFFICIAL`. A future rule does not override a valid predecessor before its effective date. Expired/stale/unofficial evidence remains visible but cannot satisfy a current requirement. If an applicable requirement has no current official rule, readiness fails closed.

### Provider authority

A rule may retain any HTTPS research source so unofficial evidence can be shown explicitly, but it can be `CURRENT` only when its host matches provider authority:

- Google Play: `support.google.com`, `developer.android.com`;
- Apple App Store: `developer.apple.com`.

A copied blog/search result can therefore never silently become current policy authority.

### Scope and conflicts

Rules are scoped by platform, region (`GLOBAL` or ISO alpha-2) and app category (`all` wildcard). Two simultaneous current official rules are a conflict when they govern the same provider/requirement, overlap in scope and disagree on operator or expected value. The evaluator emits a `CONFLICT` blocker and never guesses a winner.

### Account-only state

A current `account_only=true` rule without explicit account-derived evidence yields `NEEDS_ACCOUNT_CONFIRMATION`. This is neither a fabricated PASS nor automatically a blocker for non-live readiness. The core contains no Play Console/App Store Connect client.

### Third-party SDK inventory

`ThirdPartySdkEvidence` records SDK id/version, platforms, data-practice review, Google Data Safety accounting, Apple App Privacy accounting, Apple privacy-manifest presence, permissions and data types. Narrow invariant checks block an unreviewed SDK, a Google SDK omitted from Data Safety evidence, or an Apple SDK omitted from App Privacy evidence. Whether a particular SDK itself must ship an Apple privacy manifest remains mutable rule/evidence, not a universal constant.

## Official-source baseline retrieved 2026-08-27

These facts seed acceptance fixtures/docs only; none is hard-coded into evaluator logic.

### Google Play target API

Source: `https://support.google.com/googleplay/android-developer/answer/11926878`

At retrieval, ordinary new apps and updates require Android 16 / API 36 from **2026-08-31**; Wear OS/Android Automotive and Android TV/XR have provider-specific target treatment; an extension path to **2026-11-01** is documented. The engine therefore needs effective dates and scoped exceptions rather than one global target constant.

### Google Data Safety / SDK responsibility

Sources:

- `https://support.google.com/googleplay/android-developer/answer/10787469`
- `https://support.google.com/googleplay/android-developer/answer/13323374`
- `https://support.google.com/googleplay/android-developer/answer/10144311`

The provider states developers are responsible for complete/accurate user-data and Data Safety declarations, including data handled through integrated third-party libraries/SDKs.

### Google future-sensitive-permission evidence

Source: `https://support.google.com/googleplay/android-developer/answer/16558241`

At retrieval, Location Permissions and Contacts Permissions changes are identified as effective **2026-10-28**. R13.15 represents these as `FUTURE` before that date rather than prematurely enforcing them.

### Apple upload toolchain

Source: `https://developer.apple.com/news/upcoming-requirements/`

Since **2026-04-28**, App Store Connect uploads must use Xcode 26 or later and the relevant 26-series SDK. The exact version/date is rule evidence, not engine logic.

### Apple privacy manifest / required-reason APIs

Sources:

- `https://developer.apple.com/documentation/bundleresources/privacy-manifest-files`
- `https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api`

Apple documents `PrivacyInfo.xcprivacy`, data-collection declarations, required-reason API categories and approved reasons. App/SDK required-reason use must be represented in the appropriate privacy manifest.

### Apple App Privacy

Source: `https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/`

App Privacy responses must include app and integrated third-party partner practices, remain accurate/up to date, and include a privacy-policy URL.

### Apple age rating

Source: `https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating`

Age rating is required, questionnaire-driven and can have region-specific results; an unrated app cannot be published on the App Store.

## Evaluation algorithm

Given `source_sha`, date, context, `ComplianceRuleSet` and `ComplianceInput`:

1. validate bounded identifiers, dates, URLs, hashes, fact values, SDK inventory and provider/platform pairing;
2. select matching provider/platform/region/category rules;
3. classify currentness;
4. preserve non-current evidence;
5. require at least one current official rule per applicable requirement;
6. detect overlapping current-rule conflicts;
7. evaluate current non-account rules against local facts;
8. emit account-only confirmations without live query;
9. evaluate bounded SDK inventory invariants;
10. compute `BLOCKED`, `READY_WITH_WARNINGS` or `READY`;
11. emit deterministic snapshot/digest.

No network I/O, subprocess, credential resolution, store mutation or publication belongs to this algorithm.

## Fail-closed behavior

R13.15 rejects or blocks malformed Git/source hashes, malformed dates, retrieval dates after evaluation, malformed/non-HTTPS sources, invalid provider/platform pairs, duplicate rules/facts/SDK ids, missing current official evidence, stale-only/unofficial-only evidence, current-source conflicts, missing current facts, unreviewed SDK practices and provider declarations that omit integrated SDK practices.

## Durable schema

`schemas/store-compliance-v1.schema.json` describes the emitted snapshot. The snapshot embeds applicable rules so source URL, source digest, dates, scope, expected value and remediation remain inspectable rather than hidden behind only a ruleset digest. Schema v1 pins exact Git/SHA-256 shapes, bounded enums/scopes/findings, `legal_certification=false` and `live_account_query_attempted=false`.

## Security/privacy and manual state

No credentials, store-account token, user telemetry or publication path is added. External source retrieval remains governed ResearchGuard work. **Manual: NONE.** Live account forms may remain `NEEDS_ACCOUNT_CONFIRMATION`; this is an explicit capability boundary, not missing core evidence.

## Acceptance gates

Required exact-head gates are R0 Repository Guard, full Python Core and KodeStudio UI Smoke. Existing mobile workflows may supply additional regression evidence but do not substitute. After technical acceptance, plan+continuity end-sync changes must be re-gated on the final exact SHA, then merged with `expected_head_sha`, followed by exactly one continuity-only normalization before R13.16.
