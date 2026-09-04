# Kodepoia — R16 detailed phase plan

**Phase:** R16  
**Roadmap title:** Hardening / Beta / v1.0  
**Status:** COMPLETE
**Phase planning started:** 2026-08-31  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `b83c5cf0354f675e468e3ab37c2eefa66aaa9d56`  
**Execution checkpoint:** R1–R15 are COMPLETE + NORMALIZED. R16 planning is ACCEPTED + NORMALIZED. R16.1–R16.17 are COMPLETE + NORMALIZED on exact normalized `main` `41706493d974799b7011953e584b887ca6db1996`. R16.18 is COMPLETE at END-sync on immutable technical source `230ff65feaaa50e9b0c740658e06c74976448908` after fresh exact-source R16.18 #8 / `33833525270`, R16.9 #76 / `33833525226`, R0 #2399 / `33833525292`, Python Core #2371 / `33833525209` 5/5, KodeStudio UI Smoke #2336 / `33833525297` and standalone R16.17 #21 / `33833525293` all SUCCESS. Phase closure remains pending fresh exact-END re-gates, exact-head PR #373 merge, and the unique post-merge continuity-only R16 phase normalization. Optional live capability/manual evidence remains CONDITIONAL / NOT TRIGGERED; no public release/signing/provider cutover is claimed.

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
| R16.11 | Representative real Godot 3D beta project | COMPLETE + NORMALIZED | NONE |
| R16.12 | Representative real Windows desktop application | COMPLETE + NORMALIZED | NONE |
| R16.13 | Representative ComfyUI beta workflow | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |
| R16.14 | Representative audio/voice/cinematic beta workflow | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |
| R16.15 | Long-term project durability, resume and upgrade soak | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |
| R16.16 | Resource, concurrency, leak and diagnostics soak | COMPLETE + NORMALIZED | NONE |
| R16.17 | v1.0 packaging, migration, rollback and release readiness | COMPLETE | CONDITIONAL / NOT TRIGGERED |
| R16.18 | Integrated adversarial + real-project RC acceptance | IN_PROGRESS | CONDITIONAL / NOT TRIGGERED |

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

## R16.12 END authority

- State: **COMPLETE**; manual **NONE**. R16.13 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `270e022a03d7a596eedd27d8989b22278f18cbca`; clean START `e654a7eff3bdfa7c7b5ee1e36d47cfbf20e03c3d`; immutable technical source `7c51c1580ed2c2d9ee18758c6a8cb57dae1ce084`.
- Exact-source technical gates on that source: R16.12 #11 / `33676531167` SUCCESS Windows; R16.9 #40 / `33676531542` SUCCESS Ubuntu + Windows; R0 #2354 / `33676531431` SUCCESS Ubuntu + Windows; Python Core #2326 / `33676531657` SUCCESS 5/5; KodeStudio UI Smoke #2291 / `33676531178` SUCCESS.
- R16.12 focused + supply-chain regression tests: 28/28 PASS. Representative acceptance: 10/10 PASS, `security_claim=true`, `critical_veto=false`, `secret_free=true`, `manual_state=NONE`, no live credentials and no destructive host actions.
- Canonical exercised path: repository-supported WPF under .NET SDK `10.0.400` x64. The representative project path is 161 characters and contains spaces; build/runtime smoke and governed `dotnet publish` succeed without shell interpolation.
- Package evidence on the technical source is unsigned and source-bound: 5 files / 184779 bytes; package manifest `ab2ce29a00714e61b89ef4a2ff5a9703ab17dd249a45b0c366bbe3e881ca4ce5`; package binding `7d569c2bfcc8cbd488cbf81b8c0c2b82c03f6ef66e326aa02c3fb142982c6fec`; diagnostic `528949bdd3f51da4618cc67e4829e5e65ab2095d0838b747a7109c5b41508af2`; semantic `4413d7f755d43759fdf460cc36fcbf4cc5f86b30a9563ccd185ccfd7c292f818`; evidence `65b519ff05e1cfe4dce0dee4b60c373fab134c6b39d1cf7ffce20cef1e0d8321`; artifact `9864607094`, archive SHA-256 `0f6026347f0527456d26ea2246f8043d3384f4d8f1fa7093dbf5408299996fab`.
- Accepted boundaries: WorkspaceBoundary confinement and workspace-escape negative control; malicious project/config text remains data-only; bounded cancellation restores exact bytes; injected build failure recovers through SafeChange; typed SQLite persistence stays workspace-bounded; Windows named-pipe IPC remains local-only and rejects an unauthorized method; package/build evidence remains exact-source and secret-free.
- R16.12 is COMPLETE at END-sync. R16.13 remains unauthorized until this documentation/evidence END head passes fresh exact-head R16.12/R16.9/R0/Python/UI gates, PR #357 merges with `expected_head_sha` equal to that exact END head, and the unique continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

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

