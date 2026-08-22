# R6.9 — KodeAppSecurity baseline — Design

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `616899291fc3b4dc40695415a5008d6fdd599230`  
**Manual intervention:** NONE

## Objective

R6.9 establishes a structured, platform-aware application-security baseline for Kodepoia and later generated products without claiming that a desktop local-first IDE is automatically compliant with a Web-application standard.

OWASP ASVS 5.0.0 is the stable external catalogue used only where a requirement maps to a real Kodepoia surface. Requirement references are version-qualified (`v5.0.0-x.y.z`) so later ASVS releases cannot silently change their meaning.

Representative mappings used by this foundation:

- `v5.0.0-1.2.5`: OS-command injection / command construction — relevant to governed process execution;
- `v5.0.0-5.3.2`: generated or validated file paths — relevant to `WorkspaceBoundary` and path traversal;
- `v5.0.0-13.3.1`: secrets-management solution and exclusion of secrets from source/build artifacts — relevant to `KodeSecrets` and persisted quality evidence.

Authentication/session requirements are not declared PASS merely because Kodepoia currently lacks a browser-authentication surface. Such controls are explicitly `not_applicable` with rationale when absent.

## Design principles

1. **Applicability is evidence, not success.** `not_applicable` is a distinct state and cannot block or count as PASS.
2. **Measured security results require provenance.** PASS/WARN/FAIL requirements require an `evidence_source`; UNKNOWN may remain unmeasured.
3. **Threat residual risk defaults to UNKNOWN.** Existing architectural mitigations are recorded, but their presence is not automatically converted into a LOW residual-risk assertion.
4. **Failures fail closed.** Failed applicable requirements, affected dependencies, or blocking high/critical threats make the aggregate security report FAIL.
5. **Dependency observations are time/provenance bound.** A dependency result requires component, version, timezone-aware `checked_at`, source, and advisory IDs when affected.
6. **Secrets stay out of evidence.** Structured details pass through the existing recursive R6.8 `redact_sensitive()` contract before persistence.
7. **No second execution/scanner path.** R6.9 does not add arbitrary SAST, package-manager, network, shell, executable, cwd, or scanner arguments. Later collectors may feed structured observations through existing governed executors.
8. **Project confinement remains mandatory.** Persistent reports live under `.kodepoia/diagnostics/security/` through `WorkspaceBoundary`.
9. **Stable regression hooks.** Requirements, dependency observations, and threats map to stable R6.3 test IDs.
10. **No certification claim.** R6.9 is a baseline/evidence layer, not a penetration test, ASVS certification, or guarantee that an artifact is secure.

## Threat-model contract

`ThreatModel` contains four typed collections with cross-reference validation:

- assets;
- trust boundaries;
- entry points;
- threats.

Every threat must reference at least one asset, at least one entry point or trust boundary, and at least one mitigation. Duplicate IDs or broken references are invalid evidence.

The initial Kodepoia model covers:

### Assets

- project workspace;
- delegated OS-backed secrets;
- audit-chain evidence;
- model context that must exclude raw secrets;
- source-SHA-bound build artifacts/evidence.

### Trust boundaries

- user-controlled project → Kodepoia process;
- Kodepoia process → governed child process;
- Kodepoia process → loopback development service;
- Kodepoia process → external network service.

### Entry points

- project files;
- structured tool requests;
- allowlisted process execution;
- loopback Godot development sockets;
- permission-scoped external network activity.

### Initial threats

- workspace path traversal;
- arbitrary command/process execution;
- raw secret disclosure;
- unintended loopback-service exposure;
- downloaded code bypassing Guardian/Sandbox governance.

Mitigations cite existing architecture (`WorkspaceBoundary`, Guardian, `PermissionSet`, `ProcessSandbox`, KillSwitch, `KodeSecrets`, redaction), but residual risk remains UNKNOWN until concrete evidence measures it.

## Requirement model

