# R13.7 — Google Play readiness design

## Scope

R13.7 models Google Play release preparation and optional credential capability without publishing. The core evaluator is local, deterministic, network-free, and consumes public/digested Android build/signing evidence rather than private key material.

The authoritative runtime module is `src/kodepoia/mobile/google_play.py`. Its output reuses the R13.1 `StoreReleaseStatus` / `StoreReadinessState` contract, binds an AAB digest to Android build/signing evidence, and never represents a successful Play Console publication.

## Policy snapshot model

`GooglePlayPolicySnapshot` is explicitly dated. The checked-in acceptance snapshot is observed on **2026-08-26** and is intentionally freshness-bounded to 30 days by Kodepoia governance. That 30-day horizon is a Kodepoia refresh rule, not a Google promise that policy is stable for 30 days. A stale snapshot produces `policy_snapshot_stale` and cannot claim `CURRENT` or store readiness.

The snapshot records these current official facts:

- ordinary Android phone/tablet new apps and updates require API 35 before 2026-08-31 and API 36 starting 2026-08-31;
- internal, closed, open and production release contexts are modeled; internal testing supports up to 100 testers;
- an app exclusively active on internal testing is exempt from the Data safety section; closed/open/production are not;
- current main-listing limits are 30 characters for app name, 80 for short description and 4000 for full description;
- staged rollout percentage is an update concept and is unavailable on a first release;
- apps on Google Play need IARC content-rating evidence;
- high-risk/sensitive permissions may require a Play permissions declaration;
- the 12-testers/14-continuous-days rule is scoped to personal developer accounts created after 2023-11-13 and is not treated as a universal organization-account rule.

Official sources retained by the snapshot:

- `https://developer.android.com/google/play/requirements/target-sdk`
- `https://support.google.com/googleplay/android-developer/answer/11926878`
- `https://support.google.com/googleplay/android-developer/answer/9845334`
- `https://support.google.com/googleplay/android-developer/answer/9859152`
- `https://support.google.com/googleplay/android-developer/answer/10787469`
- `https://support.google.com/googleplay/android-developer/answer/9898843`
- `https://support.google.com/googleplay/android-developer/answer/9859348`
- `https://support.google.com/googleplay/android-developer/answer/14151465`
- `https://support.google.com/googleplay/android-developer/answer/9859455`

No policy value is inferred from a live Play account during core acceptance.

## Release and artifact binding

`PlayReleaseIntent` models track, first-release/update intent, optional rollout percentage, and optional planned tester count. `PlayAabCandidate` binds:

- application id;
- AAB SHA-256;
- target SDK;
- Android build-evidence SHA-256;
- R13.5 signing state;
- signing inspection artifact SHA-256.

`PlayAabCandidate.from_evidence()` accepts only PASS R13.4 build evidence containing exactly one validated AAB and matching R13.5 AAB signing evidence. A signing-artifact digest differing from the candidate AAB is rejected as substitution.

A candidate that is only `UNSIGNED`, `DEBUG_SIGNED`, `TEST_SIGNED` or `SIGNING_UNAVAILABLE` cannot manufacture Play signing readiness. `UPLOAD_SIGNED` and `PLAY_APP_SIGNING_READY` are the only store-signing states accepted by the readiness evaluator. This remains state/evidence modeling; R13.7 does not request a production private key.

## Store metadata and declarations

`PlayStoreMetadata` contains an application id, canonicalized localized listings and public asset digests. It stores no local source paths. Listing lengths are checked against the active policy snapshot rather than hard-coded inside the listing type.

`PlayDataSafetyDeclaration` keeps only readiness facts in durable evidence. A completed declaration requires an HTTPS privacy-policy reference and confirmation that third-party SDK behavior was reviewed. The report retains only a declaration digest and booleans, not the URL itself.

`PlayContentRatingDeclaration` binds completed content-rating state to a questionnaire digest. Permission and SDK declarations are explicit developer-supplied policy evidence: Kodepoia does not guess business-purpose compliance from permission names. If a permission is marked as requiring a Play declaration and that declaration is incomplete, readiness is blocked. SDK policy review and Data safety accounting are likewise fail-closed when required.

## Account-scoped rules

`PlayAccountContext` distinguishes `unknown`, `personal`, and `organization`. The post-2023-11-13 personal-account closed-test rule is applied only to the matching personal-account context. Open/production capability does not become ready by pretending an unknown account satisfies account-scoped requirements.

A live account is **not** required for internal/closed dry-run readiness acceptance. Live tester enrollment and production-access approval remain outside core R13.7 evidence.

## Optional API boundary

`GooglePlayApiCapability` has only `DISABLED` and `DRAFT_ONLY` modes. A draft-only capability requires a `SecretRef`; authorization checks resolve that reference through `KodeSecrets` but `to_dict()` emits only the reference metadata. The capability always emits `publish_allowed: false`. There is deliberately no auto-publish method in R13.7.

A future live adapter may use this capability only after an explicitly authorized credential is available. Such a live action is a conditional manual/account boundary and cannot be used to satisfy the core dry-run gate.

## Determinism and durable evidence

`GooglePlayReadinessReport` contains exact source SHA, evaluation date, policy snapshot digest/freshness, release intent, public AAB identity, digests of metadata/declarations/account context, deterministic findings, and canonical `StoreReleaseStatus`. It enforces `dry_run=true` and `publish_attempted=false` at construction.

The JSON schema is `schemas/r13/google-play-readiness.schema.json` and rejects unknown top-level fields, including any attempted live token/secret field.