## R16.13 START authority

- State: **IN_PROGRESS**; core manual **NONE**; optional live ComfyUI/GPU qualification **CONDITIONAL** only if explicitly requested.
- Exact normalized base: `main` `86a174ab5d627ca9da8a5eb3979e05951582335b`; dedicated branch `r16/13-representative-comfyui-beta-workflow` created directly from that SHA.
- Prior state: R16.1–R16.12 **COMPLETE + NORMALIZED**; R16.14–R16.18 remain **PLANNED**.
- Frozen scope is unchanged: repository-owned representative ComfyUI workflow; authoritative local fixture server; validation, queue/execution transport, progress/events, output collection and cancellation; path escape, untrusted output location, arbitrary command intent and unsafe external-reference negative controls; RAM/VRAM/disk/time budgets; source/workflow/config digest binding and required sanitization. Real local ComfyUI/GPU qualification remains optional and cannot alter the core CI verdict.
- No R16.13 implementation preceded this START-sync. Core acceptance requires no model download, GPU driver change, live ComfyUI server, live credentials or destructive host action.

## R16.13 END authority

- State: **COMPLETE at END-sync**; core manual **NONE**; optional real local ComfyUI/GPU qualification **CONDITIONAL / NOT TRIGGERED**. R16.14 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `86a174ab5d627ca9da8a5eb3979e05951582335b`; clean START-sync `6c16f115c35817dc96954d923688b4488bde515c`; immutable technical source `ef48343a0967920776a2c9849949f3203f5379b6`.
- Fresh exact-technical-head gates on that immutable source are all SUCCESS: R16.13 #4 / `33682108327` Ubuntu + Windows; R16.9 #43 / `33682108284` Ubuntu + Windows; R0 Repository Guard #2359 / `33682108559` Ubuntu + Windows; Python Core #2331 / `33682108533` 5/5; KodeStudio UI Smoke #2296 / `33682108568`.
- Per OS, focused R16.13 plus R16.9 supply-chain regression tests are **31/31 PASS** and representative acceptance is **12/12 PASS** with `security_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, zero live credentials, zero destructive host actions and zero external network calls.
- The authoritative CI fixture is explicitly synthetic: `fixture_is_real_comfyui=false`, `fixture_is_real_gpu=false`; optional live local qualification remains `NOT_EXERCISED`, so no real ComfyUI server/GPU claim is inferred.
- Canonical cross-platform SHA-256 values are identical for material semantics: fixture `703bdfc4383b7b21da105f59622995708b3126d162ee245862a7fe84a54d74ed`; workflow `c359e0505cf1809ad21c1b78749c0a4a5ad235545e3c6872fdd613723c7313c4`; prompt `927a95793dc85ed78ab19a831c5a9b6ac126884e2b1a38511f17317ebf68999b`; budget `68895e08ad203e0aced0b784065ab1fb08a97d7d1cc2a21586b4b165905aa7c3`; output `1a28b874c6e2c8cf8b02a1aede34837bf8ce7576eba1abcc377ee655d459eadb`; binding `2b67d1c077340e9eae70afe45f70208d38db92f052019adb8bb0b87202f04df5`; semantic `d149b518d08bf16f864a7f940ebca13071ae63a888ff08e7b4719c8d7a2247b5`.
- Exact technical-head artifacts from R16.13 #4: Linux `9866650879 / sha256:59fb7a37a77a733216530e2be5ee3660e94a4cafcf8c651d263ff2d6bcb2693a`; Windows `9866670229 / sha256:217e542d8e42f4ff27e4771e6dfaf46d7b0261aaa2dd473480319f0e4252d282`. Platform-specific report evidence SHA-256 is Linux `de77a717a2cfec64a2d597dafa95f01b518986fe4378f4ca7490397f9385c1ab` and Windows `1678f769f51feb26b80d2996798262e46fee9fa6372f5301b72a2fe3d2d134ee`.
- The earlier raw-byte fixture-digest attempt is non-authoritative because LF/CRLF checkout changed its digest. The accepted technical source digests parsed canonical JSON and includes an explicit LF/CRLF-independence regression test.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its resulting exact END head must receive fresh R16.13/R16.9/R0/Python/UI SUCCESS before PR #359 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.13 normalization is authorized after the implementation/evidence merge. Only the resulting normalized `main` may mark R16.13 **COMPLETE + NORMALIZED** and authorize R16.14 START.

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

## R16.14 START authority

- State: **IN_PROGRESS**; core manual **NONE**; optional human listening/device-quality qualification **CONDITIONAL / NOT TRIGGERED** and only if explicitly requested.
- Exact normalized base: `main` `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; dedicated branch `r16/14-representative-audio-voice-cinematic-beta-workflow` created directly from that SHA before implementation.
- Prior state: R16.1–R16.13 **COMPLETE + NORMALIZED**; R16.15–R16.18 remain **PLANNED**.
- Frozen scope is unchanged: one repository-owned short media scenario using synthetic/public-domain text/audio fixtures; audio inspection/QA; supported TTS path; voice-governance/profile checks; alignment/viseme generation; cinematic timing/metadata flow; workspace-bounded generated media/output paths with source/provenance linkage; malformed/unsafe markup and external-reference rejection; resource limits; cancellation/failure with partial-output non-promotion.
- No R16.14 implementation preceded this START-sync. Core acceptance requires no microphone, speakers, device playback, live provider credentials, external service, or destructive host action.

