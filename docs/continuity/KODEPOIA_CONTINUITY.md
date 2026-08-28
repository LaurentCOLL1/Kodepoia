# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 28 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.5 COMPLETE + NORMALIZED. R14.6 is COMPLETE at technical/evidence level on `r14/06-authoritative-server-state`; R14.7–R14.17 remain PLANNED until R14.6 final END re-gates, PR #267 expected-head merge and the single continuity-only normalization merge.** R14.6 immutable technical source `a1425b53e1228f9c88ba373cdfabf1459393a7cf` passed R0 #1795 / `33193110717`, Python Core #1769 / `33193110651`, UI #1736 / `33193110643`, and R14 Authority Acceptance #3 / `33193110695`, all SUCCESS. Authority acceptance passed on Ubuntu and Windows with all ten frozen semantic checks true, identical state/event/trace digests, and `secrets_exposed=false`. Manual state: NONE.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 planning : **ACCEPTED + NORMALIZED**.
- R13 phase status: **COMPLETE + NORMALIZED**.
- R13.1–R13.14: **COMPLETE + NORMALIZED**.
- R13.14 normalized `main`: **`80e9ae84f4c9edd8b2e41eadb93310abae6e442f`** after implementation PR #247 and continuity-only normalization PR #248. Manual **CONDITIONAL / NOT TRIGGERED**.
- R13.15: **COMPLETE + NORMALIZED**. Final normalization head **`2122fd685fd20973ae045658e79d94295bb389cb`** passed R0 #1720 / `33099025034`, Python Core #1694 / `33099024801`, and KodeStudio UI Smoke #1661 / `33099024892`; normalization PR #250 merged as normalized `main` **`dce60a60b58ff2c069d689144291f8c682b7e21f`**. Manual **NONE**.
- R13.16: **COMPLETE + NORMALIZED**. Final end-synchronized implementation head **`a4c4185f6b11d4574e9ecf2f2b735c2d623155b4`** passed R0 #1726 / `33113280399`, Python Core #1700 / `33113280512`, and UI #1667 / `33113280468`; PR #251 merged as **`b1865ffff26de58f63606952f5c7b8de774e01fa`**. Single continuity-only normalization head **`9bcee3c9359f8a2340878c8310b1572f38d614df`** passed R0 #1728 / `33113689078`, Python Core #1702 / `33113689208`, and UI #1669 / `33113689114`; PR #252 merged as normalized **`main` `b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`**. Manual **NONE**.
- R13.17: **COMPLETE + NORMALIZED**. Final documentation/evidence head **`cb0c63bcdcbaf2b58b3066d311780843c2598575`** passed all 12 fresh exact-head final gates; PR #253 merged as **`f56c61dbc82efd93c08e2b29ad1acff33219689f`**. Single continuity-only normalization head **`1bc52616e5e527dadfe8feafdc0d137433b37a48`** passed R0 #1746 / `33135420877`, Python Core #1720 / `33135420870`, and UI #1687 / `33135420823`; PR #254 merged as normalized **`main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**. Manual **CONDITIONAL / NOT TRIGGERED**.
- R14 planning: **ACCEPTED + NORMALIZED**. R14.1–R14.5 are **COMPLETE + NORMALIZED**. R14.5 normalization head **`721c9949914a0952b2afe8543dd37da5f8146545`** passed R0 #1793 / `33191649309`, Python #1767 / `33191649218`, and UI #1734 / `33191649134`, all SUCCESS; PR #266 merged as normalized **`main` `1b1f40334b640afb75d8a669ad312dacb96b4e6d`**. R14.6 immutable technical source **`a1425b53e1228f9c88ba373cdfabf1459393a7cf`** passed R0 #1795 / `33193110717`, Python Core #1769 / `33193110651`, UI #1736 / `33193110643`, and R14 Authority Acceptance #3 / `33193110695`, all SUCCESS. R14.6 is **COMPLETE at technical/evidence level**; final END re-gates, PR #267 merge and one continuity-only normalization remain before it is `COMPLETE + NORMALIZED` and R14.7 is authorized. Manual for R14.6: **NONE**.

## R14 planning closure and R14.1 start authority

- Planning candidate `343b7834d8b5826d5012bf78926102725b66db7f` passed R0 #1748 / `33136015617`, Python Core #1722 / `33136015593`, and UI #1689 / `33136015584`; PR #255 merged as `808e5215e45a3a90d3037efb1a3749f01b285b9c`.
- Single planning-normalization candidate `150f7f8a127a068eb79f479d0354d25ee1262c64` changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1750 / `33136198257`, Python Core #1724 / `33136198229`, and UI #1691 / `33136198210`; PR #256 merged with expected-head protection as normalized main `27af7b80072678f509f7092cf2759683efe1224f`.
- Therefore R14 planning is authoritatively **ACCEPTED + NORMALIZED**.
- R14.1 implementation branch `r14/01-backend-contracts-boundaries` started exactly from normalized planning main `27af7b80072678f509f7092cf2759683efe1224f`. Accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, and UI #1693 / `33140670391`; final END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed fresh R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`, all SUCCESS. PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`. Single continuity-only normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python #1733 / `33141096889`, and UI #1700 / `33141096815`; PR #258 merged as normalized main `41f0775731c405a6b208baec8910bdb36a78d10e`. Therefore R14.1 is **COMPLETE + NORMALIZED** and R14.2 is authorized. Manual intervention remains **NONE**.
- Frozen R14.1 scope: provider-neutral backend contracts/identities/capability snapshots, environment and endpoint semantics, secure network/runtime boundaries, canonical/redacted evidence and adversarial SSRF protections only; no concrete auth/DB/billing/flags/content/events implementation yet.

## R14.2 start authority

- Dedicated branch: `r14/02-backend-service-intent`.
- Exact branch point: normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`.
- R14.1 is COMPLETE + NORMALIZED. R14.2 accepted immutable technical source `4e04812380a495dd799e1d7b9e96741d8688de31`, which passed R0 #1761 / `33143230642`, Python Core #1735 / `33143230580`, and UI #1702 / `33143230613`, all SUCCESS. R14.2 is COMPLETE at technical/evidence level; R14.3–R14.17 remain PLANNED pending final documentation re-gates, PR #259 merge and continuity-only normalization.
- Frozen R14.2 scope: optional Project DNA/KodeProduct backend service intent, deterministic dependency graph, conditional Wizard questions, requirements/acceptance derivation, compatibility validation, backward-compatible disabled default; no provisioning, deployment, credentials or concrete backend service implementation.
- Manual intervention: **NONE**.

## R14.2 post-merge normalization authority

- Accepted immutable technical source: `4e04812380a495dd799e1d7b9e96741d8688de31`.
- Technical gates: R0 #1761 / `33143230642`, Python Core #1735 / `33143230580`, KodeStudio UI Smoke #1702 / `33143230613`, all SUCCESS.
- Final END-synchronized head: `cc034784b6b3350f3e24ece55e5d2304fa60705c`; relative to the technical source only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_2_ACCEPTANCE.md`, and continuity changed.
- Final fresh exact-head gates: R0 #1766 / `33143514421`, Python Core #1740 / `33143514423`, UI #1707 / `33143514466`, all SUCCESS.
- Implementation/evidence PR #259 merged with `expected_head_sha=cc034784b6b3350f3e24ece55e5d2304fa60705c` as `ad5de7c1697d061946bf75220420c75b73851531`.
- Single authorized normalization branch: `r14/02-continuity-normalization`, created exactly from `ad5de7c1697d061946bf75220420c75b73851531`. Its cumulative diff MUST contain exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; no plan/code/schema/test/workflow bytes may remain changed.
- Final normalization head `b3587acf2a9c37d2e407a62bc1e805863f553564` changed exactly this continuity file and passed R0 #1768 / `33145379528`, Python Core #1742 / `33145379581`, and UI #1709 / `33145379554`, all SUCCESS.
- Normalization PR #260 merged with expected-head protection as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`. Therefore R14.2 is authoritatively **COMPLETE + NORMALIZED** and R14.3 is authorized.
- Manual intervention: **NONE**.

## R14.3 technical acceptance authority

