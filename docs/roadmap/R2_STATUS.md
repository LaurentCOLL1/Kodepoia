# R2 — Project Wizard + Project DNA + KodeProduct — Status

**Phase:** R2  
**Status:** IMPLEMENTED — awaiting PR validation/merge  
**Date:** 2026-08-21

## Implemented

- [x] Mandatory target-platform selection in Project DNA.
- [x] Game/application/tool/plugin/library/AI project types.
- [x] 2D / 2.5D / 3D / hybrid dimensions.
- [x] YES / NO / UNDECIDED capability states.
- [x] Platform-specific performance budgets.
- [x] Validation that rejects mobile-only inputs for a Windows-only project.
- [x] Adaptive question list: touch/gyro only appears for Android/iOS.
- [x] YAML persistence under `.kodepoia/project.yaml`.
- [x] Project initializer creates the persistent `.kodepoia/` workspace.
- [x] KodeProduct PRD/GDD model with requirements, priorities and acceptance criteria.
- [x] Requirement traceability hooks to code refs and test refs.
- [x] Machine-readable JSON schemas for Project DNA and Product Spec.
- [x] CLI `kodepoia project-init`.
- [x] KodeStudio New Project dialog using the same validated domain model.

## Acceptance

The R2 PR must pass all existing Windows/Ubuntu R0 and Python Core checks before merge.
