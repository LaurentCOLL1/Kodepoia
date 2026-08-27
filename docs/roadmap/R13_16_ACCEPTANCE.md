# R13.16 Acceptance — CLI + KodeStudio Mobile/DeviceLab/Release workspace

**Subdivision:** R13.16  
**Status:** CANDIDATE / NOT YET ACCEPTED  
**Manual:** NONE

## Frozen acceptance claim

R13.16 is accepted only when the exact candidate head proves that Kodepoia exposes the already accepted R13 mobile/release model through structured CLI and KodeStudio surfaces without introducing raw tooling, credential or editable-evidence authority.

## Required functional checks

1. `kodepoia r13` registers exactly the structured intents `status`, `scaffold`, `build`, `test`, `package`, `device`, `compliance`, `release`.
2. CLI input is limited to the project root for this orchestration surface; raw executable, argv, Gradle/Xcode, device-shell and store-token flags are rejected by parsing.
3. Valid mobile Project DNA produces passive `READY` metadata and a capability matrix.
4. Missing/invalid/non-mobile Project DNA produces explicit `BLOCKED` state.
5. Passive status invokes no execution backend and has no external-process/network authority.
6. A passive evidence file reporting `status=pass` remains read-only reported data and cannot change passive workspace state into `PASS`.
7. Execution without a governed backend returns `BLOCKED` / `EXECUTION_BACKEND_UNAVAILABLE` rather than falling back to shell/tool discovery.
8. Active global KillSwitch returns `CANCELLED` before any executor call.
9. An injected governed executor receives only bounded Project-DNA-derived execution context and may return a terminal receipt.
10. KodeStudio exposes separate Refresh and execution actions, a read-only evidence/capability viewer, explicit blockers and protected-operation cancellation.
11. R13 workspace localization has source English plus pseudo-localization and normal fallback behavior.
12. Interactive R13 KodeStudio controls carry accessible names/descriptions.

## Focused automated tests

`tests/test_mobile_r13_16_workspace.py` covers:

- passive refresh/backend separation;
- evidence PASS non-escalation;
- backend-unavailable blocking;
- KillSwitch cancellation before executor dispatch;
- structured bounded execution context;
- missing/non-mobile DNA blocking;
- raw dangerous CLI option rejection;
- pseudo-localization/fallback behavior.

KodeStudio UI Smoke remains responsible for importing/constructing the complete window with the new R13 page under the repository UI environment and for detecting regressions in navigation/accessibility/pseudo-localized layout.

## Exact-head gates required for acceptance

The final technical candidate must pass on one exact SHA:

- **R0 Repository Guard** — SUCCESS;
- **Python Core** — SUCCESS, including full Ubuntu/Windows tests and package builds;
- **KodeStudio UI Smoke** — SUCCESS.

R13.16 introduces no new external Android/Apple/provider execution seam, so a new platform workflow is not required solely for this subdivision. If standard gates reveal an affected existing platform regression, the relevant existing R13 workflow must also be rerun and succeed before acceptance.

## Manual state

**NONE.** No physical device, Play Console/App Store Connect account, service credential, production signing material, Android SDK/Xcode installation on the user machine, paid provider quota or live publication action is needed for the frozen R13.16 core claim.

## End synchronization and merge rule

After an exact-head technical candidate passes all required gates:

1. update `R13_PLAN.md` and continuity in the same work cycle to mark R13.16 `COMPLETE` and R13.17 `PLANNED`;
2. record candidate/run authority in this acceptance file;
3. because documentation bytes changed, rerun fresh R0 + full Python Core + KodeStudio UI Smoke on the final end-synchronized head;
4. merge the implementation PR with `expected_head_sha=<final exact head>`;
5. create exactly one continuity-only normalization branch from the implementation merge;
6. verify its diff changes exactly `docs/continuity/KODEPOIA_CONTINUITY.md`;
7. pass fresh exact-head R0 + Python Core + UI Smoke and merge normalization with `expected_head_sha`;
8. only the resulting normalized `main` authorizes R13.17.

No PASS evidence or completion SHA is recorded here before those facts exist.