- Dedicated branch: `r14/03-local-backend-runtime`, started exactly from normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.
- Mandatory START-sync head `86dd7e43a2d2895909f8ecd95a743099fc37c55f` changed exactly `docs/roadmap/R14_PLAN.md` and continuity before implementation.
- Accepted immutable technical source: `4de5036e7a37f949ec64ae68d9ee45e57ac99631`, tree `693662541c60387ecbb14d0994c66266696a9153`.
- Technical exact-head gates: R0 #1770 / `33146235062`, Python Core #1744 / `33146235104`, KodeStudio UI Smoke #1711 / `33146235181`, all SUCCESS.
- Ubuntu full Python suite: 1477 passed / 13 skipped / 46 warnings; Windows Core, both package builds and Python internal UI smoke also SUCCESS.
- Focused `33146069094`: 36 passed after compileall. Cross-platform focused `33146135676`: runtime tests SUCCESS on Ubuntu and Windows; a duplicate cleanup race did not affect the tested implementation and no temporary file remains in the accepted tree.
- Frozen R14.3 scope: deterministic local backend scaffold/workspace, repository-owned bounded local runner, typed configuration/environment overlays, KodeSecrets references, loopback-first bind policy, health/readiness/liveness, graceful shutdown, redacted logs and reproducible fixture service. No public deployment, auth semantics, production TLS termination, managed hosting or later R14 service semantics.
- Final END-synchronized head: `8411ce92da962a37cb9a5936bdac740d9a132204`; relative to the immutable technical source only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_3_ACCEPTANCE.md`, and continuity changed.
- Final exact-head re-gates: R0 #1775 / `33146496788`, Python Core #1749 / `33146496859`, and UI #1716 / `33146496739`, all SUCCESS.
- Implementation/evidence PR #261 merged with `expected_head_sha=8411ce92da962a37cb9a5936bdac740d9a132204` as `d288772a90d5877cabe35adb6e71f0ede32f6b8d`.
- Single authorized normalization branch: `r14/03-continuity-normalization`, created exactly from that merge. Its cumulative diff MUST contain exactly `docs/continuity/KODEPOIA_CONTINUITY.md`. After fresh R0 + full Python Core + KodeStudio UI Smoke and merge with expected-head protection, R14.3 is authoritatively **COMPLETE + NORMALIZED** and R14.4 is authorized.
- Manual intervention: **NONE**.

## R14.4 start authority

- Dedicated branch: `r14/04-auth-identity-sessions`.
- Exact branch point: normalized `main` `f28e6762830ec9a2b22ddedc24bdc9a446e5f4b2`.
- R14.1–R14.3 are COMPLETE + NORMALIZED; R14.4 is IN_PROGRESS; R14.5–R14.17 remain PLANNED.
- Current standards basis: OAuth 2.0 Security BCP RFC 9700; OIDC issuer/audience/nonce policy; WebAuthn Level 3 current published Candidate Recommendation; strict session lifecycle and token redaction.
- Core acceptance uses only deterministic local providers. No real IdP tenant, public domain, production TLS, provider client secret or authenticator registration is required. Conditional manual intervention is **NOT TRIGGERED**.
- Frozen R14.4 scope: typed auth/account/realm identities, deterministic local provider, session/access/refresh lifecycle, rotation/revocation, PKCE/state/nonce/redirect/issuer/audience/algorithm policy, passkey public-credential contracts and explicit OIDC adapter boundary; no external tenant provisioning or generalized federation.
- Accepted immutable technical source: `3660f351649e85450324df25888d577afb02b19a`. Technical gates: R0 #1779 / `33187747722`, Python Core #1753 / `33187747723`, UI #1720 / `33187747872`, all SUCCESS. Ubuntu full suite: 1494 passed / 13 skipped / 46 warnings; focused `33187554520`: 29 tests passed on Ubuntu and Windows.
- Final END-synchronized head: `05b16a796bb65d513de0b631eca432195ee01461`; relative to the immutable technical source only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_4_ACCEPTANCE.md`, and continuity changed.
- Final exact-head re-gates: R0 #1783 / `33189022908`, Python Core #1757 / `33189022727`, and UI #1724 / `33189022765`, all SUCCESS.
- Implementation/evidence PR #263 merged with `expected_head_sha=05b16a796bb65d513de0b631eca432195ee01461` as `cae2a1ddcaa79390ff923336ee331eba81937e84`.
- Single continuity-only normalization head `8601ac19b87635648aef1c5f5c37a6cb899c26be` changed exactly continuity and passed R0 #1785 / `33189536524`, Python Core #1759 / `33189536553`, and UI #1726 / `33189536543`, all SUCCESS; PR #264 merged with expected-head protection as normalized `main` `45dc68f1cd3bf05c62aede1b2519c6c513c67166`. Therefore R14.4 is **COMPLETE + NORMALIZED**.
- Manual intervention remains **CONDITIONAL / NOT TRIGGERED**.

## R14.5 start authority

- Dedicated branch: `r14/05-postgresql-persistence`.
- Exact branch point: normalized `main` `45dc68f1cd3bf05c62aede1b2519c6c513c67166`.
- R14.1–R14.4 are COMPLETE + NORMALIZED; R14.5 is IN_PROGRESS; R14.6–R14.17 remain PLANNED.
- Stable database authority for core acceptance is PostgreSQL 18.x; PostgreSQL 19 pre-release builds are not production authority.
- Frozen R14.5 scope: provider-neutral PostgreSQL capability/connection policy, repository-owned migrations with checksums/rollback, transaction/unit-of-work semantics, optimistic/pessimistic concurrency, bounded deadlock retry, idempotency primitives and deterministic backup/restore evidence; no managed-cloud provisioning or production credentials.
- Manual intervention: **NONE**.
- Accepted immutable technical source: `3273ac50b43b64f6f365522f170765f44f45eedf`.
- Technical gates: R0 #1787 / `33190672723`, Python Core #1761 / `33190672676`, UI #1728 / `33190672761`, PostgreSQL Acceptance #1 / `33190672769`, all SUCCESS.
- Ubuntu full suite: 1509 passed / 13 skipped / 46 warnings. PostgreSQL focused suite: 44 passed against PostgreSQL 18.6 (`180006`). All eight persistence checks passed; migration digest `b96484ae6d56fe54b013b975572310d8daf44cf43116c5c43edc73845856b71b`, restore digest `bcc5ae8b707231568263e0f52c8426dd956a67e4e131bcf97becb4b45ccb9f6e`, no secrets exposed.
- Final END-synchronized head: `9606436453c6cc2bed90120bc3f9069311ef65e0`; relative to the immutable technical source only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_5_ACCEPTANCE.md`, and continuity changed.
- Final exact-head re-gates: R0 #1791 / `33191315047`, Python Core #1765 / `33191315090`, UI #1732 / `33191315092`, and PostgreSQL Acceptance #5 / `33191315129`, all SUCCESS.
- Implementation/evidence PR #265 merged with `expected_head_sha=9606436453c6cc2bed90120bc3f9069311ef65e0` as `39d8aa12e3d36a618376f7060d1088f9fe61ba32`.
- Single continuity-only normalization head `721c9949914a0952b2afe8543dd37da5f8146545` changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1793 / `33191649309`, Python Core #1767 / `33191649218`, and UI #1734 / `33191649134`, all SUCCESS; PR #266 merged with expected-head protection as normalized `main` `1b1f40334b640afb75d8a669ad312dacb96b4e6d`. Therefore R14.5 is **COMPLETE + NORMALIZED** and R14.6 was authorized.

## R14.6 technical acceptance authority

- Dedicated branch: `r14/06-authoritative-server-state`.
- Exact branch point: normalized `main` `1b1f40334b640afb75d8a669ad312dacb96b4e6d`.
- Mandatory START-sync head: `5278559563b05d42e132518b3d8581531bd06ac3`; cumulative START-sync changes were exactly `docs/roadmap/R14_PLAN.md` and continuity before implementation.
- R14.1–R14.5 are COMPLETE + NORMALIZED; R14.6 is now COMPLETE at technical/evidence level; R14.7–R14.17 remain PLANNED until final END re-gates, merge and normalization.
- Standards/security basis for this work cycle: RFC 9110 HTTP semantics; RFC 6455 WebSocket plus RFC 8441/9220 HTTP/2 and HTTP/3 bootstrapping; OWASP API Security 2023 object/function authorization and bounded resource-consumption risks. These are transport/security compatibility references, not sources of application authority.
- Frozen R14.6 scope: authoritative domain/command/state identities; actor/session/object authorization; current-revision and sequence enforcement; idempotent duplicate handling; atomic state+event outcome; provider-neutral request/realtime transport contracts; reconnect cursor/resume semantics; bounded queues/backpressure/timeouts and server-issued lease/clock policy. No matchmaking, cloud-save or product-specific gameplay rules.
- Client messages are intents only. They cannot supply trusted state revisions, authorization decisions, server timestamps, queue capacity, lease authority or event sequence truth.
- Accepted immutable technical source: `a1425b53e1228f9c88ba373cdfabf1459393a7cf`.
- Technical exact-head gates: R0 Repository Guard #1795 / `33193110717`, Python Core #1769 / `33193110651`, KodeStudio UI Smoke #1736 / `33193110643`, and R14 Authority Acceptance #3 / `33193110695`, all SUCCESS.
- Authority Acceptance #3 passed on Ubuntu and Windows. All ten frozen checks are true: `forgery`, `stale_revision`, `duplicate`, `out_of_order`, `reconnect`, `backpressure`, `transaction_event_consistency`, `deterministic_multiclient`, `lease_expiry`, and `reserved_fields`.
- Cross-platform evidence is semantically identical: final state digest `59c1afb567245df4f3521052564d0bdfbaa4a5423eb7db7997c1e20160a988a3`; event stream digest `3adad95a513ee4812126d7d9695cc297d2f57287263a5686ee1ee5c08a15e4a1`; trace digest `839f65c4ffbe019c43f6aad988ee8258945c328f348135ffef9320955102f178`; `secrets_exposed=false`.
- Ubuntu authority evidence artifact id `9694600447`, ZIP digest `sha256:ec252c2e055cdb8aa9f94b0f6273f87e6e2724b22f715b8a8e986047766b194a`; Windows artifact id `9694625857`, ZIP digest `sha256:5a2b0ad3d0841649ee3d20cc8057b3def7644f208d44e7a5bfc8154053409464`.
- END synchronization is restricted to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_6_ACCEPTANCE.md`, and continuity relative to the immutable technical source. The resulting exact END head must pass fresh R0 + full Python Core + KodeStudio UI Smoke + R14 Authority Acceptance before PR #267 may merge with `expected_head_sha`.
- After implementation/evidence merge, exactly one continuity-only normalization branch may change only this continuity file; it must pass fresh R0/Python/UI and merge with expected-head protection before R14.6 becomes **COMPLETE + NORMALIZED** and R14.7 is authorized.
- Manual intervention: **NONE**.

