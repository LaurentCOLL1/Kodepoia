# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1–R9.8 COMPLETE + NORMALIZED. R9.9 implementation ACCEPTED; final documentation/continuity gates pending.** `docs/roadmap/R9_PLAN.md` reste l’autorité structurelle exhaustive de R9.1–R9.11. R9.8 REQUIRED est SATISFIED sur l’implementation head `86777ddc7a87ad6041ddc599e20e93af38512a19` par l’evidence locale canonique SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967` (5744 octets). R9.8 final documentation/continuity head `935c977926a11a7ba93f77c49a20b0eebe568b6d` a passé R0 #1181 / `32643022172`, Python Core #1155 / `32643022212` 5/5 avec Ubuntu `719 passed / 6 skipped / 46 warnings`, et UI Smoke #1122 / `32643022181`; PR #119 a fusionné sous `647039ad4cb6a0fa0c369ba5eeb97c153b561637`. Sa normalisation continuity-only head `586097a25d6027b2c7a86d44c8876a6728cbf2d6` a passé R0 #1183 / `32643425656`, Python Core #1157 / `32643425619`, UI Smoke #1124 / `32643425675`; PR #120 a fusionné sous `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`. R9.9 est acceptée côté implémentation sur `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324` avec R0 #1188 / `32644669495`, Python Core #1162 / `32644669572` 5/5 et Ubuntu `724 passed / 6 skipped / 46 warnings`, UI Smoke #1129 / `32644669558`, tous SUCCESS. Le premier candidat `a8913dd1c46730babec7ac123e65de4bb6c8ca52` est REJECTED : Python Core #1159 a découvert deux défauts R9.9, corrigés sans affaiblir les gates. Manual R9.9 = **CONDITIONAL NOT TRIGGERED**. Le head documentaire antérieur `1b2172f29d0e51909c33e161e7748e2e64f41948` a passé R0 #1189 / `32644989683`, Python #1163 / `32644989676`, UI #1130 / `32644989677`, mais ce commit de continuité crée un nouveau head qui doit repasser les trois gates avant merge PR #121. **Ne pas commencer R9.10 avant merge + normalisation post-merge de R9.9.**

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée et sa normalisation requise.
- R1–R6 : COMPLETE.
- R7 : COMPLETE.
- R8 : COMPLETE.
- R9 planning : ACCEPTED + NORMALIZED.
- R9.1 : COMPLETE + NORMALIZED.
- R9.2 : COMPLETE + NORMALIZED; manual CONDITIONAL NOT TRIGGERED.
- R9.3 : COMPLETE + NORMALIZED.
- R9.4 : COMPLETE + NORMALIZED.
- R9.5 : COMPLETE + NORMALIZED; manual CONDITIONAL NOT TRIGGERED.
- R9.6 : COMPLETE + NORMALIZED.
- R9.7 : COMPLETE + NORMALIZED.
- R9.8 : COMPLETE + NORMALIZED; manual REQUIRED SATISFIED.
- R9.9 : implementation ACCEPTED; final documentation/continuity exact-head gates pending on this synchronized head; manual CONDITIONAL NOT TRIGGERED.
- R9.10 : PLANNED / NOT STARTED.
- R9.11 : PLANNED / NOT STARTED.
- R10–R16 : PENDING / NOT STARTED.

## R9 planning acceptance

