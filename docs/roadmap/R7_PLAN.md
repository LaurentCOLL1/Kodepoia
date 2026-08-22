# Kodepoia — R7 detailed phase plan

**Phase:** R7  
**Roadmap title:** Research sécurisé  
**Status:** PLANNING  
**Phase planning started:** 2026-08-22  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `06089d2577f3573e36020b2fbe5a06cf5d0f7939`

## Purpose and authority

R7 implements the frozen KodeResearch capability without changing Kodepoia's foundations. It covers local and official documentation, governed Web research, GitHub, community/forums and YouTube, including transcript acquisition, local STT fallback, frame extraction/analysis hooks and version awareness. External content is always evidence/data, never agent instructions.

This file is the exhaustive execution/recovery plan for R7. The R7.1–R7.11 subdivision structure becomes frozen when this plan is merged. No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must update this plan and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any foundation change requires an ADR.

R7.1 MUST NOT begin before this plan is merged to `main` with the required planning CI gates successful on the exact final planning head.

## Phase objective

Deliver a deterministic, auditable and local-first research layer that can gather, normalize, cache, cite and compare information from the source classes required by the frozen roadmap while preserving provenance, version/date context and trust boundaries. The system must explicitly distinguish source facts from model inference, preserve uncertainty/staleness, resist indirect prompt injection, avoid arbitrary network/process surfaces and remain usable offline for previously cached/configured project research.

Out of scope for R7: general autonomous browser control, arbitrary shell execution, arbitrary file download/install, remote LLM requirements, R8 Vault/AssetPipeline behavior, R9 ComfyUI/VRAM orchestration, R10 Blender, R11 audio/voice/cinematics, store/release compliance crawling and fine-tuning.

## Permanent phase-wide architecture and governance boundaries

Every R7 subdivision must preserve:

- `WorkspaceBoundary` confinement for project-local persistent research data and symlink/path escape rejection;
- existing `ResearchGuard` as the single external-content trust boundary; no second prompt-injection engine with conflicting semantics;
- `Guardian` + `PermissionSet` authorization for network, credential use, downloads and external-tool actions;
- `ProcessSandbox` + global KillSwitch for every external executable; no model-supplied arbitrary executable/argv/cwd/env/host;
- structured research/tool APIs only;
- `KodeSecrets` broker/redaction for optional credentials; secrets never enter prompts, caches or persisted research content;
- SafeChange/Backup/Recovery/Audit primitives when mutations or durable state changes require them;
- versioned schemas/DataGovernance and canonical/anti-tamper evidence where reports are persisted;
- explicit `UNKNOWN`, `UNAVAILABLE`, `N/A`, `BLOCKED` and `STALE` semantics; missing evidence never manufactures PASS or freshness;
- exact source provenance: locator, source class, retrieval time, content digest and relevant version/date metadata;
- platform-aware behavior and local-first/offline-capable behavior for already cached/configured research;
- R6 Health/Budget/Regression/CI/AppSecurity/Privacy/License/BOM contracts and R6.12 major-patch/rollback contract;
- ADR requirement for any change to a frozen foundation.

## Research trust and network model

1. External text, metadata, transcripts, comments, README files, issue bodies, subtitles and extracted page content are untrusted data.
2. `ResearchGuard` wraps/sanitizes content before it can enter model context. Suspicious indicators remain evidence; suspicious content is not silently deleted unless policy requires blocking.
3. Fetch adapters accept typed locators/requests, not arbitrary model-authored command lines.
4. HTTP policy must reject unsafe schemes, credential-bearing URLs, prohibited redirects and local/private/link-local/loopback targets unless a separately authorized local-source adapter explicitly owns that target class.
5. Response size, MIME/content-type, redirect count, timeout and rate limits are bounded.
6. Downloaded media or files are never executed. Any external tool consumes only validated sandbox/workspace paths.
7. Optional authenticated GitHub/provider access uses secret references resolved outside model context.
8. Cache entries retain provenance and content hashes; cache reuse never rewrites retrieval date/version evidence as if freshly observed.

## Global prerequisites

Before R7.1 implementation begins:

- R1–R6 are COMPLETE on normalized `main`;
- `R6_INTEGRATED_ACCEPTANCE.json` remains valid and `tests/test_r6_12_repository_integration.py` passes;
- Python baseline remains 3.12.x; current accepted local baseline is Python 3.12.4 on Windows 11;
- existing `WorkspaceBoundary`, `ResearchGuard`, Guardian/permissions, Sandbox/KillSwitch, Secrets, Audit, DataGovernance, R6 quality gates and KodeContext/KodeMemory remain available;
- no new mandatory remote API or cloud LLM dependency is introduced;
- any optional external binary/provider added later must have deterministic capability detection and explicit unavailable semantics.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | PLANNED | NONE | R6 COMPLETE + planning PR merged |
| R7.2 | Local + official documentation research | PLANNED | NONE | R7.1 |
| R7.3 | Governed Web fetch + extraction | PLANNED | NONE | R7.1–R7.2 |
| R7.4 | GitHub research adapter | PLANNED | CONDITIONAL | R7.1 + R7.3 |
| R7.5 | Community/forums research normalization | PLANNED | NONE | R7.1 + R7.3 |
| R7.6 | YouTube metadata + transcript ingestion | PLANNED | CONDITIONAL | R7.1 + R7.3 |
| R7.7 | Local STT + frame extraction/analysis hooks | PLANNED | REQUIRED | R7.6 + R5 process/media baseline |
| R7.8 | Version-awareness + provenance/conflict model | PLANNED | NONE | R7.2–R7.7 |
| R7.9 | Research cache + Context/Memory orchestration | PLANNED | NONE | R7.1–R7.8 |
| R7.10 | CLI + KodeStudio Research UX | PLANNED | NONE | R7.1–R7.9 |
| R7.11 | Adversarial hardening + R7 integrated acceptance | PLANNED | CONDITIONAL | R7.1–R7.10 |

---

# R7.1 — KodeResearch contracts + ResearchGuard hardening

## Objective and rationale

Create the typed domain contract and one safe ingestion pipeline before any live-source adapter exists. Strengthen the existing `ResearchGuard` only as required for R7 while preserving its role as the single external-content boundary.

## In scope

- `ResearchRequest`, `ResearchSource`, `ResearchArtifact`, `ResearchCitation`, `ResearchFinding`, `ResearchStatus`, trust/source-kind enums and canonical IDs;
- source classes: local, official_docs, web, github, forum/community, youtube;
- content digest, retrieval time, author/publisher/version/date fields and explicit freshness state;
- guarded-content envelope retaining suspicious indicators and original provenance;
- versioned schemas for persisted request/result/report records;
- project-confined `.kodepoia/research/` store layout;
- deterministic policy errors for blocked/unsafe requests.

## Out of scope

No live HTTP, GitHub, forum or YouTube traffic; no STT/media processing; no UI.

## Detailed implementation plan

Create a research package under `src/kodepoia/intelligence/research/` with contracts, policy and store primitives. Reuse `src/kodepoia/core/research_guard.py`; extend tests and guard metadata rather than replacing the class with a separate policy engine. Canonical serialization must recompute derived fields/digests on load and reject tampering. Persistent writes resolve through `WorkspaceBoundary` and use atomic replacement.

## Deliverables

Research package/contracts/store, schemas under `schemas/`, focused tests, ResearchGuard regression tests, design/acceptance docs.

## Acceptance gates / Definition of Done

R0, Python Core and UI Smoke SUCCESS on exact head; focused contracts/schema/round-trip/tamper tests; path-escape tests; suspicious external content remains data and cannot alter tool intent; no network/process surface introduced.

## Validation and evidence

Exact implementation SHA, workflow run IDs, test counts, schema IDs/digests and acceptance document.

## Rollback / recovery

Remove the new research package/schema/store integration and restore any touched guard file; no persisted migration is irreversible at this stage.

## Risks and regression traps

Over-broad regex blocking legitimate documentation; loss of original evidence; trusting deserialized derived fields; creating a second guard engine; leaking untrusted content into tool arguments.

## Manual intervention

**NONE**.

---

# R7.2 — Local + official documentation research

