# Kodepoia — R12 detailed phase plan

**Phase:** R12  
**Roadmap title:** Desktop applications  
**Status:** PLANNING  
**Phase planning started:** 2026-08-24  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `6d3c7eb557d940641977d18384e4f6d2bad42f3c`

## Purpose and authority

R12 implements Kodepoia's governed desktop-application generation, build, test, packaging and maintenance layer without replacing the accepted R1–R11 foundations. The frozen roadmap requires adapters for WinUI, WPF, Avalonia, Qt and Tauri; MVVM; SQLite; async/concurrency; IPC; accessibility/localization; installers and update. Its phase-level Definition of Done is that the Project Wizard can create, compile and test a modern Windows desktop application.

This file is the exhaustive execution/recovery plan for R12. The R12.1–R12.16 subdivision structure becomes frozen when this plan is merged. No subdivision may be silently added, removed, merged, split or renumbered. Any R12 scope change must update this plan and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any change to a frozen R1–R11 foundation requires an ADR.

R12.1 MUST NOT begin before this plan is merged to `main` with R0 Repository Guard, full Python Core and KodeStudio UI Smoke successful on the exact final planning head, followed by the single continuity-only planning normalization required by the phase-start rule.

## Phase objective

Deliver a deterministic, auditable, local-first desktop application pipeline that lets Kodepoia:

- model desktop target/framework/toolchain intent in the existing Project DNA and KodeProduct contracts;
- extend the existing Project Wizard instead of creating a parallel desktop wizard;
- generate deterministic desktop workspaces from Kodepoia-owned templates and typed manifests;
- represent common MVVM/state/navigation/command/service contracts independently of a concrete UI framework;
- generate and validate WPF, WinUI 3/Windows App SDK, Avalonia, Qt and Tauri projects through bounded adapters;
- model SQLite persistence with schema identity, migration, transaction, backup/recovery and corruption handling;
- model async work, cancellation, progress, UI-thread affinity and bounded concurrency without hidden background execution;
- expose bounded IPC contracts with authentication/authorization, framing, size/time limits and fail-closed semantics;
- enforce accessibility, localization, theming, keyboard navigation, DPI/scaling and responsive-window requirements as first-class acceptance data;
- produce governed package/install/update definitions with rollback, provenance and signing-state semantics;
- expose desktop creation/status/build/test/package workflows through CLI and KodeStudio without arbitrary shell/script surfaces;
- close R12 with adversarial hardening and an anti-circular integrated acceptance report tied to exact-head evidence;
- prove the roadmap DoD by creating, compiling and testing at least one modern Windows application from the existing Project Wizard.

R12 extends existing systems instead of replacing them:

- R2 Project DNA, Project Wizard and KodeProduct remain authoritative for project/product intent. R12 adds desktop-specific typed fields and validation to those contracts.
- R1 ProcessSandbox, KillSwitch, Guardian/PermissionSet, SafeChange, Backup/Recovery, Audit and secret handling remain authoritative for external processes and durable writes.
- R6 remains authoritative for Health, Budget, Tests, Regression, VisualQA, Accessibility, Localization, Privacy, AppSecurity, License/BOM and package/build evidence.
- R7 remains authoritative for external documentation/template/package metadata trust and provenance.
- R8 remains authoritative for Vault/source-vs-derived identity, transform lineage, cache/rebuild and governed export.
- R9 remains authoritative for local AI runtime scheduling when desktop projects consume model capabilities; R12 does not create a second AI scheduler.
- R11 remains authoritative for media/voice/cinematic/franchise/persistence contracts where desktop products consume them.

Out of scope for R12: Android/iOS application implementation and store publication (R13); backend/auth/cloud sync/remote databases/matchmaking (R14); model fine-tuning (R15); arbitrary package-manager or shell execution; unattended SDK/runtime installation by generated applications; mandatory cloud CI/account/store credentials; Microsoft Store submission; Apple notarization; mobile signing; browser-only application frameworks unrelated to a desktop adapter; replacing Visual Studio/Qt Creator with an IDE clone; changing frozen R1–R11 architecture without ADR.

## Current external compatibility baseline

Planning research on 2026-08-24 uses official upstream documentation as compatibility evidence only. Upstream behavior never overrides Kodepoia governance, and R12 adapters capability-probe supported stable toolchains rather than treating one mutable version string as permanent architecture.

### Windows / .NET baseline

