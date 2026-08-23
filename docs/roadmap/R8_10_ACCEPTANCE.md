# R8.10 — CLI + KodeStudio Vault/Asset/VCS UX — Acceptance

**Status:** ACCEPTED / PENDING MERGE  
**Manual intervention:** NONE

## Accepted implementation candidate

- Exact accepted implementation head: `6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22`.
- Base normalized R8.9 main: `8ca2eec6192b3d82495309b1c5bc2e6e8e49132a`.
- PR: #99.
- Merge SHA: PENDING.

No implementation code is accepted from a later SHA unless the complete R0/Python/UI gate set is rerun on that later SHA.

## Authoritative automated CI on the exact implementation head

- R0 Repository Guard #1083 / `32614391934`: SUCCESS Ubuntu + Windows.
- Python Core #1057 / `32614392022`: SUCCESS 5/5.
- Ubuntu authoritative suite: `571 passed / 6 skipped / 46 warnings`.
- Package build/evidence: SUCCESS on Ubuntu and Windows inside Python Core #1057.
- KodeStudio UI Smoke #1024 / `32614391930`: SUCCESS.
- Python Core's integrated Windows KodeStudio smoke: SUCCESS.

R8.10 manual intervention is `NONE`; no hardware-local, credential-bearing or external-provider acceptance step is required.

## Accepted architecture and behavior

### One façade for CLI and KodeStudio

`AssetService` is the single R8.10 application façade. It composes the accepted Vault/store, search, duplicate, R6 governance, VCS and Git LFS services. The root CLI and KodeStudio call this façade; the Qt Vault panel does not implement a second Git/LFS/process/socket/secret path.

Accepted service operations include status/doctor, ingest, list/show/search, duplicate evidence, lineage, rebuild, materialization, deletion plan + confirmed deletion, governed export plan + confirmed export, VCS status, LFS diagnostics and revision repository evidence.

### Conservative governance remains authoritative

- Missing license evidence remains `NOASSERTION`/unknown and blocks export.
- R8.10 does not create a second license engine or infer legal conclusions.
- Search governance blockers remain excluded unless the user explicitly enables blocked-result visibility.
- Export still delegates to R8.6 governance/reuse preflight before any promoted target is written.

### Explicit destructive-operation confirmation

- Overwriting a materialized asset requires explicit confirmation.
- Vault revision deletion requires explicit confirmation and has a separately inspectable deletion plan.
- Project asset export requires explicit confirmation in addition to governance/reuse approval.
- Duplicate detection remains evidence-only; there is no destructive auto-merge.

### KodeStudio Vault UX

The accepted KodeStudio page exposes:

- Vault/VCS/LFS health;
- text search and kind/role/reuse filters;
- explicit include-blocked control;
- read-only asset/revision results and details;
- license warning state;
- duplicate inspection;
- rebuild action;
- selected-revision VCS/LFS evidence;
- upstream/downstream lineage;
- background operation state, visible budget/progress and cancellation.

### Worker and database isolation

Potentially expensive work uses `QThreadPool`/`QRunnable`. Each worker calls `AssetService.fork()` and obtains independent SQLite-backed Vault/search connections; the UI-owned service connection is not reused across worker threads. Completion/error data returns through Qt signals and widget mutation remains on the GUI side.

`AssetCancellationToken` provides cooperative thread-safe cancellation checkpoints. Cancelled work does not become READY and does not bypass underlying transactional/governance/integrity behavior.

### Accessibility/localization regression behavior

R8.10 extends, rather than bypasses, the accepted R6.5 accessibility and R6.6 localization contracts:

- new interactive Vault controls are registered with stable accessibility IDs/names/descriptions;
- pseudo-localized navigation now explicitly expects the seventh `Vault` item;
- both UI workflows include the R8.10 Vault smoke alongside existing accessibility/localization/Research regressions.

## Rejected/intermediate candidates

The first PR candidate `7bb5c9b95b191d7dc97ca76ca81f175d5f424730` was **not accepted**. Python Ubuntu passed, but the Windows KodeStudio smoke correctly reported three regressions:

1. new Vault controls were not yet registered in the accessibility contract;
2. the pseudo-localization test still expected exactly six navigation items;
3. the R7.10 Research accessibility audit therefore also saw the unregistered Vault controls on the main surface.

The gates were not weakened. R8.10 registered the new controls, updated the navigation contract to seven entries, and added the R8.10 UI smoke to both UI workflows.

Candidate `66f9e1c1d3fb528ed3fc2fedc3934d342c20fb93` then passed R0/Python/UI, but was deliberately not frozen because the implementation was further completed with visible operation budget/progress and explicit lineage UX.

The final implementation candidate `6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22` reran the entire gate set and passed.

## External semantic cross-check

Qt documents `QThreadPool`/`QRunnable` as the standard mechanism for running queued work on reusable threads rather than the GUI thread. Qt SQL documentation also requires a database connection to be used only from the thread that created it unless explicitly moved. R8.10's worker-local `AssetService.fork()` design follows these constraints instead of sharing the UI service's database connections across threads.

## Security result

R8.10 introduces no model-supplied arbitrary executable, argv, cwd, environment, Git command/refspec/config key, remote URL/host, raw socket or secret surface. VCS/LFS behavior continues to use the accepted structured R8.7/R8.8 boundaries; asset paths remain project/Vault confined; license/export policy remains R8.6/R6-governed.

## Documentation gate still required before merge

This acceptance file and `docs/roadmap/R8_10_DESIGN.md` are documentation-only additions after the exact implementation head above. `docs/continuity/KODEPOIA_CONTINUITY.md` must be synchronized in the same work cycle. The resulting final documentation head must then pass:

- R0 Repository Guard;
- full Python Core;
- KodeStudio UI Smoke.

Only after all three succeed on that exact documentation head may PR #99 be merged. The post-merge normalization must then record the PR #99 merge SHA and mark R8.10 COMPLETE before R8.11 implementation begins.

## Result

R8.10 implementation is **ACCEPTED / PENDING MERGE** on exact head `6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22`. R8.11 remains blocked until the documentation gate, PR #99 merge and R8.10 post-merge normalization are complete.