## Objective and rationale

Provide deterministic offline-first research over project/local documentation and explicitly configured official documentation sources, with provenance and version context.

## In scope

- workspace/local file adapter for supported text/Markdown/JSON/YAML and safely extractable document text where existing dependencies permit;
- official-doc source manifest with canonical publisher/domain/product/version metadata;
- chunking with stable source offsets/anchors and citation reconstruction;
- content-hash based cache reuse;
- source-version observations and stale/unknown handling.

## Out of scope

General Web crawling, recursive filesystem scanning outside authorized roots, PDF OCR, arbitrary binaries and live forum/YouTube behavior.

## Detailed implementation plan

Local file reads go only through validated project/workspace paths. Official-doc manifests describe approved roots/domains and versions but do not create a hidden allow-all network bypass. Parsers retain line/section/URL anchors. Unsupported formats return explicit `UNAVAILABLE` rather than guessed content.

## Deliverables

Local/official adapters, manifest schema, fixtures for multiple versions, citation/chunk tests and acceptance docs.

## Acceptance gates / Definition of Done

Offline fixture suite; symlink/path-escape rejection; exact line/section citation reconstruction; deterministic cache digest; version mismatch/staleness visible; R0/Python/UI gates successful.

## Validation and evidence

Exact SHA, fixture hashes, run IDs, source/version examples and acceptance report.

## Rollback / recovery

Delete adapter/cache records created by fixtures; preserve source documents untouched.

## Risks and regression traps

Accidental traversal outside workspace; treating an unofficial mirror as official; cache masquerading as fresh retrieval; silently dropping anchors.

## Manual intervention

**NONE**.

---

# R7.3 — Governed Web fetch + extraction

## Objective and rationale

Add a bounded read-only Web transport and deterministic extraction layer suitable for technical research without becoming a general browser agent.

## In scope

- typed HTTP(S) research requests;
- URL normalization, redirect policy, DNS/target safety checks, timeout/size/MIME/rate limits;
- text/HTML extraction with title, headings, canonical locator and publication/update metadata when evidenced;
- robots/provider policy metadata when applicable;
- deterministic fake/local test transport so CI does not depend on public Internet availability;
- cache validators such as ETag/Last-Modified when available without fabricating freshness.

## Out of scope

JavaScript browser automation, login form automation, arbitrary POST actions, file execution, install/update actions and hidden network retries.

## Detailed implementation plan

Expose a read-only transport interface. Production HTTP uses fixed methods/headers and bounded redirects; tests inject a deterministic transport. SSRF defenses validate every redirect target and block unsafe schemes/credential-bearing URLs/private network destinations. Extracted text is passed through `ResearchGuard` before context use.

## Deliverables

Web transport/policy/extractor, schemas/fixtures, malicious redirect/oversize/MIME tests and acceptance docs.

## Acceptance gates / Definition of Done

SSRF/redirect/timeout/oversize tests; prompt-injection fixtures; no arbitrary method/body/header execution surface from model input; deterministic offline CI; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, run IDs, policy matrix and representative guarded extraction evidence.

## Rollback / recovery

Disable/remove Web adapter; cached Web artifacts remain inert data and may be purged safely.

## Risks and regression traps

DNS rebinding/redirect bypass, decompression bombs, credential-bearing URLs, charset/parser ambiguity, external content reaching tool-control fields.

## Manual intervention

**NONE**.

---

# R7.4 — GitHub research adapter

## Objective and rationale

Support read-only repository research through structured GitHub entities while preserving provenance, pagination/rate-limit state and optional secret-broker authentication.

## In scope

Repository metadata, files/blobs, commits, releases/tags, issues, PRs and comments required for research; public unauthenticated mode; optional authenticated read mode via secret reference; immutable commit-SHA locators where possible.

## Out of scope

GitHub writes, branch/PR mutation, Actions administration, arbitrary GraphQL supplied by the model and credential exposure.

## Detailed implementation plan

Build on the governed Web transport or a narrow GitHub client adapter. Inputs are typed owner/repo/resource selectors. Normalize paginated evidence and rate-limit metadata. Prefer commit-SHA/raw blob provenance for exact technical evidence. All issue/PR/README content is passed through ResearchGuard.