## R14.1 post-merge normalization authority

- Accepted immutable technical source: `84972d283f6f530ae46ebf6c0452188927b178ff`.
- Technical gates: R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, KodeStudio UI Smoke #1693 / `33140670391`, all SUCCESS.
- Final END-synchronized documentation/evidence head: `75e5d68752a56b8a21fa4842e803d86f772f7468`; relative to the technical source only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_1_ACCEPTANCE.md`, and continuity changed.
- Final fresh exact-head gates: R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, UI #1698 / `33140864338`, all SUCCESS.
- Implementation/evidence PR #257 merged with `expected_head_sha=75e5d68752a56b8a21fa4842e803d86f772f7468` as `6059b6d706d1208fdcad102c9fa217abaf31d099`.
- Single authorized normalization branch: `r14/01-continuity-normalization`, created exactly from `6059b6d706d1208fdcad102c9fa217abaf31d099`. Its final cumulative diff MUST contain exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; no plan/code/schema/test/workflow bytes may remain changed.
- This normalization candidate declares the resulting main state **R14.1 COMPLETE + NORMALIZED** and keeps R14.2 **PLANNED**. That declaration becomes authoritative only when this exact candidate passes fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and its PR merges with expected-head protection.
- Manual intervention: **NONE**.

## R12 final closure authority

- Accepted R12.16 implementation source: `1927d9ab673228101c932b1cb6b89243296ac957`.
- Final R12 evidence head: `f12132b777569a6a03171e759dd1b36d3a1858b4`.
- Canonical report `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R12.16 PR #217 merged as `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`.
- R12 normalization head `f9a1fc05708be3a4b4048b2b33e6ac228485285e` passed R0 #1594 / `32844549399`, Python #1568 / `32844549531`, UI #1535 / `32844549411`, WPF #82 / `32844549655`, WinUI3 #72 / `32844549414`, Avalonia #68 / `32844549519`, Qt6 #63 / `32844549568`, Tauri2 #54 / `32844549393`, Integrated Windows #7 / `32844549496`, all SUCCESS.
- R12 normalization PR #218 merged as `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`.
- Therefore R12 is authoritatively **COMPLETE + NORMALIZED**.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update phase-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`; synchronize continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update the same plan fields so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts; synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set truthful `BLOCKED`/`MANUAL_REQUIRED`, never synthetic `COMPLETE`.
- Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status.
- A stale subdivision index or stale phase status is a governance defect and blocks acceptance.

This rule applies to R13 and all later R phases unless a later accepted ADR explicitly changes it.

## R13 planning closure authority

### Frozen roadmap scope

R13 is exactly **Mobile / Platform / Release**: Android export/signing/AAB/APK/device tests/store; interface iOS/Mac/Xcode; DeviceLab; KodeRelease/Updater/Diagnostics; current compliance. R14 backend/live-service work remains outside R13.

### Accepted planning and normalization

- planning candidate `6f44e8faf8ef675dab5c8079541ce436ff55b4b2` passed R0 #1596 / `32846530810`, Python #1570 / `32846530804`, UI #1537 / `32846530786`;
- PR #219 merged as `9a5c678c226cb845c639b914e6365b475ab20e86`;
- planning normalization `b7ca326ac6f9fbb74bdbe69fefe6faf4aaadf653` passed R0 #1598 / `32846946552`, Python #1572 / `32846946574`, UI #1539 / `32846946557`;
- PR #220 merged as `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`.
- Therefore R13 planning is **ACCEPTED + NORMALIZED**.

### Current external baseline — date-aware, not architecture constants

- Google Play: new apps/updates must target Android 16 / API 36 from **2026-08-31**; R13 store-ready acceptance starts at API 36.
- Android Compose/AGP/compileSdk values are capability-probed and versioned; mutable ecosystem versions are not frozen architecture constants.
- Google Play publication uses Android App Bundle for new apps; upload-key and Play App Signing key states remain separate; production secrets never enter repo/evidence/argv.
- Apple App Store Connect production uploads require Xcode 26+ with iOS/iPadOS 26 SDK+ since 2026-04-28; beta/TestFlight capability remains distinct from stable production capability.
- SwiftUI Observation support is available from iOS 17/iPadOS 17; R13.9 uses Observation-compatible state mapping while deployment target remains explicit project intent rather than a hidden mutable default.
- GitHub macOS 26 runner-image/runtime evidence is capability input; exact hosted runtime probes remain authoritative.
- Firebase Test Lab models a matrix as devices × test executions; device configurations include model, OS version, orientation and locale. Android can target physical or virtual Test Lab devices, while the current iOS Test Lab offering is physical-device based. Quotas/costs are project-scoped and remain explicit capability evidence.
- External device providers are optional; credentials, billing/quota and physical-device availability are not global phase prerequisites.
- Release-provider behavior is likewise versioned evidence: SemVer 2.0.0 forbids modifying the contents of an already released version; Google Play staged rollouts apply to updates and support percentage changes plus halt/resume, while an eligible previous fully rolled-out version may replace a halted 100% rollout; Apple phased release currently uses a seven-day provider-defined schedule and permits cumulative pauses up to 30 days. None of these mutable provider facts is a permanent architecture constant.
- Diagnostic-provider behavior is also versioned evidence: Android ANR categories/timeouts are platform/OEM-sensitive rather than universal constants; Apple crash reports, Jetsam reports and console logs remain distinct source types, and privacy-sensitive data must not be introduced into app logs.

## R13.1 closure authority

- R13.1 accepted source **`04bee35bba58645f6ef91e8cf5530b5062c6803d`**; PR #221 merged as `029a49e4d6772b2870357e0327acf470ef40e03b`; normalization PR #222 merged as `a63c25e0bb7dfa4f45c87f61f20de9477a64935a`.
- Therefore R13.1 is **COMPLETE + NORMALIZED**.

## R13.2 closure authority

- R13.2 accepted candidate **`27b75959e3240f67330d901c3b4a084242ae28b0`**; final head `3cc31e2ca367bfe97866f4e33a106e9d4c0da870`; PR #223 merged as `12d55b5ed94527b619f4f8259d4443dd6e71931c`; normalization PR #224 merged as **`4a4985b58f449fb1bc1b2a455a41255d40fccfac`**.
- Therefore R13.2 is **COMPLETE + NORMALIZED**.

## R13.3 closure authority

- Authorized base: `4a4985b58f449fb1bc1b2a455a41255d40fccfac`.
- Accepted candidate **`73d9024a1b06711885296775cb9f51370b52c3d0`** passed R0 #1615 / `32880841487`, Python #1589 / `32880841447`, UI #1556 / `32880841420`.
- Final head **`954d907503e4fa92f7eccefd70bfe5f5808e4c11`** passed R0 #1617 / `32883252890`, Python #1591 / `32883252848`, UI #1558 / `32883252862`.
- PR #225 merged as **`e153b5d84d235b529fd8f522315467c766087b92`**.
- Continuity-only normalization **`a5ddc4eacd2eaf4a78dfb4de7224a151d036b5e7`** passed R0 #1619 / `32883829735`, Python #1593 / `32883829471`, UI #1560 / `32883829356`; PR #226 merged as normalized `main` **`634e75cbdc0b05974781b40beecf54ad85766ed8`**.
- Therefore R13.3 is authoritatively **COMPLETE + NORMALIZED**.

## R13.4 closure authority

- Authorized normalized base: **`634e75cbdc0b05974781b40beecf54ad85766ed8`**.
- Dedicated implementation branch: **`r13/04-android-build-export`**; PR #227.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. Hosted CI proved the frozen build/package semantics; no user-machine SDK install, production signing key, Play account or physical Android device was required for R13.4 core acceptance.
- Rejected candidate `8c8e8dc2877f3a8de62d5e2b9fb19197f6b8a24c` failed because the hosted stable SDK manager could not provision API 37; rejected candidate `2d542963978c6eeb2c2ee7284686835f6e1323a9` failed due an ambiguous version-catalog matcher. Their evidence is not reused.
- Accepted implementation candidate **`0a58fd4e2f255786fe10ed00b7665ea49773d52b`** passed R0 #1636 / `32888926818`, Python #1610 / `32888926891`, UI #1577 / `32888926909`, and R13 Android Build Acceptance #38 / `32888926881`.
- Final end-synchronized head **`c479d429540b4941d96d3fcc39b8d85561917750`** passed R0 #1638 / `32890540226`, Python #1612 / `32890540400`, UI #1579 / `32890540232`, and R13 Android Build Acceptance #42 / `32890540329`; PR #227 merged as **`b212ae166ee7eceac59ef3c39d56272acfdfdfa6`**.
- Continuity-only normalization **`98f347616a389960c4627b424d12757fd73a4d33`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1640 / `32891329175`, Python #1614 / `32891329245`, UI #1581 / `32891329226`; PR #228 merged as normalized `main` **`939565f6409a45c93d0168546c1b4bb947d13ad4`**.
- Therefore R13.4 is authoritatively **COMPLETE + NORMALIZED**.

## R13.5 closure authority

- Authorized normalized base: **`939565f6409a45c93d0168546c1b4bb947d13ad4`**.
- Dedicated implementation branch: **`r13/05-android-signing`**; PR #229.
- Initial technical candidate **`a58227cd21112a65710002d2e673a1466889d7ce`** passed technical gates but was not accepted as final because required subdivision artifacts `R13_5_DESIGN.md` and `R13_5_ACCEPTANCE.md` were missing.
- Accepted implementation candidate **`1b299f5ab69bd5ac90d8ea805d59c216643f68e3`** passed R0 #1643 / `32894851393`, Python Core #1617 / `32894851604`, KodeStudio UI Smoke #1584 / `32894851851`, R13 Android Build Acceptance #51 / `32894851296`, and R13 Android Signing Acceptance #4 / `32894851385`; both Android workflows succeeded on Ubuntu and Windows.
- Final end-synchronized head **`030a3c548aebd77b736f139f995bf3951b17c33d`** passed fresh R0 #1645 / `32895748636`, Python Core #1619 / `32895748542`, KodeStudio UI Smoke #1586 / `32895748608`, R13 Android Build Acceptance #55 / `32895748735`, and R13 Android Signing Acceptance #8 / `32895748633`; both Android workflows again succeeded on Ubuntu and Windows.
- PR #229 merged with `expected_head_sha=030a3c548aebd77b736f139f995bf3951b17c33d` as **`bc354a48d6cd52b04462d58ced2a855770217d5f`**.
- The single continuity-only normalization head **`2517fb071f091c7a2312301504126bd4c8f70bbd`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1647 / `32896670665`, Python Core #1621 / `32896670704`, and KodeStudio UI Smoke #1588 / `32896670776`; PR #230 merged as normalized `main` **`56d6da4184709a54841ed36b21128477c78c6e9d`**.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. Hosted CI proved the frozen signing/state-model semantics with an ephemeral test identity; production keystore/private-key/password material and a live Play account were not required.
- Therefore R13.5 is authoritatively **COMPLETE + NORMALIZED**.

## R13.6 closure authority

- Authorized normalized base: **`56d6da4184709a54841ed36b21128477c78c6e9d`**.
- Dedicated implementation branch: **`r13/06-android-device-testing`**; implementation PR #231.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. Hosted emulator evidence established the frozen R13.6 core claim; no physical device or external account was required.
- Rejected candidate **`6367d8df1c691b3701d30f21e0cb6ffec2b468fb`** passed its standard/build/signing gates but Device #2 / `32899713104` failed because collection began before the launched emulator registered ONLINE in ADB. Evidence is rejected and not reused.
- Rejected candidate **`8e3092855279feaa8bfeb45350410d22cb18b6d4`** passed its other required gates but Device #4 / `32900347557` timed out with `R13.6 emulator did not register online in ADB: not-visible`; cleanup succeeded. Evidence is rejected and not reused.
- Rejected candidate **`5a2869253c10d841049e78fa53f15f4d87105eec`** proved hosted KVM/SDK/build but the emulator could not discover the AVD created by `avdmanager`; evidence is rejected and not reused.
- Rejected candidate **`22512f22d225c79fc69f9b7ca337d7838d13bb4d`** fixed deterministic AVD discovery and boot, but the CI helper missed the already-online `device` state due a literal-tab matcher; evidence is rejected and not reused.
- Accepted technical candidate **`91fac3fe1f80b04b570636002f4ba98e0c64724a`** reuses governed `parse_adb_devices` and passed R0 #1653 / `32903990807`, Python #1627 / `32903990720`, UI #1594 / `32903990770`, Android Build #72 / `32903990739`, Android Signing #25 / `32903990787`, and Android Device #10 / `32903990871`, all SUCCESS on exact head.
- End-synchronized head **`05238743d01f71d6feaa4dc6d832efbab1633c81`** changed only `docs/roadmap/R13_PLAN.md` and continuity, marked R13.6 COMPLETE/R13.7 PLANNED, and passed fresh R0 #1654 / `32906607557`, Python #1628 / `32906607562`, UI #1595 / `32906607621`, Android Build #74 / `32906607561`, Android Signing #27 / `32906607601`, and Android Device #12 / `32906607620`, all SUCCESS.
- PR #231 merged with **`expected_head_sha=05238743d01f71d6feaa4dc6d832efbab1633c81`** as **`8c5751bfe4c795f3386ea97caa92beb9c29be23d`**.
- Single continuity-only normalization **`4c97fea1d7e47cdb85aed6d9c096012592a6a11c`** changed exactly one file (`docs/continuity/KODEPOIA_CONTINUITY.md`) relative to the implementation merge, passed R0 #1656 / `32907230177`, Python Core #1630 / `32907230212`, and KodeStudio UI Smoke #1597 / `32907230236`, all SUCCESS.
- Normalization PR #232 merged with `expected_head_sha=4c97fea1d7e47cdb85aed6d9c096012592a6a11c` as normalized **`main` `6b943e29528245318904c86913eb5783d238797c`**.
- Therefore R13.6 is authoritatively **COMPLETE + NORMALIZED**.

## R13.7 closure authority

- Authorized normalized base: **`6b943e29528245318904c86913eb5783d238797c`**.
- Dedicated implementation branch: **`r13/07-google-play-readiness`**; implementation PR #233.
- Objective: model Google Play track intent, staged rollout, AAB upload-candidate identity, localized listing metadata/assets, date-aware official-policy evidence, Data safety/content-rating/permission/SDK findings, Play App Signing readiness and an optional credential-gated API capability boundary without automatic upload or publication.
- Current official policy facts used as **versioned evidence**, not architecture constants: ordinary new apps/updates must target Android 16/API 36+ from 2026-08-31; current listing maximums are 30 characters for app name, 80 for short description and 4000 for full description; published apps require IARC content rating/questionnaire. These values remain source/effective-date scoped and cannot silently claim CURRENT when stale.
- Accepted technical candidate **`b0179797628058670417e6f76e7f4e48a3dda365`** passed R0 Repository Guard #1658 / `32909573868`, Python Core #1632 / `32909573856`, KodeStudio UI Smoke #1599 / `32909573888`, R13 Android Build Acceptance #81 / `32909573855`, R13 Android Signing Acceptance #34 / `32909573847`, and R13 Google Play Readiness Acceptance #2 / `32909573884`, all SUCCESS.
- Google Play Readiness #2 passed on Ubuntu and Windows and uploaded exact-head dry-run evidence artifacts `r13-7-google-play-Linux-b0179797628058670417e6f76e7f4e48a3dda365` with digest **`sha256:ad8b6c90db8a67a6dd6cfcdab6ea31025605ebbd4cfcdc66b757b1438a098523`** and `r13-7-google-play-Windows-b0179797628058670417e6f76e7f4e48a3dda365` with digest **`sha256:2432063cde90dae29d1da5798257ed468ad8a21504523c72a1b914a8f399224e`**. The evidence is dry-run/non-publishing and did not mutate a Play account.
- Final end-synchronized head **`fceae9acfd6f7bb82410682798c4da236ecf37c5`** changed only `docs/roadmap/R13_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the accepted technical candidate and passed fresh R0 Repository Guard #1660 / `32932172947`, Python Core #1634 / `32932172980`, KodeStudio UI Smoke #1601 / `32932172949`, R13 Android Build Acceptance #85 / `32932172950`, R13 Android Signing Acceptance #38 / `32932172996`, and R13 Google Play Readiness Acceptance #6 / `32932172955`, all SUCCESS on that exact head.
- PR #233 merged with **`expected_head_sha=fceae9acfd6f7bb82410682798c4da236ecf37c5`** as **`8d5afe50e270cd25f92f5c746ab42e2623ea28eb`**.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No Play Console login, service-account credential, API token, live upload, tester enrollment, billing or publication action was required for the frozen R13.7 core acceptance.
- Single continuity-only normalization **`a128bfc22f13693f2a7c6a20ffe86017bfbb3fef`** changed exactly one file (`docs/continuity/KODEPOIA_CONTINUITY.md`) relative to the implementation merge, passed R0 #1662 / `32932799221`, Python Core #1636 / `32932799240`, and KodeStudio UI Smoke #1603 / `32932799192`, all SUCCESS. Normalization PR #234 merged with `expected_head_sha=a128bfc22f13693f2a7c6a20ffe86017bfbb3fef` as normalized **`main` `3a88f944a1424648fd4d1477c7c88b5da38e86dd`**.
- Therefore R13.7 is authoritatively **COMPLETE + NORMALIZED**.

