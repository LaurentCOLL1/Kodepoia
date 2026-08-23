# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R9 COMPLETE + NORMALIZED. R10 planning ACCEPTED + NORMALIZED. R10.1–R10.2 COMPLETE + NORMALIZED. R10.3 implementation + final documented acceptance ACCEPTED and merged; post-merge continuity normalization is the only remaining R10.3 completion condition.** `docs/roadmap/R10_PLAN.md` is the exhaustive authority for R10.1–R10.12. R10.3 immutable implementation head `5a3042ae4d7214fb8cfe5d2790eae229563d9fc6` passed R0 #1231 / `32664784120`, Python Core #1205 / `32664784136`, UI Smoke #1172 / `32664784085`; Ubuntu reported 772 passed / 7 skipped / 46 warnings with R7/R8/R9 integrated acceptance PASS. Final documented head `da215a245ea45cd470fbedf16202c64ceedb1db0` passed R0 #1232 / `32664886435`, Python Core #1206 / `32664886275`, UI Smoke #1173 / `32664886288`. Manual state NONE. PR #135 merged as `71964f1d4aa54428050f2c57ff0c9c3e50a4abd8`. The current branch `r10/3-continuity-normalization` changes continuity only. If its exact head passes R0 + full Python Core + UI Smoke and merges, **R10.3 becomes COMPLETE + NORMALIZED and R10.4 is authorized.** R10.4 manual state is CONDITIONAL; it is triggered only if an accepted hosted/CPU validation cannot authoritatively cover a planned bake/backend-specific path.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité after each accepted merge and required normalization.
- R1–R6 : COMPLETE.
- R7 : COMPLETE.
- R8 : COMPLETE.
- R9 planning : ACCEPTED + NORMALIZED.
- R9.1–R9.11 : COMPLETE + NORMALIZED; inherited/required manual gates remain resolved as recorded below.
- R9 phase : **COMPLETE + NORMALIZED**.
- R10 planning : **ACCEPTED + NORMALIZED**.
- R10.1 : **COMPLETE + NORMALIZED**; manual NONE.
- R10.2 : **COMPLETE + NORMALIZED**; manual REQUIRED SATISFIED.
- R10.3 : implementation ACCEPTED; final documented acceptance ACCEPTED; PR #135 MERGED; manual NONE; post-merge continuity normalization pending.
- R10.4 : PLANNED; manual CONDITIONAL; NOT STARTED until R10.3 normalization merges.
- R10.5–R10.12 : PLANNED only; implementation NOT STARTED.
- R11–R16 : PENDING / NOT STARTED.

## R9 planning acceptance

- Frozen-roadmap title : **ComfyUI + VRAM**.
- Accepted plan head `fc73a3c96cecb78820f9e94738ace2c280dc4251`; R0 #1103 / `32623437662`, Python #1077 / `32623437659`, UI #1044 / `32623437660`, all SUCCESS; PR #103 merge `1d5daab6168ee6aceab3de089d8cc46ea7dc2145`.
- Planning normalization head `51a6bb7d04d8aacd47e621b15a747f6e9d08781c`; R0 #1106 / `32623679409`, Python #1080 / `32623679387`, UI #1047 / `32623679382`, all SUCCESS; PR #104 merge `e3f7bf6039cee918a5d505fb47ed536cde087e0e`.
- Frozen manual states : R9.1 NONE; R9.2 CONDITIONAL; R9.3 NONE; R9.4 NONE; R9.5 CONDITIONAL; R9.6 NONE; R9.7 NONE; R9.8 REQUIRED; R9.9 CONDITIONAL; R9.10 NONE; R9.11 CONDITIONAL.

## R9 accepted implementation heads and manual states

