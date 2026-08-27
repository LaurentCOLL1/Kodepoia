# R13.13 — KodeRelease design

**Status:** IMPLEMENTATION IN PROGRESS  
**Authorized base:** `bad4790bbc6a34c42bbc86d45db013722a25fdae`  
**Branch:** `r13/13-koderelease`  
**Manual:** NONE

## Frozen objective

R13.13 creates the local, deterministic `KodeRelease` authority above already accepted Android/iOS artifacts and evidence. It does not publish to a store, invoke a self-updater, install a production binary, hold store credentials, or synthesize remote rollout state.

The durable model covers:

- SemVer 2.0.0 product versions plus Android `versionCode` and Apple build-number mappings;
- `ReleaseTrainId`, channel and immutable `ReleaseCandidate` identities;
- artifact digest + provenance binding and evidence/changelog/SBOM/compliance digest binding;
- optimistic revision locking for deterministic concurrent promotions;
- immutable released-version seals;
- explicit rollout intent bound to dated provider-policy evidence;
- rollback points that restore KodeRelease local authority without claiming that already-installed client binaries were downgraded;
- fail-closed promotion semantics: every rejected promotion returns the unchanged prior authority state.

## External provider facts — versioned evidence, not architecture constants

The implementation uses current official behavior only to constrain provider-capability evidence:

1. **Semantic Versioning 2.0.0** — a released version must not have its contents modified; modifications require a new version. Build metadata does not change SemVer precedence. Source: https://semver.org/
2. **Google Play staged rollouts** — staged rollout is for app updates rather than a first publication; the percentage can be changed, a rollout can be halted and resumed, and users already served a halted staged version remain on it. Source: https://support.google.com/googleplay/android-developer/answer/6346149
3. **Google Play full-rollout halt** — current Play Console behavior can halt a fully rolled-out release (except internal track and subject to eligibility); an eligible previous fully rolled-out release may become available again. This is a provider serving behavior, not a promise that already-updated clients are downgraded. Source: https://support.google.com/googleplay/android-developer/answer/16285429
4. **Apple phased release** — current App Store Connect phased release distributes an update over seven days using provider-defined percentages 1/2/5/10/20/50/100; it may be paused for a cumulative 30 days and can be accelerated to all users. Source: https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases

Each provider-policy object therefore carries source URL, retrieval date and a content digest. KodeRelease never treats these mutable facts as permanent constants and never upgrades policy evidence into live account capability.

## Core model

### `SemanticVersion`

Strict SemVer 2.0.0 parser/comparator. Numeric major/minor/patch and prerelease precedence are implemented exactly; build metadata is ignored for precedence. A candidate with equal or lower precedence than the current authority is not a forward promotion.

### `ReleaseVersion`

Binds one product version to at least one platform build identity:

- Android `versionCode`: bounded positive integer;
- Apple build number: bounded dotted numeric identity.

A candidate containing Android artifacts requires an Android mapping; a candidate containing iOS/iPadOS artifacts requires an Apple mapping.

### `ReleaseArtifactBinding`

Binds an artifact ID, platform, package kind, artifact SHA-256 and provenance SHA-256. Android accepts APK/AAB release artifacts; Apple accepts APP/XCARCHIVE/IPA artifacts. Artifact ordering is canonical and duplicate identities fail closed.

### `ReleaseCandidate`

Frozen release candidate containing:

- candidate/train/channel identities;
- `ReleaseVersion`;
- immutable artifact bindings;
- required evidence digest set;
- changelog, SBOM and compliance digests;
- optional rollout intent.

The candidate digest, artifact-set digest and evidence-set digest are separately computed. A `PromotionRequest` must bind all three, preventing a caller from reusing an approval against substituted bytes or evidence.

### `ReleaseAuthorityState`

Immutable local authority for one train/channel. It carries:

- monotonically increasing revision;
- current authoritative candidate/artifact/version/build identities;
- immutable released-version seals;
- bounded rollback-point history.

No store account state is stored here.

### Promotion transaction

`promote_release()` is pure/deterministic. It validates in bounded order:

1. expected revision (optimistic lock);
2. train and channel identity;
3. expected prior authoritative candidate;
4. candidate/artifact/evidence digests;
5. released-version immutability;
6. product version forward precedence;
7. Android/Apple build-number monotonicity when applicable.

On any failure the original `ReleaseAuthorityState` is returned unchanged. On success revision advances exactly once and the prior authority becomes a rollback point.

### Rollback transaction

`rollback_release()` restores a known rollback point only when the expected revision matches and the point belongs to the same train/channel. It increments local revision and preserves release seals/history. It is deliberately not a store mutation and does not claim a device downgrade.

### Rollout evidence and intent

`RolloutPolicyEvidence` describes current provider capabilities. `RolloutIntent` is only an intent:

- `LOCAL` supports immediate local authority without store evidence;
- `GOOGLE_PLAY` may use immediate or explicit staged percentage intent and requires bound Play policy evidence;
- `APP_STORE` may use immediate or provider-phased intent; arbitrary user-selected percentages are rejected because current phased percentages are provider-defined.

No network endpoint, credential, token, raw store command or publish side effect exists in R13.13 core.

## Durable schema

`schemas/mobile-release-v1.schema.json` validates the canonical serialized release candidate, including strict IDs, digests, platform/package values, version mapping and rollout-intent fields. Runtime validation remains stricter where cross-field platform rules are required.

## Security / governance invariants

- no arbitrary executable, argv, endpoint or store token field;
- no private key, keystore password, App Store Connect key or Play service-account material;
- canonical JSON hashing prevents ordering-based identity drift;
- released-version seals prevent mutation under an already released semantic version;
- failed promotion cannot mutate current authority;
- stale concurrent writer cannot win because expected revision is mandatory;
- provider policy evidence cannot manufacture live publication state;
- rollback is local authority restoration only;
- public release remains an explicit user-controlled operation implemented only by an accepted capability-gated seam elsewhere.

## Acceptance gates

R13.13 introduces no new real external tool/platform seam. Required technical candidate gates are therefore:

- R0 Repository Guard;
- full Python Core;
- KodeStudio UI Smoke.

Any byte change made during end synchronization creates a new exact head and all three gates must be rerun before implementation merge with `expected_head_sha`. After merge, exactly one continuity-only normalization must pass fresh R0 + Python + UI before R13.14 can start.
