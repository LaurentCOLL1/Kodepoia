# Kodepoia — R16 detailed phase plan

**Phase:** R16  
**Roadmap title:** Hardening / Beta / v1.0  
**Status:** IN_PROGRESS
**Phase planning started:** 2026-08-31  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `b83c5cf0354f675e468e3ab37c2eefa66aaa9d56`  
**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.11 are COMPLETE + NORMALIZED. R16.12 is IN_PROGRESS from normalized `main` `270e022a03d7a596eedd27d8989b22278f18cbca` on dedicated branch `r16/12-representative-windows-desktop-application` after mandatory START-sync and before implementation. R16.13–R16.18 remain PLANNED. Manual NONE for R16.12 unsigned/core CI acceptance.

## Purpose and authority

R16 implements the frozen-roadmap capability **“Red-team prompt injection / repo malveillant / secrets / plugins / commandes destructrices / mémoire corrompue / recovery. Tests sur vrais projets Godot 2D/3D, vraie app Windows, ComfyUI, audio/voice et projet long terme.”**

The phase converts the already implemented Kodepoia v1.0 architecture into a defensible beta/release candidate. It does not redesign the product and does not treat a green happy-path suite as security evidence. R16 attacks the existing trust boundaries, proves fail-closed behavior under adversarial inputs and corrupted state, then validates the same boundaries on representative real project workflows before v1.0 release readiness is claimed.

This file is the exhaustive execution and recovery authority for R16. The subdivision list R16.1–R16.18 is frozen when the planning PR and its single planning continuity normalization are accepted. No subdivision may be silently added, removed, merged, split or renumbered. Scope/status/manual-state changes must update this plan and continuity in the same work cycle; architecture changes require an ADR when they cross the frozen v1.0 boundary.

## Permanent subdivision status synchronization rule

For every R16 subdivision:

1. **Start, before implementation:** prior normalized subdivisions are `COMPLETE + NORMALIZED`, the active subdivision becomes `IN_PROGRESS`, later subdivisions remain `PLANNED`; phase status/checkpoint and continuity are synchronized in the same work cycle.
2. **End, before final documentation/evidence re-gates:** the accepted active subdivision becomes `COMPLETE`; later subdivisions stay `PLANNED`; continuity is synchronized in the same work cycle.
3. A triggered manual gate uses truthful `BLOCKED` / `MANUAL_REQUIRED`, never synthetic `COMPLETE`.
4. Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status.
5. A stale subdivision index, stale phase status, mixed-SHA evidence, replayed evidence, evidence from a different fixture/project, or a security result not bound to the exact tested source is an acceptance blocker.
6. Every adversarial/security decision is fail-closed. Unknown trust, unknown provenance, unknown credential scope, unknown plugin/tool identity, unknown destructive impact, corrupted state without a validated recovery source, or incomplete red-team coverage means `DENIED`, `QUARANTINED`, `UNTRUSTED`, `RECOVERY_REQUIRED` or `INCONCLUSIVE`, never PASS.
7. Red-team fixtures MUST be synthetic, bounded and non-destructive. No acceptance test may use live secrets, real credential theft, uncontrolled malware, destructive host commands, or production targets.

## Phase objective

Deliver a deterministic, auditable, local-first hardening and beta capability that proves Kodepoia can:

- distinguish trusted instructions from untrusted repository, document, web, tool, plugin, memory and model content;
- resist direct and indirect prompt-injection attempts without granting untrusted content authority over policy, permissions or tool execution;
- inspect and quarantine malicious or suspicious repositories/workspaces before executable hooks, scripts, project metadata or generated instructions can gain authority;
- prevent secrets, credentials, private keys, tokens and protected project data from leaking through prompts, logs, reports, traces, tool arguments, subprocess environments or generated artifacts;
- keep plugin/MCP/tool discovery separate from tool trust, authorization and execution, with explicit capability scopes and least privilege;
- prevent destructive command execution, confused-deputy behavior and excessive agency through typed operations, bounded permissions, approvals and reversible SafeChange paths;
- detect, quarantine and recover from poisoned/corrupted memory or context without silently promoting the corrupted state into durable authority;
- prove KillSwitch, ProcessSandbox, backup, SafeChange and recovery behavior under injected faults, cancellation, partial writes and corrupted state;
- harden dependency, plugin, workflow and release supply chains with deterministic inventories, provenance and integrity evidence;
- validate Kodepoia on representative real Godot 2D and 3D projects rather than only synthetic unit fixtures;
- validate a real Windows desktop application workflow from workspace creation/edit/build/test/package through failure and rollback paths;
- validate representative ComfyUI generation/orchestration workflows while respecting local resource and trust boundaries;
- validate audio, TTS/voice and cinematic/media workflows with machine-verifiable outputs and governance boundaries;
- resume and evolve a long-lived project across repeated sessions, schema/version changes, backup/restore and interruption without continuity loss;
- expose resource, latency, concurrency, leak and failure diagnostics without leaking sensitive content;
- produce a v1.0 release candidate with bounded packaging/update/migration/rollback, documented limitations and truthful capability claims;
- close the phase with one integrated exact-head adversarial and representative-project acceptance authority that cannot pass through circular evidence.

## Explicitly out of scope

R16 does **not** authorize:

- changing the frozen v1.0 architecture merely to simplify acceptance;
- autonomous penetration testing of third-party or Internet targets;
- creation, deployment or execution of real malware, ransomware, credential stealers, persistence mechanisms or destructive payloads;
- storing real secrets in fixtures, logs, reports or repository history;
- bypassing user consent, repository permissions, OS security, provider policy, plugin/MCP authorization or existing R1 governance boundaries;
- allowing model output, repository text, README instructions, issue content, tool descriptions, plugin metadata or memory entries to become privileged policy merely because they are syntactically valid;
- treating a security scanner as proof that an application is secure;
- treating aggregate pass rate as sufficient when any critical security invariant fails;
- mandatory cloud infrastructure, paid external security service, external model API, public package registry or production deployment for core acceptance;
- mandatory dedicated GPU, microphone, speakers or signing certificate for core CI acceptance;
- silently installing system drivers, Godot, ComfyUI, CUDA/ROCm, audio drivers, plugins or untrusted binaries;
- public v1.0 publication, store submission, domain cutover, production signing or credential use without separately authorized user action;
- claiming hardware/provider/platform coverage that was not actually exercised.

## Current external security compatibility baseline — 2026-08-31

External security guidance is informative compatibility evidence, not a replacement for repository-owned contracts or the frozen architecture. Exact versions/dates and capability probes used by a subdivision must be captured in its evidence.

### OWASP GenAI / LLM application risks

R16 treats the OWASP 2025 LLM/GenAI risks as a threat taxonomy, especially prompt injection, sensitive-information disclosure, supply chain, data/model poisoning, improper output handling, excessive agency, vector/embedding weaknesses and unbounded consumption. Prompt injection is assumed possible even when instructions are hidden in otherwise valid content; therefore deterministic permission and tool boundaries, not prompt wording alone, remain authoritative.

Official references:

- https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
- https://genai.owasp.org/llm-top-10/

### NIST AI RMF / GenAI profile

NIST AI 600-1 is an informative cross-sector companion to AI RMF 1.0 for identifying and managing generative-AI risks across the lifecycle. R16 uses it to structure risk evidence and residual-risk documentation; it does not convert voluntary framework text into hidden product requirements.

Official reference:

- https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

### NCSC secure AI lifecycle guidance

The NCSC secure-AI guidance separates secure design, secure development, secure deployment and secure operation/maintenance. R16 maps threat modelling, supply-chain controls, secure defaults, incident/recovery handling, logging/monitoring and update safety to those lifecycle stages.

Official reference:

- https://www.ncsc.gov.uk/collection/guidelines-secure-ai-system-development/guidelines

### Model Context Protocol security baseline

MCP tools/resources/prompts are external capability surfaces, not trusted instructions. R16 requires explicit user control, data-access consent, tool trust boundaries, least privilege and secure authorization. When HTTP authorization is supported, token audience validation, secure token storage, HTTPS and PKCE are compatibility requirements; token passthrough is never treated as an acceptable shortcut.

Official references:

- https://modelcontextprotocol.io/specification/2025-11-25
- https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization

## Existing architectural touchpoints at the planning branch point

R16 hardens existing v1.0 components rather than inventing parallel security infrastructure. Primary touchpoints include:

- `src/kodepoia/core/guardian.py`, `permissions.py`, `sandbox.py`, `safe_change.py`, `backup.py`, `recovery.py`, `kill_switch.py`, `secrets.py`, `research_guard.py` and `audit.py`;
- `src/kodepoia/intelligence/memory.py` and research ingestion/orchestration under `src/kodepoia/intelligence/research/`;
- KodeCode parsing, patching, workspace and execution under `src/kodepoia/kodecode/`;
- KodeGodot project/edit/executor/runtime boundaries under `src/kodepoia/kodegodot/`;
- desktop workspace/persistence/IPC/packaging under `src/kodepoia/desktop/`;
- ComfyUI client/execution/workflow/resource boundaries under `src/kodepoia/comfyui/`;
- audio/TTS/voice/cinematic boundaries under `src/kodepoia/media/`;
- `src/kodepoia/quality/security.py`, privacy, patch gate, build, license/BOM and health authorities;
- existing project wizard/DNA, experience/tuning, backend and KodeStudio surfaces where untrusted content or privileged operations can cross subsystem boundaries.

## R16 cross-cutting security invariants

These invariants are phase-wide and cannot be waived by a subdivision-local PASS:

