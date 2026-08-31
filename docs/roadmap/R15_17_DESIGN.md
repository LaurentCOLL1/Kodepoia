# R15.17 — Adversarial integrated Experience/Bench/Fine-tuning acceptance

## Status

`IN_PROGRESS` — this document defines the executable R15.17 acceptance architecture. It is not, by itself, evidence that R15.17 passed.

## Objective

Close R15 with a non-circular, exact-source, end-to-end acceptance proving that the Experience → governance → dedup/holdout → dataset → KodeBench → gap decision → training → evaluation → export → GGUF/Ollama → registry/rollback chain composes safely.

The integrated scenario uses only synthetic or repository-owned fixtures. Optional hardware/tool capabilities are allowed to be unavailable, but unavailability must remain explicit and must never be converted into a synthetic PASS.

## Exact adversarial inventory

The scenario must execute all fourteen invariants defined by `R15_PLAN.md`:

1. unvalidated/unopted experience is blocked before training eligibility;
2. synthetic secret/private material is redacted or quarantined and is absent from emitted evidence;
3. unknown/disallowed license blocks training inclusion;
4. source revocation invalidates dependent dataset/candidate lineage;
5. exact/near duplicate groups remain split-atomic;
6. protected benchmark holdout and near-duplicate contamination cannot enter training;
7. mixed dataset/benchmark/model identity evidence is rejected;
8. a system defect can produce `FIX_SYSTEM_FIRST` rather than automatic training;
9. training/resume is bound to the exact base/tokenizer/dataset/config lineage;
10. any critical-domain regression vetoes promotion even when aggregate score improves;
11. wrong-base adapter export/Ollama binding is rejected;
12. excessive or critical quantization quality loss is rejected;
13. rejected candidates cannot be promoted and rollback restores the exact prior role mapping;
14. missing optional GPU/llama.cpp/Ollama capability remains truthful `UNAVAILABLE`/conditional evidence.

## Implementation surfaces

- `src/kodepoia/tuning/integrated_acceptance.py` owns the executable scenario, exact check inventory, canonical JSON hashing, identity bindings and semantic evidence validation.
- `scripts/r15_17_integrated_acceptance.py` executes the scenario against an explicit 40-character source SHA and emits canonical JSON.
- `schemas/r15/r15-integrated-evidence.schema.json` rejects incomplete, relabelled or structurally forged PASS evidence.
- `tests/test_r15_17_integrated_acceptance.py` executes the scenario, validates the schema, checks deterministic/path-independent evidence and deliberately falsifies checks, identities and optional-capability state.
- `.github/workflows/r15-integrated-acceptance.yml` checks out the exact evidence SHA and re-executes the focused acceptance on Ubuntu and Windows.

## Non-circular acceptance rules

R15.17 never accepts a checked-in `PASS` field as proof. The scenario recomputes outcomes through the R15.1–R15.14 public contracts, derives identity digests from the current execution and recomputes `semantic_digest` from the evidence payload.

A valid report requires, simultaneously:

- the exact ordered fourteen-check inventory;
- every check equal to `true`;
- exactly eight SHA-256 identity bindings for dataset, benchmark suite/protection, base model, training plan, adapter, evaluation binding and quantization policy;
- `manual_state = conditional_not_triggered`;
- `optional_capability_state = unavailable` for the repository-owned missing-capability fixture;
- `secrets_exposed = false`;
- `status = pass` and `blockers = []`;
- a semantic digest that matches a fresh canonical recomputation.

Changing a check or identity while retaining `status=pass` is therefore insufficient and is explicitly tested as invalid.

## Capability boundary

The core integrated scenario does not claim a live GPU, llama.cpp installation, Ollama daemon, public model push, remote provider, secret-bearing integration or production deployment. The repository fixture deliberately supplies a missing conversion toolchain and verifies that R15.12 reports the capability boundary as unavailable/fail-closed. Hardware-local evidence remains governed by R15.16 and is not fabricated by R15.17 CI.

## Exact-source CI

The dedicated workflow derives `EVIDENCE_SOURCE_SHA` from the pull-request head SHA or push SHA, checks out that exact commit, asserts the 40-character SHA, runs focused tests, executes the scenario, validates the Draft 2020-12 schema and the in-code semantic validator, and repeats the executable scenario on Windows.

The Ubuntu job uploads the generated scenario evidence as an Actions artifact. Checked-in canonical evidence and the R15 END synchronization are produced only after an immutable technical candidate has passed the required gates; they must bind that exact technical source rather than a later mutable branch name.

## Closure boundary

R15.17 is not complete until the immutable technical source has passed the dedicated integrated workflow together with the required R0 Repository Guard, Python Core and KodeStudio UI Smoke gates, followed by END synchronization, fresh exact-END re-gates, protected merge and one post-merge R15 phase normalization. R16 remains forbidden before that sequence completes.