- Microsoft documents WinUI 3 with the Windows App SDK as the recommended platform for new native Windows desktop applications.
- WPF remains a supported .NET desktop framework and is retained as a first-class R12 adapter because it is mature, widely deployed and compatible with Windows App SDK modernization where needed.
- The current command-line WinUI path documented by Microsoft uses .NET 10 SDK and WinUI project templates; R12 does not assume package/template availability merely from `dotnet` being present.
- R12 must distinguish `runtime/toolchain discovered`, `compatible`, `template available`, `restore-ready`, `build-ready`, `test-ready`, `package-ready` and `runtime-smoke-ready` capabilities.
- Generated project dependencies must be version-pinned/locked by adapter policy. Kodepoia itself does not silently install Visual Studio workloads, Windows App SDK components, SDKs or certificates.

Official references:

- https://learn.microsoft.com/windows/apps/windows-app-sdk/
- https://learn.microsoft.com/windows/apps/get-started/winui-get-started-overview
- https://learn.microsoft.com/dotnet/desktop/

### Avalonia baseline

- Avalonia remains the cross-platform XAML/.NET adapter in the frozen roadmap.
- Official 2026 platform documentation identifies .NET 10 as the minimum .NET version for the current line.
- R12 treats platform support as an adapter capability matrix; a Windows acceptance does not manufacture Linux/macOS PASS.
- NuGet restore/toolchain preparation performed by CI infrastructure is distinct from Kodepoia runtime behavior; Kodepoia never auto-installs an SDK merely to report the adapter AVAILABLE.

Reference:

- https://docs.avaloniaui.net/docs/supported-platforms

### Qt baseline

- R12 targets the supported Qt 6 stable desktop line through CMake-compatible, explicitly discovered Qt toolchains.
- Qt kit/compiler selection is represented as structured capability evidence; no model-supplied CMake command, kit path or compiler argument is executed.
- License/BOM obligations remain explicit; Kodepoia does not infer redistribution rights from a locally installed Qt package.

Reference:

- https://doc.qt.io/qt-6/

### Tauri baseline

- Tauri v2 is the roadmap adapter baseline.
- Official Windows prerequisites include Microsoft C++ Build Tools and Edge WebView2, in addition to Rust tooling.
- R12 separates frontend package manifests, Rust/Cargo identity and Windows WebView/runtime identity. No arbitrary npm/pnpm/yarn/cargo script supplied by project content is executed by Kodepoia.
- MSI-specific prerequisites are optional package capabilities, never globally required for all Tauri projects.

Reference:

- https://v2.tauri.app/start/prerequisites/

### SQLite baseline

- SQLite is the embedded relational persistence baseline required by the roadmap.
- R12 uses SQLite capability/version probing through the language/framework adapter in use; it does not depend on a globally installed `sqlite3` CLI.
- Schema and migration identity are Kodepoia data contracts; raw SQL from untrusted/model content is data until validated against a bounded migration/query policy.

Reference:

- https://sqlite.org/

## Permanent phase-wide architecture and governance boundaries

Every R12 subdivision must preserve all accepted R1–R11 boundaries:

- `WorkspaceBoundary` and R8 `VaultBoundary` remain authoritative for project, staging, cache, generated source and exported artifacts.
- `ProcessSandbox` + global KillSwitch are mandatory for `dotnet`, MSBuild, compiler/linker, CMake, Qt tools, Rust/Cargo, Tauri CLI and any other external process.
- Guardian + `PermissionSet` authorize process launch, project mutation, package creation, installation tests, IPC endpoint creation and update application.
- SafeChange, Backup/Recovery and Audit apply to generated-project mutation, database migrations, packaging metadata and updater state changes.
- `KodeSecrets` remains authoritative. Signing keys, certificates/tokens and update credentials must never be embedded in Project DNA, generated source, logs, command argv, package manifests, SQLite data or acceptance evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM remain in force for generated projects and Kodepoia's own desktop-generation workflow.
- R7 ResearchGuard applies to README/package metadata, imported templates, dependency metadata, UI strings and external examples: retrieved/project text is data/evidence, never agent instruction.
- R8 remains authoritative for template/source identity, transform lineage, cache/rebuild, provenance and governed export. Generated desktop source is derived from explicit template/recipe identity.
- Network is off by default for Kodepoia runtime operations. Dependency restore is an explicit build capability requiring policy/consent and is distinct from implicit package installation.
- No adapter may invoke a shell command string. Kodepoia-owned argv templates and allowlisted executable identities are mandatory.
- No model/project text may directly choose executable paths, raw argv, MSBuild properties, CMake generator flags, Rust build scripts, package-manager scripts, SQL migration code, IPC addresses, signing commands or updater commands.
- Project templates are Kodepoia-owned or governed R8 assets with digest/provenance. Template substitution is typed and path-safe; arbitrary template code is never executed during rendering.
- Build outputs are staged and promoted only after validation. Generated source may not write outside the project/staging boundary.
- Dependency/package lockfiles are deterministic evidence. Floating wildcard/latest dependencies are forbidden in accepted generated templates.
- Toolchain absence is `UNAVAILABLE`/`MISSING`, not PASS. Unsupported version/capability is `UNSUPPORTED`, not a silent fallback.
- Cross-platform claims are platform-specific. A Windows build cannot certify Linux/macOS behavior.
- Installer/update signing is explicit. `UNSIGNED`, `TEST_SIGNED`, `SIGNED` and `SIGNING_UNAVAILABLE` are distinct states; no fake signature status is permitted.
- Update logic is local/test-fixture first. R12 does not introduce a production update server; remote distribution infrastructure belongs to later deployment/backend work unless separately accepted by ADR.
- IPC is local by default. Network listeners are not introduced as an IPC shortcut.
- SQLite migrations are versioned, bounded, transaction-aware and rollback-tested. Failed migration never silently advances schema version.
- UI-thread affinity, cancellation and lifecycle are explicit contracts; background tasks cannot outlive the owning project/run without a governed durable job contract.
- Accessibility and localization remain mandatory quality gates, not optional framework demos.
- Exact-head acceptance remains mandatory. Missing evidence never manufactures PASS.
- ADR required if implementation would alter a frozen R1–R11 foundation rather than add an R12-scoped capability.