- Frozen-roadmap title : **ComfyUI + VRAM**.
- Planning branch point / normalized R8 `main` : `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.
- Exact accepted planning head : `fc73a3c96cecb78820f9e94738ace2c280dc4251`.
- R0 #1103 / `32623437662`, Python Core #1077 / `32623437659`, UI Smoke #1044 / `32623437660` : SUCCESS.
- Planning PR #103 merged as `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`.
- Planning normalization head `51a6bb7d04d8aacd47e621b15a747f6e9d08781c` : R0 #1106 / `32623679409`, Python #1080 / `32623679387`, UI #1047 / `32623679382`, all SUCCESS; PR #104 merge `e3f7bf6039cee918a5d505fb47ed536cde087e0e`.
- Frozen subdivision count : 11 (`R9.1`–`R9.11`).
- Frozen manual states : R9.1 NONE; R9.2 CONDITIONAL; R9.3 NONE; R9.4 NONE; R9.5 CONDITIONAL; R9.6 NONE; R9.7 NONE; R9.8 REQUIRED; R9.9 CONDITIONAL; R9.10 NONE; R9.11 CONDITIONAL.

## R9 accepted structure and evidence

| ID | Title | Exact accepted implementation/final head | Hosted acceptance | Manual final |
| --- | --- | --- | --- | --- |
| R9.1 | ComfyUI contracts, local endpoint boundary + capability schema | `cb746fbfe1f318a5b05d4a6e35f1b8afb2338b58` | R0 #1109; Python #1083; UI #1050 | NONE |
| R9.2 | Typed HTTP/WebSocket client, health, queue/history + protocol state | `89ea9d90ffab6db3563164e629f192caca91ed79` | R0 #1117; Python #1091; UI #1058 | CONDITIONAL NOT TRIGGERED |
| R9.3 | Node/model inventory + capability snapshots | `97e47799f6efe30eed58d73abf509d9d34ed862d` | R0 #1127; Python #1101; UI #1068 | NONE |
| R9.4 | Validated workflow catalog + governed model resolver | `45c2fbd3125d654cbac843e1f90133d81da12395` | R0 #1134; Python #1108; UI #1075 | NONE |
| R9.5 | Execution engine, queue/progress/reconciliation + run manifests | `ee927d50e2af9045dc80c3183aa122b1f87a30c3` | R0 #1144; Python #1118; UI #1085 | CONDITIONAL NOT TRIGGERED |
| R9.6 | Generated-output capture + R8 Vault/AssetPipeline lineage bridge | `ccc2d5f440322c433a9853e9642bff7efb5d0d0e` | R0 #1150; Python #1124; UI #1091 | NONE |
| R9.7 | Cancellation, interruption, crash recovery + free-memory semantics | `c38a6c3d9a8e60acdc6fc46e38f46f1402ccb696` | R0 #1156; Python #1130; UI #1097 | NONE |
| R9.8 | VRAM telemetry, admission scheduler + Ollama coexistence | impl `86777ddc7a87ad6041ddc599e20e93af38512a19`; docs `935c977926a11a7ba93f77c49a20b0eebe568b6d` | R0 #1181; Python #1155; UI #1122 | REQUIRED SATISFIED |
| R9.9 | Production 2D/UI/texture/concept workflow packs | impl `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324` | R0 #1188; Python #1162; UI #1129 | CONDITIONAL NOT TRIGGERED |
| R9.10 | CLI + KodeStudio ComfyUI/VRAM UX | — | — | NONE |
| R9.11 | Adversarial hardening + R9 integrated acceptance | — | — | CONDITIONAL |

### R9.1–R9.4 retained baseline

- `ComfyEndpoint` accepts only explicit loopback literals `127.0.0.1` / `::1` with explicit port and rejects credentials, non-root origin paths/query/fragment, non-loopback and redirect origin changes.
- `ComfyUIClient` exposes a fixed typed surface only; response bodies/WebSocket frames are bounded, HTTP redirects stay exact-origin loopback, and queue/history remain terminal execution authority.
- R9.3 capability identity binds endpoint/system/features/nodes/models/unavailable evidence while timestamp does not change identity; capability drift is explicit `STALE`.
- R9.4 `WorkflowDefinition` binds canonical graph/revision/allowlisted classes/parameters/model requirements; only declared `$param`, `$input`, `$model` markers are substitutable and arbitrary graph fragments are rejected.
- `GovernedModelResolver` resolves only discovered inventory tokens. Ambiguity requires explicit selection; external-local models without R8 evidence remain `NOASSERTION` and non-exportable.

### R9.5–R9.7 retained baseline

- R9.5 persists `PREPARED` before the first and only prompt POST; ambiguous submission never triggers an automatic second POST. Run manifests are append-only and terminal success requires coherent history plus required output references.
- R9.6 retrieves only reconciled prompt outputs through the fixed client, validates path/hash/length/type before promotion, then routes generated assets through unchanged R8 `AssetService` / `TransformService` lineage and governance.
- R9.7 cancellation reconciles state before and after the side effect; targeted safe cancellation is preferred and legacy global `/interrupt` is not used as an unsafe substitute. `/free` is a request, never proof of reclaimed bytes.

### R9.8 accepted baseline

- Base normalized R9.7 `main` : `5cfea5053ef0e32b055aa85309e0ff849ef827e2`.
- Accepted implementation head : `86777ddc7a87ad6041ddc599e20e93af38512a19`.
- Hosted implementation gates : R0 #1179 / `32642291824`, Python Core #1153 / `32642291811`, UI Smoke #1120 / `32642291850`; Ubuntu `719 passed / 6 skipped / 46 warnings`; all SUCCESS.
- Manual REQUIRED : **SATISFIED** on the same head with evidence `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, 5744 bytes.
- Real loopback ComfyUI `0.33.0` reported device `cuda:0 AMD Radeon RX 6750 XT : native`, total VRAM `12868124672`, admission-time free `12461146112` bytes.
- Resource profile estimate `8589934592`, reserve `536870912`, headroom `536870912`; scheduler `admit`.
- Real generation workflow `wf_3aa2ac5225d8a3d88bcf8b3b7aee7205`; output SHA-256 `a18b2eae0fd90f36382e92638bef7984cd591cfd8d9d2466941f66e65f488e92`, length `1029726`; observed peak delta `8050443776`, OOM false.
- `/free`/unload acknowledgement was followed by remeasurement; `reclaimed_bytes` remains deliberately null.
- Ollama coexistence = `n/a`; no model was loaded/downloaded solely for acceptance.
- Final documentation/continuity head `935c977926a11a7ba93f77c49a20b0eebe568b6d`: R0 #1181, Python #1155, UI #1122, all SUCCESS; PR #119 merge `647039ad4cb6a0fa0c369ba5eeb97c153b561637`.
- Post-merge continuity normalization head `586097a25d6027b2c7a86d44c8876a6728cbf2d6`: R0 #1183 / `32643425656`, Python #1157 / `32643425619`, UI #1124 / `32643425675`, all SUCCESS; PR #120 merge `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`.

