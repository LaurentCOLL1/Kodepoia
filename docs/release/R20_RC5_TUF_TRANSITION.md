# Kodepoia 1.1.0-rc5 — TUF publication transition

This branch stages the exact public TUF metadata generation for `v1.1.0-rc5` after successful exact-source qualification, the Windows updater/package-data fix, selectable installation path correction, and offline Targets authorization.

- Release source: `3f25eefa1a65cbbe9eb5822d6f68741675cf179b`
- Installer SHA-256: `30636a6ef5db4b3d171acc3817282595eff8ba724ff6c175329a10e8c5e8d42b`
- Installer size: `37712707`
- Root: v2, unchanged
- Targets: v5, offline-signed, preserving rc3 + rc4 and adding rc5
- Snapshot: v7, pending online signing
- Timestamp: v7, pending online signing
- Draft GitHub Release: `v1.1.0-rc5`, exact asset uploaded, not yet published

Publication remains fail-closed. The release stays draft until the exact Targets v5 bytes are bound by signed Snapshot v7 and Timestamp v7, the resulting transition passes validation on the exact branch head, and the staged asset/tag source is revalidated before publication.

No private Root, Targets, Snapshot or Timestamp key material is stored in this branch.
