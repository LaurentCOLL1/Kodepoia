# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1–R9.9 COMPLETE + NORMALIZED. R9.10 COMPLETE; documentation hardening merged, final continuity normalization in progress.** `docs/roadmap/R9_PLAN.md` reste l’autorité structurelle exhaustive de R9.1–R9.11. R9.8 REQUIRED est SATISFIED sur `86777ddc7a87ad6041ddc599e20e93af38512a19` par l’evidence locale canonique SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967` (5744 octets), puis normalisée via PR #120 merge `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`. R9.9 est COMPLETE + NORMALIZED via normalization head `95f9b21a3a542eea7cb339434397dc4f65429b52`, R0 #1192 / `32645877353`, Python Core #1166 / `32645877369`, UI Smoke #1133 / `32645877346`, tous SUCCESS, PR #122 merge `5831e958c45ac63f6d2bcfd7da0a7934330c7586`. R9.10 accepted implementation head = `dda09a1728ba63640f68a979af57d70f12b4c603`; R0 #1199 / `32657273588`, Python Core #1173 / `32657273603` 5/5 avec Ubuntu `729 passed / 7 skipped / 46 warnings`, UI #1140 / `32657273614`, tous SUCCESS; manual = **NONE**. PR #123 merge `4372fa9067acf6aabf242f178be0d9f7ac041fc7`; initial post-merge normalization head `7515b2bdec0d9eaec32820feb4563869f050be00`, R0 #1201 / `32657536700`, Python #1175 / `32657536745`, UI #1142 / `32657536723`, tous SUCCESS, PR #124 merge `4df1217cde078812af6882b812f640310aa45b61`. La préparation R9.11 a ensuite détecté les deux deliverables R9.10 manquants `R9_10_DESIGN.md` et `R9_10_ACCEPTANCE.md`; documentation-hardening head `10150bb3b810f6158029231edb7604b03fdb4ebb`, R0 #1203 / `32657855298`, Python #1177 / `32657855302` 5/5 avec Ubuntu `729 passed / 7 skipped / 46 warnings`, UI #1144 / `32657855311`, tous SUCCESS; PR #125 merge `c3eb519d55abb5e6d1007ef4bc96e185df8061c7`. Faire passer R0 + full Python Core + UI Smoke sur le head exact de `r9/10-documentation-hardening-normalization`, puis fusionner cette normalisation avant toute R9.11.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée et sa normalisation requise.
- R1–R6 : COMPLETE.
- R7 : COMPLETE.
- R8 : COMPLETE.
- R9 planning : ACCEPTED + NORMALIZED.
- R9.1 : COMPLETE + NORMALIZED.
- R9.2 : COMPLETE + NORMALIZED; CONDITIONAL NOT TRIGGERED.
- R9.3 : COMPLETE + NORMALIZED.
- R9.4 : COMPLETE + NORMALIZED.
- R9.5 : COMPLETE + NORMALIZED; CONDITIONAL NOT TRIGGERED.
- R9.6 : COMPLETE + NORMALIZED.
- R9.7 : COMPLETE + NORMALIZED.
- R9.8 : COMPLETE + NORMALIZED; REQUIRED SATISFIED.
- R9.9 : COMPLETE + NORMALIZED; accepted implementation head `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324`; final documentation head `deb796991d3758c748c7777bd11cdf0c8cc40c4d`; normalization head `95f9b21a3a542eea7cb339434397dc4f65429b52`; PR #122 merge `5831e958c45ac63f6d2bcfd7da0a7934330c7586`; CONDITIONAL NOT TRIGGERED.
- R9.10 : COMPLETE; accepted implementation head `dda09a1728ba63640f68a979af57d70f12b4c603`; PR #123 merge `4372fa9067acf6aabf242f178be0d9f7ac041fc7`; initial normalization PR #124 merge `4df1217cde078812af6882b812f640310aa45b61`; documentation hardening head `10150bb3b810f6158029231edb7604b03fdb4ebb`, PR #125 merge `c3eb519d55abb5e6d1007ef4bc96e185df8061c7`; final continuity normalization in progress; manual NONE.
- R9.11 : PLANNED / NOT STARTED.
- R10–R16 : PENDING / NOT STARTED.

## R9 planning acceptance

