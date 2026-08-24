# R11.11 — Acceptance

Status: **IMPLEMENTED — FINAL DOCUMENTATION HEAD GATES PENDING**  
Manual intervention: **NONE**

## Base and scope

- Base normalized `main`: `5020bf6e46c7078b045bea77437e9b063169a9e5`.
- Branch: `r11/11-franchise-dna-canon`.
- Frozen scope: Franchise DNA, immutable/versioned Canon records/snapshots, authority tiers, validity, supersedes/deprecates relations, deterministic conflict/query policy, proposed/reviewed/canonical/deprecated workflow, and governed durable promotion.

## Acceptance criteria

- Franchise DNA identity is deterministic and remains separate from R2 Project DNA identities.
- Canon record/snapshot canonical JSON and SHA-256 identities are deterministic and order-independent where order is semantically irrelevant.
- Missing/self/circular supersession/deprecation relations fail closed.
- Equal-highest-authority conflicting canonical facts remain `CONFLICTED`; query refuses an ambiguous winner.
- Higher-authority selection is deterministic while conflict/shadow evidence remains explicit.
- R7/external research authority cannot become `CANONICAL` through the R11.11 transition API.
- Historical record/snapshot values are immutable; transitions return new records.
- Durable persistence is Guardian-authorized, SafeChange-snapshotted and Audit-recorded.
- Canon/Franchise schemas validate canonical examples without network resolution.

## Accepted implementation head

Exact candidate: `38dc7dce1bf288b61eabfa3b174add11ade4ae49`.

- R0 Repository Guard #1437 / `32760860029`: **SUCCESS**.
- Python Core #1411 / `32760860051`: **SUCCESS**.
- KodeStudio UI Smoke #1378 / `32760859982`: **SUCCESS**.
- Ubuntu and Windows Python Core: **SUCCESS**.
- Ubuntu and Windows package builds: **SUCCESS**.
- Internal KodeStudio UI job: **SUCCESS**.
- Prior R7/R8/R9 integrated acceptance checks: **PASS** on Ubuntu; Windows skips the Unix-only report emission steps as designed.

## Manual state

**NONE.** All behavior is contract/governance logic exercised with synthetic canon/franchise fixtures. No user content judgment or external runtime is required.

## Finalization

This acceptance update changes documentation only. Its resulting exact head must pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #177 can merge with `expected_head_sha`.

After merge, exactly one continuity-only post-merge normalization must pass the same gates and merge. Only that normalization authorizes R11.12.
