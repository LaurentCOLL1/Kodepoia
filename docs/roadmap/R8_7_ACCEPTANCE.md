# R8.7 — Asset-aware Git/VCS integration — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** NONE

## Accepted implementation

- Exact implementation head: `c52c54ae8b4c1eee386b4dbbdec945fa04afa0f3`.
- PR: #93.
- Merge SHA: `b90ddcb1b4823442a9e58c7a0c1444966c5bd8a9`.

## Authoritative CI on the exact head

- R0 Repository Guard #1061 / `32603884834`: SUCCESS.
- Python Core #1035 / `32603884762`: SUCCESS 5/5.
- Ubuntu authoritative suite: `552 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #1002 / `32603884719`: SUCCESS.

## Accepted scope

- Reuses `ProcessSandbox` and the existing R4 Git execution boundary; the product API exposes only fixed structured Git operations.
- Repository status returns exact HEAD, branch/detached state and typed tracked-worktree states including untracked, ignored and conflicted conditions.
- Machine parsing uses stable porcelain `-z` records; no human-formatted status parser is used.
- Binary diff metadata uses `--numstat`; binary files remain binary evidence and never receive fabricated line counts.
- Stage/unstage accepts only explicit workspace-confined paths, rejects `.git` metadata paths, snapshots the Git index through `SafeChangeManager`, and appends tamper-evident audit records.
- Git index discovery uses `git rev-parse --git-path index`, preserving managed worktree compatibility without assuming `.git` is a directory.
- Vault revision ↔ repository path/last-commit evidence binds working bytes to the exact Vault revision digest/length.
- No remote push, arbitrary Git subcommand, flags, refspec, config key or history rewrite is exposed.

## Manual gate outcome

R8.7 manual state is **NONE**. No user-side command, credentials or remote Git mutation was required for authoritative acceptance.
