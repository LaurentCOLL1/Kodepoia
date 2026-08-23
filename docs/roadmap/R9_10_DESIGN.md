# R9.10 — CLI + KodeStudio ComfyUI/VRAM UX — Design

## Status and authority

This document records the already-accepted R9.10 implementation required by `docs/roadmap/R9_PLAN.md`.

- Frozen subdivision: **R9.10 — CLI + KodeStudio ComfyUI/VRAM UX**.
- Base normalized R9.9 `main`: `5831e958c45ac63f6d2bcfd7da0a7934330c7586`.
- Exact accepted implementation head: `dda09a1728ba63640f68a979af57d70f12b4c603`.
- Implementation PR: #123; merge `4372fa9067acf6aabf242f178be0d9f7ac041fc7`.
- Accepted post-merge normalization head: `7515b2bdec0d9eaec32820feb4563869f050be00`.
- Normalization PR: #124; merge `4df1217cde078812af6882b812f640310aa45b61`.
- Manual intervention mode: **NONE**.

This file is a documentation-hardening record created after the implementation and its continuity normalization were accepted. It does not redefine the frozen R9.10 scope or authorize any new runtime surface.

## Objective

Expose the accepted R9.1–R9.9 ComfyUI capabilities through one safe application façade and a non-blocking KodeStudio surface, while preserving the fixed loopback boundary, governed workflow catalog, persisted run evidence and R9.8 VRAM admission semantics.

The design deliberately avoids creating a second networking, process, workflow-execution or GPU-control architecture in the CLI or UI.

## Single governed façade

`kodepoia.comfyui.service.ComfyService` is the shared R9 façade for both CLI and KodeStudio.

Its construction composes the previously accepted services rather than duplicating them:

- fixed-loopback `ComfyUIClient`;
- capability snapshot inventory/store;
- accepted R9.9 `ProductionWorkflowPackCatalog`;
- governed model resolver and workflow validator;
- persisted execution/run store;
- lifecycle cancellation/free-memory service and audit store;
- typed VRAM telemetry adapter and GPU admission policy.

The service metadata root is constrained to `<project>/.kodepoia/comfyui`; an escaping resolved metadata path is rejected with `ComfyGovernanceError`.

`ComfyService.fork()` creates a worker-safe façade with a fresh client using the already-validated endpoint while reusing the immutable governed catalog. GUI workers therefore do not share mutable transport objects.

## Accepted service surface

The façade exposes only bounded, typed operations:

- `status()` — fixed-loopback protocol state plus persisted capability state;
- `inventory()` — capture/read typed capability inventory;
- `workflows()` — enumerate the accepted R9.9 production packs and compatibility;
- `validate()` — compatibility validation for one governed family;
- `run()` — instantiate and submit one accepted workflow pack from bounded scalar parameters;
- `run_status()` — read/reconcile one persisted Kodepoia run;
- `cancel()` — targeted cancellation for one persisted run;
- `vram()` — typed telemetry plus optional family admission decision;
- `free_memory()` — conservative accepted lifecycle cleanup request;
- `evidence()` — persisted run/revision/lifecycle/output/capability evidence.

`run()` does not accept a raw graph. It validates the selected production pack, validates bounded parameters, refreshes the capability snapshot, resolves the explicit checkpoint selection through the governed resolver, evaluates VRAM admission, instantiates the frozen workflow definition, persists the snapshot and run evidence, then submits through the accepted execution service.

If compatibility is not `COMPATIBLE`, or admission is not `ADMIT`, execution returns an explicit blocked/defer/reject state rather than bypassing validation.

Persisted run reconstruction verifies that the saved capability identity and reconstructed workflow-instance digest match the run manifest. Mismatches fail closed.

The known-run scan used by lifecycle evidence is bounded to at most 10,000 accepted persisted run files; exceeding the bound is a protocol error.

## CLI architecture

`kodepoia comfy` is a thin JSON-producing adapter over `ComfyService`. It exposes:

- `status`;
- `inventory`;
- `workflows`;
- `validate`;
- `run`;
- `run-status`;
- `cancel`;
- `vram`;
- `free-memory`;
- `evidence`.