## R13.8 closure authority

- Authorized normalized base: **`3a88f944a1424648fd4d1477c7c88b5da38e86dd`**.
- Dedicated branch: **`r13/08-apple-xcode-bridge`**; implementation PR #235.
- Rejected predecessor **`6ca7ab7aea9cfd8fbe69c6626bfbcd294bdf3e44`** failed R13 Apple Xcode Acceptance #9 / `32934587012` during focused tests before capability collection. Its evidence is rejected and not reused.
- Accepted technical candidate **`d4aad2fdd3b632ebef52de6b9082e5562d95108b`** passed R0 #1665 / `32934771636`, Python #1639 / `32934771679`, UI #1606 / `32934771709`, and Apple Xcode #11 / `32934771666`, all SUCCESS on exact head.
- Final end-synchronized head **`46512808ebc77b2762849f50157676d5d9ecd95d`** passed R0 #1667 / `32935142434`, Python #1641 / `32935142396`, UI #1608 / `32935142443`, and Apple Xcode #15 / `32935142412`, all SUCCESS; PR #235 merged with expected head as **`42e4450afc095542d722e6c3f1b671361565af23`**.
- Single continuity-only normalization head **`1c4a718f757f8973afe60f000a8c6aa9b3239122`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1670 / `32983561564`, Python #1644 / `32983561750`, and UI #1611 / `32983561686`, all SUCCESS. Normalization PR #236 merged with `expected_head_sha=1c4a718f757f8973afe60f000a8c6aa9b3239122` as normalized **`main` `cd1e34321c57a7f6e25d1d1c17d084469761c8a3`**.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No Apple Developer membership, signing certificate/private key, provisioning profile, App Store Connect credential, physical Apple device or user-machine Xcode installation was required.
- Therefore R13.8 is authoritatively **COMPLETE + NORMALIZED**.

