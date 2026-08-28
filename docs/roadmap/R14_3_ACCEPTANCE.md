# R14.3 — Acceptance evidence ledger

## Current state

**Status: IMPLEMENTATION_CANDIDATE_PENDING**

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

## Manual intervention

**NONE.** No provider account, secret, paid quota, public endpoint, production certificate, managed host or device is required for R14.3 acceptance.
