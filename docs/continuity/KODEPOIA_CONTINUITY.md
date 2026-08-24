# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R9 COMPLETE + NORMALIZED. R10 planning ACCEPTED + NORMALIZED. R10.1–R10.8 COMPLETE + NORMALIZED. R10.9 LOD generation/preservation/variant-lineage implementation and final exact-head acceptance are ACCEPTED + merged; post-merge continuity normalization is the only remaining R10.9 completion condition.** `docs/roadmap/R10_PLAN.md` remains the exhaustive authority for R10.1–R10.12. R10.9 implementation candidate `fa64f49776a29ece4d06cd05f508632129ee863d` passed R0 #1295 / `32690770568`, Python Core #1269 / `32690770644`, UI Smoke #1236 / `32690770565`; final documented head `f12b786a10e7e42e7814a96f049daf485ce12692` passed R0 #1296 / `32690925110`, Python Core #1270 / `32690925091`, UI Smoke #1237 / `32690925181`, all SUCCESS. Ubuntu reported **837 passed / 7 skipped / 46 warnings** with R7/R8/R9 integrated acceptance PASS; Windows Python and Ubuntu/Windows package builds SUCCESS. Manual state **NONE**. PR #147 merged as `daa7fd921528301742e19d9fac8d3ed452676b79`. Current branch `r10/9-continuity-normalization` changes continuity only. If its exact head passes R0 + full Python Core + UI Smoke and merges, **R10.9 becomes COMPLETE + NORMALIZED and R10.10 is authorized.** R10.10 frozen manual state is REQUIRED; do not proceed beyond its manual acceptance checkpoint until the user supplies the required local Blender 5.2 + Godot 4.7 evidence.

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
- R10.9 : implementation/final exact-head acceptance ACCEPTED + PR #147 MERGED — manual NONE — post-merge normalization pending.
- R10.10 : PLANNED — manual REQUIRED; NOT STARTED until R10.9 normalization merges.
- R10.11 : PLANNED — manual NONE.
- R10.12 : PLANNED — manual CONDITIONAL.
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

## R10.9 accepted implementation and merge — LOD / preservation / lineage

- Base normalized R10.8 `f2c21350cce9a8dc9e168b35940c566f389fd4b6`; branch `r10/9-lod-lineage`; PR #147.
- Implementation candidate `fa64f49776a29ece4d06cd05f508632129ee863d` adds static/skinned LOD profiles, strictly descending triangle ratios and absolute budgets, a fixed offline Blender `DECIMATE`/`COLLAPSE` bootstrap, post-decimation material/UV/normal/extent/surface-area preservation checks, stricter skin-group/weight/influence checks, fail-closed Shape Key handling and deterministic R8 `lod_variant` revision lineage.
- Source overwrite is forbidden; each accepted tier is a separate derived R8 model revision. No universal non-standard glTF LOD extension is invented.
- Candidate exact-head gates: R0 #1295 / `32690770568`, Python #1269 / `32690770644`, UI #1236 / `32690770565` SUCCESS; Ubuntu **837 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS, Windows Python and Ubuntu/Windows package builds SUCCESS.
- Frozen manual state **NONE**.
- Final documented head `f12b786a10e7e42e7814a96f049daf485ce12692`: R0 #1296 / `32690925110`, Python #1270 / `32690925091`, UI #1237 / `32690925181` SUCCESS; Ubuntu **837 passed / 7 skipped / 46 warnings**, R7/R8/R9 PASS, Windows Python and Ubuntu/Windows package builds SUCCESS.
- PR #147 merged as `daa7fd921528301742e19d9fac8d3ed452676b79`.
- Current branch `r10/9-continuity-normalization` changes only this continuity file.

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

## R10.9 normalization rule / next action

The current branch `r10/9-continuity-normalization` is the **single post-merge continuity normalization** after accepted R10.9 PR #147. Freeze its exact commit after this update. Require R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact SHA, with R7/R8/R9 integrated acceptance still PASS.

If all three gates succeed, merge the normalization PR into `main`. **The act of merging that exact validated continuity-only normalization makes R10.9 COMPLETE + NORMALIZED and authorizes R10.10.** Do not create another recursive R10.9 continuity commit solely to record the normalization's own run IDs; record those exact-head IDs in the normalization PR body/merge record.

R10.10 must start from the resulting normalized `main`. Its frozen title is **GLB/glTF export + Blender round-trip + Godot 4.7 acceptance**, its frozen manual state is **REQUIRED**, and it depends on R10.4–R10.9 plus R5/R8. Implement and validate the hosted candidate first, then stop at the required real local Blender 5.2.x + Godot 4.7 acceptance checkpoint and provide the exact bounded command/evidence instructions. Do not continue to R10.11 until that evidence is supplied and reviewed.
