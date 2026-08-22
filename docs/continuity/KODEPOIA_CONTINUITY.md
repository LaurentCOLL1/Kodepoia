# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R7 COMPLETE. R8 planning ACCEPTED. R8.1–R8.5 COMPLETE. R8.6 AUTHORIZED / NOT STARTED.** `docs/roadmap/R8_PLAN.md` reste l'autorité structurelle exhaustive R8.1–R8.11. Les acceptances R8.1–R8.5 sont exact-head et fusionnées. R8.5 manual = CONDITIONAL NOT TRIGGERED. La prochaine action autorisée est **R8.6 — Provenance, license/BOM + governed reuse/export**, sur une branche dédiée depuis le `main` normalisé après l'acceptance R8.1–R8.5. Ne pas commencer R8.7 directement. Toute modification de structure R8 synchronise plan + continuité; tout changement de fondation exige un ADR.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée.
- R1–R6 : COMPLETE.
- R7 : COMPLETE.
- R8 planning : ACCEPTED.
- R8.1–R8.5 : COMPLETE.
- R8.6 : AUTHORIZED / NOT STARTED.
- R8.7–R8.11 : PLANNED / NOT STARTED.
- R9–R16 : PENDING / NOT STARTED.

## R8 planning acceptance

- Branch point : `b98832b339902527bce8a5ea95b5a08a19839a40`.
- Planning head exact : `08844fc09501ed8a4974909eca4595021bc73bf4`.
- R0 Repository Guard #1039 / `32600268817` : SUCCESS Ubuntu + Windows.
- Python Core #1013 / `32600268710` : SUCCESS 5/5.
- KodeStudio UI Smoke #980 / `32600268680` : SUCCESS.
- PR #83 merge : `60412afac35678b2a25547a7f0c937891a8a1004`.
- Planning normalization PR #84 merge : `dfc07ee3dbb746b66c2dabd945b4015979f374d3`.

## R8 accepted structure and evidence

| ID | Title | Exact accepted head | CI | Manual final |
| --- | --- | --- | --- | --- |
| R8.1 | Asset/Vault contracts, identity, schemas + boundary | `0e382bcdc82c5d289a9007c40d4a4b6c72120e5c` | R0 #1043; Python #1017; UI #984 | NONE |
| R8.2 | Inter-project Vault store, revisions, reuse + preservation | `2046b981cb9506999c40e3fee1a22608efecaa80` | R0 #1045; Python #1019; UI #986 | NONE |
| R8.3 | Source/derived lineage + reproducible transform cache/rebuild | `a1b0b6b4e07b15521acdd3a86dd963ebe4acc9c8` | R0 #1047; Python #1021; UI #988 | NONE |
| R8.4 | Duplicate + near-duplicate detection | `4bf9cbd4892208084cd8ce6554edfd96a971bc04` | R0 #1050; Python #1024; UI #991 | NONE |
| R8.5 | Semantic asset search + hybrid ranking | `08c90bd8d52a7dd2dfc8da6ce94f6731701469f6` | R0 #1052; Python #1026; UI #993 | CONDITIONAL NOT TRIGGERED |
| R8.6 | Provenance, license/BOM + governed reuse/export | NOT STARTED | — | NONE planned |
| R8.7 | Asset-aware Git/VCS integration | NOT STARTED | — | NONE planned |
| R8.8 | Git LFS tracking, pointer/object integrity + diagnostics | NOT STARTED | — | CONDITIONAL planned |
| R8.9 | Godot 4.7 source/import bridge + rebuild verification | NOT STARTED | — | CONDITIONAL planned |
| R8.10 | CLI + KodeStudio Vault/Asset/VCS UX | NOT STARTED | — | NONE planned |
| R8.11 | Adversarial hardening + R8 integrated acceptance | NOT STARTED | — | CONDITIONAL planned |

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

## R8 exact merge chain

- R8.1 PR #85 merge `7001d9042dda5611f4dbcf7dacb7cd29110e6735`.
- R8.2 PR #86 merge `2d68f918b1058c1dd75be236ad74048eb598a3e6`.
- R8.3 PR #87 merge `ec83fba0e664387ec4abccf047721d1ab77d4a8e`.
- R8.4 PR #88 merge `a35502e0f5f09e07f3ddfd7f929f6d4d4bb490f7`.
- R8.5 PR #89 merge `9bb1f169d7f1534b0068ad43691accf1b6a5e14a`.

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
4. continuity is synchronized with accepted evidence;
5. scope/structure changes synchronize plan + continuity in the same work cycle;
6. foundation changes require an ADR.

## Next action

**R1–R7 COMPLETE. R8.1–R8.5 COMPLETE. R8.6 AUTHORIZED / NOT STARTED.** The next allowed implementation is only **R8.6 — Provenance, license/BOM + governed reuse/export** from normalized `main`. Do not start R8.7 first.
