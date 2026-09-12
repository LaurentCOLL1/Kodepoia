# Kodepoia 1.1.0-rc4 — TUF publication transition

This branch stages the exact public TUF metadata generation for `v1.1.0-rc4` after successful exact-source qualification, the fresh Root bootstrap fix, offline Targets authorization, and online Snapshot/Timestamp signing.

- Release source: `42e58b6b9c00d53c27e005020d6e99688958ee3a`
- Installer SHA-256: `54f751593b86d62eec50ea6852cc8683f0154d8645f9d98b84ccc6319ba058ee`
- Installer size: `37713467`
- Root: v2, unchanged
- Targets: v4, offline-signed, preserving rc3 and adding rc4
- Snapshot: v6, online-signed
- Timestamp: v6, online-signed
- Draft GitHub Release: `v1.1.0-rc4`, exact asset uploaded, not yet published

Publication order is intentionally fail-closed:

1. validate this exact metadata generation on the PR head;
2. publish the already-staged GitHub prerelease so the exact Targets payload URL exists;
3. re-verify the public asset digest/size and tag source;
4. merge this PR with expected-head protection so Targets/Snapshot/Timestamp become visible together;
5. validate fresh-root discovery and upgrade against the final published generation.

No private Root, Targets, Snapshot or Timestamp key material is stored in this branch.