1. **Instruction/data separation:** untrusted content may inform reasoning but cannot override policy, user intent, permission state, tool contracts or system authority.
2. **Least privilege:** each operation receives only the minimum files, environment, credentials, network access and tool capability needed for the explicit task.
3. **No secret-as-context default:** secret values are resolved only at the narrow execution boundary that needs them and are redacted from durable evidence.
4. **Typed operations over shell text:** structured operations are preferred; generated shell/PowerShell arguments never bypass Guardian/PermissionSet/ProcessSandbox validation.
5. **Deny unknown destructive impact:** delete/overwrite/reset/force/recursive/system-wide operations are denied or require explicit bounded authorization and reversible evidence.
6. **Untrusted plugins/tools:** discovery metadata, descriptions, schemas and annotations do not establish trust. Identity, origin, requested capabilities and authorization are evaluated independently.
7. **Memory is evidence, not policy:** durable memory/context cannot grant permissions, change architecture, suppress security gates or silently rewrite project authority.
8. **Recovery before continuation:** detected corruption or partial write blocks downstream mutation until a known-good state is restored and verified.
9. **Bounded resource consumption:** CPU/RAM/VRAM/disk/process/network/time/concurrency limits fail closed before unbounded work begins.
10. **Exact-source evidence:** every acceptance artifact binds source SHA, fixture/project identity, policy/config digest, dependency/tool versions and verdict.
11. **Critical veto:** any critical confidentiality/integrity/availability invariant failure vetoes promotion regardless of aggregate score.
12. **Truthful capability claims:** `unavailable`, `not exercised`, `conditional` and `unsupported` remain valid outcomes; they are never rewritten as PASS.

## Evidence and acceptance model

Every R16 technical subdivision produces repository-owned machine-readable evidence with at least:

- exact source SHA and clean-tree assertion;
- subdivision and schema version;
- fixture/project identity and immutable digest;
- OS/runtime/tool/dependency versions relevant to the claim;
- policy/config/permission digest;
- enumerated attack/fault/workflow case IDs;
- expected and observed decision/action;
- sanitized diagnostics with explicit redaction assertions;
- rollback/recovery result when mutation is exercised;
- critical-veto field;
- final `PASS` / `FAIL` / `INCONCLUSIVE` / `UNAVAILABLE` status.

A report is invalid if it contains an unhashed live secret, depends on a different source SHA, silently skips a required critical case, reuses stale mutable workspace state, or cannot distinguish `not exercised` from `passed`.

## Manual-intervention policy

- Core R16 acceptance is CI-owned and must remain executable with repository fixtures on supported GitHub-hosted runners.
- Optional hardware/provider/live-environment claims may be `CONDITIONAL`; they do not block core acceptance unless that external capability itself is being claimed.
- If a conditional gate triggers, execution stops before the following subdivision and records the exact command, expected artifact, source SHA, environment prerequisites and acceptance criteria required from the user.
- No manual screenshot-only or prose-only evidence can replace a machine-readable core acceptance artifact.

## Frozen subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R16.1 | Threat model, adversarial corpus and red-team harness | COMPLETE + NORMALIZED | NONE |
| R16.2 | Prompt-injection and untrusted-content hardening | COMPLETE + NORMALIZED | NONE |
| R16.3 | Malicious repository/workspace quarantine and safe bootstrap | COMPLETE + NORMALIZED | NONE |
| R16.4 | Secrets, privacy and exfiltration hardening | COMPLETE + NORMALIZED | NONE |
| R16.5 | Plugin/MCP/tool trust, authorization and supply-chain boundary | COMPLETE + NORMALIZED | NONE |
| R16.6 | Destructive-command, excessive-agency and confused-deputy hardening | COMPLETE + NORMALIZED | NONE |
| R16.7 | Memory/context poisoning detection, quarantine and rebuild | COMPLETE + NORMALIZED | NONE |
| R16.8 | Fault injection, KillSwitch, backup and recovery drills | COMPLETE + NORMALIZED | NONE |
| R16.9 | Dependency/workflow/release supply-chain provenance hardening | COMPLETE + NORMALIZED | NONE |
| R16.10 | Representative real Godot 2D beta project | COMPLETE + NORMALIZED | NONE |
| R16.11 | Representative real Godot 3D beta project | COMPLETE | NONE |
| R16.12 | Representative real Windows desktop application | PLANNED | NONE |
| R16.13 | Representative ComfyUI beta workflow | PLANNED | CONDITIONAL |
| R16.14 | Representative audio/voice/cinematic beta workflow | PLANNED | CONDITIONAL |
| R16.15 | Long-term project durability, resume and upgrade soak | PLANNED | CONDITIONAL |
| R16.16 | Resource, concurrency, leak and diagnostics soak | PLANNED | NONE |
| R16.17 | v1.0 packaging, migration, rollback and release readiness | PLANNED | CONDITIONAL |
| R16.18 | Integrated adversarial + real-project RC acceptance | PLANNED | CONDITIONAL |

---

# R16.1 — Threat model, adversarial corpus and red-team harness

## Objective

Create the canonical R16 threat model and deterministic adversarial/fault harness before modifying defensive behavior, so later hardening can be measured against frozen attack IDs rather than self-authored happy paths.

## Scope

- trust-boundary inventory across prompts, repository/workspace, research/web documents, tools/plugins/MCP, memory, secrets, subprocesses, files, network, model/runtime, desktop, ComfyUI, Godot and media;
- attacker goals mapped to confidentiality, integrity and availability;
- synthetic adversarial corpus for direct/indirect injection, authority spoofing, malicious metadata, path traversal, symlink/junction abuse, secret bait, tool-description injection, memory poisoning, destructive command proposals, resource exhaustion and malformed/corrupted state;
- deterministic red-team/fault-runner contract and evidence schema;
- critical-case veto classification.

## Dependencies

Normalized R15 `main`; existing R1 security/governance, R6 quality/security, R7 research, R8 asset/vault and R15 experience/tuning authorities.

## Detailed implementation

1. Inventory every untrusted-to-privileged boundary and assign stable boundary IDs.
2. Define attacker capabilities without using live malware or real credentials.
3. Freeze attack/fault case IDs with payload digest, expected decision, affected invariant and severity.
4. Implement a fixture loader that rejects mutable/out-of-scope or secret-bearing fixture input.
5. Implement deterministic runner/report contracts with exact-source, case-set and policy digests.
6. Add mutation-free baseline mode to measure current behavior without granting red-team fixtures real host authority.
7. Add a coverage assertion that every frozen critical boundary has at least one positive and one negative case.

## Deliverables

- threat-model document/data contract;
- adversarial fixture corpus;
- red-team/fault runner and acceptance report schema;
- tests for fixture integrity, deterministic ordering, coverage and critical veto.

## Definition of done

All critical boundaries are enumerated and represented by immutable synthetic cases; the runner is deterministic on Ubuntu and Windows; attack content cannot escape the fixture sandbox; evidence binds exact SHA and case-set digest.

## Validation / proof

Dedicated R16.1 workflow plus fresh exact-head R0, full Python Core and KodeStudio UI Smoke. Negative controls must demonstrate that removing/bypassing the expected boundary causes the harness to fail rather than silently PASS.

## Rollback

Remove the R16.1 harness/fixtures/tests/workflow as one bounded feature set; no persistent project/user data migration is introduced.

## Risks

False confidence from incomplete cases; unsafe fixture design; accidental secret-like strings reaching scanners/logs; nondeterminism from platform path semantics.

## Manual intervention

**NONE.** Synthetic fixtures are authoritative.

## R16.1 END acceptance authority

- Normalized branch point: `main` `fcb8d3c532949ce8e8d728e6bb1171e7132af342`; clean START `e7b29e354610cef652b36f54f976010f18ab9c9b`; immutable technical source `c2fd7d63af9bea5a11d357ae324df214c1651c39`.
- Technical-source gates: R16.1 #3 / `33426065776` SUCCESS Ubuntu + Windows; R0 #2260 / `33426065732` SUCCESS Ubuntu + Windows; Python Core #2232 / `33426065658` SUCCESS 5/5; UI Smoke #2197 / `33426065644` SUCCESS.
- Semantic evidence identical cross-platform: acceptance `2b26d7095d0a89322c4ae3286f47b8bf420347a934ce03b98898b0a23db17c5f`; baseline `b8c75cf586b92be1767052e0607ecd9252f665b8f0b1d3427182590bf2470179`; negative control `6934fd90e7da7ce953c235f883c38ae724afefeb185d0ed48099bda2dbe68063`; corpus `faa7f8bafa48438351a7435c3a55946f0a42ab8695540935a070865659189a51`; case-set `8aca9cb7fd1f3cfe5445bebaee48569f7dbb21a63ca35567dc636a84f9c22963`; policy `bf9fc7cea89a07ed003829bef1d6e1d0de7670b217f9b3a2c96bbc9f0724139e`.
- Coverage is 14 critical boundaries / 28 immutable synthetic cases, one benign + one adversarial per boundary. Baseline is mutation-free with `security_claim=false`; negative control is FAIL with `critical_veto=true`; `secrets_exposed=false`; manual NONE.
- Technical-source artifacts: Linux `9770791161` archive SHA-256 `afdcfbbe1484423dd296663e2124577a5a944858c5df1d6c82159e4717c82c76`; Windows `9770836165` archive SHA-256 `95e63820eb9549b6a6c0d08ec550491acd80b825751b3bf2fa7868f7c447b895`.
- R16.1 is COMPLETE at END-sync. Fresh exact-END R16.1/R0/Python/UI re-gates are mandatory before protected merge; R16.2 remains PLANNED until post-merge normalization.

---

# R16.2 — Prompt-injection and untrusted-content hardening

## Objective

Prevent direct/indirect untrusted instructions from acquiring policy, permission, tool or mutation authority across repository, research, document, web, tool-output and model-output flows.

## Scope

Instruction/data labelling, trust metadata, prompt/context assembly, research/document ingestion, model/tool output handling, hidden/encoded injection variants, authority-spoofing and security-boundary regression tests.