## R12 identity and evidence model

R12 separates durable identities instead of conflating filenames, mutable installations or display labels:

1. **DesktopTargetProfileId** — Project DNA desktop intent: platforms, framework, architecture, packaging and feature decisions.
2. **DesktopToolchainIdentity** — adapter/runtime/compiler/SDK/platform identity plus capabilities and executable digests where applicable.
3. **DesktopTemplateIdentity** — exact Kodepoia template set, schema version and digest.
4. **DesktopScaffoldDefinitionId** — canonical Project DNA + KodeProduct + template + adapter recipe identity.
5. **DesktopWorkspaceManifestId** — deterministic generated-file manifest with normalized paths, digests and lineage.
6. **DesktopFrameworkAdapterId** — typed adapter contract for WPF, WinUI, Avalonia, Qt or Tauri.
7. **MVVMContractId** — framework-neutral view-model/state/navigation/command/service contract identity.
8. **DesktopBuildDefinitionId / BuildRunId** — target/toolchain/configuration/locked dependencies/limits bound to one build result.
9. **DesktopTestDefinitionId / TestRunId** — unit/integration/UI-smoke definition and exact result identity.
10. **SQLiteSchemaId / MigrationChainId** — canonical database schema and ordered migration identity.
11. **AsyncPolicyId** — cancellation, concurrency, dispatcher/UI-thread and progress policy identity.
12. **IPCContractId** — transport, endpoint scope, message schema, authorization, size/time limits and protocol version.
13. **DesktopAccessibilityProfileId** — keyboard/focus/semantics/contrast/scaling/localization test profile.
14. **PackageDefinitionId** — packaging format, architecture, identity, files, capabilities and signing state.
15. **UpdatePolicyId / UpdateManifestId** — version/channel/compatibility/rollback policy and artifact digest identity.
16. **R12IntegratedEvidenceDigest** — semantic digest tying accepted R12 subdivision evidence, any required/triggered local evidence and prior integrated reports without circular self-attestation.

## Desktop budget model

R12 budgets extend R6 Budget and may be target/profile-specific. They include as applicable:

- generated source file count/bytes and template expansion wall time;
- restore/build/test wall time and process output limits;
- package bytes, installed bytes and update delta bytes;
- startup wall time and first-window readiness where measurable;
- steady-state and peak RAM/CPU/handle/thread counts for bounded smoke fixtures;
- UI event queue/backlog, concurrent task count and cancellation latency;
- IPC request/response bytes, queue depth, timeout and connection count;
- SQLite database bytes, transaction duration, migration wall time/steps and rollback storage;
- accessibility issue count, untranslated-string count and pseudo-localization layout failures;
- dependency count and license/BOM findings;
- installer/update rollback duration and retained backup bytes.

Budget overruns are explicit `BUDGET_EXCEEDED`, never silently demoted to PASS.

## Global prerequisites

Before R12.1 implementation begins:

