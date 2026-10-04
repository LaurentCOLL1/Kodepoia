# V2.6.4 — Production TUF transition and updater compatibility staging

Status: **IMPLEMENTATION / QUALIFICATION — STAGED ONLY — NO LIVE MUTATION AUTHORITY**

V2.6.4 prepares the production-TUF transition required for the terminal Kodepoia `1.1.0`
release while preserving the exact V2.6.3 candidate and the current fail-closed production truth.
It does not publish, sign, refresh, or activate the live repository.

## Frozen release candidate

The transition request is bound to the V2.6.3 candidate, not to the later V2.6.4 development SHA:

- public version: `1.1.0`;
- channel: `stable`;
- platform: `windows-x86_64`;
- source SHA: `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- installer: `KodepoiaSetup.exe`;
- installer bytes: `38,834,833`;
- installer SHA-256: `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- Authenticode truth: unsigned, with the already accepted exact-target `allow-unsigned` policy.

The public/runtime baseline remains `v1.1.0-rc8` until the later publication subdivision succeeds.

## Production observation boundary

V2.6.4 reads the repository-carried production TUF metadata and packaged production Root without
modifying either. The production Root pin must match exactly, the Root threshold remains 2-of-3,
and all top-level role signatures and snapshot/targets cross-bindings must verify.

At the deterministic V2.6.4 reference time (`2026-10-04T00:00:00Z`), Snapshot v10 and Timestamp
v10 are expired. That condition is an expected production observation and remains fail-closed.
V2.6.4 must not extend their existing expiry values, claim that they are fresh, or treat the
current live repository as update-eligible.

## Deterministic transition request

The staging evidence emits a deterministic request for a future governed signing operation. It:

- preserves every currently authorized historical target and requests no revocation;
- requests the stable target path
  `channels/stable/windows-x86_64/1.1.0/46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe`;
- binds the exact V2.6.3 installer hash and byte length;
- retains the existing production Root unchanged;
- requests monotonic Targets, Snapshot, and Timestamp generations;
- requires fresh future Snapshot/Timestamp metadata rather than reusing stale online metadata;
- records that production role signatures are still required later;
- resolves no signing secret and never treats synthetic keys as production proof;
- carries a canonical request digest so later live work can prove it signed the reviewed request.

The request is evidence for a future transition. It is not signed TUF metadata and is not a claim
that a production ceremony has occurred.

## Isolated updater compatibility rehearsal

The existing R18/R19 updater primitives are reused with an explicitly synthetic in-memory TUF
repository. The fixture deliberately does **not** match the candidate installer binary and is
recorded as `production_proof=false`.

The rehearsal proves only updater behavior:

- an installed `1.1.0-rc8` identity selecting the stable channel discovers `1.1.0` as newer;
- wrong-channel discovery does not silently cross-promote;
- the target is TUF/hash validated before install eligibility;
- tampered target bytes are rejected;
- verified cache behavior remains available while offline;
- expired metadata is rejected;
- timestamp rollback is rejected;
- corrupt metadata is rejected;
- a repository rooted in a different Root is rejected.

Existing target-scoped Authenticode semantics are preserved: `allow-unsigned` accepts only an
actually unsigned (`NotSigned`) target; invalid, broken, malformed, or untrusted signatures remain
rejected.

## Effect boundary

V2.6.4 does **not**:

- mutate `update-repository/metadata`;
- invoke R20.4 refresh mode or resolve production online-signing secrets;
- publish a GitHub Release or create/repoint `v1.1.0`;
- upload public release assets;
- activate a live updater target;
- claim production Authenticode signing;
- submit WinGet;
- authorize V2.6.5 or V2.6.6 before V2.6.4 qualification, merge, and normalization.

## Definition of done

V2.6.4 is complete only when the deterministic transition request, production read-only
observation, isolated adversarial updater rehearsal, exact-head tests, and all required PR workflows
succeed on one unchanged head; that head merges with `expected_head_sha`; and a post-merge
normalization records completion and authorizes V2.6.5 only.
