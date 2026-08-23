# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R9 COMPLETE + NORMALIZED. R10 planning ACCEPTED + NORMALIZED. R10.1–R10.4 COMPLETE + NORMALIZED. R10.5 implementation + final documented acceptance ACCEPTED and merged; post-merge continuity normalization is the only remaining R10.5 completion condition.** `docs/roadmap/R10_PLAN.md` is the exhaustive authority for R10.1–R10.12. R10.5 immutable implementation head `9b8ba987fc3ba6cc37b342d345c2af83f6802e20` passed R0 #1242 / `32666866880`, Python Core #1216 / `32666866872`, UI Smoke #1183 / `32666866877`; Ubuntu reported **788 passed / 7 skipped / 46 warnings** with R7/R8/R9 integrated acceptance PASS. Final documented head `589c370b0ea60a12f9e40fa858c3c0ac03ae0900` passed R0 #1243 / `32666978837`, Python Core #1217 / `32666978847`, UI Smoke #1184 / `32666978771`. Manual state **NONE**. PR #139 merged as `fda94ca7850a5704f05a83642f93c164945fa7a0`. The current branch `r10/5-continuity-normalization` changes continuity only. If its exact head passes R0 + full Python Core + UI Smoke and merges, **R10.5 becomes COMPLETE + NORMALIZED and R10.6 is authorized.** R10.6 manual state is CONDITIONAL.

## Source de vérité / état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque merge accepté et sa normalisation requise.
- R1–R6 : COMPLETE.
- R7 : COMPLETE.
- R8 : COMPLETE.
- R9 : **COMPLETE + NORMALIZED**.
- R10 planning : **ACCEPTED + NORMALIZED**.
- R10.1 : **COMPLETE + NORMALIZED** — manual NONE.
- R10.2 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED.
- R10.3 : **COMPLETE + NORMALIZED** — manual NONE.
- R10.4 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R10.5 : implementation ACCEPTED + final docs ACCEPTED + PR #139 MERGED — manual NONE — post-merge normalization pending.
- R10.6 : PLANNED — manual CONDITIONAL — NOT STARTED until R10.5 normalization merges.
- R10.7 : PLANNED — manual CONDITIONAL.
- R10.8 : PLANNED — manual CONDITIONAL.
- R10.9 : PLANNED — manual NONE.
- R10.10 : PLANNED — manual REQUIRED.
- R10.11 : PLANNED — manual NONE.
- R10.12 : PLANNED — manual CONDITIONAL.
- R11–R16 : PENDING / NOT STARTED.

## Historical acceptance source of truth

Granular R7/R8/R9 evidence, rejected candidates, manual evidence and canonical integrated reports remain authoritative in `docs/roadmap/R7_*`, `R8_*`, `R9_*` and merged PR history. This continuity keeps only the exact closure facts required to resume without manufacturing or reinterpreting evidence.

### R7 retained closure

- Integrated report: `status=pass`, `blockers=[]`, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`.
- R7.7 REQUIRED SATISFIED; accepted local head `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- FFmpeg digest `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`; whisper.cpp `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`; STT model `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- Final R7 normalization head `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; PR #82 established R8 branch point `b98832b339902527bce8a5ea95b5a08a19839a40`.

### R8 retained closure

- Integrated report: `status=pass`, `blockers=[]`, `source_sha=d1589cf94545b854f995e7b6706c4b67e9b7ac1a`, digest `6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`.
- R8.9 REQUIRED SATISFIED with local Godot evidence SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`.
- R8.11 accepted implementation `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`; final normalization PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.

### R9 retained closure

- Frozen title: **ComfyUI + VRAM**; R9.1–R9.11 COMPLETE + NORMALIZED.
- R9.8 REQUIRED SATISFIED; canonical local evidence SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, 5744 bytes; real workflow output SHA-256 `a18b2eae0fd90f36382e92638bef7984cd591cfd8d9d2466941f66e65f488e92`.
- Integrated report `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, `source_sha=e8e7e83c107bdb8bcb29882936720bc9eeb1c246`, digest `19291d79bd800fdb76d96656f9f150ee3114dbcde08d2e82415aff7ff747816a`.
- Final documented R9 head `bcc5eafebf01fddf740c6bee99186ad281285e8d`: R0 #1212 / `32658810381`, Python #1186 / `32658810412`, UI #1153 / `32658810385` SUCCESS; PR #127 merge `6bddb255437b4ef4756f6cbcb6d33ff78c906271`.
- Final normalization `e3d4e396bb062bbc97297572d7c90f640c03cea2`: R0 #1214 / `32658997406`, Python #1188 / `32658997391`, UI #1155 / `32658997367` SUCCESS; PR #128 merge `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`.

## R10 planning baseline

