# R13.1 — Acceptance

## Scope

Accept the framework-neutral mobile contracts and secure toolchain boundary only. No Android/iOS build, device access, signing or store operation is claimed by this subdivision.

## Manual intervention

**NONE.** All frozen R13.1 claims are deterministic Python/schema/path-boundary behavior and can be authoritatively tested in hosted CI.

## Candidate acceptance gates

On one exact implementation head:

1. R0 Repository Guard — SUCCESS.
2. Full Python Core — SUCCESS, including Ubuntu and Windows tests and package builds.
3. KodeStudio UI Smoke — SUCCESS.
4. `tests/test_r13_1_mobile_contracts.py` passes as part of Python Core.
5. R13.1 JSON schemas validate under Draft 2020-12 and accept canonical model payloads.
6. Negative tests prove rejection of traversal/symlink escape, executable substitution, non-allowlisted environment variables/path escape, raw Gradle-task injection, invalid cross-platform package/API combinations and config-only manufactured `AVAILABLE`.
7. No checked-in PASS evidence is created before these gates succeed.

## Required evidence

Record the immutable implementation source SHA and exact GitHub Actions run IDs/conclusions for R0, Python Core and KodeStudio UI. If the accepted candidate is followed by documentation/status-byte changes, run fresh exact-head gates on the resulting final head before merge.

## Completion sequence

After candidate acceptance, update `R13_PLAN.md` and continuity in the same work cycle so R13.1 is `COMPLETE` and R13.2 remains `PLANNED`. Re-gate the resulting final head, merge with `expected_head_sha`, create exactly one post-merge continuity-only normalization, gate that exact normalization head and merge it. Only then is R13.2 authorized.

## Failure policy

Any failed candidate is rejected. Fix only the defect on the same R13.1 branch, freeze a new SHA, and rerun all required exact-head gates. Never reuse successful jobs from a rejected SHA.