## Dependencies

R16.1 frozen case set; `core/research_guard.py`; intelligence context/research; orchestrator/model boundaries; Guardian/PermissionSet.

## Detailed implementation

1. Introduce/extend explicit trust-origin labels through context assembly without relying on natural-language warnings alone.
2. Ensure untrusted content is quoted/structured as data and cannot alter system/user policy state.
3. Add deterministic checks preventing untrusted content from granting tool permissions, suppressing confirmation, widening filesystem/network scope or rewriting continuity/roadmap authority.
4. Treat tool/model/research outputs as untrusted until validated by the consuming contract.
5. Add encoded, nested, role-spoofed, README/comment, retrieved-document and tool-output injection cases.
6. Ensure malicious content remains inspectable/auditable after safe normalization without executing embedded directives.
7. Add fail-closed behavior when trust provenance is missing or contradictory.

## Deliverables

Trust-origin contracts; hardened context/research/orchestration paths; adversarial acceptance fixtures/tests; sanitized decision evidence.

## Definition of done

All R16.1 critical prompt-injection cases are denied/contained as expected; benign data remains usable; no untrusted payload can mutate permission/policy state or directly trigger privileged tools.

## Validation / proof

Exact-head adversarial suite on Ubuntu/Windows plus R0/Python/UI. Include false-positive controls using benign README/code/document instructions that remain readable but non-authoritative.

## Rollback

Revert trust-propagation and consuming-boundary changes together; no durable schema migration without versioned fallback.

## Risks

Overblocking legitimate project instructions; provenance loss across serialization; unsafe normalization; prompt-only mitigation mistaken for authorization.

## Manual intervention

**NONE.**

## R16.2 END acceptance authority

- Normalized branch point: `main` `ad7ec8339ea3e61fefa29fad6693a0e476b6bc58`; clean START `c3095e36bde1d580f4496397c280304384157aa9`; immutable technical source `6d4aee8947f2350a16e2316aae217030195cb68f`.
- Technical-source gates: R16.2 #12 / `33441078478` SUCCESS Ubuntu + Windows; R0 #2270 / `33441078505` SUCCESS Ubuntu + Windows; Python Core #2242 / `33441078446` SUCCESS 5/5; UI Smoke #2207 / `33441078170` SUCCESS.
- Cross-platform acceptance content is byte-identical: JSON SHA-256 `daa1714932a36fb24ba2050e607c99e48d6d5f7fe9b3ef8eb72c57f6667b0ced`; semantic `17e3d997642f3d52e0f3e6fc2c792ef91d83d8566876596936630c249198a434`; policy `97878fe69267c6fa6f2266d5bdcc87793385a315ca0b18d699d773fc31a2b990`; canonical R16 corpus `faa7f8bafa48438351a7435c3a55946f0a42ab8695540935a070865659189a51`; R16 case-set `8aca9cb7fd1f3cfe5445bebaee48569f7dbb21a63ca35567dc636a84f9c22963`; targeted prompt/ingestion set `138328e20a43b6501f2413eb248bd4de29fadbc98a67ac975893ababf0d087ca`; supplemental R16.2 set `d2a31a206689f51668609812b32c4c9d7b3f247de7ac3dedeb29fabb7ea1ab8e`.
- Acceptance exercises 18/18 cases with `security_claim=true`, `critical_veto=false`, synthetic-only fixtures, no live secrets and no destructive host actions. Linux artifact `9776303161` archive SHA-256 `9a248e5e71cb7ce92a7b06b67a3055d8956dda672ec858d043c191f520ba5bf7`; Windows artifact `9776290305` archive SHA-256 `39d1ea79415a7d15095461b6bd2f1c01eb28e8f8d0ab3c45d022a3c7c8b2cd7e`.
- Compatibility regression found by full Python Core was corrected before acceptance: `ResearchGuard` retains its public R7.1 guard/schema version `1`; R16.2 trust provenance is additive and does not force a legacy schema migration.
- Manual NONE. R16.2 is COMPLETE at END-sync. Fresh exact-END R16.2/R0/Python/UI re-gates are mandatory before protected merge; R16.3 remains PLANNED until the implementation merge and its unique post-merge continuity-only normalization complete.

---

# R16.3 — Malicious repository/workspace quarantine and safe bootstrap

## Objective

Make opening, indexing, analyzing or bootstrapping an unknown repository/workspace safe before any repository-controlled executable behavior receives authority.

## Scope

Repository discovery, project wizard/workspace loading, KodeCode/KodeGodot parsing, hooks/scripts/task metadata, path/symlink/junction boundaries, archives/submodules/LFS references when applicable, generated project instructions and executable project metadata.

## Dependencies

R16.1–R16.2; Guardian, ProcessSandbox, Project Wizard/DNA, KodeCode workspace/parser, KodeGodot project/runtime.

## Detailed implementation

1. Add preflight trust/quarantine state for newly opened or materially changed workspaces.
2. Separate parse/index/read operations from executable build/run/hook/plugin operations.
3. Canonicalize filesystem paths and reject traversal or workspace escape through symlink/junction/relative-path tricks.
4. Prevent repository-owned configuration from silently widening command, environment, filesystem or network permissions.
5. Treat hooks, task runners, Godot editor/import scripts, shell/batch/PowerShell files and generated instructions as discoverable but non-authoritative until allowed by the proper boundary.
6. Add bounded archive/submodule/external-reference handling where supported; unknown external content stays quarantined.
7. Produce a machine-readable workspace-risk summary without exposing file contents unnecessarily.

## Deliverables

Workspace preflight/quarantine contracts; hardened loaders/parsers/executors; malicious-repo fixtures; acceptance report.

## Definition of done

Representative malicious repositories can be safely opened/analyzed without executing their payloads or escaping workspace scope; explicitly authorized safe project operations still function.

## Validation / proof

Cross-platform malicious-repo corpus including traversal, symlink/junction where supported, hook/task metadata, malicious project instructions and executable-file bait; exact-head gates.

## Rollback

Revert preflight/quarantine and loader changes atomically; fixture repos are disposable and contain no live payload.

## Risks

Platform-specific path semantics; hidden execution paths; false positives on legitimate build tooling; TOCTOU between preflight and execution.

## Manual intervention

**NONE.** Host-destructive execution is never part of acceptance.

## R16.3 END acceptance authority

- Normalized branch point: `main` `71e9ab8e2b56457e856109aa509a863c110d3fa3`; clean START `362bed9d2fc8ce3a12cbefaa1726e903fdb1469a`; immutable technical source `66a6e9466f97cbc8c30e3f51544d6d5b0a553e69`.
- Technical-source gate: R16.3 #3 / `33467123726` SUCCESS Ubuntu + Windows after exact checkout provenance, compile, Ruff, focused tests and acceptance on the same SHA.
- Cross-platform acceptance JSON is byte-identical: SHA-256 `68df97e7a33cba9f9596eeed06d8aa6eb16b098dfd69d55a5372e07551fd4f16`; semantic `40877687b4cefd11f5be78d6f32d09c963b12db1fbb74eaef4d9b692129e1eda`; 8/8 critical cases PASS with `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, synthetic-only fixtures, no live secrets and no destructive host actions.
- Linux artifact `9785244200` archive SHA-256 `5edb5ca2ada84c081ece142afb3a761d3856dbeb033ccf696905ffb757bb29d1`; Windows artifact `9785248696` archive SHA-256 `8e884c69f50d98e17bb5f7948b641d2fb0b2096722c3fbbd8fa89cda3cc0754d`.
- Security boundary delivered: new/materially changed workspaces default to quarantine; parse/index/read remains usable; write/execute requires exact-fingerprint approval; material change invalidates approval; critical symlink escape/resource-bound findings fail closed; repository hooks/scripts/tasks/instructions/archives/external references remain discoverable but non-authoritative; risk summaries exclude repository contents and external destinations.
- Manual NONE. R16.3 is COMPLETE at END-sync. Fresh exact-END R16.3/R0/Python/UI re-gates are mandatory before protected merge; R16.4 remains PLANNED until the implementation merge and unique post-merge continuity-only normalization complete.

---

# R16.4 — Secrets, privacy and exfiltration hardening

## Objective

Prove that secrets and protected data remain outside durable AI context/evidence and cannot be exfiltrated through prompts, logs, reports, subprocesses, URLs, artifacts or tool calls.

## Scope

Secret detection/redaction, vault/credential references, environment filtering, argv/log/report sanitation, network/tool boundaries, crash diagnostics, experience/tuning/research data paths, desktop persistence and CI artifacts.

## Dependencies

R16.1–R16.3; `core/secrets.py`; R8 vault/lineage; quality privacy/security; experience/tuning governance.

## Detailed implementation

1. Freeze synthetic secret classes and canaries; no real credential enters tests.
2. Centralize redaction/taint assertions for environment, argv, stdin/stdout/stderr, logs, reports and serialized evidence.
3. Resolve secret values only at narrow execution boundaries and pass references elsewhere when possible.
4. Deny attempts to send secret-tainted values to unapproved network/plugin/tool/research destinations.
5. Ensure exception traces and failure artifacts remain useful after redaction.
6. Scan generated CI evidence and repository artifacts for synthetic canary leakage.
7. Add rotation/revocation-compatible identity handling so cached credentials cannot become durable project state.

## Deliverables

Secret-taint/redaction contracts; hardened boundary adapters; exfiltration fixtures; leak-scanning acceptance.

## Definition of done

No synthetic canary appears in durable report/log/artifact/context; approved execution can still consume a secret at its bounded endpoint; denied exfiltration produces sanitized auditable evidence.

## Validation / proof

Cross-platform leak matrix over success/failure/cancel/timeout paths; repository-artifact scan; R0/Python/UI exact-head gates.

## Rollback

Revert redaction/taint integrations as a coherent unit; no real secret migration is introduced.

## Risks

Redaction breaking diagnostics; alternate encodings; structured-object serialization leaks; environment inheritance.

## Manual intervention

**NONE.** Synthetic secrets only.

## R16.4 END acceptance authority

- Normalized branch point: `main` `cb6ec02629fd94f9d23b04ebfed525571c8482d9`; clean START `d244d98e6699b1872d2d9457fb87ca39cb58eaad`; immutable technical source `f4dfa88870ee25956edf99476f5bd130a1cec471`.
- Technical-source gate: R16.4 #3 / `33514844394` SUCCESS Ubuntu + Windows after exact checkout provenance, compile, Ruff, 10 focused tests and exact-source acceptance.
- Cross-platform acceptance JSON is byte-identical: SHA-256 `8fb41bde8798b0b0734d19f582e298da20f8af40b88c2d02faa72b8279c7fac1`; semantic `7f5101b4371a531b6b1e610b1908f6b54e0123b111de1e4343f41887f57cfa0f`; 10/10 critical cases PASS with `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, synthetic-only fixtures, no live secrets, no destructive host actions and no network calls.
- Linux artifact `9803136169` archive SHA-256 `041fb37ee017329c23c062ae26a81a29fcd83d40f6b0e08a9eebbcba9b93f43f`; Windows artifact `9803152318` archive SHA-256 `e82cb50a838704931fa99c038d32f353410b5c70a900285f0ec1e3f5093724bb`.
- Security boundary delivered: `SecretRef` remains durable while secret values are resolved only at narrow use boundaries; raw/common encoded canaries are redacted; raw secrets are denied in argv and ordinary env maps; captured stdout/stderr and exceptions are sanitized; artifact scans are bounded/fail-closed; secret-tainted egress requires explicit destination plus payload authority and secret material is denied in URLs; fresh backend resolution observes rotation/revocation.
- Manual NONE. R16.4 is COMPLETE at END-sync. Fresh exact-END R16.4/R0/Python/UI re-gates are mandatory before protected merge; R16.5 remains PLANNED until implementation merge and unique post-merge continuity normalization complete.