- Frozen-roadmap title: **Blender / 3D**.
- Exhaustive plan: `docs/roadmap/R10_PLAN.md`.
- Scope: governed `bpy/headless`, geometry, UV/PBR, mesh QA, rigs/skinning, animation/retarget, human/animal profiles, LOD, GLB/glTF and Godot 4.7 acceptance.
- Planning head `3bfd6adbff13578f052e8d2bcbd99af3780043ef`: R0 #1216 / `32661485353`, Python #1190 / `32661485175`, UI #1157 / `32661485210` SUCCESS; PR #129 merge `a42282a1329c51f341ad997947222f0d297ad732`.
- Planning normalization `0e9c9fd1ceb4ef1ac8bc852a3a59c2e7a5e752cd`: R0 #1218 / `32661630595`, Python #1192 / `32661630543`, UI #1159 / `32661630557` SUCCESS; PR #130 merge `43eb8cafc73d18a5d31bf47c41890b0dafe8c659`.
- Upstream compatibility baseline: Blender 5.2.x LTS, governed headless `bpy`, GLB/glTF 2.0, Godot 4.7 interoperability through accepted R5 boundaries.
- Frozen manual states: R10.1 NONE; R10.2 REQUIRED; R10.3 NONE; R10.4 CONDITIONAL; R10.5 NONE; R10.6 CONDITIONAL; R10.7 CONDITIONAL; R10.8 CONDITIONAL; R10.9 NONE; R10.10 REQUIRED; R10.11 NONE; R10.12 CONDITIONAL.

## R10.1 closure — contracts/runtime boundary

- Base `43eb8cafc73d18a5d31bf47c41890b0dafe8c659`.
- Implementation `f8d629ca0109037863bd7dd5d109f11cd72a196e`: R0 #1220 / `32662214432`, Python #1194 / `32662214437`, UI #1161 / `32662214438` SUCCESS.
- Final docs `41382cc42d6f6ce400ec20da4aa6b791a041b049`: R0 #1221 / `32662337000`, Python #1195 / `32662336983`, UI #1162 / `32662336981` SUCCESS.
- Manual NONE; PR #131 merge `b246bf1fab3d06ade534fa1f61412154027921e0`.
- Normalization `ab25a5e74c2bd4a4f4e4be2f917c3d4f5e05c0e5`: R0 #1223 / `32662515164`, Python #1197 / `32662515183`, UI #1164 / `32662515217` SUCCESS; PR #132 merge `1ceb7b3528ca09943a542da2a1b0c0f86174ae10`.

## R10.2 closure — real headless Blender

- Base `1ceb7b3528ca09943a542da2a1b0c0f86174ae10`.
- Hosted implementation `b107c565e0df628eb3308543acd998f94b0b6942`: R0 #1225 / `32662882198`, Python #1199 / `32662882146`, UI #1166 / `32662882152` SUCCESS.
- Manual candidate `0a2da2334cc6ebe116819110ba80ad1729e22057`: R0 #1226 / `32663068270`, Python #1200 / `32663068251`, UI #1167 / `32663068243` SUCCESS.
- Manual **REQUIRED SATISFIED** with Blender 5.2.0 LTS / Windows AMD64.
- Canonical evidence `docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json`: SHA-256 `3b65790c4f553640f6d3c14bc141940bca73695a911a343a4ad78449445f243a`, 1141 bytes, `status=pass`, `blockers=[]`; background=true; online_access=false; glTF exporter=true; bmesh=true; no timeout/cancel/crash/OOM.
- Final docs `7755afacd4e434d8ab50207b24aadd5423b1b7bf`: R0 #1227 / `32664160175`, Python #1201 / `32664160218`, UI #1168 / `32664160163` SUCCESS; PR #133 merge `28c5cda03f0ff291b9b9dd6a6d95a21b6b7d2545`.
- Normalization `c8647e7ae65e109590268bfb4d215064bd7eb46a`: R0 #1229 / `32664367853`, Python #1203 / `32664367848`, UI #1170 / `32664367863` SUCCESS; PR #134 merge `397749b6d1ea7b0d904446ebfef2e6b6c22780ce`.

## R10.3 closure — governed geometry authoring

- Base `397749b6d1ea7b0d904446ebfef2e6b6c22780ce`.
- Implementation `5a3042ae4d7214fb8cfe5d2790eae229563d9fc6`: R0 #1231 / `32664784120`, Python #1205 / `32664784136`, UI #1172 / `32664784085` SUCCESS; Ubuntu 772 passed / 7 skipped / 46 warnings; R7/R8/R9 PASS.
- Final docs `da215a245ea45cd470fbedf16202c64ceedb1db0`: R0 #1232 / `32664886435`, Python #1206 / `32664886275`, UI #1173 / `32664886288` SUCCESS.
- Manual NONE; PR #135 merge `71964f1d4aa54428050f2c57ff0c9c3e50a4abd8`.
- Normalization `633f6bd5181f1a7ee4dd74390005c39974fe1c55`: R0 #1234 / `32665113032`, Python #1208 / `32665113118`, UI #1175 / `32665113054` SUCCESS; PR #136 merge `96d690d3283db5e0190c13acdcc043b182d04d63`.

