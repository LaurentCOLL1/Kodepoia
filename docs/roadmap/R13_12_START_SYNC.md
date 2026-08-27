# R13.12 — Start synchronization

**Status:** IN_PROGRESS

**Authorized normalized base:** `fb05135c4a5e1b7177dd4c68e6f05f61a489594e`

**Dedicated branch:** `r13/12-devicelab-matrices`

## Governance state

R13.1–R13.11 are `COMPLETE + NORMALIZED`. R13.12 is the only active subdivision. R13.13–R13.17 remain `PLANNED / NOT STARTED`.

Manual state starts **CONDITIONAL / NOT TRIGGERED**. Core R13.12 acceptance must not require a paid cloud account, production credential, or physical-device quota when equivalent provider-neutral routing/evidence semantics can be proven deterministically with accepted local/hosted providers.

## Frozen implementation direction

DeviceLab will remain provider-neutral and capability-driven. Matrix identity binds platform, provider, model, OS version, locale, orientation, execution/test identity, artifact digest, and requested physical/virtual class. Provider selection must be deterministic and must not silently upgrade simulator/virtual evidence into physical-device proof.

Firebase Test Lab is an optional provider adapter. Official Test Lab semantics treat a test matrix as devices × test executions; device configurations include model, OS version, orientation and locale. Android supports physical and virtual device targets, while iOS Test Lab devices are physical. Quota/cost state is project-scoped and must remain explicit `AVAILABLE`, `UNAVAILABLE`, `QUOTA_EXCEEDED`, `BUDGET_EXCEEDED`, or equivalent bounded capability evidence rather than an inferred PASS.

## Next action

Synchronize the live phase plan and continuity authority to this same R13.12 start state before implementation changes, then implement the provider-neutral DeviceLab contracts, deterministic routing, evidence binding, quotas/budgets, retries/leases and optional Firebase capability seam with focused adversarial tests.