## Deliverables

GitHub adapter, fixtures, optional-auth capability detection, rate-limit tests and acceptance docs.

## Acceptance gates / Definition of Done

Deterministic fixture suite; public GitHub locator normalization; no write endpoint exposure; secret value absent from logs/results; exact-SHA citation tests; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, run IDs, fixture hashes and, when available, one read-only live public-repository probe captured as non-secret evidence.

## Rollback / recovery

Disable adapter and remove optional credential reference; no remote state has been mutated.

## Risks and regression traps

Rate-limit drift, default-branch movement, token leakage, treating issue comments as instructions, citing mutable branch content as immutable.

## Manual intervention

**CONDITIONAL** — only if authoritative acceptance requires an authenticated/private-repository capability that hosted CI cannot exercise. If triggered, use a least-privilege read-only token stored through KodeSecrets; never paste the token into chat/logs. Evidence returned must contain only redacted capability/result metadata and exact source SHAs. Otherwise NOT TRIGGERED.

---

# R7.5 — Community/forums research normalization

## Objective and rationale

Represent forum/community evidence without conflating popularity, recency or anecdotal consensus with official documentation.

## In scope

Thread/post/comment normalization, author/display metadata, timestamps, parent/thread relationships, quoted-text separation, source trust tier and claim/evidence linking; generic HTML forum support plus provider-specific read adapters only when justified.

## Out of scope

Posting, voting, moderation actions, account automation, sentiment-as-truth scoring and hidden scraping bypasses.

## Detailed implementation plan

Use R7.3 transport and typed community extractors. Preserve thread context and timestamps; distinguish quoted content from author content. Ranking metadata may describe recency/source type but must not convert community consensus into authoritative fact.

## Deliverables

Community models/extractors/fixtures, nested quote tests, provenance tests and acceptance docs.

## Acceptance gates / Definition of Done

Prompt-injection fixtures in posts/comments; nested/edited/deleted content semantics; no community source auto-promoted to official; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, run IDs and canonical normalized-thread fixtures.

## Rollback / recovery

Remove provider adapters and purge cache entries; no external mutation.

## Risks and regression traps

Quote attribution errors, deleted/edited post ambiguity, popularity bias, provider HTML drift, prompt injection through code blocks/signatures.

## Manual intervention

**NONE**.

---

# R7.6 — YouTube metadata + transcript ingestion

## Objective and rationale

Provide safe read-only YouTube research with video identity, metadata and timestamped transcripts before introducing local media fallback.

## In scope

YouTube URL/video-ID normalization; metadata and chapter/time markers when evidenced; human/automatic transcript tracks where legally/technically accessible; language/track provenance; timestamp citations; guarded transcript content; explicit unavailable/blocked states.

## Out of scope

Media execution, account login automation, DRM bypass, unrestricted downloading, STT and frame extraction (R7.7).

## Detailed implementation plan

Use a narrow provider adapter with deterministic fixtures. If an external helper is required for metadata/transcript retrieval, it must be optional, version-detected and invoked through ProcessSandbox with fixed command templates and validated IDs/paths. Transcript text is always ResearchGuard-wrapped.

## Deliverables

YouTube locator/provider interfaces, transcript models, fixtures in multiple languages/track types, tests and acceptance docs.

## Acceptance gates / Definition of Done

Video-ID validation; timestamp round-trip; unavailable transcript semantics; malicious subtitle/prompt-injection fixtures; no arbitrary helper arguments; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, run IDs, provider/helper version if used and non-copyright-intensive fixture evidence.

## Rollback / recovery

Disable provider/helper integration and purge cached transcript artifacts.

## Risks and regression traps

Provider/API drift, geo/age/network restrictions, transcript availability differences, helper supply-chain changes, treating captions as instructions.

## Manual intervention

**CONDITIONAL** — only if a live provider behavior cannot be authoritatively validated in hosted CI. If triggered, run the planned read-only `kodepoia research youtube-probe <public-video-url>` command on the exact accepted candidate head and return the generated redacted JSON evidence; no account login or cookies are required for the baseline. Otherwise NOT TRIGGERED.

