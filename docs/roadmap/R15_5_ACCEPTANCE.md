# R15.5 — Acceptance record

**Acceptance state:** IMPLEMENTED / TECHNICAL GATES PENDING  
**Clean START:** `4c9bee744e4c43ef130e50c4867ca3d467878c51`  
**Manual:** NONE

## Acceptance contract

R15.5 is accepted only when the exact technical head proves on Ubuntu and Windows that immutable dataset construction remains deterministic, group-safe, contamination-safe, provenance-traceable and manifest/export reconciled, and the same final documented END-head passes R0 Repository Guard, full Python Core and KodeStudio UI Smoke.

## Required adversarial coverage

The focused acceptance must prove:

- deterministic policy and dataset identities;
- row-order-independent split membership and byte-identical JSONL rebuilds;
- optional internal test split without using KodeBench protected holdouts;
- one split per authoritative R15.4 duplicate group;
- authoritative R15.4 representative selection and governed full-group mode;
- complete exclusion of exact/near contaminated groups;
- fail-closed sanitizer/governance/dedup policy mismatch handling;
- source digest and byte-length reconciliation;
- only CURATED, fully authorized, explicitly licensed records are selected;
- deterministic domain and `(domain, task)` balancing at complete-group granularity;
- tokenizer-independent text, prompt-completion and conversational source forms;
- safe manifest provenance fields reconcile to the Experience provenance source;
- canonical manifest-to-JSONL reconciliation for example ID, split, source/group/task/domain/language/format metadata and row digest;
- tampered JSONL or export digest mismatch fails closed;
- no raw payload or governed `storage_key` in manifests/cards;
- per-split hashes, byte counts, row/group counts and domain/task/language statistics;
- local repository and Hugging Face-compatible file maps require no network or publication authorization;
- repository JSON-schema validation for manifest and dataset-card records.

## Evidence

Pending fresh exact-head R15.5 acceptance after completion of the full planned scope. No stale run or pre-correction SUCCESS claim is accepted as final evidence.
