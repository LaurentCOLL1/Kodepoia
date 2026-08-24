# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R9 COMPLETE + NORMALIZED. R10 planning ACCEPTED + NORMALIZED. R10.1–R10.10 COMPLETE + NORMALIZED. R10.11 CLI + KodeStudio Blender/3D UX is ACCEPTED + merged; its single post-merge continuity normalization is the only remaining R10.11 completion condition.** `docs/roadmap/R10_PLAN.md` remains the exhaustive authority for R10.1–R10.12. R10.10 normalization head `02f8bd922662869390038a44327f3519fcebaf39` passed R0 #1321 / `32710626638`, Python #1295 / `32710626649`, UI #1262 / `32710626665`, all SUCCESS, and PR #150 merged as `0bb957b4401026af265ab42e0eb296a9e8615001`, making R10.10 COMPLETE + NORMALIZED and authorizing R10.11. R10.11 historical candidate `e8b1b12a8c199dfcd1829a6d206567ed7be9c324` passed R0 #1323 / `32713096826` but Python #1297 / `32713096801` and UI #1264 / `32713096799` failed only because the historical R6.6 pseudo-locale regression still expected 8 navigation entries after the intentional ninth Blender / 3D page was added. Corrective exact candidate `a75813ac6ab11b7e9e87bf99784bf00696aaef41` changed only that expected navigation count to 9, preserved the pseudo-localization/truncation assertions and dedicated R10.11 Blender page coverage, then passed R0 #1324 / `32713740897`, Python #1298 / `32713740901`, UI #1265 / `32713740869`, all SUCCESS with R7/R8/R9 integrated acceptance PASS. PR #151 merged as `56daf7db7d493f1f89d722bf46f95afa2f9aad24`. Current branch `r10/11-continuity-normalization` changes continuity only. If its exact head passes R0 + full Python Core + UI Smoke and merges, **R10.11 becomes COMPLETE + NORMALIZED and R10.12 is authorized.** R10.12 frozen manual state is CONDITIONAL.

## Source de vérité / état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque merge accepté et normalisation requise.
- R1–R9 : **COMPLETE + NORMALIZED**.
- R10 planning : **ACCEPTED + NORMALIZED**.
- R10.1 : **COMPLETE + NORMALIZED** — manual NONE.
- R10.2 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED.
- R10.3 : **COMPLETE + NORMALIZED** — manual NONE.
- R10.4 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R10.5 : **COMPLETE + NORMALIZED** — manual NONE.
- R10.6 : **COMPLETE + NORMALIZED** — manual CONDITIONAL TRIGGERED AND SATISFIED.
- R10.7 : **COMPLETE + NORMALIZED** — manual CONDITIONAL TRIGGERED AND SATISFIED.
- R10.8 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R10.9 : **COMPLETE + NORMALIZED** — manual NONE.
- R10.10 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED.
- R10.11 : implementation/final exact-head acceptance ACCEPTED + PR #151 MERGED — manual NONE — post-merge normalization pending.
- R10.12 : PLANNED — manual CONDITIONAL; NOT STARTED until R10.11 normalization merges.
- R11–R16 : PENDING / NOT STARTED.

## Historical acceptance source of truth

Detailed evidence, rejected candidates, canonical JSON reports and exact acceptance narratives remain authoritative in `docs/roadmap/R7_*`, `R8_*`, `R9_*`, `R10_*` and merged PR history. This continuity retains the exact closure facts required to resume without manufacturing or reinterpreting evidence.

### R7 retained closure

- Integrated report `status=pass`, `blockers=[]`, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`.
- R7.7 REQUIRED SATISFIED; accepted local head `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- Final R7 normalization head `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; PR #82 established R8 branch point `b98832b339902527bce8a5ea95b5a08a19839a40`.

### R8 retained closure

- Integrated report `status=pass`, `blockers=[]`, source SHA `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`, digest `6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`.
- R8.9 REQUIRED SATISFIED; local Godot evidence SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`.
- Final normalization PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.

### R9 retained closure

