# R6.11 — KodeLicense + KodeBOM foundation — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `36524978a963d8c759d36902bc1ab00989da0549`  
**Manual intervention:** CONDITIONAL — NOT TRIGGERED

R6.11 is COMPLETE only after its exact final implementation head passes required hosted gates, the implementation PR merges, and post-merge plan/status/continuity normalization is CI-green and merged.

## Acceptance matrix

| Gate | Required | Current |
| --- | --- | --- |
| stable component IDs | yes | IMPLEMENTED |
| project/package/asset component kinds | yes | IMPLEMENTED |
| resolved/unresolved/N/A version state | yes | IMPLEMENTED |
| exact version only for resolved components | yes | IMPLEMENTED |
| strict N/A component/integrity coupling | yes | IMPLEMENTED |
| all-N/A BOM remains UNKNOWN | yes | IMPLEMENTED |
| N/A excluded from scoring/license decisions/SPDX packages | yes | IMPLEMENTED |
| N/A R6.3 BOM case remains SKIP | yes | IMPLEMENTED |
| manifest/source provenance retained | yes | IMPLEMENTED |
| SHA-256 integrity evidence retained | yes | IMPLEMENTED |
| recorded hash distinct from verified claim | yes | IMPLEMENTED |
| integrity mismatch blocks BOM | yes | IMPLEMENTED |
| optional declared + mandatory concluded license assertion | yes | IMPLEMENTED |
| SPDX expression / NOASSERTION / NONE distinct | yes | IMPLEMENTED |
| NOASSERTION/NONE require provenance+rationale | yes | IMPLEMENTED |
| LicenseRef custom-text hash supported | yes | IMPLEMENTED |
| custom text hash requires standalone LicenseRef | yes | IMPLEMENTED |
| no free-text→SPDX inference | yes | IMPLEMENTED |
| no unresolved range→exact license inference | yes | IMPLEMENTED |
| exact-expression allow/warn/deny/unknown policy | yes | IMPLEMENTED |
| unmatched license cannot silently ALLOW | yes | IMPLEMENTED |
| only DENY blocks | yes | IMPLEMENTED |
| policy fingerprint tamper binding | yes | IMPLEMENTED |
| explicit BOM inventory completeness provenance | yes | IMPLEMENTED |
| deterministic BOM counts/blockers/status/hash | yes | IMPLEMENTED |
| deterministic license counts/blockers/status/score/hash | yes | IMPLEMENTED |
| BOM bound to SPDX 3.0 baseline + 3.0.1 serialization reference | yes | IMPLEMENTED |
| SPDX compatibility view explicitly not conformance claim | yes | IMPLEMENTED |
| current Kodepoia pyproject BOM coverage | yes | IMPLEMENTED |
| build/runtime/optional/dev requirements retained | yes | IMPLEMENTED |
| duplicate package across groups merged deterministically | yes | IMPLEMENTED |
| package URL retained when available | yes | IMPLEMENTED |
| BOM JSON Schema | yes | IMPLEMENTED |
| license JSON Schema | yes | IMPLEMENTED |
| `.kodepoia/bom/` confinement | yes | IMPLEMENTED |
| `.kodepoia/licenses/` confinement | yes | IMPLEMENTED |
| Health `dependencies` adapter | yes | IMPLEMENTED |
| Health `licenses` adapter | yes | IMPLEMENTED |
| stable R6.3 BOM/license cases | yes | IMPLEMENTED |
| secret redaction in component details | yes | IMPLEMENTED |
| no shell/installer/scanner/arbitrary remote fetch path | yes | IMPLEMENTED |
| R0 exact final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| Python Core exact final head, all jobs | yes | PENDING FINAL HEAD |
| KodeStudio UI Smoke exact final head | yes | PENDING FINAL HEAD |
| implementation PR merge | yes | PENDING |
| post-merge normalization | yes | PENDING |

## Required behavioral acceptance

The final suite must demonstrate at minimum:

