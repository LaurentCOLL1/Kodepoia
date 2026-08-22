# R7.10 — CLI + KodeStudio Research UX — Acceptance

**Status: COMPLETE**

## Accepted implementation

- Accepted head: `cfd0f7ba02af04b456993f686827f10810b3a61a`
- PR: #78
- Merge commit: `963799042ee30723fd2856f54dad9dedde6ed225`
- Manual intervention: **NONE**

## Scope

This acceptance covers the frozen R7.10 subdivision only: one shared Research service, CLI operations, KodeStudio Research UX, textual status/trust/freshness/provenance presentation, cancellation, cited/redacted export, accessibility/localization integration and explicit capability states.

## Accepted invariants

- CLI and KodeStudio consume the same framework-independent `ResearchService`; no second trust, permission, provenance or status model exists.
- External research remains guarded/untrusted data. Rendering/export never promotes it to instructions, authority or validated/global experience.
- Interactive Web access is BLOCKED by default. Explicit opt-in grants only `Capability.NETWORK` and still passes through `KodeGuardian` plus accepted R7.3 Web policy/transport.
- No Qt widget opens sockets, reads secret values or launches arbitrary processes directly.
- Persisted GitHub/Community/YouTube evidence remains queryable; missing live-provider configuration is explicit rather than silently mapped to generic Web.
- Cancellation is checked before dispatch and before persistence/result promotion. A cancelled fetch cannot create a new artifact presented as READY.
- Query/show/cache/status/media-capability outputs preserve explicit READY/BLOCKED/UNAVAILABLE/UNKNOWN/STALE/CANCELLED semantics.
- Result views preserve source IDs, artifact/finding/citation IDs, locators, version, freshness, trust, suspicious flag and ResearchGuard indicators.
- Display/export text uses the existing research/Secrets redaction path; exports remain confined below `.kodepoia/research/exports/` through `WorkspaceBoundary`.
- KodeStudio Research work uses a worker/thread-pool boundary; the GUI event loop is not synchronously used for long research operations.
- Interactive controls are keyboard reachable, have stable accessibility metadata, and semantic states are textual rather than color-only.
- Pseudo-localization may legitimately expand the window/navigation; the acceptance invariant is absence of truncation, not a fixed 1100 px width.
- Existing R7.7 media commands and R7.1–R7.9 persisted evidence remain compatible.

## Deliverables

- `src/kodepoia/intelligence/research/service.py`
- `src/kodepoia/intelligence/research/research_cli.py`
- `src/kodepoia/kodestudio/research_panel.py`
- `schemas/research-ux-result-v1.schema.json`
- `tests/test_r7_10_research_service.py`
- `tests/test_r7_10_research_cli.py`
- `tests/test_r7_10_research_ui.py`
- `docs/roadmap/R7_10_DESIGN.md`
- R7.10 UI coverage in `.github/workflows/python-core.yml` and `.github/workflows/ui-smoke.yml`

## Exact-head hosted acceptance

All required workflows succeeded on accepted head `cfd0f7ba02af04b456993f686827f10810b3a61a`:

- R0 Repository Guard — **#1025 / `32598029034` — SUCCESS**
- Python Core — **#999 / `32598029045` — SUCCESS, 5/5 jobs**
- Authoritative Ubuntu suite — **494 passed / 5 skipped / 46 warnings**
- KodeStudio UI Smoke — **#966 / `32598029037` — SUCCESS**
- Embedded `kodestudio-ui-windows` job inside Python Core — **SUCCESS**

## Rejected candidates retained as evidence

No failed candidate is treated as accepted evidence.

- `93e4db5e206dcd28d8e4edd16195c4ba30d714e6`: Python logic passed, but the Qt smoke exposed two incorrect test assumptions: searching for untranslated literal `Research` inside pseudo-localized text, and using nonexistent `AccessibilityReport.blocked` instead of the accepted `blockers` contract.
- `46911628d720464a073fe9b4c269a36f2c8f4a18`: the corrected UI contract passed except an old pseudo-locale assertion required exact window width 1100 px while the new sixth navigation section correctly expanded it to 1170 px. The test was corrected to assert minimum baseline dimensions plus the existing no-truncation navigation bound.

These failures changed tests to reflect the existing accessibility/localization contracts; they did not weaken the R7.10 UX requirements or create false PASS evidence.

## Manual intervention

**NONE.** No live provider/account/network probe was required for R7.10; deterministic hosted evidence covers the frozen acceptance contract.

## Completion rule result

R7.10 is accepted on the exact head above. R7.11 becomes authorized only after the separate R7.10 normalization PR itself passes exact-head hosted gates and is merged to `main`.
