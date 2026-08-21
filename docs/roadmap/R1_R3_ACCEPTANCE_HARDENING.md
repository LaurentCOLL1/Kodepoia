# R1–R3 Acceptance Hardening

This corrective phase preserves the frozen Kodepoia v1.0 architecture and closes acceptance gaps found during the post-R3 audit.

## Rule

A roadmap phase may be marked `COMPLETE` only when each frozen requirement has all of the following:

1. an implementation;
2. an automated test where automation is possible;
3. CI evidence for repository-portable behavior;
4. hardware-local evidence when the requirement depends on the target workstation.

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
- [ ] CI confirmation for this hardening PR.

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
- [ ] CI confirmation for this hardening PR.

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
- [ ] CI confirmation for this hardening PR.
- [ ] Hardware-local R3 acceptance report generated on the target workstation.

## Completion policy

R1 and R2 may be marked `COMPLETE` after their CI acceptance checks pass.

R3 must remain incomplete until the target workstation runs, with two or three real installed Ollama candidates:

```powershell
kodepoia ollama-status
kodepoia r3-accept --model <candidate1> --model <candidate2> [--model <candidate3>]
```

The generated `.kodepoia/benchmarks/r3-local-acceptance.json` is the hardware-local acceptance evidence. R4 must not begin before that evidence exists and R3 is marked `COMPLETE`.
