# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 23 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1 COMPLETE + NORMALIZED. R9.2 COMPLETE + NORMALIZED. R9.3 COMPLETE + NORMALIZED. R9.4 COMPLETE + NORMALIZED. R9.5 IMPLEMENTATION ACCEPTED; final documentation gates pending.** `docs/roadmap/R9_PLAN.md` est l’autorité structurelle exhaustive de R9.1–R9.11. R9.4 est normalisée via PR #112 sous `920267d9096d340e50379f28c0f9506b9347f9f0`. R9.5 est acceptée côté implémentation sur `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112` avec R0 #1142 / `32629125994`, Python Core #1116 / `32629126032`, UI Smoke #1083 / `32629125952`, tous SUCCESS; Ubuntu `654 passed / 6 skipped / 46 warnings`. Manual R9.5 = CONDITIONAL NOT TRIGGERED. Faire passer les trois gates sur le head documentaire final de PR #113, fusionner #113 uniquement si tous sont SUCCESS, puis effectuer une normalisation continuity-only avant toute R9.6.

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
- R9 planning normalization : ACCEPTED sur `51a6bb7d04d8aacd47e621b15a747f6e9d08781c`; R0 #1106 / `32623679409`; Python Core #1080 / `32623679387`; UI Smoke #1047 / `32623679382`; PR #104 merge `e3f7bf6039cee918a5d505fb47ed536cde087e0e`.
- R9.1 : COMPLETE; implementation head `dfde39746f0ec909a865a9f0ef75b6856e77c88f`, final documentation head `cb746fbfe1f318a5b05d4a6e35f1b8afb2338b58`; PR #105 merge `2eeadafb7cf12328a2c502684187a24ae82a82b7`; normalization head `1bd7dafa0307bc1985ef6811e529393c508680f8`; R0 #1111 / `32624628174`, Python #1085 / `32624628215`, UI #1052 / `32624628266`, all SUCCESS; PR #106 merge `2d646a08412b18709b5a1d3aa0c9a4bfed30ea05`.
- R9.2 : COMPLETE + NORMALIZED; implementation head `15186ced206f05d8baf764738615e6625aa6d459`, final documentation head `89ea9d90ffab6db3563164e629f192caca91ed79`; R0 #1117 / `32625547484`, Python Core #1091 / `32625547536`, UI Smoke #1058 / `32625547485`, all SUCCESS; manual CONDITIONAL NOT TRIGGERED; PR #107 merge `549c1d6f0adc622d92997240bb2e6df2a654b3ee`; normalization head `3fd267d6f5901f0da3a41f85325cf7e58a9ded9f`; R0 #1119 / `32625925666`, Python #1093 / `32625925669`, UI #1060 / `32625925742`, all SUCCESS; PR #108 merge `9c18a0dc88f311c6aab469cdd6c9a02ca453805b`.
- R9.3 : COMPLETE + NORMALIZED; implementation head `915075149fa81b31308c3eedcfa35e74f8a9b7a4`, final documentation head `97e47799f6efe30eed58d73abf509d9d34ed862d`; R0 #1127 / `32626703651`, Python Core #1101 / `32626703557`, UI Smoke #1068 / `32626703574`, all SUCCESS; manual NONE; PR #109 merge `fdd054fa93a91b9e9bb017fe2df982f364c4ecfc`; normalization head `6da529ca8a2aa20d7c2d13e69e21c9579173a1fb`; R0 #1130 / `32626924944`, Python #1104 / `32626924986`, UI #1071 / `32626924952`, all SUCCESS; PR #110 merge `e9152cbe15ba9da2b383e2e6577251ca7c424e41`.
- R9.4 : COMPLETE + NORMALIZED; implementation head `e158fd643ecf55a1ed9022193a48d2d1ee1716ed`, final documentation head `45c2fbd3125d654cbac843e1f90133d81da12395`; R0 #1134 / `32627572953`, Python Core #1108 / `32627572958`, UI Smoke #1075 / `32627572965`, all SUCCESS; manual NONE; PR #111 merge `5f9c0ddf0a0f1835a172c30b287eba1a6ee79921`; normalization head `7c9ea55f531c919fe8d843dc84166a20db663a19`; R0 #1138 / `32627915880`, Python #1112 / `32627915886`, UI #1079 / `32627915883`, all SUCCESS; PR #112 merge `920267d9096d340e50379f28c0f9506b9347f9f0`.
- R9.5 : IMPLEMENTATION ACCEPTED on `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112`; R0 #1142 / `32629125994`, Python Core #1116 / `32629126032`, UI Smoke #1083 / `32629125952`, all SUCCESS; Ubuntu `654 passed / 6 skipped / 46 warnings`; manual CONDITIONAL NOT TRIGGERED; final documentation gates / PR #113 merge pending.
- R9.6–R9.11 : PLANNED / NOT STARTED; structure R9.1–R9.11 figée par le plan fusionné.
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
- Planning normalization head `51a6bb7d04d8aacd47e621b15a747f6e9d08781c`: R0 #1106 / `32623679409`, Python #1080 / `32623679387`, UI #1047 / `32623679382`, all SUCCESS; PR #104 merge `e3f7bf6039cee918a5d505fb47ed536cde087e0e`.
- Plan authority: `docs/roadmap/R9_PLAN.md`.
- Frozen subdivision count: 11 (`R9.1`–`R9.11`).
- Frozen manual states: R9.1 NONE; R9.2 CONDITIONAL; R9.3 NONE; R9.4 NONE; R9.5 CONDITIONAL; R9.6 NONE; R9.7 NONE; R9.8 REQUIRED; R9.9 CONDITIONAL; R9.10 NONE; R9.11 CONDITIONAL.
- R9.8 REQUIRED reason: hosted CI cannot authoritatively validate real GPU VRAM allocation/release/backend behavior; acceptance requires real local ComfyUI/GPU evidence on the exact R9.8 head.
- Planning acceptance and normalization are complete.

