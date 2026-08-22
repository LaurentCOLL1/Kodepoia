# R7.9 implementation changelog

- Added content-addressed query/result cache manifests under `.kodepoia/research/cache`.
- Added TTL/revalidation assessment without rewriting source freshness.
- Added version/content/source-sensitive deduplication.
- Added typed cached-report reload validation through `ResearchStore`.
- Added bounded citation-preserving Context summaries with secret redaction and guard/trust metadata.
- Added explicit project-only Research Memory bridge with global/training promotion disabled.
- Added deterministic schemas and acceptance tests.
