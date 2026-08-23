# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R8 COMPLETE. R9 planning ACCEPTED.** `docs/roadmap/R9_PLAN.md` est l’autorité structurelle exhaustive de R9.1–R9.11. Le planning R9 est accepté sur le head exact `fc73a3c96cecb78820f9e94738ace2c280dc4251` avec R0 Repository Guard #1103 / `32623437662`, Python Core #1077 / `32623437659`, et KodeStudio UI Smoke #1044 / `32623437660`, tous SUCCESS; PR #103 est fusionnée en `main` sous `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`. Manual R9.8 = REQUIRED real local GPU/ComfyUI; R9.2/R9.5/R9.9/R9.11 = CONDITIONAL. Une normalisation continuity-only `r9/planning-normalization` enregistre cette acceptation avant le démarrage de R9.1. **Ne pas commencer R9.1 avant fusion acceptée de cette normalisation.** Après cette fusion, la prochaine action autorisée est R9.1 sur une branche dédiée.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée et sa normalisation requise.
- R1–R6 : COMPLETE.
- R7 : COMPLETE.
- R8 : COMPLETE.
- R8 planning : ACCEPTED.
- R8.1–R8.11 : COMPLETE.
- R8.11 : MERGED via PR #101 sous `2a3a0b7da3803fb4d59158b94b9219aded201f17`.
- R8 final continuity-only normalization : ACCEPTED sur `023014143c06379b7aad0b0698567c4818c172d3`; R0 #1101 / `32622805643`; Python Core #1075 / `32622805684`; UI Smoke #1042 / `32622805735`; PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.
- R9 planning : ACCEPTED sur head exact `fc73a3c96cecb78820f9e94738ace2c280dc4251`; R0 #1103 / `32623437662`; Python Core #1077 / `32623437659`; UI Smoke #1044 / `32623437660`; PR #103 merge `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`.
- R9 planning normalization : IN PROGRESS sur `r9/planning-normalization`, continuity-only, branch point `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`.
- R9.1–R9.11 : PLANNED / NOT STARTED; structure R9.1–R9.11 maintenant figée par le plan fusionné.
- R10–R16 : PENDING / NOT STARTED.

## R8 planning acceptance

- Branch point : `b98832b339902527bce8a5ea95b5a08a19839a40`.
- Planning head exact : `08844fc09501ed8a4974909eca4595021bc73bf4`.
- R0 Repository Guard #1039 / `32600268817` : SUCCESS Ubuntu + Windows.
- Python Core #1013 / `32600268710` : SUCCESS 5/5.
- KodeStudio UI Smoke #980 / `32600268680` : SUCCESS.
- PR #83 merge : `60412afac35678b2a25547a7f0c937891a8a1004`.
- Planning normalization PR #84 merge : `dfc07ee3dbb746b66c2dabd945b4015979f374d3`.

## R9 planning acceptance

