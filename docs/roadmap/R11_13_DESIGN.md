# R11.13 — CLI + KodeStudio Audio/Voice/Cinematics/Franchise UX

## Base

Normalized `main`: `3ca78857de17280c758912d35705881f8d31c73a`.

## Design

R11.13 adds presentation/workflow bindings only. Accepted R11.1–R11.12 domain services remain authoritative; this subdivision does not create a second media runtime or persistence implementation.

### Structured CLI

`kodepoia r11` exposes the frozen capability groups:

- `audio`
- `cues`
- `voice`
- `synthesis`
- `alignment`
- `facial`
- `cinematics`
- `continuity`
- `franchise`
- `canon`
- `savebridge`

Every group provides `status` with stable JSON and explicit state/blocker/evidence semantics. `synthesis` and `cinematics` additionally expose read-only governed runtime/evidence status operations. The CLI deliberately exposes no raw argv, executable, ffmpeg filter graph, model path, raw script or migration-code option.

### Shared workspace model

`R11WorkspaceService` is a read-only presentation registry. It binds a capability group to its accepted subdivision, accepted evidence path(s), blocker list and high-level operation identifiers. Runtime state defaults to `NOT_PROBED`; R11.13 never manufactures a live-runtime claim by looking at preserved evidence.

R11.5 and R11.9 accepted local evidence is surfaced by repository-relative evidence identity only. Secrets, personal paths and raw runtime arguments are not persisted or emitted.

### KodeStudio

KodeStudio gains one intentional tenth navigation entry: **Media / Franchise**. The page uses the existing `QListWidget` + `QStackedWidget` application architecture and contains five tabs:

1. Audio
2. Voice
3. Cinematics
4. Franchise / Canon
5. Persistence

Each tab exposes read-only capability state, runtime state, accepted evidence and explicit blockers. There is no raw command editor, model-path editor, ffmpeg/Piper/Godot argument editor or free-form migration-code editor.

`Refresh R11 status` refreshes the accepted presentation state without launching an external runtime. `Cancel protected media operations` reuses the global R1 KillSwitch boundary; R11.13 does not invent a parallel cancellation mechanism.

### Accessibility and localization

All newly interactive R11 widgets use stable object names plus accessible names/descriptions. R11 owns a dedicated localizable source catalog and pseudo-locale so the existing R6 pseudo-localization/truncation acceptance can intentionally expand from 9 to 10 main navigation entries.

## Security boundaries

- no new subprocess execution;
- no arbitrary filesystem path input;
- no network access;
- no model download/install;
- no raw commands or scripts;
- existing KillSwitch is reused for cancellation;
- runtime availability remains explicit `NOT_PROBED` unless an accepted runtime adapter performs a governed probe elsewhere.

## Rollback

Revert the R11.13 CLI registration, presentation registry, KodeStudio workspace and localization/tests. R11.1–R11.12 data/evidence remains intact.
