# R6.9 — KodeAppSecurity baseline — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `616899291fc3b4dc40695415a5008d6fdd599230`  
**Manual intervention:** NONE

R6.9 is COMPLETE only after the exact final implementation head passes all required hosted gates, the implementation PR merges, and post-merge plan/status/continuity normalization is CI-green and merged.

## Acceptance matrix

| Gate | Required | Current |
| --- | --- | --- |
| Structured threat assets/boundaries/entry points/threats | yes | IMPLEMENTED |
| Duplicate/broken threat references rejected | yes | IMPLEMENTED |
| Residual risk defaults UNKNOWN rather than inferred LOW | yes | IMPLEMENTED |
| Stable security requirement IDs | yes | IMPLEMENTED |
| explicit applicable / not_applicable semantics | yes | IMPLEMENTED |
| not_applicable never PASS | yes | IMPLEMENTED |
| N/A rationale required | yes | IMPLEMENTED |
| measured PASS/WARN/FAIL requires evidence source | yes | IMPLEMENTED |
| version-qualified ASVS references | yes | IMPLEMENTED |
| path/input/network/auth/session categories remain applicability-aware | yes | IMPLEMENTED |
| secure-storage evidence helper | yes | IMPLEMENTED |
| dependency timestamp/provenance evidence | yes | IMPLEMENTED |
| affected dependency requires advisory IDs | yes | IMPLEMENTED |
| recursive security-evidence secret redaction | yes | IMPLEMENTED |
| aggregate UNKNOWN/PASS/WARN/FAIL semantics | yes | IMPLEMENTED |
| blockers derived from evidence | yes | IMPLEMENTED |
| canonical SHA-256 evidence | yes | IMPLEMENTED |
| derived counts/blockers/hash tamper rejection | yes | IMPLEMENTED |
| `security-report-v1` JSON Schema | yes | IMPLEMENTED |
| `.kodepoia/diagnostics/security/` confinement | yes | IMPLEMENTED |
| Health `security` adapter | yes | IMPLEMENTED |
| stable R6.3 security cases | yes | IMPLEMENTED |
| N/A/UNKNOWN/WARN adapters never manufacture PASS | yes | IMPLEMENTED |
| no unrestricted security scanner/process/network path | yes | IMPLEMENTED |
| R0 exact final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| Python Core exact final head, all jobs | yes | PENDING FINAL HEAD |
| KodeStudio UI Smoke exact final head | yes | PENDING FINAL HEAD |
| implementation PR merge | yes | PENDING |
| post-merge normalization | yes | PENDING |

## Required behavioral acceptance

The final test suite must demonstrate at minimum:

1. the Kodepoia threat model is complete enough to contain assets, trust boundaries, entry points and threats with valid cross-references;
2. malformed/duplicate cross-references fail closed;
3. `not_applicable` is structurally distinct from PASS and requires rationale;
4. an applicable control cannot hide behind N/A;
5. measured PASS/WARN/FAIL controls require evidence provenance;
6. ASVS references are pinned to the accepted `v5.0.0-x.y.z` form;
7. OS-backed/no-plaintext secret evidence can pass while plaintext/non-OS evidence fails and blocks;
8. dependency observations require timezone-aware provenance and affected results require advisory IDs;
9. affected dependencies fail the aggregate report;
10. UNKNOWN, WARN, PASS and FAIL aggregate states are distinguishable;
11. counts, blockers and canonical evidence hash reject tampering;
12. secret-shaped nested fields/tokens are redacted;
13. Health SECURITY preserves UNKNOWN and blocking FAIL semantics;
14. R6.3 IDs are stable and N/A/UNKNOWN are SKIP rather than PASS;
15. security report persistence requires initialized `.kodepoia` and remains project-confined;
16. the JSON Schema accepts the canonical report;
17. deterministic malformed payload variants fail closed.

## External-reference interpretation

OWASP ASVS 5.0.0 is used as a reference catalogue only where Kodepoia has an applicable surface. This phase does not claim ASVS certification or full Web-application applicability.

Representative accepted mappings include:

- `v5.0.0-1.2.5`: command-injection prevention for process-execution surfaces;
- `v5.0.0-5.3.2`: trusted/generated or strictly validated file paths for path-traversal relevant surfaces;
- `v5.0.0-13.3.1`: secrets-management solution and exclusion of secrets from source/build artifacts.

Absent browser authentication/session features are explicitly N/A rather than silently PASS.

## Manual intervention

**NONE.**

R6.9 does not require local GPU/Godot/hardware evidence. Hosted Windows + Ubuntu Python/CI are authoritative for this foundation. Do not request a local user run unless a later demonstrated regression changes the accepted phase contract through a governed decision.

## Failure recovery / anti-regression

- Do not weaken N/A semantics to fix a failing test.
- Do not remove provenance requirements from measured checks/dependencies.
- Do not convert an affected dependency into UNKNOWN/CLEAR without evidence.
- Do not lower threat residual risk merely to obtain PASS.
- Do not disable recursive secret redaction.
- Do not loosen `WorkspaceBoundary` confinement.
- Do not add arbitrary scanner commands, executables, cwd, URLs or model-provided process arguments.
- Do not remove/narrow R0, Python Core, UI Smoke or R6.8 package-build gates.

## Completion record

PENDING exact-final-head CI, implementation merge and post-merge normalization.
