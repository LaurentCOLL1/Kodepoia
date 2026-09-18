# Kodepoia next actions

Last synchronized: 2026-09-18 after V2.1.6 implementation PR `#486` merged and post-merge continuity normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0 and V2.1.1 through V2.1.6 are **COMPLETE + NORMALIZED**.

## V2.1.5 accepted implementation

V2.1.5 implementation PR `#484` was qualified with **27/27** `completed/success` pull-request workflows on exact head:

`f46068a410e7e0ea3f32f8decc77eed6aa105355`

It merged from that unchanged head as:

`bfe7fa6b4def1a291d97bd2b9365bda321bcde52`

The final exact-head qualification included:

- `R0 Repository Guard` run `35265257329` = `completed/success`;
- `Python Core` run `35265257418` = `completed/success`;
- `KodeStudio UI Smoke` run `35265257290` = `completed/success`;
- `R17 Windows Installer` run `35265257386` = `completed/success`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35265257328` = `completed/success`.

V2.1.5 exact-head evidence:

- Ubuntu artifact `v2-1-5-extended-sources-ubuntu-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `6275abca3e380e118120718834fd34e68e819822860220b4f79a2f63ff69c2e7`;
- Windows artifact `v2-1-5-extended-sources-windows-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `68373539d62e0e348ce6ab7ff5f23c567b0f0e287a98901f31895d34986a4b0b`.

The deterministic V2.1.5 acceptance reported **12/12 PASS** on Ubuntu and Windows. Accepted product truth includes:

- YouTube and community discovery items remain descriptor-only `candidate-only` / `unfetched` candidates until an explicit guarded acquisition succeeds;
- official YouTube `search.list` payloads are normalized into bounded video descriptors without implicit fetch or persistence;
- YouTube metadata/transcript acquisition uses the existing guarded provider path and keeps network, credential, provider and transcript-unavailable states explicit;
- community acquisition remains guarded and preserves semantic thread relationships such as parent/quote linkage without treating popularity as authority;
- acquired community/media content enters the canonical `ResearchStore` / `EvidenceWorkspace` / selection lifecycle with existing provenance, revision, citation and Research Pack contracts;
- speech-to-text and frame extraction remain explicitly non-authoritative and cannot silently become trusted evidence;
- KodeStudio exposes typed Community/YouTube fetch choices, provider state and candidate-to-explicit-fetch handoff without collapsing discovery into acquisition;
- source content remains untrusted data and cannot grant permissions or invoke protected actions;
- V2.1.6 adversarial hardening and all release/TUF/updater work remained out of scope.

## V2.1.6 accepted implementation

Implementation PR `#486` was qualified on exact head `2e788df0886e1e31512f53547ea4603186e964eb` with **27/27** successful pull-request workflows and merged as `7efcc3e941fe8db0e3cc00c81b147716c91eb30b`.

The deterministic acceptance reported **12/12 PASS** on Ubuntu and Windows with evidence payload SHA-256 `076195a992effe8a1eac25d6074a5fc12508d004da7f9ec8b01f3177a4c40f74`.

Exact-head artifacts:

- Ubuntu `v2-1-6-researchguard-hardening-ubuntu-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `32d972eb83a070fcb7a2844eae11403518bdfe412bd445db74a9556269a0dac1`;
- Windows `v2-1-6-researchguard-hardening-windows-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `7dd9a6ff8e79f40829a2b11439583ced1c221d63c4c0ca1882d2829a9f0ed4ee`.

Accepted product truth includes:

- unsafe extended-source locators, private/local/link-local/metadata targets, mixed public/private DNS and malicious redirects fail closed before trusted acquisition;
- `BLOCKED` is reserved for policy/security denial and `UNAVAILABLE` for provider/transport failure;
- provider diagnostics are KodeSecrets-redacted;
- cancellation cannot persist new extended-source evidence after the cancellation gate trips;
- stale/offline/cache and version-conflict states remain explicit while immutable evidence/citation lineage is preserved;
- adversarial source text remains data-only and cannot grant capabilities, escape WorkspaceBoundary or invoke protected actions;
- KodeStudio preserves V2.1.5 Community/YouTube and descriptor-only lifecycle semantics while structurally surfacing V2.1.6 degraded states.

## Immediate execution order

### V2.2 planning — CURRENT

The current task is to qualify the planning-only authority:

`docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md`

This plan derives directly from the accepted Roadmap V2 V2.2 deliverables and existing source primitives. It freezes six subdivisions:

1. **V2.2.1 — Project Knowledge catalog and contracts**
2. **V2.2.2 — Bounded semantic retrieval**
3. **V2.2.3 — Explainable Context Builder**
4. **V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle**
5. **V2.2.5 — Project Memory bridge and workspace consumption**
6. **V2.2.6 — Project Knowledge hardening and integrated acceptance**

The planning PR is documentation-only. It must be qualified on its exact final head and merged before any V2.2 implementation. Then perform exactly one post-merge continuity normalization; only that normalized state may authorize **V2.2.1**.

### V2.2.1 — Project Knowledge catalog and contracts — NOT YET AUTHORIZED

After planning normalization only, V2.2.1 may establish the deterministic project-scoped knowledge catalog over:

- governed Research Packs;
- WorkspaceBoundary-confined project files;
- verified active-project MemoryStore records.

It must preserve provenance/trust/version metadata and must not implement semantic retrieval, context injection, automatic memory writes, cross-workspace orchestration or release work.

The accepted V2.1 chain remains invariant:

`discovery -> candidate-only/unfetched -> explicit guarded fetch -> persisted evidence -> explicit include/exclude -> cited synthesis -> governed Research Pack`

Research-derived/project knowledge remains data and cannot become instruction authority merely by being indexed, retrieved or placed in context.

## Later V2 order

Only after V2.2 is completed subdivision by subdivision and normalized may the roadmap proceed to V2.3. Do not pull forward V2.3 Model Lab, V2.4 accelerator qualification, V2.5 cross-workspace orchestration or V2.6 release work.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md. V2.1.6 est COMPLETE + NORMALIZED. La tâche courante est la planification V2.2 seulement : qualifie la PR de planification sur son head exact, fusionne-la uniquement si tous ses workflows PR sont completed/success, puis effectue une normalisation post-merge avant toute V2.2.1. Le plan V2.2 doit conserver Research Packs immuables, project scope, ResearchGuard, WorkspaceBoundary, KodeSecrets, R16.7 MemoryStore hardening et l'interdiction de promotion implicite de texte Web en instructions durables. La distribution publique reste v1.1.0-rc8; R20 reste terminal.`