## R16.14 END authority

- State: **COMPLETE at END-sync**; core manual **NONE**; optional human listening/device-quality qualification **CONDITIONAL / NOT TRIGGERED**. R16.15 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `429a018192bcb00221f9fc4e6ae64d0fdbc40cfd`; clean START-sync `7ed6f09262fc259bd875fc76c4583b758474090b`; immutable technical source `92505a002a77c29c5621cdfaa332d43385307b31`.
- Fresh exact-technical-head gates on that immutable source are all SUCCESS: R16.14 #2 / `33709267769` Ubuntu + Windows; R16.9 #47 / `33709267732` Ubuntu + Windows; R0 Repository Guard #2365 / `33709267690` Ubuntu + Windows; Python Core #2337 / `33709267539` 5/5; KodeStudio UI Smoke #2302 / `33709267641`.
- Representative media acceptance is **16/16 PASS** on both hosted OS paths with `security_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, `live_credentials_used=false`, `destructive_host_actions=false` and `external_network_calls=0`. Focused R16.14 plus R16.9 supply-chain regression tests also pass on both OS paths.
- The authoritative CI fixture is explicit synthetic media: `fixture_is_synthetic_audio=true`, `fixture_is_real_tts_runtime=false`, `fixture_is_human_listened=false`; optional human/device listening remains `NOT_EXERCISED`, so no real TTS engine, microphone, speaker, playback-device or subjective-quality claim is inferred.
- Accepted audio facts are deterministic and cross-platform: mono 16-bit PCM WAV, 16000 Hz, 16000 frames, 1.0 second, zero clipped samples. Workspace escape, unsafe external reference, unapproved voice identity/profile use, malformed/unsafe markup, resource-boundary and cancellation/partial-output promotion controls fail closed as required.
- Canonical cross-platform SHA-256 values are identical for material semantics: fixture `bee1f3459d97bc059de630c49afd75aa8156ba14ae3367151660d791f5f5a452`; text `7ac74b671415b23c03a7a044514cf3e5560a9b5b760b31e2c46c857c804ff2d7`; profile `5b3c28c2afd1ac53f1a4e7834bf5e0adc1bde8cb5227250deda853e6f0446dd3`; voice binding `904865b55a531339d527b16be0d3acfc429aa7fa4a322c5ba9550070e6e9f68b`; TTS request `4f2cd932ac4a1e02c78b614eb39226b05909a774925c6abb5ee210be6a5403db`; audio `4d4a7b63ec4e6c9765e5451ec36b4c2c9d28f5fb3a69cba1886d67b9bd29966f`; alignment `e7bf2de62066cfdd2c0c56f9f46e375fdc135cde16821b2047470f1b591da478`; viseme `9bb00001a32380616488ac85b91d8480e1d8e923fed486811af299a354927349`; cinematic `55e4a9044e8cfb8e8cd14cbf0ed574f7f3581061c88cd590ad52670e22bde6d9`; binding `210a9a6cc10890ff4d5467b9783373d45417358181a144d8d060f7b0726a703d`; semantic `62db8be0c807002d2a04549db58a509b613cf6ba18d9493af82e98f3c1bdc3fd`.
- Exact technical-head artifacts from R16.14 #2: Linux `9876404530 / sha256:144502ee168b12fd8e8018da236e7c109fdaf79f17bd98bd0ddeb1c27dc78ee9`; Windows `9876415748 / sha256:20f3669edd24624dd43ca3313c5a8197d7e66104b8861dbd79074cfc4a1d3506`. Report file SHA-256 is Linux `3c5f9b7f857855061b4a473dc643baaacdd4eb4dfd9943ec96837a790919fa9e` and Windows `1a572d3986f653a6de23bf8f61223828f25d859ddc1a362fc507ab9d8ecf55a6`; platform-specific evidence SHA-256 is Linux `4f4419fc01410e68acf3d6fb20a6e4655e4a0ed8149d361bfdbbb0a4fab1c55f` and Windows `9096479309bd95a7f788cdf718a7a6a9fad8845ac5dee05e325a4b901a8690ad`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its resulting exact END head must receive fresh R16.14/R16.9/R0/Python/UI SUCCESS before PR #361 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.14 normalization is authorized after the implementation/evidence merge. Only the resulting normalized `main` may mark R16.14 **COMPLETE + NORMALIZED** and authorize R16.15 START.

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

## R16.15 START authority

- State: **IN_PROGRESS**; core manual **NONE**; optional extended wall-clock/local-environment soak **CONDITIONAL / NOT TRIGGERED** and non-authoritative for core CI unless explicitly requested.
- Exact normalized base: `main` `00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f`; dedicated branch `r16/15-long-term-project-durability-resume-upgrade-soak` created directly from that SHA before implementation.
- R16.14 normalization authority is complete: candidate `82e019f49fe82dc2c2e7c98ce8da70f54a06a548` changed only continuity, passed fresh R0 #2369 / `33711020942` Ubuntu + Windows, Python Core #2341 / `33711020891` 5/5 and KodeStudio UI Smoke #2306 / `33711021031`, then PR #362 merged with `expected_head_sha=82e019f49fe82dc2c2e7c98ce8da70f54a06a548` as normalized `main` `00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f`.
- Prior state: R16.1–R16.14 **COMPLETE + NORMALIZED**; R16.16–R16.18 remain **PLANNED** and unauthorized.
- Frozen R16.15 scope is unchanged: deterministic long-lived project fixture; repeated clean-process session resume; durable-authority reconstruction; representative cross-domain change history; forward schema/version migration and supported rollback/recovery; injected stale/corrupt memory, interrupted-write and partial-artifact checkpoints; orphan/duplicate-authority, silent-loss and stale permission/secret-state rejection; bounded deterministic CI soak plus separately truthful optional extended local soak.
- No R16.15 implementation preceded this START-sync. Core acceptance must remain deterministic, synthetic/bounded, non-destructive, network-independent and free of live credentials.

## R16.15 END authority

- State: **COMPLETE at END-sync**; core manual **NONE**; optional extended wall-clock/local-environment soak **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`. R16.16 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `00cd7b978ea62417cb0bf7ed175d2b2c9e6fe12f`; clean START-sync `cf29886a7f48f1d43e2f57e34a9c3483f4ada519`; immutable technical source `377040f326d2cf87eec4d68b0f90ca2ed615cc04`.
- Fresh exact-technical-head gates on that immutable source are all SUCCESS: R16.15 #13 / `33771718895` Ubuntu + Windows; R16.9 #54 / `33771719752` Ubuntu + Windows; R0 Repository Guard #2374 / `33771719659` Ubuntu + Windows; Python Core #2346 / `33771718602` 5/5; KodeStudio UI Smoke #2311 / `33771718965`.
- Focused R16.15 plus R16.9 supply-chain regression is **31/31 PASS** on both hosted OS paths. Representative durability acceptance is **20/20 PASS** per OS with `durability_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, `external_network_calls=0` and `destructive_host_actions=0`.
- The authoritative bounded profile performs 3 clean-process resume sessions and 8 deterministic soak cycles. Final durable database version is 2 with schema SHA-256 `a489ab34411a5f0ce00b02e09fde1be0a45b3935df6fa696267c3b15ebd91ff5`; failed migration rollback, memory tamper quarantine/recovery and artifact-registry recovery all succeed without promoting corrupt/partial state.
- Canonical cross-platform material SHA-256 values are identical: fixture `9bd8b2e63b1c17b351744e9552da7927c911e7da78ddcd8b25e4dc19a0e899b5`; semantic `1f128da121ebb957b7a1f29dc96007d381ef6ad4f2e340e3c59c10eb0f56dd7c`; policy `f921f368f516523f6a803fd01320a825cc8086189c1ebc77165fd9cd6f77dc05`; authority `be7bf480b34a47175bd4cf8c492ecd3b4d11a097cbe09ee2ba8f132ddda6d5b7`. The earlier raw-checkout-byte fixture digest was rejected as non-authoritative because LF/CRLF checkout differences changed it; the accepted source hashes canonical parsed JSON and includes an explicit LF/CRLF regression.
- Runtime evidence is truthful rather than normalized away: Ubuntu uses CPython 3.12.14 / SQLite 3.45.1; Windows uses CPython 3.12.10 / SQLite 3.49.1. Platform-specific project byte counts and evidence digests are allowed while material semantic/config/fixture authority digests remain identical.
- Exact technical-head artifacts from R16.15 #13 are Linux `9900010682 / sha256:2fee659600eb57e5e58a5988c08c238aeed9538d17e01b8dacff3eab01af96d7` with evidence SHA-256 `333b8a6a4c4caf76444c8800d3243182dcc21906d713c77418bdef810234c8ab`, and Windows `9900045779 / sha256:39fae32fc3e65bb004796a46c7391bea3f82f4bd7d04664f123aa0f918f90f3a` with evidence SHA-256 `653544c4d7555afa64529d53456618819d807ecf7bb720e85cd0abf1e3bbc1f4`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its resulting exact END head must receive fresh R16.15/R16.9/R0/Python/UI SUCCESS before PR #363 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.15 normalization is authorized after the implementation/evidence merge. Only the resulting normalized `main` may mark R16.15 **COMPLETE + NORMALIZED** and authorize R16.16 START.

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

## R16.16 START authority

- State: **IN_PROGRESS**; manual intervention **NONE**.
- Exact normalized R16.15 base: `main` `d19a8b1fa32fa5e28fa23b036407bc5bd902ef92`; dedicated branch `r16/16-resource-concurrency-leak-diagnostics-soak` created directly from that SHA before implementation.
- R16.15 final exact-END `46dc20e7bd734c2902e0c2ac2deb2ef909cf43b3` passed R16.15 #16 / `33773493932` Ubuntu + Windows, R16.9 #56 / `33773493833` Ubuntu + Windows, R0 #2376 / `33773493409` Ubuntu + Windows, Python Core #2348 / `33773494099` 5/5 and KodeStudio UI Smoke #2313 / `33773493773`; PR #363 merged with exact expected head as implementation/evidence `main` `f1a57893f136e5b5b058aa420adcd4f24bf81c9e`.
- The unique R16.15 post-merge continuity-only normalization candidate `86eb24e3e8e42fa6ca46bd1731a42a1877188d80` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #2378 / `33774559173` Ubuntu + Windows, Python Core #2350 / `33774558881` 5/5 and KodeStudio UI Smoke #2315 / `33774559462`, then PR #364 merged with exact expected head as normalized `main` `d19a8b1fa32fa5e28fa23b036407bc5bd902ef92`. No second R16.15 normalization is authorized.
- Prior state: R16.1–R16.15 **COMPLETE + NORMALIZED**; R16.17–R16.18 remain **PLANNED** and unauthorized.
- Frozen R16.16 scope: deterministic bounded load profiles for representative code/Godot/ComfyUI/media/desktop fixtures; CPU/RAM/VRAM/disk/process/time budgets; repeated/concurrent workloads; supported cancellation races; worker/process/file-handle/temp-artifact cleanup; privacy-safe diagnostics; frozen regression thresholds/baselines; explicit environment variance and `INCONCLUSIVE` handling.
- Core acceptance remains bounded, deterministic, network-independent, non-destructive and free of live credentials. Unknown capacity or ambiguous resource state fails closed where the frozen scope requires it.
- No R16.16 implementation bytes precede this START-sync.

## R16.16 END authority

- R16.16 state: **COMPLETE at END-sync**; manual intervention **NONE**. R16.17–R16.18 remain **PLANNED** and unauthorized.
- Exact normalized base: `main` `d19a8b1fa32fa5e28fa23b036407bc5bd902ef92`; clean START-sync `ff971a012a0066b995d52deb1e4e8b0ac0a413de`; immutable technical source `fb34d4a92131fa5cc51e3211405ac38908246d6c`.
- Fresh exact-technical-head gates are all SUCCESS: R16.16 #6 / `33777526743` Ubuntu + Windows; R16.9 #58 / `33777526756` Ubuntu + Windows; R0 Repository Guard #2380 / `33777526844` Ubuntu + Windows; Python Core #2352 / `33777526769` 5/5; KodeStudio UI Smoke #2317 / `33777526726`.
- Focused R16.16 plus R16.9 supply-chain regression is **36/36 PASS** on both hosted OS paths. Representative resource/concurrency/leak/diagnostics acceptance is **18/18 PASS** per OS with `resource_claim=true`, `critical_veto=false`, `secret_free=true`, `core_manual_required=false`, `manual_state=NONE`, `external_network_calls=0` and `destructive_host_actions=0`.
- Five bounded representative profiles (`code`, `comfyui`, `desktop`, `godot`, `media`) are stable across repeats. Each repetition executes 15 operations and generates 565248 transient bytes before complete cleanup; temporary files/bytes and thread delta are zero after each repetition.
- Four workers reach the governed cancellation boundary; all four are cancelled with `post_cancel_mutations=0` and consistent state. Two ProcessSandbox/KillSwitch child processes are signalled and unregistered with `active_after=0` and complete cleanup.
- Canonical cross-platform material SHA-256 values are identical: fixture `72a344812fbcca004dc3b4047b33e5488c2d7da85007a4568d8148034b9ce74c`; policy `f1222282157aa947b8fbeee223e95ad1604cb65a60889745ba186eb9ca3c75de`; semantic `92e9dad3a2d5e0a02e44f5f6c3d8bb6d1d83a438fe87e5565b3aa669a0638dfc`; authority `7e2f33450b1b4ae3a119435385c99cbcdb8d64138197fb20e869129e69e01001`; representative-profile semantic `749eaf6bcb2b6ea2999baa0a6d43917527e270e827803b3f0b602fce6be60206`.
- CPU measurement and the absolute CPU budget are PASS on both hosted OS paths. Repeat-to-repeat CPU variance is truthfully `INCONCLUSIVE` when samples are below the frozen 50 ms significance floor, while a dedicated significant 22x regression negative control still fails closed. VRAM remains `INCONCLUSIVE` on hosted runners rather than a synthetic PASS; if VRAM becomes required, unknown capacity blocks the claim.
- Runtime evidence remains explicit: Ubuntu CPython 3.12.14 with `posix-maxrss`; Windows CPython 3.12.10 with governed `tracemalloc` fallback where the portable working-set probe is unavailable.
- Exact technical-head R16.16 #6 artifacts: Linux `9902269140 / sha256:0838eb2baedb8aed20630778e784296effbf56f002d9398ddc0f9c3ffb2816cc` with evidence SHA-256 `6ae8dd7efcf4f84fab1957c04b03fac2c65f4ac410d29e2636a5ffd6f7a60afa`; Windows `9902209604 / sha256:38463b81bf4ce262fb8c311e857c02061482c3059584a6ae0ff335e6cf587958` with evidence SHA-256 `ca2779324eae245b3e2669b0c6fb9f98db44b6f372761902a6fd8e733a67320c`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its exact resulting head must pass fresh R16.16/R16.9/R0/Python/UI SUCCESS before PR #365 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.16 normalization is authorized. Only the resulting normalized `main` may mark R16.16 **COMPLETE + NORMALIZED** and authorize R16.17 START.

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

## R16.17 START authority

- State: **IN_PROGRESS**; core manual state **CONDITIONAL / NOT TRIGGERED**. R16.18 remains **PLANNED** and unauthorized.
- Exact normalized R16.16 base: `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; dedicated branch `r16/17-v1-packaging-migration-rollback-release-readiness` created directly from that SHA before implementation.
- R16.16 final exact-END `96a1068b678d33778893fc23e096decd3e41e04b` passed R16.16 #9 / `33779722512` Ubuntu + Windows, R16.9 #60 / `33779722137` Ubuntu + Windows, R0 #2382 / `33779722619` Ubuntu + Windows, Python Core #2354 / `33779722505` 5/5 and KodeStudio UI Smoke #2319 / `33779722529`; PR #365 merged with exact expected head as implementation/evidence `main` `068f522b052b820c40474ab8a3c689ac47610761`.
- The unique R16.16 post-merge continuity-only normalization candidate `b260f4c12ae7a9aa84a6fd56a06008e35964abb3` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #2384 / `33782242108` Ubuntu + Windows, Python Core #2356 / `33782241929` 5/5 and KodeStudio UI Smoke #2321 / `33782241719`, then PR #366 merged with exact expected head as normalized `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`. No second R16.16 normalization is authorized.
- Prior state: R16.1–R16.16 **COMPLETE + NORMALIZED**; R16.18 remains **PLANNED** and unauthorized.
- Frozen R16.17 scope: v1.0 RC identity/versioning; deterministic supported package/build artifacts; exact-source manifest/provenance/checksums; dependency/BOM/license evidence; hosted install/extract/consume checks; declared prior-fixture upgrade/migration; rollback/recovery on failure; secure defaults, known limitations and security/privacy/incident/recovery guidance.
- Production signing, store/public registry publication, production credentials and provider/domain cutover remain optional conditional actions and are not inferred from core CI. If explicitly requested, manual intervention becomes required and execution must stop before claiming completion until exact evidence is supplied.
- Core acceptance remains bounded, deterministic, source-bound, non-destructive and free of live production credentials. No public release occurs automatically.
- No R16.17 implementation bytes precede this START-sync.