| ID | Title | Accepted implementation head | Manual final |
| --- | --- | --- | --- |
| R9.1 | ComfyUI contracts, local endpoint boundary + capability schema | `dfde39746f0ec909a865a9f0ef75b6856e77c88f` | NONE |
| R9.2 | Typed HTTP/WebSocket client, health, queue/history + protocol state | `15186ced206f05d8baf764738615e6625aa6d459` | CONDITIONAL NOT TRIGGERED |
| R9.3 | Node/model inventory + capability snapshots | `915075149fa81b31308c3eedcfa35e74f8a9b7a4` | NONE |
| R9.4 | Validated workflow catalog + governed model resolver | `e158fd643ecf55a1ed9022193a48d2d1ee1716ed` | NONE |
| R9.5 | Execution engine, queue/progress/reconciliation + run manifests | `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112` | CONDITIONAL NOT TRIGGERED |
| R9.6 | Generated-output capture + R8 Vault/AssetPipeline lineage bridge | `f453db0c5ec5705b4dea8ae00a5937583f466fa1` | NONE |
| R9.7 | Cancellation, interruption, crash recovery + free-memory semantics | `20cc4bbc93e547fac9fee28d7be44268358d29e4` | NONE |
| R9.8 | VRAM telemetry, admission scheduler + Ollama coexistence | `86777ddc7a87ad6041ddc599e20e93af38512a19` | REQUIRED SATISFIED |
| R9.9 | Production 2D/UI/texture/concept workflow packs | `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324` | CONDITIONAL NOT TRIGGERED |
| R9.10 | CLI + KodeStudio ComfyUI/VRAM UX | `dda09a1728ba63640f68a979af57d70f12b4c603` | NONE |
| R9.11 | Adversarial hardening + R9 integrated acceptance | `e8e7e83c107bdb8bcb29882936720bc9eeb1c246` | CONDITIONAL NOT TRIGGERED |

## R9.8 retained local evidence

