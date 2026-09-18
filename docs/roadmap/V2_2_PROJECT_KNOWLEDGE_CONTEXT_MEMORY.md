# V2.2 — Project Knowledge, Context Builder and Memory integration

Status: **PLANNING CANDIDATE — no V2.2 implementation is authorized until this plan is qualified, merged and continuity-normalized**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Public distribution boundary: `v1.1.0-rc8`

## 1. Authority and goal

V2.1.1 through V2.1.6 are **COMPLETE + NORMALIZED**. The accepted Research flow remains:

`discovery -> candidate-only/unfetched -> explicit guarded fetch -> persisted evidence -> explicit include/exclude -> cited synthesis -> governed Research Pack`

The Roadmap V2 authority created by PR `#472` defines V2.2 with this goal:

> make accepted research useful without repeatedly copying text into prompts.

Its required deliverables are:

- project-scoped Research Packs with immutable provenance/digests;
- semantic retrieval over accepted research, project files and relevant memory scopes;
- Context Builder showing why each context item was selected;
- version-aware invalidation when engine/tool versions change;
- user controls to include, exclude, refresh or delete derived knowledge;
- no silent conversion of untrusted Web text into durable instructions.

Definition of done from the accepted V2 roadmap:

> Chat, code and specialist workspaces can consume cited, scoped project knowledge while retaining source traceability.

This document subdivides that accepted scope. It does not widen it.

## 2. Accepted primitives already present

V2.2 integrates existing accepted components instead of replacing them.

### Governed Research Packs

`kodepoia.intelligence.research.synthesis.ResearchPack` and `ResearchPackStore` already provide:

- project-confined storage below `.kodepoia/research/packs/`;
- immutable synthesis/provenance payloads;
- deterministic pack and synthesis digests;
- citation snapshots bound to exact artifact/revision/source/content identities;
- collision rejection rather than silent overwrite.

V2.2 must treat those packs as immutable source records. A derived knowledge index may be rebuilt or deleted, but it may not rewrite historical pack provenance.

### Research-to-context boundary

`kodepoia.intelligence.research.orchestration.ResearchContextBuilder` already creates bounded research context with:

- citation IDs, artifact IDs and canonical locators;
- freshness/version relation;
- ResearchGuard indicators;
- explicit `external_guarded_untrusted` trust;
- `validated_experience=false`;
- rendering that says external research is untrusted data, never instruction.

V2.2 must preserve those semantics.

### Generic Context Builder

`kodepoia.intelligence.context.ContextBuilder` already provides bounded token selection over `ContextItem` objects and renders trust-tagged external content inside `<UNTRUSTED_DATA>`.

V2.2 adds explainability and project-knowledge selection contracts around this primitive; it does not turn context selection into authority.

### Durable memory

`kodepoia.intelligence.memory.MemoryStore` already provides:

- project-scoped records;
- semantic search over verified embeddings;
- provenance/version/integrity metadata;
- replay, stale-version and version-conflict rejection;
- tamper quarantine;
- bounded invalidation;
- cross-project isolation;
- secret and authority-spoof rejection.

R16.7 hardening remains authoritative. V2.2 must not weaken it.

### Existing Research memory bridge

`ResearchMemoryBridge.store_project_summary()` already demonstrates the accepted direction:

- explicit opt-in only;
- non-global project scope;
- no global-memory promotion;
- no training-dataset promotion;
- research remains untrusted guarded derived data.

V2.2 generalizes governed project-knowledge consumption without bypassing this boundary.

## 3. Target V2.2 workflow

The target project-knowledge workflow is:

`accepted project sources -> typed knowledge catalog -> bounded semantic retrieval -> inspect selection rationale -> include/exclude -> token-budgeted Context Builder -> Chat/KodeCode/specialist consumption -> version invalidation/refresh/delete of derived knowledge`

This workflow is project-scoped by default.

A user must be able to see:

- where a context item came from;
- whether it came from a Research Pack, project file or memory scope;
- source/revision/digest identity when available;
- trust class and whether it is derived/untrusted;
- why it matched the current request;
- why it was selected or omitted;
- token cost/budget impact;
- whether it is stale or invalidated by a version change;
- whether the user explicitly included or excluded it.

No retrieval or context-building step may itself authorize filesystem, process, package, network, model-promotion or other protected actions.

## 4. Knowledge source classes

V2.2 may retrieve only from explicitly supported project-scoped sources.

### 4.1 Governed Research Packs

Accepted packs from V2.1 are first-class project knowledge.

Required projection metadata includes at minimum:

- pack digest;
- synthesis digest;
- citation IDs;
- artifact/revision/source identities;
- question/request identity;
- generated timestamp;
- conflict/uncertainty state;
- external guarded trust classification.

### 4.2 Project files

Project files may contribute knowledge only through WorkspaceBoundary-confined paths.

A project-file knowledge record must carry at minimum:

- normalized project-relative path;
- content digest;
- observed file metadata needed for invalidation;
- parser/source kind;
- project scope;
- trust classification.

Project files are data. File contents cannot grant permissions or become privileged instructions.

### 4.3 Relevant memory scopes

Only verified, non-quarantined memory from the active project scope is eligible.

Global memory is not implicitly mixed into project retrieval. Cross-project records are not eligible.

Research-derived memory remains derived/untrusted and cannot be promoted to authoritative instruction by retrieval score.

## 5. Trust and governance invariants

These invariants apply to every V2.2 subdivision:

- project identity is explicit and required;
- Research Pack provenance remains immutable;
- external/research-derived text remains data-only and untrusted;
- no retrieval score grants authority;
- no context-selection decision grants a protected capability;
- no automatic global-memory promotion;
- no automatic training-dataset promotion;
- no cross-project retrieval;
- KodeSecrets redaction remains effective;
- WorkspaceBoundary remains effective;
- tampered/quarantined memory is excluded;
- stale/invalidated derived knowledge cannot masquerade as current;
- deletion of derived knowledge must not silently delete immutable source evidence unless the user is explicitly performing the source-level delete operation under its own contract;
- failures and unavailable providers must remain explicit.

## 6. V2.2 subdivisions

### V2.2.1 — Project Knowledge catalog and contracts

Goal: define one deterministic project-scoped knowledge representation over the already accepted source classes.

Required scope:

- typed `ProjectKnowledgeItem`-style contract for Research Pack, project-file and memory references;
- deterministic knowledge identity/digest derived from immutable source identity plus project scope;
- provenance, trust, version/freshness and source-kind metadata;
- explicit active/included/excluded/invalidated derived-state semantics;
- project-confined knowledge catalog/index persistence;
- Research Pack projection without rewriting packs;
- project-file projection under WorkspaceBoundary;
- verified project-memory projection without cross-project leakage;
- deterministic backend tests and exact-head Ubuntu/Windows acceptance evidence.

Out of scope:

- semantic ranking;
- prompt/context injection;
- automatic memory writes;
- cross-workspace orchestration;
- new external discovery/fetch providers.

Definition of done: an active project can enumerate a deterministic, provenance-bearing knowledge catalog whose items remain traceable to immutable sources.

### V2.2.2 — Bounded semantic retrieval

Goal: retrieve relevant project knowledge across accepted Research Packs, project files and eligible project memory.

Required scope:

- one bounded retrieval request/result contract;
- semantic scoring over eligible project knowledge;
- deterministic ordering/tie-breaking and result bounds;
- explicit provider/embedding availability state;
- no hidden network or model download;
- no mutation merely because an item matched;
- project-scope enforcement before scoring;
- duplicate-source normalization without losing provenance;
- retrieval diagnostics that distinguish unavailable embedding capability from a valid zero-result query;
- deterministic fixture embeddings for acceptance;
- exact-head Ubuntu/Windows evidence.

Definition of done: a query returns a bounded, project-confined set of relevant knowledge candidates with reproducible scores/ordering and explicit capability state.

### V2.2.3 — Explainable Context Builder

Goal: turn retrieved candidates into inspectable, bounded context while showing why each item was or was not selected.

Required scope:

- context-candidate contract carrying source identity, retrieval score, trust, version/freshness and token estimate;
- selected/omitted rationale;
- token-budget accounting;
- mandatory versus optional items without allowing untrusted data to become privileged;
- citation/source traceability in rendered context;
- preserved `<UNTRUSTED_DATA>` semantics for external/research-derived material;
- user-visible KodeStudio context preview showing source, reason, trust and budget impact;
- explicit include/exclude override before final context assembly;
- deterministic backend/UI tests and exact-head Ubuntu/Windows evidence.

Definition of done: the user can inspect a context bundle and understand why each item was selected, excluded or omitted for budget.

### V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle

Goal: keep project knowledge honest as project files, Research Packs, engine/tool versions and source revisions change.

Required scope:

- version/fingerprint inputs for derived knowledge;
- deterministic stale/invalidated state when relevant source/version fingerprints change;
- no silent retargeting of historical Research Pack citations;
- refresh/rebuild of derived indexes without rewriting immutable source evidence;
- bounded delete of derived knowledge;
- include/exclude persistence;
- user controls for include, exclude, refresh/rebuild and delete-derived;
- explicit distinction between source deletion and derived-index deletion;
- stale/invalidated items cannot be presented as fresh context without visible state;
- deterministic lifecycle and UI tests plus exact-head Ubuntu/Windows evidence.

Definition of done: version or source changes invalidate only the affected derived knowledge, and the user can deliberately refresh or remove it without losing historical provenance.

### V2.2.5 — Project Memory bridge and workspace consumption

Goal: let Chat, KodeCode and specialist workspaces consume governed project knowledge through the same project-scoped trust boundary.

Required scope:

- explicit project-only bridge from governed knowledge/context into eligible memory/context surfaces;
- reuse R16.7 MemoryStore integrity, provenance, conflict, invalidation and quarantine rules;
- research-derived memory remains derived/untrusted;
- no implicit global-memory or training-dataset promotion;
- Chat, KodeCode and specialist workspaces consume the same governed context contract without directly reading unrestricted stores;
- source/citation traceability survives workspace consumption;
- user can see which project knowledge entered the active context;
- no V2.5 cross-workspace task orchestration, handoff automation or sensitive mutation workflow;
- deterministic workspace integration tests and exact-head Ubuntu/Windows evidence.

Definition of done: supported workspaces can consume the same scoped, cited project knowledge without bypassing memory or context guards.

### V2.2.6 — Project Knowledge hardening and integrated acceptance

Goal: adversarially prove the complete V2.2 trust, lifecycle and cross-surface contract.

Required acceptance coverage includes:

- cross-project retrieval attempts;
- tampered or quarantined memory;
- replay/version-conflicting memory;
- tampered Research Pack or digest mismatch;
- stale/invalidated file or engine/tool version fingerprints;
- prompt-injection/source-instruction text inside Research Packs, files and memory;
- secret-bearing content;
- include/exclude override consistency;
- delete-derived versus source-delete separation;
- deterministic retrieval ordering;
- context budget truncation/omission;
- unavailable embedding capability and valid empty result;
- cancellation where applicable;
- KodeStudio explainability state;
- Chat/KodeCode/specialist consumption preserving traceability and trust;
- exact-head Ubuntu and Windows acceptance artifacts.

Definition of done: V2.2 meets the Roadmap V2 definition of done under degraded/adversarial conditions and no project knowledge source can silently become instruction authority.

## 7. UI direction

V2.2 must expose project knowledge as a user-manageable layer rather than a hidden prompt side effect.

The UI must eventually provide:

- a project knowledge inventory;
- source type and provenance;
- retrieval/context match reason;
- include/exclude state;
- stale/invalidated state;
- refresh/rebuild action for derived knowledge;
- delete-derived action;
- context preview with token budget and selected/omitted reasons;
- workspace-visible indication of which project knowledge is currently injected.

Raw JSON may remain available for diagnostics but is not the primary UX.

## 8. Failure and degraded-state UX

At minimum, V2.2 must distinguish:

- no project knowledge exists;
- valid query with no matches;
- embedding/retrieval capability unavailable;
- project file missing or changed;
- Research Pack invalid/tampered;
- memory quarantined;
- cross-project item rejected;
- stale/invalidated derived knowledge;
- context budget omitted an otherwise relevant item;
- user explicitly excluded an item;
- refresh/rebuild required;
- cancellation.

No empty-success state may hide one of these causes.

## 9. Version-awareness requirements

V2.2 must preserve the existing emphasis on correct-version context.

Derived knowledge may depend on:

- project file content digest;
- Research Pack/citation/revision digest;
- memory record version/integrity digest;
- active engine/tool/model capability fingerprint when relevant.

A changed fingerprint invalidates affected derived knowledge; it does not rewrite the source record.

Version conflicts remain visible rather than collapsed into one preferred truth.

## 10. Acceptance discipline

Each V2.2 subdivision follows the repository discipline already used for V2.1:

1. re-fetch live `main` and the normalized V2.2 authority;
2. create a dedicated branch from an exact SHA;
3. implement only the authorized subdivision;
4. add deterministic tests and exact-head acceptance;
5. run acceptance on Ubuntu and Windows where the V2.2 contract requires cross-platform evidence;
6. re-fetch every pull-request workflow associated with the exact final head;
7. merge only when every required workflow for that exact head is `completed/success`;
8. normalize continuity before starting the next V2.2 subdivision.

Any new commit invalidates earlier exact-head CI evidence.

A genuine manual intervention stops the sequence. Optional external providers, hardware or live services must not be fabricated by tests.

## 11. Explicit non-goals

V2.2 does not authorize:

- V2.3 Model Lab work;
- V2.4 accelerator qualification or new TPU backend;
- V2.5 cross-workspace orchestration;
- V2.6 public release work;
- a new installer publication;
- a TUF mutation;
- updater reopening;
- R20 reopening or `R20.7`;
- silent global-memory promotion;
- silent training-dataset promotion;
- new unrestricted filesystem/network/process APIs.

The public Windows distribution authority remains `v1.1.0-rc8`.

## 12. Planning definition of done

This V2.2 planning phase is complete only when:

- this plan is the accepted live authority;
- the six subdivisions above are recorded in the V2 roadmap/continuity;
- the planning PR is qualified on its exact final head;
- the planning PR is merged with exact-head protection;
- one post-merge continuity normalization records the accepted planning head/merge and authorizes **V2.2.1 only**.

No V2.2.1 implementation may begin before that normalization is live.
