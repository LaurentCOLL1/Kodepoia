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
- [x] CI confirmation for this hardening PR.

**R1 acceptance status: COMPLETE.**

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

**R2 acceptance status: COMPLETE.**

## R3 acceptance matrix

- [x] Model-agnostic Brain protocol.
- [x] Ollama local adapter.
- [x] Non-streaming chat.
- [x] Streaming chat.
- [x] Tool-call payload/result support.
- [x] Structured-output payload support.
- [x] Thinking and keep-alive support.
- [x] Image payload support for multimodal Ollama messages.
- [x] Model unload and unscored preload support.
- [x] FAST / CORE / CODER / EMBED / VISION registry and routing.
- [x] Capability-aware routing for tools and structured output.
- [x] Persistent SQLite/WAL memory.
- [x] Embedding persistence and semantic retrieval.
- [x] Semantic retrieval wired into the Orchestrator context path.
- [x] Token-budgeted Context Builder.
- [x] Streaming Orchestrator path.
- [x] Expanded repeated multi-model benchmark.
- [x] Strict validators for exact instruction, Godot 4, typed GDScript, Git worktree, structured JSON and real Ollama tool calls.
- [x] Thinking-budget / `done_reason` diagnostics.
- [x] Cold-load separated from scored correctness.
- [x] `kodepoia r3-accept` enforces two or three distinct installed local models and writes hardware-local evidence.
- [x] CI coverage for benchmark/acceptance hardening.
- [x] Hardware-local R3 acceptance report generated and technically reviewed on the target workstation.

## R3 hardware-local evidence

Official evidence: `.kodepoia/benchmarks/r3-local-acceptance.json` generated on 2026-08-21.

Environment:
- Windows 11;
- Python 3.12.4;
- Ollama 0.32.14;
- loopback URL `http://127.0.0.1:11434` verified;
- 5 repetitions per finalist;
- `temperature=0`;
- `num_predict=1024`;
- profile `full-capability-thinking-aware`;
- `acceptance_completed=true`.

Accepted defaults:
- `KodeFast` → `granite4.1:3b`;
- `KodeCore` → `gpt-oss:20b`;
- `KodeCoder` → `ornith:9b`.

Final results:
- Granite: 35/40, 0.875 x5, 131.366 tok/s, zero errors/preload failures/timeouts/budget exhaustions; its only systematic weakness is Git worktree 0/5, so non-trivial repository decisions are routed to CORE/CODER.
- GPT-OSS: 40/40, 1.0 x5, all eight categories 5/5, 15.909 tok/s, zero errors/preload failures/timeouts/budget exhaustions.
- Ornith: 40/40, 1.0 x5, all eight categories 5/5, 64.512 tok/s, zero errors/preload failures/timeouts/budget exhaustions, ~6.31 GB resident VRAM.

**R3 acceptance status: COMPLETE.**

## Completion policy result

R1, R2 and R3 now satisfy the hardening acceptance policy on this branch.

The remaining integration gate before R4 is repository-level:

1. final CI on the acceptance-documentation head must be green;
2. PR #8 must be merged into `main`;
3. `main` must be verified after merge;
4. continuity must reflect the merged state;
5. only then may R4 begin.