---

# R7.7 — Local STT + frame extraction/analysis hooks

## Objective and rationale

Complete the frozen YouTube/media research requirement when transcripts are missing or visual evidence matters, using governed local processing rather than cloud services.

## In scope

- capability detection for a supported local media helper (`ffmpeg` baseline) and one supported local STT adapter;
- bounded media acquisition only through the R7.6 provider policy and sandboxed validated paths;
- audio extraction, timestamped STT segments and transcript confidence/provenance;
- deterministic frame sampling by timestamp/scene policy, image hash/dimensions and source-video hash;
- `FrameAnalysisProvider` hook for an accepted local vision-capable model; explicit `UNAVAILABLE` when no such model is configured;
- CPU/RAM/disk/time budgets and cancellation/KillSwitch behavior;
- cleanup/recovery of temporary media.

## Out of scope

Cloud STT/vision requirement, model auto-download without approval, arbitrary codecs/executables, R9 VRAM scheduler and full video editing.

## Detailed implementation plan

All helper invocations use ProcessSandbox and fixed argument templates generated from validated typed parameters. Media paths live under a bounded temporary/workspace area. STT models are user-provided/configured artifacts with hash/version metadata; absence is explicit. Frame extraction uses deterministic timestamps and Pillow validation. Semantic frame analysis is capability-gated: R7 must expose the hook and provenance but must never claim visual interpretation when no accepted vision provider is configured.

## Deliverables

Media/STT/frame adapters, helper capability report, schemas, tiny licensed/generated fixture media, cancellation/cleanup tests, benchmark evidence format and acceptance docs.

## Acceptance gates / Definition of Done

Hosted deterministic fixture tests plus required real local-media validation; stdout/stderr drained without deadlock; KillSwitch/cancellation works; generated transcript/frame timestamps match fixture tolerance; no arbitrary argv/cwd; temporary artifacts cleaned; R6 Budget/Regression hooks pass; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA; helper/STT versions and hashes; source fixture hash; command-safe capability report; transcript segment count/timestamps; extracted frame count/hashes; resource measurements; hosted run IDs; local acceptance JSON.

## Rollback / recovery

Kill active helper through existing KillSwitch/process governance, remove temporary media, restore pre-run cache/store snapshot if persistence was being updated, retain audit record.

## Risks and regression traps

Process deadlocks, huge media, malformed codecs, disk exhaustion, model/license provenance, AMD/Windows acceleration differences, timestamps drifting after transcoding, accidental claim of visual analysis without a provider.

## Manual intervention

**REQUIRED** — real local media validation is authoritative because hosted CI cannot prove the accepted Windows/local-tool path.

Planned prerequisites: exact candidate head; Python 3.12.x environment; `ffmpeg` discoverable by the capability detector; configured supported local STT engine/model with recorded version/hash; no secrets; generated/licensed fixture supplied by the repository.

Planned commands, to be finalized verbatim in `R7_7_DESIGN.md` before the gate:

1. `python -m kodepoia.cli research-media-doctor --json .kodepoia/research/r7_7_media_doctor.json`
2. `python -m kodepoia.cli research-media-acceptance --fixture tests/fixtures/research/r7_7_media_fixture.mp4 --output .kodepoia/research/r7_7_local_acceptance.json`
3. `python -m pytest -q tests/test_r7_7_media_local_acceptance.py`

Expected success: commands exit 0; capability report identifies exact helper/STT versions without secrets; acceptance report is PASS, bound to candidate `source_sha`, with transcript/frame hashes and zero failed required checks.

Failure recovery: stop through KillSwitch/normal process cancellation, delete only R7.7 temporary fixture outputs, preserve logs, do not install/change drivers automatically, return to the exact candidate head.

Evidence to send back: the two JSON reports plus pytest terminal summary, with personal paths/usernames redacted if present. Do not send model files, tokens, cookies or unrelated logs.

Do not do yet: do not run these commands before R7.7 implementation/design explicitly declares the manual gate ready.

---

# R7.8 — Version-awareness + provenance/conflict model