1. SPDX expression normalization accepts ordinary expressions and `LicenseRef-*` while rejecting malformed characters/parentheses;
2. `NOASSERTION` and `NONE` remain distinct explicit known-unknown/none states and require provenance+rationale;
3. custom-license text hashes require one standalone unambiguous `LicenseRef-*`, never a composite expression;
4. recorded, unknown, mismatched and N/A integrity states remain distinct;
5. a N/A component requires N/A integrity, while applicable components reject N/A integrity;
6. empty/all-N/A BOM is UNKNOWN, incomplete/unresolved BOM is WARN, fully resolved fixture can PASS, mismatch FAILs and blocks;
7. N/A components are counted separately but excluded from dependency Health scoring, license decisions and SPDX package entries;
8. N/A BOM cases remain R6.3 SKIP and all-N/A license evidence yields no decisions/UNKNOWN;
9. complete inventory requires review provenance;
10. pyproject ranges remain unresolved rather than being treated as installed exact versions;
11. unresolved pyproject dependencies remain NOASSERTION rather than inheriting current web metadata;
12. duplicate normalized package names across dependency groups merge while preserving requirements/groups;
13. current Kodepoia pyproject inventory includes build/runtime/optional/dev dependencies and preserves one source-manifest SHA-256;
14. proprietary Kodepoia license can be represented as a source-hash-backed `LicenseRef-Kodepoia-Proprietary` without claiming an SPDX-listed license;
15. SPDX compatibility view records 3.0 baseline, 3.0.1 serialization/context, excluded N/A IDs and `conformance_claim=false`;
16. license policy forbids default ALLOW, uses exact expressions and leaves unmatched/NOASSERTION UNKNOWN;
17. license report can distinguish UNKNOWN/PASS/WARN/FAIL and DENY creates blocker;
18. incomplete license inventory cannot PASS;
19. BOM/license JSON round-trip preserves canonical evidence;
20. counts/blockers/hash/blocking-field tampering is rejected;
21. duplicate components and duplicate requirement evidence fail closed;
22. Health dependencies/licenses preserve UNKNOWN/WARN/PASS/FAIL semantics;
23. R6.3 adapters map unresolved/unknown/N/A to SKIP and mismatch/DENY to FAIL;
24. stores require initialized `.kodepoia`, persist inside project boundary and round-trip;
25. JSON Schemas accept canonical PASS and all-N/A reports;
26. component detail secrets are redacted.

## Current-project acceptance interpretation

The current Kodepoia `pyproject.toml` declares version ranges, not a lock/resolved artifact inventory. Therefore the truthful current-project BOM is expected to be WARN for dependency resolution/integrity, not PASS. This is accepted behavior for the foundation because R6.11 must not manufacture exact versions, hashes or license conclusions.

The repository's own `LICENSE` is proprietary/all-rights-reserved text. R6.11 may represent it with a project-local `LicenseRef-Kodepoia-Proprietary` bound to the `LICENSE` SHA-256; it must not map that text to an SPDX-listed open-source identifier.

## Development diagnostic / hardening

Initial diagnostic head `5d76ba98f0fc715f2e672fc27cc1b99fc015bc8e` passed R0 #863, Python Core #837 with all five jobs and UI Smoke #804. Independent review nevertheless found a false-green path: N/A components could contribute to BOM PASS and an R6.3 BOM PASS case.

The contract was hardened before final acceptance:

- strict component-resolution/integrity N/A coupling;
- N/A counts in canonical report/schema;
- all-N/A BOM becomes UNKNOWN;
- N/A excluded from dependency Health score, license decisions and SPDX package view;
- N/A R6.3 BOM case becomes SKIP;
- custom license-text hash requires one standalone `LicenseRef-*`;
- schemas and tests enforce the same rules.

Hardened diagnostic head `ad19f69d1d706db657be809698395a2340ec779c` passed R0 #869, Python Core #843 with all five jobs and UI Smoke #810. No blocker, provenance, unknown-state or architecture boundary was weakened.

## Standards interpretation

- Frozen R6 BOM baseline: SPDX 3.0 family.
- Current patch-level specification/serialization rechecked 2026-08-22: SPDX 3.0.1.
- Current SPDX JSON-LD context: `https://spdx.org/rdf/3.0.1/spdx-context.jsonld`.
- SPDX declared/concluded licensing and explicit NoAssertion semantics are reference context for the evidence model.
- Current CycloneDX stable interoperability context: 1.7; not a replacement for the frozen SPDX baseline.

The compact `spdx_compatibility_view()` is normalization/interoperability evidence only. It is not claimed as an official conformant SPDX JSON-LD document. The lexical expression normalizer is also not a replacement for the official SPDX license-list/parser/ontology.

## Manual intervention

**CONDITIONAL — NOT TRIGGERED.**

No user action is currently required. Foundation acceptance intentionally includes unresolved `NOASSERTION` and neutral N/A evidence. Manual resolution is required only if an acceptance-critical real component must receive a specific license conclusion and trusted repository/package/authoritative-source evidence remains ambiguous. Never invent an SPDX ID to satisfy the gate.

## Failure recovery / anti-regression

- Never infer a dependency's exact version from a range.
- Never copy a current package-page license onto an unresolved allowed version range.
- Never convert free-text license metadata into an SPDX identifier without explicit evidence.
- Never treat missing license evidence or N/A as ALLOW/PASS.
- Never let NOASSERTION/NONE become PASS through scoring.
- Never call a recorded digest independently verified without verification evidence.
- Never suppress integrity mismatch or DENY blockers.
- Never loosen component/provenance duplicate checks or evidence hash validation.
- Never loosen N/A component/integrity coupling or let N/A enter applicable scoring.
- Never loosen `WorkspaceBoundary` confinement.
- Never add model-controlled installer, scanner, shell command, arbitrary package URL fetch, license-page instruction execution or publisher.
- Never claim official SPDX conformance from the compact compatibility view.

## Completion record

PENDING exact-final-head CI, implementation merge and post-merge normalization.