- Frozen-roadmap title: **ComfyUI + VRAM**.
- Planning branch point / normalized R8 `main`: `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.
- Planning branch: `r9/planning`.
- Exact accepted planning head: `fc73a3c96cecb78820f9e94738ace2c280dc4251`.
- R0 Repository Guard #1103 / `32623437662`: SUCCESS.
- Python Core #1077 / `32623437659`: SUCCESS.
- KodeStudio UI Smoke #1044 / `32623437660`: SUCCESS.
- Planning PR #103 merged as `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`.
- Plan authority: `docs/roadmap/R9_PLAN.md`.
- Frozen subdivision count: 11 (`R9.1`–`R9.11`).
- Frozen manual states: R9.1 NONE; R9.2 CONDITIONAL; R9.3 NONE; R9.4 NONE; R9.5 CONDITIONAL; R9.6 NONE; R9.7 NONE; R9.8 REQUIRED; R9.9 CONDITIONAL; R9.10 NONE; R9.11 CONDITIONAL.
- R9.8 REQUIRED reason: hosted CI cannot authoritatively validate real GPU VRAM allocation/release/backend behavior; acceptance requires real local ComfyUI/GPU evidence on the exact R9.8 head.
- Planning acceptance is complete; continuity-only normalization must now pass the same exact-head gate set before R9.1 begins.

## R8 accepted structure and evidence

| ID | Title | Exact accepted head | CI | Manual final |
| --- | --- | --- | --- | --- |
| R8.1 | Asset/Vault contracts, identity, schemas + boundary | `0e382bcdc82c5d289a9007c40d4a4b6c72120e5c` | R0 #1043; Python #1017; UI #984 | NONE |
| R8.2 | Inter-project Vault store, revisions, reuse + preservation | `2046b981cb9506999c40e3fee1a22608efecaa80` | R0 #1045; Python #1019; UI #986 | NONE |
| R8.3 | Source/derived lineage + reproducible transform cache/rebuild | `a1b0b6b4e07b15521acdd3a86dd963ebe4acc9c8` | R0 #1047; Python #1021; UI #988 | NONE |
| R8.4 | Duplicate + near-duplicate detection | `4bf9cbd4892208084cd8ce6554edfd96a971bc04` | R0 #1050; Python #1024; UI #991 | NONE |
| R8.5 | Semantic asset search + hybrid ranking | `08c90bd8d52a7dd2dfc8da6ce94f6731701469f6` | R0 #1052; Python #1026; UI #993 | CONDITIONAL NOT TRIGGERED |
| R8.6 | Provenance, license/BOM + governed reuse/export | `8c88aeb8a32abce2e9ecb670da3c2acbb4a31cfe` | R0 #1057; Python #1031; UI #998 | NONE |
| R8.7 | Asset-aware Git/VCS integration | `c52c54ae8b4c1eee386b4dbbdec945fa04afa0f3` | R0 #1061; Python #1035; UI #1002 | NONE |
| R8.8 | Git LFS tracking, pointer/object integrity + diagnostics | `32e5ace263546d85ee662c5ba333caaaefaa8bcc` | R0 #1066; Python #1040; UI #1007 | CONDITIONAL NOT TRIGGERED |
| R8.9 | Godot 4.7 source/import bridge + rebuild verification | `da8b4aedd280dadffcf4099bfa2b902cb70d81a7` | R0 #1071; Python #1045; UI #1012 | REQUIRED SATISFIED |
| R8.10 | CLI + KodeStudio Vault/Asset/VCS UX | `6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22` | R0 #1083; Python #1057; UI #1024 | NONE |
| R8.11 | Adversarial hardening + R8 integrated acceptance | `d1589cf94545b854f995e7b6706c4b67e9b7ac1a` | R0 #1092; Python #1066; UI #1033; final doc gates #1098/#1072/#1039 | CONDITIONAL NOT TRIGGERED |

### R8.1 accepted baseline

- Logical `AssetId` is separate from immutable `AssetRevisionId`.
- Revision identity is bound to canonical content/provenance/lineage semantics, not mutable runtime status or path/display name.
- SHA-256 + exact byte length verifies immutable content.
- `VaultBoundary` composes accepted `WorkspaceBoundary` confinement; traversal, absolute and symlink escapes fail closed.
- Versioned record/revision/project-reference schemas and tamper-checked canonical loading are accepted.

### R8.2 accepted baseline

- Vault bytes are content-addressed under SHA-256 identity; identical bytes may share storage while logical revisions/provenance remain distinct.
- Canonical JSON manifests are recovery authority; SQLite is a rebuildable index.
- Ingest and materialization operate only through explicit authorized project/Vault boundaries and verify staged/target bytes.
- Project references and pinned-source policy block deletion. Deletion is two-phase and object removal occurs only when no remaining revision requires it.

### R8.3 accepted baseline

- Source and derived revisions remain explicit and linked by exact lineage edges.
- Transform cache identity includes exact input revisions/digests, versioned recipe, tool/provider identity and relevant environment identity.
- Callers select a registered transform and typed parameters only; no arbitrary executable/argv/cwd/environment surface is exposed.
- Transform output is confined to managed staging, verified before promotion, and cancelled work does not become READY.
- Cache paths alone never imply validity; stale/corrupt/missing output is not a cache hit.

### R8.4 accepted baseline

- Exact duplicate identity is SHA-256 + length; it does not erase logical provenance.
- Near-duplicate fingerprints are typed/versioned evidence with explicit score/threshold and never semantic truth.
- Image dHash and deterministic normalized-document fingerprints are accepted for their supported kinds.
- Duplicate decisions are durable non-destructive records; there is no destructive auto-merge.
- Precursor `72bfdeddd78df1676addc4e0c4a78e4d9a8e3936` was not accepted because it added two Pillow deprecation warnings; final head restored the baseline to 46 warnings.

### R8.5 accepted baseline

- Search documents and vector indexes are rebuildable and separate from canonical Vault source manifests/bytes.
- Vector validity is bound to provider + model + provider-contract version + exact search-document digest.
- Metadata/model/provider changes surface `STALE`; missing/unavailable vectors never become current silently.
- Ranking policy v1 combines deterministic lexical relevance and cosine semantic similarity; exact facets filter before ranking.
- Governance `BLOCKED` records are excluded by policy before score ordering, not merely penalized.
- Lexical fallback remains available when the embedding provider is unavailable.
- `OllamaEmbeddingProvider` reuses the accepted R3 `OllamaClient.embed` API; no second arbitrary network/model-download surface was created.
- Manual CONDITIONAL was NOT TRIGGERED because no EMBED contract change/new authoritative hardware-local model was required.

### R8.6 accepted baseline

- Canonical R8 Vault revisions bridge into the existing R6 BOM/license policy engine; no second legal engine exists.
- Missing or conflicting license evidence is explicit and blocks export rather than becoming unrestricted reuse.
- Provenance, creator/publisher, attribution and notice evidence are preserved; local filesystem locators are hashed/redacted from exported reports.
- Derived asset BOM components retain explicit source-revision lineage requirements, so transformation never invents or erases rights.
- Project BOM contribution is derived from canonical Vault project references.
- Export performs policy/reuse-scope preflight before writes, stages inside the authorized boundary, emits notices plus BOM/license evidence, and promotes atomically; blocked/failed export leaves no promoted partial target.
- Exact accepted head `8c88aeb8a32abce2e9ecb6706c4b67e9b7ac1a`; R0 #1057 / `32603562499`; Python Core #1031 / `32603562511` 5/5 with Ubuntu `547 passed / 5 skipped / 46 warnings`; UI Smoke #998 / `32603562503`; PR #91 merge `57c2aa010f438b95a3d753040f1565ae4b68e262`; manual NONE.
- Rejected precursor `85b6c0a550297934194a58122b735a9d0808c5c6` failed only newly added fixture tests because the fixture misused frozen `ProjectAssetReference`/R8.3 transform contracts; the accepted correction changed the fixture and did not weaken production safeguards.

### R8.7 accepted baseline

- Asset VCS is a structured local-only adapter over the accepted R4/ProcessSandbox Git boundary; no arbitrary Git command surface was added.
- Repository evidence exposes exact HEAD, branch/detached state and typed modified/added/deleted/renamed/untracked/ignored/conflicted states parsed from machine-stable porcelain `-z` output.
- Binary diff metadata uses `--numstat`; binaries remain explicit and never receive fabricated text-line counts.
- Stage/unstage requires explicit workspace-confined paths, rejects `.git` metadata and traversal, snapshots the index with `SafeChangeManager`, and appends tamper-evident audit events.
- Git index discovery uses `git rev-parse --git-path index`, retaining compatibility with managed worktrees without assuming `.git` is a directory.
- Vault revision ↔ working repository evidence records SHA-256, exact length, tracked state and last commit SHA; working bytes cannot silently claim equality with a different Vault revision.
- No remote push, arbitrary flags/refspecs/config keys, merge/rebase automation or history rewrite is exposed.
- Exact accepted head `c52c54ae8b4c1eee386b4dbbdec945fa04afa0f3`; R0 #1061 / `32603884834`; Python Core #1035 / `32603884762` 5/5 with Ubuntu `552 passed / 5 skipped / 46 warnings`; UI Smoke #1002 / `32603884719`; PR #93 merge `b90ddcb1b4823442a9e58c7a0c1444966c5bd8a9`; manual NONE.

### R8.8 accepted baseline

- Git LFS pointer v1 parsing is independent, strict and canonical: version URL, SHA-256 OID, exact size and ordered extension evidence are validated without invoking a remote.
- Git LFS capability/list/fsck operations use a fixed local ProcessSandbox surface; fetch/pull/push and migration/history rewrite are not exposed.
- `.gitattributes` heavy-asset policy and path-effective attributes are inspectable; updates are restricted to the frozen policy set, explicitly confirmed, SafeChange-snapshotted, atomic and audited.
- Pointer, invalid pointer, missing/mismatched local LFS object, hydrated match/mismatch and pointer-only working tree are distinct states.
- Local object probing is confined to the authorized Git common directory; an external storage location est explicit `UNAVAILABLE`.
- Exact accepted head `32e5ace263546d85ee662c5ba333caaaefaa8bcc`; R0 #1066 / `32604356727`; Python Core #1040 / `32604356661` 5/5 with Ubuntu `558 passed / 5 skipped / 46 warnings`; UI Smoke #1007 / `32604356692`; PR #95 merge `8923f6aa75656033887dd93551fc7b2651d78f04`; manual CONDITIONAL NOT TRIGGERED.
- Rejected precursor `6b02a22fb4c526a53579a96e81ade3a3088a5e88` failed one new fixture because the active LFS clean filter rewrote the malformed test case; accepted fixture now stages exact raw blobs and production safeguards were not weakened.

### R8.9 accepted baseline

- Exact accepted implementation head `da8b4aedd280dadffcf4099bfa2b902cb70d81a7`.
- R0 Repository Guard #1071 / `32613177879`: SUCCESS Ubuntu + Windows.
- Python Core #1045 / `32613177848`: SUCCESS 5/5; Ubuntu `565 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #1012 / `32613177859`: SUCCESS.
- The frozen CONDITIONAL Godot gate became REQUIRED because hosted CI does not execute the authoritative real Godot 4.7 `--import` rebuild.
- Required local acceptance is SATISFIED: 4/4 PASS, 0 failed, Godot `4.7.2.stable.steam.ed1daf0bf`, rebuild state `ready`, import return code `0`, 7 generated cache files, audit chain valid.
- Local evidence SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`, 2969 bytes.
- Project digest `bac971ef0dc7a0c8898cea3a7e5d788b9d33343690f28ca52c3af98b9022c212`; source digest `d6b791957eb782fbb0b00272b902c025fb4cc3b9d396b850d64a8ffc050c6091`; import sidecar digest `1b70ea13afe340575035099e25ccceeea41e22153d3700449b2f8c2e66dfbd87`; manifest digest `aca5eb8dd2c877a17eadd666c29239a3f95c2674c776f86cc5cabafc6b1f47d8`.
- `.godot/**` and legacy `.import/**` are generated cache, never source authority; `<asset>.import` is reproducibility metadata bound to the source/Vault identity.
- Rebuild reuses the accepted R5 KodeGodotExecutor/Guardian/Permissions/ProcessSandbox path; no arbitrary subprocess/argv surface was added.
- Missing/incompatible Godot is explicit `UNAVAILABLE` before cache purge; cache-root symlinks fail closed; source/project mutation during import fails acceptance.
- Final acceptance/continuity documentation head `5db05258e666f1ed77a0ef349becc965f7105b43`; R0 #1073 / `32613557555`; Python #1047 / `32613557563`; UI #1014 / `32613557610`; all SUCCESS.
- PR #97 merged as `af371bf07c56aa60a91ae3e39b14cc60c3307151`.

### R8.10 accepted baseline

- Exact accepted implementation head `6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22`; base normalized R8.9 main `8ca2eec6192b3d82495309b1c5bc2e6e8e49132a`.
- R0 Repository Guard #1083 / `32614391934`: SUCCESS Ubuntu + Windows.
- Python Core #1057 / `32614392022`: SUCCESS 5/5; Ubuntu `571 passed / 6 skipped / 46 warnings`; package builds Ubuntu + Windows SUCCESS.
- KodeStudio UI Smoke #1024 / `32614391930`: SUCCESS; Python Core integrated Windows UI smoke SUCCESS.
- Final pre-merge documentation/continuity head `29928598224aa8df74a768984928733b1d52ef94`; R0 #1086 / `32620855929`, Python Core #1060 / `32620855945`, UI Smoke #1027 / `32620855926`; all SUCCESS.
- PR #99 merged as `a72da6be019f2b1771ab42d04b37c44b0d7464d3`.
- Post-merge normalization head `ca7a0efe3ec0065199cf8c1a61b7eb9f97e76f13`; R0 #1088 / `32620997813`, Python #1062 / `32620997824`, UI #1029 / `32620997864`; all SUCCESS; PR #100 merge `32c9dc413a89b74cd702c25b21a257cfc21d3cfc`.
- `AssetService` is the single façade used by CLI and KodeStudio over Vault/search/duplicates/governance/VCS/LFS. KodeStudio contains no second direct Git/LFS/process/socket/secret path.
- Unknown/missing license evidence remains `NOASSERTION`/blocked; governed export still uses R8.6/R6 and cannot be silently allowed.
- Materialize overwrite, Vault deletion and asset export require explicit confirmation; duplicates remain non-destructive evidence.
- KodeStudio Vault UX exposes search filters, explicit blocked-result opt-in, details/license warning, duplicate evidence, rebuild, VCS/LFS health/evidence, lineage source→derived, visible operation budget/progress and cooperative cancellation.
- Long operations run via `QThreadPool`/`QRunnable`; each worker uses `AssetService.fork()` with independent SQLite connections instead of sharing the UI service across threads.
- R6.5 accessibility and R6.6 pseudo-localization contracts were extended for Vault; both UI workflows execute the R8.10 smoke.
- Manual intervention: NONE.

### R8.11 accepted baseline

- Exact accepted implementation head `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`; base normalized R8.10 main `32c9dc413a89b74cd702c25b21a257cfc21d3cfc`.
- Implementation gates: R0 Repository Guard #1092 / `32621457672`: SUCCESS Ubuntu + Windows; Python Core #1066 / `32621457675`: SUCCESS 5/5 with Ubuntu `587 passed / 7 skipped / 46 warnings`; KodeStudio UI Smoke #1033 / `32621457788`: SUCCESS.
- Final documentation head `456c072108917a93176454adaa68234f4c087e57`: R0 #1098 / `32621787439` SUCCESS; Python Core #1072 / `32621787435` SUCCESS 5/5 with `R8 integrated acceptance: PASS` and Ubuntu `588 passed / 6 skipped / 46 warnings`; UI Smoke #1039 / `32621787433` SUCCESS.
- R8-specific integrated model/schema are separate from frozen R7: exactly R8.1–R8.11, canonical acceptance source, SHA-256, exact byte length, accepted head, manual state + explicit reason, derived satisfaction, blockers and deterministic digest.
- Repository validation uses canonical Git blobs via `git show HEAD:<path>` and fails closed on missing/mismatched bytes, hash, head or manual state.
- Adversarial suite covers forged manifest, poisoned SQLite rebuildable index, transform staging escape, cross-output cache poisoning, hostile metadata, Git option-shaped filename, malformed LFS pointer, pre-cancel rebuild, failed materialization and bounded many-asset fixture.
- Rejected first candidate `28fe9610bcdf9d92a4e6aa0367441b342bfd288b`: Python Ubuntu correctly found one real transform-cache cross-output identity defect and one fixture assertion type mismatch. Gates were not weakened.
- Production hardening commit `781e2cc154b3be8d7f120fbf62da09ad0d8af8ad`: cache HIT now binds inputs, recipe, tool, environment, requested logical output asset, content digest/length, DERIVED role/kind, READY status, lineage and transform provenance. Old cache docs lacking output identity become STALE and rebuild.
- `docs/roadmap/R8_11_ACCEPTANCE.md` fixes implementation head `d1589cf...`; manual CONDITIONAL resolves to **CONDITIONAL NOT TRIGGERED** because R8.5/R8.8 inherited conditionals remain resolved, R8.9 REQUIRED remains SATISFIED, and hosted CI can execute the integrated path.
- `scripts/r8_integrated_acceptance.py` emits or validates the canonical report; Linux Python Core executes it before pytest.
- Canonical report `docs/roadmap/R8_INTEGRATED_ACCEPTANCE.json`: `schema_version=1`, `source_sha=d1589cf94545b854f995e7b6706c4b67e9b7ac1a`, `status=pass`, `blockers=[]`, `evidence_sha256=6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`.
- PR #101 merged as `2a3a0b7da3803fb4d59158b94b9219aded201f17`.
- Final continuity-only normalization first head `f2004ffbfada8ee7e6cdb942efc19d2aa7aecb6d`: R0 #1100 / `32622694931`, Python Core #1074 / `32622694930` 5/5 with R8 verifier PASS, UI Smoke #1041 / `32622694936`; all SUCCESS.
- Manual intervention: CONDITIONAL NOT TRIGGERED.

## R8 exact merge chain

- R8.1 PR #85 merge `7001d9042dda5611f4dbcf7dacb7cd29110e6735`.
- R8.2 PR #86 merge `2d68f918b1058c1dd75be236ad74048eb598a3e6`.
- R8.3 PR #87 merge `ec83fba0e664387ec4abccf047721d1ab77d4a8e`.
- R8.4 PR #88 merge `a35502e0f5f09e07f3ddfd7f929f6d4d4bb490f7`.
- R8.5 PR #89 merge `9bb1f169d7f1534b0068ad43691accf1b6a5e14a`.
- R8.6 PR #91 merge `57c2aa010f438b95a3d753040f1565ae4b68e262`.
- R8.7 PR #93 merge `b90ddcb1b4823442a9e58c7a0c1444966c5bd8a9`.
- R8.8 PR #95 merge `8923f6aa75656033887dd93551fc7b2651d78f04`.
- R8.9 PR #97 merge `af371bf07c56aa60a91ae3e39b14cc60c3307151`.
- R8.10 PR #99 merge `a72da6be019f2b1771ab42d04b37c44b0d7464d3`; normalization PR #100 merge `32c9dc413a89b74cd702c25b21a257cfc21d3cfc`.
- R8.11 PR #101 merge `2a3a0b7da3803fb4d59158b94b9219aded201f17`.
- R8 final normalization PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`; accepted planning branch point for R9.

## R7 source of truth retained

R7 remains COMPLETE and must not be reinterpreted retroactively.

- R7.1 `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` — manual NONE.
- R7.2 `9101e686a32b24bb33a23d7ac578bf25570e115e` — manual NONE.
- R7.3 `4efd2cb016e774fa3ef06590ffda377606d875e9` — manual NONE.
- R7.4 `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be` — CONDITIONAL NOT TRIGGERED.
- R7.5 `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5` — manual NONE.
- R7.6 `b623836b8f5bd39fce101eca7fe4653a996a9562` — CONDITIONAL NOT TRIGGERED.
- R7.7 `04cef94c82fdacafe7313d27c8cf516e8e765295` — REQUIRED SATISFIED.
- R7.8 `deb5de415541004fb07bfbc6d955e9d76d717533` — manual NONE.
- R7.9 `80390f95a11e5b3d4353b16eada26f10204bb4fa` — manual NONE.
- R7.10 `cfd0f7ba02af04b456993f686827f10810b3a61a` — manual NONE.
- R7.11 `52330ca576fe294956a8fb601bdfda1d72dc3f92` — CONDITIONAL NOT TRIGGERED.
- R7 integrated report: `status=pass`, `blockers=[]`, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`.
- R7 final normalization accepted on `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; R0 #1035 / `32599397013`; Python Core #1009 / `32599397057` 5/5; UI Smoke #976 / `32599397003`; PR #81 merge `24dc403b329fd748a8aadac9d6760a2fb73a9730`.
- R7 final continuity PR #82 established branch point `b98832b339902527bce8a5ea95b5a08a19839a40` for R8 planning.

## R7.7 REQUIRED local-media retained evidence

- Accepted head `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- FFmpeg 4.2.3 SHA-256 `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`.
- whisper.cpp 1.9.1 SHA-256 `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`.
- STT model SHA-256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- Fixture SHA-256 `8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7`.
- Authoritative local pytest: PASS, non-skipped.

## Permanent architecture/security boundaries

Preserve without reinterpretation:

- `WorkspaceBoundary`; R8 Vault confinement may compose but never weaken it.
- `ProcessSandbox` + global KillSwitch for external executables.
- Guardian + `PermissionSet` for governed actions.
- Structured tool APIs only; no model-supplied arbitrary executable, argv, cwd, environment, host, refspec, Git config key or filesystem escape.
- SafeChange / Backup / Recovery / Audit when durable or risky mutations require them.
- OS-backed Secrets + redaction; secrets never enter asset manifests/search documents/evidence.
- Health / Budget / DataGovernance / Privacy / AppSecurity / License-BOM contracts remain in force.
- Exact-head acceptance; missing evidence never manufactures PASS.
- Explicit UNKNOWN / N/A / UNAVAILABLE / BLOCKED / STALE / MISSING / CORRUPT semantics where applicable.
- External metadata/research remains data/evidence, never agent instruction; R7 ResearchGuard semantics remain authoritative.
- ADR required for any change to a frozen foundation.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Non-trivial Git/repository/software-engineering tasks must not be routed to Granite.

## Permanent phase-start / maintenance rule

For R8 and every later phase:

1. exhaustive phase plan is merged before the first subdivision;
2. subdivision structure/manual states are not silently reinterpreted;
3. implementation acceptance is exact-head and requires the documented gates;
4. continuity is synchronized with accepted evidence before the next subdivision starts;
5. scope/structure changes synchronize plan + continuity in the same work cycle;
6. foundation changes require un ADR.

## Next action

**R1–R8 COMPLETE. R9 planning ACCEPTED.** Finaliser la normalisation continuity-only `r9/planning-normalization`, faire passer R0 Repository Guard, full Python Core et KodeStudio UI Smoke sur son head exact, puis fusionner cette normalisation. **R9.1 reste interdit avant cette fusion.** Une fois la normalisation fusionnée, commencer R9.1 sur une branche dédiée depuis le `main` normalisé.