## Objective and rationale

Make research version-aware so old documentation or mutable community content cannot silently override evidence relevant to the project's actual tool/framework version.

## In scope

Observed product/version/date/channel metadata, target-version constraints from Project DNA/context, freshness/staleness policy, mutable vs immutable source identity, conflict groups, supersession links and deterministic ranking inputs.

## Out of scope

LLM-only truth arbitration, automatic upgrades/migrations and release-store compliance decisions.

## Detailed implementation plan

Create a `SourceVersion`/`VersionObservation` model that distinguishes exact, range, inferred and unknown versions. Store evidence for every inference and never promote inferred version to exact. Conflicting claims remain visible with independent citations. Ranking favors relevance/authority/freshness only through explicit policy fields; it does not delete contradictory evidence.

## Deliverables

Version/provenance models, policies, schemas, multi-version/conflict fixtures, tests and acceptance docs.

## Acceptance gates / Definition of Done

Old/new docs conflict remains visible; exact vs inferred distinction survives round-trip; mutable branch/forum evidence marked accordingly; unknown version never reported current; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, run IDs and canonical conflict/staleness reports.

## Rollback / recovery

Remove derived version indexes; original artifacts/citations remain intact.

## Risks and regression traps

Semantic-version assumptions for non-semver products, timezone/date ambiguity, mutable pages, false freshness from cache re-read.

## Manual intervention

**NONE**.

---

# R7.9 — Research cache + Context/Memory orchestration

## Objective and rationale

Integrate accepted research evidence with KodeContext/KodeMemory without allowing external content to become persistent trusted instruction or validated experience automatically.

## In scope

Content-addressed research cache, query/result manifests, TTL/revalidation metadata, deduplication, bounded context selection, citation-preserving summaries, research-memory scope and invalidation by source/version/hash.

## Out of scope

Promotion into global validated knowledge/Experience without existing validation/governance; vector-store redesign; hidden background crawling.

## Detailed implementation plan

Persist `.kodepoia/research/` artifacts via WorkspaceBoundary. Research cache entries retain guarded status and provenance. KodeContext receives structured findings/citations, not raw uncontrolled blobs by default. KodeMemory may index research cache in the already defined research scope but must preserve untrusted provenance and DataGovernance labels. No research item enters validated/global memory solely because an LLM summarized it.

## Deliverables

Cache/orchestrator/context-memory adapters, schemas, invalidation/dedup tests, bounded-context tests and acceptance docs.

## Acceptance gates / Definition of Done

Cache replay preserves original retrieval metadata; source hash/version changes invalidate derived entries; untrusted flag survives Memory/Context round-trip; token/context limits respected; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, run IDs, cache manifest hashes and context-selection fixture evidence.

## Rollback / recovery

Drop derived cache/index entries; primary source artifacts remain independently recoverable.

## Risks and regression traps

Cache poisoning, trust laundering through summaries, stale embeddings, citation loss, context explosion.

## Manual intervention

**NONE**.

---

# R7.10 — CLI + KodeStudio Research UX

## Objective and rationale

Expose R7 through usable structured commands and the frozen KodeStudio Research surface without bypassing permissions, provenance or uncertainty semantics.

## In scope

CLI research commands for query/fetch/show/cache/status/media capability; KodeStudio Research panel with source filters, version/freshness badges, citations, suspicious-content warning, blocked/unavailable states and cancel action; no secret display.

## Out of scope

General browser UI, arbitrary terminal, credential editor exposing values and R8+ asset workflows.

## Detailed implementation plan

UI calls the same research service APIs as CLI. Network/media actions flow through Guardian/permissions and can be cancelled. Result views show source class, locator, retrieved/published/version metadata and trust warnings. Copy/export operations preserve citations and provenance.

## Deliverables

CLI handlers, KodeStudio Research widgets/models, UI tests/smokes, accessibility/localization hooks and acceptance docs.

## Acceptance gates / Definition of Done

Windows UI Smoke SUCCESS; keyboard navigation/focus intact; pseudo-localization does not break panel; cancellation works; secrets absent; blocked/unknown/stale visually distinct and not mislabeled PASS/current; R0/Python/UI SUCCESS.