- Canonical local evidence digest `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, **5744 bytes**.
- Accepted R9.8 implementation head `86777ddc7a87ad6041ddc599e20e93af38512a19`.
- Loopback ComfyUI `0.33.0`; device `cuda:0 AMD Radeon RX 6750 XT : native`.
- Total VRAM `12868124672`, admission-time free `12461146112` bytes.
- Resource profile estimate `8589934592`, reserve `536870912`, headroom `536870912`; scheduler `admit`.
- Real workflow `wf_3aa2ac5225d8a3d88bcf8b3b7aee7205`; output SHA-256 `a18b2eae0fd90f36382e92638bef7984cd591cfd8d9d2466941f66e65f488e92`; OOM false.
- `/free` acknowledgement followed by remeasurement; `reclaimed_bytes` remains null.
- Ollama coexistence = `n/a`; no model/custom node was downloaded solely for acceptance.
- Final docs head `935c977926a11a7ba93f77c49a20b0eebe568b6d`: R0 #1181, Python #1155, UI #1122; PR #119 merge `647039ad4cb6a0fa0c369ba5eeb97c153b561637`.
- Normalization head `586097a25d6027b2c7a86d44c8876a6728cbf2d6`: R0 #1183 / `32643425656`, Python #1157 / `32643425619`, UI #1124 / `32643425675`; PR #120 merge `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`.

## R9.9 retained baseline

- Base normalized R9.8 `main`: `bc5d4687e0ef6d91901a8b04103907aad8bb48f8`.
- Rejected candidate `a8913dd1c46730babec7ac123e65de4bb6c8ca52`: Python Core #1159 exposed two newly introduced R9.9 defects; gates were not weakened.
- Accepted implementation `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324`: R0 #1188 / `32644669495`, Python #1162 / `32644669572` 5/5, UI #1129 / `32644669558`; Ubuntu `724 passed / 6 skipped / 46 warnings`.
- Four mandatory families: `concept`, `ui_illustration`, `material_source`, `sprite_2d`; core nodes only; explicit resolver-driven checkpoint selection; bounded typed parameters and aggregate pixel/VRAM budgets.
- No arbitrary graph/custom-node/model installer, model download, process or URL surface. Missing/ambiguous models remain BLOCKED.
- `material_source` is source-only and does not claim production-ready PBR semantics.
- Final synchronized docs head `deb796991d3758c748c7777bd11cdf0c8cc40c4d`: R0 #1190, Python #1164, UI #1131; PR #121 merge `3c4d98177e887dad5adbff2f29f7c985c7929015`.
- Post-merge normalization `95f9b21a3a542eea7cb339434397dc4f65429b52`: R0 #1192 / `32645877353`, Python #1166 / `32645877369`, UI #1133 / `32645877346`; PR #122 merge `5831e958c45ac63f6d2bcfd7da0a7934330c7586`.

## R9.10 retained baseline and recovered documentation defect

- Base normalized R9.9 main `5831e958c45ac63f6d2bcfd7da0a7934330c7586`.
- Rejected `d62a688092ceec9a90b4d78fb4e8feac8fddd24e`: accessibility registration + pseudo-locale regression exposed by UI gates; service/package paths remained green.
- Rejected `4394401510e34f3050040ebedd8799b91e3c0f51`: remaining `comfyEvidenceView` registration defect; UI workflow strengthened to include dedicated R9.10 smoke.
- Accepted implementation `dda09a1728ba63640f68a979af57d70f12b4c603`: R0 #1199 / `32657273588`, Python #1173 / `32657273603`, UI #1140 / `32657273614`; Ubuntu `729 passed / 7 skipped / 46 warnings`.
- `ComfyService` is the single governed façade shared by CLI and KodeStudio; no arbitrary endpoint/URL/graph/process/custom-node/model installer/model download surface.
- PR #123 merge `4372fa9067acf6aabf242f178be0d9f7ac041fc7`.
- Initial continuity normalization `7515b2bdec0d9eaec32820feb4563869f050be00`: R0 #1201 / `32657536700`, Python #1175 / `32657536745`, UI #1142 / `32657536723`; PR #124 merge `4df1217cde078812af6882b812f640310aa45b61`.
- R9.11 preparation found missing planned `R9_10_DESIGN.md` + `R9_10_ACCEPTANCE.md`; R9.11 stopped rather than manufacturing evidence.
- Documentation hardening `10150bb3b810f6158029231edb7604b03fdb4ebb`: R0 #1203 / `32657855298`, Python #1177 / `32657855302`, UI #1144 / `32657855311`; PR #125 merge `c3eb519d55abb5e6d1007ef4bc96e185df8061c7`.
- Final hardening normalization `f1f590ae0b5fa178934b11313d8b546abe6e86c1`: R0 #1205 / `32658034662`, Python #1179 / `32658034624`, UI #1146 / `32658034628`; PR #126 merge `8cd01c5f5d1ae667602d2e13c1d86219d86748cf`.
- R9.10 COMPLETE + NORMALIZED, manual NONE.

## R9.11 accepted implementation, integrated report and final merge

- Base fully normalized R9.10 main: `8cd01c5f5d1ae667602d2e13c1d86219d86748cf`.
- PR #127 branch: `r9/11-adversarial-integrated-acceptance`.
- Accepted immutable implementation head: `e8e7e83c107bdb8bcb29882936720bc9eeb1c246`.
- Implementation gates:
  - R0 #1207 / `32658452681`: SUCCESS.
  - Python #1181 / `32658452650`: SUCCESS 5/5; Ubuntu **745 passed / 7 skipped / 46 warnings**; R7 PASS; R8 PASS; package builds and Windows tests/UI SUCCESS.
  - UI #1148 / `32658452730`: SUCCESS.
- Manual **CONDITIONAL NOT TRIGGERED** because R9.11 changed no authoritative hardware-facing ComfyUI/GPU/node/model/output semantics and inherited manual gates were already resolved.
- R9.11 added R9-specific integrated acceptance contracts/schema, adversarial cross-subsystem seam tests, deterministic Git-blob verifier and anti-circular documentation sequence without modifying frozen R7/R8 integrated reports.
- Canonical report `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, `source_sha=e8e7e83c107bdb8bcb29882936720bc9eeb1c246`, SHA-256 `19291d79bd800fdb76d96656f9f150ee3114dbcde08d2e82415aff7ff747816a`.
- Report binds all R9.1–R9.11 acceptance blobs plus R9.8 reviewed local evidence SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, 5744 bytes.
- Final synchronized documentation/evidence head: `bcc5eafebf01fddf740c6bee99186ad281285e8d`.
- Exact final gates on that head:
  - R0 Repository Guard #1212 / `32658810381`: SUCCESS Ubuntu + Windows.
  - Python Core #1186 / `32658810412`: SUCCESS 5/5; Linux printed `R7 integrated acceptance: PASS`, `R8 integrated acceptance: PASS`, `R9 integrated acceptance: PASS`; Ubuntu **745 passed / 7 skipped / 46 warnings**; package builds Ubuntu+Windows SUCCESS; Windows Python and embedded UI SUCCESS.
  - KodeStudio UI Smoke #1153 / `32658810385`: SUCCESS.
