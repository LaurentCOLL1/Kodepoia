# R5 — Hardware-local Godot acceptance

**Status:** ACCEPTED / COMPLETE  
**Accepted:** 2026-08-22

This document records the final real-workstation acceptance for R5.6. No further R5 hardware action is required unless a regression is demonstrated.

## Target environment

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- loopback ports LSP `6005`, DAP `6006`, debug `6007`.

## Acceptance history

The initial probe exposed a `ProcessSandbox.run()` pipe-draining defect. It was corrected by draining stdout/stderr through `communicate(timeout=...)` while preserving global kill-switch registration. The post-fix probe then passed **5/5**.

The first full acceptance exposed two additional integration defects: Movie Maker was incorrectly combined with headless/dummy rendering, and the long-lived socket-based Godot editor service used unread stdio pipes. Those were corrected by using a real renderer for `--write-movie` and a sandboxed `spawn_background()` path for socket services.

A later 17/19 run isolated the final DAP defect: the TCP connection timeout remained attached to the protocol socket and Kodepoia waited synchronously for the DAP `launch` response before sending `configurationDone`. The final fix switches an established protocol socket back to blocking mode and supports deferred DAP launch/configuration sequencing.

## Final accepted evidence

Report generated `2026-08-22T06:49:29.198572+00:00`:

```text
probe_only=false
acceptance_completed=true
passed=19
failed=0
total=19
```

All nineteen real checks passed:

1. engine version;
2. project inspection;
3. scene parse;
4. scene domain analysis;
5. GDScript inspection;
6. GDScript `--check-only`;
7. project import;
8. scene smoke;
9. 120-frame benchmark (~101.0 effective FPS);
10. Movie Maker capture;
11. governed scene edit + SafeChange snapshot;
12. Godot service start;
13. LSP symbols;
14. LSP diagnostics;
15. DAP initialize;
16. DAP project launch;
17. DAP threads;
18. Windows release export;
19. audit hash-chain verification.

### Material artifacts and protocol proof

- Movie capture: `.kodepoia/captures/r5-acceptance.avi`, **64,612 bytes**.
- Renderer/device observed during capture: AMD Radeon RX 6750 XT through Godot Compatibility/OpenGL.
- Godot services: LSP 6005 and DAP 6006 initialized; debug server port 6007.
- DAP project launch: PASS; returned `launched=true`.
- DAP threads: PASS; thread ID 1, name `Main`.
- Governed scene edit: PASS with `snapshot_created=true` and distinct before/after SHA-256 values.
- Windows release export: `.kodepoia/exports/r5-acceptance.exe`, **109,127,680 bytes**.
- Audit chain: `valid=true`.

## Final CI supporting the hardware evidence

PR #28 functional head `8e9f01d785a691ce03d3b589367b724b073c8cec` passed:

- Repository Guard `32557370901` — SUCCESS;
- Python Core `32557370829` — SUCCESS Windows + Ubuntu, including PowerShell acceptance-runner syntax validation;
- KodeStudio UI Smoke `32557370915` — SUCCESS Windows.

PR #28 was then merged as `ecb0455d179c8c0b2de0a5d1d8a496a0f8f980e8`.

## Result

The hardware acceptance gate defined for R5 is satisfied. R5 may remain closed unless a demonstrated regression requires reopening it.

R6 is **AUTHORIZED / NOT STARTED** after post-merge normalization reaches `main`.
