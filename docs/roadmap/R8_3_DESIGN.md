# R8.3 — Source/derived lineage + reproducible transform cache/rebuild — Design

R8.3 adds the AssetPipeline core without introducing ComfyUI, Blender, audio/TTS generation or arbitrary command execution.

- A `TransformRecipe` has a stable transform ID, schema version, JSON parameters, output kind, determinism state and optional seed.
- A `ToolIdentity` and trusted environment identity participate in the cache key together with exact input revision IDs/digests.
- Callers select only a registered transform ID and typed parameters. Adapters own their implementation; no caller/model executable, argv, cwd or environment surface is exposed.
- Authoritative CI uses `fixture.text-uppercase.v1`, a pure-Python deterministic transform. Future executable adapters must use the accepted ProcessSandbox + KillSwitch boundary with fixed templates.
- Inputs must be immutable READY revisions. Output executes in Vault staging, is confined to staging, SHA-256/length verified, promoted as a DERIVED revision and linked to exact inputs through lineage edges.
- Cache hits verify the cache record, revision identity and object bytes. Missing/stale/corrupt cache state never manufactures a hit.
- The service rejects a transform if the proposed output logical asset already appears in any input ancestor, preventing lineage cycles.
- Cancellation before promotion creates no READY derived revision.