---

# R16.5 — Plugin/MCP/tool trust, authorization and supply-chain boundary

## Objective

Ensure external tools/plugins/MCP servers are discoverable without being trusted by default, and can exercise only explicitly authorized capabilities with bound identity and provenance.

## Scope

Plugin registry/manifest, MCP/tool schemas and descriptions, tool identity/origin, capability requests, authorization scopes, consent/approval UX contracts, token handling when supported, version/digest pinning and revocation.

## Dependencies

R16.1–R16.4; Guardian/PermissionSet; plugin surfaces; model/tool orchestration; KodeStudio integration.

## Detailed implementation

1. Separate discovery, installation/registration, trust, authorization and invocation states.
2. Treat tool descriptions/annotations/schema text as untrusted metadata rather than executable policy.
3. Bind invocation to stable tool/plugin identity, version/digest, requested operation and initiating user/session intent.
4. Apply deny-by-default capability scopes for filesystem, network, subprocess, secrets and mutation.
5. Prevent token passthrough and cross-tool credential reuse; validate intended audience when an HTTP OAuth/MCP path supports it.
6. Add revocation/disable behavior that blocks new calls and sanitizes cached authorization state.
7. Add malicious plugin/tool fixtures covering deceptive descriptions, schema drift, capability escalation, replaced binaries/manifests and response injection.

## Deliverables

Tool/plugin trust contracts; capability authorization layer/adapters; registry/provenance evidence; adversarial tests.

## Definition of done

Unknown/replaced/escalating tools are denied or quarantined; approved least-privilege tools work; tool content cannot self-authorize; credential scopes do not silently cross identities.

## Validation / proof

Synthetic local plugin/MCP fixtures only; exact-head tool-security suite Ubuntu/Windows plus R0/Python/UI.

## Rollback

Revoke/disable R16 trust records and revert integration; no external plugin is required for core acceptance.

## Risks

Confusing discovery with trust; unstable tool identity; schema drift; overbroad cached consent; protocol-version differences.

## Manual intervention

**NONE** for core fixtures. No live third-party MCP server is claimed.

## R16.5 END acceptance authority

