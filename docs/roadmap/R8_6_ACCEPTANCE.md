# R8.6 — Provenance, license/BOM + governed reuse/export — Candidate acceptance

**Status:** CANDIDATE / PENDING EXACT-HEAD CI  
**Manual intervention:** NONE

## Implemented scope

- Bridges canonical R8 Vault revisions into the accepted R6 `BomComponent` / `BomReport` / `LicensePolicy` / `LicenseReport` engine.
- Preserves asset provenance, creator/publisher/attribution/notice evidence without exporting raw local filesystem locators.
- Missing or conflicting license evidence never becomes unrestricted reuse; both are export-blocking.
- Derived revisions expose explicit source-revision requirements from R8 lineage instead of inventing new rights.
- Project BOM inventory is derived from canonical Vault project references.
- Export performs a complete policy/reuse-scope plan before writing, stages all outputs, emits attribution notices + BOM/license evidence, then atomically promotes the export directory.
- Failed/blocked export leaves no promoted partial target.

## Acceptance gates

R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all succeed on one exact implementation head before merge. Post-merge continuity normalization records that exact head, PR/merge SHA, workflow IDs, authoritative test count and final manual state before R8.7 starts.
