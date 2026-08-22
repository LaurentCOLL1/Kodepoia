# R8.4 — Duplicate + near-duplicate detection — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** NONE

## Accepted implementation

- Exact implementation head: `4bf9cbd4892208084cd8ce6554edfd96a971bc04`.
- PR: #88.
- Merge SHA: `a35502e0f5f09e07f3ddfd7f929f6d4d4bb490f7`.

## Authoritative CI on the exact head

- R0 Repository Guard #1050 / `32602783051`: SUCCESS.
- Python Core #1024 / `32602783030`: SUCCESS 5/5.
- Ubuntu authoritative suite: `536 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #991 / `32602783048`: SUCCESS.

## Accepted scope

Exact duplicate grouping by SHA-256 + content length while preserving logical records/provenance; typed/versioned near-duplicate fingerprints; deterministic normalized-document evidence; Pillow image dHash evidence; explicit similarity threshold/algorithm/version/score; durable non-destructive keep-separate/supersession decision records. Detection never auto-deletes or auto-merges.

## Rejected precursor

Candidate `72bfdeddd78df1676addc4e0c4a78e4d9a8e3936` passed its focused behavior but introduced two additional Pillow deprecation warnings through `Image.getdata()`. It was not accepted. The final head switched the R8.4 code to the current flattened-pixel API and restored the existing suite baseline to 46 warnings before acceptance.
