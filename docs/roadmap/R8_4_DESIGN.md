# R8.4 — Duplicate + near-duplicate detection — Design

R8.4 keeps exact byte identity and probabilistic similarity separate.

- Exact duplicates are grouped only by verified SHA-256 + content length; identical bytes do not collapse logical asset IDs, revisions or provenance.
- Near-duplicate detection is typed and versioned. Images use a 64-bit difference hash built from a grayscale 9x8 resample; documents have a deterministic normalized-text shape fingerprint.
- Every near candidate records algorithm, algorithm version, score and the exact revision pair. Thresholds are explicit and never redefine content identity.
- Fingerprinting reads only verified Vault object paths. Unsupported asset kinds produce no guessed similarity result.
- Decisions such as `KEEP_SEPARATE` or logical supersession are durable records only. Detection never deletes, overwrites, rewrites provenance or silently merges assets.
- Pillow is already an accepted dependency in Kodepoia; R8.4 does not add a new external binary or network service.