## R10.4 closure — governed UV/PBR

- Base `96d690d3283db5e0190c13acdcc043b182d04d63`.
- Rejected candidate `d4e8eddb7fb8dd158777fdd37668a737677f7f5b`: Python #1210 exposed an over-broad substring security test on legitimate `input_socket`; production networking absent; test hardened with AST import inspection, not weakened.
- Accepted implementation `edc67ae12f8e15051b91af48d20a5bd2ef2a9629`: R0 #1237 / `32665514493`, Python #1211 / `32665514469`, UI #1178 / `32665514503` SUCCESS; Ubuntu 778 passed / 7 skipped / 46 warnings; R7/R8/R9 PASS.
- Final docs `db984125af9964df698739fffe84c227a6eaa1a6`: R0 #1238 / `32665608941`, Python #1212 / `32665609020`, UI #1179 / `32665608911` SUCCESS.
- Manual **CONDITIONAL NOT TRIGGERED**: no bake implemented/claimed; R10.2 real-runtime evidence remains baseline.
- PR #137 merge `b44a0d6b618e26742c1704f9bf0ad8d262880601`.
- Normalization `c5b97ea79b8109c23c68d28efadeea216570da73`: R0 #1240 / `32665808278`, Python #1214 / `32665808252`, UI #1181 / `32665808254` SUCCESS; PR #138 merge `ee9017c2d552105425959841b893ed816593fe77`.
- Therefore R10.4 **COMPLETE + NORMALIZED**.

## R10.5 accepted implementation and merge — mesh QA

- Base normalized R10.4 `ee9017c2d552105425959841b893ed816593fe77`.
- Branch `r10/5-mesh-qa`; PR #139.
- Immutable accepted implementation head `9b8ba987fc3ba6cc37b342d345c2af83f6802e20`.
- Implementation gates: R0 #1242 / `32666866880` SUCCESS; Python #1216 / `32666866872` SUCCESS; UI #1183 / `32666866877` SUCCESS.
- Python Ubuntu: **788 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS.
- Final documented head `589c370b0ea60a12f9e40fa858c3c0ac03ae0900`.
- Final exact-head gates: R0 #1243 / `32666978837` SUCCESS; Python #1217 / `32666978847` SUCCESS; UI #1184 / `32666978771` SUCCESS.
- Manual **NONE**.
- Accepted scope: canonical profile/budgets; asset-class-aware boundary policy; read-only source + evaluated mesh facts; BMesh degenerate/loose/boundary/non-manifold/winding checks; finite coordinates; duplicate indicators; UV layer/zero-area facts; transform sanity; material/texture/shape-key/evaluated-triangle budgets; tangent-space normal-map validation; deterministic `PASS/WARN/BLOCK`; canonical report digest; fail-closed requested overlap semantics; staging input rehash; no derived `.blend` and no implicit repair.
- `MeshRepairRecipe` v1 is a typed request contract only and allows `recalculate_normals`; R10.5 validator executes no repair and claims no derivative without governed lineage and revalidation.
- PR #139 merged as `fda94ca7850a5704f05a83642f93c164945fa7a0`.
- Current branch `r10/5-continuity-normalization` changes this continuity file only.

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

## R10.5 normalization rule / next action

The current branch `r10/5-continuity-normalization` is the **single post-merge continuity normalization** after accepted R10.5 PR #139. Freeze its exact commit after this update. Require R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact SHA, with R7/R8/R9 integrated acceptance still PASS.

If all three gates succeed, merge the normalization PR into `main`. **The act of merging that exact validated continuity-only normalization makes R10.5 COMPLETE + NORMALIZED and authorizes R10.6.** Do not create another recursive R10.5 continuity commit solely to record the normalization's own run IDs; record those exact-head IDs in the normalization PR body/merge record.

R10.6 must start from the resulting normalized `main`. Its frozen manual state is **CONDITIONAL**. Prefer deterministic hosted fixtures for rig hierarchy/weight semantics. Trigger a bounded local Blender 5.2 acceptance only if runtime-specific skinning behavior differs from those deterministic fixtures or cannot be authoritatively validated through already accepted runtime evidence. If triggered, stop before R10.7 and provide exact local command/evidence requirements; never use manual weight painting as acceptance evidence.
