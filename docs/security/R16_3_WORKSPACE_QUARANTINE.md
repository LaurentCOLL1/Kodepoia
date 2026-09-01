# R16.3 — Malicious repository/workspace quarantine and safe bootstrap

## Security contract

R16.3 treats a newly opened or materially changed repository as **quarantined data** until the exact
working-tree fingerprint has been explicitly approved. Opening, bounded scanning, reading, indexing and
parsing remain possible; mutation, process execution, installation and network-authority operations do not.

The preflight is deliberately read-only. It never runs Git, package managers, task runners, Godot editor
plugins, project scripts, shell files or repository-provided hooks. Risk evidence reports relative paths,
classifications and digests rather than repository file contents or discovered external destinations.

## Boundary rules

1. `WorkspaceBoundary` remains the canonical filesystem confinement authority and resolves paths before
   containment checks.
2. `WorkspacePreflight` walks without following directory symlinks and rejects external symlink targets with
   a critical veto.
3. Git hooks, task/build metadata, shell/batch/PowerShell files, binaries, Godot addon scripts, archives,
   submodule/LFS metadata, external references and permission-widening metadata are discoverable but
   non-authoritative.
4. Approval is not stored in repository-controlled files. It is bound to the exact content fingerprint.
5. Before every privileged operation the workspace is rescanned. A material change therefore returns the
   workspace to quarantine and defeats approval replay/TOCTOU-by-change.
6. Scan limits fail closed as `BLOCKED`; archive and external content are not expanded or fetched during
   bootstrap.
7. Critical containment findings cannot be approved.

## KodeCode integration

`QuarantinedKodeCodeExecutor` wraps an existing `KodeCodeExecutor`. It maps the existing structured tool
effects (`read`, `write`, `execute`) to workspace operations and performs the current preflight before
delegating. The legacy executor remains unchanged for compatibility, while safe repository opening has an
explicit hardened entry point.

## Acceptance

The R16.3 workflow runs on Ubuntu and Windows and binds evidence to the exact checkout SHA. Synthetic
fixtures verify:

- new-workspace quarantine with read-only usability;
- execution denial before approval;
- exact-fingerprint approval for explicitly authorized operations;
- automatic re-quarantine after material changes;
- discovery of executable/task/submodule/archive/external-reference bait without execution;
- sanitized machine-readable risk summaries;
- external symlink escape denial when supported;
- resource-bound fail-closed behavior.

No live secret, real malware, external repository fetch, package installation from fixture metadata, host
destructive action or real project mutation is used by core acceptance.
