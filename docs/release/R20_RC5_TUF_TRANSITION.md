# Kodepoia 1.1.0-rc5 — TUF publication transition

This branch stages the exact public TUF metadata generation for `v1.1.0-rc5` after successful exact-source qualification, the Windows updater/package-data fix, selectable installation path correction, offline Targets authorization, and online Snapshot/Timestamp signing.

- Release source: `3f25eefa1a65cbbe9eb5822d6f68741675cf179b`
- Installer SHA-256: `30636a6ef5db4b3d171acc3817282595eff8ba724ff6c175329a10e8c5e8d42b`
- Installer size: `37712707`
- Root: v2, unchanged
- Targets: v5, offline-signed, preserving rc3 + rc4 and adding rc5; SHA-256 `d5c30941d6ae9ad21555db0e16ef6a1aa8f38a6d0049fdcebd29fc71d97a2757`; length `2392`
- Snapshot: v7, signed by the authorized Snapshot key; SHA-256 `66d7095dbe98ca5cd5d8de098d3537466aa92ec782db6b64c3282fce18a69df2`; length `469`; expires `2026-09-15T21:47:58Z`
- Timestamp: v7, signed by the authorized Timestamp key; SHA-256 `e91412f70ed161e9f26b3dd61721377af543d3ab837e6ee8d72d4c5ba64f8586`; length `470`; expires `2026-09-14T21:47:58Z`
- Online public signing package SHA-256: `9fb1666baf2dc44f6f2324bd059aa3ee1b64faab3a9cfa23a1cce5dad15cda00`
- Draft GitHub Release: `v1.1.0-rc5`, exact asset uploaded, not yet published

Publication remains fail-closed:

1. validate this exact metadata generation on the PR head;
2. publish the already-staged GitHub prerelease so the exact Targets payload URL exists;
3. re-verify the public asset digest/size and tag source;
4. merge the metadata PR with expected-head protection so Targets/Snapshot/Timestamp become visible together;
5. validate fresh-root discovery and upgrade against the final published generation.

No private Root, Targets, Snapshot or Timestamp key material is stored in this branch.