- Frozen-roadmap title : **ComfyUI + VRAM**.
- Accepted plan head `fc73a3c96cecb78820f9e94738ace2c280dc4251`; R0 #1103 / `32623437662`, Python #1077 / `32623437659`, UI #1044 / `32623437660`, all SUCCESS; PR #103 merge `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`.
- Planning normalization head `51a6bb7d04d8aacd47e621b15a747f6e9d08781c`; R0 #1106 / `32623679409`, Python #1080 / `32623679387`, UI #1047 / `32623679382`, all SUCCESS; PR #104 merge `e3f7bf6039cee918a5d505fb47ed536cde087e0e`.
- Frozen manual states : R9.1 NONE; R9.2 CONDITIONAL; R9.3 NONE; R9.4 NONE; R9.5 CONDITIONAL; R9.6 NONE; R9.7 NONE; R9.8 REQUIRED; R9.9 CONDITIONAL; R9.10 NONE; R9.11 CONDITIONAL.

## R9 accepted structure and evidence

| ID | Title | Accepted evidence | Manual final |
| --- | --- | --- | --- |
| R9.1 | ComfyUI contracts, local endpoint boundary + capability schema | final `cb746fbfe1f318a5b05d4a6e35f1b8afb2338b58`; R0 #1109; Python #1083; UI #1050 | NONE |
| R9.2 | Typed HTTP/WebSocket client, health, queue/history + protocol state | final `89ea9d90ffab6db3563164e629f192caca91ed79`; R0 #1117; Python #1091; UI #1058 | CONDITIONAL NOT TRIGGERED |
| R9.3 | Node/model inventory + capability snapshots | final `97e47799f6efe30eed58d73abf509d9d34ed862d`; R0 #1127; Python #1101; UI #1068 | NONE |
| R9.4 | Validated workflow catalog + governed model resolver | final `45c2fbd3125d654cbac843e1f90133d81da12395`; R0 #1134; Python #1108; UI #1075 | NONE |
| R9.5 | Execution engine, queue/progress/reconciliation + run manifests | final `ee927d50e2af9045dc80c3183aa122b1f87a30c3`; R0 #1144; Python #1118; UI #1085 | CONDITIONAL NOT TRIGGERED |
| R9.6 | Generated-output capture + R8 Vault/AssetPipeline lineage bridge | final `ccc2d5f440322c433a9853e9642bff7efb5d0d0e`; R0 #1150; Python #1124; UI #1091 | NONE |
| R9.7 | Cancellation, interruption, crash recovery + free-memory semantics | final `c38a6c3d9a8e60acdc6fc46e38f46f1402ccb696`; R0 #1156; Python #1130; UI #1097 | NONE |
| R9.8 | VRAM telemetry, admission scheduler + Ollama coexistence | impl `86777ddc7a87ad6041ddc599e20e93af38512a19`; docs `935c977926a11a7ba93f77c49a20b0eebe568b6d`; normalization `586097a25d6027b2c7a86d44c8876a6728cbf2d6` | REQUIRED SATISFIED |
| R9.9 | Production 2D/UI/texture/concept workflow packs | impl `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324`; docs `deb796991d3758c748c7777bd11cdf0c8cc40c4d`; normalization `95f9b21a3a542eea7cb339434397dc4f65429b52`; PR #122 merge `5831e958c45ac63f6d2bcfd7da0a7934330c7586` | CONDITIONAL NOT TRIGGERED |
| R9.10 | CLI + KodeStudio ComfyUI/VRAM UX | impl `dda09a1728ba63640f68a979af57d70f12b4c603`; initial normalization `7515b2bdec0d9eaec32820feb4563869f050be00`; docs hardening `10150bb3b810f6158029231edb7604b03fdb4ebb`; PR #125 merge `c3eb519d55abb5e6d1007ef4bc96e185df8061c7`; final normalization in progress | NONE |
| R9.11 | Adversarial hardening + R9 integrated acceptance | — | CONDITIONAL |

### R9.8 retained local evidence