- Normalized branch point: `main` `eb62c9087dcb463917487ceb228d6926d6f9bb26`; clean START `c5eb6aa7d4fcd7551acf203651f51643dde9a695`; immutable technical source `4a3c925592e1e2915e7075825ca2d40e45ba1f1b`.
- Technical-source gate: R16.5 #3 / `33517964905` SUCCESS Ubuntu + Windows after exact checkout provenance, compile, Ruff, 12 focused tests and exact-source acceptance.
- Cross-platform acceptance is semantically identical: semantic SHA-256 `c8143a0386d384818cc4eef908cc224994c06291074e6a7e266f757c6483b83c`; 12/12 critical cases PASS with `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, synthetic local plugin/MCP/tool fixtures, no live third-party server, no live credentials and zero network calls.
- Linux artifact `9804400604` archive SHA-256 `e152d53eed46e710819b2980e8c6d7167f4cd61a06892fd77c2e52a93edfb1df`, payload SHA-256 `a51107a56236025532b750452238a7d61a53621a7721724e2aa1da181ce9ef7e`; Windows artifact `9804418715` archive SHA-256 `0b9faf72095b15a5f629e387c9b83849eb4f731651f6bc411aa39eb526f9dd74`, payload SHA-256 `435ee5cf1059b23c1615d7d5f745801fe84bb8d52494fa56b6b944c13df4efce`.
- Security boundary delivered: discovery/registration/trust/invocation are distinct; descriptions, schemas and tool results remain untrusted data-only; identity/version/artifact and definition digests are pinned; capability escalation and missing runtime permissions fail closed; invocation approval binds exact identity, operation, capability set and initiating intent; credential issuer/audience are identity-bound; cross-tool/replayed approvals are denied; definition or binary replacement is quarantined; revocation clears cached invocation grants.
- Manual NONE. R16.5 is COMPLETE at END-sync. Fresh exact-END R16.5/R0/Python/UI re-gates are mandatory before protected merge; R16.6 remains PLANNED until implementation merge and unique post-merge continuity normalization complete.

---

# R16.6 — Destructive-command, excessive-agency and confused-deputy hardening

## Objective

Prevent a model, malicious repository, plugin or ambiguous request from causing destructive or overprivileged actions beyond explicit user intent.

## Scope

PermissionSet/Guardian, command construction, file mutations, git operations, process execution, recursive/delete/reset/force operations, privilege/environment changes, network side effects, SafeChange and approval boundaries.

## Dependencies

R16.1–R16.5; core security primitives; KodeCode/KodeGodot executors; backend/desktop command surfaces.

## Detailed implementation

1. Classify operations by mutability, reversibility, scope and destructive potential using structured contracts.
2. Deny unknown or unbounded destructive impact before process launch.
3. Require explicit bounded authorization for high-impact but supported operations and bind approval to exact target/scope/action digest.
4. Prefer SafeChange/backup/transactional staging before overwrites or multi-file mutations.
5. Prevent confused-deputy escalation where a lower-trust source induces a higher-trust component to widen capability.
6. Enforce command/argument allowlists or typed builders at privileged boundaries; never evaluate model-generated shell text as policy.
7. Add cancellation/KillSwitch propagation and ensure partial mutation is detected and recoverable.

## Deliverables

Operation-risk contracts; hardened permission/execution/mutation boundaries; destructive-intent fixtures; recovery-linked evidence.

## Definition of done

All critical destructive/escalation cases are denied or constrained; authorized bounded mutations remain functional and reversible; no approval can be replayed for a different target/action.

## Validation / proof

Synthetic disposable workspaces; no host/system destructive commands. Include negative controls for force/reset/delete/path-scope widening and approval replay. Exact-head gates.

## Rollback

Restore previous permission/execution code and discard disposable workspaces; no persistent host state is modified by tests.

## Risks

False negatives from command aliases; platform-specific shells; approval TOCTOU; overly broad SafeChange snapshots.

## Manual intervention

**NONE.**

## R16.6 implementation evidence

- Normalized R16.5 base: `727b0717dea86425eb566b53b3b1cc38c9937169`; dedicated branch `r16/06-destructive-command-excessive-agency-hardening`.
- Immutable technical source: `de2648e9c7648e59dd43f9d2dccd10d0ea93da18`.
- Exact-source focused acceptance: R16.6 #3 / 33532542824 SUCCESS on Ubuntu + Windows; exact checkout, compileall, Ruff, focused adversarial tests and acceptance emission all passed.
- Exact-source repository qualification: R0 #2289 / 33532542438 SUCCESS, Python Core #2261 / 33532542746 SUCCESS across all five jobs, KodeStudio UI Smoke #2226 / 33532542489 SUCCESS.
- Technical artifacts: Linux `9810360507 / sha256:8465a92f36edb6a2de014116aa0519bebdc7f9a828c89483b0e054a055d91c05`; Windows `9810383609 / sha256:081dff3ad19cd6fab0e6f9c29d5e966392b020389a6d4a6d9664b90a451ebe92`.
- Accepted scope: structured impact classification; fail-closed unknown/unbounded mutation handling; exact one-shot approval binding across actor/action/target/scope/capability/tool/provider/operation; material-drift and replay rejection; authenticated bounded delegation against confused-deputy escalation; typed non-shell process commands constrained by PermissionSet allowlists; SafeChange snapshots; KillSwitch propagation and explicit `RECOVERY_REQUIRED` state after possible partial mutation.
- Legacy `KodeGuardian.authorize(..., confirmed=True)` remains API-compatible but no longer converts a destructive `CONFIRM` into ambient `ALLOW`; bound authority must come from the R16.6 exact-intent path.
- Tests remain synthetic/disposable and do not execute destructive host commands, live credential operations or production mutations. Manual state: **NONE**.
- R16.7 remains blocked until this END-sync receives fresh exact-head R16.6/R0/Python/UI gates, PR #345 merges with `expected_head_sha`, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

# R16.7 — Memory/context poisoning detection, quarantine and rebuild

## Objective

Make durable memory/context resilient to malicious, stale or corrupted entries and prevent memory content from becoming hidden policy or permission authority.

## Scope

`intelligence/memory.py`, context serialization, project continuity links, retrieved memory, experience/research-derived context, integrity/version metadata, quarantine/rebuild and bounded forgetting/invalidation.

## Dependencies

R16.1–R16.6; R15 provenance/governance; existing continuity/project identity contracts.

## Detailed implementation

1. Version memory records with origin, project scope, integrity digest and trust class.
2. Prevent memory entries from granting permissions, changing architecture, disabling security or overriding newer authoritative project state.
3. Detect malformed, tampered, conflicting, replayed or out-of-scope memory and quarantine rather than silently repair into authority.
4. Add deterministic rebuild from known-good authoritative sources where available.
5. Separate user/project facts, derived summaries and executable/action suggestions.
6. Add poison fixtures for authority spoofing, secret embedding, cross-project contamination, stale instructions and corruption.
7. Ensure quarantine/rebuild is auditable and does not erase unrelated valid memory.

## Deliverables

Memory integrity/trust schema; quarantine/rebuild service; poison fixtures/tests; recovery evidence.

## Definition of done

Poisoned/corrupted entries cannot change permissions/policy or cross project scope; valid memory survives targeted quarantine; rebuild produces deterministic known-good state or truthfully reports unrecoverable/inconclusive.

## Validation / proof

Exact-head memory-poison suite with corruption/tamper/replay/cross-project cases; R0/Python/UI.

## Rollback

Use versioned backward-compatible reader or explicit migration rollback; preserve original test snapshots for recovery verification.

## Risks

Legitimate historical context falsely quarantined; schema drift; silent scope collapse; non-deterministic summarization.

## Manual intervention

**NONE.**

## R16.7 implementation evidence

- Normalized R16.6 base: `9c358e48e97352046160d48cee0417ade435b6ac`; dedicated branch `r16/07-memory-context-poisoning-hardening`.
- Immutable technical source: `f095781fde179045fcbcf7fb89661f72f9c51c46`.
- Exact-source focused acceptance: R16.7 #3 / 33548649753 SUCCESS on Ubuntu + Windows; exact checkout, compileall, Ruff, 18 focused adversarial tests and 15-case acceptance emission all passed.
- Exact-source repository qualification: R0 #2299 / 33548649697 SUCCESS Ubuntu + Windows, Python Core #2271 / 33548649730 SUCCESS across all five jobs, KodeStudio UI Smoke #2236 / 33548649767 SUCCESS.
- Cross-platform acceptance semantic SHA-256: `da712c044ecc6fc7a6a7263c512603ffabe7f55ef126d3ad6214e2135fe60136`; 15/15 critical cases PASS with `security_claim=true`, `critical_veto=false`, `manual=NONE`, synthetic-only fixtures, zero network calls, zero live secrets and no raw poison persistence.
- Technical artifacts: Linux `9816508603 / archive sha256:20f5b1f01c3bcb9272813f82a8b54932a857a2910dfc1a16682c425ae2b04acc / payload sha256:a4a699a2da38d68c4571d846614fba07425746039bf510e8bdb83175dc1787ed`; Windows `9816556278 / archive sha256:65b69553bcd265e0d7cd1b681719abf0b383238a92003de77da31319a9ee7b7f / payload sha256:a79b8b777038efbeb7b1be985d4018de3828fa034a4b8aa26631dea439512fba`.
- Accepted scope: versioned provenance/project-scope/trust/record-class/integrity/expiry metadata; fail-closed tamper, replay, same-version conflict, stale-version, cross-project and expiry handling; hashed quarantine evidence without raw secret retention; memory content cannot self-authorize, alter policy/architecture or raise its trust class; bounded invalidation preserves unrelated valid memory; deterministic authoritative rebuild replaces only matching lineages and reports `INCONCLUSIVE` when no trustworthy source exists; action suggestions cannot become authoritative rebuild facts.
- Legacy memory rows migrate as data-only/untrusted and legacy add/list/semantic-search behavior remains available. Tests are synthetic/disposable and do not use live secrets, production memory or network calls. Manual state: **NONE**.
- R16.8 remains blocked until this END-sync receives fresh exact-head R16.7/R0/Python/UI gates, PR #347 merges with `expected_head_sha`, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

# R16.8 — Fault injection, KillSwitch, backup and recovery drills

## Objective

Prove recovery semantics under realistic partial failure rather than only nominal backup/restore tests.

## Scope

KillSwitch, ProcessSandbox, SafeChange, backup/recovery, interrupted writes, subprocess crash/hang, disk/resource denial simulation, corrupted checkpoint/state, cancellation and restart.

## Dependencies

R16.1–R16.7; existing R1 recovery primitives and subsystem persistence contracts.

## Detailed implementation

1. Define deterministic fault injection points around prepare/write/commit/verify/cleanup stages.
2. Exercise KillSwitch before launch, during process execution and during multi-step mutation.
3. Verify atomicity or explicit partial-state detection for interrupted writes.
4. Corrupt synthetic backups/checkpoints and prove integrity rejection.
5. Restore from known-good backup and re-run invariant checks before continuation.
6. Verify recovery does not restore stale permissions/secrets/tool trust outside the snapshot contract.
7. Record recovery point objective semantics for repository-local state without claiming production disaster-recovery guarantees.

## Deliverables

Fault injector; recovery acceptance harness; corruption fixtures; machine-readable recovery reports.

## Definition of done

Every critical injected fault ends in clean rollback, validated recovery or explicit blocked state; no partial/corrupt state is silently accepted as current authority.

## Validation / proof

Cross-platform fault matrix, exact-source evidence, fresh R0/Python/UI.

## Rollback

Fault injection is test-scoped; remove harness and restore baseline code. Test workspaces/backups are disposable.

## Risks

Fault points that do not model real persistence order; nondeterministic process timing; backup scope omissions.

## Manual intervention

**NONE.**

## R16.8 implementation evidence

- Normalized R16.7 base: `951c53959956d1b88b3c9c3a8c4c328c1127236b`; clean START-sync head `692b0ab931d3d59bf9f14aef7643ad83cbedc412`; dedicated branch `r16/08-fault-injection-recovery`.
- Immutable technical source: `9bea715e7f575696ba66240d6ff127e72e85f82e`.
- Exact-source focused acceptance: R16.8 #3 / `33561149190` SUCCESS on Ubuntu + Windows; exact checkout, compileall, Ruff, focused recovery/adversarial tests and machine-readable acceptance emission all passed.
- Exact-source repository qualification: R0 #2308 / `33561149073` SUCCESS Ubuntu + Windows; Python Core #2280 / `33561148836` SUCCESS across all five jobs; KodeStudio UI Smoke #2245 / `33561148947` SUCCESS.
- Cross-platform semantic acceptance SHA-256: `f94ccc46356a24a8be2726a724191e1dc2eb148c049e184f38431be2f4af8c26`; 16/16 cases PASS with `security_claim=true`, `critical_veto=false`, `manual=NONE`, synthetic-only fixtures, zero network calls, zero live secrets, zero destructive host actions and no production disaster-recovery claim.
- Exact-source artifacts: Linux `9821331886 / sha256:9d2efca69b657333aead766a044318d26c3bccd2fd63320343885172a43d8943`; Windows `9821324996 / sha256:0735008e3eb6610891f0af3f8d7bc9bd2b786f824ed5322a18efe27cd6d40bad`.
- Accepted scope: deterministic one-shot fault points at prepare/write/commit/verify/cleanup; integrity-bound v2 recovery checkpoints; legacy checkpoints remain readable as data but cannot become recovery authority; synthetic ENOSPC/resource denial; KillSwitch before launch, against a hanging registered subprocess and during multi-step mutation; bounded timeout handling; corrupted checkpoints/snapshots/backups fail closed; verified known-good restoration; exact task binding; narrow single-file recovery that does not roll unrelated permissions/secrets/tool-trust state backward; repository-local recovery point objective only.
- R16.8 is COMPLETE at END-sync. Fresh exact-END R16.8/R0/Python/UI re-gates are mandatory before PR #349 may merge with exact `expected_head_sha`; R16.9 remains PLANNED until the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

# R16.9 — Dependency/workflow/release supply-chain provenance hardening

## Objective

Harden the software/tooling supply chain so dependencies, GitHub Actions, generated artifacts, plugins and release inputs have explicit identity/integrity/provenance and cannot silently drift into the v1.0 candidate.

## Scope

Python/build dependencies, optional tooling, GitHub Actions references/permissions, BOM/license inventory, artifact digests/provenance, plugin/tool packages, generated binaries/packages and release manifest inputs.

## Dependencies

R16.1–R16.8; quality license/BOM/build/security; existing CI workflows and packaging.

## Detailed implementation

1. Produce deterministic dependency/tool inventory with source/version/digest where applicable.
2. Audit workflow token permissions, untrusted PR input handling, shell interpolation and artifact boundaries.
3. Pin or otherwise integrity-bind security-critical external actions/tools according to repository policy while preserving maintainability.
4. Bind build/package artifacts to source SHA and build manifest; generate checksums and provenance metadata.
5. Detect dependency/plugin replacement or unexpected manifest drift and fail closed.
6. Ensure license/BOM evidence covers release candidate dependencies and distinguishes optional/unavailable components.
7. Add synthetic tamper tests for manifests/artifacts/dependency identity.

## Deliverables

Supply-chain manifest/provenance contracts; hardened workflows/build paths; tamper tests; RC BOM/license evidence.

## Definition of done

A changed/tampered/unexpected release input cannot silently produce a promoted artifact; workflow permissions are least-privilege for their job; candidate artifacts are bound to exact source and manifest.

## Validation / proof

CI-owned tamper/manifest tests plus R0/Python/UI; no external signing key required.

## Rollback

Revert workflow/build/provenance changes together; previous artifacts remain non-promoted historical evidence.

## Risks

Dependency resolver nondeterminism; action version compatibility; false assumptions about provenance equaling security.

## Manual intervention

**NONE** for core provenance. Production signing remains later conditional scope.

## R16.9 implementation evidence

- Clean START: `31249739d3b1a617bdf8aa2c8080d777875739c7` from normalized R16.8 `main` `9e62f7d8a85965c64d66cf317e028993b669f775`.
- Immutable technical source: `026ddc91672c144977453c9852a5288e9533af22`.
- Exact-source focused acceptance: R16.9 #7 / 33585517872 SUCCESS on Ubuntu + Windows; exact checkout, wheel+sdist build, compile, Ruff, 24/24 focused tests and 19/19 acceptance/tamper cases PASS per OS.
- Exact-source repository qualification: R0 #2319 / 33585517967 SUCCESS Ubuntu + Windows; Python Core #2291 / 33585517983 SUCCESS 5/5; KodeStudio UI Smoke #2256 / 33585518000 SUCCESS.
- Accepted scope: seven verified external action identities; twelve v1 promotion authority workflows pinned to full immutable commit SHAs with `contents: read`; forty-five historical workflows inventoried but non-authoritative for v1 promotion; deterministic 23-entry dependency/tool inventory; exact-source BuildManifest + BOM binding; fail-closed action drift/unapproved action, privileged permissions, `pull_request_target`, direct untrusted PR shell interpolation, artifact path escape, cross-source replay and serialized evidence tamper.
- Evidence: policy `bee3cc2e13b43e5b6751913b45de6deed83ee4b4447cec71ca39bc5a004148ef`; semantic acceptance `3a115fd23a65085658a27c08a2f71cc0aa5a3f3157b091cca1091342ee06b0ce`; acceptance report `d4c44fb4dd6034e448fc1d63900721cb189dc33c97860bfb5e0573e0ef648fe5`; promotion manifest `3f4a487a52b087a26791080cb7b90ed333120cc87c98f53e9589fac28f951e81`; workflow audit `be9440ba570031b411389e7b85472ec05b043eace6e2d57b3a2540327ba5c743`; dependency inventory `b372e3383ee8ad1619a133c9e7de4cd274e3d3ca45dcc5247614642b85772ca2`.
- Exact-source artifacts: Linux `9829927043 / sha256:c7af04d4cfd2e51419d57e9c4cef029bb75db7ddc1b48ec415e8f8955fe4141c`; Windows `9829937614 / sha256:0754ec9ab8eb1cc1d6a061437a0a1219ccb615efd3983fa8b161b4739866336b`.
- External attestations remain optional provenance evidence and never a security verdict; core acceptance used no live credentials, signing key, network calls or destructive host actions. Manual state: **NONE**.
- R16.10 remains blocked until this END-sync head passes fresh exact-head R16.9/R0/Python/UI gates, PR #351 merges with `expected_head_sha`, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

# R16.10 — Representative real Godot 2D beta project

## Objective

Validate the hardened product on a representative, repository-owned real Godot 2D project workflow rather than an isolated parser fixture.

## Scope

Project creation/opening, scene/script/resource edits, KodeGodot inspection, run/test/export-safe paths, asset changes, error diagnosis, interruption/recovery and malicious-content negative controls embedded in non-authoritative project text.

## Dependencies

R16.1–R16.9; existing KodeGodot and asset workflows.

## Detailed implementation

1. Add or designate a bounded representative 2D project with deterministic assets/scenes/scripts and clear license/provenance.
2. Execute create/open/analyze/edit/validate/run or supported headless checks through public Kodepoia surfaces.
3. Exercise a realistic change request spanning multiple files and verify SafeChange/rollback.
4. Inject benign untrusted project instructions that must remain data, plus a malicious negative-control variant that must not execute.
5. Capture project digest, produced diffs, diagnostics and recovery evidence.
6. Keep engine availability capability-probed; repository-level machine checks remain authoritative where external executable is unavailable.

## Deliverables

Representative Godot 2D beta fixture/project; end-to-end acceptance runner/report; regression tests.

## Definition of done

The supported 2D workflow completes deterministically without bypassing hardened boundaries; malicious project text cannot acquire execution authority; rollback returns to the exact pre-change project digest.

## Validation / proof

CI exact-head acceptance with repository-owned fixture. Any live Godot binary claim must record executable/version and actual invocation rather than infer availability.

## Rollback

Discard/reset the representative project workspace; no external project is modified.

## Risks

Fixture becoming too synthetic; Godot-version differences; generated import/cache noise; platform path differences.

## Manual intervention

**NONE** for core acceptance.

## R16.10 implementation evidence

- Exact normalized base: `main` `3957a30053da791facb2de7fbbbb0614d0fa03d6`; dedicated branch `r16/10-representative-godot-2d-beta-project`; final immutable technical candidate before END-sync: `499292dd553460bb48f3092112d5bcb81544242b` (tree-identical retrigger of clean source `ee433680428fd525970456d740980e432d38bea5`).
- Exact-source focused acceptance: R16.10 #20 / `33638816914` SUCCESS on Ubuntu + Windows. Both jobs passed exact checkout/provenance, wheel+sdist build, compile, Ruff, focused tests, machine-readable acceptance emission and artifact upload.
- Exact-source supply-chain regression qualification: R16.9 #23 / `33638824052` SUCCESS Ubuntu + Windows after registering the R16.10 focused workflow as the 13th immutable authority while preserving strict `all(item.authoritative)` enforcement and full-SHA action pins.
- Exact-source repository qualification: R0 #2333 / `33638823984` SUCCESS Ubuntu + Windows; Python Core #2305 / `33638824758` SUCCESS 5/5; standalone KodeStudio UI Smoke #2270 / `33638824596` SUCCESS.
- Acceptance summary: 10/10 cases PASS on each OS; `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, no live credentials, zero network calls, no destructive host action. Untrusted repository/project text remains data-only.
- Godot live capability is truthfully `capability_absent` on both hosted runners; no executable/version/invocation is claimed.
- Canonical cross-platform SHA-256: fixture/restored `e87b912f36b960e724b4d2eb6367794c6933ae0255353b5cbcbb400294c66b95`; changed `0312025cdbfef593ba21a4280d9d897c4ef8aa37ec8201ceeec9c9b9b96f054e`; diff `4226629a0be5da2ba2dfb3f344d56b973d9893462ef8cba64c7bc8b37a450542`; diagnostic `f61d0af7376d7deda7ad2ac65b5debdf47154f432403d41c150d351a59fc6b07`; recovery `6f107c6ff1c683ad31597e400512fb247ed56b6e4d035c1a9f0e4dce5ab5a7d5`; semantic `25b95aa0ae5ccd909a1b93e9e0d3540482a2f6c6c01491c6fd7845fd80bbe095`.
- Exact-source artifacts: Linux `9850084807 / sha256:09eede99ef70a5b9faefdde5965001e1c3d33de8ad55d34242fa97582f2e5c28`; Windows `9850065450 / sha256:f0d2da48b853f1d27d8cc14e61884c32357438ed85a9d1616cd86ffdd6c252da`.
- SafeChange rollback uses canonical LF manifest serialization and restores the original project digest exactly.
- R16.10 is COMPLETE at END-sync. R16.11 remains unauthorized until fresh exact-END R16.10/R16.9/R0/Python/UI gates, PR #353 exact-head merge, and the unique continuity-only post-merge normalization all succeed.