## R13.9 closure authority

- Authorized normalized base: **`cd1e34321c57a7f6e25d1d1c17d084469761c8a3`**.
- Dedicated implementation branch: **`r13/09-ios-swiftui-scaffold`**; implementation PR #237.
- Rejected candidate **`dff635c527471b7d1b9f84a7bc005e24c27885f6`** is not reusable: Python Core #1646 / `32988110826` and UI #1613 / `32988110898` failed on a circular import caused by eager `ios_scaffold` re-export from `kodepoia.mobile.__init__`; Apple SwiftUI Scaffold #7 / `32988110841` failed before Xcode on an over-strict unquoted-PBX assertion. Both defects were corrected before the accepted candidate.
- Accepted exact-head technical candidate **`5bd50590c312d32a1e1d8c6162ab491a8b2733f6`** passed R0 Repository Guard #1675 / `32995414520`, Python Core #1649 / `32995414548`, KodeStudio UI Smoke #1616 / `32995414622`, R13 Apple Xcode Acceptance #45 / `32995414551`, and R13 Apple SwiftUI Scaffold Acceptance #16 / `32995414601`, all SUCCESS.
- Apple SwiftUI #16 ran on hosted **`macos-26`**, passed focused R13.9 tests, built the canonical SwiftUI fixture against the iOS Simulator toolchain with signing disabled, verified exact-head evidence, and uploaded **`r13-9-apple-swiftui-macOS-5bd50590c312d32a1e1d8c6162ab491a8b2733f6`**, digest **`sha256:d679b56020fdc90ddad20cfcd4ccdd208d33b12fcf14878161598e773d424e26`**.
- End-synchronized head **`812283ecc64ad21a3f55656fc7bc6185ca67616f`** changed only `docs/roadmap/R13_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the accepted technical candidate and passed fresh exact-head R0 #1676 / `32996307641`, Python #1650 / `32996307621`, UI #1617 / `32996307617`, Apple Xcode #47 / `32996307538`, and Apple SwiftUI Scaffold #18 / `32996307609`, all SUCCESS.
- PR #237 merged with **`expected_head_sha=812283ecc64ad21a3f55656fc7bc6185ca67616f`** as implementation merge **`178e94fdad85ce8345fbd5bb1d34c54074bc67df`**.
- Single continuity-only normalization head **`a314962cddca9544442b52a3d6e8fb4d3deb221f`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1678 / `32996925610`, Python Core #1652 / `32996925689`, and KodeStudio UI Smoke #1619 / `32996925659`, all SUCCESS. Normalization PR #238 merged with `expected_head_sha=a314962cddca9544442b52a3d6e8fb4d3deb221f` as normalized **`main` `e85faee11f6a3116e7cf4a1a99872c530ac76d26`**. R13.9 is authoritatively **COMPLETE + NORMALIZED**.
- Manual remains **CONDITIONAL / NOT TRIGGERED**. Hosted macOS established the frozen simulator compile/build claim. No Apple Developer account, signing certificate/private key, provisioning profile, App Store Connect credential/token, physical Apple device, raw destination/build setting or user-machine Xcode installation was required.

## R13.10 closure authority

- Authorized normalized base: **`e85faee11f6a3116e7cf4a1a99872c530ac76d26`**.
- Dedicated implementation branch: **`r13/10-apple-signing-archive`**; implementation PR #239.
- Accepted exact-head technical candidate **`35e0e9c8e15c7ac5f5d9d2407f2e7c72c32af4f4`** passed R0 Repository Guard #1680 / `33005940105`, Python Core #1654 / `33005940043`, KodeStudio UI Smoke #1621 / `33005940111`, R13 Apple Xcode Acceptance #56 / `33005940108`, R13 Apple SwiftUI Scaffold Acceptance #27 / `33005940057`, and R13 Apple Signing Archive Acceptance #2 / `33005940040`, all SUCCESS on that exact head.
- Final end-synchronized head **`0e2f98e3b5e74086782287aeb34fcacd1c10f97c`** changed only `docs/roadmap/R13_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the accepted technical candidate and passed fresh R0 Repository Guard #1682 / `33006842222`, Python Core #1656 / `33006842300`, KodeStudio UI Smoke #1623 / `33006842253`, R13 Apple Xcode Acceptance #60 / `33006842191`, R13 Apple SwiftUI Scaffold Acceptance #31 / `33006842189`, and R13 Apple Signing Archive Acceptance #6 / `33006842187`, all SUCCESS.
- PR #239 merged with **`expected_head_sha=0e2f98e3b5e74086782287aeb34fcacd1c10f97c`** as implementation merge **`738ee5a82dad81f49192aa9a223209940e4cd35a`**.
- Single continuity-only normalization **`f3cb9f815a594dbcd935d512746d5a74c555e2d8`** changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 Repository Guard #1684 / `33007431653`, Python Core #1658 / `33007431612`, and KodeStudio UI Smoke #1625 / `33007431638`, all SUCCESS. Normalization PR #240 merged with `expected_head_sha=f3cb9f815a594dbcd935d512746d5a74c555e2d8` as normalized **`main` `5c92b43cb407fb359bd692ba60a9862cb19b4201`**.
- Core R13.10 semantics are non-production and fail closed: simulator build and unsigned generic-iOS archive are independent of distribution credentials; Team/profile/certificate/entitlement substitutions are bounded; `KodeSecrets` retains only secret references; missing production credentials remain `DISTRIBUTION_CREDENTIALS_REQUIRED`; no live export/upload, physical-device capability, TestFlight acceptance or App Store acceptance is synthesized.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No Apple Developer membership, distribution certificate/private key, provisioning secret, App Store Connect credential/token, physical Apple device, or live upload was required for the frozen core claim.
- Therefore R13.10 is authoritatively **COMPLETE + NORMALIZED**.

## R13.11 closure authority

