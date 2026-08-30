# R15.5 — Acceptance record

**Acceptance state:** IMPLEMENTED / TECHNICAL GATES PENDING  
**Clean START:** `4c9bee744e4c43ef130e50c4867ca3d467878c51`  
**Manual:** NONE

## Acceptance contract

R15.5 is accepted only when the exact technical head proves on Ubuntu and Windows that immutable dataset construction remains deterministic, group-safe and contamination-safe, and the same final documented END-head passes R0 Repository Guard, full Python Core and KodeStudio UI Smoke.

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
- deterministic task/domain balancing at group granularity;
- tokenizer-independent text, prompt-completion and conversational source forms;
- canonical manifest-to-row/source digest reconciliation;
- no raw payload or governed `storage_key` in manifests/cards;
- per-split hashes/counts/domain/task/language/group statistics;
- repository JSON-schema validation for manifest and dataset-card records.

## Evidence

Pending. No run ID or SUCCESS claim is recorded until the corresponding exact-head CI result exists.
