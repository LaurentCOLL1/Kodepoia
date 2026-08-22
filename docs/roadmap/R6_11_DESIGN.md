# R6.11 — KodeLicense + KodeBOM foundation — Design

**Status:** IN PROGRESS  
**Starting normalized main:** `36524978a963d8c759d36902bc1ab00989da0549`  
**Manual intervention:** CONDITIONAL — NOT TRIGGERED

## Objective

Create a local-first, auditable dependency/asset BOM and license-evidence layer that preserves exact provenance, unresolved versions, unknown licenses, N/A scope and policy uncertainty instead of manufacturing release/legal conclusions.

## Standards baseline

R6 remains frozen on the **SPDX 3.0 family** as its BOM baseline. On 2026-08-22 the current SPDX specification/serialization is 3.0.1, including JSON-LD context `https://spdx.org/rdf/3.0.1/spdx-context.jsonld`. R6.11 records:

- `SPDX_BASELINE = 3.0` to preserve the frozen roadmap decision;
- `SPDX_SERIALIZATION_VERSION = 3.0.1` as the current compatible patch-level reference;
- current JSON-LD context as interoperability metadata.

SPDX distinguishes declared license information from concluded license information and distinguishes an explicit `NoAssertionLicense` known-unknown from a missing relationship. R6.11 mirrors those semantics with optional `declared_license` and required `concluded_license` evidence. The compact R6.11 compatibility view is not a conformance claim.

CycloneDX 1.7 is current stable interoperability context. It supports component hashes, licensing, package URLs and inventory metadata. R6.11 does not silently replace SPDX with CycloneDX and does not make CycloneDX generation a completion requirement.

## BOM model

### `BomComponent`

Each component records:

- stable component ID;
- name and kind (`project`, `package`, `asset`);
- resolution state (`resolved`, `unresolved`, `not_applicable`);
- exact version only when resolved;
- Package URL when available;
- source locator and provenance source;
- optional source SHA-256;
- structured integrity evidence;
- optional declared license and mandatory concluded-license assertion;
- all manifest requirements/groups that caused the component to be included;
- redacted structured details.

Duplicate component IDs and duplicate requirement evidence fail closed.

### N/A coupling

`NOT_APPLICABLE` is a scope state, never an implicit PASS:

- N/A component must have `IntegrityStatus.NOT_APPLICABLE`;
- applicable components may not use N/A integrity;
- N/A components cannot claim an exact version;
- N/A is counted separately in BOM evidence;
- an all-N/A BOM is `UNKNOWN`, not PASS;
- N/A components are excluded from dependency Health scoring, license-policy decisions and SPDX compatibility packages;
- N/A BOM cases remain R6.3 `SKIP`;
- the compatibility view records excluded N/A component IDs separately.

This mirrors the R6.9/R6.10 anti-false-green rule that out-of-scope evidence is neutral rather than successful.

### Pyproject collector

`KodeBOM.from_pyproject()` uses stdlib `tomllib` and `WorkspaceBoundary`. It inventories:

- the Kodepoia project;
- `[build-system].requires`;
- `[project].dependencies`;
- every `[project.optional-dependencies]` group, including dev/code/ui groups.

The parser merges the same normalized Python package across groups while preserving each requirement string and group.

A version range such as `Pillow>=12.3,<12.4` is **not** an exact resolved version. Such a dependency remains `UNRESOLVED`, its artifact integrity remains `UNKNOWN`, and its concluded license remains explicit `NOASSERTION`. Current PyPI metadata is not copied onto unresolved ranges because it may describe a different exact release.

The manifest SHA-256 is retained as provenance for every component discovered from that manifest.

## Integrity semantics

`IntegrityEvidence` supports:

- `RECORDED`: a SHA-256 digest is recorded; this does not claim independent verification;
- `MISMATCH`: observed and expected SHA-256 differ; this blocks the BOM;
- `UNKNOWN`: no exact artifact/hash evidence exists;
- `NOT_APPLICABLE`: only valid for an N/A component.

R6.11 does not rename recorded hashes as verified evidence.

## License assertion semantics

`LicenseAssertion` supports:

- `SPDX_EXPRESSION`: an evidence-backed SPDX-style expression or `LicenseRef-*`;
- `NOASSERTION`: explicit known-unknown, always with rationale and provenance;
- `NONE`: explicit inspected-no-license-information state, always with rationale and provenance.

No free-text license field is automatically converted into an SPDX identifier.

Kodepoia's current proprietary repository license may be represented as `LicenseRef-Kodepoia-Proprietary` when its `LICENSE` file SHA-256 is supplied as custom-license evidence. A custom text hash is accepted only for one unambiguous standalone `LicenseRef-*`, never for a composite expression. This does not pretend the proprietary terms are an SPDX-listed license.

