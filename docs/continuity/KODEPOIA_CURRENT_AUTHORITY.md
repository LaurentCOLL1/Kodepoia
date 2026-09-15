# Kodepoia — Current Authority

**Current public state:** R1–R20 COMPLETE + NORMALIZED; R20 terminal; no R20.7 authorized. The updater corrective/validation sequence ending with rc8 is complete and the exercised updater incident is **CLOSED**.  
**Current development direction:** Roadmap V2, with V2.1 Research Workspace as the first usability priority.

This compact file summarizes the current cross-phase/public-release and development authority. It does not replace immutable historical phase evidence. For any future mutation, read it together with `docs/continuity/STATE.md` and `docs/continuity/NEXT.md`, then re-fetch the live GitHub state rather than assuming a previously recorded `main` SHA is still HEAD.

## Current repository and release

- Repository: `LaurentCOLL1/Kodepoia`.
- Canonical branch: `main`.
- Current public beta prerelease: **`v1.1.0-rc8`**.
- Exact qualified rc8 source/tag target: `fa787ab7ef76f2556b56ac1f058916a1425455af`.
- Source PR: `#462`; exact-source qualification: **40/40** PR-triggered workflows `completed/success` before merge.
- Accepted Windows installer: `KodepoiaSetup.exe`.
- Installer size: `37,730,750` bytes.
- Installer SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`.
- Installer claim: `production_signed=false`; rc8 is a prerelease/beta, not a production-signed stable release.
- Target-scoped TUF policy for this exact artifact: `authenticode_policy="allow-unsigned"`.
- Authoritative R17 exact-source run: `34871154670`; artifact ID: `10360685910`.
- Qualified rc8 TUF transition: PR `#464`, exact head `10804c629ca81de8b5e54ddfbfaf53370e88a201`, **30/30** PR-triggered workflows `completed/success`, merged as `1deb84e1b63581ed78ea90480fde2019623d01de` only after the public release/tag/asset were reverified.
- Closure-time CI normalization: PR `#466`, exact head `ab86b7c5b504189c69c4317317a9b7e330a33239`, **25/25** PR-triggered workflows `completed/success`, merged as `6d53794aa71a7740ca7157e41f2ae37f60f33a80`.
- Canonical rc8 E2E closure: PR `#467`, exact head `a6e67e0ad052275e6b2bf069a50c127ec4043fdf`, **25/25** PR-triggered workflows `completed/success`, merged as `e40477699d98bda2f804c269339929de719556b5`; its seven push-triggered post-merge workflows also completed successfully.

The historical `rc5 -> rc6` validation attempt remains **failed/incomplete** and must never be relabeled successful. rc7 is the corrective predecessor that restored a healthy installed baseline; rc8 is the validation-only candidate that completed the real Windows updater proof.

## Current TUF generation

- Root: **v2**, SHA-256 `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`, threshold 2-of-3, expiry `2027-09-08T14:59:19Z`.
- Targets: **v8**, SHA-256 `800028c1c2d42d99ed0c71f5b9a8c68cf37dd9aa36250764765f17827394acce`, length `4525`, expiry `2027-09-12T20:49:31Z`, signed by offline Targets keyid `70e86d478a769ffbefbf6febc37435a2a4563197df03d6dcda6627282fa5cf00`.
- Targets v8 preserves rc3 through rc7 and authorizes rc8 at exact source, payload URL, length and SHA-256 with `withdrawn=false` and target-scoped `authenticode_policy="allow-unsigned"`.
- Snapshot: **v10**, SHA-256 `61c8292e1eca986cd48f3523bdd0dfcbd82769fc740b126737e5ce6dcc103592`, length `470`, expiry `2026-09-17T19:48:41Z`, signed by online keyid `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`.
- Timestamp: **v10**, SHA-256 `c1b7eab48908c29ad63dc3ad2a3dfffafa157d9d15e07faf7a34ea666a7c58c7`, length `472`, expiry `2026-09-16T19:48:41Z`, signed by distinct online keyid `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.
- Snapshot v10 binds exact Targets v8 bytes/version/hash/length; Timestamp v10 binds exact signed Snapshot v10 bytes/version/hash/length.
- Root/Targets private custody remains outside Git/repository/CI. Snapshot/Timestamp remain distinct low-authority online signing roles.

## Real Windows updater acceptance

The complete installed updater path succeeded:

`installed rc7 -> discover rc8 -> download -> verify -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> check again`

The terminal post-upgrade state showed KodeStudio running as `1.1.0-rc8`, Beta selected, candidate `1.1.0-rc8`, source `tuf-verified-metadata`, declared size `37730750` bytes and status that the installed version is current, with download/install controls disabled. Full evidence is in `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md`.

## V2 development authority

Roadmap V1/R1–R20 remains frozen historical authority. The user explicitly authorized a separate **Roadmap V2** on 2026-09-15. The planning baseline was live `main` `6b7ec8d4504da83579af98d8235326ea4268d63f` (PR `#471` merge), but this SHA must be re-fetched before future implementation because it is not a permanent HEAD assertion.

