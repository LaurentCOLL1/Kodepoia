# R15.4 — Exact/near deduplication, contamination firewall and quarantine

**Status:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING  
**Normalized base:** `ffb5a830cce35334b3f62e69fae2e2c02c717080`  
**Clean START:** `68a6d1a5d35430128db8fa450bd9afa4e0c7c36e`  
**Immutable technical source:** `b82c7595f69f94e173a6e7893073585c9f8c1aae`  
**Manual state:** NONE

## Design

R15.4 adds a deterministic, local, dependency-light duplicate/contamination authority after R15.3 sanitization. The source sanitized payload remains unchanged; comparison normalization and fingerprints are derived metadata only.

`DedupPolicy` versions normalization, shingle size and near-match threshold and exposes a canonical SHA-256 policy digest. Comparison fingerprints bind exact normalized-content SHA-256, sorted SHA-256 shingle identities, token count and policy digest. Exact and near matches are clustered deterministically with stable group IDs independent of input row order.

Near comparison uses repository-owned token shingles and Jaccard similarity. The threshold is inclusive and policy-bound. A policy change produces a different policy/group identity and therefore cannot silently reuse old derived decisions.

Protected benchmark holdouts live in a separate registry whose safe manifest contains only stable IDs and fingerprint metadata. `scan_contamination` compares candidate fingerprints to registered holdouts; exact and threshold-reaching near matches contaminate the duplicate group, and every member of that group is quarantined for downstream dataset building. Near matches remain review-signaled while still failing closed.

## Security and reproducibility invariants

- benchmark raw content is absent from safe registry/report serialization;
- a contaminated member quarantines its complete duplicate group;
- dedup groups are deterministic across row order and platform;
- fingerprints created under different policy digests cannot be compared or reused;
- split-group identity is established before R15.5 so duplicate variants cannot cross train/validation/test;
- source sanitized content is never rewritten by comparison normalization;
- empty/invalid policy or duplicate/conflicting identities fail closed;
- no external dataset, network service, GPU or manual intervention is required for R15.4 acceptance.

## Technical evidence

- focused R15.4 #7 / `33284070954`: SUCCESS Ubuntu + Windows, 68 cumulative R15.1–R15.4 tests per OS + Ruff + compile;
- R0 #2092 / `33284070915`: SUCCESS Ubuntu + Windows;
- Python Core #2067 / `33284070930`: SUCCESS 5/5;
- KodeStudio UI Smoke #2032 / `33284070882`: SUCCESS.

Fresh exact END-head gates remain mandatory before merge.