- Authorized normalized base: **`5c92b43cb407fb359bd692ba60a9862cb19b4201`**.
- Dedicated implementation branch: **`r13/11-ios-simulator-xctest-testflight`**; implementation PR #241.
- Rejected candidate **`88f58c798cd1329fddb3df131ae622311fd31ec4`** is not reusable: R13 Apple XCTest Acceptance #2 / `33010810241` and Python Core #1660 failed because focused duplicate-overlay validation observed canonical-PBX cardinality drift before the intended explicit `already present` rejection. The corrected implementation checks the test-target/scheme marker first.
- Accepted exact-head technical candidate **`c90a5804473dfbc7ed5da9b739dfd345dfa3a598`** passed R0 Repository Guard #1687 / `33011155725`, Python Core #1661 / `33011155704`, KodeStudio UI Smoke #1628 / `33011155662`, R13 Apple Xcode Acceptance #78 / `33011155694`, R13 Apple SwiftUI Scaffold Acceptance #49 / `33011155773`, R13 Apple Signing Archive Acceptance #24 / `33011155762`, and R13 Apple XCTest Acceptance #4 / `33011155751`, all SUCCESS on that exact head.
- Apple XCTest #4 job **`98317467434`** ran on hosted `macos-26`, passed all 8 focused R13.11 tests, executed the canonical real XCTest simulator acceptance, selected **`iPhone Air` / iOS `26.5`**, and produced evidence with `scope=SIMULATOR`, `summary.result=PASSED`, `total_test_count=2`, `passed_tests=2`, `failed_tests=0`, `physical_device_capability_proven=false`, `signing_credential_used=false`, `blockers=[]`. TestFlight remained `UNAVAILABLE`, `credential_reference_present=false`, `live_query_attempted=false`, `remote_build_state_proven=false` because no App Store Connect credential was supplied.
- Exact-head technical artifact **`r13-11-apple-xctest-macOS-c90a5804473dfbc7ed5da9b739dfd345dfa3a598`** has artifact ID **`9622789696`** and uploaded ZIP SHA-256 **`2b35b9470e7af218688f7b805cc2dabbd3ad5a6f012dcfa38df54bd5276c2b28`**. Bounded evidence binds app-model digest `3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0`, XCTest-plan digest `2cd0ca39fcdd8fef33cdc1c5e49c3210e569c234dcf5d62764bf04dfe9009137`, workspace-manifest digest `6403b900068c70e59a985e351ac20ef5856f599b65027c1fa1ad2dc242112835`, and `.xcresult` tree digest `4bcb4519d3461b07c652961130167aa08de9ef3b0c5a978e5ffc68efddc9444d`.
- Final end-synchronized head **`1f0e0e47bae3c0cea27127f5e2071c1a2a72db1c`** changed exactly `docs/roadmap/R13_PLAN.md`, `docs/roadmap/R13_11_ACCEPTANCE.md`, and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the technical candidate and passed fresh R0 Repository Guard #1688 / `33013883587`, Python Core #1662 / `33013883599`, KodeStudio UI Smoke #1629 / `33013883520`, R13 Apple Xcode Acceptance #80 / `33013883547`, R13 Apple SwiftUI Scaffold Acceptance #51 / `33013883510`, R13 Apple Signing Archive Acceptance #26 / `33013883513`, and R13 Apple XCTest Acceptance #6 / `33013883546`, all SUCCESS.
- PR #241 merged with **`expected_head_sha=1f0e0e47bae3c0cea27127f5e2071c1a2a72db1c`** as implementation merge **`1b3c127925b2775d77ab0d491e7fb16e800fe741`**.
- Single continuity-only normalization head **`02364597f34459edc12a1e911832477df109b78f`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 Repository Guard #1690 / `33014801858`, Python Core #1664 / `33014801948`, and KodeStudio UI Smoke #1631 / `33014801867`, all SUCCESS. Normalization PR #242 merged with **`expected_head_sha=02364597f34459edc12a1e911832477df109b78f`** as normalized **`main` `fb05135c4a5e1b7177dd4c68e6f05f61a489594e`**.
- Core frozen acceptance is fully established by hosted CI: canonical R13.9 fixture binding, deterministic simulator selection, real `xcodebuild test`, bounded `.xcresult` parsing/evidence, simulator-only partitioning, no signing credential, and fail-closed TestFlight state without credentials.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No Apple Developer membership, signing identity/private key, provisioning profile, App Store Connect credential/token, physical Apple device, live upload, beta group or tester enrollment was required.
- Therefore R13.11 is authoritatively **COMPLETE + NORMALIZED**.

## R13.12 closure authority

- Authorized normalized base before R13.12: **`fb05135c4a5e1b7177dd4c68e6f05f61a489594e`**.
- Dedicated implementation branch: **`r13/12-devicelab-matrices`**; implementation PR **#243**.
- Accepted technical candidate **`250c179590bc2b63b625b806cb5b1f1d618bd640`** passed R0 Repository Guard #1692 / `33016321788`, Python Core #1666 / `33016321879`, KodeStudio UI Smoke #1633 / `33016321824`, R13 Android Device Acceptance #130 / `33016321843`, and R13 Apple XCTest Acceptance #22 / `33016321680`, all SUCCESS on exact head.
- Final end-synchronized candidate **`bda11ed6d4f0fa68f79b669d00ed13e7197cd389`** passed fresh R0 Repository Guard #1695 / `33035203327`, Python Core #1669 / `33035203377`, KodeStudio UI Smoke #1636 / `33035203316`, R13 Android Device Acceptance #136 / `33035203355`, and R13 Apple XCTest Acceptance #28 / `33035203317`, all SUCCESS on that exact head.
- Android Device #136 completed the full hosted API 36 path: accepted SDK/image installation, KVM verification, governed staging + instrumentation overlay, app/instrumentation APK build, bounded headless emulator launch, ADB instrumentation/evidence collection, exact-head verification, evidence upload and owned cleanup. Apple XCTest #28 completed focused tests, the canonical hosted `macos-26` real simulator XCTest, exact-head simulator-only evidence verification and upload.
- PR #243 merged with **`expected_head_sha=bda11ed6d4f0fa68f79b669d00ed13e7197cd389`** as implementation merge **`fff7283194eaba74281e6e66963b4369cf1cb4cc`**.
- Single continuity-only normalization head **`a33a5763ce7bce7a4e271ceaecfaf49ecb7f2ab4`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 Repository Guard #1697 / `33035980323`, Python Core #1671 / `33035980325`, and KodeStudio UI Smoke #1638 / `33035980376`, all SUCCESS; normalization PR #244 merged with **`expected_head_sha=a33a5763ce7bce7a4e271ceaecfaf49ecb7f2ab4`** as normalized **`main` `bad4790bbc6a34c42bbc86d45db013722a25fdae`**.
- The implementation remains provider-neutral and local/hosted-first. Firebase Test Lab is optional capability state only; no live external execution seam, Firebase/Google Cloud account, service-account credential, billing mutation, physical-provider allocation or cloud matrix was required. Manual remained **CONDITIONAL / NOT TRIGGERED**.
- Therefore R13.12 is authoritatively **COMPLETE + NORMALIZED**.

## R13.13 closure authority

- Authorized normalized base: **`bad4790bbc6a34c42bbc86d45db013722a25fdae`**.
- Dedicated implementation branch: **`r13/13-koderelease`**; implementation PR **#245**.
- Accepted exact-head technical candidate **`3381caa21573f44c47d354f36b0e00c4d82e454e`** passed R0 Repository Guard #1699 / `33075296657`, Python Core #1673 / `33075296667`, and KodeStudio UI Smoke #1640 / `33075296615`, all SUCCESS.
- Final end-synchronized head **`8fd1b548129b73ceff5bc665001ce4a4bd59fa79`** passed fresh R0 Repository Guard #1703 / `33081597102`, Python Core #1677 / `33081597094`, and KodeStudio UI Smoke #1644 / `33081597217`, all SUCCESS on that exact SHA.
- PR #245 merged with **`expected_head_sha=8fd1b548129b73ceff5bc665001ce4a4bd59fa79`** as implementation merge **`627c7e5b21c71ae33652493660c7933e81634929`**.
- Single continuity-only normalization head **`5bfacd4d554f8245f7939c20691825c8cc9a25d2`** changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 Repository Guard #1705 / `33089274530`, Python Core #1679 / `33089274603`, and KodeStudio UI Smoke #1646 / `33089274597`, all SUCCESS. Normalization PR #246 merged with **`expected_head_sha=5bfacd4d554f8245f7939c20691825c8cc9a25d2`** as normalized **`main` `69efa1f5cf92ae3c3ce4040fe5abe54faae2ed8b`**.
- Frozen implementation provides strict SemVer/product version mapping, Android `versionCode` and Apple build number validation, release train/channel/candidate identities, immutable artifact/provenance/evidence/changelog/SBOM/compliance bindings, optimistic promotion revisions, released-version seals, provider-scoped rollout intent/policy evidence and local rollback points. Failed/stale promotions fail closed; rollback restores only a known immutable local release authority and does not claim remote store mutation or installed-client downgrade.
- No network publication seam, store credential, external account, production signing secret, physical device or self-updater was introduced. Manual remained **NONE**.
- Therefore R13.13 is authoritatively **COMPLETE + NORMALIZED**.

## R13.14 normalization authority

- Authorized normalized base: **`69efa1f5cf92ae3c3ce4040fe5abe54faae2ed8b`**.
- Dedicated implementation branch: **`r13/14-mobile-diagnostics`**, created exactly from that normalized main.
- Status: **COMPLETE + NORMALIZED**. Final normalization head `0c990e8d68c1940a092d589bd6b864299d064eeb` passed R0 #1713 / `33095670861`, Python Core #1687 / `33095670808`, and KodeStudio UI Smoke #1654 / `33095670718`, all SUCCESS; PR #248 merged as normalized `main` `80e9ae84f4c9edd8b2e41eadb93310abae6e442f`. R13.15 is now IN_PROGRESS; R13.16–R13.17 remain PLANNED / NOT STARTED.
- Frozen core claim: deterministic/local structured mobile-diagnostic ingestion and evidence only. Android logcat/crash/ANR/test/performance sources and Apple XCTest/result/log/crash/Jetsam/console-style sources stay platform/source explicit; no provider timeout, cluster threshold or report type is promoted to a universal architecture constant.
- Diagnostic payloads are bounded and redacted before any persisted/exportable representation; source digests, device/toolchain/artifact and release correlation remain explicit; crash/ANR fingerprinting and dedup must be deterministic; corrupt/oversized inputs fail closed; cross-release substitution is rejected; no continuous hidden telemetry, background surveillance, secret collection or silent network uploader is introduced.
- Accepted exact-head technical candidate **`ebb446daf6a6c38cff71b0834151ace74ff46099`** passed R0 Repository Guard #1707 / `33094260088`, Python Core #1681 / `33094260123`, and KodeStudio UI Smoke #1648 / `33094260179`, all SUCCESS. Python Core passed full Ubuntu/Windows tests and package builds including focused R13.14 diagnostics tests. Durable schema/model enforce source digest verification, strict bounded input, deterministic redaction, provider/platform/source separation, release/artifact/device/toolchain/test-run binding, deterministic fingerprinting, bounded performance snapshots and retention/export, and `continuous_hidden_telemetry=false`.
- Final end-synchronized head **`42b500d3a4a19fad9370fb4b56fa528f5ed742eb`** changed no implementation semantics after the accepted technical candidate and passed fresh exact-head R0 Repository Guard #1711 / `33095039101`, Python Core #1685 / `33095038903`, and KodeStudio UI Smoke #1652 / `33095038908`, all SUCCESS. PR #247 merged with **`expected_head_sha=42b500d3a4a19fad9370fb4b56fa528f5ed742eb`** as implementation merge **`a7a6fc43823c53e78d31d71e20c110abbc35196d`**.
- This branch **`r13/14-normalize-continuity`** was created exactly from implementation merge `a7a6fc43823c53e78d31d71e20c110abbc35196d` and is the single allowed continuity-only normalization. It changes no plan/code/schema/test bytes. No live external account/device/credential seam was introduced; manual remains **CONDITIONAL / NOT TRIGGERED**. R13.15 stays PLANNED until this normalization exact head passes fresh R0 + full Python Core + UI Smoke and its PR merges with `expected_head_sha`.
- Manual starts **CONDITIONAL / NOT TRIGGERED**. A physical device, Play Console/Firebase account, Apple Developer/TestFlight/App Store Connect account, production signing material or user-machine Xcode/Android SDK is not a core prerequisite. If a frozen claim is discovered that truly requires device-only diagnostics unavailable to accepted hosted CI, stop before R13.15 and request only bounded user-controlled evidence, never credentials/secrets in chat.

