# V2.5 — Cross-workspace orchestration

Status: **PLANNING UNDER QUALIFICATION**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Planning base: `4e049eb10b9781c14eb3e81a2c027575c26dbaf1`  
Public distribution boundary: `v1.1.0-rc8`

## 1. Goal

V2.5 adds governed orchestration across multiple Kodepoia project workspaces without weakening the isolation, authority, provenance, tool-policy or evidence contracts already accepted in R1-R20 and V2.1-V2.4.

The user must be able to coordinate work that spans several projects while retaining explicit visibility of:

- which workspace owns each task;
- which other workspace supplied context;
- which data crossed a workspace boundary;
- which tool/effect is requested at the destination;
- whether an action is read-only or mutating;
- which approvals are still required;
- what exact evidence was produced;
- whether execution is running, blocked, cancelled, failed or complete.

V2.5 is orchestration over existing Kodepoia services. It must not create a second Project Knowledge engine, second KodeCode tool engine, second Model Lab, second project/session manager or ungoverned process launcher.

## 2. Existing authority to reuse

V2.5 must reuse rather than replace:

- `kodestudio.project_sessions` for validated Kodepoia project roots and active/recent project identity;
- Project DNA and project lineage as project-owned configuration;
- `ProjectWorkspaceContextSession` for project-scoped governed context;
- Project Knowledge, semantic retrieval and Context Builder provenance/trust/citation rules;
- KodeCode tool policies and their READ/WRITE effects;
- WorkspaceBoundary for filesystem/project confinement;
- ResearchGuard and KodeSecrets for untrusted-data and secret boundaries;
- ProcessSandbox and KillSwitch for process execution/cancellation;
- R16 memory integrity/quarantine rules;
- V2.3 Model Lab governance and V2.4 accelerator/distributed truth;
- KodeStudio accessibility/localization patterns;
- exact-head evidence and immutable acceptance lineage.

The existing `kodepoia.orchestrator` namespace is the implementation home for typed orchestration contracts. It is not permission to expose raw shell, unrestricted filesystem discovery or model-controlled process surfaces.

## 3. Workspace identity and isolation

Every orchestration participant is an explicit Kodepoia project workspace.

A workspace identity must bind at least:

- a canonical validated project root;
- an opaque/stable workspace ID;
- the project scope used by governed knowledge/context/memory;
- Project DNA identity/digest where present;
- current project/session state needed by the requested operation.

Rules:

- no global workspace may substitute for a project workspace;
- no workspace may impersonate another by path aliases, symlinks, case tricks or user/model text;
- discovery is limited to explicitly opened/recent/selected Kodepoia projects; V2.5 must not recursively scan arbitrary disks for projects;
- source and destination workspace identities must be distinct when a cross-workspace boundary is claimed;
- a destination operation is authorized only by the destination workspace's own policies and state;
- source workspace context never grants destination mutation authority.

## 4. Workspace relationship graph

V2.5 may expose an explicit relationship graph between selected workspaces.

Relationship metadata is descriptive and bounded. It may express facts such as:

- depends-on;
- produces-for;
- consumes-from;
- shared-contract;
- shared-asset;
- parent/companion project.

Relationship creation must be explicit. Inference from filenames, chat text, model output, repository similarity or filesystem proximity may be shown as a suggestion but cannot become accepted relationship authority without confirmation.

The graph must be deterministic, project-scoped and serializable without credentials or unrestricted host paths beyond the validated project identities already held by Kodepoia.

## 5. Cross-workspace context projection

Cross-workspace context is a bounded handoff, not shared global memory.

A context/handoff packet must bind:

- source workspace identity;
- destination workspace identity;
- source context snapshot digest;
- selected source records/artifacts;
- citations/provenance/trust classes;
- freshness/version metadata;
- purpose/task binding;
- packet digest;
- data-only authority marker.

Project Knowledge, Research Packs, memory, retrieved context and model text remain **data only**. Crossing a workspace boundary cannot upgrade trust or authority.

The destination must be able to inspect what arrived before using it. Omitted, stale, revoked, quarantined or tampered source material must remain visibly omitted/rejected.

No hidden cross-project memory store is authorized.

## 6. Orchestration plan and task graph

An orchestration plan is a typed deterministic DAG of bounded tasks.

Each task must bind:

- task ID;
- owning workspace;
- optional source workspaces;
- declared goal;
- dependencies;
- requested Kodepoia surface/service;
- requested effect class;
- input/handoff digests;
- expected output/evidence class;
- approval state;
- lifecycle state.

Model-generated text may propose task descriptions, but it may not directly set:

- filesystem permission;
- arbitrary command/argv;
- arbitrary environment variables;
- rendezvous/network endpoints;
- package-install requests;
- credentials;
- release/TUF authority;
- registry/model promotion authority.

Task dependency cycles must fail closed. Missing dependency evidence must block downstream tasks.

## 7. Routing and specialists

V2.5 may route a task to an existing Kodepoia surface or specialist only through a fixed typed catalog.

Routing must be based on explicit capability/project intent and must remain inspectable.

No dynamic Python import, arbitrary executable selection, shell command, model-provided module name or network endpoint may be created from task text.

Routing decisions must preserve:

- requested vs observed capability truth;
- project/platform/engine constraints;
- KodeCode tool-policy effects;
- Model Lab promotion/training boundaries;
- existing specialist trust boundaries.

## 8. Mutating handoffs and approval

Cross-workspace mutation is never implicit.

A mutating destination task requires:

1. validated destination workspace identity;
2. accepted task-plan lineage;
3. accepted handoff/context lineage;
4. destination-owned tool/service preflight;
5. explicit destination mutation preview;
6. explicit user confirmation for the mutating action;
7. execution through the destination's existing bounded service;
8. post-action evidence tied to the same task and workspace.

Read-only orchestration may aggregate status/evidence without mutation approval.

Approval for one task must not authorize sibling or later tasks automatically.

A source workspace can request work; it cannot approve protected destination actions on behalf of the user.

## 9. Concurrency and conflict control

V2.5 may execute independent read-only or non-conflicting tasks concurrently, but concurrency is not itself an authority grant.

The orchestration layer must:

- prevent conflicting concurrent writes to the same bounded target;
- surface workspace/task locks or equivalent conflict state;
- cancel dependent work when a prerequisite fails or is cancelled;
- never treat partial task completion as whole-plan success;
- preserve deterministic task/evidence ordering in persisted records;
- use KillSwitch-compatible cancellation for any launched process group.

The first implementation need not maximize parallelism. Correct isolation, provenance and recovery take priority.

## 10. Failure, cancellation and recovery

Required lifecycle states include at least:

- proposed;
- awaiting_approval;
- ready;
- running;
- blocked;
- cancelled;
- failed;
- completed.

Recovery must bind the original:

- plan digest;
- task ID;
- source/destination workspace identities;
- task dependencies;
- input/handoff digests;
- requested service/effect;
- approval/evidence lineage.

Recovery must fail closed if workspace identity, dependency graph, tool policy, protected target or required input evidence changed incompatibly.

Cancellation must stop downstream scheduling and must not manufacture completion evidence.

## 11. KodeStudio UX

KodeStudio must expose a dedicated orchestration workspace that makes cross-workspace truth visible.

At minimum the UX must show:

- selected workspaces and relationship graph/list;
- source and destination for each task;
- task DAG/dependencies;
- requested service/effect;
- context/handoff provenance and digest;
- approval requirements;
- lifecycle state;
- current blocker/diagnostic;
- evidence/output references;
- cancellation/recovery controls where applicable.

The UI must distinguish read-only aggregation from destination mutation.

Empty/degraded states are first-class:

- no other project selected;
- project missing/invalid;
- relationship not confirmed;
- context unavailable/stale/quarantined;
- capability unavailable;
- task blocked on approval;
- conflicting write;
- cancelled plan;
- incompatible recovery.

No UI state may claim success from a fixture, stale evidence or partial completion.

## 12. Security and trust boundaries

V2.5 preserves all accepted boundaries:

- WorkspaceBoundary remains destination-project authoritative;
- ResearchGuard keeps untrusted/source/model content data-only;
- KodeSecrets prevents credential serialization or prompt exposure;
- ProcessSandbox/KillSwitch remain the only bounded process boundary;
- project-scoped memory cannot silently become global or cross-project memory;
- no arbitrary shell/argv/env/package-install/rendezvous surface;
- no silent network/provider enablement;
- no hidden project discovery;
- no release/TUF/updater mutation;
- no R20 reopening or R20.7.

Cross-workspace orchestration is coordination, not privilege composition. Combining two limited workspaces must never produce greater authority than either workspace explicitly grants.

## 13. Persistence and evidence

Persisted orchestration records must be versioned and integrity-verifiable.

Evidence must be sufficient to reconstruct:

- exact source/destination identities;
- exact plan/task lineage;
- exact approved inputs;
- exact output/evidence references;
- task state transitions;
- cancellation/recovery lineage.

Secrets, credentials, raw unrestricted host environment and unrelated project data must not be serialized.

Historical evidence is immutable. A retry/recovery creates new evidence linked to the prior attempt rather than rewriting prior truth.

## 14. Deterministic CI versus live dependencies