- R1–R11 are COMPLETE + NORMALIZED on `main`;
- R11 canonical integrated report remains present and PASS with semantic digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`;
- the R11.14 post-merge normalization PR is merged as `6d3c7eb557d940641977d18384e4f6d2bad42f3c`;
- Python baseline remains 3.12.x unless separately changed and accepted;
- existing Project DNA already supports `desktop_app` and Windows target semantics and remains the authoritative base contract;
- existing Project Wizard and KodeProduct remain accepted and accessible;
- no mandatory cloud service/account/store credential is introduced;
- hosted CI may provision build dependencies in workflow setup, but Kodepoia runtime must not silently download/install toolchains;
- adapter acceptance distinguishes deterministic unit/fixture tests from real toolchain build/runtime evidence.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R12.1 | Desktop contracts, identities, capability model + secure toolchain boundaries | PLANNED | NONE | R11 COMPLETE + planning PR merged |
| R12.2 | Project DNA/KodeProduct desktop profiles + Project Wizard target selection | PLANNED | NONE | R12.1 + R2 |
| R12.3 | Deterministic desktop scaffold/template/workspace manifest engine | PLANNED | NONE | R12.1–R12.2 + R8 |
| R12.4 | Framework-neutral MVVM/state/navigation/command/service contracts | PLANNED | NONE | R12.1–R12.3 |
| R12.5 | WPF/.NET desktop adapter + build/test bridge | PLANNED | CONDITIONAL | R12.1–R12.4 + R6 |
| R12.6 | WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge | PLANNED | CONDITIONAL | R12.1–R12.5 |
| R12.7 | Avalonia cross-platform desktop adapter | PLANNED | CONDITIONAL | R12.1–R12.4 + R12.5 evidence patterns |
| R12.8 | Qt 6/CMake desktop adapter | PLANNED | CONDITIONAL | R12.1–R12.4 + R6/R8 |
| R12.9 | Tauri v2/Rust/WebView2 desktop adapter | PLANNED | CONDITIONAL | R12.1–R12.4 + R6/R8 |
| R12.10 | SQLite persistence, schema migrations, transactions + backup/recovery | PLANNED | NONE | R12.1–R12.4 + R1/R6 |
| R12.11 | Async/concurrency, cancellation, progress + UI-thread lifecycle safety | PLANNED | NONE | R12.4 + adapter contracts |
| R12.12 | Local IPC contracts, framing, authorization + lifecycle isolation | PLANNED | CONDITIONAL | R12.1 + R12.11 + R1/R6 |
| R12.13 | Accessibility, localization, theming, keyboard/focus + DPI/scaling QA | PLANNED | CONDITIONAL | R12.4–R12.9 + R6 |
| R12.14 | Packaging/install/update/signing-state + rollback model | PLANNED | CONDITIONAL | R12.5–R12.13 + R1/R6/R8 |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | PLANNED | NONE | R12.1–R12.14 |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | PLANNED | CONDITIONAL | R12.1–R12.15 + R6/R8/R11 evidence |

## R12.1 — Desktop contracts, identities, capability model + secure toolchain boundaries

**Manual intervention:** NONE.

Deliver:

- versioned contracts/schemas for desktop target profile, toolchain identity/capabilities, adapter identity, build/test/package status and evidence;
- finite adapter enum containing exactly the frozen R12 adapters;
- structured toolchain discovery with allowlisted executable names/roots and no process launch during pure discovery;
- fixed argv builders for capability/version/build/test operations; no shell strings;
- bounded environment override allowlist and redaction policy;
- explicit capability states including `NOT_PROBED`, `AVAILABLE`, `UNAVAILABLE`, `UNSUPPORTED`, `BLOCKED`, `FAILED`;
- project/staging/output-root validation using existing workspace boundaries;
- schemas and canonical serialization/digest rules.

Acceptance:

- traversal/symlink/executable substitution/env injection/raw argv attacks fail closed;
- capability reports cannot claim AVAILABLE without accepted evidence;
- compile + focused tests + exact-head R0/full Python/UI.

## R12.2 — Project DNA/KodeProduct desktop profiles + Project Wizard target selection

**Manual intervention:** NONE.

Deliver:

- backward-compatible Project DNA evolution for desktop framework, architecture, deployment/package intent and optional desktop capabilities;
- migration/load behavior for existing schema-v1 projects without silently rewriting intent;
- KodeProduct requirements/acceptance mapping for desktop-specific constraints;
- existing KodeStudio Project Wizard adapts when `ProjectType.DESKTOP_APP` is selected: Windows-first defaults, framework selection, architecture, persistence/IPC/package/update decisions and relevant budgets;
- game-only engine/dimension/input controls remain disabled for desktop app projects;
- deterministic serialization and UI accessibility/localization coverage.

Acceptance:

- old Project DNA round-trips without semantic drift;
- impossible platform/framework combinations fail validation;
- Wizard creates desktop DNA/Product intent without creating/building source yet;
- focused unit/UI tests + exact-head R0/full Python/UI.

## R12.3 — Deterministic desktop scaffold/template/workspace manifest engine

**Manual intervention:** NONE.

Deliver:

- Kodepoia-owned versioned template manifests and renderer;
- safe identifier/namespace/path normalization;
- deterministic file ordering/content/line endings and workspace manifest hashes;
- typed substitutions only; no executable template directives;
- collision/path-escape/reserved-name checks;
- preview/dry-run diff before durable creation;
- SafeChange/Backup/Audit integration for regeneration/update;
- R8 lineage from DNA/Product/template identity to every generated file.

Acceptance:

- same definition produces identical manifest/content digests;
- path traversal, template substitution injection and overwrite attacks fail closed;
- regeneration preserves user-owned regions/files according to explicit ownership policy;
- focused tests + exact-head gates.

## R12.4 — Framework-neutral MVVM/state/navigation/command/service contracts

**Manual intervention:** NONE.

Deliver:

- typed view/view-model binding intent independent of concrete UI framework;
- observable state, commands, validation, navigation/routes, dialogs, service lifetimes and dependency boundaries;
- deterministic generated sample application model used by all adapters;
- no framework object serialized into Project DNA/KodeProduct;
- lifecycle/disposal semantics suitable for later async/IPC/database resources.

Acceptance:

- deterministic contract serialization;
- cycle/duplicate-route/invalid-command/service-lifetime conflicts rejected;
- adapter conformance fixtures for equivalent logical app behavior;
- focused tests + exact-head gates.

## R12.5 — WPF/.NET desktop adapter + build/test bridge

**Manual intervention:** CONDITIONAL.

Trigger manual evidence only if authoritative Windows runtime behavior required by acceptance cannot be demonstrated by the accepted GitHub Windows runner/toolchain evidence. Toolchain installation itself is not an automatic Kodepoia action.

Deliver:

- WPF project/template mapping from shared desktop/MVVM contracts;
- bounded `.NET`/MSBuild discovery and capability probe;
- locked dependency/project configuration;
- deterministic build/test invocation through ProcessSandbox/KillSwitch;
- build artifact manifest and test result parsing;
- Windows-target validation without claiming non-Windows runtime support.

Acceptance:

- real Windows compile/test on an accepted stable .NET toolchain in CI or bounded local evidence;
- missing/incompatible SDK fails as UNAVAILABLE/UNSUPPORTED;
- malicious project property/argv/environment injection rejected;
- exact-head gates.

## R12.6 — WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge

**Manual intervention:** CONDITIONAL.

Trigger if hosted Windows CI cannot prove the required WinUI build/runtime/deployment semantic. Any manual step must use an exact candidate SHA and a bounded repository-owned fixture.

Deliver:

- WinUI 3 project/template mapping from shared contracts;
- Windows App SDK/template capability probe distinct from generic `dotnet` presence;
- packaged/unpackaged development intent represented structurally;
- application/package identity, manifest and deployment-mode contracts;
- build/test/runtime-smoke evidence without silently enabling Developer Mode or installing workloads;
- no certificate/private key requirement for ordinary development acceptance.

Acceptance:

- accepted Windows toolchain builds the canonical generated fixture;
- package identity/deployment metadata validate deterministically;
- unavailable template/workload never becomes PASS;
- exact-head gates.

## R12.7 — Avalonia cross-platform desktop adapter

**Manual intervention:** CONDITIONAL.

Trigger only for platform runtime claims not demonstrated by CI. A Windows acceptance certifies Windows only; Linux/macOS claims require their own evidence.

Deliver:

- Avalonia project/template mapping from common MVVM contracts;
- .NET/Avalonia capability and locked dependency identity;
- deterministic Windows/Linux/macOS target matrix metadata;
- build/test artifact parsing and platform-specific state;
- no silent mobile scope expansion despite Avalonia's broader platform support.

Acceptance:

- canonical fixture build/tests on supported CI targets selected by the subdivision;
- cross-platform evidence remains partitioned by OS/architecture;
- exact-head gates.

## R12.8 — Qt 6/CMake desktop adapter

**Manual intervention:** CONDITIONAL.

Trigger if an authoritative Qt/compiler runtime/build seam is unavailable in hosted CI and the adapter would otherwise claim it.

Deliver:

- Qt 6/CMake template mapping from desktop contracts;
- explicit Qt/CMake/compiler/kit identity and capability reporting;
- fixed CMake configure/build/test templates with no model/user raw flag injection;
- deterministic resource/project manifest generation;
- license/BOM declarations for generated dependency choices.

Acceptance:

- real supported Qt/CMake toolchain compiles/tests repository-owned fixture where availability is claimed;
- kit/compiler/path/generator substitution attacks fail closed;
- exact-head gates.

## R12.9 — Tauri v2/Rust/WebView2 desktop adapter

**Manual intervention:** CONDITIONAL.

Trigger if real Windows WebView2/Rust/C++ Build Tools semantics required for an AVAILABLE claim cannot be proven by CI.

Deliver:

- Tauri v2 workspace mapping with bounded Rust/frontend configuration;
- Rust/Cargo, C++ Build Tools and WebView2 capability identities on Windows;
- locked Cargo/frontend dependency manifests;
- explicit allowlist of Kodepoia-owned build/test/package operations;
- package-manager lifecycle scripts disabled/rejected unless a separately governed Kodepoia-owned template requires and audits one;
- MSI capability remains separate/optional.

Acceptance:

- canonical Windows fixture compile/test on accepted capability set;
- Cargo/build-script/frontend-script/path/env injection attacks fail closed;
- exact-head gates.

## R12.10 — SQLite persistence, schema migrations, transactions + backup/recovery

**Manual intervention:** NONE.

Deliver:

- versioned SQLite schema/model contracts and deterministic schema digest;
- bounded migration graph with cycle/missing-path detection;
- parameterized query/data-access intents; raw model-supplied SQL is not an execution surface;
- transactions, busy/timeout policy, foreign-key/integrity checks;
- SafeChange/Backup/Recovery/Audit integration for destructive migrations/import;
- corruption/incompatible/newer-schema states and dry-run migration report;
- framework-neutral persistence service mapping usable by adapters.

Acceptance:

- commit/rollback/crash/corrupt/tampered checksum/migration-cycle cases covered;
- failed migration restores accepted pre-state and never advances version;
- focused tests + exact-head gates.

## R12.11 — Async/concurrency, cancellation, progress + UI-thread lifecycle safety

**Manual intervention:** NONE.

Deliver:

- framework-neutral async operation descriptors and cancellation propagation;
- KillSwitch bridge for governed external build/test/package operations;
- UI dispatcher/main-thread affinity intent mapped by adapters;
- bounded worker/concurrency/queue policies and progress snapshots;
- ownership/disposal rules preventing orphan tasks after window/project/run closure;
- timeout/deadlock/starvation-safe test harnesses.

Acceptance:

- cancellation, timeout, double-completion, stale callback, close-during-task and bounded-queue cases deterministic;
- no hidden background daemon introduced;
- focused tests + exact-head gates.

## R12.12 — Local IPC contracts, framing, authorization + lifecycle isolation

**Manual intervention:** CONDITIONAL.

Trigger only when an OS-specific named-pipe/socket semantic required for an acceptance claim cannot be tested in hosted CI.

Deliver:

- versioned local IPC envelope/schema and endpoint identity;
- platform adapter for supported local transports, defaulting to local-only scope;
- framing/length limits, timeouts, cancellation, peer/session identity and authorization hooks;
- no network listener fallback;
- replay/stale-version/oversized/truncated/malformed message handling;
- lifecycle cleanup and collision-safe endpoint allocation.

Acceptance:

- malicious frames/oversize/version substitution/unauthorized peer/replay/timeout fail closed;
- process shutdown leaves no owned endpoint orphan;
- exact-head gates.

## R12.13 — Accessibility, localization, theming, keyboard/focus + DPI/scaling QA

**Manual intervention:** CONDITIONAL.

Trigger for OS/framework semantics not machine-verifiable in hosted CI, such as an interactive screen-reader/runtime-only issue discovered during acceptance.

Deliver:

- shared accessible-name/description/role/state/tab-order/focus requirements mapped to each adapter;
- keyboard-only navigation and focus restoration tests;
- localization resource generation, locale fallback and pseudo-localization;
- RTL-safe text/layout intent where supported;
- theme/high-contrast/dark-light semantics;
- Windows DPI/scaling/resizable-window layout validation profiles;
- integration with R6 accessibility/localization/VisualQA instead of duplicate governance.

Acceptance:

- canonical UI fixtures pass structural accessibility and pseudo-localization checks;
- missing accessible metadata and hard-coded translatable strings fail the configured gate;
- exact-head gates.

## R12.14 — Packaging/install/update/signing-state + rollback model

**Manual intervention:** CONDITIONAL.

Trigger if the subdivision makes a real installer/install/update/signing claim that hosted CI cannot prove. No user production certificate is required for phase acceptance; signing may remain `UNSIGNED`/`TEST_SIGNED` when explicitly declared.

Deliver:

- framework-specific package adapters with common PackageDefinition/ArtifactManifest;
- MSIX/installer/archive capability states where applicable to the selected framework;
- version/channel/compatibility update manifest and local-fixture update source;
- digest verification before install/update promotion;
- rollback/backup/recovery/audit integration;
- explicit signing identity/state without secret leakage;
- no production update server or store submission.

Acceptance:

- package contents are deterministic enough for semantic manifest verification even when upstream binaries contain nondeterministic metadata;
- tampered/wrong-version/wrong-arch/update-downgrade/signature-state substitution rejected;
- failed update returns to prior verified state;
- exact-head gates.

## R12.15 — CLI + KodeStudio Desktop workspace and governed Wizard workflow

**Manual intervention:** NONE.

Deliver:

- structured `kodepoia r12`/desktop CLI status, scaffold, validate, build, test and package intents with stable JSON/exit semantics;
- no raw command/executable/flag/script/SQL/signing-key input surface;
- KodeStudio Desktop workspace integrating Project Wizard output, target/framework capability status, build/test/package evidence and blockers;
- explicit refresh vs execute distinction: status refresh does not silently build/install/restore;
- cancellation through global KillSwitch;
- accessibility/localization and pseudo-localization for all new KodeStudio controls.

Acceptance:

- unavailable capability returns explicit non-zero/blocked state where execution is requested;
- read-only evidence cannot be edited into PASS;
- no external process on passive refresh;
- exact-head gates.

## R12.16 — Adversarial hardening + Wizard-to-Windows integrated acceptance

**Manual intervention:** CONDITIONAL.

Trigger if the final roadmap DoD requires an interactive/real Windows runtime semantic not established by the accepted hosted Windows runner. If triggered, freeze one exact candidate SHA, one bounded local collector, prerequisites, exact commands, expected output, privacy/recovery instructions and review the resulting evidence before proceeding.

Deliver:

- adversarial suite spanning Project DNA -> template -> adapter -> build/test -> SQLite/async/IPC -> package/update seams;
- attacks including path/symlink/identifier injection, environment/argv/MSBuild/CMake/Cargo/script injection, dependency/lock substitution, schema/version substitution, SQL misuse, IPC malformed/replay/oversize, cancellation races, package/update tampering and evidence substitution;
- canonical `R12_INTEGRATED_ACCEPTANCE.json` schema/model/verifier;
- anti-circular report generation following the R11 pattern: implementation head must pass gates before canonical PASS report is created;
- integrated evidence binding R12.1–R12.16 acceptances, required/triggered local evidence and prior canonical integrated reports;
- end-to-end canonical desktop fixture created from the existing Project Wizard (`ProjectType.DESKTOP_APP`, Windows target), scaffolded, compiled and tested using a modern Windows adapter;
- package artifact validation for the canonical fixture; runtime launch/install smoke is required only if the chosen accepted evidence path can safely and deterministically prove it.

Acceptance ordering:

1. freeze one immutable implementation head with report absent;
2. exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke;
3. satisfy any triggered CONDITIONAL real-runtime gate;
4. freeze implementation SHA/run IDs in R12.16 acceptance;
5. generate canonical integrated report from immutable evidence;
6. fresh exact-head R0/full Python/UI on final docs/evidence head;
7. merge implementation/evidence PR with `expected_head_sha`;
8. exactly one continuity-only R12.16 post-merge normalization + same exact-head gates + merge;
9. only then R12 is COMPLETE + NORMALIZED and R13 planning may begin.

## Manual intervention matrix

`NONE` means hosted deterministic tests/gates are sufficient for the frozen claim. `CONDITIONAL` means implementation MUST stop and request a bounded exact-head manual action only if the stated real OS/toolchain/runtime semantic is actually required and not already proven by accepted CI evidence.

| Subdivision | Frozen state | Trigger |
| --- | --- | --- |
| R12.1 | NONE | — |
| R12.2 | NONE | — |
| R12.3 | NONE | — |
| R12.4 | NONE | — |
| R12.5 | CONDITIONAL | WPF Windows build/runtime semantic unavailable in accepted CI |
| R12.6 | CONDITIONAL | WinUI/Windows App SDK build/deployment semantic unavailable in accepted CI |
| R12.7 | CONDITIONAL | claimed OS runtime not proven in CI |
| R12.8 | CONDITIONAL | claimed Qt/compiler/runtime semantic not proven in CI |
| R12.9 | CONDITIONAL | claimed Tauri/Rust/WebView2 semantic not proven in CI |
| R12.10 | NONE | — |
| R12.11 | NONE | — |
| R12.12 | CONDITIONAL | required OS-specific IPC semantic unavailable in CI |
| R12.13 | CONDITIONAL | required interactive accessibility/DPI semantic unavailable in CI |
| R12.14 | CONDITIONAL | real install/update/signing semantic unavailable in CI |
| R12.15 | NONE | — |
| R12.16 | CONDITIONAL | final Wizard-to-Windows DoD contains runtime/install semantic not proven in CI |

No manual gate may be silently converted to synthetic PASS. If a condition triggers, work stops before the next subdivision until exact-head evidence is reviewed and accepted.

## Required acceptance artifacts per subdivision

Every R12.x implementation must include:

- `docs/roadmap/R12_<n>_DESIGN.md` describing frozen scope, contracts, security boundaries and rollback;
- `docs/roadmap/R12_<n>_ACCEPTANCE.md` binding exact implementation/final-documentation SHA(s), gates and manual state;
- focused tests named for the subdivision;
- versioned schemas for newly durable R12 data;
- local acceptance JSON only when a REQUIRED/triggered CONDITIONAL real-runtime seam exists;
- no generated PASS evidence checked in before its exact source head is independently accepted.

## Exact-head gate policy

For the planning PR and every R12 subdivision/final normalization:

- R0 Repository Guard must be SUCCESS;
- full Python Core must be SUCCESS, including Ubuntu/Windows matrices and package build evidence where the workflow defines them;
- KodeStudio UI Smoke must be SUCCESS;
- all three top-level runs must refer to the same exact head SHA;
- if final acceptance/documentation changes the head after implementation gates, the resulting exact documentation head is re-gated before merge;
- merge always uses `expected_head_sha`;
- after every accepted implementation merge, exactly one continuity-only normalization is permitted before the next subdivision;
- no next subdivision starts until that normalization passes and merges.

## Planning acceptance / recovery sequence

This R12 planning cycle itself follows the same anti-drift rule:

1. branch `r12/00-phase-plan` from normalized `main` `6d3c7eb557d940641977d18384e4f6d2bad42f3c`;
2. create this `docs/roadmap/R12_PLAN.md` and synchronize `docs/continuity/KODEPOIA_CONTINUITY.md` in the same planning candidate;
3. freeze one exact planning candidate head;
4. require R0 Repository Guard + full Python Core + KodeStudio UI Smoke SUCCESS on that head;
5. record the accepted planning head/run IDs without silently changing R12 scope; if recording changes bytes, re-gate the final documentation head;
6. merge the planning PR with `expected_head_sha`;
7. create exactly one post-merge planning continuity normalization, changing only `docs/continuity/KODEPOIA_CONTINUITY.md`;
8. exact-head R0/full Python/UI on that normalization and merge with `expected_head_sha`;
9. only then mark R12 planning **ACCEPTED + NORMALIZED** and authorize R12.1.

If any planning gate fails, correct only the planning defect, create a new head and restart all three exact-head gates. R12.1 remains forbidden throughout recovery.

## Phase completion definition

R12 is COMPLETE + NORMALIZED only when:

- R12.1–R12.16 are individually accepted and normalized in order;
- the existing Project Wizard can create a desktop-app Project DNA/KodeProduct definition and deterministically scaffold a modern Windows project;
- at least one modern Windows adapter has authoritative exact-head evidence that the generated canonical fixture compiles and its tests pass;
- framework adapters expose truthful capability states and do not manufacture cross-platform availability;
- MVVM, SQLite, async/cancellation, IPC, accessibility/localization and package/update contracts are integrated and regression-tested;
- any triggered real-runtime/manual evidence is reviewed and PASS;
- `R12_INTEGRATED_ACCEPTANCE.json` verifies `status=pass`, `blockers=[]` with anti-circular evidence binding;
- final R0/full Python/KodeStudio UI gates pass on the exact evidence head;
- implementation/evidence merge is followed by exactly one accepted continuity-only normalization;
- no architecture-v1.0 boundary has changed without accepted ADR.

Only then may R13 planning begin.
