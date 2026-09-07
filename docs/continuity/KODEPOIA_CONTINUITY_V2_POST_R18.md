# KODEPOIA CONTINUITY V2 — POST-R18

**Status:** ACTIVE POST-R18 CONTINUITY AUTHORITY

**Purpose:** this file is the hand-off document to resume work if the current ChatGPT conversation reaches its length limit. It records the authoritative post-R18 repository state, the first defects found on the installed Windows prerelease, the verified code-level causes, the desired product behavior, and the next implementation sequence. It does **not** reopen R18, create R18.12, or alter the frozen R18 completion authority.

---

## 1. Canonical repository and release state

- Repository: `LaurentCOLL1/Kodepoia`.
- Canonical `main` at creation of this continuity v2: `c0896c2783e76e49fda1744171c6523ce1293a9f`.
- R18 remains **COMPLETE + NORMALIZED**. R18.1–R18.11 are complete; no R18.12 is authorized.
- Public Windows prerelease: `v1.1.0-rc1` / **Kodepoia 1.1.0-rc1**.
- Release accepted source: `c64bac012ef3afa332526a539901b11428fd966f`.
- Public Release URL: `https://github.com/LaurentCOLL1/Kodepoia/releases/tag/v1.1.0-rc1`.
- Public installer asset: `KodepoiaSetup.exe`.
- Installer size: `37192342` bytes.
- Installer SHA-256: `3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0`.
- The same payload is mirrored at repository root as Git LFS path `/KodepoiaSetup.exe`, with `/KodepoiaSetup.exe.sha256` beside it.
- Current release is a prerelease / beta-RC and remains `production_signed=false`.
- Public WinGet submission, production Authenticode signing, and production TUF key custody/rotation have **not** been triggered.

### Important distinction

R18 proved the update/release mechanisms using trusted/synthetic acceptance infrastructure. The public `v1.1.0-rc1` publication made the installer discoverable, but it did **not** by itself create a production structured update repository or production TUF trust anchor for installed clients.

---

## 2. Real installed-user feedback that starts the post-R18 track

The Windows installation itself completed successfully.

Two user-visible defects were then observed in the installed application:

1. **Language selection defect / unclear behavior**
   - The application starts in French on a French Windows system.
   - In Settings, selecting **English** does not visibly switch the application away from French.
   - Desired result: the language choice must reliably switch between French and English, persist, and be obvious to the user. Prefer immediate retranslation; if a restart is technically required, the UI must clearly apply/prompt/restart and the next launch must honor the choice.

2. **Updater unavailable in the installed application**
   - Clicking **Rechercher des mises à jour / Check for updates** returns:
     `Canal indisponible: no structured update repository is configured`
   - Desired result: Kodepoia must be able to discover, download, verify, and install future Kodepoia updates **from inside Kodepoia**, without the user having to manually download and run a full installer again.
   - Reusing the existing installer internally as the upgrade engine is acceptable for the first implementation, provided Kodepoia performs the download/verification/handoff itself and the user only gives explicit update confirmation. Delta patching can be considered later.

These two defects are **not fixed yet** by this continuity file.

---

## 3. Verified diagnosis — language behavior

Relevant implementation:

- `src/kodepoia/kodestudio/app_v11.py`
- `src/kodepoia/kodestudio/v11_localization.py`

Verified behavior in `app_v11.py`:

- Language selector values are `fr` and `en`.
- Changing the selector only executes `_save_locale(...)`.
- `_save_locale` writes `~/.kodepoia/settings.json`.
- The Settings text explicitly says the selected language is used **the next time KodeStudio starts**.
- The current window is **not rebuilt/retranslated** when the combo box changes.
- Startup locale precedence is currently:
  1. explicit `requested` locale,
  2. environment variable `KODEPOIA_LOCALE`,
  3. saved locale in `~/.kodepoia/settings.json`,
  4. detected OS locale.

Verified behavior in `v11_localization.py`:

