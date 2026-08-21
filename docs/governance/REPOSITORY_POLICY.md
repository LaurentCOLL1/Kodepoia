# Repository Policy

## Source of truth

The Git repository is the source of truth for Kodepoia code, text configuration, schemas, decisions and reproducible build logic.

## What belongs in Git

- source code;
- tests;
- schemas;
- non-secret configs/templates;
- ADRs and architecture;
- build/release scripts;
- small mergeable assets.

## What belongs in Git LFS

Heavy, non-mergeable assets listed in `.gitattributes`, including Blender sources, large 3D binaries, lossless audio and video masters.

## What does not belong in the repository

- AI model weights/checkpoints/caches;
- credentials or keys;
- local package caches;
- generated build directories;
- temporary diagnostic dumps unless deliberately attached as a controlled artifact.

## Reproducibility

Derived assets should eventually be rebuildable by KodeAssetPipeline from source assets plus versioned recipes. Model dependencies should be identified by source, version and hash through KodeModelRegistry rather than committed as weights.
