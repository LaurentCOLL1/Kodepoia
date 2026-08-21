# R2 — Project Wizard + Project DNA + KodeProduct — Status

**Phase:** R2  
**Status:** COMPLETE ON R1–R3 HARDENING BRANCH  
**Accepted:** 2026-08-21

## Validation evidence

Original implementation:
- PR #4 — `R2: implement Project Wizard, Project DNA and KodeProduct`.
- Merge commit: `ae5283df4468e03f2ab1d7a11e3708913539d7e7`.

Acceptance hardening:
- PR #8 — `R1-R3 Acceptance Hardening` (still open while R3 hardware-local acceptance is pending).
- Validated hardening commit: `e2cc5cb624e14c459b92fd9128343c8e2b4a1d1f`.
- `R0 Repository Guard` run `32456258458`: SUCCESS on Windows and Ubuntu.
- `Python Core` run `32456258437`: SUCCESS on Windows and Ubuntu; Windows KodeStudio smoke job SUCCESS.
- `KodeStudio UI Smoke` run `32456258443`: SUCCESS on Windows.

## Implemented and accepted

- [x] Mandatory target-platform selection in Project DNA.
- [x] Game/application/tool/plugin/library/AI project types.
- [x] 2D / 2.5D / 3D / hybrid dimensions.
- [x] YES / NO / UNDECIDED capability states.
- [x] Platform-specific performance budgets.
- [x] Validation rejecting mobile-only inputs for a Windows-only project.
- [x] Adaptive questions: touch/gyro/accelerometer only for Android/iOS; motion controllers only for XR.
- [x] Genres and graphics style.
- [x] Online and multiplayer decisions.
- [x] Ollama / Blender / ComfyUI / research tool choices.
- [x] Download and install approval policies.
- [x] Project lineage fields.
- [x] YAML persistence under `.kodepoia/project.yaml`.
- [x] Project initializer creates the persistent `.kodepoia/` workspace.
- [x] KodeProduct PRD/GDD model with vision, goals, metrics, constraints, MVP, requirements and acceptance criteria.
- [x] Requirement traceability hooks to code refs and test refs.
- [x] Machine-readable JSON schemas synchronized with Project DNA and ProductSpec.
- [x] CLI `kodepoia project-init`.
- [x] KodeStudio New Project dialog using the same validated domain model.
- [x] Qt → domain `StrEnum` boundary normalized for `ProjectType`, `Dimension`, `DecisionState`, `ApprovalPolicy`, `ProductDocumentType` and capability states.
- [x] Qt regression tests verify game/non-game adaptation and Android touch visibility.

## Qt boundary rule

KodeStudio combo boxes store primitive string values in Qt item data. Domain values are reconstructed explicitly at the UI boundary before comparisons or model construction. Do not rely on object identity of `QComboBox.currentData()` for Python `StrEnum` values.

## Merge note

R2 is accepted on `agent/r1-r3-acceptance-hardening`, but the PR is intentionally not merged yet because the same PR contains R3 hardening and R3 still requires hardware-local model acceptance on the target workstation.