## R9 accepted structure and evidence

| ID | Title | Exact accepted head | CI | Manual final |
| --- | --- | --- | --- | --- |
| R9.1 | ComfyUI contracts, local endpoint boundary + capability schema | `cb746fbfe1f318a5b05d4a6e35f1b8afb2338b58` | R0 #1109; Python #1083; UI #1050 | NONE |
| R9.2 | Typed HTTP/WebSocket client, health, queue/history + protocol state | `89ea9d90ffab6db3563164e629f192caca91ed79` | R0 #1117; Python #1091; UI #1058 | CONDITIONAL NOT TRIGGERED |
| R9.3 | Node/model inventory + capability snapshots | `97e47799f6efe30eed58d73abf509d9d34ed862d` | R0 #1127; Python #1101; UI #1068 | NONE |
| R9.4 | Validated workflow catalog + governed model resolver | `45c2fbd3125d654cbac843e1f90133d81da12395` | R0 #1134; Python #1108; UI #1075 | NONE |
| R9.5 | Execution engine, queue/progress/reconciliation + run manifests | `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112` (implementation) | R0 #1142; Python #1116; UI #1083 | CONDITIONAL NOT TRIGGERED |
| R9.6 | Generated-output capture + R8 Vault/AssetPipeline lineage bridge | — | — | NONE |
| R9.7 | Cancellation, interruption, crash recovery + free-memory semantics | — | — | NONE |
| R9.8 | VRAM telemetry, admission scheduler + Ollama coexistence | — | — | REQUIRED |
| R9.9 | Production 2D/UI/texture/concept workflow packs | — | — | CONDITIONAL |
| R9.10 | CLI + KodeStudio ComfyUI/VRAM UX | — | — | NONE |
| R9.11 | Adversarial hardening + R9 integrated acceptance | — | — | CONDITIONAL |

### R9.1 accepted baseline

- Base normalized R9 planning `main`: `e3f7bf6039cee918a5d505fb47ed536cde087e0e`.
- Accepted implementation head `dfde39746f0ec909a865a9f0ef75b6856e77c88f`: R0 #1108 / `32624052368`, Python Core #1082 / `32624052364`, UI Smoke #1049 / `32624052378`, all SUCCESS.
- Python Ubuntu on implementation head: `612 passed / 6 skipped / 46 warnings`; R7 and R8 integrated acceptance PASS; package builds Ubuntu + Windows SUCCESS.
- Final documentation head `cb746fbfe1f318a5b05d4a6e35f1b8afb2338b58`: R0 #1109 / `32624132192`, Python Core #1083 / `32624132167`, UI Smoke #1050 / `32624132173`, all SUCCESS.
- PR #105 merged as `2eeadafb7cf12328a2c502684187a24ae82a82b7`.
- Post-merge continuity normalization head `1bd7dafa0307bc1985ef6811e529393c508680f8`: R0 #1111 / `32624628174`, Python #1085 / `32624628215`, UI #1052 / `32624628266`, all SUCCESS; PR #106 merged as `2d646a08412b18709b5a1d3aa0c9a4bfed30ea05`.
- `ComfyEndpoint` accepts only explicit loopback literals `127.0.0.1` / `::1` with explicit port, rejects credentials/non-root origin paths/query/fragment/non-loopback and validates redirects against the exact origin without DNS resolution.
- R9.1 adds immutable capability/queue/run/resource contracts, inert prompt/history/output references, bounded transport limits, deterministic canonical JSON/SHA-256 envelopes, explicit exception taxonomy, and four strict versioned root schemas.
- R9.1 performs no HTTP/WebSocket/socket/subprocess/model/GPU action; network behavior starts only in R9.2.
- Manual intervention: NONE.

