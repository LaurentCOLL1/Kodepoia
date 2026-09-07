# R19 — Installed Experience & Trusted Self-Update Hardening

Status: **PLANNING CANDIDATE**

Started: **2026-09-07**

Planning base: `main` `d0ba02f9d8101890602c5e1a412292cb27aa08c3` — R18 remains **COMPLETE + NORMALIZED** and frozen. No `R18.12` is authorized.

## Phase objective

Resolve the two defects observed in the installed Windows `v1.1.0-rc1` build and turn the R18 update primitives into a real installed-product workflow: reliable French/English preference behavior, a production/beta TUF repository bootstrap, a bounded HTTPS update transport wired into packaged startup, a user-consented in-app Windows update handoff, and release automation/integrated acceptance for the next corrective prerelease.

R19 is a post-R18 hotfix/evolution phase. It does not reopen or rewrite the completion semantics of R18.

## Verified starting facts

- Public prerelease: `v1.1.0-rc1`, source `c64bac012ef3afa332526a539901b11428fd966f`, `production_signed=false`.
- Installed application starts successfully on Windows.
- On a French Windows system, selecting English currently does not visibly retranslate the running UI.
- Current locale persistence rewrites `~/.kodepoia/settings.json` with only `{"locale": ...}`.
- Current locale precedence is explicit request, `KODEPOIA_LOCALE`, saved preference, OS detection.
- Packaged startup currently reaches the update settings UI with no production update service injected, producing `no structured update repository is configured`.
- R18 already provides verified TUF metadata parsing/verification, rollback/freeze/expiry defenses, target hash/size verification, staged verified download and explicit-confirmation installer handoff.
- `src/kodepoia/update/bootstrap.py` contains only a synthetic acceptance root and must not be treated as production trust.

## External architecture constraints re-verified for planning

- TUF requires four top-level roles: Root, Targets, Snapshot and Timestamp. Targets metadata binds target hashes/sizes; Snapshot provides repository consistency; Timestamp limits freeze/staleness exposure.
- GitHub REST `GET /releases/latest` returns the latest non-prerelease, non-draft release, so it cannot be the sole discovery mechanism for the current beta/RC channel.
- Public GitHub Release assets may be used as installer payload storage, but TUF metadata remains the authorization authority for what Kodepoia is allowed to install.

## Phase-wide governance and security boundaries

- R18 remains frozen; no R18 subdivision is added or modified.
- Never mutate the already published `v1.1.0-rc1` asset in place to simulate an update.
- Never commit, package, log or surface private TUF keys, Authenticode private keys, passwords or tokens.
- Synthetic acceptance trust material must remain unmistakably non-production and must never be silently promoted.
- Network update availability must never gate application startup or normal offline/local-first use.
- Update discovery accepts only repository-defined/allowlisted metadata and target paths; model-generated arbitrary URLs are non-authoritative.
- No installer is launched without explicit user confirmation after version/source/hash/size verification.
- User settings, projects, Project DNA, assets and local model data must remain outside update replacement scope except through existing guarded migration/backup contracts.
- All R19 branches require exact-head validation before merge and expected-head merge protection. Each completed subdivision is followed by a continuity-only normalization before the next subdivision starts.
- If a subdivision reaches a genuine external credential/custody boundary — real TUF private-key creation/custody, Authenticode certificate use, repository secret configuration or equivalent — stop before later subdivisions and provide the user exact manual actions.

## Subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R19.1 | Language Switching Hardening | PLANNED | NONE | normalized R19 planning |
| R19.2 | Production/Beta Update Repository Bootstrap | PLANNED | POSSIBLE / EXPECTED AT REAL KEY CUSTODY BOUNDARY | R19.1 |
| R19.3 | Network UpdateTransport & Packaged Startup Wiring | PLANNED | NONE after R19.2 public trust material exists | R19.2 |
| R19.4 | Seamless Windows In-App Update | PLANNED | NONE | R19.3 |
| R19.5 | Corrective RC Release Automation & Integrated Acceptance | PLANNED | CONDITIONAL for external signing/secrets/publication effects | R19.1–R19.4 |

No subdivision may be silently added, removed, merged, split or renumbered. Any scope change requires an explicit roadmap + continuity change in a governed work cycle.

