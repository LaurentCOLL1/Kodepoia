# R6.8 — KodeCI + KodeBuild foundation — Design

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `fc7bd4d5803c451b4d343d08bcc212868ad24412`  
**Branch:** `feature/r6-8-ci-build`  
**Manual intervention:** CONDITIONAL

## Objective

Convert CI and Python package builds into structured, source-SHA-bound evidence while preserving every existing R0/Python/UI gate and avoiding any unrestricted build/process API.

## KodeCI contract

`src/kodepoia/quality/ci.py` defines stable check IDs and explicit states:

- `queued`;
- `in_progress`;
- `pass`;
- `fail`;
- `cancelled`;
- `skipped`;
- `unknown`.

A required `fail`, `cancelled` or `skipped` check makes the report FAIL. A required queued/in-progress/unknown check keeps the report UNKNOWN. Optional non-PASS evidence produces WARN rather than manufacturing PASS. R6.3 adapters preserve these distinctions.

CI evidence is bound to a 40-character source Git SHA, hash-protected, validates derived counts/blockers and persists only under `.kodepoia/workflows/` through `WorkspaceBoundary`.

## KodeBuild contract

`src/kodepoia/quality/build.py` records:

- exact source SHA;
- platform;
- Python version;
- build backend;
- deterministic source-input SHA-256;
- dependency-input SHA-256 (`pyproject.toml` in this foundation);
- artifact file name, kind, byte size and SHA-256;
- structural validation result;
- recursively redacted metadata;
- derived PASS/FAIL/UNKNOWN state and blockers;
- canonical evidence SHA-256.

Python acceptance requires both a wheel and source distribution. Wheel validation checks for the `kodepoia/` package and `.dist-info/METADATA`; sdist validation checks for `pyproject.toml` and `src/kodepoia/__init__.py`. Missing or structurally invalid required artifacts are blocking failures.

The source-input digest covers `pyproject.toml`, `README.md` and the complete `src/` tree in stable relative-path order. It is not described as the Git commit object hash; it is a deterministic digest of build-relevant source inputs.

## Secret handling

Persisted build metadata recursively redacts fields whose names identify passwords, tokens, authorization/API/access/private keys and redacts common inline secret/Bearer patterns. R6.8 must never copy raw CI secrets into `.kodepoia/` evidence.

## Workflow integration

The existing `Python Core` workflow retains its test and Windows UI jobs unchanged in purpose. R6.8 adds a separate `package-build` matrix for `ubuntu-latest` and `windows-latest`:

1. checkout;
2. Python 3.12;
3. fixed installation of declared development/build dependencies;
4. fixed `python -m build --wheel --sdist --outdir dist`;
5. fixed `scripts/r6_8_collect_build.py` evidence collection/validation;
6. `actions/upload-artifact@v4` upload of packages and latest manifests.

The collector exposes no model-supplied executable, command, argv, cwd, host or output path. Source SHA/platform arrive through fixed CI environment variables and are validated by the structured models.

## Reproducibility semantics

R6.8 records exact per-platform artifact digests. It does **not** require the Windows and Ubuntu archives to be byte-identical and does not call differing archive hashes a regression by themselves. Archive timestamps/toolchain/platform details can legitimately make byte identity differ; the required invariant is traceable source/dependency inputs plus validated per-artifact hashes.

## Provenance reference context

SLSA provenance concepts are informative context only. Kodepoia does not claim a SLSA level in R6.8. GitHub artifact attestations are also not made a mandatory PR/test-build gate: GitHub documentation describes them as provenance links, not a guarantee that an artifact is secure, and advises against signing frequent builds used only for automated testing. A later release phase may add attestations if it has a real downloadable release surface.

## Persistence

- CI: `.kodepoia/workflows/<workflow-id>/latest.json` plus timestamped snapshots.
- Build: `.kodepoia/releases/<platform>/latest.json` plus timestamped snapshots.

Both roots are resolved through `WorkspaceBoundary`; symlink escapes remain rejected.

## Health and R6.3 integration

A validated wheel+sdist pair maps to Health `build` PASS/100. Missing/invalid required artifacts map to blocking FAIL/0. No artifact evidence maps to UNKNOWN.

Stable R6.3 build cases are `build:<platform>:wheel` and `build:<platform>:sdist`. CI cases are `ci:<workflow-id>:<check-id>`.

## Conditional manual gate

The manual gate is **not automatically triggered**. Hosted Windows is sufficient if the final R6.8 head successfully builds, validates, hashes and uploads the required Windows package/evidence artifacts. A local Windows gate may be requested only after a concrete hosted-CI limitation is demonstrated and documented on the frozen final head.

## Rollback

Rollback removes the additive CI/build modules, schemas, tests, collector and package-build job, and removes the `build` development dependency. Existing R0/Python/UI jobs and all R6.1–R6.7 evidence remain untouched. Project-local historical evidence is not silently deleted.