Expression handling is deliberately limited to lexical normalization/guarding needed by R6.11. It rejects unsafe/malformed syntax but does **not** replace the official SPDX License List, full expression parser, ontology or legal interpretation. A caller must still provide evidence-backed identifiers.

## License policy

`LicensePolicy` evaluates exact normalized concluded-license expressions only. Rules produce:

- `ALLOW`;
- `WARN`;
- `DENY`;
- unmatched / NOASSERTION / NONE → `UNKNOWN` unless a non-ALLOW policy default explicitly says otherwise.

An `ALLOW` default is forbidden so that unmatched evidence cannot silently become permitted. Only `DENY` blocks. The policy fingerprint is SHA-256-bound into the license report.

This is a configurable engineering/release policy, **not** a legal compatibility engine. R6.11 does not infer whether GPL/LGPL/MIT/proprietary combinations are legally compatible.

## Reports

### `BomReport`

Canonical report contains project/scope, explicit inventory completeness and review provenance, SPDX baseline/serialization version, deterministic counts/blockers/status, sorted components and canonical SHA-256 evidence binding.

Status:

- UNKNOWN: no applicable component evidence (empty or all-N/A);
- FAIL: applicable integrity mismatch;
- WARN: incomplete inventory, unresolved applicable component or unknown applicable integrity;
- PASS: complete inventory and every applicable included component resolved with recorded integrity.

### `LicenseReport`

Derived from a validated BOM + license policy and bound to the BOM evidence SHA-256. N/A components do not create license decisions.

Status:

- UNKNOWN: no applicable decisions;
- FAIL: any DENY;
- WARN: incomplete inventory or any WARN/UNKNOWN;
- PASS: complete inventory and all applicable decisions ALLOW.

Counts, blockers, score and policy fingerprint are derived/tamper checked.

## SPDX compatibility view

`KodeBOM.spdx_compatibility_view()` exposes versioned package/license/integrity normalization using the current SPDX 3.0.1 context, excludes N/A components from package entries, records excluded N/A IDs separately and includes `conformance_claim: false`.

R6.11 does **not** claim that this compact view is a fully conformant SPDX JSON-LD document. Official SPDX conformance also requires the official structural and semantic validation layers; that is outside the minimum R6.11 foundation unless added later through a governed validator.

## R6 integrations

- Health `dependencies` from applicable BOM resolution/integrity evidence;
- Health `licenses` from applicable license-policy evidence;
- stable R6.3 test IDs `bom:<component-id>` and `license:<component-id>`;
- unresolved/unknown/N/A/warn evidence never becomes fake PASS;
- integrity mismatch / DENY maps to FAIL;
- no applicable evidence maps to UNKNOWN or SKIP as appropriate.

## Persistence

- BOM: `.kodepoia/bom/`;
- licenses: `.kodepoia/licenses/`;
- latest + timestamped snapshots;
- initialized `.kodepoia` required;
- all paths through `WorkspaceBoundary`;
- atomic temporary-file replacement.

## Architecture boundaries

R6.11 adds no shell execution, package installer, remote scanner, arbitrary URL fetcher, license-page instruction executor or store publisher. External metadata review is done outside the runtime contract and does not create a new model-to-network or model-to-process path.

## Development hardening record

Initial diagnostic head `5d76ba98f0fc715f2e672fc27cc1b99fc015bc8e` passed R0 #863, Python Core #837 (all five jobs) and UI Smoke #804. Independent review nevertheless found a false-green possibility: N/A components could still contribute to BOM PASS and a BOM R6.3 PASS case.

The implementation was hardened before acceptance:

- strict N/A component/integrity coupling;
- N/A counts added to the canonical report/schema;
- all-N/A BOM becomes UNKNOWN;
- N/A excluded from dependency Health scoring, license decisions and SPDX package view;
- N/A BOM test case becomes SKIP;
- custom text hash requires one standalone `LicenseRef-*` rather than a composite expression;
- schemas and tests enforce these semantics.

Hardened diagnostic head `ad19f69d1d706db657be809698395a2340ec779c` passed R0 #869, Python Core #843 (all five jobs) and UI Smoke #810. No architecture boundary, provenance rule, blocker or unknown-state rule was weakened.

## Manual intervention

**CONDITIONAL — NOT TRIGGERED.**

Foundation acceptance can prove known licenses, unresolved `NOASSERTION` behavior and N/A neutrality with fixtures and the real Kodepoia manifest. User intervention is required only if an acceptance-critical real component must receive a specific license conclusion and trusted authoritative evidence remains genuinely ambiguous. In that case, ambiguity remains UNKNOWN/blocking until governed resolution or removal; no SPDX ID is invented.
