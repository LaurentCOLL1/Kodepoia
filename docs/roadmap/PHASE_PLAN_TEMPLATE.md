# Kodepoia — Phase plan template

Use this template whenever a new major roadmap phase `RX` is started.

The phase plan MUST be created and merged to `main` before implementation of `RX.1` begins. The concrete file name is `docs/roadmap/RX_PLAN.md` (for example `R7_PLAN.md`).

## Phase identity

- **Phase:** `RX`
- **Roadmap title:** `<exact frozen-roadmap title>`
- **Status:** `PLANNING` → `IN PROGRESS` → `COMPLETE`
- **Started:** `<YYYY-MM-DD>`
- **Architecture:** v1.0 frozen unless an accepted ADR explicitly changes it.
- **Source of truth:** normalized current `main`.

## Phase objective

Describe precisely what the phase must deliver, why it exists in the frozen roadmap, what user/product capabilities it enables, and what is explicitly outside this phase.

## Phase-wide architecture and governance boundaries

List every existing boundary that must remain in force, including where relevant:

- `WorkspaceBoundary`;
- `ProcessSandbox` and global KillSwitch;
- Guardian / `PermissionSet`;
- SafeChange snapshots;
- AuditLog hash chain;
- Secrets / Health / Budget / DataGovernance constraints;
- structured Tool APIs instead of arbitrary model-supplied commands;
- loopback-only or other transport restrictions already accepted;
- any phase-specific ADRs or frozen architecture constraints.

## Global prerequisites

List all prerequisites that must be true before `RX.1` starts: accepted earlier phases, required software versions, external tools, accounts, hardware, test fixtures, datasets, credentials/configuration boundaries, and any evidence that must already exist.

## Subdivision index

The complete phase must be decomposed into numbered subdivisions `RX.1`, `RX.2`, `RX.3`, etc. Every subdivision planned for the phase MUST appear here before implementation starts.

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| RX.1 | `<title>` | PLANNED | NONE / REQUIRED / CONDITIONAL | `<dependencies>` |
| RX.2 | `<title>` | PLANNED | NONE / REQUIRED / CONDITIONAL | `<dependencies>` |

Do not silently add, remove, merge, split, or renumber subdivisions. Any scope change must be recorded in this plan and in continuity in the same work cycle; architecture changes require an ADR when applicable.

---

# RX.1 — `<precise title>`

## Objective and rationale

Explain in detail the exact capability, problem being solved, expected behavior, and why this subdivision exists at this point in the dependency chain.

## In scope

List concrete functionality, modules, adapters, schemas, reports, commands, UI, workflows, fixtures, documentation, or integrations included in this subdivision.

## Out of scope

List nearby functionality that must NOT be implemented yet, especially work reserved for later `RX.N` subdivisions or later roadmap phases.

## Dependencies and prerequisites

Specify:

- prior subdivisions that must be COMPLETE;
- required repository state / branch point;
- required runtime or external-tool versions;
- required test data or fixtures;
- required permissions/configuration;
- hardware or OS requirements, if any.

## Detailed implementation plan

Describe the implementation in enough detail that another LLM can resume without guessing. Include expected modules/files, APIs, data models, schemas, persistence locations, orchestration flow, security boundaries, error handling, compatibility behavior, and migration policy.

## Deliverables

Enumerate every expected source file, test, schema, documentation file, fixture, generated evidence type, workflow modification, or other artifact.

## Acceptance gates / Definition of Done

Define exact objective acceptance criteria. Include, as applicable:

- focused tests;
- full regression suite;
- Windows and Ubuntu CI;
- KodeStudio smoke;
- repository guard;
- schema/round-trip validation;
- security/governance checks;
- hardware-local validation;
- external-tool validation;
- performance/budget thresholds;
- produced evidence and exact fields expected;
- PR merge requirement;
- post-merge continuity normalization.

A subdivision is never COMPLETE from partial CI or unverified claims.

## Validation and evidence

Describe exactly what evidence must be preserved: run IDs, commit/head SHA, logs, reports, generated files, benchmark values, screenshots/captures, audit verification, hardware/software versions, or other artifacts.

## Rollback / recovery

Describe how to revert the subdivision safely, including data/schema compatibility, snapshots/backups, reversible migrations, and what must be restored if validation fails.

## Risks and regression traps

Record known technical risks, security concerns, performance risks, concurrency/process risks, protocol sequencing risks, cross-platform differences, and defects from earlier phases that must not regress.

## Manual intervention

Set exactly one state:

- **NONE** — the subdivision can be implemented and authoritatively accepted without user-side execution.
- **REQUIRED** — user-side execution or access is mandatory for acceptance.
- **CONDITIONAL** — normally automated, but a defined condition may require user-side execution.

If the state is `REQUIRED` or `CONDITIONAL`, document ALL of the following before implementation reaches the manual gate:

1. **Reason:** why ChatGPT/GitHub CI cannot authoritatively perform this operation.
2. **Prerequisites:** software, branch/commit, hardware, files, credentials/configuration and safety conditions required first.
3. **Exact actions/commands:** copy-paste-ready commands or precise UI actions, in order.
4. **Expected output:** exact success indicators, files, values, exit codes, log lines or UI state.
5. **Failure recovery:** what to do for common errors and how to return to a safe state.
6. **Evidence to send back:** exactly which logs/files/JSON/screenshots/text the user must provide.
7. **Do not do yet:** actions that must be avoided until the evidence is reviewed.
8. **Privacy/security note:** redact secrets and never request passwords, tokens, private keys or unrelated personal data.

Manual acceptance must never be inferred from silence or from a partial result.

## Completion record

When accepted, append:

- accepted implementation head SHA;
- PR number and merge SHA;
- authoritative CI run IDs and conclusions;
- hardware-local evidence if required;
- manual evidence summary if required;
- post-merge normalization PR/merge if used;
- final status `COMPLETE`.

---

Repeat the complete subdivision section for every planned `RX.N`.

## Phase completion rule

The major phase `RX` can be marked COMPLETE only when every subdivision listed in the phase plan is either:

1. `COMPLETE` with its required acceptance evidence; or
2. explicitly removed from scope by a recorded roadmap/architecture decision, with ADR when required.

No hidden, implied, or undocumented subdivision may be used to claim phase completion.

## Ongoing maintenance rule

Update `RX_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, important recovered defects, or phase ordering changes.