- PR #127 merged as `6bddb255437b4ef4756f6cbcb6d33ff78c906271`.
- This final continuity-normalization branch changes only `docs/continuity/KODEPOIA_CONTINUITY.md`; no canonical R9 acceptance blob/report is modified.

## R9 final continuity normalization closure

- Final normalization branch: `r9/11-final-continuity-normalization`.
- Exact validated normalization head: `e3d4e396bb062bbc97297572d7c90f640c03cea2`.
- Exact-head gates:
  - R0 Repository Guard #1214 / `32658997406`: SUCCESS.
  - Python Core #1188 / `32658997391`: SUCCESS.
  - KodeStudio UI Smoke #1155 / `32658997367`: SUCCESS.
- PR #128 **MERGED**; resulting `main` merge commit `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`.
- The merge commit explicitly records that the exact-head gates succeeded and that the frozen R9 completion condition is satisfied.
- Therefore R9 is **COMPLETE + NORMALIZED** and R10 planning is authorized.
- Per the frozen anti-recursion rule, no extra R9-only continuity commit is required solely to record these run IDs; this R10 planning-cycle synchronization records the closure as historical state.

## R10 planning baseline and closure

- Frozen-roadmap title: **Blender / 3D**.
- Frozen roadmap scope: `bpy/headless`, geometry, UV/PBR, rigs, animation, retarget, humans/animals, LOD, GLTF, and validation of topology/normals/weights/budgets.
- Planning branch: `r10/planning`.
- Planning branch point / normalized R9 `main`: `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`.
- Exhaustive plan file: `docs/roadmap/R10_PLAN.md`.
- Initial plan commit: `24b76dbb24d9e52038e0a594b1dae3bdcedb1346`.
- Accepted exact planning head: `3bfd6adbff13578f052e8d2bcbd99af3780043ef`.
- Planning acceptance gates: R0 #1216 / `32661485353` SUCCESS; Python Core #1190 / `32661485175` SUCCESS; UI #1157 / `32661485210` SUCCESS.
- Planning PR #129 merged as `a42282a1329c51f341ad997947222f0d297ad732`.
- Planning normalization head `0e9c9fd1ceb4ef1ac8bc852a3a59c2e7a5e752cd` passed R0 #1218 / `32661630595`, Python Core #1192 / `32661630543`, UI #1159 / `32661630557`, all SUCCESS; PR #130 merged as `43eb8cafc73d18a5d31bf47c41890b0dafe8c659`.
- Therefore R10 planning is **ACCEPTED + NORMALIZED**.
- Upstream compatibility baseline: Blender 5.2.x LTS, governed headless `bpy`, GLB/glTF 2.0 as primary exchange contract, and Godot 4.7 interoperability through accepted R5 boundaries. External references are compatibility evidence only.
- Frozen subdivision/manual-state structure:
  - R10.1 Blender contracts, runtime discovery + secure process boundary — NONE.
  - R10.2 Headless `bpy` runner, capability probe + real-runtime acceptance — REQUIRED.
  - R10.3 Structured scene/geometry authoring + deterministic transform recipes — NONE.
  - R10.4 UV + PBR material pipeline + governed texture lineage — CONDITIONAL.
  - R10.5 Mesh QA: topology, normals, tangents, UV and production budgets — NONE.
  - R10.6 Armatures, skinning + weight validation — CONDITIONAL.
  - R10.7 Animation actions/NLA + governed retargeting — CONDITIONAL.
  - R10.8 Human + animal profile pipelines — CONDITIONAL.
  - R10.9 LOD generation, preservation checks + variant lineage — NONE.
  - R10.10 GLB/glTF export + Blender round-trip + Godot 4.7 acceptance — REQUIRED.
  - R10.11 CLI + KodeStudio Blender/3D UX — NONE.
  - R10.12 Adversarial hardening + R10 integrated acceptance — CONDITIONAL.