## R16.17 END authority

- R16.17 state: **COMPLETE at END-sync**; core manual state **CONDITIONAL / NOT TRIGGERED**. Production signing, store/public-registry publication, production credentials and provider/domain cutover remain `NOT_TRIGGERED` / `NOT_EXERCISED`; R16.18 remains **PLANNED** and unauthorized.
- Exact normalized base: `main` `68cc2bb761329b3f1b4932319302db3dcc01cd2b`; clean START-sync `5cbae3c525467c3230d7156649b008e418c3d604`; immutable technical source `496d43bf48d23dd9ffe8283e910aa4bcaa1a2cf0`.
- Fresh exact-technical-head gates are all SUCCESS: R16.17 #13 / `33796341834` Ubuntu + Windows plus `cross-platform-package-determinism`; R16.9 #69 / `33796341820` Ubuntu + Windows; R0 Repository Guard #2390 / `33796341818` Ubuntu + Windows; Python Core #2362 / `33796341864` 5/5; KodeStudio UI Smoke #2327 / `33796341904`.
- Exact-source release-readiness acceptance is **13/13 PASS per OS** with `release_claim=true`, `critical_veto=false`, `core_manual_required=false`, `manual_state=CONDITIONAL_NOT_TRIGGERED`, `production_credentials_used=false`, `public_release_performed=false` and `network_publication_calls=0`.
- RC identity is `kodepoia-v1.0.0rc1` / version `1.0.0rc1`. Hosted installation is offline from `kodepoia-1.0.0rc1-py3-none-any.whl` with no dependency installation and imports the exact RC version.
- Canonical package bytes are identical across Linux and Windows after repository-owned archive-metadata canonicalization. SHA-256: wheel `b4378b6336d8f92e307e81a540e9698fd261dde2c4411fe5c224b16a8ee413e6`; sdist `bfa606908d1a2d34f9d46aaa95acb8087970662d72268e3cd7007987e07fab86`. Same-OS rebuild identity and the dedicated cross-platform comparison both PASS.
- Declared migration from prior fixture version `0.1.0a4` to `1.0.0rc1` passes backup verification, migration and exact rollback/recovery; both migration and failed-migration exact-rollback critical cases PASS.
- Exact-source build manifest/provenance, dependency/BOM/license evidence, secure defaults, known limitations, release notes and security/privacy/incident/recovery guidance all satisfy the frozen R16.17 acceptance contract. Release notes SHA-256 are `d9d0e9ed60c5ee25df2a58307162b65f595fa07c9606d49ef9a22c95582d5375`; security/operations guidance SHA-256 is `2a2bb5e8932c45ed055386f6ab550c92f8c449ba0be0cbac0fee67ac2e302525`.
- Optional production actions remain truthful: external artifact attestation `NOT_EXERCISED`; production credentials `NOT_USED`; production signing, provider/domain cutover, public-registry publication and store submission `NOT_TRIGGERED`. No public release occurred automatically.
- Exact technical-head R16.17 #13 artifacts: Linux `9909316760 / sha256:2375f2796c4300f691055969d06d643604fc83e241d2f859d1c99bd2488a9614`, acceptance evidence SHA-256 `42bcf021a2de790cf376b2f889ce8ef2f058e5b5d4dafbb7b286e8b40bc99873`, report-file SHA-256 `b605c8bd9640edf998e5f35cd6e1881b00f2845474dce537eb30912e06133f2d`; Windows `9909428110 / sha256:3f515dabe3cf38edfbcaebda38d6cfecf364424cff489159ffc609741502de10`, acceptance evidence SHA-256 `9eef0f27bf9234281f8ea4b7cfb59048fc15c851745872b5639a4fd7c6d4621c`, report-file SHA-256 `b645727f0c8b96fa2592650b4fcdbb85515c72180cdaed636259ab4bd41d25e9`.
- This END-sync may change only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the immutable technical source. Its exact resulting head must pass fresh R16.17/R16.9/R0/Python/UI SUCCESS before PR #367 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16.17 normalization is authorized. Only the resulting normalized `main` may mark R16.17 **COMPLETE + NORMALIZED** and authorize R16.18 START.

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

