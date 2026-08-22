# R8.7 — Asset-aware Git/VCS integration — Candidate acceptance

**Status:** CANDIDATE / PENDING EXACT-HEAD CI  
**Manual intervention:** NONE

## Implemented scope

- Reuses `ProcessSandbox` and the existing R4 Git execution boundary; the product API exposes only fixed structured Git operations.
- Repository status returns exact HEAD, branch/detached state and typed tracked-worktree states including untracked, ignored and conflicted conditions.
- Machine parsing uses stable porcelain `-z` records; no human-formatted status parser is used.
- Binary diff metadata uses `--numstat`; binary files remain binary evidence and never receive fabricated line counts.
- Stage/unstage accepts only explicit workspace-confined paths, rejects `.git` metadata paths, snapshots the Git index through `SafeChangeManager`, and appends tamper-evident audit records.
- Git index discovery uses `git rev-parse --git-path index`, preserving managed worktree compatibility without assuming `.git` is a directory.
- Vault revision ↔ repository path/last-commit evidence binds working bytes to the exact Vault revision digest/length.
- No remote push, arbitrary Git subcommand, flags, refspec, config key or history rewrite is exposed.

## Acceptance gates

R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all succeed on one exact implementation head before merge. Post-merge normalization must complete before R8.8 begins.
