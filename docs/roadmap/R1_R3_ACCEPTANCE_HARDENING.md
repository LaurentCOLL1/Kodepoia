# R1–R3 Acceptance Hardening

This corrective phase preserves the frozen Kodepoia v1.0 architecture and closes acceptance gaps found during the post-R3 audit.

## Rule

A roadmap phase may be marked `COMPLETE` only when each frozen requirement has all of the following:

1. an implementation;
2. an automated test where automation is possible;
3. CI evidence for repository-portable behavior;
4. hardware-local evidence when the requirement depends on the target workstation.

## Latest CI evidence

Validated commit: `e2cc5cb624e14c459b92fd9128343c8e2b4a1d1f`

- `R0 Repository Guard` run `32456258458`: **SUCCESS** on Windows and Ubuntu.
- `Python Core` run `32456258437`: **SUCCESS** on Windows and Ubuntu, including its Windows KodeStudio smoke job.
- `KodeStudio UI Smoke` run `32456258443`: **SUCCESS** on Windows.

The R2 Qt/`StrEnum` regression is covered by the UI smoke suite. Qt combo boxes now store primitive string values and every Qt → domain boundary explicitly reconstructs the expected `StrEnum` (`ProjectType`, `Dimension`, `DecisionState`, `ApprovalPolicy`, `ProductDocumentType`, and capability states).

## R1 acceptance matrix

- [x] Guardian deterministic allow / confirm / deny decisions.
- [x] Permission scopes.
- [x] Append-only audit chain.
- [x] SafeChange snapshots.
- [x] Restricted ProcessSandbox.
- [x] Secrets redaction.
- [x] Schema migration support.
- [x] Data governance.
- [x] Verified SHA-256 backup archives and restore.
- [x] Atomic recovery checkpoint and simulated restart/resume.
- [x] ResearchGuard.
- [x] Global KillSwitch capable of terminating active protected subprocesses.
- [x] KodeStudio exposes the emergency stop.
- [x] KodeStudio offscreen UI smoke test exists.
- [x] CI confirmation for this hardening PR.

**R1 acceptance status on the hardening branch: COMPLETE.**

## R2 acceptance matrix

- [x] Mandatory target platform selection.
- [x] Adaptive game/non-game questions.
- [x] Mobile input questions only when Android/iOS is targeted.
- [x] XR input questions only when XR is targeted.
- [x] Graphics style and genres.
- [x] Per-target performance budgets.
- [x] YES / NO / UNDECIDED capability states.
- [x] Local AI/creation tool choices.
- [x] Download and install policies.
- [x] Project lineage.
- [x] YAML Project DNA persistence.
- [x] PRD/GDD ProductSpec, MVP, requirements and acceptance criteria.
- [x] Requirement traceability to code/test references.
- [x] Project DNA and ProductSpec JSON Schemas synchronized with the Python domain model.
- [x] KodeStudio exposes the same validated domain model.
- [x] Windows-only validation rejects mobile-only inputs.
- [x] Qt `StrEnum` boundaries normalized and regression-tested.
- [x] CI confirmation for this hardening PR.

**R2 acceptance status on the hardening branch: COMPLETE.**

## R3 acceptance matrix

- [x] Model-agnostic Brain protocol.
- [x] Ollama local adapter.
- [x] Non-streaming chat.
- [x] Streaming chat.
- [x] Tool-call payload/result support.
- [x] Structured-output payload support.
- [x] Thinking and keep-alive support.
- [x] Image payload support for multimodal Ollama messages.
- [x] Model unload support.
- [x] FAST / CORE / CODER / EMBED / VISION registry and routing.
- [x] Capability-aware routing for tools and structured output.
- [x] Persistent SQLite/WAL memory.
- [x] Embedding persistence and semantic retrieval.
- [x] Semantic retrieval wired into the Orchestrator context path.
- [x] Token-budgeted Context Builder.
- [x] Streaming Orchestrator path.
- [x] Expanded multi-model R3 baseline benchmark.
- [x] `kodepoia r3-accept` enforces two or three distinct installed local models and writes a hardware-local evidence report.
- [x] CI confirmation for this hardening PR.
- [ ] Hardware-local R3 acceptance report generated on the target workstation.

**R3 status: IMPLEMENTATION COMPLETE — HARDWARE-LOCAL ACCEPTANCE PENDING.**

## Hardware-local acceptance preparation

Windows helper:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
.\scripts\r3_accept_local.ps1 -Model modelA,modelB
# or
.\scripts\r3_accept_local.ps1 -Model modelA,modelB,modelC
```

Detailed procedure: `docs/roadmap/R3_LOCAL_ACCEPTANCE.md`.

The helper verifies Python 3.12+, loopback-only Ollama, runs `ollama-status`, invokes `r3-accept`, and structurally verifies the generated evidence report.

The generated `.kodepoia/benchmarks/r3-local-acceptance.json` remains the hardware-local acceptance evidence.

## Completion policy

R1 and R2 are technically accepted on the hardening branch after the green CI evidence above.

R3 must remain incomplete until the target workstation runs, with two or three real installed Ollama candidates:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
.\scripts\r3_accept_local.ps1 -Model <candidate1>,<candidate2>[,<candidate3>]
```

Then review `.kodepoia/benchmarks/r3-local-acceptance.json` for model quality, errors, throughput and VRAM information.

PR #8 must remain unmerged while R3 hardware acceptance is pending. R4 must not begin before the R3 evidence has been generated and reviewed.
