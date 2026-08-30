# R15.5 — Immutable dataset builder, deterministic splits and dataset cards

**Status:** IMPLEMENTED / TECHNICAL GATES PENDING  
**Normalized base:** `8744df5f3a408595693c67819a29f95b3a82f1d7`  
**Clean START:** `4c9bee744e4c43ef130e50c4867ca3d467878c51`  
**Manual state:** NONE

## Design

R15.5 turns only R15-curated, explicitly authorized, sanitized and licensed Experience records into immutable derived datasets. It consumes the authoritative R15.4 `DedupResult` and `ContaminationReport`; it does not recreate duplicate or holdout similarity logic.

`DatasetPolicy` binds the explicit seed, sanitizer digest, R15.3 governance-policy digest, R15.4 dedup-policy digest, split weights, optional task/domain filters, duplicate handling, deterministic per-domain group cap and deterministic `(domain, task)` stratum cap into one canonical SHA-256 policy digest. Any mismatched sanitizer, governance lineage, dedup authority or contamination report fails closed rather than silently rebuilding under changed assumptions.

Split membership is derived from the stable R15.4 `group_id`, explicit seed and complete dataset-policy digest. Every member of one duplicate group therefore receives one split regardless of input row order. `train` and `validation` are required; an optional internal `test` split is supported but remains distinct from KodeBench protected holdouts.

The default duplicate policy exports only the representative selected by R15.4. A governed `keep_group` policy may preserve all eligible variants, but group atomicity still prevents cross-split leakage. Optional balancing ranks complete groups deterministically by domain and/or `(domain, task)` strata; it never samples individual rows across group boundaries.

## Source and representation boundary

`DatasetSource` verifies the supplied sanitized text byte-for-byte against the governed `ContentRef` SHA-256 and byte length. The builder accepts only `CURATED` records with PASSED sanitization, fully allowed training authorization, explicit license metadata and matching R15.3 sanitizer/governance lineage. Benchmark-protected or R15.4-contaminated groups are excluded before selection.

Canonical tokenizer-independent source forms are:

- plain `text`;
- exact `prompt` + `completion` JSON objects;
- exact `messages` arrays with structured roles/content.

No tokenizer, chat template or model-family formatting is baked into the immutable source representation. Training-specific templating remains downstream work.

## Immutable artifacts, provenance and reconciliation

Each JSONL row is canonical JSON, ordered by deterministic `example_id`, and includes stable source/group/task/domain/language identity plus the governed payload. Per-split bytes and SHA-256 digests are reproducible from the same manifest-bound source state.

The canonical dataset manifest intentionally contains no raw training payload and no governed `storage_key`. It records source/content/contract/row/representation digests, safe provenance (`source_type`, `source_id`, `origin_digest`, `project_scope`, license), R15.4 group/split identity, transformation lineage, complete policy descriptor, selection exclusions, and per-split byte/domain/task/language/group statistics.

Every completed `DatasetBuild` performs a fail-closed reconciliation pass over its JSONL bytes: export digest, byte count, row count, `example_id`, split, source/group/task/domain/language/format metadata and canonical `row_digest` must all match the manifest. A tampered or incomplete export therefore cannot be returned as a valid build.

The dataset card is a separate derived documentation record containing dataset/policy identity, intended use, limitations, licenses, languages, domains, tasks and aggregate split statistics. Its Markdown rendering includes YAML-compatible metadata for interoperability, but R15.5 does not authorize publication or upload to any public hub.

`repository_file_map()` exposes manifest/card/README plus split JSONL files as a framework-neutral local export. `huggingface_file_map()` is a zero-network interoperability adapter exposing only `README.md` and conventional `train.jsonl`, `validation.jsonl`, `test.jsonl` files; it performs no account access or upload.

## External interoperability reference

Hugging Face documentation currently recognizes JSONL as a supported dataset file format, conventional `train` / `validation` / `test` split names, and dataset cards as documentation surfaces for dataset context, responsible use and metadata such as license/language. R15.5 uses those conventions only for interoperability; Kodepoia's repository-owned manifest and governance policies remain authoritative.

References:

- https://huggingface.co/docs/datasets/repository_structure
- https://huggingface.co/docs/hub/datasets-cards
- https://huggingface.co/docs/dataset-viewer/configs_and_splits

## Security and reproducibility invariants

- no protected holdout or contaminated duplicate group enters an export;
- duplicate groups cannot cross splits;
- row order cannot change dataset identity, split membership or exported bytes;
- domain and `(domain, task)` balancing operate only on complete groups;
- a sanitizer/governance/dedup policy mismatch fails closed;
- source payload digest and byte length are reconciled before export;
- manifest provenance remains traceable without exposing governed storage keys;
- manifests/cards contain no raw payload or governed storage key;
- every export row is reconciled back to manifest identity and digest;
- JSONL is derived payload, never source authority;
- missing explicit license, non-CURATED state or unresolved authorization is not promoted;
- dataset/card/row/export identities use canonical SHA-256 digests;
- public-framework adapters are local file maps only and confer no publication authorization;
- no GPU, model download, network dataset, public account or manual intervention is required.

## Technical evidence

Pending fresh exact-head R15.5 acceptance on Ubuntu + Windows, followed by R0 Repository Guard, full Python Core and KodeStudio UI Smoke.
