# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1–R9.10 COMPLETE + NORMALIZED. R9.11 implementation + final integrated documentation ACCEPTED and merged; final continuity normalization is the only remaining R9 completion condition.** `docs/roadmap/R9_PLAN.md` reste l’autorité structurelle exhaustive de R9.1–R9.11. R9.8 REQUIRED reste SATISFIED par l’evidence locale canonique SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967` (5744 octets). R9.11 accepted implementation head = `e8e7e83c107bdb8bcb29882936720bc9eeb1c246`; implementation gates R0 #1207 / `32658452681`, Python #1181 / `32658452650`, UI #1148 / `32658452730`, Ubuntu `745 passed / 7 skipped / 46 warnings`; manual **CONDITIONAL NOT TRIGGERED**. Canonical R9 integrated report: `status=pass`, `blockers=[]`, `source_sha=e8e7e83c107bdb8bcb29882936720bc9eeb1c246`, digest `19291d79bd800fdb76d96656f9f150ee3114dbcde08d2e82415aff7ff747816a`. Final documentation/evidence head `bcc5eafebf01fddf740c6bee99186ad281285e8d` passed R0 #1212 / `32658810381`, Python #1186 / `32658810412` 5/5 with Linux `R7 PASS`, `R8 PASS`, `R9 PASS`, Ubuntu `745 passed / 7 skipped / 46 warnings`, and UI #1153 / `32658810385`; all SUCCESS. PR #127 merged as `6bddb255437b4ef4756f6cbcb6d33ff78c906271`. The current branch `r9/11-final-continuity-normalization` changes continuity only. If its exact head passes R0 + full Python Core + UI Smoke and its PR is merged into `main`, then by the frozen phase-completion rule **R9 is COMPLETE + NORMALIZED** and R10 planning becomes authorized. No extra manual R9 intervention is required.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité after each accepted merge and required normalization.
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
- R9.9 : COMPLETE + NORMALIZED; CONDITIONAL NOT TRIGGERED.
- R9.10 : COMPLETE + NORMALIZED; manual NONE.
- R9.11 : implementation ACCEPTED; final documentation/evidence ACCEPTED; PR #127 MERGED; CONDITIONAL NOT TRIGGERED; final continuity normalization pending.
- R9 phase : **COMPLETE + NORMALIZED iff this exact final continuity-normalization commit is merged to `main`; otherwise IN PROGRESS solely for that normalization.**
- R10–R16 : PENDING / NOT STARTED; R10 is authorized only after the final R9 normalization merge.

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

## Final R9 normalization rule / next action

The current branch `r9/11-final-continuity-normalization` is the **single final R9 normalization**. Freeze its exact commit after this update. Require R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact SHA. Linux Python must still report R7 PASS, R8 PASS and R9 PASS with `blockers=[]` and unchanged integrated digest `19291d79bd800fdb76d96656f9f150ee3114dbcde08d2e82415aff7ff747816a`.

If all three gates succeed, merge the normalization PR into `main`. **The act of merging that exact validated continuity-only normalization satisfies the last frozen R9 phase-completion condition; at that point R9 is COMPLETE + NORMALIZED and R10 planning/work is authorized.** Do not create another recursive continuity update solely to record the normalization's own run IDs; those exact-head IDs belong in the normalization PR body/merge record, as established by prior R9 normalizations.
