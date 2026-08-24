# R11.1 — Media/voice/cinematic contracts, identities + secure runtime boundaries

## Design

R11.1 adds only typed R11 domain roots and a finite media runtime boundary. It reuses the accepted `kodepoia.core.sandbox.ProcessSandbox`; it does not create a second subprocess layer and it does not launch external media software.

The durable contract vocabulary includes `AudioSourceIdentity`, `AudioQAReport`, `VoiceRuntimeIdentity`, `VoiceModelIdentity`, generic typed root references for later voice/cinematic/franchise contracts, and explicit R11 status semantics including `RIGHTS_BLOCKED`, `CONFLICTED` and `MIGRATION_REQUIRED`.

`MediaRuntimeBoundary` validates executable identity against configured roots and per-runtime executable-name allowlists, confines input/output paths, filters environment overrides, and compiles only Kodepoia-owned ffprobe/PCM argv templates. Raw shell text, arbitrary filter graphs, URLs, arbitrary TTS flags and arbitrary Godot scripts are not accepted.

R11.1 performs no real ffmpeg/TTS/Godot execution. Manual state is **NONE**.
