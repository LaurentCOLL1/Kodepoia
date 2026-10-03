# V2.6.2 — Full V2 integrated regression and adversarial hardening

Status: **UNDER QUALIFICATION — NO PUBLICATION AUTHORITY**

V2.6.2 proves the terminal V2 codebase under the no-new-feature freeze established by V2.6.1.
It does not create a new product capability and it does not create release, tag, updater, TUF,
signing or WinGet publication authority.

## Exact authority

V2.6.1 is COMPLETE + NORMALIZED from implementation PR `#553` and normalization PR `#554`.

The accepted terminal release freeze remains unchanged:

- target: `Kodepoia 1.1.0`;
- channel: `stable`;
- build type: `release`;
- tag: `v1.1.0`;
- current public/runtime baseline: `v1.1.0-rc8`;
- candidate source SHA: deliberately unset until V2.6.3;
- production Authenticode signing: not verified;
- WinGet publication: OUT;
- production TUF snapshot/timestamp freshness: expired and fail-closed;
- production TUF transition/freshness resolution: V2.6.4 only.

## Integrated regression contract

The existing exact-head V2 acceptance chain remains authoritative and is rerun on every Python Core
pull-request job:

- V2.0 capability truth;
- V2.1.1 through V2.1.6 Research Workspace;
- V2.2.1 through V2.2.6 Project Knowledge / Context / Memory;
- V2.3.1 through V2.3.6 Model Lab governance;
- V2.4.1 through V2.4.6 accelerator / distributed production hardening;
- V2.5.1 through V2.5.6 cross-workspace orchestration;
- V2.6.1 terminal release freeze.

The complete `pytest` suite must pass before the V2.6.2 evidence artifact is generated. This keeps
the evidence bound to the same exact source that passed the complete deterministic Python regression
suite on Ubuntu and Windows.

## Critical-veto domains

V2.6.2 aggregates fail-closed evidence over these mandatory domains:

1. `v2-regression` — the complete accepted V2.0-V2.5 chain remains wired and executable;
2. `security-privacy` — prompt injection, secret handling, tool authority and quarantine;
3. `workspace-memory-research` — project scope, memory integrity, ResearchGuard and knowledge trust;
4. `model-lab` — privacy/licensing/holdout, candidate quality, accelerator lineage and live-proof honesty;
5. `orchestration` — fixed routing, exact approval, handoff integrity, cancellation and recovery;
6. `packaged-windows` — packaged KodeStudio smoke, custom install path, uninstall and project durability;
7. `resilience` — KillSwitch, recovery, corruption rejection and bounded resource soak;
8. `updater` — offline/local availability, rollback/freeze/expiry and verified metadata fail-closed behavior;
9. `release-freeze` — V2.6.1 identity, Authenticode, WinGet and no-public-effect truth stays unchanged;
10. `ci-evidence` — exact-head Ubuntu/Windows evidence is generated only after the full Python test suite.

A failure in any critical domain is a release-hardening veto. A veto cannot be converted into a pass
by averaging, by unrelated successful domains or by provider availability.

## Provider and live boundaries

Mandatory V2.6.2 evidence is deterministic and provider-independent. It must not require live Kaggle,
new network access, credentials, signing keys or production TUF custody.

Previously accepted live evidence remains historical evidence. V2.6.2 must not fabricate new live
success and must not weaken the distinction between fixture, staged and production evidence.

## Windows and durability boundaries

Existing Windows acceptance remains mandatory:

- KodeStudio UI smoke on packaged-relevant surfaces;
- package build on Windows;
- R17 installer build;
- silent custom-directory installation;
- installed application smoke independent of the development Python environment;
- trusted updater resources present in the installation;
- uninstall verification;
- project durability regression coverage.

V2.6.2 does not freeze the final release candidate. That belongs to V2.6.3.

## Updater and TUF boundary

Expired TUF metadata remains rejected. Offline/unavailable update state remains distinct from
verification failure. Rollback, metadata tampering and expiry must fail closed.

V2.6.2 must not refresh, resign or mutate production TUF metadata. The observed production
snapshot/timestamp expiry remains unresolved until the authorized V2.6.4 transition stage.

## Definition of done

V2.6.2 is complete only when:

- all required critical domains are represented by deterministic checks;
- the full V2 acceptance chain remains wired;
- the complete Python test suite succeeds on Ubuntu and Windows;
- packaged Windows/UI/durability surfaces remain mandatory;
- critical-veto aggregation reports no veto;
- exact-head V2.6.2 evidence is emitted on Ubuntu and Windows;
- all required pull-request workflows succeed on the unchanged exact head;
- the implementation PR merges with `expected_head_sha`;
- post-merge normalization authorizes V2.6.3 only.

No public release effect is authorized by V2.6.2.
