# R17 — Distribution & Guided Creation UX

Status: **COMPLETE AT END-SYNC — PENDING EXACT-HEAD MERGE + PHASE NORMALIZATION**

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

## Technical acceptance evidence

- Immutable accepted technical source: `7ed0731c1aa3c94d8a5feb13a08ae7ad953a86c9`.
- R17 Windows Installer #8 / `33899936010`: **SUCCESS** on Windows Server 2025. Focused R17 packaging/UX tests: **11 passed**. Nuitka 4.2 built the complete standalone distribution and Inno Setup 6.7.1 produced `KodepoiaSetup.exe`.
- Installer identity: version `1.1.0-rc1`; `KodepoiaSetup.exe` SHA-256 `e1871a7f01a08685aadd993e3a51d8ecf01e5bcbdd52bb050652b5bcdf1f9cc2`; `production_signed=false`.
- Installer artifact: Actions artifact `9947822021`, name `KodepoiaSetup-Windows`, 33,444,079 bytes, ZIP digest `sha256:877d884568024b3653cbb725eea73e3c8a2fab7b6fdaed1f763bc26e81546f06`.
- End-user independence was exercised, not inferred: silent install succeeded; installed `KodepoiaStudio.exe` launched from a clean temporary working directory while developer `python.exe` and `pip.exe` were absent from `PATH` and `PYTHONHOME`/`PYTHONPATH` were cleared; packaged UI smoke returned success; silent uninstall succeeded; the installed executable was confirmed removed.
- Exact-source general gates: Temporary R17 Exact-Head Premerge Gates #6 / `33900785285` — R0 Repository Guard **SUCCESS** Ubuntu + Windows, full Python Core **SUCCESS** Ubuntu + Windows, and KodeStudio + R17 UI smoke **SUCCESS** Windows.
- Superseded diagnostic predecessor `4cd308200ec9fbdef6f15f660373962fee02d2b0` / installer run #7 `33895528885` is **NON-AUTHORITATIVE** for the final decision because its installed packaged smoke failed. Its failure was used only to harden diagnostics and isolation; its PASS fragments are not reused as final acceptance evidence.
- Diagnostic candidate `d703abf62321e9c8cbdde2cb1ceb9adf39035d42` and targeted run `33899782461` validated the diagnostic/clean-smoke contract before integration but are not the immutable final technical source.
- Core manual intervention: **NONE**. Production code signing and public/store publication remain **CONDITIONAL / NOT TRIGGERED**; no certificate, production signing identity, store credential or publication action was exercised.
- This END-sync is documentation-only relative to the immutable technical source. Its resulting exact END-head must pass fresh R17 Windows Installer + R0 + full Python Core + KodeStudio UI gates before the implementation/evidence PR may merge to `main`.

## Out of scope

- Reopening or rewriting the frozen v1.0/R16 roadmap history.
- Automatic public/store release.
- Production code signing without explicit credentials and evidence.
- Bundling third-party local models or Ollama binaries into KodepoiaSetup without a separate governed licensing/provenance decision.
- Replacing existing guarded backend, research, media, mobile or tuning architecture.

## Manual state

Core R17 implementation: **NONE planned**.

Optional production signing / public publication: **CONDITIONAL / NOT TRIGGERED**.
