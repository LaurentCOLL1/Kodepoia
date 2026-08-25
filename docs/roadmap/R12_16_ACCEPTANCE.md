# R12.16 — Acceptance

## Scope

Adversarial hardening + anti-circular Wizard-to-Windows integrated acceptance only.

Base normalized `main`: `30095003ab5fa61328319be320122ff647ce351a`.
Branch: `r12/16-adversarial-integrated-acceptance`.
Manual intervention: **CONDITIONAL / NOT TRIGGERED**.

The conditional manual trigger was evaluated after the accepted implementation gates. It did **not** trigger because hosted Windows CI established the frozen R12 Definition of Done: the existing Project Wizard produced desktop DNA/Product intent, deterministic scaffold output was created and reloaded through DesktopWorkspaceService, a modern Windows WPF fixture compiled and its runtime test passed under .NET 10, and the resulting application artifact tree was semantically manifested and reverified. R12 does not claim interactive installation, Microsoft Store publication, production signing, or Developer Mode launch semantics.

## Required implementation acceptance

The immutable pre-report implementation candidate contains:

- `src/kodepoia/desktop/integrated_acceptance.py` with strict evidence bindings and anti-circular verifier;
- strict schemas `schemas/r12/r12-windows-ci-acceptance.schema.json` and `schemas/r12/r12-integrated-acceptance.schema.json`;
- `scripts/r12_16_windows_ci_acceptance.py` producing candidate-bound Windows CI evidence;
- `scripts/r12_16_build_integrated_report.py` capable of generating the later canonical report but unable to succeed without already accepted Windows CI evidence;
- `.github/workflows/r12-integrated-windows.yml` on `windows-latest` + Python 3.12 + .NET 10;
- `tests/test_desktop_r12_16.py` covering evidence substitution plus path/env/SQL/IPC/cancellation/package attacks;
- this acceptance and `R12_16_DESIGN.md`;
- no checked-in `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json` and no checked-in `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json` on the immutable implementation candidate before its independent acceptance.

Required exact-head implementation gates:

- R0 Repository Guard;
- full Python Core, including Linux/Windows test matrix and package build evidence defined by the workflow;
- KodeStudio UI Smoke;
- WPF, WinUI, Avalonia, Qt and Tauri regression workflows;
- dedicated `R12 Integrated Windows Acceptance` on the same exact candidate SHA.

The dedicated Windows workflow must create one Project Wizard desktop intent, persist DNA/Product, scaffold deterministically, reload via DesktopWorkspaceService, compile/test the WPF shared model through ProcessSandbox, verify semantic package artifacts, emit a schema-valid JSON artifact and exit successfully.

## Accepted implementation source

Accepted immutable implementation SHA: **`1927d9ab673228101c932b1cb6b89243296ac957`**.

Exact-head gates on that SHA — all `SUCCESS`:

- R0 Repository Guard #1590 / run `32842609351`;
- Python Core #1564 / run `32842609414`;
- KodeStudio UI Smoke #1531 / run `32842609362`;
- R12 WPF Acceptance #79 / run `32842609356`;
- R12 WinUI3 Acceptance #69 / run `32842609315`;
- R12 Avalonia Acceptance #65 / run `32842609365`;
- R12 Qt6 Acceptance #60 / run `32842609324`;
- R12 Tauri2 Acceptance #51 / run `32842609391`;
- R12 Integrated Windows Acceptance #4 / run `32842609416`.

Rejected implementation candidates are never reusable evidence:

- `64035fc92757e275bdf13eda60d6a47596b22c2e` — rejected because one adversarial test assertion expected the wrong error-message regex even though the boundary correctly failed closed;
- `af2daa01d4c98c2a6ce7ba48830819f513d8e741` — rejected because the integrated collector attempted package verification over the mutable global staging tree rather than an isolated application artifact tree.

The accepted fix snapshots only `app/Release/net10.0-windows` into a dedicated `package-artifact` tree before semantic manifest construction and verification.

## Accepted Windows CI evidence

Exact workflow artifact: `r12-16-windows-ci-1927d9ab673228101c932b1cb6b89243296ac957` from run `32842609416`.

