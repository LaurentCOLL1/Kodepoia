# R11.9 — Godot 4.7 cinematic assembly, movie capture + A/V sync

## Objective

Prove that accepted R11.8 cinematic semantics can cross the existing R5/KodeGodot boundary into a bounded real Godot 4.7 Movie Maker capture, then be validated as an identity-bound audio/video artifact without adding arbitrary script, argv, project or encoder surfaces.

## Authority boundaries

- R11.8 remains authoritative for `ShotDefinition`, `SequenceTimeline`, exact frame timebase and event/reference identities.
- R11.7/R10 remain authoritative for facial semantic identities; R11.9 does not mutate topology or rig semantics.
- R5/KodeGodot remains authoritative for actual Godot process execution. R11.9 reuses `GodotRuntime.capture_movie()` and its `ProcessSandbox` contract instead of introducing another launcher.
- R11.2-style media inspection governs post-capture facts. R11.9 adds a movie-specific fixed ffprobe query and verifier; no arbitrary ffprobe flags are accepted.

## Assembly intent

`GodotCinematicAssemblyIntent` is deliberately declarative. It contains only:

- sequence identity + digest;
- integer fixed FPS and total frame budget;
- typed track intents (`camera`, `body`, `facial`, `dialogue`, `music`, `sfx`, `foley`, `subtitle`, `event`);
- event identity, start frame, duration and governed reference identity;
- fixed command policy `r11.9.godot.capture.v1`.

No raw Godot path, GDScript text, property expression, method call, command line, environment variable, executable name or arbitrary payload is accepted from a cinematic/model input.

`build_godot_assembly_intent()` verifies the R11.8 shot digest, exact timebase, exact shot duration and total frame bounds before materialization. Fractional FPS timebases are rejected for this R11.9 capture path because the existing R5 movie contract uses an integer `--fixed-fps` argument.

## Real capture boundary

The existing accepted `GodotRuntime.capture_movie()` is the only production capture launcher. It validates the project/scene/output, writes below `.kodepoia/captures`, and compiles the fixed command shape:

`godot --path . --write-movie <governed AVI> --fixed-fps <bounded integer> --quit-after <bounded frame count> --scene <governed res:// scene>`

Movie capture intentionally does not add `--headless`: the R5 implementation already records that Movie Maker requires a real renderer. `ProcessSandbox` supplies the executable allowlist, bounded cwd, timeout and KillSwitch integration.

## Trusted synthetic local fixture

The REQUIRED acceptance never touches a private Godot project. The collector creates a temporary repository-defined fixture containing exactly:

- `project.godot` with 640×360 viewport and `gl_compatibility` renderer;
- `capture.tscn` with one camera, light, simple body mesh, simple face mesh and audio player;
- fixed trusted `capture.gd` that animates only those synthetic meshes;
- deterministic synthetic stereo 48 kHz tone WAV lasting exactly 90/30 = 3 seconds;
- canonical assembly-intent JSON.

The script is Kodepoia-authored fixture implementation, not model/user-supplied executable content. No network, plugins, imported personal assets, project copy, shell, `OS.execute()`, model download or external encoder installation is used.

## Frozen local capture profile

- 640×360.
- 30 FPS.
- 90 frames / expected 3.0 seconds.
- AVI output under temporary-project `.kodepoia/captures`.
- maximum output: 64 MiB.
- video duration/frame-count tolerance: 1 frame (+ 0.01 s parser allowance).
- A/V duration difference tolerance: 2 frames (+ 0.01 s parser allowance).
- exactly one video and one audio stream.
- audio sample rate must be 44.1 or 48 kHz and channels mono/stereo.

## Post-capture validation

The fixed ffprobe query requests only format duration/size and stream index/type/resolution/frame rates/frame count/duration/sample rate/channels. The verifier fails closed on:

- missing/extra audio or video streams;
- wrong resolution or FPS;
- malformed/non-finite duration;
- excessive frame or duration drift;
- excessive A/V duration mismatch;
- unexpected audio facts;
- empty/oversized output;
- digest mismatch/spoofed output assumptions.

The accepted evidence stores only privacy-minimized runtime identities, executable SHA-256 values, fixture hashes, assembly identity/digest, output digest and bounded media facts. Local filesystem paths are not evidence fields.

## Exact-head collector

`scripts/r11_9_local_acceptance.py` requires `--source-sha` and verifies it against the actual repository `.git/HEAD` before any runtime call. It requires explicit Godot and ffprobe executables, permits only expected executable basenames, performs no download/install, uses a temporary fixture directory, and deletes the capture with that temporary directory after facts/digests are recorded.

If Godot is unavailable/not 4.7, ffprobe is unavailable, the renderer/movie writer fails, the process times out/cancels, the output is absent/malformed, or A/V facts exceed policy, the collector returns FAIL evidence and a non-zero exit code. Failure is not manually overridden.

## Security / rollback

- No arbitrary argv or GDScript generation surface.
- No private project or personal recording.
- Network is not needed by the collector.
- No automatic runtime/plugin/codec install.
- Capture is temporary and bounded; rollback is deletion of derived temp/capture evidence only.
- R11.8 definitions and R5 contracts remain source of truth.

## External behavior relied upon

Godot Movie Maker documents `--write-movie`, forced/overridable fixed FPS and bounded `--quit-after` capture. It also warns that Ctrl+C/F8 can leave AVI/WAV outputs without valid duration metadata; R11.9 therefore accepts only the collector's clean bounded process result and ffprobe-validated output.