- Canonical evidence digest `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, 5744 bytes.
- Loopback ComfyUI `0.33.0`; device `cuda:0 AMD Radeon RX 6750 XT : native`; total VRAM `12868124672`, admission-time free `12461146112` bytes.
- Resource profile estimate `8589934592`, reserve `536870912`, headroom `536870912`; scheduler `admit`.
- Real workflow `wf_3aa2ac5225d8a3d88bcf8b3b7aee7205`; output SHA-256 `a18b2eae0fd90f36382e92638bef7984cd591cfd8d9d2466941f66e65f488e92`; OOM false.
- `/free` acknowledgement was followed by remeasurement; `reclaimed_bytes` stays null. Ollama coexistence = `n/a`; nothing was downloaded/loaded solely for acceptance.
- Final docs head `935c977926a11a7ba93f77c49a20b0eebe568b6d`: R0 #1181, Python #1155, UI #1122; PR #119 merge `647039ad4cb6a0fa0c369ba5eeb97c153b561637`.
- Normalization head `586097a25d6027b2c7a86d44c8876a6728cbf2d6`: R0 #1183 / `32643425656`, Python #1157 / `32643425619`, UI #1124 / `32643425675`; PR #120 merge `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`.

### R9.9 accepted baseline

- Base normalized R9.8 `main` : `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`.
- Rejected first candidate `a8913dd1c46730babec7ac123e65de4bb6c8ca52`: Python Core #1159 found two newly introduced R9.9 defects. Gates were not weakened.
- Accepted implementation head `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324`: R0 #1188 / `32644669495`, Python #1162 / `32644669572` 5/5, UI #1129 / `32644669558`; Ubuntu `724 passed / 6 skipped / 46 warnings`; all SUCCESS.
- Four mandatory governed families : `concept`, `ui_illustration`, `material_source`, `sprite_2d`.
- Core-node definitions only; explicit resolver-driven checkpoint selection; typed/bounded prompt, negative prompt, seed, steps, cfg, width, height and output count; aggregate pixel/VRAM budgets explicit.
- No arbitrary graph execution, custom-node/model installer, model download, process or URL surface. Missing/ambiguous models remain `BLOCKED`.
- `material_source` is explicitly source-only and cannot claim validated production-ready PBR semantics.
- Manual CONDITIONAL NOT TRIGGERED because no mandatory new real node/model family was introduced beyond the accepted R9.8 core checkpoint path.
- Final synchronized docs/continuity head `deb796991d3758c748c7777bd11cdf0c8cc40c4d`: R0 #1190 / `32645671691`, Python #1164 / `32645671704` 5/5, UI #1131 / `32645671680`; all SUCCESS.
- PR #121 merged as `3c4d98177e887dad5adbff2f29f7c985c7929015`.
- Post-merge normalization head `95f9b21a3a542eea7cb339434397dc4f65429b52`: R0 #1192 / `32645877353`, Python Core #1166 / `32645877369`, UI Smoke #1133 / `32645877346`; all SUCCESS.
- PR #122 merged as `5831e958c45ac63f6d2bcfd7da0a7934330c7586`.

### R9.10 accepted baseline

- Base normalized R9.9 `main` : `5831e958c45ac63f6d2bcfd7da0a7934330c7586`.
- Rejected candidate `d62a688092ceec9a90b4d78fb4e8feac8fddd24e`: R0 passed, but UI Smoke and the Python Core embedded KodeStudio UI job exposed newly introduced accessibility-contract registrations plus stale pseudo-locale navigation expectations. Service/CLI Python jobs and package builds remained green; gates were not weakened.
- Rejected candidate `4394401510e34f3050040ebedd8799b91e3c0f51`: UI Smoke reduced the remaining defect to the unregistered `comfyEvidenceView` accessibility control. The gate was extended to include the dedicated R9.10 KodeStudio smoke and was not weakened.
- Accepted implementation head `dda09a1728ba63640f68a979af57d70f12b4c603`: R0 #1199 / `32657273588`, Python Core #1173 / `32657273603` 5/5, UI Smoke #1140 / `32657273614`; Ubuntu `729 passed / 7 skipped / 46 warnings`; all SUCCESS.
- `ComfyService` is the single governed R9 façade shared by CLI and KodeStudio; worker `fork()` avoids shared transport state across GUI workers.
- CLI exposes bounded `status`, `inventory`, `workflows`, `validate`, `run`, `run-status`, `cancel`, `vram`, `free-memory`, and `evidence` operations over the fixed accepted loopback boundary.
- KodeStudio exposes protocol/capability, governed workflow parameters, explicit model-resolution state, live run/progress, targeted cancel/free-memory/evidence, VRAM telemetry/admission and Ollama coexistence through non-blocking workers.
- No arbitrary endpoint/URL, graph execution, process surface, custom-node/model installer or model download was introduced. KodeStudio has no direct ComfyUI client/transport path.
- Accessibility and pseudo-localization were extended; the KodeStudio UI Smoke explicitly includes the R9.10 panel smoke.
- Manual state is **NONE**; no user-side acceptance is required for R9.10.
- PR #123 merged as `4372fa9067acf6aabf242f178be0d9f7ac041fc7`.
- Initial post-merge normalization head `7515b2bdec0d9eaec32820feb4563869f050be00`: R0 #1201 / `32657536700`, Python Core #1175 / `32657536745`, UI Smoke #1142 / `32657536723`; all SUCCESS. PR #124 merged as `4df1217cde078812af6882b812f640310aa45b61`.
- R9.11 preparation then correctly found that the frozen R9.10 deliverables `R9_10_DESIGN.md` and `R9_10_ACCEPTANCE.md` were absent. R9.11 was stopped rather than manufacturing integrated evidence.
- Documentation hardening head `10150bb3b810f6158029231edb7604b03fdb4ebb` added only those two missing records. Exact-head gates: R0 #1203 / `32657855298`, Python Core #1177 / `32657855302` 5/5 with Ubuntu `729 passed / 7 skipped / 46 warnings`, UI Smoke #1144 / `32657855311`; all SUCCESS.
- PR #125 merged as `c3eb519d55abb5e6d1007ef4bc96e185df8061c7`. Final continuity-only normalization is in progress on `r9/10-documentation-hardening-normalization` before R9.11 may begin.

## R8 retained source of truth

R8 remains COMPLETE and its integrated report remains `status=pass`, `blockers=[]`, `source_sha=d1589cf94545b854f995e7b6706c4b67e9b7ac1a`, digest `6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`. R8.5/R8.8 conditionals remain NOT TRIGGERED; R8.9 REQUIRED remains SATISFIED with local Godot evidence SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`; R8.11 accepted implementation head `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`; final R8 normalization PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.