---

# R19.1 — Language Switching Hardening

## Objective

Make French ↔ English selection reliable, persistent, merge-safe and immediately understandable in the installed Windows application.

## In scope

- introduce one authoritative application preference store for persisted application preferences;
- load/save settings atomically and merge-safely so changing locale preserves unrelated keys;
- define locale precedence so an explicit runtime/test request wins, then a persisted user preference wins normal product startup, then OS detection; environment override is developer/diagnostic-only and must not silently defeat the user's saved choice in the packaged product;
- replace the language selector's persistence-only behavior with immediate retranslation when feasible; otherwise provide a controlled restart/apply path that is explicit and deterministic;
- ensure v1.1 navigation, settings, chat/update surfaces and other visible labels are sourced from `V11Translator` or a compatible authoritative translation source;
- ensure French → English → French round-trip preserves unrelated preferences;
- add focused unit/UI acceptance and packaged Windows acceptance for persistence/restart behavior.

## Acceptance vetoes

R19.1 is not complete if any of the following remains true:

- selecting English then restarting still shows French because of packaging/environment precedence;
- switching locale clobbers unrelated settings;
- current-window locale behavior is silent/ambiguous to the user;
- a major v1.1 visible surface remains hard-coded to the wrong language source;
- English → French switch-back does not persist.

## Required acceptance matrix

1. French OS locale, no saved preference => French UI.
2. Select English => persisted `en`.
3. Running UI retranslates immediately, or a controlled explicit restart path applies the choice.
4. Restart packaged Kodepoia => English navigation/settings/chat/update labels.
5. Select French => persisted `fr`.
6. Restart => French UI.
7. Unrelated settings survive both switches byte-semantically.
8. Packaging environment does not accidentally force French over a saved English preference.
9. Invalid/corrupt preference content fails safely to deterministic fallback without crashing startup.

## Likely implementation files

- `src/kodepoia/kodestudio/app_v11.py`
- `src/kodepoia/kodestudio/v11_localization.py`
- new/extended application preference module under `src/kodepoia/kodestudio/`
- focused tests under `tests/`
- Windows packaged acceptance/workflow files as required

## Manual intervention

**NONE**.

---

# R19.2 — Production/Beta Update Repository Bootstrap

## Objective

Create the real structured beta/release update repository and public trust anchor that installed Kodepoia clients can consume without relying on synthetic R18 acceptance material.

## In scope

- choose and document the canonical HTTPS metadata base URL and target/payload URL strategy;
- establish a beta/release TUF repository layout using Root, Targets, Snapshot and Timestamp metadata;
- define role thresholds, key separation, rotation procedure and expiry policy;
- establish a packaged public root trust anchor distinct from `trusted_root.synthetic.json`;
- define canonical target paths such as `channels/beta/windows-x86_64/<version>/<source_sha>/KodepoiaSetup.exe`;
- include target SHA-256, byte size, source SHA, release channel, version and release-note/status metadata required by Kodepoia discovery;
- preserve GitHub Release assets as acceptable payload storage while making TUF metadata the authorization source;
- provide deterministic local/synthetic generation and verification fixtures before real keys are introduced;
- document offline recovery/rotation and compromised-key procedure.

## Manual intervention boundary

No manual action is required for schema/layout/fixture implementation. The moment real beta/production TUF private keys must be generated, stored, imported into a secret store, or used outside repository-safe synthetic fixtures, R19.2 must stop and provide exact user actions. No later subdivision starts until real public root material is safely established.

## Acceptance vetoes

- production bootstrap references synthetic acceptance root as real trust;
- private key material enters Git, packages, logs, artifacts or continuity;
- target metadata lacks hash/size/source/channel binding;
- repository URL/layout cannot be consumed over HTTPS by an installed client.

---

# R19.3 — Network UpdateTransport & Packaged Startup Wiring

## Objective

Replace `service=None` in the packaged application with a real bounded HTTPS discovery/delivery stack backed by the R19.2 trust anchor.

## In scope