### R9.2 accepted baseline

- Base normalized R9.1 `main`: `2d646a08412b18709b5a1d3aa0c9a4bfed30ea05`.
- Exact accepted implementation head: `15186ced206f05d8baf764738615e6625aa6d459`.
- Implementation gates: R0 Repository Guard #1114 / `32625248672`: SUCCESS Ubuntu + Windows; Python Core #1088 / `32625248645`: SUCCESS 5/5 with Ubuntu `626 passed / 6 skipped / 46 warnings` and Windows `623 passed / 9 skipped / 46 warnings`; KodeStudio UI Smoke #1055 / `32625248725`: SUCCESS.
- Final documentation/continuity head `89ea9d90ffab6db3563164e629f192caca91ed79`: R0 #1117 / `32625547484`, Python Core #1091 / `32625547536`, UI Smoke #1058 / `32625547485`, all SUCCESS.
- PR #107 merged as `549c1d6f0adc622d92997240bb2e6df2a654b3ee`.
- Post-merge continuity normalization head `3fd267d6f5901f0da3a41f85325cf7e58a9ded9f`: R0 #1119 / `32625925666`, Python #1093 / `32625925669`, UI #1060 / `32625925742`, all SUCCESS; PR #108 merged as `9c18a0dc88f311c6aab469cdd6c9a02ca453805b`.
- Fixed `ComfyUIClient` exposes health/system/features/prompt metadata, queue/history, bounded output retrieval, queue/history reconciliation, WebSocket event iteration and narrow probe; it exposes no public arbitrary HTTP method/path surface.
- HTTP redirects remain exact-origin loopback only, prompt IDs are percent-encoded before path use, `/view` metadata is query-encoded, response bodies and WebSocket frames are bounded, and connection failures become explicit `UNAVAILABLE` rather than fabricated readiness.
- WebSocket parser supports the required bounded RFC6455 subset and checks announced payload size before payload read; reconnect/backoff/cancellation are bounded.
- WebSocket is telemetry only; pollable queue/history remains final execution-state authority because upstream can stall WS delivery while HTTP/execution continue and success events can precede durable history persistence.
- Deterministic fixture `tests/fixtures/comfyui/r9_2_protocol.json`: version 1, SHA-256 `1b5b6947e6af1440f59ffc1d6a9d3ed3502fdc057e1bd08a5680300cb42fd656`; `.gitattributes` pins only this fixture family to LF for cross-platform byte identity.
- Rejected precursor `9b9a79f69ef7c304bd743b74bf0379f5d3688588`: R0 #1113 and UI #1054 SUCCESS; Python #1087 failed only the Windows raw fixture digest because Git converted LF→CRLF; Ubuntu remained fully green. Accepted correction changed line-ending policy only and did not weaken production safeguards.
- `comfy-probe` exists solely for the frozen conditional diagnostic and writes strict versioned evidence inside the current workspace atomically.
- Manual intervention: **CONDITIONAL NOT TRIGGERED** because deterministic loopback CI on both platforms plus current upstream ComfyUI source/tests establish every R9.2 acceptance property; no property depends on GPU, models, custom nodes or a user-specific ComfyUI deployment.

### R9.3 accepted baseline

