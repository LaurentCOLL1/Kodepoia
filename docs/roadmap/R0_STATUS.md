# R0 — Repository & Governance — Status

**Phase:** R0  
**Status:** COMPLETE  
**Completed:** 2026-08-21

## Validation evidence

- Validation PR: **#1 — R0: finalize repository governance and bootstrap validation**.
- PR #1 merged successfully after checks.
- GitHub Actions run `32434382890`:
  - `repository-bootstrap-ubuntu-latest`: **SUCCESS**;
  - `repository-bootstrap-windows-latest`: **SUCCESS**.
- Both jobs validated checkout, Python bootstrap, pinned dependencies, Git LFS availability and `scripts/check_repo.py`.

## Delivered

- [x] Private development repository `LaurentCOLL1/Kodepoia`.
- [x] Frozen Architecture v1.0 stored in-repository.
- [x] Architecture decision register stored in-repository.
- [x] Roadmap R0–R16 stored in-repository.
- [x] LLM/conversation continuity document stored in-repository.
- [x] Machine-readable freeze manifest + JSON schema.
- [x] ADR template and architecture-change issue form.
- [x] README, CHANGELOG, SECURITY, CONTRIBUTING, Code of Conduct and private development licence.
- [x] Branch/worktree policy.
- [x] `main`, `develop` and `agent/*` workflow established.
- [x] Git LFS attributes for heavy/non-mergeable assets.
- [x] AI model weights/checkpoints excluded from Git by policy.
- [x] Secret/model-weight/large-file repository checker.
- [x] JSON and YAML syntax validation.
- [x] Cross-platform GitHub Actions bootstrap guard (Windows + Ubuntu).
- [x] Pull-request and issue templates.
- [x] CODEOWNERS.
- [x] Source/module skeleton including Protected Core, quality, tools, intelligence and model router/VRAM boundaries.
- [x] Local PowerShell repository-check entry point.

## Local validation command

```powershell
python -m pip install -r scripts/requirements-r0.txt
./scripts/check_repo.ps1
```

Expected result:

```text
Kodepoia R0 repository check: PASS
```

## GitHub repository settings

The repository policy requires `main` to remain releasable and recommends server-side branch protection/rulesets (block force push/delete and require checks/PR for collaborative work) when the account/settings surface permits it.

The current ChatGPT GitHub connector exposes repository contents, branches, PRs and Actions inspection but does **not** expose repository ruleset/branch-protection mutation. Enforceable R0 controls therefore include branch/worktree policy, PR workflow, cross-platform checks, CODEOWNERS and the local checker. KodeGuardian adds stronger local enforcement in R1.

## Security note

GitHub Secret Protection availability varies by account/plan for private repositories, so R0 deliberately does not depend solely on it. Local/CI checks reject known credential forms, forbidden secret-file names/extensions, AI model weights and oversized files outside the LFS policy.

## Next phase

**R1 — KodeStudio minimal + Protected Core**, beginning with KodeGuardian, KodePermissions, KodeAudit and KodeSafeChange.
