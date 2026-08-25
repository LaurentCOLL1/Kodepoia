# R12.12 — Acceptance

## Scope

Versioned, bounded, authenticated local IPC contracts with deterministic framing, replay protection, authorization, explicit OS-local transports and lifecycle cleanup. No TCP/network listener fallback is introduced.

Manual intervention: **CONDITIONAL**.

Trigger manual evidence only if the required Windows named-pipe or Unix-domain-socket semantic cannot be demonstrated by accepted hosted CI on the exact candidate SHA. If both supported transport seams pass in hosted Windows/Linux Python Core, manual intervention is **NOT TRIGGERED**.

## Required acceptance

- protocol version, frame limits, replay window and endpoint identity are explicit and digest-stable;
- endpoint scope is structurally `local_only=true`; no `AF_INET`/TCP fallback exists;
- Windows uses an `AF_PIPE` address rooted at `\\.\pipe\`; non-Windows hosted Linux acceptance uses `AF_UNIX` in a private runtime directory;
- application envelopes use deterministic canonical JSON plus SHA-256 HMAC authentication; runtime authentication keys are never serialized into envelopes/evidence;
- the transport's `multiprocessing.connection` authentication challenge also uses the runtime auth key;
- message length is explicitly framed and bounded before parsing; truncated, overlong, malformed and oversized messages fail closed;
- stale protocol versions fail closed;
- peer session, role and method are authorized against a bounded allowlist;
- replayed message IDs fail closed through a bounded replay window;
- transport receive uses bytes APIs only; untrusted pickle/object deserialization is not an IPC execution surface;
- listener/client resources are explicitly closed; Unix runtime socket directories are removed after owned endpoint closure;
- server acceptance threads are owned non-daemon threads and cannot silently outlive the acceptance run;
- focused R12.12 tests perform a real request/response roundtrip on hosted Windows `AF_PIPE` and hosted Linux `AF_UNIX` through Python Core;
- exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed; desktop adapter workflows remain regression evidence.

## Web-researched implementation basis

- Microsoft documents that named-pipe access is controlled by security descriptors/DACLs and that default descriptors can grant broader read access than Kodepoia should assume; R12.12 therefore does **not** manufacture a claim that a custom Windows DACL is installed by Python's high-level transport wrapper;
- Microsoft documents that named pipes may be reachable remotely when the server service is available; Kodepoia allocates only local-machine `\\.\pipe\...` addresses, never accepts a remote machine address, requires authenticated application envelopes, and exposes no network-listener fallback;
- Python documents `multiprocessing.connection.Listener`/`Client` support for Windows `AF_PIPE` and Unix `AF_UNIX`, HMAC-based connection authentication, `send_bytes`/`recv_bytes`, and explicit listener closure.

Official references:

- https://learn.microsoft.com/windows/win32/ipc/named-pipe-security-and-access-rights
- https://learn.microsoft.com/windows/win32/ipc/named-pipes
- https://docs.python.org/3/library/multiprocessing.html#listeners-and-clients

## Evidence state

Base normalized `main`: `1f2d18b01e79845473fefbda98f722485310d92a`.
Branch: `r12/12-local-ipc`.
Manual state: **CONDITIONAL / PENDING hosted transport evidence**.

Exact implementation SHA and workflow run IDs are **PENDING** until the branch is frozen and independently gated.

## Merge / normalization rule

Freeze one immutable implementation head and require exact-head standard gates plus the real Windows/Linux transport tests inside Python Core. If either supported OS transport cannot be proven, stop and trigger bounded manual evidence before any R12.13 work. If hosted evidence succeeds, record manual state **NOT TRIGGERED**, update this document and continuity, re-gate the resulting final documentation head, merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization. R12.13 remains forbidden until that normalization merges.