- Base normalized R9.2 `main`: `9c18a0dc88f311c6aab469cdd6c9a02ca453805b`.
- Exact accepted implementation head: `915075149fa81b31308c3eedcfa35e74f8a9b7a4`.
- Implementation gates: R0 #1125 / `32626438121`, Python #1099 / `32626438098`, UI #1066 / `32626438104`, all SUCCESS; Ubuntu `634 passed / 6 skipped / 46 warnings`; Windows tests and Ubuntu/Windows package builds SUCCESS; R7/R8 integrated acceptance PASS.
- Final documentation/continuity head `97e47799f6efe30eed58d73abf509d9d34ed862d`: R0 #1127 / `32626703651`, Python #1101 / `32626703557`, UI #1068 / `32626703574`, all SUCCESS.
- PR #109 merged as `fdd054fa93a91b9e9bb017fe2df982f364c4ecfc`.
- Post-merge continuity normalization head `6da529ca8a2aa20d7c2d13e69e21c9579173a1fb`: R0 #1130 / `32626924944`, Python #1104 / `32626924986`, UI #1071 / `32626924952`, all SUCCESS; PR #110 merged as `e9152cbe15ba9da2b383e2e6577251ca7c424e41`.
- `ComfyCapabilityInventory` discovers only the fixed accepted loopback routes and never scans Kodepoia model directories or executes/downloads nodes/models.
- Snapshot identity binds endpoint/system/features/nodes/models/unavailable evidence but excludes `captured_at`; unchanged recapture at the same endpoint is deterministic.
- Unknown node-extension metadata is inert but SHA-256-bound so drift is visible; model tokens are relative logical identifiers only and cannot manufacture Vault/provenance/license truth.
- Capability drift yields explicit `STALE` evidence; the root-confined atomic snapshot cache is rebuildable and tamper-checked.
- Frozen R9.1 `comfy-capability-snapshot-v1` envelope remains unchanged; R9.3 adds a separate strict payload schema.
- Rejected precursor `5c714d49d775dd04d04bca95ec341289cc59a515`: R0 #1121 and UI #1062 SUCCESS, Python #1095 FAILURE with two newly introduced failures (illegal tightening of the R9.1 root schema and a determinism fixture that changed endpoint as well as timestamp). Both were corrected without weakening gates.
- Manual intervention: NONE.

### R9.4 accepted baseline

- Base normalized R9.3 `main`: `e9152cbe15ba9da2b383e2e6577251ca7c424e41`.
- Exact accepted implementation head: `e158fd643ecf55a1ed9022193a48d2d1ee1716ed`.
- Implementation gates: R0 #1132 / `32627342083`, Python #1106 / `32627342056`, UI #1073 / `32627342058`, all SUCCESS; Ubuntu `643 passed / 6 skipped / 46 warnings`; Windows tests and Ubuntu/Windows package builds SUCCESS; R7/R8 integrated acceptance PASS.
- Final documentation/continuity head `45c2fbd3125d654cbac843e1f90133d81da12395`: R0 #1134 / `32627572953`, Python #1108 / `32627572958`, UI #1075 / `32627572965`, all SUCCESS.
- PR #111 merged as `5f9c0ddf0a0f1835a172c30b287eba1a6ee79921`.
- Post-merge continuity normalization head `7c9ea55f531c919fe8d843dc84166a20db663a19`: R0 #1138 / `32627915880`, Python #1112 / `32627915886`, UI #1079 / `32627915883`, all SUCCESS; PR #112 merged as `920267d9096d340e50379f28c0f9506b9347f9f0`.
- `WorkflowDefinition` binds the canonical Kodepoia-owned API graph, revision, allowlisted classes, scalar/input/output slots and model requirements into a SHA-256 definition identity; node IDs/classes/connections cannot be parameter-mutated.
- Only declared `$param`, `$input` and `$model` markers can be substituted. Parameters are bounded JSON scalars, so a parameter cannot inject an arbitrary mapping/graph fragment.
- Validation requires a `CURRENT` R9.3 snapshot and checks node presence, allowlist, required/unknown inputs, scalar constraints, link type compatibility and output-slot types against that exact capability evidence.
- Seeds are explicit typed parameters; R9.4 does not manufacture hidden randomness.
- `GovernedModelResolver` resolves only discovered inventory tokens and exposes `RESOLVED`, `MISSING`, `AMBIGUOUS` and `BLOCKED`. Multiple candidates require explicit deterministic selection; no filename is guessed or downloaded.
- Optional `VaultModelEvidence` reuses R8 `AssetRevisionId`, exact digest, `ReuseScope`, `AssetGovernanceOutcome` and license evidence. External-local models without R8 evidence remain `NOASSERTION` and non-exportable.
- `WorkflowCatalog` loads only explicitly named, root-confined, non-symlink JSON files and recomputes canonical definition identity. There is no recursive workflow discovery.
- Frozen R9.1 root workflow envelope remains unchanged; strict R9.4 payload validation lives in `comfy-workflow-definition-payload-v1.schema.json`.
- Manual intervention: NONE.

