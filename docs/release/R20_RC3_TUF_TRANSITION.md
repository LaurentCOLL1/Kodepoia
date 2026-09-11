# Kodepoia 1.1.0-rc3 — TUF publication transition

This branch stages the exact public TUF metadata generation for `v1.1.0-rc3` after successful exact-source qualification and offline Targets authorization.

- Release source: `a369cb4239de66089785ae96c28e854a23e31f99`
- Installer SHA-256: `8689f1649cd33e08fa93bd546c383ed0029afc0d1a86b4f5cb6c3f03bcece0c1`
- Installer size: `37708034`
- Root: v2, unchanged
- Targets: v3, offline-signed
- Snapshot: v5, online-signed
- Timestamp: v5, online-signed
- Draft GitHub Release: `v1.1.0-rc3`, exact asset uploaded, not yet published

Publication order is intentionally fail-closed:

1. validate this exact metadata generation on the PR head;
2. publish the already-staged GitHub prerelease so the exact Targets payload URL exists;
3. re-verify the public asset digest/size and tag source;
4. merge this PR with expected-head protection so Targets/Snapshot/Timestamp become visible together;
5. validate client discovery/upgrade against the final published generation.

No private Root, Targets, Snapshot or Timestamp key material is stored in this branch.