## R10.1 accepted implementation and normalization closure

- Base normalized planning `main`: `43eb8cafc73d18a5d31bf47c41890b0dafe8c659`.
- Branch: `r10/1-blender-contracts-runtime-boundary`; PR #131.
- Accepted immutable implementation head: `f8d629ca0109037863bd7dd5d109f11cd72a196e`.
- Implementation gates: R0 #1220 / `32662214432` SUCCESS; Python Core #1194 / `32662214437` SUCCESS; UI #1161 / `32662214438` SUCCESS.
- Final documented acceptance head: `41382cc42d6f6ce400ec20da4aa6b791a041b049`.
- Final exact-head gates: R0 #1221 / `32662337000` SUCCESS; Python Core #1195 / `32662336983` SUCCESS; UI #1162 / `32662336981` SUCCESS.
- Manual state: **NONE**.
- Accepted scope: Blender 5.2.x runtime policy, immutable contracts/state machine, canonical JSON/SHA-256 identities, finite executable discovery, configured-root confinement, fixed safe argv, environment-injection rejection, five R10 schema roots, adversarial tests, design + acceptance docs.
- PR #131 merged as `b246bf1fab3d06ade534fa1f61412154027921e0`.
- R10.1 normalization head `ab25a5e74c2bd4a4f4e4be2f917c3d4f5e05c0e5` passed R0 #1223 / `32662515164`, Python Core #1197 / `32662515183`, UI #1164 / `32662515217`, all SUCCESS.
- PR #132 merged as `1ceb7b3528ca09943a542da2a1b0c0f86174ae10`, making R10.1 **COMPLETE + NORMALIZED** and authorizing R10.2.

## R10.2 accepted implementation, real-runtime evidence and normalization closure

- Base normalized R10.1 `main`: `1ceb7b3528ca09943a542da2a1b0c0f86174ae10`.
- Branch: `r10/2-headless-bpy-runner`; PR #133.
- Hosted immutable implementation head: `b107c565e0df628eb3308543acd998f94b0b6942`.
- Hosted gates: R0 #1225 / `32662882198` SUCCESS; Python Core #1199 / `32662882146` SUCCESS; UI #1166 / `32662882152` SUCCESS.
- Final manual candidate: `0a2da2334cc6ebe116819110ba80ad1729e22057`; gates R0 #1226 / `32663068270`, Python #1200 / `32663068251`, UI #1167 / `32663068243`, all SUCCESS.
- Manual state: **REQUIRED SATISFIED** with Blender `5.2.0` LTS on Windows AMD64.
- Canonical local evidence: `docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json`; SHA-256 `3b65790c4f553640f6d3c14bc141940bca73695a911a343a4ad78449445f243a`; **1141 bytes**; `status=pass`; `blockers=[]`.
- Probe facts: background true; online access false; glTF exporter true; bmesh true; 1 object / 8 vertices / 6 faces.
- `.blend`: 94,460 bytes / SHA-256 `dbda97a9f3f7dddeb2df92af277502aa21ac119a3ee9f49509dbdf4735389e43`.
- GLB: 1,436 bytes / SHA-256 `47fa0c82eb14f211e33a9f6b5c36d48a60d1619c33632c4cbbd9099c5d70bc1f`.
- Process return code 0; timeout/cancel/crash/OOM all false.
- Final documented evidence head: `7755afacd4e434d8ab50207b24aadd5423b1b7bf`.
- Final exact-head gates: R0 #1227 / `32664160175` SUCCESS; Python Core #1201 / `32664160218` SUCCESS; UI #1168 / `32664160163` SUCCESS.
- PR #133 merged as `28c5cda03f0ff291b9b9dd6a6d95a21b6b7d2545`.
- R10.2 normalization head `c8647e7ae65e109590268bfb4d215064bd7eb46a` passed R0 #1229 / `32664367853`, Python Core #1203 / `32664367848`, UI #1170 / `32664367863`, all SUCCESS.
- PR #134 merged as `397749b6d1ea7b0d904446ebfef2e6b6c22780ce`, making R10.2 **COMPLETE + NORMALIZED** and authorizing R10.3.

