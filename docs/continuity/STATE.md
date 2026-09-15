# Kodepoia continuity state

Last synchronized: 2026-09-15 after opening the V2 roadmap direction from live `main` `6b7ec8d4504da83579af98d8235326ea4268d63f`  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` before future release/updater/TUF mutations and re-fetch live GitHub state before acting.

The rc7 corrective release, rc8 validation-only release, rc8 TUF authorization, publication and the real installed Windows updater E2E are complete. The updater incident exercised by rc8 is **CLOSED**.

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful.

`README.md`, `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` and the explicit post-R20 current-distribution section of `docs/continuity/KODEPOIA_CONTINUITY_R20.md` are aligned to the rc8 authority. Older frozen continuity sections remain historical evidence and are not retroactively rewritten.

## Validated rc8 source and installer authority

- exact qualified rc8 source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- source PR: `#462`;
- exact-source qualification: 40/40 PR-triggered workflows `completed/success`;
- authoritative R17 run: `34871154670`;
- authoritative R17 artifact ID: `10360685910`;
- installer: `KodepoiaSetup.exe`;
- length: `37730750` bytes;
- SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- installer is genuinely unsigned;
- target-scoped policy: `authenticode_policy = "allow-unsigned"`.

The source delta was validation-only: release identity `1.1.0rc7 -> 1.1.0rc8` and serial `7 -> 8`, with no new updater feature.

## Public rc8 release authority

Public prerelease `v1.1.0-rc8` is published and was re-fetched after publication:

- tag/source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- exactly one intended installer asset: `KodepoiaSetup.exe`;
- length: `37730750` bytes;
- SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`.

The tag resolves directly to the exact qualified source.

## Live TUF authority after rc8

The qualified TUF transition was PR `#464` on exact head:

`10804c629ca81de8b5e54ddfbfaf53370e88a201`

Exactly 30 PR-triggered workflows were re-fetched for that SHA and all 30 completed with conclusion `success`. A transient Apple Xcode runner timeout was not ignored: the same job was rerun on the same SHA and completed successfully before qualification was accepted.

PR #464 was merged only after rc8 was public and its public tag/asset were reverified. TUF merge commit:

`1deb84e1b63581ed78ea90480fde2019623d01de`

Post-merge production metadata:

- Root v2;
- Targets v8;
- Snapshot v10;
- Timestamp v10.

Targets v8 preserves rc3 through rc7 and adds exactly rc8 at:

`channels/beta/windows-x86_64/1.1.0-rc8/fa787ab7ef76f2556b56ac1f058916a1425455af/KodepoiaSetup.exe`

with exact length/SHA, `withdrawn=false`, unsigned signing status and target-scoped `authenticode_policy="allow-unsigned"`.

The seven push-triggered workflows on the TUF merge commit completed successfully.

## Closure-time CI normalization

While qualifying the documentation-only incident closure, the hosted R13 Android workflows exposed an external SDK setup drift: `android-actions/setup-android@v3` still requested the obsolete implicit `tools` package through its default package list before Kodepoia's explicit SDK installation step.

PR `#466` applied the minimal normalization to the four affected workflows by setting `packages: ''` on `setup-android`, leaving each workflow's explicit SDK package installation and all acceptance assertions unchanged.

- exact qualified head: `ab86b7c5b504189c69c4317317a9b7e330a33239`;
- exact-head qualification: 25/25 PR-triggered workflows `completed/success`;
- R13 Android Build, Device, Signing and Integrated Release Readiness all completed successfully on that exact head;
- merge commit: `6d53794aa71a7740ca7157e41f2ae37f60f33a80`.

This was CI infrastructure hardening only. It changed no Kodepoia product, updater, release, TUF or acceptance semantics.

## Real Windows rc7 -> rc8 E2E — PASS

The operator confirmed the full installed path succeeded:

`installed rc7 -> discover rc8 -> download -> verify -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> check again`

The terminal post-upgrade screenshot shows:

- KodeStudio running as `1.1.0-rc8`;
- installed version `1.1.0-rc8 (beta)`;
- Beta channel selected;
- candidate `1.1.0-rc8 (beta)`;
- verification source `tuf-verified-metadata`;
- declared size `37730750` bytes;
- status that installed version is current for the selected channel;
- download/install controls disabled because no newer candidate exists.

