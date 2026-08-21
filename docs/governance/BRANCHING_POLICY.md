# Branching and Merge Policy

## Goals

- Keep `main` releasable.
- Isolate human and agent changes.
- Ensure every non-trivial change is reviewable and reversible.
- Make validation status visible before merge.

## Long-lived branches

- `main`: frozen/releasable integration line.
- `develop`: integration branch for larger multi-step development when useful.

## Short-lived branches

- `feature/*`
- `fix/*`
- `refactor/*`
- `research/*`
- `release/*`
- `agent/*`

## Agent rule

Kodepoia agents must not directly develop on `main`. A task creates or uses a dedicated branch/worktree. High-risk changes require a pre-change snapshot/dry-run and KodeGuardian approval according to policy.

## Merge gate

At minimum during R0:
- repository bootstrap check passes;
- no secret or forbidden model weight is introduced;
- large binary policy passes;
- architecture foundation changes include an ADR.

Later phases add build/tests/security/performance/visual gates.

## GitHub repository settings target

When supported by the account/plan/settings interface, configure `main` with:
- block force pushes;
- block deletion;
- require pull request before merge for collaborative work;
- require bootstrap/status checks;
- require conversation resolution where appropriate.

Rulesets/settings are platform controls and are not a substitute for local KodeGuardian policies.
