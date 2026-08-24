# R11.3 — Music/SFX/Foley cue system + loops/variants/spatialization packaging

## Design

R11.3 represents playback intent semantically and keeps asset identity in R8.

- `AudioCueDefinition` supports music, ambience, SFX, Foley, UI and dialogue-support categories with one-shot, loop, playlist or weighted playback.
- Variants carry only R8 revision IDs + exact SHA-256, and fail closed unless R11.2 QA is PASS/WARN and rights state is AVAILABLE.
- Deterministic preview/test selection hashes cue digest + explicit seed + occurrence. Runtime nondeterminism is an explicit opt-in flag and cannot be silently used by deterministic preview helpers.
- Loop regions, pre-roll/tail/crossfade, spatialization/attenuation, bus, priority, polyphony, cooldown and ducking intent are bounded typed values.
- `compile_godot_audio_intent` emits engine-neutral semantic data for the accepted R5 adapter boundary. It never emits raw `.tres`, Godot script text, filesystem paths or arbitrary resource syntax.
- No source asset is mutated or duplicated; packaging artifacts remain derived/rebuildable under R8 lineage.

Manual intervention: **NONE**. Hosted deterministic fixtures and R5/R8 contracts are authoritative; no playback listening test is required for R11.3 acceptance.