## R16.18 START authority

- State: **IN_PROGRESS**; core integrated acceptance manual state **NONE**. Optional live-capability evidence remains **CONDITIONAL / NOT TRIGGERED** and may become manual only if an optional real GPU/listening/device/production-signing/publication claim is explicitly requested.
- Exact normalized R16.17 base: `main` `41706493d974799b7011953e584b887ca6db1996`; dedicated branch `r16/18-integrated-adversarial-real-project-rc-acceptance` created directly from that SHA before implementation.
- R16.17 final exact-END `add9aa4373933a1d66f3c20f9da1fc9314b7a709` passed R16.17 #16 / `33799259885` Ubuntu + Windows plus `cross-platform-package-determinism`, R16.9 #71 / `33799259616` Ubuntu + Windows, R0 #2392 / `33799259549` Ubuntu + Windows, Python Core #2364 / `33799259554` final 5/5 and KodeStudio UI Smoke #2329 / `33799259784`; PR #367 merged exact head as implementation/evidence `main` `9ccf3415d8090449001dbdd57cec76248a29af00`.
- Unique R16.17 normalization candidate `12aaecf1c49bf55453797e67e47df4540510305f` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #2394 / `33800330466` Ubuntu + Windows, Python Core #2366 / `33800330339` 5/5 and KodeStudio UI Smoke #2331 / `33800330429`, then PR #372 merged with exact expected head as normalized `main` `41706493d974799b7011953e584b887ca6db1996`. No second R16.17 normalization is authorized.
- Prior state: R16.1–R16.17 **COMPLETE + NORMALIZED**. R16.18 is the sole active subdivision and the frozen subdivision set remains unchanged.
- Frozen R16.18 scope is unchanged: independently freeze the integrated case/project set; re-run critical R16.1–R16.9 adversarial/recovery/security cases from clean state on one exact source; re-run representative Godot 2D/3D, Windows, ComfyUI fixture, media and long-term workflows; include resource-soak and RC package/provenance linkage; fail closed on any critical failure, unauthorized skip, stale/mixed-SHA evidence or unverifiable binding; preserve truthful `UNAVAILABLE` / `NOT_EXERCISED` outcomes for non-core optional capabilities.
- Core R16.18 acceptance remains CI-owned, synthetic/bounded where external live capability is not required, non-destructive, network-independent for core verdicts and free of live production credentials. Earlier subdivision PASS reports are informative only; final critical verdicts must be re-executed or independently verified against the exact R16.18 source according to the frozen plan.
- No R16.18 implementation bytes precede this START-sync. No v1.0 public release, production signing, store/public registry publication or provider/domain cutover is authorized by this START.

