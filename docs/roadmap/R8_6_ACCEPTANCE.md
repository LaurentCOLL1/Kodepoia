# R8.6 — Provenance, license/BOM + governed reuse/export — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** NONE

## Accepted implementation

- Exact implementation head: `8c88aeb8a32abce2e9ecb670da3c2acbb4a31cfe`.
- PR: #91.
- Merge SHA: `57c2aa010f438b95a3d753040f1565ae4b68e262`.
- Rejected precursor: `85b6c0a550297934194a58122b735a9d0808c5c6` — fixture-only contract misuse; not accepted.

## Authoritative CI on the exact head

- R0 Repository Guard #1057 / `32603562499`: SUCCESS.
- Python Core #1031 / `32603562511`: SUCCESS 5/5.
- Ubuntu authoritative suite: `547 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #998 / `32603562503`: SUCCESS.

## Accepted scope

- Bridges canonical R8 Vault revisions into the accepted R6 `BomComponent` / `BomReport` / `LicensePolicy` / `LicenseReport` engine rather than introducing a second legal engine.
- Preserves provenance, creator/publisher, attribution, notice and evidence references while redacting local filesystem locators from exported evidence.
- Missing or conflicting license evidence never becomes unrestricted reuse; both are export-blocking.
- Derived revisions expose explicit source-revision requirements from R8 lineage rather than inventing rights.
- Project BOM inventory is derived from canonical Vault project references.
- Export preflights all policy and reuse-scope decisions before writing, stages outputs inside the authorized export boundary, emits attribution notices plus BOM/license evidence, then atomically promotes the completed export directory.
- Blocked or failed export leaves no promoted partial target.

## Rejected precursor

The first candidate `85b6c0a550297934194a58122b735a9d0808c5c6` failed five newly added tests because its fixture constructed `ProjectAssetReference` with positional fields in the wrong order and called an obsolete shape of the already-frozen R8.3 transform API. Existing tests remained green. The correction changed only the fixture to use the accepted contracts; production safeguards were not weakened.

## Manual gate outcome

R8.6 manual state is **NONE**. No user-side command, credential, network account or local provider was required for authoritative acceptance.