### R9.5 accepted implementation baseline

- Base normalized R9.4 `main`: `920267d9096d340e50379f28c0f9506b9347f9f0`.
- Exact accepted implementation head: `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112`.
- Implementation gates: R0 #1142 / `32629125994`, Python #1116 / `32629126032`, UI #1083 / `32629125952`, all SUCCESS; Python Core 5/5; Ubuntu `654 passed / 6 skipped / 46 warnings`; Windows tests and Ubuntu/Windows package builds SUCCESS; R7/R8 integrated acceptance PASS.
- A run persists `PREPARED` before its first and only prompt POST; immediately before the side effect, append-only evidence records `ATTEMPTING` and `submission_attempts=1`.
- Lost/ambiguous POST responses never trigger an automatic second POST. Recovery uses only bounded idempotent queue/history reads keyed by the exact persisted `prompt_id`; unresolved ambiguity remains explicit and blocks resubmission even on a later `submit()` call.
- WebSocket messages are telemetry only. Progress is accumulated monotonically, while terminal state is derived only from coherent queue/history evidence.
- Terminal history must match the persisted prompt digest and Kodepoia correlation. `SUCCEEDED` additionally requires every explicitly required output-node reference.
- Execution is bound to the exact R9.3 capability endpoint: snapshot and persisted manifest origins must equal the fixed `ComfyUIClient` origin for preparation, submission, polling/waiting and WebSocket observation.
- `ComfyRunManifest` records explicit workflow, capability/environment, model-resolution, parameters, input bindings, seeds, submission, queue/history, progress and output-reference evidence.
- `ComfyRunStore` preserves immutable digest-named revisions linked by `previous_manifest_digest_sha256`, plus an atomic current pointer that can be recovered from the validated append-only chain.
- Frozen R9.1 root run-manifest envelope remains unchanged; strict R9.5 payload validation is separate in `schemas/comfy-run-manifest-payload-v1.schema.json`.
- Deterministic fixture `tests/fixtures/comfyui/r9_5_execution.json`: version 1, SHA-256 `549eab22a20f34ad367baf8f46d5c1a5166cd9fb8cbb90fdb983b9bd1129d50a`, 542 bytes.
- Rejected precursor `4d0a5e0f66603387893d1633ba283c0e5d5d5078`: R0 #1140 and UI #1081 SUCCESS, Python #1114 / `32628835669` FAILURE with Ubuntu `652 passed / 2 failed / 6 skipped / 46 warnings`. One failure exposed the real missing snapshot/executor-origin binding; the other was a fixture-only `zip(..., strict=True)` assertion mismatch. The accepted correction strengthened production confinement and fixed only the test mechanism.
- Manual intervention: **CONDITIONAL NOT TRIGGERED** because deterministic loopback CI on both hosted platforms establishes the frozen R9.5 execution/recovery/duplicate-prevention properties, while current upstream ComfyUI evidence confirms that queue/history must remain the durable authority when WebSocket delivery stalls or success precedes output persistence. No required property depends on GPU, model/custom-node installation or a user-specific deployment.
- `docs/roadmap/R9_5_ACCEPTANCE.md` pins the implementation evidence. Final documentation/continuity head must pass all three exact-head gates before PR #113 merge.

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
- Exact accepted head `8c88aeb8a32abce2e9ecb670da3c2acbb4a31cfe`; R0 #1057 / `32603562499`; Python Core #1031 / `32603562511` 5/5 with Ubuntu `547 passed / 5 skipped / 46 warnings`; UI Smoke #998 / `32603562503`; PR #91 merge `57c2aa010f438b95a3d753040f1565ae4b68e262`; manual NONE.
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

**R1–R8 COMPLETE. R9 planning ACCEPTED + NORMALIZED. R9.1 COMPLETE + NORMALIZED. R9.2 COMPLETE + NORMALIZED. R9.3 COMPLETE + NORMALIZED. R9.4 COMPLETE + NORMALIZED. R9.5 IMPLEMENTATION ACCEPTED.** Faire passer R0 Repository Guard, full Python Core et KodeStudio UI Smoke sur le head documentaire final de PR #113. Si les trois sont SUCCESS sur ce SHA exact, fusionner #113 avec verrou exact-head. Ensuite créer une normalisation continuity-only enregistrant le final documentation head, les trois runs finaux et le merge SHA de #113; gate et fusionner cette normalisation avant toute R9.6.