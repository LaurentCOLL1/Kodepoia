# R7.10 — CLI + KodeStudio Research UX — Acceptance

**Status: IN PROGRESS — do not mark COMPLETE before exact-head hosted gates succeed.**

## Scope

This acceptance covers the frozen R7.10 subdivision only: one shared Research service, CLI operations, KodeStudio Research UX, textual status/trust/freshness/provenance presentation, cancellation, cited/redacted export, accessibility/localization integration and explicit capability states.

## Acceptance invariants

- CLI and KodeStudio consume the same framework-independent `ResearchService`; no second trust, permission, provenance or status model is introduced.
- External research remains guarded/untrusted data. Rendering or exporting a result never promotes it to instructions, authority or validated/global experience.
- Interactive Web access is BLOCKED by default. Explicit network opt-in grants only `Capability.NETWORK` and still passes through `KodeGuardian` plus the accepted R7.3 Web policy/transport.
- No Qt widget opens sockets, reads secret values or launches arbitrary processes directly.
- Persisted GitHub/Community/YouTube evidence remains queryable; missing live-provider configuration is represented explicitly instead of being silently mapped to generic Web.
- Cancellation is checked before dispatch and before persistence/result promotion. A cancelled fetch cannot create a new artifact presented as READY.
- Query/show/cache/status/media-capability outputs use explicit READY/BLOCKED/UNAVAILABLE/UNKNOWN/STALE/CANCELLED semantics.
- Result views preserve source IDs, artifact/finding/citation IDs, locators, version, freshness, trust, suspicious flag and ResearchGuard indicators.
- Representative displayed/exported text is redacted through the existing research/Secrets redaction path.
- Exports are confined below `.kodepoia/research/exports/` using `WorkspaceBoundary`.
- KodeStudio Research operations run through a worker/thread-pool boundary and do not synchronously block the GUI event loop.
- Interactive controls are keyboard reachable, carry stable accessibility metadata, and all semantic states are available as text rather than color alone.
- Source/localization changes preserve the pseudo-localized Research navigation/control surface.
- Existing R7.7 media acceptance commands and R7.1–R7.9 persisted evidence remain compatible.

## Deliverables

- `src/kodepoia/intelligence/research/service.py`
- `src/kodepoia/intelligence/research/research_cli.py`
- `src/kodepoia/kodestudio/research_panel.py`
- `schemas/research-ux-result-v1.schema.json`
- `tests/test_r7_10_research_service.py`
- `tests/test_r7_10_research_cli.py`
- `tests/test_r7_10_research_ui.py`
- `docs/roadmap/R7_10_DESIGN.md`
- workflow coverage in `.github/workflows/python-core.yml` and `.github/workflows/ui-smoke.yml`

## Hosted acceptance

Required exact-head workflows:

- R0 Repository Guard — **PENDING**
- Python Core (all required jobs) — **PENDING**
- KodeStudio UI Smoke — **PENDING**

Authoritative suite count, run IDs and accepted implementation head will be written only after the exact final head is green.

## Manual intervention

**NONE.**

## Completion rule

R7.10 remains IN PROGRESS until every required hosted gate succeeds on the exact final implementation head and this acceptance is normalized with immutable evidence. Only after the R7.10 normalization merge may R7.11 begin.
