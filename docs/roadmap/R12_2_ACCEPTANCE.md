# Kodepoia — R12.2 Acceptance

**Subdivision:** R12.2 — Project DNA/KodeProduct desktop profiles + Project Wizard target selection  
**Manual intervention:** NONE  
**Acceptance state:** PENDING EXACT-HEAD GATES

## Required behavior

- legacy schema-v1 Project DNA without `desktop` loads and re-serializes without adding the field;
- new Wizard-created `desktop_app` DNA contains explicit framework, architecture, package, persistence, IPC and update intent;
- non-desktop Project DNA cannot carry a desktop profile;
- impossible target/framework/package combinations fail closed;
- game-only fields are not propagated into new desktop DNA;
- KodeProduct receives deterministic desktop constraints and the reserved `DESKTOP-TARGET` P0 requirement;
- KodeStudio uses the existing Project Wizard dialog, exposes accessible Desktop controls, applies Windows-first defaults, disables non-desktop targets and produces Project DNA/Product files through the existing `ProjectInitializer`;
- no source scaffold, tool restore, SDK install, build or external process occurs in R12.2.

## Automated evidence

`tests/test_r12_2_desktop_project_wizard.py` covers legacy semantic round trip, explicit profile construction, impossible combinations, KodeProduct mapping and offscreen KodeStudio creation of a real `.kodepoia/project.yaml` + product file.

Required exact-head gates:

1. R0 Repository Guard — SUCCESS;
2. full Python Core — SUCCESS on Ubuntu and Windows including package builds and internal KodeStudio smoke;
3. KodeStudio UI Smoke — SUCCESS.

After the first accepted candidate, its SHA/run IDs are recorded in continuity. Because that changes bytes, the final documentation head is re-gated before expected-SHA merge.

## Manual gate

`NONE`. R12.2 only records intent and exercises KodeStudio/Python contracts; it makes no authoritative claim about an installed WPF/WinUI/Avalonia/Qt/Tauri runtime.

## Closure

After final exact-head gates, merge the implementation PR with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization with the same exact-head triplet. Only the normalization merge authorizes R12.3.