- Both real `en` and `fr` message catalogs exist.
- If no explicit locale is resolved, a French OS selects `fr`; otherwise the default is English.

### Language defect hypotheses to verify in the next implementation session

A. The user is expecting an immediate switch, but the current product only persists the selection for next launch. This alone explains why the visible UI remains French immediately after selecting English.

B. If the application is **still French after a complete restart**, check whether packaged launch/runtime sets `KODEPOIA_LOCALE=fr`; that environment variable currently outranks the saved preference.

C. Verify that the installed packaged app resolves the same Windows home directory for both write and read of `~/.kodepoia/settings.json`.

D. `_save_locale` currently rewrites that JSON object with only `{"locale": ...}`. This is acceptable only while that file is locale-only; it should become merge-safe before other application settings share it.

### Required language acceptance

At minimum, automated Windows packaged acceptance must prove:

1. launch under French OS locale with no saved preference => French UI;
2. select English => persisted `en`;
3. restart installed Kodepoia => English navigation/settings/chat labels;
4. select French => persisted `fr`;
5. restart => French UI again;
6. no accidental override from packaging environment;
7. ideally, switching language retranslates the current window immediately without a restart.

---

## 4. Verified diagnosis — update error

Relevant implementation:

- `src/kodepoia/kodestudio/app_v11.py`
- `src/kodepoia/kodestudio/update_settings.py`
- `src/kodepoia/update/discovery.py`
- `src/kodepoia/update/delivery.py`
- `src/kodepoia/update/trust.py`
- `src/kodepoia/update/bootstrap.py`

### Exact cause of the displayed error

`create_update_settings_group(...)` accepts `service=None`.

When the user clicks **Check for updates** and `service is None`, the UI deliberately returns:

`UpdateDiscoveryResult(status="channel-unavailable", detail="no structured update repository is configured")`

This is exactly the installed-user message that was observed.

`build_window(...)` in `app_v11.py` also defaults `update_service=None` and `install_service=None`.

The packaged entry path calls the normal app main without constructing/injecting a production update service. Therefore the installed `1.1.0-rc1` currently has update UI but **no production repository adapter wired into it**.

### Existing update machinery that should be reused

The repository already contains substantial R18 product code:

- `UpdateDiscoveryService` with channels `stable`, `beta`, `nightly`;
- TUF metadata verification for `root.json`, `timestamp.json`, `snapshot.json`, and `targets.json`;
- rollback/freeze/expiry checks;
- SHA-256 and declared-size target verification;
- staged verified update artifacts;
- explicit-confirmation installer handoff;
- persisted trusted discovery state.

The missing production bridge is chiefly:

1. a real network `UpdateTransport` for published metadata/targets;
2. a real packaged production trust anchor (not the synthetic acceptance root);
3. a stable public URL layout for update metadata and target installers;
4. application startup wiring that instantiates `UpdateDiscoveryService` + delivery/install service and injects them into `build_window(...)`.

### Critical security constraint

`src/kodepoia/update/bootstrap.py` intentionally ships only `trusted_root.synthetic.json` for acceptance and refuses to treat it as production trust unless there is an explicit synthetic opt-in. **Do not simply wire the synthetic root into public production updates.**

A real update service needs a separately governed production/beta trust anchor and metadata publication process.

---

## 5. Web-verified architecture constraints

### The Update Framework (TUF)

Official TUF documentation confirms that a client update repository uses four required top-level roles/metadata files:

- Root
- Targets
- Snapshot
- Timestamp

Targets metadata records target file hashes and sizes; Snapshot provides a consistent view; Timestamp helps clients detect stale/frozen metadata. This matches the security model already implemented in Kodepoia R18.

References:

- `https://theupdateframework.io/docs/metadata/`
- `https://theupdateframework.io/docs/overview/`
- `https://theupdateframework.io/docs/faq/`

### GitHub Releases

