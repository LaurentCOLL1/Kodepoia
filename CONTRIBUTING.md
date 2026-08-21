# Contributing to Kodepoia

Kodepoia is currently a private development project. These rules apply to human and agent contributions.

## Before changing code

1. Read the frozen architecture and roadmap.
2. Read relevant ADRs and Project DNA when working inside a Kodepoia-managed project.
3. Work on a branch/worktree; do not develop directly on `main`.
4. Keep changes scoped and reversible.

## Branch names

- `feature/<name>`
- `fix/<name>`
- `refactor/<name>`
- `research/<name>`
- `release/<version>`
- `agent/<task-id>`

## Architecture changes

The v1.0 foundations are frozen. Any foundation change requires a new ADR using `docs/architecture/adr/0000-template.md`.

## Required validation

Before merge, run:

```powershell
./scripts/check_repo.ps1
```

Later phases add build, unit, integration, regression, visual, performance, security and platform-specific gates.

## Large files

Use Git LFS for binary asset types listed in `.gitattributes`. Do not commit AI model weights, checkpoints or local model caches; these belong to KodeModelRegistry.

## Secrets

No secret may be committed, embedded in examples, or passed to an LLM. See `SECURITY.md`.

## Commit messages

Prefer Conventional Commit-style prefixes such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` and optionally a phase scope such as `chore(r0):`.
