# R8.10 — CLI + KodeStudio Vault/Asset/VCS UX — Design

## Frozen objective

Expose the accepted R8.1–R8.9 asset stack through one typed application façade shared by the command line and KodeStudio. The UX must preserve provenance, license/governance, duplicate/search/lineage and repository evidence, keep explicit unavailable/blocked states visible, and never create a second Git/LFS/process/network/secret implementation inside Qt.

## Single service boundary

`kodepoia.assets.service.AssetService` is the only R8.10 application façade. It composes the already accepted R8 services:

- `VaultStore` / `VaultBoundary` for canonical assets, revisions and project references;
- `AssetSearchIndex` for lexical/semantic discovery;
- `DuplicateDetector` for exact and supported near-duplicate evidence;
- `AssetGovernanceService` for R6-backed license/BOM/export policy;
- `AssetVcsService` for structured local Git evidence;
- `GitLfsService` for local Git LFS capability/tracking/object diagnostics.

CLI and KodeStudio call this façade rather than reaching directly into SQLite, Git, Git LFS, `ProcessSandbox`, `KodeSecrets` or arbitrary subprocess/network APIs.

The default Vault root is the confined project-local `.kodepoia/vault`. A previously accepted explicit Vault root may be injected by trusted application configuration. The façade continues to use `WorkspaceBoundary` for project paths and `VaultBoundary` for Vault paths.

## Typed state and conservative governance

R8.10 exposes explicit operation states `READY`, `BLOCKED`, `UNAVAILABLE` and `CANCELLED`. It never translates missing evidence into success.

If no license evidence is supplied, the façade uses the existing R8.6 governance service with a conservative policy whose unmatched/unknown state is not silently allowed. `NOASSERTION`/`NONE` remains visible as unknown and blocks governed export. R8.10 does not infer legal conclusions.

The façade provides typed summaries/details for:

- logical asset and exact revision identity;
- source/derived role, status, reuse scope and preservation state;
- content SHA-256 and exact length;
- provenance and project references;
- upstream lineage inputs and downstream derived outputs;
- license state/token;
- search score, lexical/semantic score, mode and embedding state;
- VCS and LFS evidence when a materialized project reference exists.

## CLI surface

The root CLI delegates `kodepoia asset …` to the R8.10 asset CLI. Supported operations are structured and bounded:

- `status`, `doctor`;
- `ingest`, `list`, `show`, `search`;
- `duplicates`, `lineage`, `rebuild`;
- `materialize`;
- `delete-plan`, `delete`;
- `export-plan`, `export`;
- `vcs-status`, `lfs-doctor`.

Mutation arguments remain typed and project/Vault confined. Destructive or externally materializing actions require explicit confirmation where the accepted underlying operation is destructive or overwriting:

- overwrite during materialization requires `confirmed=true`;
- revision deletion requires explicit confirmation after the deletion plan is inspectable;
- project export requires explicit confirmation and still runs the R8.6 governance/reuse preflight before any promoted target is written.

There is no arbitrary Git command, refspec, executable, argv, cwd, environment, URL, host or Git config surface.

## KodeStudio Vault page

KodeStudio adds one `Vault` navigation page backed by `AssetService` only. The page exposes:

- Vault/VCS/LFS health badges;
- text search plus exact kind/role/reuse filters;
- explicit opt-in visibility for governance-blocked search results;
- a read-only asset/revision table;
- read-only canonical details with license warning state;
- exact/near duplicate inspection;
- rebuild action;
- VCS/LFS repository evidence for the selected revision;
- upstream/downstream lineage view;
- operation status, progress/budget indicator and cooperative cancellation.

The page does not import or invoke Git/LFS/process/socket/secret implementations directly.

## Worker/threading model

Potentially expensive refresh/search/duplicate/rebuild/repository-evidence/lineage work is submitted through Qt `QThreadPool`/`QRunnable`, keeping the GUI thread free for interaction.

The UI-owned `AssetService` is not reused inside a worker. `AssetService.fork()` creates a worker-local façade with independent Vault/search SQLite connections. This avoids cross-thread database-connection reuse while preserving the same service contract.