GitHub’s REST `Get the latest release` endpoint intentionally returns the latest **non-prerelease, non-draft** release. Therefore a beta/RC update channel such as the current `1.1.0-rc1` must **not** rely only on `/releases/latest` for discovery.

Reference:

- `https://docs.github.com/en/rest/releases/releases#get-the-latest-release`

GitHub Releases may be used as an installer payload transport/source, but TUF metadata should remain the authority for what an installed client is allowed to trust and install.

---

## 6. Desired post-R18 product outcome

This continuation is a **post-R18 hotfix/evolution track**, not an extension of R18.

Do not invent or start `R18.12`.

Before implementation, create a new explicit plan/roadmap authority for the post-R18 work. Its formal phase number/name may be chosen in the next conversation, but it must preserve the frozen R18 boundary.

Recommended work breakdown:

### POST-R18-A — Language switching hardening

Goal: French ↔ English selection is reliable and user-obvious.

Implementation direction:

- create one authoritative application preference store;
- preserve saved locale without clobbering unrelated settings;
- define precedence explicitly: user-saved preference should normally beat OS detection; environment override should be developer/diagnostic-only or clearly documented;
- add `apply_locale(...)` / window retranslation or a controlled application restart action after changing the language;
- ensure all v1.1 surfaces use `V11Translator` or a compatible translation source;
- add packaged Windows tests for persistence and switch-back.

Acceptance veto: selecting English and restarting still shows French.

### POST-R18-B — Production/beta update repository bootstrap

Goal: provide a real structured repository reachable by installed clients.

Required design decisions:

- choose canonical HTTPS metadata base URL;
- choose target/payload URL strategy (GitHub Release assets are acceptable as payload storage);
- create **real** TUF trust metadata for the beta/release channel;
- establish production/beta public root material packaged into Kodepoia;
- define key custody/rotation and metadata expiry policy;
- publish channel target path(s) consistent with existing code, e.g.
  `channels/beta/windows-x86_64/<version>/<source_sha>/KodepoiaSetup.exe`;
- ensure metadata contains SHA-256, size, source SHA, channel and release notes/status fields.

Security rule: private signing keys must never be embedded in the application or repository working tree.

Possible manual intervention: secure creation/custody of real TUF signing keys may require explicit user action. If that becomes necessary, stop and provide exact commands/actions before continuing any later subdivision.

### POST-R18-C — Real network UpdateTransport and startup wiring

Goal: remove `service=None` in the packaged app.

Implementation direction:

- implement bounded HTTPS transport with timeouts and deterministic error mapping;
- fetch only allowlisted metadata names and authorized target paths;
- instantiate `UpdateDiscoveryService` with real `PackagedRootPin` and network transport;
- instantiate verified delivery/install service;
- inject both services into `build_window(...)` from the packaged entry path;
- keep startup independent of network availability;
- preserve offline/error UX rather than crashing.

Acceptance veto: installed app still displays `no structured update repository is configured`.

### POST-R18-D — Seamless in-app Windows update UX

Goal: the user does not manually reinstall Kodepoia.

First acceptable implementation:

1. user clicks **Check for updates**;
2. Kodepoia fetches/verifies trusted metadata;
3. if a newer authorized build exists, UI displays version, channel, size and notes;
4. user clicks **Download and verify**;
5. installer is staged under Kodepoia-managed update storage;
6. TUF/hash/size checks must pass;
7. user explicitly confirms **Install update**;
8. Kodepoia launches the verified Inno Setup installer in upgrade/silent mode, exits the running app, preserves settings/projects, updates installed files, and relaunches Kodepoia when safe;
9. UI/report records success/failure.

This may technically use a full installer payload internally, but the user experience is an in-program update rather than a manual reinstall.

Later optimization: delta/binary patching may be evaluated only after the secure full-installer updater is reliable.

### POST-R18-E — Release automation and integrated acceptance

Goal: future releases automatically become discoverable by installed Kodepoia clients.

Required acceptance matrix:

