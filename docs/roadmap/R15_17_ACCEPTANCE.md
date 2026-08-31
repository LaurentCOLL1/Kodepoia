# R15.17 — Integrated acceptance record

## Status

`IN_PROGRESS`

This file records the R15.17 acceptance protocol and observed candidate results. It is not itself a PASS artifact and must never be used as a substitute for re-executing the exact-source gates.

## Scope

R15.17 closes R15 only after the adversarial Experience → governance → dedup/holdout → dataset → KodeBench → decision → training → evaluation → export → GGUF/Ollama → model registry chain has been re-executed on an exact immutable source SHA.

The executable inventory is the fourteen invariants defined in `R15_PLAN.md` and implemented by `src/kodepoia/tuning/integrated_acceptance.py`. The dedicated workflow is `.github/workflows/r15-integrated-acceptance.yml`.

## Acceptance requirements

A technical candidate is acceptable only if all of the following are true on that exact candidate SHA:

- `R15 Integrated Acceptance / integrated-ubuntu` passes after compiling and linting the R15.17 surfaces, executing the focused anti-circular tests, running the exact-head scenario, and validating both the Draft 2020-12 schema and the semantic evidence validator;
- `R15 Integrated Acceptance / verifier-windows` independently executes the focused tests and exact-head scenario on Windows and validates the same claims;
- all fourteen adversarial checks are recomputed and true;
- the generated evidence binds the exact source SHA and eight SHA-256 identities for dataset, protected benchmark suite/protection, base model, training plan, adapter, evaluation binding and quantization policy;
- synthetic secret material is absent from emitted evidence;
- optional missing local capabilities remain truthful `unavailable`/conditional evidence rather than a fabricated PASS;
- `blockers` is empty and the semantic digest matches a fresh canonical recomputation;
- the required R0 Repository Guard, Python Core and KodeStudio UI Smoke gates also pass on the exact technical source before END synchronization.

After the technical source is immutable and green, canonical scenario/CI/integrated evidence may be synchronized to the repository while explicitly binding that technical source. The END head then requires fresh exact-END R0, Python Core, KodeStudio UI Smoke and R15 Integrated gates before protected merge.

## Diagnostic candidates

### `d7c86857d34f253c065cef394c4e92839ac80545`

Rejected and non-authoritative. Dedicated run `33353360083` proved exact checkout and compilation but exposed two implementation defects:

- Ubuntu Ruff rejected import organization / modern typing style in the new integrated module;
- Windows reached the executable DatasetBuilder and rejected the synthetic curated records because their governance transformation ID did not match the real R15.3 lineage contract (`r15.3-sanitize-v1`).

Both defects were corrected on the branch. No PASS claim is derived from this rejected candidate.

## Current candidate policy

The next connector-authored commit after removal of all temporary patch helpers is the next candidate to evaluate. Its status remains `IN_PROGRESS` until GitHub Actions demonstrates the required exact-source gates. Any subsequent code or evidence change creates a new candidate SHA and invalidates earlier candidate success for closure purposes.

## Closure boundary

R16 remains forbidden until R15.17 is merged through the protected process and the single post-merge R15 phase normalization has completed with fresh gates.