---

# R16.11 — Representative real Godot 3D beta project

## Objective

Validate the hardened product on a representative real 3D Godot workflow including heavier assets/scenes and process/resource boundaries.

## Scope

3D scenes/resources, meshes/materials/animation references where already supported, KodeGodot execution/diagnostics, asset lineage, edits, rollback, resource budgets and malicious metadata/text controls.

## Dependencies

R16.10 plus existing R8/R10 3D asset/Blender/Godot bridge capabilities.

## Detailed implementation

1. Add/designate a bounded representative 3D project with deterministic provenance and manageable CI size.
2. Exercise multi-file 3D project inspection/edit/validation through supported public surfaces.
3. Verify asset references remain workspace-bounded and lineage-aware.
4. Exercise failure/cancel/rollback during a representative 3D change.
5. Add resource-budget and malformed/external-reference negative controls.
6. Record exact project and artifact digests.

## Deliverables

Representative Godot 3D beta project; end-to-end acceptance evidence; regression/fault tests.

## Definition of done

Supported 3D workflow passes without trust-boundary bypass, workspace escape or unbounded resource behavior; rollback/integrity checks succeed.

## Validation / proof

Exact-head cross-platform machine acceptance where supported; truthful unavailable markers for non-installed external engine/tool capabilities.

## Rollback

Discard/reset fixture workspace and generated caches/artifacts.

## Risks

Large binary churn; GPU/renderer dependence; nondeterministic imports; accidental expansion into new engine functionality.

## Manual intervention

**NONE** for core acceptance.


## R16.11 implementation evidence

