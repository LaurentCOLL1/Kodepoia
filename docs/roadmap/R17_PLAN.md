# R17 — Distribution & Guided Creation UX

Status: **IN_PROGRESS**

Normalized base: `11194ec5bbb6a986d0fa206517ad3759378a80cf` (R16 / v1.0 COMPLETE + NORMALIZED)

## Goal

Make Kodepoia/KodeStudio installable and approachable as an end-user Windows application while preserving the local-first, guarded architecture established by v1.0.

## Frozen R17 scope

1. **Windows end-user distribution**
   - Build a standalone `KodepoiaStudio.exe` that does not require a target user to install Python or run `pip`.
   - Build `KodepoiaSetup.exe` with an uninstall entry, Start Menu shortcut, optional/default desktop shortcut, and post-install launch.
   - Add a Windows CI workflow that builds and smoke-checks the installer artifact.
   - Do not claim production signing unless a real signing identity is explicitly provided and exercised.

2. **French user experience**
   - Add French as a first-class KodeStudio locale for the shell, onboarding, project creation and Chat/Vision workflow.
   - Preserve English and pseudo-locale behavior used by existing tests.
   - Fall back safely to English where a legacy specialist panel has no French catalog yet; no fabricated translation claim.

3. **Guided project creation**
   - Preserve existing `QLineEdit` compatibility for `genres` and `graphics_style` because R13/R14 layers read `.text()`.
   - Add curated selectable presets that populate those fields instead of replacing their public widget contract.
   - Include beginner guidance for project type, genre, visual style, platform/input choices, scope and performance intent.
   - Genre guidance includes RPG, Simulation, Sex/Adult, Strategy, Action and other common categories without forcing any selection.

4. **Functional local Chat / Vision assistant**
   - Replace the Chat placeholder in the v1.1 shell with a working page.
   - Use existing local `OllamaClient` when a local model is available and selected.
   - Support structured generation/update of Summary, Goals, Success metrics, Constraints, MVP, Out of scope, Requirements and Acceptance criteria.
   - Ask targeted clarification questions when the user's intent is incomplete or changes materially.
   - Provide a deterministic guided fallback when Ollama is unavailable so a beginner is never blocked by an empty Chat page.
   - Persist draft vision locally under project metadata; no cloud dependency is introduced.

5. **Onboarding and usability**
   - Detect/use French on a French system while retaining an explicit locale override.
   - Guide users step by step and expose meaningful next actions rather than blank placeholder pages for Chat/project initiation.
   - Update README with current v1.0 status, end-user installation, developer installation, French/local AI notes and the v1.1/R17 scope.

## Acceptance

R17 is acceptable only when all of the following are demonstrated on the same technical source:

- pure-Python tests cover Vision structuring, clarification fallback, persistence and locale selection;
- Qt/UI smoke covers the v1.1 shell, real Chat page and guided project controls without breaking the accepted R12–R14 wizard contract;
- packaging static tests validate installer name, shortcuts, uninstallability and non-admin install intent;
- Windows packaging CI produces an artifact containing exactly a `KodepoiaSetup.exe` installer and verifies it exists/non-empty;
- R0 Repository Guard, full Python Core and KodeStudio UI smoke are green on the accepted source;
- no production signing/publication claim is made unless separately evidenced.

## Out of scope

- Reopening or rewriting the frozen v1.0/R16 roadmap history.
- Automatic public/store release.
- Production code signing without explicit credentials and evidence.
- Bundling third-party local models or Ollama binaries into KodepoiaSetup without a separate governed licensing/provenance decision.
- Replacing existing guarded backend, research, media, mobile or tuning architecture.

## Manual state

Core R17 implementation: **NONE planned**.

Optional production signing / public publication: **CONDITIONAL / NOT TRIGGERED**.