Artifact metadata digest: `sha256:1ca4e2f65f7fa9563598de93c6e0c90a984231554fa6d0d982ff4690baa6a21e`.

Imported repository evidence path: `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json`.

Evidence facts:

- `source_sha = 1927d9ab673228101c932b1cb6b89243296ac957`;
- `status = pass`, `blockers = []`;
- `build_returncode = 0`, `test_returncode = 0`;
- semantic evidence digest `0bbead835c2ee48f4d6a78f11f6aceaca60262eebe70c3944f6475ae82b70a24`;
- canonical shared-model digest `3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0`;
- package-manifest digest `4debf90eddd3dca3f3af05c6ab245b06246e6d6eb538bd3b769c575a8a1401e1`;
- 5 application artifacts in the isolated package tree;
- runtime sentinel `KODEPOIA_WPF_TEST_PASS:3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0`.

## Anti-circular evidence ordering

1. Freeze one immutable implementation head while both canonical checked-in R12 evidence JSON files are absent.
2. Require all implementation gates above on exactly that head.
3. Decide the CONDITIONAL manual trigger truthfully from the actual frozen claim and CI results.
4. If manual is required, stop and collect/review exact-head manual evidence before proceeding; otherwise record `conditional_not_triggered`.
5. Freeze implementation SHA + run IDs in this acceptance/PR metadata without changing the accepted implementation bytes.
6. Download the exact `R12 Integrated Windows Acceptance` artifact from that candidate; verify its source SHA, schema and semantic digest; import it unchanged as `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json`.
7. Perform the required **end-of-subdivision** synchronization: `R12_PLAN.md` + continuity mark R12.16 `COMPLETE` while preserving the accepted implementation source SHA.
8. Generate `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json` with `scripts/r12_16_build_integrated_report.py --source-sha 1927d9ab673228101c932b1cb6b89243296ac957` only after the stable acceptance/plan/continuity/evidence bytes above exist.
9. Validate the report schema and call `validate_repository_evidence`; it must bind all R12.1–R12.16 acceptances, the end-synchronized continuity bytes, exact Windows CI evidence and canonical R11 digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`.
10. Freeze the final evidence/documentation head and run fresh exact-head R0/full Python/UI plus desktop adapter regressions and integrated Windows acceptance.
11. Merge the implementation/evidence PR only with `expected_head_sha` equal to that accepted final head.
12. Create exactly one continuity-only R12.16 post-merge normalization; gate its exact head with the same standard family and merge with expected SHA.
13. Only after that normalization merge is R12 `COMPLETE + NORMALIZED`; only then may R13 planning start.

## Evidence state at acceptance freeze

Start-of-subdivision plan/continuity synchronization: **DONE**.

Normalized base: `30095003ab5fa61328319be320122ff647ce351a`.

Accepted implementation candidate: **`1927d9ab673228101c932b1cb6b89243296ac957`**.
Implementation exact-head gates: **9/9 SUCCESS**.
Dedicated Windows CI artifact: **PASS, downloaded and verified**.
Manual state: **CONDITIONAL / NOT TRIGGERED (`conditional_not_triggered`)**.
Checked-in Windows CI evidence: **AUTHORIZED in the end-of-subdivision documentation/evidence commit**.
End-of-subdivision plan/continuity synchronization: **AUTHORIZED in the same commit; R12.16 becomes COMPLETE before report generation**.
Canonical `R12_INTEGRATED_ACCEPTANCE.json`: **MUST be generated only after this acceptance + plan + continuity + Windows CI evidence are frozen; this file must not be edited after report generation because the report binds it by bytes/digest**.
Final evidence/documentation gates and merge results: **must be recorded in PR metadata and then in the single post-merge continuity normalization, not by mutating this report-bound acceptance**.

## Failure policy

Any failed gate rejects that exact candidate. Correct only R12.16, freeze a new SHA, and restart every required implementation gate. Missing evidence, stale workflow runs, editable `status=pass`, mismatched source SHA, recomputed attacker digests, or prior-phase substitution never manufacture PASS.