- Exact normalized base: `main` `75e58ba578d6c5f654be1c3a8e35fae7f86cb72a`; clean START-sync head `58816b94d4823fd51612151a03c56e3dbe2fe117`; dedicated branch `r16/11-representative-godot-3d-beta-project`.
- Immutable technical source: `4be69eef7300c380d125f35d484c57d8df054d72`.
- Exact-source focused acceptance: R16.11 #12 / `33662240625` SUCCESS Ubuntu + Windows. Both jobs passed exact checkout provenance, wheel+sdist build, compile, Ruff, focused R16.10/R16.11 plus R16.9 supply-chain regression tests, machine-readable acceptance emission and artifact upload.
- Exact-source supply-chain qualification: R16.9 #34 / `33662240583` SUCCESS Ubuntu + Windows after registering the R16.11 workflow as immutable v1 authority with full-SHA actions and read-only permissions.
- Exact-source repository qualification: R0 #2346 / `33662240657` SUCCESS; Python Core #2318 / `33662240501` SUCCESS; KodeStudio UI Smoke #2283 / `33662240630` SUCCESS.
- Acceptance summary: 15/15 cases PASS per OS with `security_claim=true`, `critical_veto=false`, `manual_state=NONE`, zero network calls, no live credentials and no destructive host action. Godot is truthfully `capability_absent` on both hosted runners.
- Representative fixture budget: 8 files, 3754 bytes total, maximum single file 1388 bytes; deterministic OBJ mesh, material, scenes, script, provenance and malicious-metadata negative control stay repository-owned and CI-bounded.
- Canonical cross-platform SHA-256: fixture/pre-change/restored/cancel-restored `69f88a9cb0c250e33ce40783bc11de179cf06a86c669feaafcf1419f2234dcb1`; changed `4a59aaa65f06d04c3df3f088b625f5e3fba6b4999267769ab26e7ae82903d7ab`; diff `d701bff2aa3100c3b46d571deea69e7abc7a35068162e6141a9e6d9cd89e9fe6`; diagnostic `d041a7f188fd1ed47caca5753e1322ed1793cbc441930957616e7dc05ffe473e`; recovery `6d4ac38558c776ac3cc74c13f7ba5dce0cbe15d7dd6c4e27edffda8a3b30687d`; asset content `7e1702ec3110d793088cb7f779e5c0e30fdd1826110013b6c85e4062cd9c5f77`; semantic `bc3ee5d201026acd880fab0b06e84e6a335e72e23685935611d8531b9c6ac294`; deterministic asset revision `rev_c14815e60f06b6b3dca5ffdc7dfa5b84`.
- Exact-source artifacts: Linux `9859239402 / archive sha256:0bff3e1437de0f0a04617d8beb9cf10b86deb15a034bd9daec8872781f7c7d3f / payload sha256:382339653ca3b4d00f28fbdc4d31e196b862eee9ff43ddd2b7580a95d46386e1`; Windows `9859245340 / archive sha256:3c195da388272bee3f6f29243ca626554fb568726f76b25c6756f50886207dab / payload sha256:b8cea082e2933ee39c767f09e100e38862bcfb0db86a3c31babce6476207c4af`.
- Accepted boundaries: public KodeGodot 3D inspection/analysis/edit paths; Vault lineage-aware reference; WorkspaceBoundary confinement; external-reference negative control; untrusted metadata remains inspectable data without process/tool authority; bounded cancellation rollback; SHA-precondition failure; integrity-bound checkpoint; aggregate SafeChange exact restore; audit-chain verification; explicit resource budgets.
- R16.11 is COMPLETE at END-sync. R16.12 remains unauthorized until this documentation/evidence END head passes fresh exact-head R16.11/R16.9/R0/Python/UI gates, merges with exact `expected_head_sha`, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

# R16.12 — Representative real Windows desktop application

## Objective

Validate Kodepoia on a representative Windows desktop application workflow through workspace, code, build/test/package and failure/recovery boundaries.

## Scope

Existing desktop scaffolds/adapters (for example WPF/WinUI3/Tauri/Avalonia/Qt paths where supported), Windows path/process semantics, packaging evidence, IPC/persistence and SafeChange rollback.

## Dependencies

R16.1–R16.11; `src/kodepoia/desktop/`; Windows CI runner.

## Detailed implementation

1. Choose one repository-supported Windows application path as canonical representative, with others remaining compatibility probes rather than hidden requirements.
2. Create/open/edit the app through public Kodepoia interfaces.
3. Run supported static/build/test/package checks with exact toolchain capability evidence.
4. Exercise path quoting, long/space-containing paths, cancellation and failed-build recovery.
5. Verify generated package/build evidence is source-bound and secret-free.
6. Add malicious project/config negative controls without executing host-destructive payloads.

## Deliverables

Representative Windows app fixture/project; Windows end-to-end acceptance; package/build manifest evidence.

## Definition of done

The chosen Windows workflow completes on `windows-latest` using supported toolchain capabilities or truthfully marks a capability unavailable; failures do not corrupt workspace or leak sensitive data.

## Validation / proof

Dedicated Windows acceptance plus full Python Core and UI Smoke; exact-source package/build manifest.

## Rollback

Reset disposable workspace/artifacts; no installed system application is required.

## Risks

Hosted-runner toolchain drift; packaging framework differences; shell quoting; signing assumptions.

## Manual intervention

**NONE** for unsigned/core CI acceptance.


## R16.12 START authority

- State: **IN_PROGRESS**; manual **NONE** for unsigned/core CI acceptance.
- Exact normalized base: `main` `270e022a03d7a596eedd27d8989b22278f18cbca`; dedicated branch `r16/12-representative-windows-desktop-application` created directly from that SHA.
- Prior state: R16.1–R16.11 **COMPLETE + NORMALIZED**; R16.13–R16.18 remain **PLANNED**.
- Frozen scope is unchanged: one repository-supported Windows desktop path is canonical; other supported desktop adapters remain compatibility probes. Acceptance covers public create/open/edit surfaces, Windows path/process semantics, supported static/build/test/package checks with exact toolchain capability evidence, quoting/long-and-space paths, cancellation and failed-build recovery, source-bound secret-free package/build evidence, malicious project/config negative controls, IPC/persistence and SafeChange rollback.
- No R16.12 implementation preceded this START-sync. No manual signing, installed system application or production target is required for core CI acceptance.

---

# R16.13 — Representative ComfyUI beta workflow

## Objective

Validate a representative ComfyUI workflow through Kodepoia’s existing client/execution/workflow/resource boundaries while proving safety under unavailable GPU/server and malicious workflow metadata.

## Scope

ComfyUI workflow validation, local fixture/wire protocol, resource scheduling, output handling, cancellation/recovery, malicious node/workflow metadata and optional real local ComfyUI/GPU qualification.

## Dependencies

R16.1–R16.12; existing R9 ComfyUI capabilities and resource budgets.

## Detailed implementation

1. Freeze a representative repository-owned workflow fixture with deterministic node/config/output expectations.
2. Exercise validation, queue/execution transport, progress/events, output collection and cancellation against the authoritative local fixture server.
3. Reject path escape, untrusted output locations, workflow-supplied arbitrary command intent and unsafe external references.
4. Enforce RAM/VRAM/disk/time budgets before/through execution.
5. Bind output metadata to workflow/source/config digest and sanitize prompts/paths where required.
6. Provide optional real local ComfyUI qualification command that records server/version/GPU facts without altering core verdict.

## Deliverables

Representative ComfyUI beta workflow; local deterministic acceptance; optional local qualification schema.

## Definition of done

Core fixture execution and all security/resource negative controls pass in CI; real-server/GPU capability is never inferred when not exercised.

## Validation / proof

CI fixture acceptance plus exact-head R0/Python/UI. Optional real local report must match exact source SHA and workflow digest.

## Rollback

Cancel fixture server/jobs and remove generated outputs; no model download or GPU driver change is required.

## Risks

Protocol/version drift; large outputs; GPU-dependent claims; unsafe custom-node assumptions.

## Manual intervention

**CONDITIONAL.** Only if a **real local ComfyUI/GPU qualification claim** is explicitly required. Core acceptance remains automated and does not trigger this gate.

---

# R16.14 — Representative audio/voice/cinematic beta workflow

## Objective

Validate existing media/audio/TTS/voice/cinematic capabilities as one representative project workflow with governance, deterministic artifacts and failure recovery.

## Scope

Audio inspection/QA, TTS registry/runtime, voice governance/profiles, alignment/visemes, cinematic timing/capture contracts where supported, file/path safety, consent/governance metadata and resource limits.

## Dependencies

R16.1–R16.13; existing R11 media stack.

## Detailed implementation

1. Build a repository-owned short media scenario using synthetic/public-domain text/audio fixtures only.
2. Exercise audio validation, supported TTS path, voice-governance checks, alignment/viseme generation and cinematic metadata flow.
3. Verify generated media/output paths remain workspace-bounded and source/provenance-linked.
4. Reject unapproved voice identity/profile use and malformed/unsafe markup or external references.
5. Exercise cancellation/failure and verify partial outputs are not promoted as valid final assets.
6. Keep human listening/device playback as optional quality qualification, never core correctness evidence.

## Deliverables

Representative media beta fixture; integrated media acceptance report; governance/failure tests.

## Definition of done

Machine-verifiable media contracts pass, invalid governance/markup/path cases fail closed, and partial/cancelled artifacts cannot be promoted.

## Validation / proof

CI machine acceptance and exact-head gates. Optional listening/device evidence, if requested, is supplementary and source-bound.

## Rollback

Delete disposable generated media and restore fixture workspace.

## Risks

Codec/backend differences; nondeterministic TTS output; subjective quality mistaken for functional correctness; voice-consent ambiguity.

## Manual intervention

**CONDITIONAL.** Only for an explicitly requested human listening/device-quality claim; core acceptance is automated.

---

# R16.15 — Long-term project durability, resume and upgrade soak

## Objective

Prove that a project can survive repeated sessions, interruptions, schema/version evolution and backup/recovery cycles without continuity drift or silent corruption.

## Scope

Project DNA, memory/context, continuity, desktop persistence, save/migration bridges, artifact registries, backups, interrupted sessions, repeated edits and bounded simulated time/session progression.

