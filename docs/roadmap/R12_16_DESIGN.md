# R12.16 — Adversarial hardening + Wizard-to-Windows integrated acceptance

## Frozen scope

R12.16 closes R12 without changing architecture v1.0. It hardens the seams accepted in R12.1–R12.15 and proves the phase Definition of Done through the existing Project Wizard and a real hosted Windows build/test path.

Base normalized `main`: `30095003ab5fa61328319be320122ff647ce351a`.
Dedicated branch: `r12/16-adversarial-integrated-acceptance`.
Manual intervention: **CONDITIONAL**.

The manual condition is triggered only if the frozen phase claim requires an interactive/runtime/install Windows semantic that accepted hosted Windows CI cannot establish. Compilation, deterministic WPF harness execution, and semantic package-artifact verification are intended to be proven in CI. No production certificate, Store account, Developer Mode change, trust-store change, or interactive installer action is part of the default R12.16 claim.

## Anti-circular evidence architecture

R12.16 follows the already accepted R11 pattern: implementation must be accepted before a canonical integrated PASS report exists.

1. The first immutable R12.16 implementation candidate contains code, schemas, tests, this design, the acceptance plan, and the Windows CI collector/workflow.
2. `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json` and `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json` are absent from that initial implementation candidate.
3. Exact-head implementation gates run, including the dedicated `R12 Integrated Windows Acceptance` workflow. Its JSON is an Actions artifact tied to the exact candidate SHA, not a checked-in self-attestation.
4. Only after the implementation head is independently accepted is that exact Windows CI artifact reviewed/imported as `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json`.
5. The canonical report generator then binds repository bytes for all R12.1–R12.16 acceptance documents, continuity, the imported Windows CI evidence, and the accepted canonical R11 integrated report.
6. The canonical R12 report never binds itself as an input. Its semantic digest excludes `generated_at` but includes every evidence identity and implementation source SHA.
7. Final documentation/evidence bytes are re-gated on their own exact head before merge.

## Evidence contracts

### Windows CI evidence

`WizardWindowsEvidence` is versioned schema 1 and is valid only when all of these are true:

- `source_sha` is the exact 40-character candidate SHA;
- Project Wizard intent is exactly `desktop_app`, `windows`, `wpf`, `x64`, `archive` for the canonical fixture;
- persisted Project DNA and Product bytes have SHA-256 identities;
- the deterministic R12 scaffold manifest has a SHA-256 identity tied to the persisted DNA/Product digests;
- the shared desktop app model has a SHA-256 identity;
- WPF build and test return codes are both zero;
- the runtime harness sentinel is exactly `KODEPOIA_WPF_TEST_PASS:<model_sha256>`;
- the semantic package artifact manifest has a SHA-256 identity and at least one artifact;
- status is `pass` and blockers is empty;
- `evidence_sha256` is recalculated from all semantic fields except `generated_at` and itself.

The file is validated against `schemas/r12/r12-windows-ci-acceptance.schema.json`.

### Integrated report

`R12IntegratedReport` schema 1 binds:

- exact implementation `source_sha`;
- `docs/continuity/KODEPOIA_CONTINUITY.md` by SHA-256 and byte size;
- exactly sixteen ordered R12 acceptance files, R12.1 through R12.16, each by SHA-256 and byte size;
- the Windows CI evidence file by file SHA-256/size plus its semantic evidence digest and source SHA;
- exactly the accepted R11 integrated report and frozen R11 semantic digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`;
- the satisfied R12.16 manual state (`conditional_not_triggered` or, only if actually triggered and reviewed, `conditional_satisfied`);
- `status=pass`, `blockers=[]`;
- a deterministic semantic `evidence_sha256` excluding only `generated_at` and itself.

The verifier reopens and rehashes every bound repository file. An editable `status=pass` field, a recomputed attacker digest on substituted Windows evidence, or a modified prior R11 report cannot rebind the accepted report because both file and semantic identities are checked.

## Canonical Wizard-to-Windows chain

The Windows collector performs one bounded chain on `windows-latest`:

1. Build Project DNA through `ProjectWizardState` with `ProjectType.DESKTOP_APP`, Windows, WPF, x64, archive.
2. Create a ProductSpec and apply the accepted desktop product intent.
3. Persist DNA + Product through `ProjectInitializer`.
4. Hash the persisted source-of-truth files.
5. Load Kodepoia's owned canonical R12 desktop template.
6. Render/preview/apply it through `DesktopScaffoldEngine` with lineage bound to the DNA/Product digests.
7. Reload the project through `DesktopWorkspaceService`; require truthful `READY` status and `PASS` pure validation without process execution.
8. Map the shared `canonical_sample_app()` through `WpfAdapter`.
9. Discover the accepted .NET 10 toolchain, restore through fixed Kodepoia argv, compile the WPF app and harness, and execute the bounded STA harness through `ProcessSandbox`.
10. Build an `ArtifactManifest` over staging output and call `verify_artifact_tree` before accepting the package-manifest digest.
11. Emit a bounded JSON evidence artifact and validate its strict JSON schema.

This is not an OS installer or Store deployment claim. The package proof is semantic manifest validation over the compiled canonical fixture, consistent with R12.14's frozen local/test-fixture package model.

## Adversarial hardening

`tests/test_desktop_r12_16.py` adds cross-seam attacks beyond ordinary happy-path acceptance:

- acceptance/continuity/Windows-CI evidence substitution;
- prior R11 canonical digest substitution;
- integrated-report digest forgery and self-attestation attempts;
- repository evidence path traversal;
- scaffold path/identifier boundary attacks;
- environment/toolchain injection;
- raw SQL table/identifier injection;
- IPC HMAC tampering, replay and oversized frames;
- KillSwitch/cancellation race with owned-operation cleanup;
- package artifact mutation after manifest creation.

Existing R12.1–R12.15 focused tests and all five framework regression workflows remain in force; R12.16 does not duplicate or weaken their coverage.

## Security boundaries

- No arbitrary executable, shell string, raw argv, MSBuild/CMake/Cargo flag, SQL, signing key, certificate, or updater credential is introduced.
- Windows external process execution remains through accepted adapters and ProcessSandbox.
- Project/scaffold/evidence paths remain repository/workspace bounded and symlink-sensitive.
- No network listener is introduced; IPC remains local-only.
- No production signing or installer trust claim is made.
- No evidence field can convert missing/failed evidence into PASS.
- The integrated report is generated only after an independently accepted implementation SHA exists.

## Manual-gate decision rule

At subdivision start the condition is **NOT TRIGGERED**. Hosted Windows CI can prove the frozen create/scaffold/compile/test path and WPF harness runtime semantic. If implementation later demonstrates that phase completion truly depends on an interactive launch, Developer Mode, package installation, certificate trust, or another runtime semantic that hosted CI cannot safely establish, R12.16 becomes `BLOCKED / MANUAL_REQUIRED`; no final report or R13 work may proceed until bounded exact-head evidence is reviewed.

## Rollback / recovery

- If implementation tests fail, correct only R12.16 on this branch and restart exact-head acceptance from the new SHA.
- Failed/rejected candidate artifacts are never reused.
- If Windows CI evidence does not match the immutable candidate SHA or semantic digest, discard it and rerun on the correct head; do not edit it into PASS.
- If final evidence/documentation changes bytes, re-gate the resulting exact head before merge.
- After the implementation/evidence merge, exactly one continuity-only normalization is allowed; any code/plan change during normalization is a governance defect.
