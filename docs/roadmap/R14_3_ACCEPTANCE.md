# R14.3 — Acceptance evidence ledger

## Current state

**Status: TECHNICAL_CANDIDATE_ACCEPTED / FINAL_REGATES_PENDING**

R14.3 starts exactly from R14.2 normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d` on `r14/03-local-backend-runtime`. Mandatory START-sync completed before implementation on head `86dd7e43a2d2895909f8ecd95a743099fc37c55f`; cumulative START-sync changes are exactly `docs/roadmap/R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.

## Frozen claims

R14.3 may claim only:

- deterministic local/test backend workspace generation;
- typed provider-neutral local config and environment overlays;
- KodeSecrets reference-only durable configuration;
- loopback-first repository-owned fixture runtime;
- ProcessSandbox/KillSwitch process ownership;
- liveness/readiness/health observations;
- graceful-first bounded shutdown with governed fallback;
- deterministic scaffold/config/manifest identity and redacted logs.

R14.3 does not claim production serving, public deployment, production TLS, provider hosting, authentication semantics, database implementation, matchmaking, cloud saves, commerce, flags, content delivery, event ingestion or LiveOps.

## Required focused assertions

- zero R14.2 runtime intents cannot manufacture a backend workspace;
- enabled R14.2 runtime intents produce deterministic R14.3 local config;
- non-loopback and privileged bind requests are rejected;
- environment overlay cannot widen host or mutate service selection;
- raw secret values never enter config, manifest, generated files or runtime log;
- strict Draft 2020-12 config/manifest/health schemas accept canonical documents and reject extra fields;
- generate twice yields byte-identical tree and identical manifest digest;
- divergent owned file is not silently overwritten;
- runtime starts on loopback with ephemeral port and reaches READY within a bounded window;
- health/readiness/liveness are observable without external network access;
- runtime is registered with KillSwitch while active and unregistered after stop;
- graceful stop completes in a bounded window with ManagedProcess fallback;
- staging/production config cannot start the R14.3 local fixture;
- occupied fixed port fails closed and leaves no governed process behind;
- Windows and Ubuntu focused execution both pass before technical acceptance.

## Required technical candidate gates

After focused prevalidation, the first accepted immutable implementation candidate must bind one unchanged SHA to fresh:

1. R0 Repository Guard — COMPLETED / SUCCESS.
2. full Python Core — COMPLETED / SUCCESS, including Ubuntu/Windows core, both package builds and internal KodeStudio smoke.
3. KodeStudio UI Smoke — COMPLETED / SUCCESS.

Then END-sync may change only `R14_PLAN.md`, this ledger and continuity before fresh exact-head re-gates, merge with expected-head protection and exactly one continuity-only post-merge normalization.

## Accepted technical candidate record

- Immutable source SHA: `4de5036e7a37f949ec64ae68d9ee45e57ac99631`.
- R0 Repository Guard #1770 / `33146235062`: COMPLETED / SUCCESS.
- Python Core #1744 / `33146235104`: COMPLETED / SUCCESS; Ubuntu full `pytest` = **1477 passed, 13 skipped, 46 warnings**; Windows Core = SUCCESS; both package builds and Python internal KodeStudio smoke = SUCCESS.
- KodeStudio UI Smoke #1711 / `33146235181`: COMPLETED / SUCCESS.
- Focused implementation/compatibility prevalidation `33146069094`: **36 passed** after compileall; diagnostic only and non-authoritative for merge acceptance.
- Cross-platform focused runtime prevalidation `33146135676`: Ubuntu SUCCESS and Windows SUCCESS. A second duplicate cleanup invocation failed only because the temporary files had already been deleted by the first invocation; no implementation test failed and no temporary file remains in the accepted tree.
- Accepted implementation tree: `693662541c60387ecbb14d0994c66266696a9153`.
- Manual intervention: NONE.
- Next authority: END-synchronized documentation/evidence head changing only plan, this ledger and continuity, followed by fresh exact-head R0/Python/UI.

## End synchronization and normalization

The accepted technical source is immutable. END-sync may change only `docs/roadmap/R14_PLAN.md`, this ledger and `docs/continuity/KODEPOIA_CONTINUITY.md`. That final head must pass fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #261 may merge with expected-head protection. Then exactly one continuity-only post-merge normalization must pass another fresh exact-head R0/Python/UI before R14.3 is COMPLETE + NORMALIZED and R14.4 is authorized.

## Manual intervention

**NONE.** No provider account, secret, paid quota, public endpoint, production certificate, managed host or device is required for R14.3 acceptance.