Mandatory V2.5 acceptance must be deterministic and require no live Kaggle, external model hub, arbitrary network access or private credentials.

Fixtures may prove orchestration mechanics only. They cannot be presented as live provider/model/release evidence.

Any existing provider-specific truth continues to use its own accepted V2.1-V2.4 gates.

## 15. Frozen subdivisions

### V2.5.1 — Workspace registry, identity and relationship graph

Implement typed cross-workspace identities and explicit relationships over validated Kodepoia projects.

Includes:

- bounded selected-workspace registry;
- stable workspace identity and project-scope binding;
- relationship graph;
- duplicate/path-alias/symlink/cross-scope rejection;
- read-only KodeStudio workspace inventory.

Does not include task orchestration or destination mutation.

### V2.5.2 — Cross-workspace context handoff and provenance

Implement explicit data-only context/artifact handoff packets.

Includes:

- source/destination binding;
- governed context snapshot reuse;
- citations/trust/freshness/version visibility;
- packet digest and tamper rejection;
- explicit include/exclude;
- no global/shared memory promotion.

Does not include mutating task execution.

### V2.5.3 — Orchestration plan, dependency DAG and routing

Implement typed orchestration plans and task DAGs.

Includes:

- deterministic DAG validation;
- task/workspace ownership;
- fixed service/specialist routing;
- capability/effect visibility;
- dependency/blocker propagation;
- plan preview.

Does not include automatic protected mutations.

### V2.5.4 — Governed execution, approval, cancellation and recovery

Execute approved tasks through existing destination-owned services.

Includes:

- explicit mutation preview/confirmation;
- destination tool-policy enforcement;
- conflict control;
- bounded concurrency;
- cancellation and dependent-task blocking;
- lineage-safe recovery.

No raw shell/argv/env/package surface is authorized.

### V2.5.5 — KodeStudio orchestration workspace and operational history

Provide the integrated user workflow.

Includes:

- workspace/relationship management;
- task DAG/status;
- handoff inspection;
- approval controls;
- evidence/output timeline;
- cancellation/recovery UX;
- EN/FR/qps-ploc and accessibility.

### V2.5.6 — Cross-workspace hardening and integrated acceptance

Adversarially prove the full V2.5 chain.

Coverage includes:

- cross-project path/symlink/identity confusion;
- context authority spoofing;
- stale/revoked/tampered handoffs;
- dependency cycles/missing evidence;
- malicious routing/service/tool text;
- unauthorized destination writes;
- concurrent write conflicts;
- cancellation/orphan/partial-success handling;
- incompatible recovery;
- project deletion/move between planning and execution;
- secret leakage;
- deterministic UI degraded states;
- exact-head Ubuntu/Windows acceptance.

Definition of done: Kodepoia can coordinate bounded work across explicit project workspaces while preserving each workspace's independent authority, provenance and mutation boundaries.

## 16. Planning and implementation discipline

Every V2.5 subdivision must:

1. re-fetch live `main` and current authorities;
2. branch from the exact live SHA;
3. modify only the authorized subdivision;
4. reuse accepted services instead of creating parallel engines;
5. add deterministic tests and exact-head acceptance evidence;
6. invalidate all prior-SHA results after any implementation commit;
7. read exact failing logs before correction or rerun;
8. merge only after all required workflows succeed on the unchanged exact head;
9. use `expected_head_sha` protection;
10. post-merge normalize before authorizing the next subdivision.

## 17. Release boundary

The user has explicitly required that the next public release wait until V2 is completely finished.

Therefore:

- no V2.5 step authorizes a public release;
- `v1.1.0-rc8` remains the public reference during V2.5;
- V2.6 remains the dedicated V2 hardening and next-public-Windows-release phase;
- release/tag/installer/TUF/updater mutation remains unauthorized until V2.6 authority explicitly permits it;
- V2.6 implementation must not begin until V2.5.6 is complete, merged and post-merge normalized.

## 18. Planning definition of done

V2.5 planning is complete only when:

- this planning contract is exact-head qualified;
- all six subdivisions and their boundaries are frozen;
- existing reuse points are explicit;
- workspace identity/isolation is explicit;
- cross-workspace context remains data-only;
- task DAG/routing/effect semantics are explicit;
- destination mutation approval is explicit;
- concurrency/cancellation/recovery semantics are explicit;
- KodeStudio UX and degraded states are explicit;
- deterministic CI boundaries are explicit;
- release/TUF/R20 boundaries are explicit;
- planning PR is merged with `expected_head_sha`;
- post-merge normalization authorizes **V2.5.1 only**.

Until that normalization is complete, no V2.5 implementation subdivision is authorized.