## Validation and evidence

Exact SHA, workflow run IDs, UI smoke evidence and representative redacted result JSON.

## Rollback / recovery

Remove/disable Research UI/CLI routes while retaining lower-level research data APIs.

## Risks and regression traps

UI freezing on network/media work, exposing secret values, status color without text, citation links losing source identity.

## Manual intervention

**NONE**.

---

# R7.11 — Adversarial hardening + R7 integrated acceptance

## Objective and rationale

Close R7 with cross-source prompt-injection/security regression tests and a machine-readable integrated acceptance record tied to exact implementation heads and subdivision acceptance evidence.

## In scope

Cross-source malicious fixtures; SSRF/redirect/path/process/secret/cancellation tests; source/version conflict tests; missing/blocked/N/A/unknown semantics; integrated R7 acceptance JSON with per-subdivision accepted head/manual state/source acceptance doc/SHA-256; repository-integration validator; R6 Health/Regression/TechnicalDebt/AppSecurity/BOM review for new dependencies/helpers.

## Out of scope

R16 full red-team/beta hardening and unrelated future-phase acceptance.

## Detailed implementation plan

Create `R7_INTEGRATED_ACCEPTANCE.json` only after R7.1–R7.10 are accepted. Validator recalculates source-document hashes and fails closed on missing accepted head, unsatisfied REQUIRED/triggered CONDITIONAL manual gate, missing evidence, wrong source SHA or altered derived digest. Injection fixtures must prove external text cannot cause tool execution, permission escalation, secret exfiltration or policy bypass.

## Deliverables

Adversarial fixtures/tests, dependency/helper security review, integrated acceptance schema/report, repository-integration test, final R7 status/continuity normalization.

## Acceptance gates / Definition of Done

All R7.1–R7.11 acceptance docs PASS; R7.7 REQUIRED manual evidence satisfied; any triggered R7.4/R7.6/R7.11 conditional evidence satisfied; R0 Repository Guard, Python Core full jobs and KodeStudio UI Smoke SUCCESS on exact final implementation head; R6.12 major-patch gate applied if classification requires it; integrated validator PASS; normalization merged; only then R7 becomes COMPLETE.

## Validation and evidence

Exact accepted head, all authoritative workflow run IDs, manual evidence summaries, integrated report digest and normalization merge SHA.

## Rollback / recovery

Use existing SafeChange/Backup/Recovery/Audit primitives and R6.12 rollback gate for any major patch; remove new network/provider capability by adapter disablement without mutating user source data.

## Risks and regression traps

False PASS from skipped live/manual evidence, hash self-trust, conditional gate silently ignored, security fixtures testing only regex patterns rather than end-to-end tool isolation, provider/dependency drift.

## Manual intervention

**CONDITIONAL** — triggered only if final acceptance needs a live external-provider probe unavailable to hosted CI beyond the already REQUIRED R7.7 local gate. Any trigger must be documented before execution with exact read-only command, expected output, failure recovery and redacted evidence requirements. Silence never satisfies it.

## Phase completion rule

R7 is COMPLETE only when every subdivision listed above is COMPLETE with authoritative evidence, every REQUIRED and triggered CONDITIONAL manual gate is satisfied, `R7_INTEGRATED_ACCEPTANCE.json` validates against exact acceptance-document bytes/heads, final hosted CI is successful and plan/status/continuity agree on normalized `main`.

## Ongoing maintenance rule

Update this file and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, recovered defects or phase ordering changes. Architecture/foundation changes require an ADR.

## Planning-PR acceptance

This planning PR is documentation-only and does not implement R7.1. It is accepted only if:

1. `R7_PLAN.md` exists and contains the complete frozen R7.1–R7.11 structure;
2. continuity is synchronized and still says R7.1 has NOT started;
3. R0 Repository Guard succeeds;
4. Python Core succeeds for all required jobs;
5. KodeStudio UI Smoke succeeds;
6. all checks correspond to the exact final planning head;
7. the PR is merged to `main` without bypassing a failed/missing required gate.

After that merge, and only after it, the next authorized action is R7.1 implementation.