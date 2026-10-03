# V2.6.2 — Full V2 integrated regression and adversarial hardening

Status: **IMPLEMENTATION / QUALIFICATION — NO PUBLICATION AUTHORITY**

V2.6.2 proves the terminal V2 codebase under the no-new-feature freeze established by
V2.6.1. It does not add product capability and does not create a release candidate.

## Authority and frozen release truth

V2.6.1 is COMPLETE + NORMALIZED. V2.6.2 is the only authorized implementation
subdivision.

The frozen release truth remains unchanged:

- terminal public target: Kodepoia `1.1.0`, stable, release, tag `v1.1.0`;
- current public/runtime baseline: `v1.1.0-rc8`;
- exact candidate source SHA: still unset until V2.6.3;
- production Authenticode signing: not verified;
- WinGet publication: OUT for `v1.1.0`;
- production TUF snapshot/timestamp freshness: stale/expired and fail-closed;
- production TUF mutation: not authorized in V2.6.2.

## Integrated regression gate

The existing `Python Core` matrix is the canonical integrated V2 regression gate.
It already runs the exact-head V2.0 through V2.6.1 acceptance scripts and then the
complete `pytest` suite on Ubuntu and Windows.

V2.6.2 evidence is deliberately generated only after that full `pytest` step.
GitHub Actions applies the default success condition to later steps, so a failed
earlier regression prevents the V2.6.2 evidence step from running.

The V2.6.2 layer therefore aggregates terminal evidence; it does not replace or
weaken historical acceptance suites.

## Critical-veto domains

The terminal veto is fail-closed across:

- ResearchGuard network/provenance/cancellation boundaries;
- Project Knowledge project isolation, provenance, prompt-injection and secret handling;
- Model Lab privacy/license/contamination/evaluation/activation gates;
- multi-GPU topology, lineage, launcher and provider-truth boundaries;
- cross-workspace handoff, approval, cancellation, recovery and secret sanitization;
- prompt-injection, secrets and MemoryStore integrity/isolation;
- KillSwitch cancellation, recovery, backup and checkpoint integrity;
- project durability and bounded resource-soak policy;
- updater offline/freshness/rollback/tamper and verified-delivery behavior;
- packaged Windows custom-directory install, trusted updater resources, smoke and uninstall;
- V2.6.1 terminal release identity and no-publication freeze.

Any missing critical domain is a V2.6.2 veto.

## Determinism and provider independence

Mandatory V2.6.2 focused acceptance uses repository state and deterministic tests only.
It requires no live provider, no network credential and no Kaggle action. Historical
live evidence remains historical evidence and is never fabricated or refreshed here.

## Effect boundary

V2.6.2 performs no live release effect. It must not:

- publish a GitHub Release;
- create or repoint `v1.1.0`;
- upload public release assets;
- mutate production TUF metadata;
- activate a live updater target;
- provision signing secrets;
- submit WinGet.

V2.6.3 remains unauthorized until V2.6.2 is exact-head qualified, merged with
unchanged-head protection and post-merge normalized.
