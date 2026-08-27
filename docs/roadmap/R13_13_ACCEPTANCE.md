# R13.13 — KodeRelease acceptance

**Status:** PENDING EXACT-HEAD ACCEPTANCE  
**Authorized base:** `bad4790bbc6a34c42bbc86d45db013722a25fdae`  
**Branch:** `r13/13-koderelease`  
**Manual:** NONE

## Frozen acceptance claim

R13.13 is accepted only if KodeRelease provides a deterministic local release authority over already accepted mobile artifacts and fails closed on version/build regression, artifact/evidence substitution, released-version mutation, stale concurrent promotion and invalid rollback. The core claim explicitly excludes live Google Play/App Store publication and any self-updater behavior.

## Required implementation artifacts

- `src/kodepoia/mobile/release.py`
- `schemas/mobile-release-v1.schema.json`
- `tests/test_mobile_r13_13_release.py`
- `docs/roadmap/R13_13_DESIGN.md`
- `docs/roadmap/R13_13_ACCEPTANCE.md`
- start/end synchronization in `docs/roadmap/R13_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`

No new external-tool workflow is required unless implementation later introduces a real network/store/tool execution seam. Such a seam is not part of the frozen core design.

## Focused acceptance cases

1. strict SemVer 2.0.0 parsing rejects leading zeroes and malformed prerelease/build values;
2. SemVer ordering handles numeric prerelease identifiers and ignores build metadata for precedence;
3. candidate serialization/digests are deterministic independent of input ordering;
4. platform/package mismatch is rejected;
5. Android artifacts require `versionCode`; Apple artifacts require Apple build mapping;
6. release candidate requires bounded evidence plus changelog/SBOM/compliance digests;
7. first valid promotion succeeds and advances authority revision exactly once;
8. stale expected revision produces deterministic concurrency conflict and leaves prior state unchanged;
9. train/channel or prior-authority mismatch fails without mutation;
10. candidate/artifact/evidence digest substitution is rejected independently;
11. lower/equal product-version precedence is rejected for forward promotion;
12. Android versionCode and Apple build-number regression are rejected even when product SemVer increases;
13. an already released semantic version cannot be reused with different candidate/artifact content;
14. successful promotion seals the released version and creates a bounded rollback point for the former authority;
15. rollback requires exact revision and same authority and restores only a known immutable local release point;
16. rollback never claims a remote store mutation or installed-client downgrade;
17. Google staged rollout intent requires bound provider policy evidence and a bounded percentage;
18. App Store phased intent cannot choose arbitrary rollout percentages and current schedule evidence remains provider-versioned;
19. provider policy substitution/mismatch fails closed;
20. durable release candidate validates against `mobile-release-v1.schema.json`;
21. no secret/token/raw-command/network publication field exists in the core durable model.

## Current official evidence used by the design

External facts are not PASS evidence for implementation; they only define truthful provider-capability constraints.

- SemVer 2.0.0: https://semver.org/
- Google Play staged rollout: https://support.google.com/googleplay/android-developer/answer/6346149
- Google Play full rollout halt: https://support.google.com/googleplay/android-developer/answer/16285429
- Apple phased release: https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases

## Required exact-head technical gates

The technical candidate must have all of the following on the **same exact SHA**:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS, including complete OS/package matrix;
- KodeStudio UI Smoke — SUCCESS.

Focused R13.13 tests must be included in Python Core and pass on supported CI platforms.

## End synchronization and merge rule

After one technical candidate passes, this document, `R13_PLAN.md` and continuity may record the accepted technical facts. Any such documentary byte change produces a new final head. The same three required gates must then pass freshly on that exact final head before merge.

Implementation merge must use `expected_head_sha=<final-head>`.

After implementation merge, exactly one continuity-only normalization is permitted. Its exact head must pass fresh R0 Repository Guard + Python Core + KodeStudio UI Smoke before normalization merge. R13.14 stays `PLANNED` until normalized main is established.

## Manual gate

**NONE.** No Play Console account, App Store Connect account, production signing identity, service-account credential, token, physical device or live store mutation is required for R13.13 core acceptance. If implementation unexpectedly becomes dependent on such a prerequisite, this acceptance contract must not be marked PASS; the scope must remain blocked rather than requesting secrets in chat.