## R16.18 END authority

- R16.18 state: **COMPLETE at END-sync**; core integrated acceptance manual state **NONE**. Optional live-capability evidence remains **CONDITIONAL / NOT TRIGGERED** and `NOT_EXERCISED`. R16/v1.0 phase closure remains pending fresh exact-END re-gates, exact-head implementation/evidence merge, and the unique post-merge continuity-only R16 phase normalization.
- Exact normalized base: `main` `41706493d974799b7011953e584b887ca6db1996`; immutable technical source `230ff65feaaa50e9b0c740658e06c74976448908`.
- Fresh exact-technical-head gates are all SUCCESS: R16.18 #8 / `33833525270`; R16.9 #76 / `33833525226`; R0 Repository Guard #2399 / `33833525292`; Python Core #2371 / `33833525209` 5/5; KodeStudio UI Smoke #2336 / `33833525297`; standalone R16.17 #21 / `33833525293`.
- Canonical non-circular integrated authority received **33/33** fresh exact-source case/platform reports with `blockers=[]`, `critical_veto=false`, `rc_acceptance_claim=true`, `cross_platform_rc_packages_identical=true`, `historical_evidence_used_for_verdict=false`, `core_manual_required=false` and `manual_state=CONDITIONAL_NOT_TRIGGERED`.
- Canonical digests: authority `43bb342e1c888a07f6ce64c75b7da5e9aadf0e3e09fada478f81cb320def359a`; policy `9835509598f3be0aa32c404dd73cb5f550ba381ac27919f257b79efd35c4e83a`; execution policy `2d35ee076677f247f96a911756bc535119db688e347007f1c46f4c8a0797713c`; integrated contract `71fa8fe1fcab744c30905884a74ac121f8cf41e4ea7d5442fe1c07d59a01d5d3`; canonical report file `a4c43067f369f2c03d84948cf7fad4a7a162c82e80a9edfaff4f3027c7e73600`; GitHub artifact archive `28c905ea2bbafbd755a1cb62037af0ddde6cba64a3868f55000bd301a46171d4`.
- Exact-source RC package SHA-256 is cross-platform identical: wheel `e27ae68aabd90f6c6d22d5223650272c53dfa4fd3bdb342c7085ed79928765af`; sdist `947605aa27d3db7e0bec3e86f39470fd656a2df4c6cf5f9e3d578e96d647f2f0`.
- The superseded cross-platform package mismatch was repaired without weakening the veto by canonicalizing Git checkout line endings before checkout in integrated-case jobs, matching the already accepted R16.17 release-readiness discipline. The accepted exact source remains fail-closed if Linux/Windows RC bytes differ.
- Optional/live truth remains explicit: `optional_live_capabilities=NOT_EXERCISED`; no production credential use, production signing, public release, store/public-registry publication or provider/domain cutover occurred.
- This END-sync changes only `docs/roadmap/R16_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to immutable technical source `230ff65feaaa50e9b0c740658e06c74976448908`. Its exact resulting END head must pass fresh R16.18/R16.9/R0/Python/UI SUCCESS before PR #373 may merge with `expected_head_sha` equal to that exact head.
- Exactly one post-merge continuity-only R16 phase normalization is authorized. Only the normalized `main` produced by its fresh exact-head R0/Python/UI-gated merge may be called **R16 COMPLETE + NORMALIZED / v1.0 phase complete**. No public release is implied by phase completion.
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
