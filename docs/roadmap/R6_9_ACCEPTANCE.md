# R6.9 — KodeAppSecurity baseline — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `616899291fc3b4dc40695415a5008d6fdd599230`  
**Manual intervention:** NONE

## Accepted implementation identity

- starting normalized main: `616899291fc3b4dc40695415a5008d6fdd599230`;
- implementation branch: `feature/r6-9-appsecurity`;
- accepted implementation head: `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`;
- implementation PR: #50;
- implementation merge: `f5c135edf0be464a02b4b46d67c14e665f236009`.

## Acceptance matrix

| Gate | Required | Result |
| --- | --- | --- |
| Structured threat assets/boundaries/entry points/threats | yes | PASS |
| Duplicate/broken threat references rejected | yes | PASS |
| Residual risk defaults UNKNOWN rather than inferred LOW | yes | PASS |
| Stable security requirement IDs | yes | PASS |
| explicit applicable / not_applicable semantics | yes | PASS |
| not_applicable never PASS | yes | PASS |
| N/A rationale required | yes | PASS |
| measured PASS/WARN/FAIL requires evidence source | yes | PASS |
| version-qualified ASVS references | yes | PASS |
| path/input/network/auth/session categories remain applicability-aware | yes | PASS |
| secure-storage evidence helper | yes | PASS |
| dependency timestamp/provenance evidence | yes | PASS |
| affected dependency requires advisory IDs | yes | PASS |
| recursive security-evidence secret redaction | yes | PASS |
| aggregate UNKNOWN/PASS/WARN/FAIL semantics | yes | PASS |
| blockers derived from evidence | yes | PASS |
| canonical SHA-256 evidence | yes | PASS |
| derived counts/blockers/hash tamper rejection | yes | PASS |
| `security-report-v1` JSON Schema | yes | PASS |
| `.kodepoia/diagnostics/security/` confinement | yes | PASS |
| Health `security` adapter | yes | PASS |
| stable R6.3 security cases | yes | PASS |
| N/A/UNKNOWN/WARN adapters never manufacture PASS | yes | PASS |
| no unrestricted security scanner/process/network path | yes | PASS |
| R0 exact final head Windows+Ubuntu | yes | PASS |
| Python Core exact final head, all jobs | yes | PASS |
| KodeStudio UI Smoke exact final head | yes | PASS |
| implementation PR merge | yes | PASS |
| post-merge normalization | yes | IN THIS NORMALIZATION PR |

## Accepted behavioral scope

The accepted implementation demonstrates:

1. a typed Kodepoia threat model containing assets, trust boundaries, entry points and threats with validated cross-references;
2. duplicate/broken references fail closed;
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

## Final hosted CI evidence — exact implementation head

Accepted head: `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`.

- R0 Repository Guard #812 `32573265598` — SUCCESS Windows + Ubuntu;
- Python Core #786 `32573265793` — SUCCESS for all five jobs:
  - `python-core-ubuntu-latest`;
  - `python-core-windows-latest` including PowerShell acceptance-runner syntax;
  - integrated `kodestudio-ui-windows`;
  - `package-build-ubuntu-latest`;
  - `package-build-windows-latest`;
- KodeStudio UI Smoke #753 `32573265579` — SUCCESS Windows.

The final exact implementation head therefore preserved R0, full Python Core, integrated UI, separate UI smoke, and both R6.8 package-build gates.

## Development diagnostic finding

Initial draft head `85742e808dfb68dbe6e1f5f64c2b4fee5d63b0f3` compiled and built packages successfully, but Python Core Ubuntu found exactly one R6.9 test failure: the test expected a blocking Health SECURITY metric score of `0.0`, while the implemented deterministic aggregate score was `75.0` because one failing requirement scored 0 and five measured LOW residual-risk threats scored 90 each. The metric was already `FAIL` and `blocking=true`; the blocker independently forces failure regardless of the aggregate numeric score.

Only the incorrect test expectation was corrected. No security status, blocker, scoring formula, applicability rule, provenance requirement, redaction rule, threat risk or `WorkspaceBoundary` behavior changed.

Diagnostic head `0251a62c92230a486abfdd8b151e59a1adb98bb3` then passed R0 #810 `32573142662`, Python Core #784 `32573142620` for all five jobs, and UI Smoke #751 `32573142653` before the final acceptance record produced the exact accepted head above.

## External-reference interpretation

OWASP ASVS 5.0.0 is used as a reference catalogue only where Kodepoia has an applicable surface. This phase does not claim ASVS certification or full Web-application applicability.

Representative accepted mappings include:

- `v5.0.0-1.2.5`: command-injection prevention for process-execution surfaces;
- `v5.0.0-5.3.2`: trusted/generated or strictly validated file paths for path-traversal relevant surfaces;
- `v5.0.0-13.3.1`: secrets-management solution and exclusion of secrets from source/build artifacts.

Absent browser authentication/session features are explicitly N/A rather than silently PASS. Existing architecture mitigations do not automatically make threat residual risk LOW; the baseline factory intentionally starts residual risk at UNKNOWN until concrete evidence measures it.

## Manual intervention

**NONE.**

R6.9 required no local GPU/Godot/hardware evidence. Hosted Windows + Ubuntu CI were authoritative for this foundation, so no user-side manual step was requested or needed.

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

R6.9 implementation is accepted on head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351` and merged by PR #50 as `f5c135edf0be464a02b4b46d67c14e665f236009`. This post-merge normalization records R6.9 COMPLETE and promotes R6.10 to NEXT / NOT STARTED after this normalization PR is CI-green and merged.