## R10.3 accepted implementation and merge

- Base normalized R10.2 `main`: `397749b6d1ea7b0d904446ebfef2e6b6c22780ce`.
- Branch: `r10/3-geometry-authoring`; PR #135.
- Accepted immutable implementation head: `5a3042ae4d7214fb8cfe5d2790eae229563d9fc6`.
- Implementation gates: R0 #1231 / `32664784120` SUCCESS; Python Core #1205 / `32664784136` SUCCESS; UI #1172 / `32664784085` SUCCESS.
- Python Core Ubuntu: **772 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS; package builds Ubuntu/Windows + Windows tests/UI SUCCESS.
- Manual state: **NONE**.
- Accepted scope: canonical geometry recipes, stable machine object IDs, bounded primitive/transform/modifier catalog, BMesh triangulation + normal recalculation, context-governed join/separate/origin operations, source/evaluated topology statistics, staging-only derived `.blend`, recipe-digest binding and hostile/tamper tests.
- Recipe-level arbitrary filesystem paths remain unavailable; direct R8 append is fail-closed until a trusted lineage-backed staged binding exists, preserving source immutability and WorkspaceBoundary.
- Final documented acceptance head: `da215a245ea45cd470fbedf16202c64ceedb1db0`.
- Final exact-head gates: R0 #1232 / `32664886435` SUCCESS; Python Core #1206 / `32664886275` SUCCESS; UI #1173 / `32664886288` SUCCESS.
- PR #135 merged as `71964f1d4aa54428050f2c57ff0c9c3e50a4abd8`.
- Post-merge normalization branch: `r10/3-continuity-normalization`; this branch changes continuity only.

## R8 retained source of truth

R8 remains COMPLETE and its integrated report remains `status=pass`, `blockers=[]`, `source_sha=d1589cf94545b854f995e7b6706c4b67e9b7ac1a`, digest `6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`. R8.5/R8.8 conditionals remain NOT TRIGGERED; R8.9 REQUIRED remains SATISFIED with local Godot evidence SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`; R8.11 accepted implementation head `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`; final R8 normalization PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.

## R7 retained source of truth

R7 remains COMPLETE; integrated report `status=pass`, `blockers=[]`, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`. R7.7 REQUIRED remains SATISFIED; accepted head `04cef94c82fdacafe7313d27c8cf516e8e765295`; FFmpeg digest `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`; whisper.cpp `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`; STT model `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`. Final R7 normalization head `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; PR #82 established R8 planning branch point `b98832b339902527bce8a5ea95b5a08a19839a40`.

## Permanent architecture/security boundaries

Preserve without reinterpretation:

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

## R10.3 normalization rule / next action

The current branch `r10/3-continuity-normalization` is the **single post-merge continuity normalization** after accepted R10.3 PR #135. Freeze its exact commit after this update. Require R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact SHA, with prior R7/R8/R9 integrated acceptance still PASS.

If all three gates succeed, merge the normalization PR into `main`. **The act of merging that exact validated continuity-only normalization makes R10.3 COMPLETE + NORMALIZED and authorizes R10.4.** Do not create another recursive R10.3 continuity commit solely to record the normalization's own run IDs; record those exact-head IDs in the normalization PR body/merge record.

R10.4 must start from the resulting normalized `main`. Its manual state is **CONDITIONAL**. Prefer deterministic hosted/CPU fixtures and do not introduce a bake path merely to exercise the conditional gate. If a planned bake/backend-specific behavior cannot be authoritatively validated without a real local runtime, stop before R10.5 and provide exact local command/evidence requirements. Otherwise record **CONDITIONAL NOT TRIGGERED** and continue normally.