### R9.9 accepted implementation baseline

- Base normalized R9.8 `main` : `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`.
- Branch : `r9/9-production-workflow-packs`; PR #121.
- Rejected first candidate : `a8913dd1c46730babec7ac123e65de4bb6c8ca52`. R0 #1185 and UI #1126 succeeded, but Python Core #1159 failed with two newly introduced defects: the aggregate-pixel test did not actually exceed its configured ceiling, and an empty negative prompt contradicted the already-frozen R9.4 scalar-string contract. No gate was weakened.
- Production correction tightened aggregate pixel budgets to ensure multi-output requests have an effective bound and requires a non-empty bounded negative prompt consistent with R9.4.
- Exact accepted implementation head : `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324`.
- Implementation gates : R0 #1188 / `32644669495`, Python Core #1162 / `32644669572` 5/5, UI Smoke #1129 / `32644669558`, all SUCCESS; Ubuntu `724 passed / 6 skipped / 46 warnings`; Windows tests and Ubuntu/Windows package builds SUCCESS; R7/R8 integrated acceptance PASS.
- Four mandatory governed families are present : `concept`, `ui_illustration`, `material_source`, `sprite_2d`.
- Packs use only governed core-node definitions, explicit resolver-driven checkpoint selection and bounded typed parameters. No custom-node installer, model download, arbitrary graph execution, process surface or URL surface is introduced.
- Seeds/settings, width/height, output count, aggregate pixels and estimated VRAM are explicit. `material_source` is explicitly source-only and cannot claim production-ready validated PBR semantics.
- Missing/ambiguous model resolution remains explicit `BLOCKED`; compatibility is bound to a CURRENT capability snapshot.
- The frozen R9.9 CONDITIONAL trigger is **NOT TRIGGERED** because the mandatory packs introduce no required real node/model family outside the already accepted core checkpoint generation family exercised by R9.8.
- Acceptance source : `docs/roadmap/R9_9_ACCEPTANCE.md`. The prior documentation-only head `1b2172f29d0e51909c33e161e7748e2e64f41948` passed R0 #1189 / `32644989683`, Python #1163 / `32644989676`, UI #1130 / `32644989677`; this synchronized continuity commit supersedes that head for final exact-head acceptance.

## R8 retained source of truth

R8 remains COMPLETE and must not be reinterpreted. Its integrated report remains `status=pass`, `blockers=[]`, `source_sha=d1589cf94545b854f995e7b6706c4b67e9b7ac1a`, digest `6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`.