## R13.15 normalization authority

- Authorized normalized base: **`80e9ae84f4c9edd8b2e41eadb93310abae6e442f`** after R13.14 normalization PR #248.
- Dedicated implementation branch: **`r13/15-store-compliance-engine`**, created exactly from that normalized main.
- Status: **COMPLETE + NORMALIZED**. Single continuity-only normalization head **`2122fd685fd20973ae045658e79d94295bb389cb`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 Repository Guard #1720 / `33099025034`, Python Core #1694 / `33099024801`, and KodeStudio UI Smoke #1661 / `33099024892`, all SUCCESS; normalization PR #250 merged with `expected_head_sha=2122fd685fd20973ae045658e79d94295bb389cb` as normalized **`main` `dce60a60b58ff2c069d689144291f8c682b7e21f`**. R13.16 is now **IN_PROGRESS**; R13.17 remains **PLANNED / NOT STARTED**.
- Frozen core: versioned provider rules with official-source provenance, retrieved/effective/expires windows, platform/region/category scope, severity/remediation, deterministic currentness and conflict handling; Google target API/Data safety/permissions/content rating; Apple SDK minimum/privacy manifest/required-reason APIs/App Privacy/privacy policy/age rating; third-party SDK declarations; localization/accessibility/store assets. Compliance output is advisory readiness evidence, never legal certification.
- Official evidence baseline retrieved **2026-08-27**: Google Play API 36 deadline **2026-08-31** for ordinary new apps/updates, provider-specific form-factor exceptions and extension path to **2026-11-01**; future-effective sensitive-permission changes remain future until their own effective date. Apple production uploads require Xcode 26+/SDK 26+ since **2026-04-28**; required-reason APIs require approved reasons; App Privacy includes integrated third-party partner practices and a required privacy-policy URL; age rating is required and region-sensitive. Mutable facts remain rule data, not architecture constants.
- Manual: **NONE**. Account-only forms may remain `NEEDS_ACCOUNT_CONFIRMATION`; no store account, token, credential, live upload/publication, production key or physical device is needed for core acceptance.
- Accepted technical candidate **`dc9e04b1d0170b889ae02231a68304e7b7a11c60`** first passed R0 #1715 / `33097922318`, Python Core #1689 / `33097922338`, and UI #1656 / `33097922322`. Final end-synchronized head **`a6109e2d6f1a093bc709eb8385d8f0ce8dac0341`** then passed fresh exact-head R0 #1718 / `33098494117`, Python Core #1692 / `33098494367`, and KodeStudio UI Smoke #1659 / `33098494215`, all SUCCESS; Google Play Readiness #184 / `33098494495` and Apple Xcode Acceptance #167 / `33098494315` also passed as directly relevant regressions. PR #249 merged with **`expected_head_sha=a6109e2d6f1a093bc709eb8385d8f0ce8dac0341`** as implementation merge **`a92f5b1e31f09f37320e0759f7633569b9125487`**. This branch **`r13/15-normalize-continuity`** was created exactly from that merge and is the single allowed continuity-only normalization. Durable `store-compliance-v1` semantics remain unchanged: provider-scoped dated evidence, explicit current/future/expired/stale/unofficial states, fail-closed conflicts, SDK accounting, account-only confirmations, deterministic digests, `legal_certification=false`, and `live_account_query_attempted=false`.
- Therefore R13.15 is authoritatively **COMPLETE + NORMALIZED**.

## R13.16 normalization authority

- Authorized normalized base before R13.16: **`dce60a60b58ff2c069d689144291f8c682b7e21f`**, produced by R13.15 normalization PR #250.
- Dedicated implementation branch: **`r13/16-cli-kodestudio-workspace`**; implementation PR **#251**.
- Initial technical candidate **`8325b29a237078c7c6a333c04a9c1947e6737f7c`** is rejected and none of its decision evidence is reused. R0 #1722 succeeded but KodeStudio UI Smoke #1663 / `33111023452` failed because a pre-existing pseudo-localization regression test still expected 11 main navigation entries after R13.16 legitimately introduced the twelfth Mobile/DeviceLab/Release workspace entry.
- Accepted exact-head technical candidate **`1b2eec0e97467b8ddc3dd1c100b86140a7f4453d`** passed R0 Repository Guard #1723 / `33111158773`, Python Core #1697 / `33111158821`, and KodeStudio UI Smoke #1664 / `33111158807`, all SUCCESS. Same-candidate supplemental R13 regressions also passed: Google Play Readiness #206, Android Build #285, Android Signing #238, Android Device #223, Apple Xcode #189, Apple SwiftUI Scaffold #160, Apple Signing Archive #135 and Apple XCTest #115.
- Final end-synchronized implementation head **`a4c4185f6b11d4574e9ecf2f2b735c2d623155b4`** changed only `docs/roadmap/R13_16_ACCEPTANCE.md`, `docs/roadmap/R13_PLAN.md`, and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the accepted technical candidate and passed fresh exact-head R0 Repository Guard #1726 / **`33113280399`**, Python Core #1700 / **`33113280512`**, and KodeStudio UI Smoke #1667 / **`33113280468`**, all SUCCESS. The separate UI gate specifically re-proved the corrected pseudo-localized 12-entry navigation surface.
- PR #251 merged with **`expected_head_sha=a4c4185f6b11d4574e9ecf2f2b735c2d623155b4`** as implementation merge **`b1865ffff26de58f63606952f5c7b8de774e01fa`**.
- Single continuity-only normalization head **`9bcee3c9359f8a2340878c8310b1572f38d614df`** changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh exact-head R0 Repository Guard #1728 / `33113689078`, Python Core #1702 / `33113689208`, and KodeStudio UI Smoke #1669 / `33113689114`, all SUCCESS; normalization PR #252 merged with **`expected_head_sha=9bcee3c9359f8a2340878c8310b1572f38d614df`** as normalized **`main` `b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`**.
- Frozen core behavior remains unchanged: structured `kodepoia r13` intents only; passive refresh/status remains process/network-authority free; passive evidence cannot manufacture PASS; missing governed execution authority is `BLOCKED`; global KillSwitch cancels before executor dispatch; injected execution context is bounded to Project-DNA-derived data; KodeStudio separates passive Refresh and explicit execution, with evidence/capability views read-only, localized, pseudo-localized and accessibility-aware.
- Manual remained **NONE**. No physical device, store account, credential, production signing secret, local Android SDK/Xcode installation, paid provider quota or live publication was required.
- Therefore R13.16 is authoritatively **COMPLETE + NORMALIZED**.

## R13.17 normalization authority

