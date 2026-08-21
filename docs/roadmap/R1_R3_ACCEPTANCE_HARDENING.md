# R1–R3 Acceptance Hardening

This corrective phase preserved the frozen Kodepoia v1.0 architecture and closed the acceptance gaps discovered after the initial R1–R3 implementation.

## Final state

- R1: **COMPLETE**.
- R2: **COMPLETE**.
- R3: **COMPLETE — hardware-local acceptance passed**.
- PR #8 — `R1-R3 Acceptance Hardening`: **MERGED into `main`** on 21 August 2026.
- Merge commit: `8e16e6a7d9f6c38d26a663ba9bdafd4950dba7c4`.

## Acceptance rule used

A phase was only considered complete when its frozen requirements had implementation, test/CI evidence where portable, and hardware-local evidence where workstation-dependent.

## R1 acceptance

Accepted capabilities include Guardian decisions, permissions, append-only audit, SafeChange snapshots, ProcessSandbox, Secrets, Schema/DataGovernance, verified backup/restore, atomic recovery/resume, ResearchGuard, global KillSwitch, KodeStudio emergency STOP and Windows UI smoke.

## R2 acceptance

Accepted capabilities include mandatory platform selection, adaptive project questions, platform-specific inputs, performance budgets, capability states, local tool/download/install policies, lineage, YAML Project DNA, PRD/GDD ProductSpec, MVP/requirements/acceptance criteria, traceability, synchronized schemas and the Qt `StrEnum` boundary fix with regression coverage.

## R3 acceptance

Accepted capabilities include model-agnostic KodeBrain, local Ollama streaming/non-streaming, tools, structured output, thinking, images, keep-alive, unload/preload, FAST/CORE/CODER/EMBED/VISION registry/routing, persistent semantic memory, token-budgeted context, streamed orchestration, deterministic repeated benchmarks, strict validators, `done_reason`/budget diagnostics, cold-load separation and local-only `r3-accept`.

Official evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

Accepted defaults on the target workstation:
- `KodeFast` → `granite4.1:3b` — 35/40, 131.366 tok/s; Git worktree is a known 0/5 weakness and must route to CORE/CODER.
- `KodeCore` → `gpt-oss:20b` — 40/40, all eight categories 5/5.
- `KodeCoder` → `ornith:9b` — 40/40, all eight categories 5/5, 64.512 tok/s, ~6.31 GB resident VRAM.

All three final candidates had zero transport errors, preload failures/timeouts and budget exhaustions in the official acceptance. The architecture remains model-agnostic.

## Final CI and merge evidence

Final hardening head: `e3f62b4d74f36e05f3041d56853ad50b7378c73c`.

- R0 Repository Guard run `32504945920` — **SUCCESS**.
- Python Core run `32504946020` — **SUCCESS** on Ubuntu and Windows, including PowerShell runner syntax.
- KodeStudio UI Smoke run `32504946114` — **SUCCESS**.

PR #8 was merged only after these checks were green.

## Phase closure

The R1–R3 acceptance-hardening phase is **CLOSED**. Do not reopen it without new evidence or an ADR-level reason.

**R4 — KodeCode is now AUTHORIZED / NOT STARTED.** New R4 work must branch from the latest `main`.
