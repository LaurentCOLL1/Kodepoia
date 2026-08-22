# R6.11 — KodeLicense + KodeBOM foundation — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `36524978a963d8c759d36902bc1ab00989da0549`  
**Accepted implementation head:** `d0590ed3eda663ad713fc36d962c8dac1df109eb`  
**Implementation PR:** #54  
**Implementation merge:** `248b1331fe2b26229b932c36aefb83c70065c52a`  
**Manual intervention:** CONDITIONAL — NOT TRIGGERED

R6.11 is accepted as a local-first License/BOM foundation. Completion here means the implementation contract and its hosted evidence are accepted; it does **not** claim legal compatibility, SPDX conformance, or resolution of every real dependency license.

## Accepted contract

- stable component IDs and project/package/asset kinds;
- explicit `resolved`, `unresolved`, `not_applicable` component states;
- exact version only for resolved components;
- strict N/A component/integrity coupling;
- all-N/A BOM remains `UNKNOWN`, never PASS;
- N/A excluded from dependency scoring, license decisions and SPDX package entries and remains R6.3 SKIP;
- structured provenance, source locator, purl, manifest/source SHA-256 and requirement-group evidence;
- integrity `recorded`, `mismatch`, `unknown`, `not_applicable`, with recorded digest distinct from independently verified evidence;
- integrity mismatch is blocking;
- declared-license assertion optional and concluded-license assertion mandatory;
- `SPDX_EXPRESSION`, `NOASSERTION`, `NONE` remain distinct;
- NOASSERTION/NONE require rationale and provenance;
- custom-license text SHA-256 requires one standalone `LicenseRef-*`;
- no free-text→SPDX inference and no unresolved range→current-web-license inference;
- deterministic `pyproject.toml` collector covering build/runtime/all optional groups;
- normalized duplicate Python package names are merged while preserving every requirement/group;
- exact-expression `ALLOW/WARN/DENY/UNKNOWN` policy, default ALLOW forbidden, only DENY blocking;
- canonical BOM/license reports, policy fingerprint and SHA-256 anti-tamper checks;
- SPDX 3.0 family baseline with 3.0.1 serialization/context interoperability metadata and explicit `conformance_claim=false`;
- `.kodepoia/bom/` and `.kodepoia/licenses/` stores through `WorkspaceBoundary`;
- Health `dependencies` and `licenses` adapters;
- stable R6.3 `bom:<id>` / `license:<id>` cases;
- JSON Schemas and focused tests including the real Kodepoia `pyproject.toml`;
- no shell, installer, scanner, arbitrary remote fetch, license-page instruction execution or publishing path.

## Design hardening evidence

Initial diagnostic head `5d76ba98f0fc715f2e672fc27cc1b99fc015bc8e` passed R0 #863, Python Core #837 and UI Smoke #804. Independent review nevertheless found a potential false-green path in N/A handling. The implementation was hardened so N/A is neutral/UNKNOWN/SKIP, excluded from applicable scoring/decisions/SPDX packages, and coupled strictly to N/A integrity. A custom text hash was also restricted to one standalone `LicenseRef-*`.

Hardened diagnostic head `ad19f69d1d706db657be809698395a2340ec779c` passed R0 #869, Python Core #843 with all five jobs and UI Smoke #810.

Two branch-only tool mistakes occurred during final evidence handling: a temporary README overwrite and a temporary `NONEXISTENT` file. Both were fully reverted before acceptance. The final PR diff contained only the nine intended R6.11 files; `README.md` was restored to the exact main blob and the temporary file was absent.

## Final exact-head hosted evidence

Final net-clean accepted head: `d0590ed3eda663ad713fc36d962c8dac1df109eb`.

- R0 Repository Guard #885 / `32578903951` — SUCCESS Windows + Ubuntu;
- Python Core #859 / `32578903981` — SUCCESS all five jobs: core Ubuntu, core Windows including PowerShell syntax validation, integrated Windows UI, package-build Ubuntu, package-build Windows;
- KodeStudio UI Smoke #826 / `32578903942` — SUCCESS Windows;
- PR #54 was made ready and merged using `expected_head_sha=d0590ed3eda663ad713fc36d962c8dac1df109eb`;
- implementation merge: `248b1331fe2b26229b932c36aefb83c70065c52a`.

## Current-project interpretation

Kodepoia's current `pyproject.toml` declares dependency ranges rather than an exact resolved artifact inventory. The truthful current-project dependency BOM therefore remains WARN for resolution/integrity until exact versions/artifacts/hashes are supplied. This is accepted foundation behavior; no exact version or license is manufactured.

Kodepoia's own proprietary/all-rights-reserved `LICENSE` may be represented as `LicenseRef-Kodepoia-Proprietary` bound to that file's SHA-256. This does not convert it into an SPDX-listed open-source license.

## Standards interpretation

- frozen R6 BOM baseline: SPDX 3.0 family;
- current patch-level interoperability reference checked 2026-08-22: SPDX 3.0.1;
- current JSON-LD context used by the compact view: `https://spdx.org/rdf/3.0.1/spdx-context.jsonld`;
- CycloneDX 1.7 remains optional interoperability context, not a replacement baseline;
- compact SPDX view and lexical expression normalization are not official SPDX conformance or legal analysis.

## Manual intervention

**CONDITIONAL — NOT TRIGGERED.** No user action was required for R6.11 acceptance. A future manual resolution is required only if an acceptance-critical real component must receive a specific license conclusion and trusted authoritative evidence remains genuinely ambiguous.

## Anti-regression

Never infer exact versions from ranges, copy current package-page licenses onto unresolved ranges, treat NOASSERTION/NONE/N/A as ALLOW/PASS, call recorded hashes independently verified, suppress integrity/DENY blockers, weaken N/A coupling/provenance/hash validation/WorkspaceBoundary, add model-controlled execution or arbitrary network fetches, or claim legal/SPDX conformance from the compact compatibility view.

## Completion record

**R6.11 implementation COMPLETE.** Post-merge normalization is performed by `feature/r6-11-post-merge-normalization`; R6.12 may start only after that normalization PR is CI-green and merged.