The CLI does not accept an arbitrary endpoint, URL, route, workflow graph, executable, model installer, model downloader or custom-node installer.

Production workflow family values come from `ProductionWorkflowFamily`. Run parameters are typed by argparse and then revalidated by the production pack. VRAM reserve/headroom values are additionally bounded by the service to 0–65,536 MiB.

Machine-readable results are emitted as deterministic JSON-compatible structures. Governed/protocol/unavailable/value errors are converted to explicit `blocked` or `unavailable` results and non-zero exit status.

## KodeStudio architecture

`kodepoia.kodestudio.comfy_panel.create_comfy_page()` constructs a dedicated ComfyUI + VRAM page.

The panel imports `ComfyService` rather than the ComfyUI transport/client. Long-running operations execute in `QThreadPool` workers. Each worker calls `facade.fork()` when available, preventing shared client state and keeping the GUI thread free.

The panel exposes:

- connection/protocol status;
- capability snapshot state;
- explicit model-resolution state;
- VRAM free/total telemetry;
- admission decision;
- Ollama coexistence state;
- governed workflow family and explicit checkpoint selection;
- bounded prompt, negative prompt, dimensions, output count, seed, steps and CFG controls;
- validate/run/refresh/cancel/free-memory/evidence actions;
- persisted run state and progress;
- structured evidence details.

Run refresh is driven by a one-second Qt timer that starts a non-blocking service operation. Progress and terminal state come from the persisted/reconciled R9 run state, not UI-local guesses.

Cancel acts only on the page's current persisted `run_id`. Evidence retrieval likewise requires that exact run identifier.

## Accessibility and localization

The R9.10 controls are integrated with the existing KodeStudio accessibility contract through `mark_accessible`. Named interactive controls have explicit accessible names; descriptive controls requiring additional context have explicit descriptions.

The recovered implementation defect around `comfyEvidenceView` was corrected by registering that `QPlainTextEdit` through the same accessibility contract rather than weakening the audit.

The pseudo-locale navigation expectation was updated for the additional ComfyUI page, and the dedicated R9.10 KodeStudio smoke is explicitly part of `.github/workflows/ui-smoke.yml`.

## Security and governance invariants

R9.10 preserves the following invariants:

- fixed accepted loopback ComfyUI boundary only;
- no arbitrary network endpoint or route console;
- no raw workflow JSON/graph execution entry point;
- no arbitrary executable/process surface;
- no custom-node installation automation;
- no model installation/download automation;
- only the four accepted R9.9 production workflow families;
- explicit model selection remains resolver-governed;
- VRAM admission cannot be bypassed by the CLI or UI;
- run lifecycle operations are tied to persisted run IDs;
- persisted capability/model/workflow identity mismatches fail closed;
- lower-level R9.1–R9.9 evidence remains authoritative and unmodified.

## Recovered defects during implementation

Two candidate heads were correctly rejected before acceptance:

1. `d62a688092ceec9a90b4d78fb4e8feac8fddd24e` — R0 passed, but UI Smoke and the Python Core embedded KodeStudio UI job found unregistered new accessibility controls and a stale pseudo-locale navigation expectation.
2. `4394401510e34f3050040ebedd8799b91e3c0f51` — the remaining failure was reduced to the unregistered `comfyEvidenceView` control; the UI workflow was also strengthened to execute the dedicated R9.10 panel smoke.

The gates were not weakened. The final implementation candidate `dda09a1728ba63640f68a979af57d70f12b4c603` fixed the defects and passed all required gates.

## Rollback

R9.10 is a façade/UI/CLI layer over accepted lower-level R9 services. Rolling it back removes the `ComfyService`-backed CLI and KodeStudio wiring while leaving R9.1–R9.9 contracts, stores, workflow packs, lifecycle behavior and hardware evidence intact.

## Documentation-hardening note

During preparation of R9.11 integrated acceptance, the repository was found to lack the planned `R9_10_DESIGN.md` and `R9_10_ACCEPTANCE.md` deliverables. This document closes that missing design record without changing production code.

R9.11 remains unauthorized until this documentation-hardening candidate passes exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke, is merged, and the resulting continuity-only normalization is also accepted and merged.
