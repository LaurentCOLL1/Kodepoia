# Kodepoia local model catalog

`models/` is the repository-local home for model payloads used by Kodepoia. The directory layout and manifests are versioned; large model payloads are local-only and are intentionally ignored by Git.

## Layout

- `registry/` — tracked model index.
- `llm/` — language models, with role-oriented subfolders such as `fast`, `core`, `coder`, `reviewer`, `vision` and `general`.
- `embeddings/` — embedding models.
- `rerankers/` — retrieval rerankers.
- `tts/` — text-to-speech models.
- `stt/` — speech-to-text models.
- `lipsync/` — alignment/phoneme/viseme models.
- `audio/` — other learned audio models.
- `vision/` — vision understanding models.
- `image-generation/` — image generation/editing models.
- `3d/` — learned 3D/geometry/material models.

Every installed payload must be described by a tracked `manifest.json` and referenced from `registry/models.json`. Payload paths are relative to this repository so the Kodepoia tree is portable as a unit.

## Git policy

Do not commit model weights or downloaded third-party model payloads. Git tracks only Kodepoia-owned manifests, metadata, documentation and schemas. `KodeModelRegistry` verifies local payload bytes against SHA-256 identities recorded in those manifests.

Explicit installation/download actions may place files here, but runtime collectors do not silently download models.