The active planning documents are:

- `docs/roadmap/KODEPOIA_ROADMAP_V2.md`;
- `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The first V2 priority is **V2.1 Research Workspace**. Current source behavior on the planning baseline is intentionally recorded truthfully: KodeStudio's Research “Search” invokes `ResearchService.query()` over existing persisted research reports; it is not external discovery. Web acquisition is a separate guarded fetch primitive for an explicit URL/locator. V2.1 must turn those primitives into a real `question -> discovery -> guarded fetch -> evidence selection -> cited synthesis -> Research Pack` workflow without weakening ResearchGuard.

Post-rc8 source features on `main` are development capabilities until a later release is explicitly qualified. Their presence in source does not mean they exist in the public rc8 installer.

For remote tuning, Kaggle **T4×2** is the primary V2 target for the current CUDA/PyTorch/PEFT/QLoRA path. The two GPUs remain separate 16 GiB devices and multi-GPU use requires explicit qualification. **TPU v5e-8 is deferred experimental capacity**, not a release blocker; support requires a separate XLA/JAX or PyTorch/XLA backend/acceptance and should be scheduled only if benchmark evidence justifies it.

No post-rc8 release version or TUF transition is authorized solely by the V2 roadmap.

## Continuity hierarchy

Use the following documents in this order when interpreting current state:

1. `docs/continuity/STATE.md` for immediate operational authority;
2. `docs/continuity/NEXT.md` for the next authorized direction and resume prompt;
3. this file for the compact cross-phase/public-release/development summary;
4. `docs/roadmap/KODEPOIA_ROADMAP_V2.md` for the active V2 development ordering;
5. `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md` for the first V2 implementation contract;
6. `docs/continuity/KODEPOIA_CONTINUITY_R20.md` for terminal R20 authority and historical post-R20 release operations;
7. `docs/continuity/KODEPOIA_CONTINUITY_R19.md` for frozen R19 authority;
8. `docs/continuity/KODEPOIA_CONTINUITY.md` for the large historical R1–R18 continuity archive;
9. phase plans and Git history for immutable phase-specific evidence.

The large legacy continuity archives intentionally remain historical. Stale “current” wording inside old frozen sections is superseded by `STATE.md`, `NEXT.md`, this file and the explicit current-distribution section of the R20 continuity rather than by retroactive rewriting of historical phase evidence.

## Terminal R20 boundary

R20 is **COMPLETE + NORMALIZED**. Post-R20 releases and updater/TUF operations are release operations built on the completed R20 machinery. They do **not** create R20.7 or reopen R20.

The rc7 corrective release, rc8 validation-only release, rc8 TUF authorization, public release verification, real Windows rc7 -> rc8 E2E and continuity closure are complete. No additional rc8 corrective release or TUF mutation is required by this incident. V2 work proceeds as a new roadmap while preserving all existing fail-closed trust invariants.
