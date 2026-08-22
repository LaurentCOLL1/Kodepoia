# R8.3 — Source/derived lineage + reproducible transform cache/rebuild — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** NONE

## Accepted implementation

- Exact implementation head: `a1b0b6b4e07b15521acdd3a86dd963ebe4acc9c8`.
- PR: #87.
- Merge SHA: `ec83fba0e664387ec4abccf047721d1ab77d4a8e`.

## Authoritative CI on the exact head

- R0 Repository Guard #1047 / `32602634343`: SUCCESS.
- Python Core #1021 / `32602634319`: SUCCESS 5/5.
- Ubuntu authoritative suite: `532 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #988 / `32602634320`: SUCCESS.

## Accepted scope

Typed transform/tool/determinism contracts, registered adapters only, cache identity bound to exact input revisions/digests + recipe + tool + environment identity, source/derived lineage, cycle rejection, managed staging, verified promotion, deterministic cache hit/miss/corrupt semantics and KillSwitch cancellation safety. R8.3 did not introduce an arbitrary executable/argv/cwd/environment surface; the authoritative transform fixture is pure Python.