- older installed RC detects newer beta RC;
- stable does not accidentally consume beta/nightly;
- beta can consume authorized RC/beta target;
- tampered installer rejected;
- wrong SHA/size rejected;
- expired metadata rejected;
- rollback/freeze rejected;
- withdrawn release rejected;
- offline state is non-destructive;
- update is never installed without explicit user confirmation;
- application restarts on updated version;
- projects/user settings remain intact;
- French/English selection remains intact through update;
- clean uninstall still succeeds after update.

---

## 7. Versioning recommendation for the first corrective release

Do not mutate the already published `v1.1.0-rc1` asset in place as the normal update path.

Prefer a new prerelease identity after the fixes, for example `1.1.0-rc2`, subject to explicit roadmap/version authority in the next phase.

The installed `rc1` cannot fully self-update until a build containing the real update-service wiring exists. Therefore the first transition may require one final manual installation of the corrective build; after that, subsequent builds should update in-program. If a bootstrap helper/updater can safely be added to rc1 without mutating the published immutable expectation, document that separately rather than silently replacing rc1.

---

## 8. Known current user environment state

User report as of 2026-09-07:

- Windows installer completed successfully.
- Installed app launches successfully.
- UI currently appears in French.
- Selecting English does not visibly switch the current UI.
- Update check reports the exact structured-repository error above.

No claim is made yet about whether English persists after a full application restart; verify this first in the next troubleshooting/implementation session.

---

## 9. Files likely to change in the next implementation phase

Expected core files (not exhaustive):

- `src/kodepoia/kodestudio/app_v11.py`
- `src/kodepoia/kodestudio/v11_localization.py`
- `src/kodepoia/kodestudio/update_settings.py`
- `src/kodepoia/kodestudio/app_v11_entry.py`
- `src/kodepoia/update/discovery.py`
- `src/kodepoia/update/delivery.py`
- `src/kodepoia/update/trust.py`
- new production network transport/bootstrap modules as needed
- packaging/release workflows
- focused language/update tests
- Windows installer acceptance
- continuity/roadmap/README for the new post-R18 phase

Do not modify the frozen R18 completion semantics to pretend these post-install discoveries were part of an unfinished R18.

---

## 10. Resume protocol for a new ChatGPT conversation

Upload or point ChatGPT to this file and use a request equivalent to:

> `@Recherche sur le Web Continue Kodepoia à partir de KODEPOIA_CONTINUITY_V2_POST_R18.md. R18 est gelée COMPLETE + NORMALIZED. Commence par vérifier main et la Release actuels, puis planifie et exécute le nouveau track post-R18 pour corriger le changement Français/English et rendre les mises à jour Kodepoia réellement utilisables depuis l'application. Ne crée pas R18.12. Procède subdivision par subdivision avec branche dédiée, tests exact-head, merge et continuité. Si et seulement si une intervention manuelle de ma part devient nécessaire, arrête les subdivisions suivantes et donne-moi exactement les actions à effectuer.`

On reprise, ChatGPT must first verify the current `main`, current public release(s), open PRs, and whether this continuity v2 itself has been superseded by a newer continuity record.

---

## 11. Authority / safety rules for continuation

- R18 remains frozen and complete.
- No `R18.12`.
- Never silently replace an already published release asset to simulate an update.
- Never embed private TUF/AuthentiCode keys in source, package, logs, artifacts, or continuity files.
- Network update checks must never gate Kodepoia startup.
- No update installation without explicit user confirmation.
- Exact-head CI evidence remains required before merges.
- If secure TUF key creation/custody, Authenticode certificate use, repository secret configuration, or another genuinely external credential action is required, treat it as a manual intervention boundary and provide exact instructions before continuing later subdivisions.

---

## 12. Continuity creation record

- Created post-R18 after real installation feedback on 2026-09-07.
- Base `main`: `c0896c2783e76e49fda1744171c6523ce1293a9f`.
- This file is documentary continuity only; it does not claim the language or updater defects are fixed.