- implement bounded HTTPS transport with explicit connect/read timeouts, size ceilings and deterministic error mapping;
- allowlist top-level metadata names and authorized target paths;
- prevent redirects/scheme changes from escaping approved HTTPS update origins unless explicitly covered by the repository contract;
- instantiate `PackagedRootPin`, `UpdateDiscoveryService` and verified delivery/install service from packaged startup;
- inject services into `build_window(...)`/update settings;
- keep startup independent of update-network availability;
- expose offline, TLS, metadata-expiry, trust and repository errors as non-destructive UI states;
- test stable/beta/nightly isolation against a controlled HTTPS fixture and packaged startup.

## Acceptance veto

Installed Kodepoia must no longer report `no structured update repository is configured` when configured for the real beta repository.

## Manual intervention

**NONE**, assuming R19.2 public trust material and endpoint exist.

---

# R19.4 — Seamless Windows In-App Update

## Objective

Allow a user to discover, download, verify and install a newer authorized Windows Kodepoia build from inside Kodepoia without manually fetching the installer.

## Required flow

1. User chooses Check for updates.
2. Kodepoia fetches and verifies trusted metadata.
3. UI presents authorized version, channel, size and notes.
4. User chooses Download and verify.
5. Installer is staged in Kodepoia-managed update storage.
6. TUF/hash/size/source checks pass before install is enabled.
7. User explicitly confirms Install update.
8. Kodepoia launches only the verified Inno Setup payload in the governed upgrade mode, exits safely, preserves user data/settings, and relaunches when the installer contract permits.
9. Result is recorded as success/failure/recovery evidence.

## In scope

- guarded process handoff and shutdown/relaunch coordination;
- stale/tampered staged payload rejection;
- cancellation and offline recovery;
- preservation of user preferences/projects;
- installer return/result handling where available;
- no silent install before explicit confirmation.

Delta patching is out of scope until the full-installer self-update path is reliable.

## Manual intervention

**NONE**.

---

# R19.5 — Corrective RC Release Automation & Integrated Acceptance

## Objective

Ship the first corrective prerelease after `v1.1.0-rc1` and prove the full installed upgrade path end to end.

## Version authority

The intended next prerelease identity is **`1.1.0-rc2`**, subject to the existing canonical release-identity machinery and exact-source release acceptance. `v1.1.0-rc1` remains immutable historical release state and is never overwritten.

## In scope

- update canonical release identity to the authorized corrective RC;
- build and verify Windows installer/bundle/provenance using existing R18 machinery;
- publish/update TUF target metadata so the new RC becomes discoverable to beta clients;
- integrated Windows acceptance from an older installed RC to the new RC;
- release publication automation only through explicit governed effects already authorized by repository policy;
- preserve truthful `production_signed` state;
- maintain rollback/revocation and withdrawal handling.

## Required integrated acceptance matrix

- older installed RC detects the newer authorized beta RC;
- stable does not consume beta/nightly;
- beta consumes only authorized beta/RC targets;
- tampered installer rejected;
- wrong hash/size/source rejected;
- expired metadata rejected;
- rollback/freeze rejected;
- withdrawn target rejected;
- offline state is non-destructive;
- install never starts without explicit user confirmation;
- application relaunches on updated version;
- projects and user settings remain intact;
- French/English preference remains intact through the update;
- clean uninstall succeeds after update.

## Manual intervention

**CONDITIONAL**. Production Authenticode signing, external credential use, repository secret configuration, public release publication or another external effect must stop at the exact boundary if credentials/authorization unavailable in the connected tooling. No private credential is requested or stored in repository content.

---

## Planning acceptance / Definition of Done

Before R19.1 starts:

- this roadmap and the corresponding R19 continuity record exist on a dedicated planning branch from exact `main`;
- R0 Repository Guard passes on the exact planning head on Ubuntu + Windows;
- full Python Core acceptance passes on the exact planning head;
- KodeStudio UI Smoke passes on the exact planning head;
- planning PR is merged with exact expected-head protection;
- one continuity-only post-merge planning normalization is gated and merged;
- only then is R19.1 START-sync authorized.

## Rollback / recovery

Planning can be reverted without product runtime effect because no R19 implementation is authorized until normalized planning enters `main`. Each implementation subdivision remains independently revertible through its branch/PR/normalization boundary.