Worker completion is reported through Qt signals. UI widgets are updated only from the receiving GUI thread. Workers are retained by the page for their lifetime and released when their `finished` signal is received.

## Cancellation and visible operation budget

`AssetCancellationToken` uses a thread-safe event and cooperative `require_active()` checkpoints. Search iteration, duplicate analysis, rebuild stages and materializing/export paths check cancellation at safe boundaries. Cancellation does not manufacture a READY result.

KodeStudio exposes the active operation and a bounded/visible operation budget/progress state. Cancellation is explicit and returns the UI to an inspectable state; it does not bypass underlying transaction, governance or integrity checks.

## Duplicate/search/lineage semantics

R8.10 preserves prior evidence semantics rather than reinterpreting them:

- exact duplicate groups and near-duplicate candidates are displayed as evidence; no automatic destructive merge is introduced;
- semantic search keeps lexical fallback and embedding state visible;
- governance-blocked records are excluded unless the user explicitly opts to include them;
- lineage exposes both the selected revision's recorded inputs and derived revisions that reference it as an input; source and derived roles remain distinct.

## VCS and Git LFS UX

Repository integration is diagnostic and structured:

- VCS status delegates to `AssetVcsService`;
- revision ↔ materialized-file evidence reports tracked state, working SHA-256/length match and last commit SHA when available;
- Git LFS capability, policy gaps and per-file diagnostics delegate to `GitLfsService`;
- missing Git/LFS capability or missing materialized references returns explicit `UNAVAILABLE` evidence rather than throwing an opaque UI failure.

R8.10 does not expose push/fetch/pull, merge/rebase, history rewrite, `git lfs migrate`, arbitrary LFS endpoints or credential handling.

## Accessibility and localization

All new interactive Vault controls are registered through the accepted KodeStudio accessibility contract with stable object names, explicit accessible names and descriptions where required. The main-navigation pseudo-localization test is extended for the seventh navigation item instead of weakening the localization gate.

The dedicated UI smoke includes the R8.10 Vault page and continues to run the R6.5 accessibility, R6.6 localization and R7.10 Research UI regressions.

## Security invariants

R8.10 preserves all frozen architecture boundaries:

- no arbitrary filesystem escape beyond accepted project/Vault boundaries;
- no Qt-side subprocess, raw Git/LFS, socket/network or secret API;
- no second license engine or policy bypass;
- no implicit network/model download for search;
- no destructive duplicate auto-merge;
- no export when governance/reuse blockers remain;
- no silent conversion of UNKNOWN/UNAVAILABLE/BLOCKED into READY;
- no cross-thread reuse of the UI service's SQLite connections.

No ADR is required because R8.10 composes accepted R8/R6/R4 boundaries without changing frozen foundations.

## Testing and acceptance evidence

R8.10 acceptance covers:

- single-façade CLI/UI behavior;
- unknown-license export blocking before target write;
- explicit overwrite/delete/export confirmation;
- duplicate evidence remains non-destructive;
- blocked search visibility remains opt-in;
- cancellation is observed before rebuild work proceeds;
- repository evidence degrades to explicit UNAVAILABLE states;
- Vault UI creation, filters, table, lineage, operation budget and cancellation controls;
- no direct Git/LFS/process/socket/secret import in the Vault panel;
- R6.5 accessibility and R6.6 pseudo-localization regressions;
- full Python Core and package-build regressions on Ubuntu and Windows.

## Rollback / recovery

R8.10 introduces an application façade, CLI wiring and Qt presentation only. Rollback removes the R8.10 CLI/service/page wiring and restores the prior navigation/accessibility expectation. Canonical Vault manifests, object bytes and accepted R8.1–R8.9 data remain valid because their schemas and storage semantics are not changed.

## Manual intervention

**NONE.** R8.10 requires no hardware-local or credential-bearing acceptance step. All required acceptance evidence is produced by repository CI on the exact implementation/documentation heads.