Full acceptance evidence is recorded in `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md`.

## Canonical closure and public-documentation alignment

The rc8 E2E closure PR `#467` was accepted on exact head `a6e67e0ad052275e6b2bf069a50c127ec4043fdf` after 25/25 PR-triggered workflows completed successfully and merged as `e40477699d98bda2f804c269339929de719556b5`; its seven push-triggered post-merge workflows also completed successfully.

After that closure, the user-facing/current-state documentation was explicitly realigned so that no active entry point continues to advertise rc4 or rc5 as the current release:

- `README.md` identifies rc8 as the recommended/current beta release, with the exact installer authority and TUF generation;
- `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` identifies rc8 and the real E2E as current authority;
- `docs/continuity/KODEPOIA_CONTINUITY_R20.md` keeps its frozen R20 evidence but updates its clearly marked post-R20 current-distribution authority to rc8;
- this file and `NEXT.md` remain the immediate resume authority.

This documentation alignment is not a new release, does not mutate TUF, does not reopen R20 and does not change the already-accepted rc8 binaries or updater behavior.

## Incident closure

The corrective/validation sequence achieved its intended proof. The updater incident is closed. No additional rc8 release mutation, TUF mutation or corrective release is required from this acceptance result.

Future work may use installed rc8 as the validated baseline, but must preserve all existing fail-closed invariants:

- exact source and artifact binding;
- TUF signature/threshold/rollback/version/expiry checks;
- exact target length and SHA-256;
- target-scoped Authenticode policy only;
- installer identity verification;
- explicit user consent before installer launch;
- no private signing material in Git, CI, public artifacts or chat.

## V2 development direction

The user explicitly authorized preparation of a **Roadmap V2** on 2026-09-15. V1/R1–R20 remain frozen historical evidence; V2 is a new development track and must not be represented as an extension such as `R20.7`.

At roadmap-open time, live `main` was re-fetched at `6b7ec8d4504da83579af98d8235326ea4268d63f` (merge of PR `#471`). This SHA is a planning baseline only; future implementation sessions must re-fetch live `main` and never assume it remains current.

Two authorities must now be distinguished:

- **public distribution authority:** Windows `v1.1.0-rc8`, still the last fully real-machine updater-E2E-qualified public baseline;
- **development authority:** live `main`, which already contains post-rc8 source changes not present in the rc8 installer.

The active V2 roadmap is `docs/roadmap/KODEPOIA_ROADMAP_V2.md`. Its first implementation priority is **V2.1 Research Workspace**, specified by `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The current Research UX must not be described as a complete Web search engine. On the planning baseline, KodeStudio's “Search” action calls `ResearchService.query()` over already persisted project research reports, while new Web acquisition is a separate guarded fetch operation requiring an explicit locator/URL. V2.1 therefore adds honest UX/diagnostics first, followed by real discovery providers, inspectable evidence, cited synthesis and governed project Research Packs.

For remote training, Kaggle **T4×2 is the primary V2 target** for the current CUDA/PyTorch/PEFT/QLoRA stack. TPU v5e-8 is deferred experimental capacity and is not a V2 release blocker. A TPU path may be scheduled only after a concrete benchmark proposal justifies the separate XLA/JAX or PyTorch/XLA engineering and acceptance work.

No public release number is reserved by the V2 planning documents. No release/TUF mutation is authorized merely by creating or accepting the roadmap.

## Resume rule

For any future work:

1. re-fetch live `main` and read this file with `docs/continuity/NEXT.md`;
2. if the work touches release/updater/TUF, also re-fetch the latest public release/tag/asset and current TUF metadata;
3. treat rc8 as the last fully real-machine E2E-validated Windows distribution baseline unless later continuity explicitly supersedes it;
4. follow `docs/roadmap/KODEPOIA_ROADMAP_V2.md` for new feature work, starting with the next uncompleted V2.1 subdivision unless the user explicitly reprioritizes;
5. use `README.md` and `KODEPOIA_CURRENT_AUTHORITY.md` as synchronized summaries, not substitutes for live revalidation;
6. stop on any discrepancy or required manual intervention rather than inferring or weakening a gate.
