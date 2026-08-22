# R7.11 — Adversarial hardening + R7 integrated acceptance — Design

**Status:** IMPLEMENTATION IN PROGRESS  
**Manual gate:** CONDITIONAL  
**Foundation change:** NONE

## Purpose

Close R7 without widening its authority surface. R7.11 adds cross-source adversarial regressions and a machine-readable phase acceptance record. It does not add a new research provider, browser, command runner, secret API or trust engine.

## Security references and architectural interpretation

The final hardening follows the already frozen architecture:

- external content is data and continues through the single accepted `ResearchGuard` boundary;
- tool/network/process authorization remains deterministic outside model text;
- providers remain least-privilege/read-only where accepted;
- Web target safety is enforced before transport and on every redirect;
- repository evidence is content-addressed and independently recalculated.

R7.11 therefore tests the existing boundaries end-to-end rather than adding a second filtering or authorization subsystem.

## Adversarial matrix

### Cross-source indirect prompt injection

Use hostile visible text representing local/official docs, Web, GitHub, Community and YouTube evidence. Every artifact must remain `guarded`, preserve suspicious indicators/provenance and gain no tool/permission authority. Context/UX serialization must retain the untrusted classification.

### SSRF and redirect/DNS target safety

Regression cases include:

- loopback/private/link-local literal targets;
- credential-bearing URLs;
- DNS answers containing any non-public address;
- redirect attempts to unsafe targets;
- resolution/rebinding paths already protected by R7.3's validate-every-hop and pinned-IP transport model.

No live network is needed; resolver/transport fixtures are deterministic.

### Workspace/path isolation

Exercise traversal/absolute/outside-workspace paths and, where supported by the host, symlink escapes for local research and Research UX exports. The result must fail closed through `WorkspaceBoundary`.

### Process/tool surface

R7.11 does not create a process API. Tests assert that Research UX fetch requests expose typed research selectors only and cannot provide arbitrary executable/argv/cwd/env. Existing R7.7 external helpers remain fixed-template `ProcessSandbox` operations governed by Guardian/KillSwitch.

### Secret non-disclosure

Representative delegated-auth/token-shaped values must be absent from view/export/context-style result serialization after redaction. No raw secret-read API is introduced.

### Cancellation

Cancellation is tested before dispatch and immediately before persistence/result promotion. A cancelled operation cannot create a new artifact represented as READY.

### Version/conflict semantics

Contradictory claims remain visible as conflict even when explicit supersession evidence exists. Ranking is presentation only; source count/popularity never becomes authority.

### Unknown/blocked/unavailable semantics

Missing providers/evidence retain explicit UNKNOWN/BLOCKED/UNAVAILABLE/N/A/STALE semantics; no missing measurement becomes PASS/CURRENT.

## Integrated acceptance model

Create a versioned `R7IntegrationReport` contract with exactly 11 subdivision records. Each record contains:

- subdivision ID;
- PASS/FAIL/UNKNOWN status;
- canonical acceptance-document repository path;
- SHA-256 of canonical repository bytes;
- canonical byte length;
- accepted implementation head;
- explicit manual state;
- derived `manual_satisfied` boolean.

The phase report contains candidate/final R7.11 `source_sha`, status, blockers and a canonical self-evidence digest computed without trusting the stored digest field.

### Manual states

Version 1 supports:

- `none`;
- `required_satisfied`;
- `conditional_not_triggered`;
- `conditional_satisfied`;
- `required_unsatisfied`;
- `conditional_triggered_unsatisfied`.

Only the first four satisfy phase completion.

## Repository validator

The domain validator accepts a `read_bytes(repository_path)` callback. It never shells out itself. It:

1. requires exactly R7.1–R7.11 once each;
2. requires the canonical `docs/roadmap/R7_N_ACCEPTANCE.md` path for each subdivision;
3. reloads canonical bytes through the caller;
4. recalculates byte length and SHA-256;
5. requires PASS + non-empty 40-hex accepted head + satisfied manual state;
6. verifies each acceptance document contains its declared accepted head;
7. requires R7.11 accepted head to equal report `source_sha`;
8. recalculates the report evidence digest and rejects tampering.

The repository-integration test may use the same fixed `git show HEAD:<repository_path>` blob loader already accepted by R6, avoiding CRLF working-tree differences on Windows.

## Final report timing

`docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json` is intentionally **not** created on the R7.11 implementation branch. The exact R7.11 accepted head cannot be embedded in its own acceptance document before that head exists. As in R6, the final report is created during post-merge normalization after hosted exact-head acceptance establishes the implementation SHA. The normalization gates then validate the real checked-in report against canonical Git blobs. R7 remains IN PROGRESS until that normalization merges.

## Quality / security / BOM review

R7.11 adds no runtime or development dependency and does not modify `pyproject.toml`. The full Python suite continues to execute R6 Health/Regression/TechnicalDebt/AppSecurity/Privacy/License/BOM and R6.12 repository-integration gates. A focused R7.11 review document records provider/helper boundaries and any dependency delta; any non-empty new dependency/helper delta would require explicit review rather than silent PASS.

## Manual decision

The R7.11 manual gate is CONDITIONAL. Deterministic hosted fixtures cover every frozen behavior, so the expected decision is `CONDITIONAL NOT TRIGGERED`. A live external-provider probe is required only if a frozen acceptance requirement cannot be established by deterministic evidence. Silence cannot satisfy a triggered gate.

## Rollback

R7.11 only adds tests, schemas, evidence contracts and documentation. Rollback removes these derived acceptance artifacts. No user research source data or remote provider state is mutated.
