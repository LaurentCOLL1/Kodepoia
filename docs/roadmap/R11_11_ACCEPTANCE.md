# R11.11 — Acceptance

Status: **IMPLEMENTED — HOSTED EXACT-HEAD GATES PENDING**  
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
- R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all be SUCCESS on one exact candidate head.
- After run IDs are recorded here, the final documentation head is re-gated before merge.

## Manual state

**NONE.** All behavior is contract/governance logic exercised with synthetic canon/franchise fixtures. No user content judgment or external runtime is required.

## Completion ordering

Accepted exact head -> final acceptance update -> re-gate exact final head -> merge with `expected_head_sha` -> exactly one continuity-only post-merge normalization -> exact-head R0/Python/UI -> merge normalization -> only then R11.12 is authorized.
