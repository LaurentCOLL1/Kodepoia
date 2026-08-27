# R13.13 — KodeRelease acceptance

**Status:** TECHNICAL CANDIDATE ACCEPTED / FINAL END-SYNC GATES PENDING  
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

## Accepted technical candidate

Exact technical candidate **`3381caa21573f44c47d354f36b0e00c4d82e454e`** passed all frozen R13.13 technical gates on that exact SHA:

- R0 Repository Guard **#1699 / `33075296657` — SUCCESS**;
- Python Core **#1673 / `33075296667` — SUCCESS**, including Ubuntu/Windows full tests, package-build Ubuntu/Windows and KodeStudio smoke job;
- KodeStudio UI Smoke **#1640 / `33075296615` — SUCCESS**.

Python Core executed the focused R13.13 tests as part of the complete suite. Additional automatically triggered regression workflows, including Apple Xcode, Apple Signing Archive, Apple SwiftUI Scaffold and Google Play Readiness, also succeeded on this candidate, but they are supplemental and do not replace the three frozen R13.13 decision gates.

No external credential, account, physical device, production signing secret or live store mutation was used or required. Manual remains **NONE**.

## Final end synchronization and merge rule

This document, `R13_PLAN.md` and continuity now end-synchronize the accepted technical facts. These documentary byte changes create a new final head, so the technical-candidate gate results above are historical evidence only for the implementation candidate and **must not** be reused to authorize merge of the final head.

The final end-synchronized head must freshly pass on one exact SHA:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS, including complete OS/package matrix;
- KodeStudio UI Smoke — SUCCESS.

Implementation PR #245 must merge with `expected_head_sha=<final-head>` only after all three are SUCCESS.

After implementation merge, exactly one continuity-only normalization is permitted. Its exact head must pass fresh R0 Repository Guard + Python Core + KodeStudio UI Smoke before normalization merge. R13.14 stays `PLANNED` until normalized main is established.

## Manual gate

**NONE.** No Play Console account, App Store Connect account, production signing identity, service-account credential, token, physical device or live store mutation is required for R13.13 core acceptance. If implementation unexpectedly becomes dependent on such a prerequisite, this acceptance contract must not be marked PASS; the scope must remain blocked rather than requesting secrets in chat.