- R8.1 `0e382bcdc82c5d289a9007c40d4a4b6c72120e5c` — NONE.
- R8.2 `2046b981cb9506999c40e3fee1a22608efecaa80` — NONE.
- R8.3 `a1b0b6b4e07b15521acdd3a86dd963ebe4acc9c8` — NONE.
- R8.4 `4bf9cbd4892208084cd8ce6554edfd96a971bc04` — NONE.
- R8.5 `08c90bd8d52a7dd2dfc8da6ce94f6731701469f6` — CONDITIONAL NOT TRIGGERED.
- R8.6 `8c88aeb8a32abce2e9ecb670da3c2acbb4a31cfe` — NONE.
- R8.7 `c52c54ae8b4c1eee386b4dbbdec945fa04afa0f3` — NONE.
- R8.8 `32e5ace263546d85ee662c5ba333caaaefaa8bcc` — CONDITIONAL NOT TRIGGERED.
- R8.9 `da8b4aedd280dadffcf4099bfa2b902cb70d81a7` — REQUIRED SATISFIED; local Godot evidence SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`.
- R8.10 `6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22` — NONE.
- R8.11 `d1589cf94545b854f995e7b6706c4b67e9b7ac1a` — CONDITIONAL NOT TRIGGERED; final documentation head `456c072108917a93176454adaa68234f4c087e57`.
- Final R8 normalization PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e` established the R9 planning branch point.

## R7 retained source of truth

R7 remains COMPLETE and must not be reinterpreted retroactively. Integrated report `status=pass`, `blockers=[]`, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`.

- R7.1 `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` — NONE.
- R7.2 `9101e686a32b24bb33a23d7ac578bf25570e115e` — NONE.
- R7.3 `4efd2cb016e774fa3ef06590ffda377606d875e9` — NONE.
- R7.4 `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be` — CONDITIONAL NOT TRIGGERED.
- R7.5 `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5` — NONE.
- R7.6 `b623836b8f5bd39fce101eca7fe4653a996a9562` — CONDITIONAL NOT TRIGGERED.
- R7.7 `04cef94c82fdacafe7313d27c8cf516e8e765295` — REQUIRED SATISFIED; FFmpeg `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`; whisper.cpp `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`; STT model `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- R7.8 `deb5de415541004fb07bfbc6d955e9d76d717533` — NONE.
- R7.9 `80390f95a11e5b3d4353b16eada26f10204bb4fa` — NONE.
- R7.10 `cfd0f7ba02af04b456993f686827f10810b3a61a` — NONE.
- R7.11 `52330ca576fe294956a8fb601bdfda1d72dc3f92` — CONDITIONAL NOT TRIGGERED.
- Final R7 normalization head `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; PR #81 merge `24dc403b329fd748a8aadac9d6760a2fb73a9730`; PR #82 established the R8 planning branch point `b98832b339902527bce8a5ea95b5a08a19839a40`.

## Permanent architecture/security boundaries

Preserve without reinterpretation :

- `WorkspaceBoundary`; Vault confinement may compose but never weaken it.
- `ProcessSandbox` + global KillSwitch for external executables.
- Guardian + `PermissionSet` for governed actions.
- Structured tool APIs only; no model-supplied arbitrary executable, argv, cwd, environment, host, refspec, Git config key, URL route or filesystem escape.
- SafeChange / Backup / Recovery / Audit when durable or risky mutations require them.
- OS-backed Secrets + redaction; secrets never enter manifests/search/evidence.
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

For R8 and every later phase :

1. exhaustive phase plan is merged before the first subdivision;
2. subdivision structure/manual states are not silently reinterpreted;
3. implementation acceptance is exact-head and requires the documented gates;
4. continuity is synchronized with accepted evidence before the next subdivision starts;
5. scope/structure changes synchronize plan + continuity in the same work cycle;
6. foundation changes require un ADR.

## Next action

**R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1–R9.8 COMPLETE + NORMALIZED. R9.9 implementation ACCEPTED; manual CONDITIONAL NOT TRIGGERED.** Faire passer R0 Repository Guard, full Python Core et KodeStudio UI Smoke sur le head exact contenant `R9_9_ACCEPTANCE.md` et cette continuité synchronisée. Si les trois gates sont SUCCESS, fusionner PR #121, créer une branche dédiée `r9/9-continuity-normalization`, faire la normalisation continuity-only post-merge avec ses trois gates, fusionner cette normalisation, puis et seulement puis commencer R9.10. **R9.10 et R9.11 restent interdits avant cette séquence.**