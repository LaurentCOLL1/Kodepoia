# R15.13 — Ollama import / Modelfile packaging acceptance

**Status:** COMPLETE — technical source accepted; exact-END re-gates pending
**Normalized base:** `ca625d51808de6c1f9c950faecc2aa785e7a757d`
**Immutable technical source:** `f0dfcd1ed3e9d2382ad44efdcd2ec05dbac1b7ac`
**Implementation PR:** #322 (non-draft successor; draft PR #321 was closed unmerged because the connected ready-for-review mutation was incompatible with GitHub current GraphQL schema)
**Manual state:** `CONDITIONAL / NOT TRIGGERED`

## Accepted scope

R15.13 implements deterministic, governed local Ollama packaging over the already accepted R15.10–R15.12 lineage. It validates exact base/artifact identity before creation, generates a bounded Modelfile from structured repository-owned configuration, creates only namespaced candidate tags, captures model digest/details, probes runtime/structured-output/tool capabilities, compares packaging behavior through KodeBench evidence, and defines governed candidate removal/rollback.

The accepted core path never performs `ollama push`, never treats a remote Ollama endpoint as authoritative, never silently replaces an active role/production tag, and never accepts model-generated text as a shell command.

## Technical-source evidence

- R15.13 Ollama Packaging Acceptance #3 / `33327931401`: SUCCESS on Ubuntu and Windows; 19 focused/dependency tests per OS; Ruff, compileall and Draft 2020-12 package-schema validation PASS.
- R0 Repository Guard #2182 / `33327931448`: SUCCESS on Ubuntu and Windows.
- Python Core #2157 / `33327931386`: SUCCESS for Ubuntu/Windows core, package builds and UI-in-core.
- KodeStudio UI Smoke #2122 / `33327931328`: SUCCESS.

These runs qualify only immutable technical source `f0dfcd1ed3e9d2382ad44efdcd2ec05dbac1b7ac`. They MUST NOT be reused as final merge evidence after this END-sync changes documentation bytes.

## Frozen acceptance invariants

1. A wrong or unproven adapter/base binding is rejected before model creation.
2. Authoritative runtime endpoints are credential-free explicit-port loopback only.
3. Candidate tags are deterministic/namespaced and cannot collide with declared active/production tags.
4. Modelfile text is deterministic and derived only from validated structured fields.
5. Created model digest/details must be captured and bound to package evidence.
6. Create/show/tags/run lifecycle failures are terminal non-success.
7. Structured-output and tool-call capabilities are claimed only when corresponding probes pass.
8. KodeBench critical regressions veto acceptance regardless of aggregate improvement.
9. Failed/rejected candidate creation is rolled back through governed candidate removal without mutating immutable source artifacts.
10. Public registry upload and remote authoritative Ollama remain out of scope.

## External compatibility evidence

Ollama's current Modelfile reference describes a Modelfile as the blueprint used to create customized models, requires `FROM`, supports `ADAPTER`, `PARAMETER`, `TEMPLATE`, `SYSTEM` and `LICENSE`, and documents `ollama create` followed by `ollama run`. The same reference warns that an adapter should use the same base model it was tuned from because mismatched bases can behave erratically. This documentation is dated interoperability evidence only; Kodepoia's frozen R15 architecture and repository tests remain the acceptance authority.

Official references:

- https://docs.ollama.com/modelfile
- https://docs.ollama.com/import

## Manual / real-runtime posture

The conditional manual gate is **not triggered** for core R15.13. Hosted/core acceptance intentionally uses deterministic fakes/fixtures and does not claim that a real large model was created on the target workstation. No Ollama registry account, token, credential or public upload is required.

If a future claim explicitly requires authoritative real-model packaging, it must use the bounded loopback-only procedure on the exact accepted source required by that later gate and preserve the same base/digest/KodeBench invariants.

## END-sync and merge rule

This file, `R15_PLAN.md` and continuity are the only documentary END-sync additions/updates. The exact final END-head produced after temporary helper cleanup must receive fresh:

- R15.13 Ollama Packaging Acceptance;
- R0 Repository Guard;
- full Python Core;
- KodeStudio UI Smoke.

PR #322 may merge only with `expected_head_sha` equal to that freshly accepted END-head. After merge, exactly one continuity-only R15.13 normalization with fresh R0 + Python Core + UI Smoke is mandatory. R15.14 remains unauthorized until the normalized `main` from that PR exists.