## Dependencies

R16.1–R16.14.

## Detailed implementation

1. Create a deterministic long-lived project fixture with versioned checkpoints across multiple simulated sessions.
2. Re-open from clean processes and prove state reconstruction from durable authorities rather than in-memory cache.
3. Apply representative cross-domain changes over multiple cycles and verify provenance/history continuity.
4. Exercise version/schema migration forward and supported rollback/recovery paths.
5. Inject stale/corrupt memory, interrupted write and partial artifact states at defined checkpoints.
6. Assert no unresolved orphan, duplicate authority, silent data loss or stale permission/secret state survives recovery.
7. Provide an optional longer wall-clock local soak profile while keeping a bounded deterministic CI profile authoritative.

## Deliverables

Long-term project fixture; session/upgrade/recovery runner; durability evidence and diff summaries.

## Definition of done

Bounded CI soak completes deterministically across clean process restarts and migrations; corruption is detected/recovered or explicitly blocks continuation; final project digest/history matches expected authority.

## Validation / proof

Exact-head bounded soak on hosted runners plus R0/Python/UI. Optional extended local soak has separate truthful evidence.

## Rollback

Restore fixture checkpoint or discard generated project; migrations remain versioned/reversible within declared support.

## Risks

Tests too short to expose accumulation bugs; migration asymmetry; stale cache; nondeterministic timestamps/IDs.

## Manual intervention

**CONDITIONAL.** Only for an optional extended wall-clock/local-environment soak beyond the authoritative bounded CI profile.

---

# R16.16 — Resource, concurrency, leak and diagnostics soak

## Objective

Prove bounded behavior under repeated/concurrent workloads and make failures diagnosable without leaking sensitive project content.

## Scope

CPU/RAM/VRAM/disk/process/time budgets, concurrency/cancellation, worker/process cleanup, file-handle/temp-artifact cleanup, repeated open/run cycles, diagnostics, privacy/redaction and regression thresholds.

## Dependencies

R16.1–R16.15; quality budgets/health/privacy; ProcessSandbox; subsystem resource managers.

## Detailed implementation

1. Define deterministic bounded load profiles for representative code/Godot/ComfyUI/media/desktop operations using fixtures.
2. Measure process/task cleanup and detect orphan workers or accumulating temp artifacts.
3. Apply concurrency/cancellation races at supported boundaries and verify state consistency.
4. Enforce hard preflight and runtime budgets; unknown capacity fails closed where required.
5. Generate privacy-safe diagnostics with aggregate/resource facts rather than raw sensitive content.
6. Compare against frozen tolerances/baselines and fail on material regressions or unbounded growth.
7. Separate environment variance from product regression through normalized metrics and explicit `INCONCLUSIVE` handling.

## Deliverables

Bounded soak/load harness; resource/leak diagnostics; regression thresholds and acceptance report.

## Definition of done

No critical unbounded resource growth, orphan process, inconsistent state or sensitive diagnostic leak is observed in the bounded profile; thresholds are explicit and source-bound.

## Validation / proof

Hosted-runner bounded soak with repeatability check; fresh exact-head R0/Python/UI.

## Rollback

Remove profiling hooks/harness; production/runtime behavior changes revert atomically with tests.

## Risks

Noisy hosted-runner metrics; false leak signals; insufficient repetitions; diagnostics themselves adding overhead.

## Manual intervention

**NONE.**

---

# R16.17 — v1.0 packaging, migration, rollback and release readiness

## Objective

Assemble a release-candidate contract that can be built, inspected, installed/extracted as supported, upgraded/migrated and rolled back without overstating production publication or signing coverage.

## Scope

Versioning, package/build manifests, dependency/BOM/license evidence, release notes, migration/rollback, configuration defaults, known limitations, security/privacy documentation, incident/recovery runbook and optional signing/publishing qualification.

## Dependencies

R16.1–R16.16; desktop/mobile/backend packaging authorities where applicable; R16.9 provenance.

## Detailed implementation

1. Freeze v1.0 RC version/build identity and exact-source manifest rules.
2. Produce deterministic supported packages/artifacts with checksums/provenance and dependency/BOM/license evidence.
3. Validate clean install/extract/start or repository-supported package consumption on hosted runners.
4. Validate supported upgrade/migration from the declared prior fixture and rollback/recovery on failure.
5. Document secure defaults, unsupported/unavailable optional capabilities, residual risks and known limitations.
6. Produce user/operator incident, backup/recovery and secret/plugin revocation guidance tied to implemented behavior.
7. Keep code signing, store/public registry publication, production credentials and domain/provider rollout as explicit conditional actions.

## Deliverables

RC package/build artifacts; manifest/provenance/BOM/license evidence; migration/rollback tests; release notes; security/operations documentation.

## Definition of done

The unsigned/core RC is reproducible, source-bound, install/consume tested as supported, migration/rollback tested, and all capability/limitation claims match evidence.

## Validation / proof

Exact-head release-readiness workflow plus R0/Python/UI and artifact integrity checks.

## Rollback

Discard non-promoted RC artifacts and restore prior supported fixture/version; no public release occurs automatically.

## Risks

Packaging framework drift; accidental claim inflation; signing/publication mistaken for core readiness; irreversible migration.

## Manual intervention

**CONDITIONAL.** Required only if production signing, store submission, public registry publication or provider/domain cutover is explicitly requested. Core RC acceptance does not require these actions.

---

# R16.18 — Integrated adversarial + real-project RC acceptance

## Objective

Create the final non-circular R16/v1.0 release-candidate authority that reruns critical adversarial, recovery and representative-project claims on one exact end head and vetoes release on any critical regression.

## Scope

Critical cases from R16.1–R16.9; representative Godot 2D/3D, Windows, ComfyUI fixture, media and long-term workflows; resource soak summary; RC package/provenance; cross-platform exact-head evidence; residual/optional capability truthfulness.

## Dependencies

R16.1–R16.17 all COMPLETE + NORMALIZED.

## Detailed implementation

1. Freeze the canonical integrated case/project set and its digest independently from prior pass/fail artifacts.
2. Re-run critical red-team cases from clean state on the exact R16.18 technical source rather than importing prior verdicts.
3. Re-run representative project workflows against exact source and immutable fixture/project digests.
4. Re-run critical recovery, secret-leak, destructive-operation, memory-poison and supply-chain tamper veto cases.
5. Verify RC artifact/source/provenance/BOM linkage and capability/limitation declarations.
6. Emit one canonical integrated report whose verdict fails if any critical case is failed, skipped without allowed reason, stale, mixed-SHA or unverifiable.
7. Run final exact-END R16 Integrated Acceptance on Ubuntu and Windows where applicable, plus R0, full Python Core and KodeStudio UI Smoke.
8. Merge the implementation/evidence PR only with exact expected head, then perform exactly one continuity-only R16 phase normalization with fresh exact-head R0/Python/UI before declaring R16/v1.0 phase closure.

## Deliverables

Canonical integrated R16 report and digest; final adversarial/project acceptance workflow; RC evidence index; phase-close continuity evidence.

## Definition of done

- all required critical adversarial/recovery/security cases PASS on the exact final head;
- representative project workflows PASS or a non-core external capability is truthfully `UNAVAILABLE`/`NOT_EXERCISED` according to the frozen plan;
- no critical case is silently skipped;
- integrated report is source/project/case-set/policy bound and independently reproducible;
- exact-END R16 Integrated, R0, Python Core and UI Smoke are all SUCCESS;
- implementation/evidence PR merges with exact expected head;
- exactly one post-merge continuity-only phase normalization passes fresh exact-head R0/Python/UI and merges;
- only that normalized `main` may be called R16 COMPLETE + NORMALIZED / v1.0 phase complete.

## Validation / proof

Canonical integrated report digest plus GitHub Actions run IDs and exact SHA recorded in plan/continuity at END-sync and final normalization. Reuse of earlier subdivision PASS reports is informative only; final critical verdicts are re-executed.

## Rollback

A failed RC is not promoted. Restore prior normalized `main`, discard/revoke candidate artifacts and repair in R16.18 scope unless a frozen earlier subdivision invariant itself is shown invalid, in which case continuity/plan must truthfully record the reopened scope before work continues.

## Risks

Circular evidence; flaky large integrated suite; optional capability mistaken for mandatory or vice versa; stale artifact reuse; release pressure weakening critical veto.

## Manual intervention

**CONDITIONAL.** Core integrated acceptance is CI-owned. Manual evidence is required only for an explicitly claimed optional live capability (for example real GPU ComfyUI qualification, listening/device quality, production signing or publication). If triggered, stop before phase completion and record exact instructions/evidence requirements.

---

## Planning acceptance and authorization boundary

R16 planning itself is accepted only when all of the following are true on one exact planning head:

1. `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` agree on the frozen R16.1–R16.18 subdivision set, statuses and manual states.
2. No R16 implementation code is present in the planning PR.
3. Fresh exact-head **R0 Repository Guard**, **full Python Core** and **KodeStudio UI Smoke** all conclude SUCCESS.
4. The planning PR merges with exact `expected_head_sha`.
5. Exactly one post-merge **planning continuity-only normalization** is created; its diff modifies only `docs/continuity/KODEPOIA_CONTINUITY.md`.
6. That normalization receives fresh exact-head R0/Python/UI SUCCESS and merges with exact expected head.
7. Only the normalized `main` resulting from step 6 authorizes R16.1.

## Recovery if planning acceptance fails

- Do not start R16.1.
- Repair only the planning/continuity authority required by the failing gate.
- Re-run all required exact-head planning gates after any head change.
- Never reuse green runs from an older planning SHA as evidence for a changed head.
- If the subdivision set itself must change before acceptance, update both plan and continuity and explain the reason in the planning PR; after acceptance the set is frozen under the permanent rule.
