# R20.5 Update Operations Runbook

This runbook is the operator procedure for **R20.5 — Expiry Monitoring, Alerting & Client UX Hardening**. It covers metadata-lifetime warnings, missed R20.4 refreshes, signing failures, and GitHub Actions outages without weakening TUF verification or Kodepoia local availability.

## Safety boundary

The R20.5 monitor is observational and read-only. It never receives Snapshot/Timestamp signing secrets, never modifies release assets or metadata, and never changes application startup behavior.

Operators must **never accept expired** or unverifiable metadata as an availability fallback. Kodepoia startup and local/offline work remain available while update discovery reports a temporary service condition. Root and Targets private authority remains offline and is never moved into CI or a routine online signer.

## Monitor and thresholds

The production workflow is `.github/workflows/r20-5-expiry-monitoring.yml`. It runs every six hours at minute 47 and may also be dispatched manually after it exists on `main`.

The monitor evaluates all four trusted metadata roles and the visible production history of `.github/workflows/r20-4-scheduled-metadata-refresh.yml`.

| Signal | Warning | Critical | Operator meaning |
| --- | ---: | ---: | --- |
| Root remaining lifetime | <= 90 days | <= 30 days | Prepare/execute the governed offline Root ceremony; online refresh cannot extend Root. |
| Targets remaining lifetime | <= 90 days | <= 30 days | Prepare/execute an offline release-authorization refresh; online refresh cannot extend Targets. |
| Snapshot remaining lifetime | <= 36 hours | <= 24 hours | Investigate R20.4 immediately; critical is at the normal refresh threshold. |
| Timestamp remaining lifetime | <= 36 hours | <= 24 hours | Investigate R20.4 immediately; critical is at the normal refresh threshold. |
| Age of last successful R20.4 production run | > 9 hours | > 18 hours | One or more expected six-hour runs are missing/stale. |
| Consecutive completed R20.4 failures | 1 | >= 2 | Inspect the failed run before the online metadata reaches expiry. |

Invalid, inconsistent, expired, rollbacked, or otherwise unverifiable metadata is always classified **critical**. The monitor does not attempt a permissive recovery.

## Normal warning response

1. Open the latest **R20.5 Update Operations Health Monitor** run and read its job summary. Confirm which role or refresh-history signal caused the warning.
2. Open the corresponding recent **R20.4 Scheduled Metadata Refresh** runs. A single failed run is a warning; record whether the next scheduled/manual run succeeds.
3. If Snapshot or Timestamp is within 36 hours of expiry, manually dispatch R20.4 rather than waiting for another schedule slot.
4. If Root or Targets is within its warning window, schedule the appropriate offline-authority procedure. Do not try to renew either role with the Snapshot/Timestamp online keys.
5. Confirm the next R20.5 monitor returns `healthy` after remediation.

## Emergency manual refresh

Use this path when Snapshot/Timestamp is critical or a scheduled R20.4 run failed and GitHub Actions is otherwise operational.

Preferred path:

```text
GitHub -> Actions -> R20.4 Scheduled Metadata Refresh -> Run workflow -> main
```

Equivalent GitHub CLI dispatch from an authenticated operator workstation:

```powershell
gh workflow run r20-4-scheduled-metadata-refresh.yml --ref main
```

Then verify all of the following before treating the incident as resolved:

- the freshness-check used the then-current exact `main` SHA;
- if refresh was due, only `update-repository/metadata/snapshot.json` and `timestamp.json` changed;
- the publication PR passed the exact-head Repository Guard checks;
- the publication merge did not race an advancing `main`;
- Root and Targets remained byte-for-byte unchanged;
- a subsequent R20.5 monitor reports a non-critical state.

If R20.4 reports that no refresh is required, do not manufacture a metadata version merely to clear an alert. Investigate the monitor's other signal instead.

## GitHub Actions outage

A GitHub Actions outage must never cause verification to be disabled, branch-protection requirements to be bypassed, or expired metadata to be accepted.

1. Determine whether GitHub Git/PR service remains available and whether only Actions is affected.
2. Keep application startup/local work unaffected. Update discovery may remain temporarily unavailable; this is safer than accepting stale trust data.
3. If online metadata is still above the critical threshold, wait for Actions service recovery and manually dispatch R20.4 immediately afterward.
4. If online metadata enters the critical window and Actions remains unavailable, an operator who retains the authorized low-authority Snapshot/Timestamp keys may prepare a replacement pair locally from a clean clone of the exact current `main` using the existing R20.4 tooling. Do not expose secret values in shell history, logs, issues, artifacts, commits, screenshots, or this runbook.
5. The locally prepared pair must still modify **only** Snapshot/Timestamp, use the distinct authorized online keys, increment versions monotonically, bind exact Targets then exact signed Snapshot bytes, and remain bounded by Root/Targets authority.
6. Do not bypass the protected publication/Repository Guard path. If required GitHub checks are unavailable, keep the prepared pair private until the checks can execute, then publish through the governed PR path.
7. After service recovery, re-run R20.4/R20.5 and confirm healthy evidence on the current `main`.

The local preparation command, after the two authorized online signer values have been supplied through a secure process-local environment, is:

```powershell
python scripts/r20_4_scheduled_metadata_refresh.py --mode refresh
```

Immediately inspect the diff and abort if anything except the two online metadata files changed.

## Signing-backend or online-key failure

If R20.4 reaches the signing job but rejects one or both online signer identities, treat the run as failed closed.

- Do not substitute a Root or Targets key.
- Do not reuse one online key for both Snapshot and Timestamp.
- Compare the public identity expected by `docs/roadmap/R20_3_PUBLIC_KEYS.json` with the configured low-authority signer identities without revealing private material.
- Restore/rotate only through the governed R20 online-signer procedure. If the retained local authorized online keys are still valid, they may be used only for the emergency local preparation described above.
- After remediation, dispatch R20.4 and then R20.5 and verify exact public evidence.

## Root/Targets authority warning or expiry risk

Root/Targets are intentionally outside routine online maintenance. If either role approaches its warning/critical threshold, Snapshot/Timestamp refresh alone is not a fix.

For Root, use the governed offline threshold ceremony and sequential Root-transition validation. For Targets, use the governed offline release-authorization procedure. In both cases, private Root/Targets material remains outside Git, GitHub Actions, public evidence, and routine online signers.

If Root or Targets is already expired, update discovery must remain failed closed until properly authorized metadata is restored. Do not alter the client to accept it.

## Closure evidence

An incident is closed only when the current public trust view verifies, the R20.4 production loop has a recent successful run, the R20.5 monitor is non-critical, the repository contains no private signer material, and no safety invariant was weakened during recovery.
