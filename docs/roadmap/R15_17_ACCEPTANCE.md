# R15.17 — Integrated acceptance record

## Status

`COMPLETE`

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

### `214f2f2b80c5ee21fb792af05a9a64805cc2ce71`

Rejected and non-authoritative. Dedicated run `33353591840` passed compilation and Ruff, then reached the executable R15.9 training contract and correctly rejected the invented fixture authorization token. The scenario now reuses the exact repository-owned R15.9 fixture authorization `repository-owned-r15.9-fixture`.

### focused preflight after the R15.9 correction

Temporary helper run `33353846658` captured the next failure rather than hiding it. All seven focused tests reached the same root cause: the scenario had executed all fourteen checks but compared dictionary insertion order with the canonical check order. The guard was corrected to validate exact set/cardinality and then normalize the evidence dictionary explicitly according to `CHECK_NAMES` before semantic hashing.

Temporary helper run `33353909274` then passed Ruff and all seven focused R15.17 tests before creating functional commit `f6001d70635da4d7f1510c0ed022122c0f741b43`. This remained preflight evidence only.

### `fe11086214a6f0aef73004d91efd63701a53040c`

Rejected and non-authoritative. Dedicated run `33353973888` proved that exact checkout, compilation, Ruff, all seven focused anti-circular tests and the exact-head integrated scenario itself passed on Ubuntu. The subsequent JSON revalidation correctly exposed a serialization-boundary defect: canonical JSON uses sorted object keys, while the semantic validator incorrectly required the in-memory insertion order of the `checks` object to equal `CHECK_NAMES`.

JSON object property order is not part of the evidence semantics. The validator and workflow assertions were therefore corrected to require the exact fourteen-key set and exact cardinality, without relying on property order. A dedicated canonical JSON round-trip test was added.

Temporary round-trip helper run `33354039370` passed Ruff, all eight focused tests, scenario generation, JSON reload, Draft 2020-12 schema validation and semantic validation. Its final push was rejected only because the workflow `GITHUB_TOKEN` is not authorized to modify another workflow file; no functional acceptance step failed.

Temporary helper run `33406621527` repeated the same functional validation successfully and then committed only the non-workflow Python/test changes as `b174c52eb701a81fc7b44e8d02cb7c4a2cc451eb`. The workflow assertion change was applied separately through the authorized GitHub connector in `02c794bd71470ebd1777f88eebaf9f571a7b5f50`. All temporary helpers were then removed, leaving only the seven intended R15.17 files in the net phase diff.

## Accepted exact-source authority

- immutable technical source: `125d40a23a0c6b40e449340e593dc0bcb342c421`;
- R15 Integrated Acceptance #21 / `33411377302`: SUCCESS Ubuntu + Windows;
- R0 Repository Guard #2231 / `33411377234`: SUCCESS Ubuntu + Windows;
- Python Core #2206 / `33411377186`: SUCCESS;
- KodeStudio UI Smoke #2171 / `33411377227`: SUCCESS;
- scenario artifact `9765260200`, archive SHA-256 `16fe30ed8a654dd2df7275dad9f37b0fdee6597e6a7d1252dd2edf2399cb1772`, semantic digest `58c93eec3a1a0e4d8cceab8f9ad23106c40648661fd64c30ca04aa8b75bd871c`;
- exact fourteen-check inventory recomputed PASS with no blockers, no secret exposure, eight bound identities and truthful optional capability state `unavailable`;
- CI authority digest `6b2d683434940eb3094051581ae03613a7db1b26d61747027a0c11798de7bd61`;
- canonical R15 integrated digest `82eb91b671c8551168c95042f5f959a9fd29d807dbcde2f58265f8f9b3d03dad`;
- manual state `CONDITIONAL / NOT TRIGGERED`; no real target-workstation training/conversion/promotion evidence is required for core closure;
- this synchronization creates the final documentary/evidence candidate; its resulting exact END-head must pass fresh R15 Integrated + R0 + Python Core + KodeStudio UI Smoke before protected merge.

## Closure boundary

R16 remains forbidden until R15.17 is merged through the protected process and the single post-merge R15 phase normalization has completed with fresh gates.