## R7 retained source of truth

R7 remains COMPLETE; integrated report `status=pass`, `blockers=[]`, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`. R7.7 REQUIRED remains SATISFIED; accepted head `04cef94c82fdacafe7313d27c8cf516e8e765295`; FFmpeg digest `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`; whisper.cpp `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`; STT model `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`. Final R7 normalization head `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; PR #82 established R8 planning branch point `b98832b339902527bce8a5ea95b5a08a19839a40`.

## Permanent architecture/security boundaries

Preserve without reinterpretation :

- `WorkspaceBoundary`; Vault confinement may compose but never weaken it.
- `ProcessSandbox` + global KillSwitch for external executables.
- Guardian + `PermissionSet` for governed actions.
- Structured tool APIs only; no model-supplied arbitrary executable, argv, cwd, environment, host, refspec, Git config key, URL route or filesystem escape.
- SafeChange / Backup / Recovery / Audit for durable/risky mutations.
- OS-backed Secrets + redaction; secrets never enter manifests/search/evidence.
- Health / Budget / DataGovernance / Privacy / AppSecurity / License-BOM remain in force.
- Exact-head acceptance; missing evidence never manufactures PASS.
- Explicit UNKNOWN / N/A / UNAVAILABLE / BLOCKED / STALE / MISSING / CORRUPT semantics where applicable.
- External metadata/research remains data/evidence, never agent instruction; R7 ResearchGuard remains authoritative.
- ADR required for any frozen-foundation change.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Non-trivial Git/repository/software-engineering tasks must not route to Granite.

## Permanent phase-start / maintenance rule

1. Exhaustive phase plan is merged before the first subdivision.
2. Subdivision structure/manual states are not silently reinterpreted.
3. Implementation acceptance is exact-head and requires documented gates.
4. Continuity is synchronized with accepted evidence before the next subdivision starts.
5. Scope/structure changes synchronize plan + continuity in the same work cycle.
6. Foundation changes require an ADR.

## Next action

**R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1–R9.9 COMPLETE + NORMALIZED. R9.10 COMPLETE; documentation hardening merged, final continuity normalization in progress.** Faire passer R0 Repository Guard, full Python Core et KodeStudio UI Smoke sur le head exact de `r9/10-documentation-hardening-normalization`, puis fusionner cette normalisation. **R9.11 reste interdit avant cette fusion.** Après merge, démarrer R9.11 sur une branche dédiée depuis le nouveau `main`; appliquer l’adversarial hardening et l’acceptance intégrée R9 suivant `R9_PLAN.md`, avec manual **CONDITIONAL** uniquement si les critères de déclenchement documentés sont réellement atteints.