- R9.1–R9.11 COMPLETE + NORMALIZED.
- R9.8 REQUIRED SATISFIED; canonical local evidence SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, 5744 bytes.
- Integrated report `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, digest `19291d79bd800fdb76d96656f9f150ee3114dbcde08d2e82415aff7ff747816a`.
- Final normalization head `e3d4e396bb062bbc97297572d7c90f640c03cea2`: R0 #1214 / `32658997406`, Python #1188 / `32658997391`, UI #1155 / `32658997367` SUCCESS; PR #128 merge `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`.

## R10 planning baseline

- Frozen title: **Blender / 3D**.
- Exhaustive plan: `docs/roadmap/R10_PLAN.md`.
- Scope: governed `bpy/headless`, geometry, UV/PBR, mesh QA, rigs/skinning, animation/retarget, human/animal profiles, LOD, GLB/glTF and Godot 4.7 acceptance.
- Planning head `3bfd6adbff13578f052e8d2bcbd99af3780043ef`: R0 #1216 / `32661485353`, Python #1190 / `32661485175`, UI #1157 / `32661485210` SUCCESS; PR #129 merge `a42282a1329c51f341ad997947222f0d297ad732`.
- Planning normalization `0e9c9fd1ceb4ef1ac8bc852a3a59c2e7a5e752cd`: R0 #1218 / `32661630595`, Python #1192 / `32661630543`, UI #1159 / `32661630557` SUCCESS; PR #130 merge `43eb8cafc73d18a5d31bf47c41890b0dafe8c659`.
- Frozen manual states: R10.1 NONE; R10.2 REQUIRED; R10.3 NONE; R10.4 CONDITIONAL; R10.5 NONE; R10.6 CONDITIONAL; R10.7 CONDITIONAL; R10.8 CONDITIONAL; R10.9 NONE; R10.10 REQUIRED; R10.11 NONE; R10.12 CONDITIONAL.

## R10.1 closure — contracts/runtime boundary

- Implementation `f8d629ca0109037863bd7dd5d109f11cd72a196e`: R0 #1220 / `32662214432`, Python #1194 / `32662214437`, UI #1161 / `32662214438` SUCCESS.
- Final docs `41382cc42d6f6ce400ec20da4aa6b791a041b049`: R0 #1221 / `32662337000`, Python #1195 / `32662336983`, UI #1162 / `32662336981` SUCCESS.
- Manual NONE; PR #131 merge `b246bf1fab3d06ade534fa1f61412154027921e0`.
- Normalization `ab25a5e74c2bd4a4f4e4be2f917c3d4f5e05c0e5`: R0 #1223 / `32662515164`, Python #1197 / `32662515183`, UI #1164 / `32662515217` SUCCESS; PR #132 merge `1ceb7b3528ca09943a542da2a1b0c0f86174ae10`.

## R10.2 closure — real headless Blender

- Hosted implementation `b107c565e0df628eb3308543acd998f94b0b6942`: R0 #1225 / `32662882198`, Python #1199 / `32662882146`, UI #1166 / `32662882152` SUCCESS.
- Manual REQUIRED SATISFIED with Blender 5.2.0 LTS / Windows AMD64.
- Canonical evidence `docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json`: SHA-256 `3b65790c4f553640f6d3c14bc141940bca73695a911a343a4ad78449445f243a`, 1141 bytes, `status=pass`, `blockers=[]`.
- Final docs `7755afacd4e434d8ab50207b24aadd5423b1b7bf`: R0 #1227 / `32664160175`, Python #1201 / `32664160218`, UI #1168 / `32664160163` SUCCESS; PR #133 merge `28c5cda03f0ff291b9b9dd6a6d95a21b6b7d2545`.
- Normalization `c8647e7ae65e109590268bfb4d215064bd7eb46a`: R0 #1229 / `32664367853`, Python #1203 / `32664367848`, UI #1170 / `32664367863` SUCCESS; PR #134 merge `397749b6d1ea7b0d904446ebfef2e6b6c22780ce`.

## R10.3 closure — governed geometry authoring

- Implementation `5a3042ae4d7214fb8cfe5d2790eae229563d9fc6`: R0 #1231 / `32664784120`, Python #1205 / `32664784136`, UI #1172 / `32664784085` SUCCESS.
- Final docs `da215a245ea45cd470fbedf16202c64ceedb1db0`: R0 #1232 / `32664886435`, Python #1206 / `32664886275`, UI #1173 / `32664886288` SUCCESS.
- Manual NONE; PR #135 merge `71964f1d4aa54428050f2c57ff0c9c3e50a4abd8`.
- Normalization `633f6bd5181f1a7ee4dd74390005c39974fe1c55`: R0 #1234 / `32665113032`, Python #1208 / `32665113118`, UI #1175 / `32665113054` SUCCESS; PR #136 merge `96d690d3283db5e0190c13acdcc043b182d04d63`.

## R10.4 closure — governed UV/PBR

- Rejected candidate `d4e8eddb7fb8dd158777fdd37668a737677f7f5b`: Python #1210 exposed an over-broad security test; test was hardened via AST import inspection, not weakened.
- Accepted implementation `edc67ae12f8e15051b91af48d20a5bd2ef2a9629`: R0 #1237 / `32665514493`, Python #1211 / `32665514469`, UI #1178 / `32665514503` SUCCESS.
- Final docs `db984125af9964df698739fffe84c227a6eaa1a6`: R0 #1238 / `32665608941`, Python #1212 / `32665609020`, UI #1179 / `32665608911` SUCCESS.
- Manual CONDITIONAL NOT TRIGGERED; PR #137 merge `b44a0d6b618e26742c1704f9bf0ad8d262880601`.
- Normalization `c5b97ea79b8109c23c68d28efadeea216570da73`: R0 #1240 / `32665808278`, Python #1214 / `32665808252`, UI #1181 / `32665808254` SUCCESS; PR #138 merge `ee9017c2d552105425959841b893ed816593fe77`.

## R10.5 closure — mesh QA

- Accepted implementation `9b8ba987fc3ba6cc37b342d345c2af83f6802e20`: R0 #1242 / `32666866880`, Python #1216 / `32666866872`, UI #1183 / `32666866877` SUCCESS; Ubuntu **788 passed / 7 skipped / 46 warnings** with R7/R8/R9 PASS.
- Final docs `589c370b0ea60a12f9e40fa858c3c0ac03ae0900`: R0 #1243 / `32666978837`, Python #1217 / `32666978847`, UI #1184 / `32666978771` SUCCESS.
- Manual NONE; PR #139 merge `fda94ca7850a5704f05a83642f93c164945fa7a0`.
- Normalization `029e7faedafad0502373a49bf1fcdd840e777f05`: R0 #1245 / `32667200910`, Python #1219 / `32667200886`, UI #1186 / `32667200899` SUCCESS; PR #140 merge `8974d7ed1893588abf35c99aeff3053b620bffa9`.

## R10.6 closure — armature/skinning

- Base normalized R10.5 `8974d7ed1893588abf35c99aeff3053b620bffa9`; branch `r10/6-armature-skinning`; PR #141.
- Original hosted implementation `4fb687b232eb7ed113991e81038284cb4a806554`: R0 #1247 / `32667542625`, Python #1221 / `32667542562`, UI #1188 / `32667542603` SUCCESS; Ubuntu **799 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS.
- CONDITIONAL was TRIGGERED because hosted CI could not authoritatively execute the real Blender Armature deformation path.
- Hardened collector head `3b1263b92d5a1a8f50e03c188a1f2fa6d4bc2880`: corrected local acceptance runtime/probe mapping, fail-closed Blender 5.2/background/offline checks and strict evidence schema.
- Hardening gates: R0 #1249 / `32668952047`, Python #1223 / `32668952036`, UI #1190 / `32668952071` SUCCESS; Ubuntu **802 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS.
- Corrected local evidence `docs/roadmap/R10_6_LOCAL_ACCEPTANCE.json`: SHA-256 `06153ac976c4568f6b555365e658e725a67898ddc1ecabf49e95e66e02f0fb4a`, source SHA `3b1263b92d5a1a8f50e03c188a1f2fa6d4bc2880`, `status=pass`, `blockers=[]`, Blender 5.2.0, background=true, online_access=false, geometry PASS, rig PASS.
- Final documented head `6065321048513c7eb87292190a7de02a61d031d7`: R0 #1252 / `32669530185`, Python #1226 / `32669530160`, UI #1193 / `32669530163` SUCCESS.
- Manual CONDITIONAL TRIGGERED AND SATISFIED; PR #141 merge `f127b6f7a6edc4821424e59eda7cb164bbe035cd`.
- Normalization `aab487b8b7fee146b55f93e0689c43d7eaf76d3b`: R0 #1254 / `32669719987`, Python #1228 / `32669719959`, UI #1195 / `32669719974` SUCCESS; PR #142 merge `8f268970f54d167a98ca8dcb11ee68fe829003eb`.

## R10.7 closure — animation/NLA/retarget

- Base normalized R10.6 `8f268970f54d167a98ca8dcb11ee68fe829003eb`; branch `r10/7-animation-retarget`; PR #143.
- Rejected candidates `0a49d3ad15c3e263652be5776f28f959562feaef` and `da56b8a20fc7cb5dfa038051305f07f80dafa4d3` remain documented with their local Blender blockers.
- Accepted source candidate `21510878f49815b7bb5551da9672a349c3fd817f`; hosted R0 #1267 / `32683968797`, Python #1241 / `32683968785`, UI #1208 / `32683968838` SUCCESS; Ubuntu **814 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS.
- Canonical local evidence `docs/roadmap/R10_7_LOCAL_ACCEPTANCE.json`: SHA-256 `f2374feadf87ce9c0f3362969aa0f98314842c73f31c2a90b42c9e2ab107a8cf`, evidence digest `3ef6f4b366a3179f36a20ed606fdf25708309ae350df2704176dfee5e3b1f0b7`, `status=pass`, `blockers=[]`, Blender 5.2.0, geometry/source-rig/target-rig/animation PASS.
- Final exact PR head `04808ee7ffbe6cd8c7f44ea5f32760c62e3161bf`: R0 #1286 / `32685828156`, Python #1260 / `32685828157`, UI #1227 / `32685828175` SUCCESS; Ubuntu **814 passed / 7 skipped / 46 warnings**.
- Manual CONDITIONAL TRIGGERED AND SATISFIED; PR #143 merge `c8bf40ec0fcbc24de7b4c63ead056a9dbd57ff77`.
- Normalization `d52c28efc5120594eb88bcb26cc1d00b431cc531`: R0 #1288 / `32686270793`, Python #1262 / `32686270790`, UI #1229 / `32686270786` SUCCESS; PR #144 merge `d485aa092c06128f0bb07093aef564d53aee56a4`.

## R10.8 closure — human/animal profiles

- Base normalized R10.7 `d485aa092c06128f0bb07093aef564d53aee56a4`; branch `r10/8-human-animal-profiles`; PR #145.
- Implementation candidate `77511b8d89c171517e7d492102145689343bc3e5`: governed `humanoid_biped`/`quadruped` profiles, exact R8 `AssetRevision` binding, frozen metre / `-Z` forward / `Y` up basis, stable piece/material/shape-key inventories, semantic zones, exact R10.6/R10.7 rig compatibility and deterministic PASS/WARN/BLOCK QA.
- Candidate gates: R0 #1290 / `32687083713`, Python #1264 / `32687083701`, UI #1231 / `32687083725` SUCCESS; Ubuntu **826 passed / 7 skipped / 46 warnings**.
- Manual CONDITIONAL NOT TRIGGERED: no approved amendment requires a specific production human/animal asset.
- Final documented head `40214211f6cc8783d3aeece84c327dc1f7e3b7db`: R0 #1291 / `32687205676`, Python #1265 / `32687205699`, UI #1232 / `32687205673` SUCCESS; Ubuntu **826 passed / 7 skipped / 46 warnings**.
- PR #145 merge `6d2c195329a4d001d173a41a827fea277087d8b2`.
- Normalization `4cb8d872cea034539ece955d8dd1bff4e3a04eaf`: R0 #1293 / `32689972029`, Python #1267 / `32689972030`, UI #1234 / `32689972024` SUCCESS; PR #146 merge `f2c21350cce9a8dc9e168b35940c566f389fd4b6`.

## R10.9 closure — LOD / preservation / lineage

- Base normalized R10.8 `f2c21350cce9a8dc9e168b35940c566f389fd4b6`; branch `r10/9-lod-lineage`; PR #147.
- Implementation candidate `fa64f49776a29ece4d06cd05f508632129ee863d` adds static/skinned LOD profiles, strictly descending triangle ratios and absolute budgets, a fixed offline Blender `DECIMATE`/`COLLAPSE` bootstrap, post-decimation material/UV/normal/extent/surface-area preservation checks, stricter skin-group/weight/influence checks, fail-closed Shape Key handling and deterministic R8 `lod_variant` revision lineage.
- Source overwrite is forbidden; each accepted tier is a separate derived R8 model revision. No universal non-standard glTF LOD extension is invented.
- Candidate exact-head gates: R0 #1295 / `32690770568`, Python #1269 / `32690770644`, UI #1236 / `32690770565` SUCCESS; Ubuntu **837 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS, Windows Python and Ubuntu/Windows package builds SUCCESS.
- Frozen manual state **NONE**.
- Final documented head `f12b786a10e7e42e7814a96f049daf485ce12692`: R0 #1296 / `32690925110`, Python #1270 / `32690925091`, UI #1237 / `32690925181` SUCCESS; Ubuntu **837 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS, Windows Python and Ubuntu/Windows package builds SUCCESS.
- PR #147 merged as `daa7fd921528301742e19d9fac8d3ed452676b79`.
- Normalization `b73564c9f30dfd16ff980bfe185ca3c9212d8078`: R0 #1298 / `32691227728`, Python #1272 / `32691227808`, UI #1239 / `32691227806` SUCCESS; PR #148 merge `ac6e2cea836ece815d75ef84cfecb99b82bc7e0f`.

## R10.10 accepted implementation and merge — GLB/glTF + Blender/Godot acceptance

- Base normalized R10.9 `ac6e2cea836ece815d75ef84cfecb99b82bc7e0f`; branch `r10/10-gltf-godot-acceptance`; PR #149.
- Initial implementation candidate `1f4f61485016790b854244a5a0a43094b7c98bab`: strict R8-bound GLB/glTF export profile, bounded glTF/GLB validator, fixed Blender export/re-import bootstrap, semantic round-trip checks, R8 `gltf_export` lineage, Godot R5 runtime reuse and one bounded local acceptance command. R0 #1300 / `32692671006`, Python #1274 / `32692671028`, UI #1241 / `32692670992` SUCCESS; Ubuntu **852 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS.
- First documented/manual candidate `64e21eca32be4fc47944962b57f341b7ed2dbf09`: R0 #1301 / `32692800763`, Python #1275 / `32692800872`, UI #1242 / `32692800747` SUCCESS. Its REQUIRED local run was **REJECTED**: exit 2, `status=fail`, 952-byte evidence SHA-256 `37b5be2bdc6d1b93320e0ce453d3612643c4c729ecf304bd021169421c409a58`, evidence digest `17ce1fb01a96fa5ddcc061f48af79c85a747824211e43460f2ab767cb0997f18`; Blender failed before either GLB existed and Godot was correctly not executed.
- Hardening candidate `85e2db277ce1cb467aeb9b056700150bc1d67fa7`: corrected Blender 5.2 Principled BSDF `Metallic` socket usage and switched the rigged fixture to the explicit Blender 5.2 layered Action slot/layer/keyframe-strip/channelbag/F-Curve API. R0 #1302 / `32707671592`, Python #1276 / `32707671595`, UI #1243 / `32707671624` SUCCESS; Ubuntu **853 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS.
- REQUIRED local acceptance on exact `85e2db277ce1cb467aeb9b056700150bc1d67fa7`: **SATISFIED** with Blender `5.2.0 LTS`, Godot `4.7.2.stable.steam.ed1daf0bf`, `status=pass`, `blockers=[]`, evidence digest `1965ad088a721c9774ea536fe908bffa3f8b07a23ac135c22c339f0d778f6627`.
- Canonical accepted evidence `docs/roadmap/R10_10_LOCAL_ACCEPTANCE.json`: **2843 bytes**, SHA-256 `da9680219dfd4e3a44683a547481b6584b9ef186ee364f27dfcfe2c0c5c29c9f`. Blender background=true, online_access=false, process returncode 0. Static GLB: 2832 bytes, SHA-256 `19a8adfbc4c9ac098a676fbdf52143dc5e445b29228830eab67d271341758308`; rigged GLB: 6796 bytes, SHA-256 `84e9f0a7c7638566962160d6b986073b37528d8bf944d8840c1b6f99f138175f`. Rigged glTF has 1 skin, 1 morph target and 1 animation; round-trip preserves `Root`/`Child`, `Smile`, `Wave`; Godot import returncode 0 and semantic smoke `pass_marker=true`.
- Final PR head `c4fdadd4e451a28b9466695a42cefabf60648e4c`: R0 #1319 / `32710039110`, Python #1293 / `32710039167`, UI #1260 / `32710039132` SUCCESS.
- PR #149 squash-merged as `836e78967fcd5dcca92c909098b4232233d12a0f` to collapse documentation-only head churn without changing the accepted tree semantics.
- R10.10 normalization head `02f8bd922662869390038a44327f3519fcebaf39`: R0 #1321 / `32710626638`, Python #1295 / `32710626649`, UI #1262 / `32710626665` SUCCESS; PR #150 merge `0bb957b4401026af265ab42e0eb296a9e8615001` made R10.10 COMPLETE + NORMALIZED and authorized R10.11.

## R10.11 accepted implementation and merge — CLI + KodeStudio Blender/3D UX

- Base normalized R10.10 `0bb957b4401026af265ab42e0eb296a9e8615001`; branch `r10/11-cli-kodestudio-blender-ux`; PR #151.
- Scope: governed shared `BlenderService`; bounded `blender3d` CLI for status/capabilities, inspection, geometry validation, QA, rig/skin, animation/retarget, LOD, GLB/glTF reports and accepted evidence; service-managed IDs only; no raw Python/expression/operator/executable/argv/path/URL/environment passthrough.
- KodeStudio adds the Blender/3D page with `QRunnable` + `QThreadPool`, cooperative cancellation, explicit operation states, runtime/capability visibility, read-only QA/evidence summaries, dedicated localization/pseudo-locale and accessibility registration, plus service/CLI/UI smoke and cancellation tests.
- Historical candidate `e8b1b12a8c199dfcd1829a6d206567ed7be9c324`: R0 #1323 / `32713096826` SUCCESS; Python #1297 / `32713096801` FAILURE and UI #1264 / `32713096799` FAILURE solely because historical R6.6 still asserted exactly 8 main-navigation items after the intentional ninth Blender / 3D entry. Other Python Core jobs were green.
- Corrective candidate `a75813ac6ab11b7e9e87bf99784bf00696aaef41` changed only that historical expected count from 8 to 9; pseudo-localization and truncation assertions remained intact, while dedicated R10.11 tests already verify the Blender page and pseudo-locale registration.
- Final exact-head gates on `a75813ac6ab11b7e9e87bf99784bf00696aaef41`: R0 #1324 / `32713740897`, Python #1298 / `32713740901`, UI #1265 / `32713740869` SUCCESS. Ubuntu/Windows tests, KodeStudio smoke, Ubuntu/Windows package builds and R7/R8/R9 integrated acceptance PASS.
- Frozen manual state **NONE**; no real Blender/Godot run is introduced by R10.11.
- PR #151 merged as `56daf7db7d493f1f89d722bf46f95afa2f9aad24`.
- Current branch `r10/11-continuity-normalization` changes only this continuity file.

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

## R10.11 normalization rule / next action

The current branch `r10/11-continuity-normalization` is the **single post-merge continuity normalization** after accepted R10.11 PR #151. Freeze its exact commit after this update. Require R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact SHA, with R7/R8/R9 integrated acceptance still PASS.

If all three gates succeed, merge the normalization PR into `main`. **The act of merging that exact validated continuity-only normalization makes R10.11 COMPLETE + NORMALIZED and authorizes R10.12.** Do not create another recursive R10.11 continuity commit solely to record the normalization's own run IDs; record those IDs in the normalization PR/merge metadata instead.

R10.12 frozen manual state is **CONDITIONAL**. Do not start R10.12 inside this normalization. Start it only from the resulting normalized `main` and only in a later authorized work cycle.