- Authorized normalized base before R13.17: **`b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`**, produced by R13.16 normalization PR #252.
- Dedicated implementation branch: **`r13/17-integrated-release-readiness`**; implementation/evidence PR **#253**.
- Rejected predecessor **`e6d7cb3768d80944692596ef6705f3f95a24c8da`** is not reusable for decision authority: its Android integrated build/collection succeeded, but the workflow assertion read `target_sdk` from the wrong JSON level.
- Accepted immutable technical source **`56f829f4395138bf90a1a8e0003bff95b67dd878`** passed the complete required candidate family. Checked-in `R13_17_CI_ACCEPTANCE.json` binds the accepted runs and immutable Android Build/Device + Apple XCTest artifacts with semantic digest **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`**.
- Canonical `docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json` has **`status=pass`**, **`blockers=[]`**, immutable technical `source_sha=56f829f4395138bf90a1a8e0003bff95b67dd878`, and semantic digest **`831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`**.
- Final documentation/evidence head **`cb0c63bcdcbaf2b58b3066d311780843c2598575`** changed no accepted implementation semantics and passed fresh exact-head R0 Repository Guard #1744 / **`33121176174`**, Python Core #1718 / **`33121176167`**, KodeStudio UI Smoke #1685 / **`33121176129`**, Android Build #327 / **`33121176121`**, Android Signing #274 / **`33121176137`**, Android Device #265 / **`33121176131`**, Google Play Readiness #248 / **`33121176193`**, Apple Xcode #231 / **`33121176116`**, Apple SwiftUI #202 / **`33121176166`**, Apple Signing Archive #177 / **`33121176186`**, Apple XCTest #157 / **`33121176106`**, and R13 Integrated Release Readiness #30 / **`33121176177`**, all SUCCESS.
- Integrated #30 passed both hosted platform jobs: Android canonical APK/AAB/unit-test evidence with exact-head assertions and Apple canonical iOS Simulator XCTest with simulator-only exact-head assertions. No virtual/simulator evidence is promoted to physical-device proof.
- PR #253 merged with **`expected_head_sha=cb0c63bcdcbaf2b58b3066d311780843c2598575`** as implementation/evidence merge **`f56c61dbc82efd93c08e2b29ad1acff33219689f`**.
- Single continuity-only normalization head **`1bc52616e5e527dadfe8feafdc0d137433b37a48`** changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md` relative to implementation/evidence merge `f56c61dbc82efd93c08e2b29ad1acff33219689f`, with no plan/code/schema/test/workflow bytes in the cumulative final diff.
- Fresh exact-head normalization gates on `1bc52616e5e527dadfe8feafdc0d137433b37a48` all completed SUCCESS: R0 Repository Guard #1746 / **`33135420877`**, Python Core #1720 / **`33135420870`**, and KodeStudio UI Smoke #1687 / **`33135420823`**.
- Normalization PR #254 merged with **`expected_head_sha=1bc52616e5e527dadfe8feafdc0d137433b37a48`** as normalized **`main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**.
- Frozen core boundaries remain unchanged: Android proof is **VIRTUAL / API 36**, Apple proof is **SIMULATOR**; physical devices, live Play/App Store/TestFlight state, production signing/provisioning credentials and automatic public publication remain outside the frozen core PASS claim.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. No physical device, live store account, production signing secret, Apple Developer/App Store Connect credential, paid provider quota or user-machine Android SDK/Xcode installation was required.
- Therefore R13.17 and Phase R13 are authoritatively **COMPLETE + NORMALIZED**.

## R14 planning authority

- Frozen roadmap title: **Backend / Platform Services / LiveOps**.
- Frozen roadmap scope: conditional Auth, DB, authoritative server, matchmaking/lobby, cloud saves, achievements/entitlements/billing, remote config/feature flags/content delivery/events. R15 fine-tuning and R16 final hardening remain outside R14.
- Authorized normalized planning base: **`b5b75b826bedabf64957494f7e2228ec1c9ff2d3`**, the R13.17 normalization merge.
- Dedicated planning branch: **`r14/00-phase-plan`**, created exactly from that normalized main.
- Exhaustive planning head **`343b7834d8b5826d5012bf78926102725b66db7f`** introduced `docs/roadmap/R14_PLAN.md` and START-sync continuity only. The plan freezes R14.1–R14.17; every subdivision remains **PLANNED** and R14.1 has not started.
- Fresh exact-head planning gates on `343b7834d8b5826d5012bf78926102725b66db7f` all completed SUCCESS: R0 Repository Guard #1748 / **`33136015617`**, Python Core #1722 / **`33136015593`**, and KodeStudio UI Smoke #1689 / **`33136015584`**. Python Core passed full Ubuntu/Windows tests plus both package builds and its internal KodeStudio smoke.
- Planning PR #255 merged with **`expected_head_sha=343b7834d8b5826d5012bf78926102725b66db7f`** as planning merge **`808e5215e45a3a90d3037efb1a3749f01b285b9c`**.
- R14 remains provider-neutral/local-first. Paid cloud accounts, production domains/TLS, production IdP tenants, managed databases, app-store billing accounts, CDN accounts and provider production credentials are not global prerequisites. Provider-live claims remain explicit `CONDITIONAL` capability evidence.
- External compatibility facts are dated evidence, not architecture constants: current auth/token/passkey standards, supported stable PostgreSQL, billing-provider server verification and event/feature-flag/observability interoperability remain capability-probed and source-provenanced.
- Single continuity-only planning normalization branch **`r14/00-planning-continuity-normalization`** was created exactly from planning merge `808e5215e45a3a90d3037efb1a3749f01b285b9c`. It is the only allowed post-planning normalization and must change exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; no R14 plan/code/schema/test/workflow bytes may remain changed in its final cumulative diff.
- **Planning normalization acceptance rule:** this exact normalization head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merge with `expected_head_sha`. Only the resulting normalized `main` makes R14 planning **ACCEPTED + NORMALIZED** and authorizes R14.1.

## Frozen R13 subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE |
| R13.2 | Project DNA/KodeProduct mobile profiles + Project Wizard target selection | COMPLETE | NONE |
| R13.3 | Android deterministic native scaffold + Kotlin/Compose shared app model | COMPLETE | NONE |
| R13.4 | Android Gradle build/export, APK/AAB, manifest/resources/ABI validation | COMPLETE | CONDITIONAL |
| R13.5 | Android signing states, keystore boundary + Play App Signing model | COMPLETE | CONDITIONAL |
| R13.6 | Android emulator/device testing + adb/instrumentation adapter | COMPLETE | CONDITIONAL |
| R13.7 | Google Play release tracks, metadata + policy/compliance readiness | COMPLETE | CONDITIONAL |
| R13.8 | Apple platform/Xcode capability bridge + macOS execution boundary | COMPLETE | CONDITIONAL |
| R13.9 | iOS/iPadOS SwiftUI/Xcode deterministic scaffold + shared app model | COMPLETE | CONDITIONAL |
| R13.10 | Apple identity, entitlements, signing/provisioning, archive/export model | COMPLETE | CONDITIONAL |
| R13.11 | iOS Simulator/XCTest, device/TestFlight evidence adapter | COMPLETE | CONDITIONAL |
| R13.12 | DeviceLab provider-neutral matrices, physical/virtual routing + evidence | COMPLETE | CONDITIONAL |
| R13.13 | KodeRelease versioning, release trains, promotion, rollout + rollback | COMPLETE | NONE |
| R13.14 | Mobile diagnostics: logs, crash/ANR/test/performance bundles + redaction | COMPLETE | CONDITIONAL |
| R13.15 | Current store compliance engine: privacy, ratings, permissions, SDK/policy evidence | COMPLETE | NONE |
| R13.16 | CLI + KodeStudio Mobile/DeviceLab/Release workspace | COMPLETE | NONE |
| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | COMPLETE | CONDITIONAL |

### R13 phase DoD target

R13 is COMPLETE only when the existing Project Wizard creates accepted Android/iOS intent; a canonical Android project scaffolds/builds/tests with validated APK/AAB release state; a canonical iOS SwiftUI/Xcode project scaffolds/compiles/tests on accepted hosted macOS simulator evidence; DeviceLab/release/diagnostics/compliance evidence is truthful and provider-scoped; any triggered manual gate is reviewed; canonical `R13_INTEGRATED_ACCEPTANCE.json` has `status=pass`, `blockers=[]`; and the final R13 implementation/evidence merge is followed by exactly one accepted continuity-only normalization.

Actual public Play/App Store publication remains explicit user-controlled behavior, not an automatic core acceptance prerequisite.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + global KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence; R12 desktop/package/update authority remain in force. Structured APIs only. Network off by default. No arbitrary shell/Gradle/Xcode/store commands. Missing evidence never manufactures PASS.

## R13 execution rule

Each subdivision: dedicated branch from normalized `main` -> start plan+continuity status sync -> implementation + focused tests -> exact-head standard/platform gates -> truthful manual state -> end plan+continuity status sync -> fresh evidence/re-gates if bytes changed -> merge with `expected_head_sha` -> exactly one continuity-only post-merge normalization + exact-head gates + merge -> only then next subdivision.

If a CONDITIONAL manual gate triggers, stop before the next subdivision and provide bounded prerequisites, exact commands/actions, expected evidence and recovery/privacy instructions. Never request passwords/private keys/tokens in chat.

## Next authorized action

Treat the current R14.6 END-synchronized branch head as the only candidate for final decision evidence once its cumulative diff from immutable technical source `a1425b53e1228f9c88ba373cdfabf1459393a7cf` is verified to contain only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_6_ACCEPTANCE.md`, and `docs/continuity/KODEPOIA_CONTINUITY.md`. Require fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Authority Acceptance on that unchanged head. If all four are SUCCESS, merge PR #267 with `expected_head_sha` equal to that exact final head. Then create exactly one `r14/06-continuity-normalization` branch from the implementation/evidence merge, change only continuity to record final head/gates/merge and declare R14.6 `COMPLETE + NORMALIZED`, require fresh R0/Python/UI on that normalization head, and merge it with expected-head protection. **Only after that normalization merge may R14.7 start on its own branch with mandatory START-sync.** Manual intervention remains NONE.