Each `SecurityRequirement` records:

- stable ID;
- category;
- title;
- applicability;
- status;
- severity;
- optional versioned ASVS reference;
- applicability rationale;
- evidence source;
- blocking flag;
- recursively redacted structured details.

Rules:

- N/A requires rationale and status `not_applicable`;
- applicable controls cannot use `not_applicable`;
- PASS/WARN/FAIL require a provenance source;
- only FAIL may be blocking;
- ASVS references, when present, must use the exact `v5.0.0-x.y.z` syntax.

## Dependency-vulnerability evidence

`DependencyVulnerabilityEvidence` records a point-in-time observation rather than pretending dependency status is timeless.

Required fields:

- component + exact observed version;
- CLEAR / AFFECTED / UNKNOWN;
- timezone-aware check time;
- provenance source;
- advisory IDs for AFFECTED observations;
- severity;
- blocking state only for AFFECTED evidence;
- redacted details.

R6.9 deliberately does not run an unrestricted network scanner. A future governed collector can supply these observations, but missing/currently-unqueried data remains UNKNOWN rather than fabricated CLEAR.

## Aggregate report semantics

`SecurityReportStatus`:

- `FAIL`: failed applicable requirement, affected dependency, or blocking threat;
- `WARN`: warning/unknown applicable requirements, unknown dependencies, or unresolved medium/high/critical/unknown threat residual risk when some measurable evidence exists;
- `UNKNOWN`: no applicable requirement/dependency measurement and all threat residual risk remains unknown;
- `PASS`: all applicable measured requirements pass, all dependency evidence is clear, and all measured threat residual risks are low.

A canonical SHA-256 covers the complete derived evidence payload. Serialized counts, blockers, aggregate status, threat references, and evidence digest are all recomputed/validated on load.

## Health / Regression integration

`KodeAppSecurity.to_health_metric()` maps the aggregate report to the pre-existing `HealthDimension.SECURITY`.

- UNKNOWN remains Health UNKNOWN with no score;
- FAIL with blockers remains a blocking Health FAIL;
- measured reports receive a deterministic score based on applicable controls, dependency evidence, and measured residual risk;
- N/A controls are excluded from the score.

`KodeAppSecurity.to_test_cases()` emits stable IDs:

- `security:<requirement-id>`;
- `security:dependency:<component>:<version>`;
- `security:threat:<threat-id>`.

N/A, WARN and UNKNOWN become SKIP rather than PASS. AFFECTED/failed/blocking evidence becomes FAIL. This preserves the R6.3 rule that a new failure cannot be hidden by skipping it.

## Persistence

`SecurityStore` writes only:

- `.kodepoia/diagnostics/security/<project>-latest.json`;
- `.kodepoia/diagnostics/security/security-<project>-<timestamp>.json`.

The initialized `.kodepoia` root is required. Paths are resolved through `WorkspaceBoundary`; writes use temporary-file + replace semantics.

## Explicitly out of scope

- third-party penetration testing;
- exploit development;
- store certification;
- cloud/backend implementation;
- automatically claiming ASVS compliance;
- mandatory remote security SaaS;
- arbitrary model-selected SAST/scanner executables or shell commands;
- copying private credentials into a report to prove they exist.

## Rollback / anti-regression

A rollback of R6.9 removes only the new security evidence module/schema/tests/docs/exports. It must not weaken Guardian, `PermissionSet`, `WorkspaceBoundary`, `ProcessSandbox`, KillSwitch, SafeChange, AuditLog, `KodeSecrets`, R6.8 redaction, existing CI/build gates, or earlier R6 evidence.

Do not:

- reinterpret N/A as PASS;
- mark a dependency CLEAR without timestamped provenance;
- mark unknown residual risk LOW merely because a mitigation exists;
- weaken a failing/blocking observation to keep Health green;
- persist raw secrets;
- add a direct model-to-shell/scanner path.
